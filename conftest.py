import typing
import logging
import os

import pytest

from requeue.rredis import Connection


logging.getLogger('asyncio').setLevel(logging.WARNING)

os.environ['TESTING'] = '1'


# Define the mock class
class MockRedis(Connection):
    def __init__(self):
        self.data: dict[str, typing.Any] = {}

    @typing.override
    async def _connect(self) -> None: ...

    @typing.override
    async def _close(self) -> None: ...

    @typing.override
    async def push(self, name: str, data: str) -> None:
        if name not in self.data:
            self.data[name] = []
        self.data[name].append(data)

    @typing.override
    async def pop(self, name: str) -> str:
        if not self.data.get(name, []):
            return ''
        return self.data[name].pop(0)

    @typing.override
    async def llen(self, name: str) -> int:
        return len(self.data[name])

    @typing.override
    async def clean(self, name: str):
        self.data[name] = []

    @typing.override
    async def walk(self, name: str) -> list[str]:
        _ = name
        return []


# Fixture to provide an instance of the mock database
@pytest.fixture
def mock_redis():
    return MockRedis()
