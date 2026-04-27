import logging
import typing
import time

from retwitch.token.token_store import TokenStore
from retwitch.token.token_oauth import TwitchAuth
from retwitch.token.exceptions import TokenUnsetError

if typing.TYPE_CHECKING:
    from retwitch.models import TokenResponse


REFRESH_TOKEN_DELTA: int = 6000
logger: logging.Logger = logging.getLogger(name='retwitch')


class TokenManager:
    def __init__(
        self,
        token_store: TokenStore,
        twitch_auth: TwitchAuth,
    ):
        self._token_store = token_store
        self.twitch_auth = twitch_auth
        self._token: TokenResponse | None = None

    @property
    def client_id(self) -> str:
        return self.twitch_auth.client_id

    async def get_access_token(self) -> str:
        if not self._token:
            raise TokenUnsetError
        if (
            self._token.last_updated + self._token.expires_in - time.time()
        ) < REFRESH_TOKEN_DELTA:
            logger.warning('token close to die, time to refresh')
            self._token = await self.twitch_auth.refresh_token(self._token)
            self.save_real_token()
        return self._token.access_token

    async def get_token_from_code(self, code: str) -> None:
        """
        получаем могучий токен
        """
        self._token = await self.twitch_auth.get_token_from_code(code=code)

    async def refresh_token(self) -> None:
        if not self._token:
            raise TokenUnsetError
        self._token = await self.twitch_auth.refresh_token(self._token)

    async def revoke(self, client_id: str | None = None) -> None:
        if not self._token:
            raise TokenUnsetError
        await self.twitch_auth.revoke(client_id=client_id, token=self._token)

    def save_real_token(self) -> None:
        if not self._token:
            raise TokenUnsetError
        self._token_store.save_real_token(self._token)

    def load_real_token(self) -> None:
        self._token = self._token_store.load_real_token()

    def generate_code_url(self) -> str:
        return self.twitch_auth.generate_code_url()
