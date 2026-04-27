import asyncio
import os
from collections.abc import Callable, Awaitable

from dotenv import load_dotenv
from faststream.rabbit import RabbitBroker, RabbitExchange

from retwitch.token.token_manager import TokenManager
from retwitch.token.token_oauth import TwitchAuth
from retwitch.token.token_store import TokenStore
from retwitch.bot import BotClient, ChannelBotClient
from retwitch.schemas.events import RetwitchEvent
from retwitch import settings
from retwitch.utils import logger_setup
from retwitch.queue import retwitch_to_queue
from requeue.fstream.publisher import Publisher


logger = logger_setup(__name__)


async def init_process(
    publisher: Publisher,
) -> Callable[[RetwitchEvent], Awaitable[None]]:
    async def process_mssg(event: RetwitchEvent) -> None:
        logger.info('processsing event: %s', event)
        payload = retwitch_to_queue(event, source='retwitch_getter')
        await publisher.publish(payload)

    return process_mssg


async def main():
    load_dotenv()
    client_id: str = os.getenv('RECLIENT_ID', '')
    client_secret: str = os.getenv('RECLIENT_SECRET', '')
    owner_id: str = os.getenv('REOWNER_ID', '')
    bot_id: str = os.getenv('REBOT_ID', '')

    token_store = TokenStore(token_file=settings.TOKEN_FILE)
    twitch_auth = TwitchAuth(client_id=client_id, client_secret=client_secret)
    token_manager = TokenManager(twitch_auth=twitch_auth, token_store=token_store)
    token_manager.load_real_token()
    await token_manager.refresh_token()
    token_manager.save_real_token()
    channel_token_store = TokenStore(
        token_file=settings.CHANNEL_TOKEN_FILE,
    )
    channel_auth = TwitchAuth(client_id=client_id, client_secret=client_secret)
    channel_token_manager: TokenManager = TokenManager(
        twitch_auth=channel_auth,
        token_store=channel_token_store,
    )
    channel_token_manager.load_real_token()
    await channel_token_manager.refresh_token()
    channel_token_manager.save_real_token()

    broker = RabbitBroker(settings.rabbit_url, virtualhost=settings.rabbit_vhost)
    exch = RabbitExchange(settings.rabbit_exchange)
    publisher = Publisher(broker=broker, exchange=exch)
    handler = await init_process(publisher=publisher)

    bot = BotClient(
        token_manager=token_manager,
        user_id=bot_id,
        broadcaster_user_id=owner_id,
    )
    bot_channel = ChannelBotClient(
        token_manager=channel_token_manager,
        user_id=bot_id,
        broadcaster_user_id=owner_id,
    )
    await asyncio.gather(bot.run(handler=handler), bot_channel.run(handler=handler))


if __name__ == '__main__':
    asyncio.run(main())
