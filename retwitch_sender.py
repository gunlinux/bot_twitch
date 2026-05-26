import asyncio
import time
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

from faststream.rabbit import RabbitBroker
from requeue.fstream.models import FQueueMessage
from requeue.fstream.consumer import RabbitConsumer

from retwitch.token.token_manager import TokenManager
from retwitch.token.token_store import TokenStore
from retwitch.token.token_oauth import TwitchAuth
from retwitch.bot import SenderBotClient
from retwitch.reqs import TwitchAccessError
from retwitch import settings
from retwitch.utils import logger_setup


logger = logger_setup(__name__)
# twitch caps bots at ~5 messages/minute; 12s spacing stays safely under that
MESSAGE_TIMEOUT = 12


class ChannelRateLimiter:
    """Per-channel token bucket: at most one message every MESSAGE_TIMEOUT seconds."""

    def __init__(self, interval: float = MESSAGE_TIMEOUT) -> None:
        self._interval = interval
        self._last_sent: dict[str, float] = defaultdict(float)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def wait(self, channel_id: str) -> None:
        async with self._locks[channel_id]:
            elapsed = time.monotonic() - self._last_sent[channel_id]
            if elapsed < self._interval:
                await asyncio.sleep(self._interval - elapsed)
            self._last_sent[channel_id] = time.monotonic()


class SenderConsumer:
    def __init__(self, bot: SenderBotClient, rate_limiter: ChannelRateLimiter) -> None:
        self.bot = bot
        self._rate_limiter = rate_limiter

    async def send_message(self, message: FQueueMessage) -> None:
        if message.data and message.data.message:
            await self._rate_limiter.wait(self.bot.broadcaster_user_id)
            await self.bot.send_message(message.data.message)

    async def process(self, message: FQueueMessage) -> None:
        logger.debug('%s process %s', __name__, message.event)
        if message.data:
            try:
                await self.send_message(message)
            except TwitchAccessError as e:
                await self.bot.token_manager.refresh_token()
                logger.warning('twitch access error, retrying once', exc_info=e)
                try:
                    await self.send_message(message)
                except TwitchAccessError as retry_e:
                    logger.critical('twitch access error after retry', exc_info=retry_e)
                    raise TwitchAccessError from retry_e


async def main():
    token_store = TokenStore(settings.TOKEN_FILE)
    token_manager = TokenManager(
        twitch_auth=TwitchAuth(
            client_id=settings.RECLIENT_ID,
            client_secret=settings.RECLIENT_SECRET,
        ),
        token_store=token_store,
    )
    token_manager.load_real_token()
    await token_manager.refresh_token()
    token_manager.save_real_token()

    broker = RabbitBroker(settings.RABBIT_URL, virtualhost=settings.RABBIT_VHOST)
    bot = SenderBotClient(
        token_manager=token_manager,
        user_id=settings.REBOT_ID,
        broadcaster_user_id=settings.REOWNER_ID,
    )
    rate_limiter = ChannelRateLimiter()
    sender_consumer = SenderConsumer(bot=bot, rate_limiter=rate_limiter)
    consumer = RabbitConsumer(
        queue_name='twitch_out', broker=broker, worker=sender_consumer.process
    )
    await bot.send_message('> sendbot rejoin chat')
    await consumer.consume()


if __name__ == '__main__':
    asyncio.run(main())
