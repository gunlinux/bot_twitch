import asyncio
import typing

from dotenv import load_dotenv

from retwitch.token import TokenManager
from retwitch.bot import SenderBotClient
from retwitch.reqs import TwitchAccessError
from retwitch import settings
from retwitch.utils import logger_setup


from requeue.requeue import Queue
from requeue.rredis import RedisConnection

from requeue.models import QueueMessage


logger = logger_setup(__name__)
# twitch has a limit of 5 messages per minute
MESSAGE_TIMEOUT = 5


async def init_process(bot: SenderBotClient) -> typing.Any:
    async def process(message: QueueMessage) -> None:
        logger.debug('%s process %s', __name__, message.event)
        if message.data:
            try:
                if message.data.message:
                    await bot.send_message(message.data.message)
            except TwitchAccessError as e:
                await bot.token_manager.refresh_token()
                logger.critical('twitch access error', exc_info=e)
            await asyncio.sleep(MESSAGE_TIMEOUT)

    return process


async def main():
    load_dotenv()

    token_manager = TokenManager(
        client_id=settings.RECLIENT_ID, client_secret=settings.RECLIENT_SECRET
    )
    token_manager.load_real_token()
    await token_manager.refresh_token()
    token_manager.save_real_token()

    async with RedisConnection(settings.redis_url) as redis_connection:
        queue: Queue = Queue(name=settings.TWITCH_OUT, connection=redis_connection)
        bot = SenderBotClient(
            token_manager=token_manager,
            client_id=settings.RECLIENT_ID,
            user_id=settings.REBOT_ID,
            broadcaster_user_id=settings.REOWNER_ID,
        )
        await bot.send_message('> sendbot rejoin chat')

        process = await init_process(bot)
        await queue.consumer(process)


if __name__ == '__main__':
    asyncio.run(main())
