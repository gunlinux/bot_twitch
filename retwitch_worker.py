import asyncio

from retwitch.handlers import RetwitchEventHandler
from requeue.requeue import Queue
from requeue.rredis import RedisConnection
from requeue.sender.sender import Sender
from retwitch.handlers import Command
from commander import get_commands_from_dir, reload_command
from commander.commands import auf
from retwitch import settings
from retwitch.utils import logger_setup


logger = logger_setup(__name__)


async def main() -> None:
    async with RedisConnection(settings.redis_url) as redis_connection:
        queue: Queue = Queue(name=settings.TWITCH_EVENTS, connection=redis_connection)
        sender = Sender(queue_name=settings.TWITCH_OUT, connection=redis_connection)
        retwitch_handler: RetwitchEventHandler = RetwitchEventHandler(
            sender=sender,
            admin='gunlinux',
        )
        Command('ауф', retwitch_handler, real_runner=auf)
        Command('gunlinAuf', retwitch_handler, real_runner=auf)
        Command('awoo', retwitch_handler, real_runner=auf)
        Command('auf', retwitch_handler, real_runner=auf)
        get_commands_from_dir(settings.COMMAND_DIR, retwitch_handler)
        reload_command_runner = reload_command(settings.COMMAND_DIR, retwitch_handler)
        Command('$reload', retwitch_handler, real_runner=reload_command_runner)

        await queue.consumer(retwitch_handler.on_message)


if __name__ == '__main__':
    asyncio.run(main())
