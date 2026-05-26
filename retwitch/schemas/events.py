from marshmallow import Schema, fields, validate, INCLUDE

from retwitch.models.events import EventType


class RetwitchEventSchema(Schema):
    event_type = fields.Enum(EventType, by_value=True, required=True)
    user_id = fields.Str(required=False, allow_none=True)
    user_login = fields.Str(required=False, allow_none=True)
    user_name = fields.Str(required=False, allow_none=True)
    event = fields.Dict(
        keys=fields.Str(), values=fields.Raw(allow_none=True), allow_none=True
    )

    class Meta:
        unknown = INCLUDE


class MetadataSchema(Schema):
    message_id = fields.Str(required=True)
    message_type = fields.Str(
        required=True,
        validate=validate.OneOf(
            [
                'session_welcome',
                'notification',
                'session_keepalive',
                'session_reconnect',
                'revocation',
            ]
        ),
    )
    message_timestamp = fields.DateTime(required=True)

    # Optional fields for notification type
    subscription_type = fields.Str(required=False)
    subscription_version = fields.Str(required=False)

    class Meta:
        unknown = INCLUDE


class SessionSchema(Schema):
    id = fields.Str(required=True)
    status = fields.Str(
        required=True,
        validate=validate.OneOf(['connected', 'disconnected', 'reconnecting']),
    )
    connected_at = fields.DateTime(required=True)
    keepalive_timeout_seconds = fields.Int(required=False, allow_none=True)
    reconnect_url = fields.Str(required=False, allow_none=True)
    recovery_url = fields.Str(required=False, allow_none=True)

    class Meta:
        unknown = INCLUDE


class PayloadSchema(Schema):
    session = fields.Nested(SessionSchema, required=False)

    # Add other possible payload fields here if needed
    class Meta:
        unknown = INCLUDE


class EventSchema(Schema):
    metadata = fields.Nested(MetadataSchema, required=True)
    payload = fields.Nested(PayloadSchema, required=True)

    class Meta:
        unknown = INCLUDE
