import json
import pytest
from requeue.rredis import RedisConnection, BotConnectionError
from requeue.models import QueueMessageStatus


async def test_redis_failes():
    r = RedisConnection('')
    name_q = 'some_q'
    with pytest.raises(BotConnectionError):
        await r.clean(name_q)

    with pytest.raises(BotConnectionError):
        await r.pop(name_q)

    payload1 = {
        'event': 'Test event 1',
        'data': json.dumps({'kinda': 1}),
        'source': 'test_queue',
        'retry': 0,
        'status': QueueMessageStatus.WAITING.value,
    }

    with pytest.raises(BotConnectionError):
        await r.push(name_q, data=json.dumps(payload1))

    with pytest.raises(BotConnectionError):
        await r.llen('message')

    with pytest.raises(BotConnectionError):
        await r.walk(name_q)
