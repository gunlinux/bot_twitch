import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any
import typing
from dataclasses import dataclass
from pathlib import Path


from requeue.fstream.models import FQueueMessage, FQueueEvent
from requeue.sender.sender import SenderABC

from retwitch.schemas import (
    EventType,
    RetwitchEvent,
)

from collections.abc import Awaitable
from typing import Protocol, runtime_checkable


logger = logging.getLogger('retwitch.handlers')
logger.setLevel(logging.DEBUG)


@runtime_checkable
class CommandRunner(Protocol):
    __name__: str

    async def __call__(
        self,
        event: RetwitchEvent,
        post: Awaitable[Any] | Callable[..., Any] | None = None,
        data: dict[str, str] | None = None,
    ) -> None: ...


@dataclass
class Command:
    name: str
    data: typing.Mapping | None = None
    real_runner: Callable[..., Any] | None = None


class EventHandler(ABC):
    def __init__(
        self, sender: SenderABC | None, admin: str | None, command_dir: str = ''
    ) -> None:
        self.commands: dict[str, Command] = {}
        self.sender: SenderABC | None = sender
        self.admin = admin
        self.command_dir = command_dir
        self.register(Command(name='$reset', real_runner=self.reload_raw_commands))

    @abstractmethod
    async def handle_event(self, event: FQueueEvent) -> None:
        pass

    @abstractmethod
    async def on_message(self, message: FQueueMessage) -> None: ...

    def register(self, command: Command) -> None:
        logger.debug('Successfully registered command %s', command.name)
        self.commands[command.name] = command

    async def chat(self, mssg: str) -> None:
        if self.sender is not None:
            await self.sender.send_message(mssg)
        else:
            logger.error('Cannot send message: sender is not initialized')

    def _clear_raw_commands(self) -> None:
        for command_name, command in self.commands.items():
            if command.real_runner is None:
                _ = self.commands.pop(command_name)
                logger.info('command removed %s', command)

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
        self._clear_raw_commands()
        self._get_commands_from_dir()


class RetwitchEventHandler(EventHandler):
    @typing.override
    async def on_message(self, message: FQueueMessage) -> None:
        logger.debug('Processing new event from queue')
        logger.debug('Received message data: %s', message.data)
        await self.handle_event(message.data)

    @typing.override
    async def handle_event(self, event: FQueueEvent) -> None:
        if event.event_type == EventType.CHANNEL_FOLLOW.name:
            await self._follow(event)

        if event.event_type == EventType.CHANNEL_SUBSCRIBE.name:
            await self._subscribe(event)

        if event.event_type == EventType.CHANNEL_RESUBSCRIBE.name:
            await self._resubscribe(event)

        if event.event_type == EventType.CHANNEL_RAID.name:
            await self._channel_raid(event)

        if event.event_type == EventType.CHANNEL_MESSAGE.name:
            await self.run_command(event)

        if event.event_type == EventType.CUSTOM_REWARD.name:
            await self._custom_reward(event)

    async def _follow(self, event: FQueueEvent) -> None:
        logger.info('donat.event _follow')
        if event.message:
            await self.chat(event.message)

    async def _subscribe(self, event: FQueueEvent) -> None:
        logger.info('donat.event _subscribe')
        if event.message:
            await self.chat(event.message)

    async def _resubscribe(self, event: FQueueEvent) -> None:
        logger.info('donat.event _resubscribe')
        if event.message:
            await self.chat(event.message)

    async def _channel_raid(self, event: FQueueEvent) -> None:
        logger.info('donat.event _channel_raid')
        if event.message:
            await self.chat(event.message)

    async def _custom_reward(self, event: FQueueEvent) -> None:
        logger.info('donat.event _custom_reward %s', event)
        if event.message:
            await self.chat(event.message)

    async def run_command(self, event: FQueueEvent) -> None:
        logger.debug('Running command for event %s', event)
        for command_name, command in self.commands.items():
            if (
                event
                and event.message
                and event.message.lower().startswith(command_name.lower())
            ):
                logger.debug('detected command: %s', command)
                if command.real_runner is None and command.data:
                    message = command.data.get('text')
                else:
                    message = await command.real_runner(event)
                if message:
                    await self.chat(typing.cast('str', message))
