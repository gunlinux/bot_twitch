import pytest
import time
from unittest.mock import AsyncMock, MagicMock
from retwitch.token.token_manager import TokenManager, REFRESH_TOKEN_DELTA
from retwitch.token.exceptions import TokenUnsetError
from retwitch.models import TokenResponse


def _make_token(expires_in: int = 86400, offset: int = 0) -> TokenResponse:
    return TokenResponse(
        access_token='access',
        refresh_token='refresh',
        expires_in=expires_in,
        last_updated=time.time() - offset,
        token_type='bearer',
    )


def _make_manager(token: TokenResponse | None = None) -> tuple[TokenManager, AsyncMock]:
    store = MagicMock()
    store.save_real_token = MagicMock()
    store.load_real_token = MagicMock(return_value=token)
    auth = MagicMock()
    refreshed = _make_token()
    auth.refresh_token = AsyncMock(return_value=refreshed)
    manager = TokenManager(token_store=store, twitch_auth=auth)
    if token:
        manager._token = token
    return manager, auth


@pytest.mark.asyncio
async def test_get_access_token_raises_when_unset():
    manager, _ = _make_manager(token=None)
    with pytest.raises(TokenUnsetError):
        await manager.get_access_token()


@pytest.mark.asyncio
async def test_get_access_token_returns_token_when_fresh():
    token = _make_token(expires_in=86400, offset=0)
    manager, auth = _make_manager(token=token)
    result = await manager.get_access_token()
    assert result == 'access'
    auth.refresh_token.assert_not_called()


@pytest.mark.asyncio
async def test_get_access_token_refreshes_when_near_expiry():
    # Token expires in REFRESH_TOKEN_DELTA - 10 seconds from now
    token = _make_token(expires_in=REFRESH_TOKEN_DELTA - 10, offset=0)
    manager, auth = _make_manager(token=token)
    result = await manager.get_access_token()
    auth.refresh_token.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_token_raises_when_unset():
    manager, _ = _make_manager(token=None)
    with pytest.raises(TokenUnsetError):
        await manager.refresh_token()


@pytest.mark.asyncio
async def test_refresh_token_updates_internal_token():
    token = _make_token()
    manager, auth = _make_manager(token=token)
    await manager.refresh_token()
    auth.refresh_token.assert_called_once_with(token)
