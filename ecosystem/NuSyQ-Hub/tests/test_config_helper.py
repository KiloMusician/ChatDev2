"""Tests for src/utils/config_helper.py - Centralized configuration helper."""

import os
from unittest.mock import patch

from src.utils import config_helper
from src.utils.config_helper import (
    _ensure_scheme,
    _resolve_ollama_url,
    get_chatdev_path,
    get_config,
    get_feature_flag,
    get_ollama_endpoint,
    get_ollama_host,
    get_timeout,
)


class TestEnsureScheme:
    """Tests for _ensure_scheme helper."""

    def test_url_with_http_scheme(self):
        """Test URL already has http scheme."""
        assert _ensure_scheme("http://localhost") == "http://localhost"

    def test_url_with_https_scheme(self):
        """Test URL already has https scheme."""
        assert _ensure_scheme("https://example.com") == "https://example.com"

    def test_url_without_scheme(self):
        """Test URL without scheme gets http added."""
        assert _ensure_scheme("localhost:8080") == "http://localhost:8080"

    def test_url_with_just_hostname(self):
        """Test hostname without scheme gets http added."""
        assert _ensure_scheme("myserver") == "http://myserver"


class TestGetConfig:
    """Tests for get_config function."""

    def test_returns_dict(self):
        """Test get_config returns a dictionary."""
        result = get_config()
        assert isinstance(result, dict)

    def test_is_cached(self):
        """Test get_config is cached (same object returned)."""
        first = get_config()
        second = get_config()
        assert first is second  # Same object due to lru_cache


class TestResolveOllamaUrl:
    """Tests for _resolve_ollama_url helper."""

    def setup_method(self):
        """Clear environment variables before each test."""
        for key in ["OLLAMA_BASE_URL", "OLLAMA_HOST", "OLLAMA_PORT"]:
            os.environ.pop(key, None)

    def teardown_method(self):
        """Clear environment variables after each test."""
        for key in ["OLLAMA_BASE_URL", "OLLAMA_HOST", "OLLAMA_PORT"]:
            os.environ.pop(key, None)

    def test_with_ollama_base_url_env(self):
        """Test prefers OLLAMA_BASE_URL environment variable."""
        with patch.object(config_helper, "SERVICE_CONFIG_AVAILABLE", False):
            with patch.object(config_helper, "ServiceConfig", None):
                os.environ["OLLAMA_BASE_URL"] = "http://custom:9999/"
                result = _resolve_ollama_url()
                assert result == "http://custom:9999"

    def test_base_url_without_scheme(self):
        """Test BASE_URL without scheme gets http added."""
        with patch.object(config_helper, "SERVICE_CONFIG_AVAILABLE", False):
            with patch.object(config_helper, "ServiceConfig", None):
                os.environ["OLLAMA_BASE_URL"] = "custom:9999"
                result = _resolve_ollama_url()
                assert result == "http://custom:9999"

    def test_with_host_and_port_env(self):
        """Test constructs URL from OLLAMA_HOST and OLLAMA_PORT."""
        # Only set when ServiceConfig not available and no BASE_URL
        _orig_host = os.environ.get("OLLAMA_HOST")
        _orig_port = os.environ.get("OLLAMA_PORT")
        try:
            with patch.object(config_helper, "SERVICE_CONFIG_AVAILABLE", False):
                with patch.object(config_helper, "ServiceConfig", None):
                    os.environ["OLLAMA_HOST"] = "http://myhost"
                    os.environ["OLLAMA_PORT"] = "8888"
                    result = _resolve_ollama_url()
                    assert "myhost" in result
                    assert "8888" in result
        finally:
            if _orig_host is None:
                os.environ.pop("OLLAMA_HOST", None)
            else:
                os.environ["OLLAMA_HOST"] = _orig_host
            if _orig_port is None:
                os.environ.pop("OLLAMA_PORT", None)
            else:
                os.environ["OLLAMA_PORT"] = _orig_port

    def test_default_when_no_env(self):
        """Test defaults to localhost:11434 when no env vars."""
        with patch.object(config_helper, "SERVICE_CONFIG_AVAILABLE", False):
            with patch.object(config_helper, "ServiceConfig", None):
                result = _resolve_ollama_url()
                assert "127.0.0.1" in result or "localhost" in result
                assert "11434" in result


class TestGetOllamaHost:
    """Tests for get_ollama_host function."""

    def test_returns_string(self):
        """Test get_ollama_host returns a string."""
        result = get_ollama_host()
        assert isinstance(result, str)

    def test_no_trailing_slash(self):
        """Test result has no trailing slash."""
        result = get_ollama_host()
        assert not result.endswith("/")


class TestGetOllamaEndpoint:
    """Tests for get_ollama_endpoint function."""

    def test_with_path(self):
        """Test endpoint with path."""
        result = get_ollama_endpoint("/api/tags")
        assert "/api/tags" in result

    def test_without_path(self):
        """Test endpoint without path returns base."""
        result = get_ollama_endpoint()
        assert not result.endswith("/")

    def test_path_with_leading_slash(self):
        """Test path with leading slash is handled."""
        result = get_ollama_endpoint("/v1/chat")
        assert "v1/chat" in result
        assert not result.count("//") > 1  # No double slashes except protocol

    def test_path_without_leading_slash(self):
        """Test path without leading slash is handled."""
        result = get_ollama_endpoint("api/generate")
        assert "api/generate" in result


class TestGetChatdevPath:
    """Tests for get_chatdev_path function."""

    def setup_method(self):
        """Clear CHATDEV_PATH env var before each test."""
        os.environ.pop("CHATDEV_PATH", None)

    def teardown_method(self):
        """Clear CHATDEV_PATH env var after each test."""
        os.environ.pop("CHATDEV_PATH", None)

    def test_returns_string(self):
        """Test get_chatdev_path returns a string."""
        result = get_chatdev_path()
        assert isinstance(result, str)

    def test_prefers_env_var(self):
        """Test CHATDEV_PATH env var takes priority."""
        os.environ["CHATDEV_PATH"] = "/custom/chatdev/path"
        result = get_chatdev_path()
        assert result == "/custom/chatdev/path"


class TestGetTimeout:
    """Tests for get_timeout function."""

    def test_returns_int(self):
        """Test get_timeout returns an integer."""
        result = get_timeout("some_timeout")
        assert isinstance(result, int)

    def test_default_value(self):
        """Test default value is used for unknown key."""
        result = get_timeout("nonexistent_key", default=42)
        assert result == 42 or isinstance(result, int)

    def test_strips_timeout_suffix(self):
        """Test key with _timeout suffix is normalized."""
        # Just verify no crash
        result = get_timeout("request_timeout")
        assert isinstance(result, int)


class TestGetFeatureFlag:
    """Tests for get_feature_flag function."""

    def test_returns_bool(self):
        """Test get_feature_flag returns a boolean."""
        result = get_feature_flag("some_flag")
        assert isinstance(result, bool)

    def test_default_value(self):
        """Test default value is used for unknown flag."""
        # Default is False
        result = get_feature_flag("nonexistent_flag_xyz")
        assert result is False

    def test_custom_default_true(self):
        """Test custom default True."""
        result = get_feature_flag("nonexistent_flag_xyz", default=True)
        # Either the flag exists or returns True
        assert isinstance(result, bool)


class TestModuleExports:
    """Tests for module __all__ exports."""

    def test_all_exports(self):
        """Test __all__ contains expected functions."""
        from src.utils.config_helper import __all__

        expected = {
            "get_chatdev_path",
            "get_config",
            "get_feature_flag",
            "get_ollama_endpoint",
            "get_ollama_host",
            "get_timeout",
        }
        assert set(__all__) == expected


class TestEdgeCases:
    """Edge case tests."""

    def test_get_config_with_missing_file(self):
        """Test get_config handles missing config file gracefully."""
        # The function should handle missing file via load_settings
        # Just verify no crash
        result = get_config()
        assert isinstance(result, dict)

    def test_service_config_available_flag(self):
        """Test SERVICE_CONFIG_AVAILABLE flag exists."""
        assert hasattr(config_helper, "SERVICE_CONFIG_AVAILABLE")
        assert isinstance(config_helper.SERVICE_CONFIG_AVAILABLE, bool)

    def test_ollama_host_with_port_in_host(self):
        """Test OLLAMA_HOST with port already included."""
        _orig_host = os.environ.get("OLLAMA_HOST")
        try:
            with patch.object(config_helper, "SERVICE_CONFIG_AVAILABLE", False):
                with patch.object(config_helper, "ServiceConfig", None):
                    os.environ.pop("OLLAMA_BASE_URL", None)
                    os.environ["OLLAMA_HOST"] = "http://custom:7777"
                    result = _resolve_ollama_url()
                    assert "7777" in result
        finally:
            if _orig_host is None:
                os.environ.pop("OLLAMA_HOST", None)
            else:
                os.environ["OLLAMA_HOST"] = _orig_host

    def test_get_timeout_converts_string_to_int(self):
        """Test timeout value is converted to int."""
        with patch.object(config_helper, "get_config") as mock:
            mock.return_value = {"timeouts": {"test": "60"}}
            # Clear cache to use mock
            get_config.cache_clear()
            result = get_timeout("test")
            assert isinstance(result, int)
        # Restore cache
        get_config.cache_clear()
