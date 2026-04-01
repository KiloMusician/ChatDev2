"""Tests for SkyclawGatewayClient.

Covers:
- Instantiation with defaults and custom base_url
- binary_info() key presence and shape
- summary() when gateway responds HTTP 200 (mocked aiohttp session)
- summary() when gateway is unreachable → running=False
- get_skyclaw_gateway_client() singleton: same instance on repeated calls

Isolation note: the module-level ``_client`` singleton is reset via
monkeypatch so tests do not bleed state into one another.
"""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.integrations.skyclaw_gateway_client as _sc_module
from src.integrations.skyclaw_gateway_client import (
    SkyclawGatewayClient,
    get_skyclaw_gateway_client,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    """Reset the module-level _client singleton before every test so
    get_skyclaw_gateway_client() always creates a fresh instance.
    """
    monkeypatch.setattr(_sc_module, "_client", None)
    yield
    monkeypatch.setattr(_sc_module, "_client", None)


def _make_aiohttp_response(status: int, json_data: dict[str, Any]) -> MagicMock:
    """Return a mock aiohttp response context-manager with json() as AsyncMock."""
    resp = MagicMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def _make_aiohttp_session(get_response: MagicMock) -> MagicMock:
    """Return a mock aiohttp.ClientSession whose .get() yields *get_response*."""
    session = MagicMock()
    session.get = MagicMock(return_value=get_response)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


# ---------------------------------------------------------------------------
# 1. Instantiation — default URL
# ---------------------------------------------------------------------------


def test_instantiation_default_url():
    """SkyclawGatewayClient created without arguments uses the module default URL."""
    client = SkyclawGatewayClient()
    # Default is http://127.0.0.1:8080 (or env-driven; just confirm it's non-empty
    # and starts with http).
    assert client.gateway_url.startswith("http")
    assert client.gateway_url  # non-empty string


# ---------------------------------------------------------------------------
# 2. Instantiation — custom base_url
# ---------------------------------------------------------------------------


def test_instantiation_custom_url():
    """Providing a custom gateway_url overrides the default."""
    custom = "http://10.0.0.1:9999"
    client = SkyclawGatewayClient(gateway_url=custom)
    assert client.gateway_url == custom


def test_instantiation_custom_url_strips_trailing_slash():
    """Trailing slashes are stripped from the provided gateway URL."""
    client = SkyclawGatewayClient(gateway_url="http://10.0.0.1:9999/")
    assert client.gateway_url == "http://10.0.0.1:9999"


# ---------------------------------------------------------------------------
# 3. binary_info() — key presence
# ---------------------------------------------------------------------------


def test_binary_info_not_found_returns_found_false(monkeypatch):
    """When no binary exists, binary_info() returns {'found': False}."""
    client = SkyclawGatewayClient()
    monkeypatch.setattr(client, "_binary", None)
    info = client.binary_info()
    assert info == {"found": False}


def test_binary_info_found_has_required_keys(tmp_path, monkeypatch):
    """When a binary is found, binary_info() includes found, path, needs_wsl,
    platform.
    """
    # Create a fake binary file so the path "exists"
    fake_binary = tmp_path / "skyclaw.exe"
    fake_binary.write_bytes(b"")

    client = SkyclawGatewayClient()
    monkeypatch.setattr(client, "_binary", fake_binary)

    info = client.binary_info()

    assert info["found"] is True
    assert "path" in info
    assert "needs_wsl" in info
    assert "platform" in info
    assert info["platform"] == sys.platform


def test_binary_info_path_matches_binary(tmp_path, monkeypatch):
    """binary_info()['path'] matches str(self._binary)."""
    fake_binary = tmp_path / "skyclaw"
    fake_binary.write_bytes(b"")

    client = SkyclawGatewayClient()
    monkeypatch.setattr(client, "_binary", fake_binary)

    info = client.binary_info()
    assert info["path"] == str(fake_binary)


# ---------------------------------------------------------------------------
# 4. summary() — gateway responds HTTP 200
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summary_when_gateway_running():
    """summary() returns running=True and populates health/status when the
    gateway responds with HTTP 200 on both /health and /status.
    """
    health_payload = {"status": "ok", "version": "0.5.0", "uptime_seconds": 42}
    status_payload = {
        "status": "ok",
        "version": "0.5.0",
        "provider": "anthropic",
        "channels": ["cli"],
        "tools": ["shell"],
        "memory_backend": "sqlite",
    }

    health_resp = _make_aiohttp_response(200, health_payload)
    status_resp = _make_aiohttp_response(200, status_payload)

    # The client calls session.get() multiple times — return different responses
    # per endpoint.  We intercept at the ClientSession level.

    def _get_side_effect(url, **kwargs):
        # Return health_resp for /health, status_resp for /status
        if "/health" in url:
            return health_resp
        return status_resp

    session_mock = MagicMock()
    session_mock.get = MagicMock(side_effect=_get_side_effect)
    session_mock.__aenter__ = AsyncMock(return_value=session_mock)
    session_mock.__aexit__ = AsyncMock(return_value=False)

    client = SkyclawGatewayClient(gateway_url="http://127.0.0.1:8080")

    with patch("aiohttp.ClientSession", return_value=session_mock):
        result = await client.summary()

    assert result["running"] is True
    assert result["gateway_url"] == "http://127.0.0.1:8080"
    assert result["health"] is not None
    assert result["health"]["version"] == "0.5.0"
    assert result["status"] is not None
    assert result["status"]["provider"] == "anthropic"
    assert "binary" in result


# ---------------------------------------------------------------------------
# 5. summary() — gateway unreachable
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summary_when_gateway_unreachable():
    """summary() returns running=False when aiohttp raises ClientConnectorError."""
    import aiohttp

    client = SkyclawGatewayClient(gateway_url="http://127.0.0.1:8080")

    # Patch aiohttp.ClientSession so that session.get() raises a connection error.
    session_mock = MagicMock()
    conn_err = aiohttp.ClientConnectorError(
        connection_key=MagicMock(ssl=False),
        os_error=OSError("connection refused"),
    )
    session_mock.get = MagicMock(side_effect=conn_err)
    session_mock.__aenter__ = AsyncMock(return_value=session_mock)
    session_mock.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=session_mock):
        result = await client.summary()

    assert result["running"] is False
    assert result["health"] is None
    assert result["status"] is None
    assert result["gateway_url"] == "http://127.0.0.1:8080"


# ---------------------------------------------------------------------------
# 6. get_skyclaw_gateway_client() — singleton behaviour
# ---------------------------------------------------------------------------


def test_get_skyclaw_gateway_client_returns_instance():
    """get_skyclaw_gateway_client() returns a SkyclawGatewayClient."""
    client = get_skyclaw_gateway_client()
    assert isinstance(client, SkyclawGatewayClient)


def test_get_skyclaw_gateway_client_singleton_same_object():
    """Calling get_skyclaw_gateway_client() twice returns the exact same object."""
    first = get_skyclaw_gateway_client()
    second = get_skyclaw_gateway_client()
    assert first is second


def test_get_skyclaw_gateway_client_url_override_on_first_call():
    """The url override is applied only on first call; subsequent calls ignore it."""
    custom_url = "http://192.168.1.100:7777"
    first = get_skyclaw_gateway_client(gateway_url=custom_url)
    assert first.gateway_url == custom_url

    # Second call — override ignored, same object returned
    second = get_skyclaw_gateway_client(gateway_url="http://ignored:1111")
    assert second is first
    assert second.gateway_url == custom_url
