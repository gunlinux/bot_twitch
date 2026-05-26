import time
from dataclasses import dataclass, field


@dataclass(repr=False)
class TokenResponse:
    access_token: str
    expires_in: int
    token_type: str
    refresh_token: str = ''
    last_updated: float = field(default_factory=lambda: time.time())

    def __repr__(self) -> str:
        def _mask(s: str) -> str:
            return f'***{s[-4:]}' if len(s) >= 4 else '***'  # noqa: PLR2004

        return (
            f'TokenResponse(token_type={self.token_type!r},'
            f' expires_in={self.expires_in},'
            f' access_token={_mask(self.access_token)!r},'
            f' refresh_token={_mask(self.refresh_token)!r})'
        )
