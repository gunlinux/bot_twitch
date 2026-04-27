import typing
from http import HTTPStatus
from collections.abc import Mapping

import aiohttp
from urllib.parse import urlencode

from retwitch.utils import logger_setup
from retwitch.schemas.token import TokenResponseSchema
from retwitch.token.exceptions import TokenRequestError

from retwitch.models import TokenResponse

logger = logger_setup(__name__)

TOKEN_URL: str = 'https://id.twitch.tv/oauth2/token'  # noqa: S105
TWITCH_AUTH: str = 'https://id.twitch.tv/oauth2/authorize'
TOKEN_REVOKE: str = 'https://id.twitch.tv/oauth2/revoke'  # noqa: S105

scopes = [
    'channel:bot',
    'channel:read:redemptions',
    'user:bot',
    'user:read:chat',
    'moderator:read:followers',
    'channel:read:subscriptions',
    'user:write:chat',
]


class TwitchAuth:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = 'https://gunlinux.ru/callback',
    ) -> None:
        self._client_id = client_id
        self._client_secret = (client_secret,)
        self._redirect_uri = redirect_uri

    @property
    def client_id(self) -> str:
        return self._client_id

    def __str__(self) -> str:
        return 'TwitchAuth'

    def __repr__(self) -> str:
        return 'TwitchAuth'

    def get_headers(self, **kwargs: dict[str, str]) -> Mapping[str, str]:
        return typing.cast(
            'Mapping[str, str]',
            {
                'Content-Type': 'application/x-www-form-urlencoded',
                **kwargs,
            },
        )

    async def _req_token(self, params: dict[str, typing.Any]) -> TokenResponse:
        logger.info('start to req')
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=TOKEN_URL, headers=self.get_headers(), params=params
            ) as resp:
                if resp.status != HTTPStatus.OK:
                    raise TokenRequestError(f'Wrong response_status: {resp.status}')  # noqa: TRY003, EM102
                return typing.cast(
                    'TokenResponse', TokenResponseSchema().load(await resp.json())
                )

    async def refresh_token(self, token: TokenResponse) -> TokenResponse:
        logger.info('refreshing token')
        params = {
            'grant_type': 'refresh_token',
            'client_id': self._client_id,
            'client_secret': self._client_secret,
            'refresh_token': token.refresh_token,
            'scope': ' '.join(scopes),
            'redirect_uri': self._redirect_uri,
        }
        return await self._req_token(params=params)

    async def revoke(self, token: TokenResponse, client_id: str | None = None) -> None:
        params = {
            'client_id': client_id or self._client_id,
            'token': token.access_token,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=TOKEN_REVOKE, headers=self.get_headers(), params=params
            ) as resp:
                logger.info('revoke: %s', resp.status)

    def generate_code_url(self) -> str:
        base_url: str = TWITCH_AUTH
        params = {
            'response_type': 'code',
            'client_id': self._client_id,
            'redirect_uri': self._redirect_uri,
            'scope': ' '.join(scopes),
            'state': 'c3ab8aa609ea11e793ae92361f002671',
        }
        query_params = urlencode(params)
        return f'{base_url}?{query_params}'

    async def get_token_from_code(self, code: str) -> TokenResponse:
        """
        получаем могучий токен
        """
        params = {
            'client_id': self._client_id,
            'code': code,
            'client_secret': self._client_secret,
            'grant_type': 'authorization_code',
            'scope': ' '.join(scopes),
            'redirect_uri': self._redirect_uri,
        }
        return await self._req_token(params=params)
