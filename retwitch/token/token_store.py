from dataclasses import dataclass, asdict
import typing
import json

from pathlib import Path

from retwitch.token import TokenResponse
from retwitch.schemas.token import TokenResponseSchema
from retwitch.utils import logger_setup


logger = logger_setup(__name__)


@dataclass
class TokenStore:
    token_file: str

    def save_real_token(self, token: TokenResponse) -> None:
        path = Path(self.token_file)
        with path.open(mode='w') as f:
            json.dump(asdict(token), f)

    def load_real_token(self) -> TokenResponse | None:
        path = Path(self.token_file)
        new_token: TokenResponse | None = None
        if path.exists():
            with path.open(mode='r') as f:
                logger.info('loading_token file from %s', self.token_file)
                new_token = typing.cast(
                    'TokenResponse', TokenResponseSchema().load(json.load(f))
                )
        return new_token
