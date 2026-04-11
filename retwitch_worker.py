import asyncio

from faststream.rabbit import RabbitBroker

from retwitch.handlers import RetwitchEventHandler
from requeue.fstream.consumer import RabbitConsumer
from requeue.sender.sender import Sender
from retwitch.handlers import Command
from commander import get_commands_from_dir, reload_command
from commander.commands import auf
from retwitch import settings
from retwitch.utils import logger_setup


logger = logger_setup(__name__)


async def main() -> None:
    broker = RabbitBroker(settings.rabbit_url, virtualhost=settings.rabbit_vhost)

    sender = Sender(exchange_name=settings.TWITCH_OUT, broker=broker)
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

    await RabbitConsumer(
        broker=broker,
        worker=retwitch_handler.on_message,
        queue_name=settings.DONATS_EVENTS,
    ).consume()


if __name__ == '__main__':
    asyncio.run(main())
