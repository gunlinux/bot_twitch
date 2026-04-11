import asyncio
import typing

from dotenv import load_dotenv
from faststream.rabbit import RabbitBroker
from requeue.fstream.models import FQueueMessage
from requeue.fstream.consumer import RabbitConsumer

from retwitch.token import TokenManager
from retwitch.bot import SenderBotClient
from retwitch.reqs import TwitchAccessError
from retwitch import settings
from retwitch.utils import logger_setup


logger = logger_setup(__name__)
# twitch has a limit of 5 messages per minute
MESSAGE_TIMEOUT = 5


async def init_process(bot: SenderBotClient) -> typing.Any:
    async def process(message: FQueueMessage) -> None:
        logger.debug('%s process %s', __name__, message.event)
        if message.data:
            try:
                if message.data.message:
                    await bot.send_message(message.data.message)
            except TwitchAccessError as e:
                await bot.token_manager.refresh_token()
                logger.critical('twitch access error', exc_info=e)
                raise TwitchAccessError from e

    return process


async def main():
    load_dotenv()

    token_manager = TokenManager(
        client_id=settings.RECLIENT_ID, client_secret=settings.RECLIENT_SECRET
    )
    token_manager.load_real_token()

    broker = RabbitBroker(settings.rabbit_url, virtualhost=settings.rabbit_vhost)
    bot = SenderBotClient(
        token_manager=token_manager,
        client_id=settings.RECLIENT_ID,
        user_id=settings.REBOT_ID,
        broadcaster_user_id=settings.REOWNER_ID,
    )
    process = await init_process(bot)
    consumer = RabbitConsumer(queue_name='twitch_out', broker=broker, worker=process)
    await bot.send_message('> sendbot rejoin chat')
    await consumer.consume()


if __name__ == '__main__':
    asyncio.run(main())
