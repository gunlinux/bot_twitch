import pytest
from unittest.mock import AsyncMock
from retwitch.handlers import RetwitchEventHandler
from retwitch.command_registry import CommandRegistry
from retwitch.models.commands import Command
from requeue.fstream.models import FQueueEvent
from retwitch.schemas.events import EventType


def _make_event(event_type: str, message: str = '') -> FQueueEvent:
    return FQueueEvent(event_type=event_type, message=message)


def _make_handler(admin: str = 'admin') -> tuple[RetwitchEventHandler, AsyncMock]:
    sender = AsyncMock()
    sender.send_message = AsyncMock()
    registry = CommandRegistry()
    handler = RetwitchEventHandler(
        sender=sender,
        admin=admin,
        command_registry=registry,
        command_dir='',
    )
    return handler, sender


@pytest.mark.asyncio
async def test_channel_message_routes_to_run_command():
    handler, sender = _make_handler()
    runner = AsyncMock(return_value='response')
    handler.register(Command('!cmd', real_runner=runner))
    event = _make_event(EventType.CHANNEL_MESSAGE.name, '!cmd')
    await handler.handle_event(event)
    runner.assert_called_once()
    sender.send_message.assert_called_once_with('response')


@pytest.mark.asyncio
async def test_channel_message_no_command_sends_nothing():
    handler, sender = _make_handler()
    event = _make_event(EventType.CHANNEL_MESSAGE.name, 'just chatting')
    await handler.handle_event(event)
    sender.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_non_message_event_routes_to_chat_notify():
    handler, sender = _make_handler()
    event = _make_event(EventType.CHANNEL_FOLLOW.name, 'SomeUser followed channel')
    await handler.handle_event(event)
    sender.send_message.assert_called_once_with('SomeUser followed channel')


@pytest.mark.asyncio
async def test_unknown_event_type_no_op():
    handler, sender = _make_handler()
    event = _make_event('unknown.event.type', 'something')
    await handler.handle_event(event)
    sender.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_chat_notify_skips_empty_message():
    handler, sender = _make_handler()
    event = _make_event(EventType.CHANNEL_FOLLOW.name, '')
    await handler.handle_event(event)
    sender.send_message.assert_not_called()
