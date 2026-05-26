import time
from dataclasses import dataclass, field


@dataclass(repr=False)
class TokenResponse:
    access_token: str
    expires_in: int
    token_type: str
    refresh_token: str = ''
    last_updated: float = field(default_factory=lambda: time.time())
