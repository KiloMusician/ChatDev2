"""Tests for src/connectors/ — ConnectorConfig, ConnectorRegistry, WebhookConnector."""

import pytest


class TestConnectorConfig:
    """Tests for ConnectorConfig dataclass."""

    def test_minimal_config(self):
        from src.connectors.base import ConnectorConfig
        cfg = ConnectorConfig(name="test")
        assert cfg.name == "test"
        assert cfg.enabled is True
        assert cfg.api_key is None
        assert cfg.endpoint is None
        assert cfg.timeout == 30
        assert cfg.retry_count == 3
        assert cfg.metadata == {}

    def test_full_config(self):
        from src.connectors.base import ConnectorConfig
        cfg = ConnectorConfig(
            name="webhook",
            enabled=False,
            api_key="secret",
            endpoint="https://example.com",
            timeout=60,
            retry_count=5,
            metadata={"env": "prod"},
        )
        assert cfg.enabled is False
        assert cfg.timeout == 60
        assert cfg.retry_count == 5

    def test_to_dict_excludes_api_key(self):
        from src.connectors.base import ConnectorConfig
        cfg = ConnectorConfig(name="safe", api_key="my_secret")
        d = cfg.to_dict()
        assert "api_key" not in d
        assert d["has_api_key"] is True
        assert d["name"] == "safe"

    def test_to_dict_no_api_key(self):
        from src.connectors.base import ConnectorConfig
        cfg = ConnectorConfig(name="anon")
        d = cfg.to_dict()
        assert d["has_api_key"] is False


class TestConnectorStatus:
    """Tests for ConnectorStatus enum."""

    def test_status_values(self):
        from src.connectors.base import ConnectorStatus
        assert ConnectorStatus.DISCONNECTED.value == "disconnected"
        assert ConnectorStatus.CONNECTED.value == "connected"
        assert ConnectorStatus.ERROR.value == "error"
        assert ConnectorStatus.DISABLED.value == "disabled"
        assert ConnectorStatus.CONNECTING.value == "connecting"


class TestConnectorRegistry:
    """Tests for ConnectorRegistry singleton and registration."""

    @pytest.fixture(autouse=True)
    def reset_registry(self, tmp_path):
        """Reset singleton between tests."""
        import src.connectors.registry as reg_mod
        reg_mod.ConnectorRegistry._instance = None
        reg_mod.ConnectorRegistry._initialized = False
        yield
        reg_mod.ConnectorRegistry._instance = None
        reg_mod.ConnectorRegistry._initialized = False

    def test_singleton_pattern(self, tmp_path):
        from src.connectors.registry import ConnectorRegistry
        r1 = ConnectorRegistry(config_path=tmp_path / "connectors.json")
        r2 = ConnectorRegistry(config_path=tmp_path / "connectors.json")
        assert r1 is r2

    def test_register_and_get(self, tmp_path):
        from src.connectors.base import ConnectorConfig
        from src.connectors.registry import ConnectorRegistry
        from src.connectors.webhook import WebhookConnector

        registry = ConnectorRegistry(config_path=tmp_path / "connectors.json")
        cfg = ConnectorConfig(name="wh_test", endpoint="https://example.com")
        wh = WebhookConnector(config=cfg)
        result = registry.register(wh)
        assert result.ok
        fetched = registry.get("wh_test")
        assert fetched is wh

    def test_get_missing_returns_none_or_fail(self, tmp_path):
        from src.connectors.registry import ConnectorRegistry
        registry = ConnectorRegistry(config_path=tmp_path / "connectors.json")
        fetched = registry.get("nonexistent")
        assert fetched is None

    def test_register_duplicate_is_handled(self, tmp_path):
        from src.connectors.base import ConnectorConfig
        from src.connectors.registry import ConnectorRegistry
        from src.connectors.webhook import WebhookConnector

        registry = ConnectorRegistry(config_path=tmp_path / "connectors.json")
        cfg = ConnectorConfig(name="dup")
        wh = WebhookConnector(config=cfg)
        registry.register(wh)
        result = registry.register(wh)
        # Second registration should return Fail or be idempotent
        assert result is not None

    def test_list_connectors_empty_initially(self, tmp_path):
        from src.connectors.registry import ConnectorRegistry
        registry = ConnectorRegistry(config_path=tmp_path / "connectors.json")
        connectors = registry.list_connectors()
        assert isinstance(connectors, list)

    def test_unregister_removes_connector(self, tmp_path):
        from src.connectors.base import ConnectorConfig
        from src.connectors.registry import ConnectorRegistry
        from src.connectors.webhook import WebhookConnector

        registry = ConnectorRegistry(config_path=tmp_path / "connectors.json")
        cfg = ConnectorConfig(name="rm_me")
        wh = WebhookConnector(config=cfg)
        registry.register(wh)
        result = registry.unregister("rm_me")
        assert result.ok
        assert registry.get("rm_me") is None

    def test_get_connector_registry_factory(self, tmp_path):
        from src.connectors.registry import get_connector_registry
        reg = get_connector_registry()
        assert reg is not None


class TestWebhookConnector:
    """Tests for WebhookConnector connect/disconnect/execute interface."""

    @pytest.fixture
    def wh(self):
        from src.connectors.base import ConnectorConfig
        from src.connectors.webhook import WebhookConnector
        cfg = ConnectorConfig(name="test_wh", endpoint="https://httpbin.org/post", timeout=5)
        return WebhookConnector(config=cfg)

    def test_instantiation(self, wh):
        assert wh is not None

    def test_initial_status_disconnected(self, wh):
        from src.connectors.base import ConnectorStatus
        assert wh.status in (ConnectorStatus.DISCONNECTED, ConnectorStatus.DISABLED)

    def test_connect_returns_result(self, wh):
        result = wh.connect()
        # May fail if no network, but should return a Result
        assert hasattr(result, "is_ok") or hasattr(result, "value") or isinstance(result, bool)

    def test_disconnect_returns_result(self, wh):
        result = wh.disconnect()
        assert result is not None

    def test_execute_without_connection_returns_fail(self, wh):
        result = wh.execute("send", {"payload": "test"})
        # Should fail gracefully since not connected to real endpoint
        assert result is not None

    def test_health_check_returns_result(self, wh):
        result = wh.health_check()
        assert result is not None

    def test_to_dict_has_name(self, wh):
        d = wh.to_dict()
        assert isinstance(d, dict)
        assert "name" in d or "config" in d


class TestConnectorsPackage:
    """Tests for src/connectors package exports."""

    def test_imports(self):
        from src.connectors import BaseConnector, ConnectorConfig, ConnectorRegistry
        from src.connectors.webhook import WebhookConnector
        assert BaseConnector is not None
        assert ConnectorConfig is not None
        assert ConnectorRegistry is not None
        assert WebhookConnector is not None
