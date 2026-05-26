import pytest
import asyncio
from unittest.mock import AsyncMock
from retwitch.command_registry import CommandRegistry
from retwitch.models.commands import Command
from requeue.fstream.models import FQueueEvent


def _make_event() -> FQueueEvent:
    return FQueueEvent(event_type='channel.chat.message', message='!auf')


def test_register_auto_prefixes_with_bang():
    reg = CommandRegistry()
    cmd = Command(name='auf', real_runner=None, data={'text': 'ауф!'})
    reg.register(cmd)
    assert 'auf' in reg.commands
    assert '!auf' in reg.commands


def test_register_dollar_prefix_not_duplicated():
    reg = CommandRegistry()
    cmd = Command(name='$reset', real_runner=AsyncMock())
    reg.register(cmd)
    assert '$reset' in reg.commands
    assert '!$reset' not in reg.commands


def test_register_bang_prefix_not_duplicated():
    reg = CommandRegistry()
    cmd = Command(name='!cmd', real_runner=None, data={'text': 'hi'})
    reg.register(cmd)
    assert '!cmd' in reg.commands
    assert '!!cmd' not in reg.commands


def test_get_command_case_insensitive():
    reg = CommandRegistry()
    cmd = Command(name='!auf', real_runner=None, data={'text': 'ауф!'})
    reg.register(cmd)
    assert reg._get_command('!AUF') is cmd
    assert reg._get_command('!auf something') is cmd


def test_get_command_unknown_returns_none():
    reg = CommandRegistry()
    assert reg._get_command('!unknown') is None


def test_get_command_empty_string_returns_none():
    reg = CommandRegistry()
    assert reg._get_command('') is None


def test_clear_raw_commands_keeps_real_commands():
    reg = CommandRegistry()
    runner = AsyncMock()
    real_cmd = Command(name='!real', real_runner=runner)
    raw_cmd = Command(name='!raw', real_runner=None, data={'text': 'raw'})
    reg.register(real_cmd)
    reg.register(raw_cmd)
    reg.clear_raw_commands()
    assert '!real' in reg.commands
    assert '!raw' not in reg.commands


@pytest.mark.asyncio
async def test_run_raw_command_returns_text():
    reg = CommandRegistry()
    cmd = Command(name='!hello', real_runner=None, data={'text': 'world'})
    reg.register(cmd)
    event = _make_event()
    result = await reg.run('!hello', event)
    assert result == 'world'


@pytest.mark.asyncio
async def test_run_real_command():
    reg = CommandRegistry()
    runner = AsyncMock(return_value='pong')
    cmd = Command(name='!ping', real_runner=runner)
    reg.register(cmd)
    event = _make_event()
    result = await reg.run('!ping', event)
    assert result == 'pong'
    runner.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_run_unknown_command_returns_empty():
    reg = CommandRegistry()
    event = _make_event()
    result = await reg.run('!nope', event)
    assert result == ''


@pytest.mark.asyncio
async def test_run_empty_message_returns_empty():
    reg = CommandRegistry()
    event = _make_event()
    result = await reg.run('', event)
    assert result == ''
