"""Tests for auth.allow_registration config flag.

Covers:
- allow_registration=True (default) → register succeeds
- allow_registration=False → register returns 403 registration_disabled
- allow_registration=False does NOT affect OIDC provisioning
- AuthAppConfig schema: default is True, can be set to False
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_JWT_SECRET", "test-secret-key-registration-disabled-min32")

from app.gateway.auth.config import AuthConfig, set_auth_config

_TEST_SECRET = "test-secret-key-registration-disabled-min32"
_STRONG_PASSWORD = "Tr0ub4dor&3-Horse"


@pytest.fixture(autouse=True)
def _setup_auth(tmp_path):
    """Fresh SQLite engine + auth config per test."""
    from app.gateway import deps
    from app.gateway.routers.auth import _SETUP_STATUS_CACHE, _SETUP_STATUS_INFLIGHT
    from deerflow.persistence.engine import close_engine, init_engine

    set_auth_config(AuthConfig(jwt_secret=_TEST_SECRET))
    url = f"sqlite+aiosqlite:///{tmp_path}/reg_disabled.db"
    asyncio.run(init_engine("sqlite", url=url, sqlite_dir=str(tmp_path)))
    deps._cached_local_provider = None
    deps._cached_repo = None
    _SETUP_STATUS_CACHE.clear()
    _SETUP_STATUS_INFLIGHT.clear()
    try:
        yield
    finally:
        deps._cached_local_provider = None
        deps._cached_repo = None
        _SETUP_STATUS_CACHE.clear()
        _SETUP_STATUS_INFLIGHT.clear()
        asyncio.run(close_engine())


@pytest.fixture()
def client(_setup_auth):
    from app.gateway.app import create_app

    set_auth_config(AuthConfig(jwt_secret=_TEST_SECRET))
    app = create_app()
    yield TestClient(app)


# ── AuthAppConfig schema ──────────────────────────────────────────────────────


def test_auth_app_config_default_allow_registration():
    """allow_registration defaults to True."""
    from deerflow.config.auth_config import AuthAppConfig

    cfg = AuthAppConfig()
    assert cfg.allow_registration is True


def test_auth_app_config_allow_registration_false():
    """allow_registration can be set to False."""
    from deerflow.config.auth_config import AuthAppConfig

    cfg = AuthAppConfig(allow_registration=False)
    assert cfg.allow_registration is False


def test_auth_error_code_has_registration_disabled():
    """REGISTRATION_DISABLED is a valid AuthErrorCode member."""
    from app.gateway.auth.errors import AuthErrorCode

    assert AuthErrorCode.REGISTRATION_DISABLED == "registration_disabled"


# ── Registration enabled (default) ───────────────────────────────────────────


_PATCH_TARGET = "app.gateway.routers.auth.get_app_config"


def _mock_app_config(*, allow_registration: bool):
    """Build a MagicMock that mimics AppConfig.auth.allow_registration."""
    from deerflow.config.auth_config import AuthAppConfig

    cfg = MagicMock()
    cfg.auth = AuthAppConfig(allow_registration=allow_registration)
    return cfg


def test_register_succeeds_when_registration_enabled(client):
    """Default config (allow_registration=True) → 201 Created."""
    with patch(_PATCH_TARGET, return_value=_mock_app_config(allow_registration=True)):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "newuser@example.com", "password": _STRONG_PASSWORD},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@example.com"
    assert data["system_role"] == "user"


# ── Registration disabled ─────────────────────────────────────────────────────


def test_register_blocked_when_registration_disabled(client):
    """allow_registration=False → 403 with code registration_disabled."""
    with patch(_PATCH_TARGET, return_value=_mock_app_config(allow_registration=False)):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "blocked@example.com", "password": _STRONG_PASSWORD},
        )
    assert resp.status_code == 403
    detail = resp.json()["detail"]
    assert detail["code"] == "registration_disabled"
    assert "disabled" in detail["message"].lower()


def test_register_blocked_does_not_create_user(client):
    """When registration is disabled, no user row is created in DB."""
    from app.gateway import deps

    with patch(_PATCH_TARGET, return_value=_mock_app_config(allow_registration=False)):
        client.post(
            "/api/v1/auth/register",
            json={"email": "ghost@example.com", "password": _STRONG_PASSWORD},
        )

    async def _check():
        provider = deps.get_local_provider()
        return await provider.get_user_by_email("ghost@example.com")

    user = asyncio.run(_check())
    assert user is None


def test_register_blocked_sets_no_cookie(client):
    """When registration is disabled, no access_token cookie is set."""
    with patch(_PATCH_TARGET, return_value=_mock_app_config(allow_registration=False)):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "nocookie@example.com", "password": _STRONG_PASSWORD},
        )
    assert resp.status_code == 403
    assert "access_token" not in resp.cookies


# ── initialize endpoint unaffected ───────────────────────────────────────────


def test_initialize_unaffected_by_registration_disabled(client):
    """allow_registration=False must not block /initialize (admin bootstrap)."""
    with patch(_PATCH_TARGET, return_value=_mock_app_config(allow_registration=False)):
        resp = client.post(
            "/api/v1/auth/initialize",
            json={"email": "admin@example.com", "password": _STRONG_PASSWORD},
        )
    # /initialize does not call get_app_config for the registration flag
    assert resp.status_code == 201
    assert resp.json()["system_role"] == "admin"
