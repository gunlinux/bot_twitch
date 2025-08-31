import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any
import typing

from gunlinuxbot.models import Event

from requeue.models import QueueMessage
from requeue.sender.sender import SenderAbc

from retwitch.schemas import (
    EventType,
    EventChannelMessage,
)
from requeue.models import QueueEvent

from collections.abc import Awaitable
from typing import Protocol, runtime_checkable


logger = logging.getLogger('gunlinuxbot.handlers')
logger.setLevel(logging.DEBUG)


@runtime_checkable
class CommandRunner(Protocol):
    __name__: str

    async def __call__(
        self,
        event: Event,
        post: Awaitable[Any] | Callable[..., Any] | None = None,
        data: dict[str, str] | None = None,
    ) -> None: ...


class Command:
    def __init__(
        self,
        name: str,
        event_handler: 'EventHandler',
        data: dict[str, typing.Any] | None = None,
        real_runner: Callable[..., Any] | None = None,
    ) -> None:
        self.name: str = name
        self.event_handler: EventHandler = event_handler
        self.event_handler.register(self.name, self)
        self.real_runner = real_runner
        self.data: dict[str, typing.Any] = {} if data is None else data

    async def run(self, event: Event) -> str | None:
        logger.debug('Running command %s for event %s', self.name, event)
        if self.real_runner is None:
            logger.warning('Command %s not implemented yet', self.name)
            return None
        return await self.real_runner(event, **self.data)

    @typing.override
    def __str__(self) -> str:
        return f'<Command> {self.name}'


class EventHandler(ABC):
    def __init__(self, sender: SenderAbc | None, admin: str | None) -> None:
        self.commands: dict[str, Command] = {}
        self.sender: SenderAbc | None = sender
        self.admin = admin

    @abstractmethod
    async def handle_event(self, event: QueueEvent) -> None:
        pass

    @abstractmethod
    async def on_message(self, message: QueueMessage) -> QueueMessage | None: ...

    def register(self, name: str, command: Command) -> None:
        logger.debug('Successfully registered command %s', name)
        self.commands[name] = command

    async def chat(self, mssg: str) -> None:
        if self.sender is not None:
            await self.sender.send_message(mssg)
        else:
            logger.error('Cannot send message: sender is not initialized')

    def clear_raw_commands(self) -> None:
        if not self.commands:
            return
        commands_to_remove: list[str] = []
        for command_name, command in self.commands.items():
            if (
                command.real_runner
                and command.real_runner.__name__ == 'command_raw_handler'
            ):
                commands_to_remove.append(command_name)
        for command in commands_to_remove:
            logger.info('command removed %s', command)
            _ = self.commands.pop(command)


class RetwitchEventHandler(EventHandler):
    @typing.override
    async def on_message(self, message: QueueMessage) -> QueueMessage | None:
        logger.debug('Processing new event from queue')
        logger.debug('Received message data: %s', message.data)
        await self.handle_event(message.data)
        message.finish()
        return message

    @typing.override
    async def handle_event(self, event: QueueEvent) -> None:
        if event.event_type == EventType.CHANNEL_FOLLOW.name:
            await self._follow(event)

        if event.event_type == EventType.CHANNEL_SUBSCRIBE.name:
            await self._subscribe(event)

        if event.event_type == EventType.CHANNEL_RESUBSCRIBE.name:
            await self._resubscribe(event)

        if event.event_type == EventType.CHANNEL_RAID.name:
            await self._channel_raid(event)

        if event.event_type == EventType.CHANNEL_MESSAGE.name:
            await self.run_command(typing.cast('EventChannelMessage', event))

        if event.event_type == EventType.CUSTOM_REWARD.name:
            await self._custom_reward(event)

    async def _follow(self, event: QueueEvent) -> None:
        logger.info('donat.event _follow')
        if event.message:
            await self.chat(event.message)

    async def _subscribe(self, event: QueueEvent) -> None:
        logger.info('donat.event _subscribe')
        if event.message:
            await self.chat(event.message)

    async def _resubscribe(self, event: QueueEvent) -> None:
        logger.info('donat.event _resubscribe')
        if event.message:
            await self.chat(event.message)

    async def _channel_raid(self, event: QueueEvent) -> None:
        logger.info('donat.event _channel_raid')
        if event.message:
            await self.chat(event.message)

    async def _custom_reward(self, event: QueueEvent) -> None:
        logger.info('donat.event _custom_reward %s', event)
        if event.message:
            await self.chat(event.message)

    async def run_command(self, event: EventChannelMessage) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        logger.debug('Running command for event %s', event)
        for command_name, command in self.commands.items():
            if (
                event
                and event.message
                and event.message.startswith(command_name.lower())
            ):
                logger.debug('detected command: %s', command)
                command_to_run = command
                mssg = await command_to_run.run(event)
                if mssg:
                    await self.chat(mssg)
