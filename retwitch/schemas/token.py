import typing
from marshmallow import Schema, fields, post_load, EXCLUDE
from retwitch.models import TokenResponse


class TokenResponseSchema(Schema):
    access_token = fields.Str(required=True)
    expires_in = fields.Int(required=True)
    token_type = fields.Str(required=True)
    refresh_token = fields.Str(required=False)

    class Meta:
        unknown = EXCLUDE

    @post_load
    def create_model(self, data: dict[str, typing.Any], **_) -> TokenResponse:
        return TokenResponse(**data)
