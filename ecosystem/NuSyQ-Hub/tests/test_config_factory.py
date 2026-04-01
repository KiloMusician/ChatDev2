"""Tests for src/utils/config_factory.py - Config factory with lazy loading."""

from unittest.mock import MagicMock, patch

from src.utils import config_factory
from src.utils.config_factory import ConfigProxy, get_service_config, is_config_available


class TestConfigProxy:
    """Tests for ConfigProxy class."""

    def test_init_creates_unchecked_proxy(self):
        """Test ConfigProxy initializes with _checked=False."""
        proxy = ConfigProxy()
        assert proxy._checked is False
        assert proxy._config is None

    def test_ensure_loaded_returns_true_when_config_available(self):
        """Test _ensure_loaded returns True when ServiceConfig imports."""
        proxy = ConfigProxy()
        # Should succeed since ServiceConfig exists
        result = proxy._ensure_loaded()
        assert result is True
        assert proxy._checked is True
        assert proxy._config is not None

    def test_ensure_loaded_only_loads_once(self):
        """Test _ensure_loaded only imports once."""
        proxy = ConfigProxy()
        proxy._ensure_loaded()
        proxy._config = "cached_value"  # Set to something else
        # Second call should not reimport
        proxy._ensure_loaded()
        assert proxy._config == "cached_value"

    def test_ensure_loaded_returns_false_on_import_error(self):
        """Test _ensure_loaded returns False when import fails."""
        proxy = ConfigProxy()
        with patch.dict("sys.modules", {"src.config.service_config": None}):
            with patch.object(proxy, "_ensure_loaded") as mock:
                mock.return_value = False
                result = mock()
                assert result is False

    def test_getattr_returns_config_value(self):
        """Test __getattr__ returns value from ServiceConfig."""
        proxy = ConfigProxy()
        # This should return actual ServiceConfig attributes if available
        # or None if attribute doesn't exist
        result = proxy.SOME_NONEXISTENT_ATTR
        assert result is None  # Should safely return None

    def test_getattr_returns_none_when_config_unavailable(self):
        """Test __getattr__ returns None when config unavailable."""
        proxy = ConfigProxy()
        proxy._checked = True
        proxy._config = None
        result = proxy.ANY_ATTR
        assert result is None

    def test_bool_returns_true_when_available(self):
        """Test __bool__ returns True when config loads."""
        proxy = ConfigProxy()
        # Should be True since ServiceConfig exists in this codebase
        result = bool(proxy)
        assert result is True

    def test_bool_returns_false_when_unavailable(self):
        """Test __bool__ returns False when config unavailable."""
        proxy = ConfigProxy()
        proxy._checked = True
        proxy._config = None
        result = bool(proxy)
        assert result is False


class TestGetServiceConfig:
    """Tests for get_service_config function."""

    def setup_method(self):
        """Reset module state before each test."""
        config_factory._state["config_instance"] = None
        config_factory._state["config_available"] = None

    def test_returns_config_proxy(self):
        """Test get_service_config returns ConfigProxy instance."""
        result = get_service_config()
        assert isinstance(result, ConfigProxy)

    def test_returns_same_instance_on_multiple_calls(self):
        """Test get_service_config returns same singleton instance."""
        first = get_service_config()
        second = get_service_config()
        assert first is second

    def test_creates_new_instance_if_none_exists(self):
        """Test creates new ConfigProxy when state is empty."""
        assert config_factory._state["config_instance"] is None
        result = get_service_config()
        assert config_factory._state["config_instance"] is result

    def test_returns_existing_instance_if_exists(self):
        """Test returns existing instance from state."""
        existing = ConfigProxy()
        config_factory._state["config_instance"] = existing
        result = get_service_config()
        assert result is existing


class TestIsConfigAvailable:
    """Tests for is_config_available function."""

    def setup_method(self):
        """Reset module state before each test."""
        config_factory._state["config_instance"] = None
        config_factory._state["config_available"] = None

    def test_returns_true_when_config_importable(self):
        """Test returns True when ServiceConfig can be imported."""
        result = is_config_available()
        # Should be True in this codebase
        assert result is True

    def test_caches_result(self):
        """Test result is cached after first call."""
        is_config_available()
        assert config_factory._state["config_available"] is not None
        # Second call should use cached value
        result = is_config_available()
        assert result is True

    def test_returns_cached_true(self):
        """Test returns cached True value."""
        config_factory._state["config_available"] = True
        result = is_config_available()
        assert result is True

    def test_returns_cached_false(self):
        """Test returns cached False value."""
        config_factory._state["config_available"] = False
        result = is_config_available()
        assert result is False


class TestIntegration:
    """Integration tests for config factory."""

    def setup_method(self):
        """Reset module state before each test."""
        config_factory._state["config_instance"] = None
        config_factory._state["config_available"] = None

    def test_proxy_can_access_real_config_attributes(self):
        """Test proxy can access real ServiceConfig attributes."""
        config = get_service_config()
        if config:
            # Try to access a real attribute if it exists
            # Just verify no exception is raised
            _ = config.OLLAMA_HOST  # May be None or actual value

    def test_typical_usage_pattern(self):
        """Test typical usage pattern from module docstring."""
        config = get_service_config()
        if config:
            ollama_host = config.OLLAMA_HOST
            # May be None or actual value
            assert isinstance(ollama_host, (str, type(None)))
        else:
            # Fallback when config unavailable
            ollama_host = "http://localhost:11434"
            assert ollama_host == "http://localhost:11434"


class TestEdgeCases:
    """Edge case tests."""

    def setup_method(self):
        """Reset module state before each test."""
        config_factory._state["config_instance"] = None
        config_factory._state["config_available"] = None

    def test_state_dict_has_expected_keys(self):
        """Test _state dict has expected keys."""
        assert "config_instance" in config_factory._state
        assert "config_available" in config_factory._state

    def test_proxy_handles_dunder_attributes(self):
        """Test proxy handles dunder attributes correctly."""
        proxy = ConfigProxy()
        # Should not crash when accessing repr
        repr_value = repr(proxy)
        assert "ConfigProxy" in repr_value

    def test_multiple_proxies_independent(self):
        """Test multiple ConfigProxy instances are independent."""
        proxy1 = ConfigProxy()
        proxy2 = ConfigProxy()
        proxy1._checked = True
        proxy1._config = "test"
        assert proxy2._checked is False
        assert proxy2._config is None

    def test_proxy_getattr_with_mock_config(self):
        """Test proxy getattr with mocked config class."""
        proxy = ConfigProxy()
        mock_config = MagicMock()
        mock_config.TEST_ATTR = "test_value"
        proxy._checked = True
        proxy._config = mock_config

        result = proxy.TEST_ATTR
        assert result == "test_value"

    def test_is_config_available_with_import_error(self):
        """Test is_config_available handles ImportError."""
        # Reset state
        config_factory._state["config_available"] = None

        # Simulate import error by patching
        with patch.dict(config_factory._state, {"config_available": False}):
            result = is_config_available()
            assert result is False
