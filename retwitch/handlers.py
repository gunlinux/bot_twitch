import logging
from abc import ABC, abstractmethod
import typing
from pathlib import Path
from retwitch.models.commands import Command
from retwitch.command_registry import CommandRegistry


from requeue.fstream.models import FQueueMessage, FQueueEvent
from requeue.sender.sender import SenderABC

from retwitch.schemas.events import (
    EventType,
)


logger = logging.getLogger('retwitch.handlers')
logger.setLevel(logging.DEBUG)


class EventHandler(ABC):
    def __init__(
        self,
        sender: SenderABC | None,
        admin: str | None,
        command_registry: CommandRegistry,
        command_dir: str = '',
    ) -> None:
        self._command_registry = command_registry
        self.sender: SenderABC | None = sender
        self.admin = admin
        self.command_dir = command_dir
        self._command_registry.register(
            Command(name='$reset', real_runner=self.reload_raw_commands)
        )
        self._command_registry.register(
            Command(name='$reload', real_runner=self.reload_raw_commands)
        )

    @abstractmethod
    async def handle_event(self, event: FQueueEvent) -> None:
        pass

    @abstractmethod
    async def on_message(self, message: FQueueMessage) -> None: ...

    async def chat(self, mssg: str) -> None:
        if self.sender is not None:
            await self.sender.send_message(mssg)
        else:
            logger.error('Cannot send message: sender is not initialized')

    def _get_commands_from_dir(self) -> list[Command]:
        # Get all files matching the '*.md' pattern
        command_path = Path.cwd() / self.command_dir
        markdown_files = [
            f for f in command_path.iterdir() if f.is_file() and f.suffix == '.md'
        ]

        out = []
        for file in markdown_files:
            # Construct the full path to each file
            # Open the file and read its contents
            data: dict[str, typing.Any] = {}
            with Path.open(file, 'r'):
                data['name'] = Path(file).stem
                data['text'] = file.read_text()

                logger.info('registred command from file %s ', data)
                out.append(
                    Command(
                        f'!{data["name"]}',
                        real_runner=None,
                        data=data,
                    )
                )
        return out

    async def reload_raw_commands(self, _: FQueueEvent) -> None:
        self._command_registry.clear_raw_commands()
        for command in self._get_commands_from_dir():
            self._command_registry.register(command)

    def register(self, command: Command) -> None:
        logger.debug('Successfully registered command %s', command.name)
        self._command_registry.register(command)


class RetwitchEventHandler(EventHandler):
    @typing.override
    async def on_message(self, message: FQueueMessage) -> None:
        logger.debug('Processing new event from queue')
        logger.debug('Received message data: %s', message.data)
        await self.handle_event(message.data)

    @typing.override
    async def handle_event(self, event: FQueueEvent) -> None:
        if event.event_type in [e.name for e in EventType]:
            await self._chat_notify(event)

    async def _chat_notify(self, event: FQueueEvent) -> None:
        logger.info('donat.event %s', event.event_type)
        if event.message:
            await self.chat(event.message)

    async def run_command(self, event: FQueueEvent) -> None:
        logger.debug('Running command for event %s', event)
        if event_message := event.message:
            message = await self._command_registry.run(event_message, event)
            if message:
                await self.chat(typing.cast('str', message))
