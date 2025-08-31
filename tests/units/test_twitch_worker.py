import logging
import json
import typing


logger = logging.getLogger(name=__name__)

from requeue.schemas import QueueMessageSchema, QueueEvent


async def test_retwitch_event_schema():
    event = """ {"event": "CHANNEL_MESSAGE", "data": {"event_type": "CHANNEL_MESSAGE", "billing_system": null, "user_name": "gunlinux", "amount": null, "currency": null, "message": "asdas", "event": {"text": "asdas", "message_type": "text", "reply": null, "channel_points_custom_reward_id": null}}, "source": "retwitch_getter", "retry": 0, "status": 1}
    """
    queue_event = typing.cast(
        'QueueEvent', QueueMessageSchema().load(json.loads(event))
    )
    assert queue_event
    assert queue_event.event == 'CHANNEL_MESSAGE'
