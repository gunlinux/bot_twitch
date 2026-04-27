import asyncio

from dotenv import load_dotenv
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
# twitch has a limit of 5 messages per minute
MESSAGE_TIMEOUT = 12


class SenderConsumer:
    def __init__(self, bot: SenderBotClient) -> None:
        self.bot = bot

    async def send_message(self, message: FQueueMessage) -> None:
        if message.data and message.data.message:
            await self.bot.send_message(message.data.message)

    async def process(self, message: FQueueMessage) -> None:
        logger.debug('%s process %s', __name__, message.event)
        if message.data:
            try:
                await self.send_message(message)
            except TwitchAccessError as e:
                await self.bot.token_manager.refresh_token()
                logger.critical('twitch access error', exc_info=e)
                raise TwitchAccessError from e


async def main():
    load_dotenv()

    token_store = TokenStore(settings.TOKEN_FILE)
    token_manager = TokenManager(
        twitch_auth=TwitchAuth(
            client_id=settings.RECLIENT_ID,
            client_secret=settings.RECLIENT_SECRET,
        ),
        token_store=token_store,
    )
    token_manager.load_real_token()

    broker = RabbitBroker(settings.rabbit_url, virtualhost=settings.rabbit_vhost)
    bot = SenderBotClient(
        token_manager=token_manager,
        user_id=settings.REBOT_ID,
        broadcaster_user_id=settings.REOWNER_ID,
    )
    sender_consumer = SenderConsumer(bot=bot)
    consumer = RabbitConsumer(
        queue_name='twitch_out', broker=broker, worker=sender_consumer.process
    )
    await bot.send_message('> sendbot rejoin chat')
    await consumer.consume(sleep_time=MESSAGE_TIMEOUT)


if __name__ == '__main__':
    asyncio.run(main())
