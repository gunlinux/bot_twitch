from retwitch.models.events import RetwitchEvent
from requeue.fstream.models import FQueueEvent, FQueueMessage


def retwitch_to_queue(
    retwitch_event: RetwitchEvent, source: str = 'retwitch_getter'
) -> FQueueMessage:
    event_type = retwitch_event.event_type.name
    return FQueueMessage(
        event=event_type,
        source=source,
        data=FQueueEvent(
            event_type=event_type,
            billing_system=None,
            user_name=retwitch_event.user_name,
            amount=None,
            currency=None,
            message=retwitch_event.message,
            event=retwitch_event.event,
        ),
    )
