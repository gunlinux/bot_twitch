from collections.abc import Mapping, Callable, Awaitable
import asyncio
import typing
import logging
import json
import random
from time import time
from collections import OrderedDict

import aiohttp
from retwitch.schemas.events import EventSchema
from retwitch.models.events import create_event_from_subevent, RetwitchEvent
from retwitch.token.token_manager import TokenManager
from retwitch.reqs import HttpReqs

"""
Рекомендация: разделить на минимум три уровня — WebSocket клиент, EventSub подписчик, обработчик событий.
"""

logger = logging.getLogger('twitchbot')
_rng = random.SystemRandom()

WS_URL = 'wss://eventsub.wss.twitch.tv/ws'
_DEDUP_MAX_SIZE = 500


class BotClient:
    def __init__(
        self,
        token_manager: TokenManager,
        user_id: str,
        broadcaster_user_id: str,
        keep_alive_timeout: int = 30,
    ):
        self.http_reqs: HttpReqs = HttpReqs(token_manager=token_manager)
        self.token_manager = token_manager
        self._keep_alive_timeout: int = keep_alive_timeout
        self._heartbeat: int = min(self._keep_alive_timeout, 25)
        self.session_id: str | None = None
        self.user_id: str = user_id
        self.broadcaster_user_id: str = broadcaster_user_id
        self.lastseen: float | None = None
        self._socket = None
        self._reconnect_url: str | None = None
        self.handler: Callable[[RetwitchEvent], Awaitable[None]] | None = None
        self._seen_message_ids: OrderedDict[str, None] = OrderedDict()

    async def create_sub(self, session_id: str) -> None:
        await self.http_reqs.create_sub_chat_message(
            session_id=session_id,
            broadcaster_user_id=self.broadcaster_user_id,
            user_id=self.user_id,
        )
        logger.info('channel_follow %s', self.broadcaster_user_id)
        await self.http_reqs.create_sub_channel_follow(
            session_id=session_id,
            broadcaster_user_id=self.broadcaster_user_id,
            user_id=self.user_id,
        )

    async def process_event(self, event: Mapping[str, typing.Any]) -> None:
        if self._socket is None:
            raise ValueError('socket_not_connected')
        # Twitch resets its keepalive timer on every message (notifications
        # included), so it only sends session_keepalive while idle. Refresh
        # lastseen on any inbound message, otherwise the watchdog kills a
        # healthy-but-busy connection.
        self.lastseen = time()
        match event['metadata']['message_type']:
            case 'session_welcome':
                logger.info('got welcome message')
                self.session_id = event['payload']['session']['id']

            case 'session_keepalive':
                logger.debug('updated last seen')

            case 'session_reconnect':
                reconnect_url = event['payload']['session']['reconnect_url']
                logger.info('session reconnect requested, url=%s', reconnect_url)
                self._reconnect_url = reconnect_url
                await self._socket.close()

            case 'revocation':
                await self._socket.close()
            case _:
                await self._handle_notification(event)

    async def _handle_notification(self, event: Mapping[str, typing.Any]) -> None:
        message_id = event.get('metadata', {}).get('message_id', '')
        if message_id:
            if message_id in self._seen_message_ids:
                logger.debug('duplicate message_id %s, skipping', message_id)
                return
            self._seen_message_ids[message_id] = None
            if len(self._seen_message_ids) > _DEDUP_MAX_SIZE:
                self._seen_message_ids.popitem(last=False)
        new_event: RetwitchEvent | None = create_event_from_subevent(event)
        if not new_event:
            return
        if self.handler:
            await self.handler(new_event)

    async def _listen(self):
        logger.info('start listen')
        while True:
            await asyncio.sleep(self._keep_alive_timeout)
            if self.lastseen is None or not self._socket:
                continue

            last_seen = time() - self.lastseen

            if last_seen > self._keep_alive_timeout * 2:
                logger.warning('we are dead %s', last_seen)
                await self._socket.close()

    async def run(self, handler: Callable[[RetwitchEvent], Awaitable[None]]) -> None:
        self.handler = handler
        await asyncio.gather(self.run_ws(), self._listen())

    async def run_ws(self):
        connect_url = WS_URL
        is_reconnect = False
        backoff = 1.0
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    params = {
                        'keepalive_timeout_seconds': self._keep_alive_timeout,
                    }
                    self._socket = await session.ws_connect(
                        connect_url,
                        heartbeat=self._heartbeat,
                        # reconnect_url already includes query params
                        params=params if not is_reconnect else None,
                    )
                    welcome_message: aiohttp.WSMessage = await self._socket.receive()
                    event = typing.cast(
                        'Mapping[str, typing.Any]',
                        EventSchema().load(json.loads(welcome_message.data)),
                    )
                    await self.process_event(event)
                    if not self.session_id:
                        logger.warning('no session_id after welcome, reconnecting')
                        connect_url = WS_URL
                        is_reconnect = False
                        continue

                    backoff = 1.0

                    if not is_reconnect:
                        # Create the new subscriptions first so the connection
                        # starts delivering events as early as possible, then
                        # reap subs left over from previous (now-dead) sessions.
                        await self.create_sub(session_id=self.session_id)
                        subs = await self.http_reqs.get_subs()
                        for sub in subs:
                            sub_session = sub.get('transport', {}).get('session_id', '')
                            if sub_session != self.session_id:
                                logger.info(
                                    'deleting stale sub %s (session %s)',
                                    sub.get('id'),
                                    sub_session,
                                )
                                await self.http_reqs.delete_event_sub(
                                    eventsub_id=sub.get('id')
                                )

                    logger.info('ready to read subs events')

                    async for mssg in self._socket:
                        logger.info('got new message: %s', mssg.data)
                        try:
                            event = typing.cast(
                                'Mapping[str, str]',
                                EventSchema().load(json.loads(mssg.data)),
                            )
                        except Exception as e:  # noqa: BLE001
                            logger.warning('cant load event %s', mssg.data, exc_info=e)
                            continue
                        await self.process_event(event)
            except Exception as e:  # noqa: BLE001
                logger.warning('ws connection error: %s', e)

            if self._reconnect_url:
                connect_url = self._reconnect_url
                self._reconnect_url = None
                is_reconnect = True
            else:
                connect_url = WS_URL
                is_reconnect = False
                jitter = _rng.uniform(0, backoff * 0.1)
                delay = min(backoff + jitter, 60.0)
                logger.info('reconnecting in %.1f seconds', delay)
                await asyncio.sleep(delay)
                backoff = min(backoff * 2, 60.0)


class ChannelBotClient(BotClient):
    @typing.override
    async def create_sub(self, session_id: str) -> None:
        logger.info('channel_subsribe %s', self.broadcaster_user_id)
        await self.http_reqs.create_sub_channel_subscribe(
            session_id=session_id, broadcaster_user_id=self.broadcaster_user_id
        )
        await self.http_reqs.create_sub_channel_raid(
            session_id=session_id, broadcaster_user_id=self.broadcaster_user_id
        )
        await self.http_reqs.create_sub_custom_reward_redemption_add(
            session_id=session_id, broadcaster_user_id=self.broadcaster_user_id
        )


class SenderBotClient(BotClient):
    @typing.override
    async def create_sub(self, session_id: str) -> None:
        # we dont need subs here
        pass

    async def send_message(self, message: str):
        await self.http_reqs.send_message(
            self.broadcaster_user_id, self.user_id, message
        )
