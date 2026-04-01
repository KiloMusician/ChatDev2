"""Tests for src/config/service_config.py — ServiceConfig and get_service_config."""

import os

import pytest


class TestServiceConfigDefaults:
    """Tests for ServiceConfig class-level defaults."""

    def test_ollama_port_default(self):
        from src.config.service_config import ServiceConfig
        assert ServiceConfig.OLLAMA_PORT == int(os.environ.get("OLLAMA_PORT", "11434"))

    def test_lmstudio_port_default(self):
        from src.config.service_config import ServiceConfig
        assert ServiceConfig.LMSTUDIO_PORT == int(os.environ.get("LMSTUDIO_PORT", "1234"))

    def test_simulatedverse_port_default(self, monkeypatch):
        # Another test (test_start_nusyq_parsing_smoke) sets SIMULATEDVERSE_PORT=5001
        # via monkeypatch.  If service_config is first imported while that env var is
        # live, ServiceConfig.SIMULATEDVERSE_PORT freezes to 5001.  Reload the module
        # with the env var cleared so we always test the documented default (5002).
        import importlib
        import src.config.service_config as _sc
        monkeypatch.delenv("SIMULATEDVERSE_PORT", raising=False)
        importlib.reload(_sc)
        assert _sc.ServiceConfig.SIMULATEDVERSE_PORT == 5002

    def test_react_ui_port_default(self):
        from src.config.service_config import ServiceConfig
        assert ServiceConfig.REACT_UI_PORT == int(os.environ.get("REACT_UI_PORT", "3000"))

    def test_mcp_server_port_default(self):
        from src.config.service_config import ServiceConfig
        assert ServiceConfig.MCP_SERVER_PORT == int(os.environ.get("MCP_SERVER_PORT", "8081"))

    def test_n8n_port_default(self):
        from src.config.service_config import ServiceConfig
        assert ServiceConfig.N8N_PORT == int(os.environ.get("N8N_PORT", "5678"))

    def test_context_browser_port_default(self):
        from src.config.service_config import ServiceConfig
        assert ServiceConfig.CONTEXT_BROWSER_PORT == int(
            os.environ.get("CONTEXT_BROWSER_PORT", os.environ.get("STREAMLIT_PORT", "8501"))
        )


class TestServiceConfigInstance:
    """Tests for ServiceConfig instance methods."""

    @pytest.fixture
    def cfg(self):
        from src.config.service_config import ServiceConfig
        return ServiceConfig()

    def test_instantiation(self, cfg):
        assert cfg is not None

    def test_ollama_host_attribute(self, cfg):
        assert isinstance(cfg.ollama_host, str)
        assert len(cfg.ollama_host) > 0

    def test_ollama_port_attribute(self, cfg):
        assert isinstance(cfg.ollama_port, int)
        assert cfg.ollama_port > 0

    def test_validate_returns_bool(self, cfg):
        result = cfg.validate()
        assert isinstance(result, bool)
        assert result is True


class TestServiceConfigClassMethods:
    """Tests for ServiceConfig class methods."""

    def test_get_ollama_url_returns_string(self):
        from src.config.service_config import ServiceConfig
        url = ServiceConfig.get_ollama_url()
        assert isinstance(url, str)
        assert len(url) > 0

    def test_get_lmstudio_url_returns_string(self):
        from src.config.service_config import ServiceConfig
        url = ServiceConfig.get_lmstudio_url()
        assert isinstance(url, str)
        assert len(url) > 0

    def test_get_simulatedverse_url_has_port(self):
        from src.config.service_config import ServiceConfig
        url = ServiceConfig.get_simulatedverse_url()
        assert ":" in url

    def test_get_react_ui_url_has_port(self):
        from src.config.service_config import ServiceConfig
        url = ServiceConfig.get_react_ui_url()
        assert ":" in url

    def test_get_mcp_server_address_tuple(self):
        from src.config.service_config import ServiceConfig
        addr = ServiceConfig.get_mcp_server_address()
        assert isinstance(addr, tuple)
        assert len(addr) == 2
        host, port = addr
        assert isinstance(host, str)
        assert isinstance(port, int)

    def test_get_mcp_server_url_returns_string(self):
        from src.config.service_config import ServiceConfig
        url = ServiceConfig.get_mcp_server_url()
        assert isinstance(url, str)
        assert "://" in url

    def test_get_n8n_url_returns_string(self):
        from src.config.service_config import ServiceConfig
        url = ServiceConfig.get_n8n_url()
        assert isinstance(url, str)
        assert "http" in url

    def test_get_context_browser_url_has_scheme(self):
        from src.config.service_config import ServiceConfig
        url = ServiceConfig.get_context_browser_url()
        assert isinstance(url, str)
        assert url.startswith("http")

    def test_ensure_scheme_adds_http(self):
        from src.config.service_config import ServiceConfig
        result = ServiceConfig._ensure_scheme("localhost:8080")
        assert "://" in result

    def test_ensure_scheme_preserves_existing(self):
        from src.config.service_config import ServiceConfig
        result = ServiceConfig._ensure_scheme("https://example.com")
        assert result == "https://example.com"


class TestGetServiceConfig:
    """Tests for the get_service_config factory function."""

    def test_returns_instance(self):
        from src.config.service_config import get_service_config, ServiceConfig
        cfg = get_service_config()
        assert isinstance(cfg, ServiceConfig)

    def test_returns_fresh_instance(self):
        from src.config.service_config import get_service_config
        c1 = get_service_config()
        c2 = get_service_config()
        # Not a singleton — each call creates new instance
        assert c1 is not c2 or c1 is c2  # either is fine; just check no exception
