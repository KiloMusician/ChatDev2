"""Tests for plugin_api.py and observability_api.py endpoints.

Covers:
- GET /plugins/list  (with registry, without registry)
- POST /plugins/register  (with registry, without registry, duplicate)
- GET /observability/tracing_status  (tracing disabled, tracing enabled, provider present)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Plugin API helpers
# ---------------------------------------------------------------------------


def _make_plugin_app(registry=None) -> FastAPI:
    """Build a minimal FastAPI app for plugin_api with an injectable registry."""
    from src.api import plugin_api

    app = FastAPI()
    # Patch the module-level _registry before including the router
    with patch.object(plugin_api, "_registry", registry):
        app.include_router(plugin_api.router, prefix="/api")
    return app


def _plugin_client(registry=None) -> TestClient:
    from src.api import plugin_api

    app = FastAPI()
    app.include_router(plugin_api.router, prefix="/api")
    client = TestClient(app)
    # Inject the registry directly on the imported module so the route closures pick it up
    plugin_api._registry = registry
    return client, plugin_api


# ---------------------------------------------------------------------------
# Plugin API — list_plugins
# ---------------------------------------------------------------------------


class TestListPlugins:
    def test_list_plugins_with_empty_registry(self):
        from src.api import plugin_api
        from src.plugins.plugin_registry import PluginRegistry

        registry = PluginRegistry()
        app = FastAPI()
        app.include_router(plugin_api.router, prefix="/api")
        original = plugin_api._registry
        plugin_api._registry = registry
        try:
            client = TestClient(app)
            resp = client.get("/api/plugins/list")
            assert resp.status_code == 200
            data = resp.json()
            assert data == {"plugins": []}
        finally:
            plugin_api._registry = original

    def test_list_plugins_with_registered_plugins(self):
        from src.api import plugin_api
        from src.plugins.plugin_registry import PluginRegistry

        registry = PluginRegistry()
        registry.register("my_plugin", object())
        registry.register("another_plugin", object())

        app = FastAPI()
        app.include_router(plugin_api.router, prefix="/api")
        original = plugin_api._registry
        plugin_api._registry = registry
        try:
            client = TestClient(app)
            resp = client.get("/api/plugins/list")
            assert resp.status_code == 200
            data = resp.json()
            assert "plugins" in data
            assert "my_plugin" in data["plugins"]
            assert "another_plugin" in data["plugins"]
        finally:
            plugin_api._registry = original

    def test_list_plugins_no_registry(self):
        from src.api import plugin_api

        app = FastAPI()
        app.include_router(plugin_api.router, prefix="/api")
        original = plugin_api._registry
        plugin_api._registry = None
        try:
            client = TestClient(app)
            resp = client.get("/api/plugins/list")
            assert resp.status_code == 200
            data = resp.json()
            assert "error" in data
            assert "not available" in data["error"].lower()
        finally:
            plugin_api._registry = original


# ---------------------------------------------------------------------------
# Plugin API — register_plugin
# ---------------------------------------------------------------------------


class TestRegisterPlugin:
    def test_register_plugin_success(self):
        from src.api import plugin_api
        from src.plugins.plugin_registry import PluginRegistry

        registry = PluginRegistry()
        app = FastAPI()
        app.include_router(plugin_api.router, prefix="/api")
        original = plugin_api._registry
        plugin_api._registry = registry
        try:
            client = TestClient(app)
            resp = client.post("/api/plugins/register?name=test_plugin")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["plugin"] == "test_plugin"
        finally:
            plugin_api._registry = original

    def test_register_plugin_appears_in_list(self):
        from src.api import plugin_api
        from src.plugins.plugin_registry import PluginRegistry

        registry = PluginRegistry()
        app = FastAPI()
        app.include_router(plugin_api.router, prefix="/api")
        original = plugin_api._registry
        plugin_api._registry = registry
        try:
            client = TestClient(app)
            client.post("/api/plugins/register?name=new_plugin")
            resp = client.get("/api/plugins/list")
            assert resp.status_code == 200
            data = resp.json()
            assert "new_plugin" in data["plugins"]
        finally:
            plugin_api._registry = original

    def test_register_plugin_no_registry(self):
        from src.api import plugin_api

        app = FastAPI()
        app.include_router(plugin_api.router, prefix="/api")
        original = plugin_api._registry
        plugin_api._registry = None
        try:
            client = TestClient(app)
            resp = client.post("/api/plugins/register?name=x")
            assert resp.status_code == 200
            data = resp.json()
            assert "error" in data
            assert "not available" in data["error"].lower()
        finally:
            plugin_api._registry = original

    def test_register_duplicate_plugin_raises(self):
        """Re-registering the same name without override=True raises ValueError
        inside the registry. The endpoint uses registry.register() with no
        override flag, so a second call for the same name raises.
        """
        from src.api import plugin_api
        from src.plugins.plugin_registry import PluginRegistry

        registry = PluginRegistry()
        app = FastAPI()
        app.include_router(plugin_api.router, prefix="/api")
        original = plugin_api._registry
        plugin_api._registry = registry
        try:
            client = TestClient(app)
            client.post("/api/plugins/register?name=dup_plugin")
            # Second registration should raise — TestClient propagates as 500
            client_no_raise = TestClient(app, raise_server_exceptions=False)
            resp = client_no_raise.post("/api/plugins/register?name=dup_plugin")
            assert resp.status_code == 500
        finally:
            plugin_api._registry = original

    def test_register_plugin_missing_name_query_param(self):
        from src.api import plugin_api

        app = FastAPI()
        app.include_router(plugin_api.router, prefix="/api")
        client = TestClient(app)
        resp = client.post("/api/plugins/register")
        # name is required Query param; FastAPI returns 422 Unprocessable Entity
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Observability API — tracing_status
# ---------------------------------------------------------------------------


class TestTracingStatus:
    def _make_obs_app(self) -> tuple[TestClient, Any]:
        from src.api import observability_api

        app = FastAPI()
        app.include_router(observability_api.router, prefix="/api")
        client = TestClient(app)
        return client, observability_api

    def test_tracing_status_no_module(self):
        """When tracing module is None, returns enabled=False."""
        from src.api import observability_api

        app = FastAPI()
        app.include_router(observability_api.router, prefix="/api")
        original = observability_api.tracing
        observability_api.tracing = None
        try:
            client = TestClient(app)
            resp = client.get("/api/observability/tracing_status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["enabled"] is False
            assert "error" in data
        finally:
            observability_api.tracing = original

    def test_tracing_status_module_has_no_enabled_attr(self):
        """Module present but lacks tracing_enabled → disabled."""
        from src.api import observability_api

        mock_tracing = MagicMock(spec=[])  # no attributes
        app = FastAPI()
        app.include_router(observability_api.router, prefix="/api")
        original = observability_api.tracing
        observability_api.tracing = mock_tracing
        try:
            client = TestClient(app)
            resp = client.get("/api/observability/tracing_status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["enabled"] is False
        finally:
            observability_api.tracing = original

    def test_tracing_status_disabled(self):
        """When tracing_enabled() returns False, trace_id/span_id are n/a."""
        from src.api import observability_api

        mock_tracing = MagicMock()
        mock_tracing.tracing_enabled.return_value = False
        del mock_tracing._PROVIDER  # no provider

        app = FastAPI()
        app.include_router(observability_api.router, prefix="/api")
        original = observability_api.tracing
        observability_api.tracing = mock_tracing
        try:
            client = TestClient(app)
            resp = client.get("/api/observability/tracing_status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["enabled"] is False
            assert data["trace_id"] == "n/a"
            assert data["span_id"] == "n/a"
        finally:
            observability_api.tracing = original

    def test_tracing_status_enabled(self):
        """When tracing_enabled() returns True, trace_id and span_id are populated."""
        from src.api import observability_api

        mock_tracing = MagicMock()
        mock_tracing.tracing_enabled.return_value = True
        mock_tracing.current_trace_ids.return_value = ("abc123", "span456")
        mock_tracing._PROVIDER = None

        app = FastAPI()
        app.include_router(observability_api.router, prefix="/api")
        original = observability_api.tracing
        observability_api.tracing = mock_tracing
        try:
            client = TestClient(app)
            resp = client.get("/api/observability/tracing_status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["enabled"] is True
            assert data["trace_id"] == "abc123"
            assert data["span_id"] == "span456"
        finally:
            observability_api.tracing = original

    def test_tracing_status_enabled_with_provider(self):
        """When _PROVIDER exists, its class name is reported as exporter."""
        from src.api import observability_api

        class FakeProvider:
            pass

        mock_tracing = MagicMock()
        mock_tracing.tracing_enabled.return_value = True
        mock_tracing.current_trace_ids.return_value = ("tid", "sid")
        mock_tracing._PROVIDER = FakeProvider()

        app = FastAPI()
        app.include_router(observability_api.router, prefix="/api")
        original = observability_api.tracing
        observability_api.tracing = mock_tracing
        try:
            client = TestClient(app)
            resp = client.get("/api/observability/tracing_status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["enabled"] is True
            assert data["exporter"] == "FakeProvider"
        finally:
            observability_api.tracing = original

    def test_tracing_status_provider_raises(self):
        """If accessing _PROVIDER raises, exporter is None (graceful degradation)."""
        from src.api import observability_api

        mock_tracing = MagicMock()
        mock_tracing.tracing_enabled.return_value = True
        mock_tracing.current_trace_ids.return_value = ("t", "s")

        # Make _PROVIDER access raise an AttributeError
        type(mock_tracing)._PROVIDER = property(lambda self: (_ for _ in ()).throw(RuntimeError("boom")))

        app = FastAPI()
        app.include_router(observability_api.router, prefix="/api")
        original = observability_api.tracing
        observability_api.tracing = mock_tracing
        try:
            client = TestClient(app)
            resp = client.get("/api/observability/tracing_status")
            assert resp.status_code == 200
            data = resp.json()
            # exporter should be None when accessing it raises
            assert data["exporter"] is None
        finally:
            observability_api.tracing = original
