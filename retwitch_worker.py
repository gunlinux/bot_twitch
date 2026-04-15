import asyncio

from faststream.rabbit import RabbitBroker

from retwitch.handlers import RetwitchEventHandler
from requeue.fstream.consumer import RabbitConsumer
from requeue.sender.sender import Sender
from retwitch.handlers import Command
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
        command_dir=settings.COMMAND_DIR,
    )
    commands = [
        Command('ауф', real_runner=auf),
        Command('gunlinAuf', real_runner=auf),
        Command('awoo', real_runner=auf),
        Command('auf', real_runner=auf),
    ]
    for command in commands:
        retwitch_handler.register(command)
    await retwitch_handler.reload_raw_commands(None)  # pyright: ignore[reportArgumentType]

    await RabbitConsumer(
        broker=broker,
        worker=retwitch_handler.on_message,
        queue_name=settings.TWITCH_EVENTS,
    ).consume()


if __name__ == '__main__':
    asyncio.run(main())
