"""Tests for OllamaServiceManager, observability_api, and plugin_api."""

from __future__ import annotations

import json
import sys
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.services.ollama_service_manager import (
    OllamaEnvironment,
    OllamaServiceManager,
    OllamaStatus,
    ensure_ollama,
    get_ollama_status,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_http_response(body: dict, status: int = 200) -> MagicMock:
    raw = json.dumps(body).encode()
    resp = MagicMock()
    resp.read.return_value = raw
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _make_completed(returncode: int = 0, stdout: str = "") -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    return result


# ---------------------------------------------------------------------------
# OllamaStatus.to_dict
# ---------------------------------------------------------------------------


class TestOllamaStatusToDict:
    def test_healthy_status_serialises(self):
        s = OllamaStatus(
            healthy=True,
            environment=OllamaEnvironment.NATIVE_WINDOWS,
            models_available=3,
            latency_ms=42.7,
        )
        d = s.to_dict()
        assert d["healthy"] is True
        assert d["environment"] == "native_windows"
        assert d["models_available"] == 3
        assert d["latency_ms"] == 42.7

    def test_none_latency_serialises_as_none(self):
        s = OllamaStatus(healthy=False, environment=OllamaEnvironment.UNAVAILABLE)
        assert s.to_dict()["latency_ms"] is None

    def test_error_field_included(self):
        s = OllamaStatus(healthy=False, environment=OllamaEnvironment.WSL, error="connection refused")
        assert s.to_dict()["error"] == "connection refused"

    def test_wsl_relay_stale_field(self):
        s = OllamaStatus(healthy=False, environment=OllamaEnvironment.WSL, wsl_relay_stale=True)
        assert s.to_dict()["wsl_relay_stale"] is True


# ---------------------------------------------------------------------------
# OllamaServiceManager.check_health
# ---------------------------------------------------------------------------


class TestCheckHealth:
    def test_healthy_when_urlopen_succeeds(self):
        mgr = OllamaServiceManager()
        resp = _make_http_response({"models": [{"name": "llama3"}, {"name": "mistral"}]})
        with patch("urllib.request.urlopen", return_value=resp):
            status = mgr.check_health()
        assert status.healthy is True
        assert status.models_available == 2
        assert status.latency_ms is not None

    def test_zero_models_still_healthy(self):
        mgr = OllamaServiceManager()
        resp = _make_http_response({"models": []})
        with patch("urllib.request.urlopen", return_value=resp):
            status = mgr.check_health()
        assert status.healthy is True
        assert status.models_available == 0

    def test_unhealthy_when_urlopen_raises(self):
        mgr = OllamaServiceManager()
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            with patch.object(mgr, "_check_wsl_relay_stale", return_value=False):
                status = mgr.check_health()
        assert status.healthy is False
        assert "connection refused" in (status.error or "")

    def test_wsl_relay_stale_flag_set_on_failure(self):
        mgr = OllamaServiceManager()
        with patch("urllib.request.urlopen", side_effect=OSError("abort")):
            with patch.object(mgr, "_check_wsl_relay_stale", return_value=True):
                status = mgr.check_health()
        assert status.wsl_relay_stale is True
        assert "WSL relay stale" in status.detail

    def test_last_status_cached(self):
        mgr = OllamaServiceManager()
        resp = _make_http_response({"models": []})
        with patch("urllib.request.urlopen", return_value=resp):
            mgr.check_health()
        assert mgr._last_status is not None
        assert mgr._last_status.healthy is True

    def test_environment_attached_to_status(self):
        mgr = OllamaServiceManager()
        mgr._environment = OllamaEnvironment.DOCKER
        resp = _make_http_response({"models": []})
        with patch("urllib.request.urlopen", return_value=resp):
            status = mgr.check_health()
        assert status.environment == OllamaEnvironment.DOCKER


# ---------------------------------------------------------------------------
# OllamaServiceManager.is_healthy
# ---------------------------------------------------------------------------


class TestIsHealthy:
    def test_returns_true_when_healthy(self):
        mgr = OllamaServiceManager()
        resp = _make_http_response({"models": [{"name": "m1"}]})
        with patch("urllib.request.urlopen", return_value=resp):
            assert mgr.is_healthy() is True

    def test_returns_false_when_offline(self):
        mgr = OllamaServiceManager()
        with patch("urllib.request.urlopen", side_effect=OSError("offline")):
            with patch.object(mgr, "_check_wsl_relay_stale", return_value=False):
                assert mgr.is_healthy() is False


# ---------------------------------------------------------------------------
# OllamaServiceManager.detect_environment
# ---------------------------------------------------------------------------


class TestDetectEnvironment:
    def test_cached_environment_returned(self):
        mgr = OllamaServiceManager()
        mgr._environment = OllamaEnvironment.DOCKER
        assert mgr.detect_environment() == OllamaEnvironment.DOCKER

    def test_native_windows_when_ollama_in_path(self):
        mgr = OllamaServiceManager()
        with patch("shutil.which", return_value="/usr/bin/ollama"):
            with patch.object(OllamaServiceManager, "_is_wsl_runtime", return_value=False):
                env = mgr.detect_environment()
        assert env == OllamaEnvironment.NATIVE_WINDOWS

    def test_wsl_when_running_inside_wsl_with_ollama_in_path(self):
        mgr = OllamaServiceManager()
        with patch("shutil.which", return_value="/usr/bin/ollama"):
            with patch.object(OllamaServiceManager, "_is_wsl_runtime", return_value=True):
                env = mgr.detect_environment()
        assert env == OllamaEnvironment.WSL

    def test_docker_when_docker_ps_finds_ollama(self):
        mgr = OllamaServiceManager()
        wsl_fail = _make_completed(returncode=1, stdout="")
        docker_ok = _make_completed(returncode=0, stdout="ollama\n")
        # First subprocess.run call is the WSL "which ollama" probe; second is docker ps
        with patch("shutil.which", return_value=None):
            with patch.object(OllamaServiceManager, "_is_wsl_runtime", return_value=False):
                with patch("os.environ.get", return_value=""):
                    with patch("pathlib.Path.exists", return_value=False):
                        with patch("subprocess.run", side_effect=[wsl_fail, docker_ok]):
                            env = mgr.detect_environment()
        assert env == OllamaEnvironment.DOCKER

    def test_unavailable_when_nothing_found(self):
        mgr = OllamaServiceManager()
        failed = _make_completed(returncode=1, stdout="")
        with patch("shutil.which", return_value=None):
            with patch.object(OllamaServiceManager, "_is_wsl_runtime", return_value=False):
                with patch("os.environ.get", return_value=""):
                    with patch("pathlib.Path.exists", return_value=False):
                        with patch("subprocess.run", return_value=failed):
                            env = mgr.detect_environment()
        assert env == OllamaEnvironment.UNAVAILABLE


# ---------------------------------------------------------------------------
# OllamaServiceManager.ensure_running
# ---------------------------------------------------------------------------


class TestEnsureRunning:
    def test_returns_true_when_already_healthy(self):
        mgr = OllamaServiceManager()
        resp = _make_http_response({"models": []})
        with patch("urllib.request.urlopen", return_value=resp):
            result = mgr.ensure_running()
        assert result is True

    def test_attempts_start_when_unhealthy(self):
        mgr = OllamaServiceManager()
        with patch("urllib.request.urlopen", side_effect=OSError("down")):
            with patch.object(mgr, "_check_wsl_relay_stale", return_value=False):
                with patch.object(mgr, "start", return_value=True) as mock_start:
                    result = mgr.ensure_running()
        mock_start.assert_called_once()
        assert result is True

    def test_passes_wsl_stale_flag_to_start(self):
        mgr = OllamaServiceManager()
        with patch("urllib.request.urlopen", side_effect=OSError("stale")):
            with patch.object(mgr, "_check_wsl_relay_stale", return_value=True):
                with patch.object(mgr, "start", return_value=False) as mock_start:
                    mgr.ensure_running()
        mock_start.assert_called_once_with(force_wsl_restart=True)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    def test_ensure_ollama_returns_bool(self):
        with patch("urllib.request.urlopen", side_effect=OSError("offline")):
            with patch.object(OllamaServiceManager, "_check_wsl_relay_stale", return_value=False):
                with patch.object(OllamaServiceManager, "start", return_value=False):
                    result = ensure_ollama()
        assert isinstance(result, bool)

    def test_get_ollama_status_returns_status(self):
        resp = _make_http_response({"models": [{"name": "qwen"}]})
        with patch("urllib.request.urlopen", return_value=resp):
            s = get_ollama_status()
        assert isinstance(s, OllamaStatus)
        assert s.models_available == 1


# ---------------------------------------------------------------------------
# OllamaServiceManager.start (unit)
# ---------------------------------------------------------------------------


class TestStart:
    def test_returns_false_when_unavailable(self):
        mgr = OllamaServiceManager()
        mgr._environment = OllamaEnvironment.UNAVAILABLE
        with patch("urllib.request.urlopen", side_effect=OSError("down")):
            with patch.object(mgr, "_check_wsl_relay_stale", return_value=False):
                result = mgr.start()
        assert result is False

    def test_skips_start_when_already_healthy(self):
        mgr = OllamaServiceManager()
        mgr._environment = OllamaEnvironment.NATIVE_WINDOWS
        resp = _make_http_response({"models": []})
        with patch("urllib.request.urlopen", return_value=resp):
            with patch.object(mgr, "_start_native_windows") as mock_start:
                result = mgr.start()
        mock_start.assert_not_called()
        assert result is True


# ---------------------------------------------------------------------------
# Observability API
# ---------------------------------------------------------------------------


def _make_observability_app(tracing_mock) -> TestClient:
    import src.api.observability_api as obs_mod
    original = obs_mod.tracing
    obs_mod.tracing = tracing_mock
    app = FastAPI()
    app.include_router(obs_mod.router)
    client = TestClient(app)
    obs_mod.tracing = original
    return client


class TestObservabilityAPI:
    def test_tracing_disabled_when_module_none(self):
        import src.api.observability_api as obs_mod
        original = obs_mod.tracing
        obs_mod.tracing = None
        try:
            app = FastAPI()
            app.include_router(obs_mod.router)
            client = TestClient(app)
            resp = client.get("/observability/tracing_status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["enabled"] is False
        finally:
            obs_mod.tracing = original

    def test_tracing_disabled_when_tracing_enabled_falsy(self):
        import src.api.observability_api as obs_mod
        original = obs_mod.tracing
        mock_tracing = SimpleNamespace(tracing_enabled=None)
        obs_mod.tracing = mock_tracing
        try:
            app = FastAPI()
            app.include_router(obs_mod.router)
            client = TestClient(app)
            resp = client.get("/observability/tracing_status")
            assert resp.status_code == 200
            assert resp.json()["enabled"] is False
        finally:
            obs_mod.tracing = original

    def test_tracing_enabled_returns_trace_ids(self):
        import src.api.observability_api as obs_mod
        original = obs_mod.tracing
        mock_tracing = SimpleNamespace(
            tracing_enabled=lambda: True,
            current_trace_ids=lambda: ("abc123", "span456"),
            _PROVIDER=None,
        )
        obs_mod.tracing = mock_tracing
        try:
            app = FastAPI()
            app.include_router(obs_mod.router)
            client = TestClient(app)
            resp = client.get("/observability/tracing_status")
            data = resp.json()
            assert data["enabled"] is True
            assert data["trace_id"] == "abc123"
            assert data["span_id"] == "span456"
        finally:
            obs_mod.tracing = original

    def test_tracing_disabled_returns_na_trace_ids(self):
        import src.api.observability_api as obs_mod
        original = obs_mod.tracing
        mock_tracing = SimpleNamespace(
            tracing_enabled=lambda: False,
            current_trace_ids=lambda: ("real", "real"),
            _PROVIDER=None,
        )
        obs_mod.tracing = mock_tracing
        try:
            app = FastAPI()
            app.include_router(obs_mod.router)
            client = TestClient(app)
            resp = client.get("/observability/tracing_status")
            data = resp.json()
            assert data["enabled"] is False
            assert data["trace_id"] == "n/a"
        finally:
            obs_mod.tracing = original

    def test_exporter_class_name_extracted(self):
        import src.api.observability_api as obs_mod
        original = obs_mod.tracing

        class FakeProvider:
            pass

        mock_tracing = SimpleNamespace(
            tracing_enabled=lambda: True,
            current_trace_ids=lambda: ("t1", "s1"),
            _PROVIDER=FakeProvider(),
        )
        obs_mod.tracing = mock_tracing
        try:
            app = FastAPI()
            app.include_router(obs_mod.router)
            client = TestClient(app)
            resp = client.get("/observability/tracing_status")
            assert resp.json()["exporter"] == "FakeProvider"
        finally:
            obs_mod.tracing = original

    def test_exporter_none_when_provider_absent(self):
        import src.api.observability_api as obs_mod
        original = obs_mod.tracing
        mock_tracing = SimpleNamespace(
            tracing_enabled=lambda: True,
            current_trace_ids=lambda: ("t", "s"),
        )
        obs_mod.tracing = mock_tracing
        try:
            app = FastAPI()
            app.include_router(obs_mod.router)
            client = TestClient(app)
            resp = client.get("/observability/tracing_status")
            assert resp.json()["exporter"] is None
        finally:
            obs_mod.tracing = original


# ---------------------------------------------------------------------------
# Plugin API
# ---------------------------------------------------------------------------


@pytest.fixture()
def plugin_client():
    import src.api.plugin_api as plugin_mod
    from src.plugins.plugin_registry import PluginRegistry
    reg = PluginRegistry()
    original = plugin_mod._registry
    plugin_mod._registry = reg
    app = FastAPI()
    app.include_router(plugin_mod.router)
    client = TestClient(app)
    yield client, reg
    plugin_mod._registry = original


class TestPluginAPI:
    def test_list_plugins_empty_registry(self, plugin_client):
        client, _reg = plugin_client
        resp = client.get("/plugins/list")
        assert resp.status_code == 200
        assert resp.json() == {"plugins": []}

    def test_list_plugins_shows_registered(self, plugin_client):
        client, reg = plugin_client
        reg.register("alpha", object())
        reg.register("beta", object())
        resp = client.get("/plugins/list")
        data = resp.json()
        assert set(data["plugins"]) == {"alpha", "beta"}

    def test_register_plugin_via_api(self, plugin_client):
        client, _reg = plugin_client
        resp = client.post("/plugins/register?name=my_plugin")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["plugin"] == "my_plugin"

    def test_registered_plugin_appears_in_list(self, plugin_client):
        client, _reg = plugin_client
        client.post("/plugins/register?name=new_one")
        resp = client.get("/plugins/list")
        assert "new_one" in resp.json()["plugins"]

    def test_list_returns_error_when_registry_none(self):
        import src.api.plugin_api as plugin_mod
        original = plugin_mod._registry
        plugin_mod._registry = None
        try:
            app = FastAPI()
            app.include_router(plugin_mod.router)
            client = TestClient(app)
            resp = client.get("/plugins/list")
            assert "error" in resp.json()
        finally:
            plugin_mod._registry = original

    def test_register_returns_error_when_registry_none(self):
        import src.api.plugin_api as plugin_mod
        original = plugin_mod._registry
        plugin_mod._registry = None
        try:
            app = FastAPI()
            app.include_router(plugin_mod.router)
            client = TestClient(app)
            resp = client.post("/plugins/register?name=anything")
            assert "error" in resp.json()
        finally:
            plugin_mod._registry = original

    def test_double_register_same_name_raises(self, plugin_client):
        _client, reg = plugin_client
        reg.register("dup", object())
        with pytest.raises(ValueError):
            reg.register("dup", object())
