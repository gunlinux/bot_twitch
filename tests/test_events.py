from retwitch.models.events import (
    EventType,
    create_event_from_subevent,
    EventChannelMessage,
    EventChannelFollow,
    EventRaid,
    EventChannelSubscribe,
    EventChannelResubscribeMessage,
    EventCustomReward,
    EventWatchStreak,
)


def _make_event(sub_type: str, payload_event: dict) -> dict:
    return {
        'metadata': {
            'message_id': 'test-id',
            'message_type': 'notification',
            'message_timestamp': '2024-01-01T00:00:00Z',
            'subscription_type': sub_type,
            'subscription_version': '1',
        },
        'payload': {
            'event': payload_event,
        },
    }


def test_unknown_subscription_type_returns_none():
    data = _make_event('channel.unknown_event', {})
    assert create_event_from_subevent(data) is None


def test_missing_subscription_type_returns_none():
    data = {
        'metadata': {
            'message_type': 'notification',
            'message_id': 'x',
            'message_timestamp': 'x',
        },
        'payload': {'event': {}},
    }
    assert create_event_from_subevent(data) is None


def test_channel_message_event():
    data = _make_event(
        EventType.CHANNEL_MESSAGE,
        {
            'chatter_user_id': 'u1',
            'chatter_user_login': 'user',
            'chatter_user_name': 'User',
            'message': {'text': 'hello'},
            'message_type': 'chat',
        },
    )
    event = create_event_from_subevent(data)
    assert isinstance(event, EventChannelMessage)
    assert event.message == 'hello'
    assert event.user_login == 'user'


def test_channel_message_missing_message_field():
    data = _make_event(
        EventType.CHANNEL_MESSAGE,
        {
            'chatter_user_id': 'u1',
            'chatter_user_login': 'user',
            'chatter_user_name': 'User',
            'message_type': 'chat',
        },
    )
    event = create_event_from_subevent(data)
    assert isinstance(event, EventChannelMessage)
    assert event.message == ''


def test_channel_follow_event():
    data = _make_event(
        EventType.CHANNEL_FOLLOW,
        {'user_id': 'u2', 'user_login': 'follower', 'user_name': 'Follower'},
    )
    event = create_event_from_subevent(data)
    assert isinstance(event, EventChannelFollow)
    assert event.message == 'Follower followed channel'


def test_channel_raid_event():
    data = _make_event(
        EventType.CHANNEL_RAID,
        {
            'from_broadcaster_user_id': 'r1',
            'from_broadcaster_user_login': 'raider',
            'from_broadcaster_user_name': 'Raider',
            'viewers': 42,
        },
    )
    event = create_event_from_subevent(data)
    assert isinstance(event, EventRaid)
    assert event.message == 'Raider just raid channel with 42'


def test_channel_subscribe_event():
    data = _make_event(
        EventType.CHANNEL_SUBSCRIBE,
        {
            'user_id': 'u3',
            'user_login': 'sub',
            'user_name': 'Sub',
            'tier': '1000',
            'is_gift': False,
        },
    )
    event = create_event_from_subevent(data)
    assert isinstance(event, EventChannelSubscribe)
    assert '1000' in event.message


def test_channel_resubscribe_event():
    data = _make_event(
        EventType.CHANNEL_RESUBSCRIBE,
        {
            'user_id': 'u4',
            'user_login': 'resub',
            'user_name': 'Resub',
            'tier': '1000',
            'message': {'text': 'love this stream'},
            'cumulative_months': 6,
            'duration_months': 1,
        },
    )
    event = create_event_from_subevent(data)
    assert isinstance(event, EventChannelResubscribeMessage)
    assert 'love this stream' in event.message


def test_channel_resubscribe_missing_message():
    data = _make_event(
        EventType.CHANNEL_RESUBSCRIBE,
        {
            'user_id': 'u4',
            'user_login': 'resub',
            'user_name': 'Resub',
            'tier': '1000',
            'cumulative_months': 3,
            'duration_months': 1,
        },
    )
    event = create_event_from_subevent(data)
    assert isinstance(event, EventChannelResubscribeMessage)
    assert event.message is not None


def test_custom_reward_event():
    data = _make_event(
        EventType.CUSTOM_REWARD,
        {
            'user_id': 'u5',
            'user_login': 'redeemer',
            'user_name': 'Redeemer',
            'status': 'fulfilled',
            'user_input': '',
            'reward': {'title': 'Hydrate', 'cost': 100},
        },
    )
    event = create_event_from_subevent(data)
    assert isinstance(event, EventCustomReward)
    assert 'Hydrate' in event.message


def test_watch_streak_event():
    data = _make_event(
        EventType.CHANNEL_CHAT_NOTIFICATION,
        {
            'chatter_user_id': 'u6',
            'chatter_user_login': 'streaker',
            'chatter_user_name': 'Streaker',
            'notice_type': 'watch_streak',
            'system_message': 'Streaker watched 10 consecutive streams!',
            'watch_streak': {'watch_streak_months': 10},
        },
    )
    event = create_event_from_subevent(data)
    assert isinstance(event, EventWatchStreak)
    assert event.message == 'Streaker watched 10 consecutive streams!'
    assert event.user_login == 'streaker'


def test_watch_streak_event_missing_system_message():
    data = _make_event(
        EventType.CHANNEL_CHAT_NOTIFICATION,
        {
            'chatter_user_id': 'u6',
            'chatter_user_login': 'streaker',
            'chatter_user_name': 'Streaker',
            'notice_type': 'watch_streak',
            'watch_streak': {'watch_streak_months': 7},
        },
    )
    event = create_event_from_subevent(data)
    assert isinstance(event, EventWatchStreak)
    assert '7' in event.message


def test_chat_notification_other_notice_type_returns_none():
    data = _make_event(
        EventType.CHANNEL_CHAT_NOTIFICATION,
        {
            'chatter_user_id': 'u7',
            'chatter_user_login': 'subber',
            'chatter_user_name': 'Subber',
            'notice_type': 'sub',
            'system_message': 'Subber subscribed!',
        },
    )
    assert create_event_from_subevent(data) is None
