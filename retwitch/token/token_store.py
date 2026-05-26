from dataclasses import dataclass, asdict
import typing
import json
import os

from pathlib import Path

from retwitch.models import TokenResponse
from retwitch.schemas.token import TokenResponseSchema
from retwitch.utils import logger_setup


logger = logger_setup(__name__)


@dataclass
class TokenStore:
    token_file: str

    def save_real_token(self, token: TokenResponse) -> None:
        path = Path(self.token_file)
        tmp_path = path.with_suffix('.tmp')
        with tmp_path.open(mode='w') as f:
            json.dump(asdict(token), f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)

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
