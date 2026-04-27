from dataclasses import dataclass
import typing
from collections.abc import Mapping
from enum import StrEnum


class EventType(StrEnum):
    CHANNEL_FOLLOW = 'channel.follow'
    CHANNEL_RAID = 'channel.raid'
    CHANNEL_MESSAGE = 'channel.chat.message'
    CHANNEL_SUBSCRIBE = 'channel.subscribe'
    CHANNEL_RESUBSCRIBE = 'channel.subscription.message'
    CUSTOM_REWARD = 'channel.channel_points_custom_reward_redemption.add'


@dataclass
class RetwitchEvent:
    event_type: EventType
    user_id: str
    user_login: str
    user_name: str
    event: dict[str, typing.Any]

    @property
    def message(self) -> str | None:
        return None


class EventRaid(RetwitchEvent):
    @property
    @typing.override
    def message(self) -> str | None:
        return f'{self.user_name} just raid channel with {self.event["viewers"]}'


class EventCustomReward(RetwitchEvent):
    @property
    @typing.override
    def message(self) -> str | None:
        title = self.event.get('title', '')
        return f'{self.user_name} took reward {title}'


class EventChannelFollow(RetwitchEvent):
    @property
    @typing.override
    def message(self) -> str | None:
        return f'{self.user_name} followed channel'


class EventChannelMessage(RetwitchEvent):
    @property
    @typing.override
    def message(self) -> str | None:
        return self.event.get('text', '')


class EventChannelSubscribe(RetwitchEvent):
    @property
    @typing.override
    def message(self) -> str | None:
        return f'{self.user_name} just subscribed to channel ({self.event.get("tier")})'


class EventChannelResubscribeMessage(RetwitchEvent):
    @property
    @typing.override
    def message(self) -> str | None:
        return (
            f'{self.user_name} just resubscribed to channel '
            f'({self.event.get("tier")}) with message {self.event.get("text")}'
        )


def create_event_from_subevent(data: Mapping[str, typing.Any]) -> RetwitchEvent | None:
    sub_type = data.get('metadata', {}).get('subscription_type', None)
    event_type = EventType(sub_type)
    event = data.get('payload', {}).get('event', {})

    match event_type:
        case EventType.CHANNEL_RAID:
            return EventRaid(
                event_type=event_type,
                user_id=event['from_broadcaster_user_id'],
                user_login=event['from_broadcaster_user_login'],
                user_name=event['from_broadcaster_user_name'],
                event={'viewers': event['viewers']},
            )

        case EventType.CUSTOM_REWARD:
            return EventCustomReward(
                event_type=event_type,
                user_id=event['user_id'],
                user_login=event['user_login'],
                user_name=event['user_name'],
                event={
                    'status': event.get('status', ''),
                    'user_input': event.get('user_input', ''),
                    'title': event.get('reward', {}).get('title'),
                    'cost': event.get('reward', {}).get('cost'),
                },
            )

        case EventType.CHANNEL_FOLLOW:
            return EventChannelFollow(
                event_type=event_type,
                user_id=event['user_id'],
                user_login=event['user_login'],
                user_name=event['user_name'],
                event={},
            )
        case EventType.CHANNEL_MESSAGE:
            return EventChannelMessage(
                event_type=event_type,
                user_id=event['chatter_user_id'],
                user_login=event['chatter_user_login'],
                user_name=event['chatter_user_name'],
                event={
                    'text': event['message'].get('text', '')
                    if event.get('message')
                    else '',
                    'message_type': event.get('message_type', ''),
                    'reply': event.get('reply', None),
                    'channel_points_custom_reward_id': event.get(
                        'channel_points_custom_reward_id'
                    ),
                },
            )
        case EventType.CHANNEL_SUBSCRIBE:
            return EventChannelSubscribe(
                event_type=event_type,
                user_id=event['user_id'],
                user_login=event['user_login'],
                user_name=event['user_name'],
                event={
                    'tier': event.get('tier'),
                    'is_gift': event.get('is_gift', False),
                },
            )
        case EventType.CHANNEL_RESUBSCRIBE:
            return EventChannelResubscribeMessage(
                event_type=event_type,
                user_id=event['user_id'],
                user_login=event['user_login'],
                user_name=event['user_name'],
                event={
                    'text': event['message'].get('text', '')
                    if event.get('message')
                    else '',
                    'tier': event.get('tier'),
                    'cumulative_months': event.get('cumulative_months', 0),
                    'streak_months': event.get('streak_months'),
                    'duration_months': event.get('duration_months', 0),
                },
            )
