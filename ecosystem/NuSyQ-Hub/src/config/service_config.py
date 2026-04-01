#!/usr/bin/env python3
"""Centralized configuration for service endpoints and ports.

This module provides configurable defaults for all service endpoints,
eliminating hardcoded host/port literals throughout the codebase.

Environment Variables:
    OLLAMA_HOST: Ollama service host (default: http://127.0.0.1)
    OLLAMA_PORT: Ollama service port (default: 11434)
    OLLAMA_BASE_URL: Full Ollama URL override
    SIMULATEDVERSE_HOST: SimulatedVerse host (default: http://127.0.0.1)
    SIMULATEDVERSE_PORT: SimulatedVerse port (default: 5002)
    REACT_UI_HOST: React UI host (default: http://127.0.0.1)
    REACT_UI_PORT: React UI port (default: 3000)
    MCP_SERVER_HOST: MCP server host (default: localhost)
    MCP_SERVER_PORT: MCP server port (default: 8081)
    MCP_SERVER_URL: Optional MCP server base URL override
    N8N_URL: N8N service URL (default: http://<host>:<port>)
    N8N_PORT: N8N service port (default: 5678)
    CONTEXT_BROWSER_HOST / STREAMLIT_HOST: Context browser host (default: http://127.0.0.1)
    CONTEXT_BROWSER_PORT / STREAMLIT_PORT: Context browser port (default: 8501)
    CONTEXT_BROWSER_BASE_URL / STREAMLIT_BASE_URL: Optional full URL override
    OPENAI_API_KEY: OpenAI API key
    OPENAI_API_BASE: OpenAI API base URL

OmniTag: {
    "purpose": "service_configuration",
    "tags": ["Python", "configuration", "service_discovery"],
    "category": "infrastructure",
    "evolution_stage": "v2.0_typed_production"
}
"""

from __future__ import annotations

import os
from typing import Final
from urllib.parse import urlparse


class ServiceConfig:
    """Centralized service configuration with environment variable fallbacks.

    This class provides typed, centralized access to all service endpoints
    used throughout the NuSyQ-Hub ecosystem.
    """

    # Ollama Configuration
    OLLAMA_HOST: Final[str] = os.environ.get("OLLAMA_HOST", "http://localhost")
    OLLAMA_PORT: Final[int] = int(os.environ.get("OLLAMA_PORT", "11434"))
    OLLAMA_BASE_URL: Final[str] = os.environ.get("OLLAMA_BASE_URL", OLLAMA_HOST)

    # LM Studio Configuration (OpenAI-compatible API)
    LMSTUDIO_HOST: Final[str] = os.environ.get("LMSTUDIO_HOST", "http://10.0.0.172")
    LMSTUDIO_PORT: Final[int] = int(os.environ.get("LMSTUDIO_PORT", "1234"))
    LMSTUDIO_BASE_URL: Final[str] = os.environ.get("LMSTUDIO_BASE_URL", "")

    # SimulatedVerse Configuration
    SIMULATEDVERSE_HOST: Final[str] = os.environ.get("SIMULATEDVERSE_HOST", "http://127.0.0.1")
    SIMULATEDVERSE_PORT: Final[int] = int(os.environ.get("SIMULATEDVERSE_PORT", "5002"))

    # React UI Configuration
    REACT_UI_HOST: Final[str] = os.environ.get("REACT_UI_HOST", "http://127.0.0.1")
    REACT_UI_PORT: Final[int] = int(os.environ.get("REACT_UI_PORT", "3000"))

    # MCP Server Configuration
    MCP_SERVER_URL: Final[str] = os.environ.get("MCP_SERVER_URL", "")
    MCP_SERVER_HOST: Final[str] = os.environ.get("MCP_SERVER_HOST", "localhost")
    MCP_SERVER_PORT: Final[int] = int(os.environ.get("MCP_SERVER_PORT", "8081"))

    # N8N Configuration
    N8N_URL: Final[str] = os.environ.get(
        "N8N_URL", f"http://127.0.0.1:{os.environ.get('N8N_PORT', '5678')}"
    )
    N8N_PORT: Final[int] = int(os.environ.get("N8N_PORT", "5678"))

    # Context Browser / Streamlit Configuration
    CONTEXT_BROWSER_HOST: Final[str] = os.environ.get(
        "CONTEXT_BROWSER_HOST",
        os.environ.get("STREAMLIT_HOST", "http://127.0.0.1"),
    )
    CONTEXT_BROWSER_PORT: Final[int] = int(
        os.environ.get("CONTEXT_BROWSER_PORT", os.environ.get("STREAMLIT_PORT", "8501"))
    )
    CONTEXT_BROWSER_BASE_URL: Final[str] = os.environ.get(
        "CONTEXT_BROWSER_BASE_URL",
        os.environ.get("STREAMLIT_BASE_URL", ""),
    )

    # OpenAI/LLM Configuration
    OPENAI_API_KEY: Final[str] = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_API_BASE: Final[str] = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

    # ------------------------------------------------------------------
    # Instance-level compatibility layer for tests and existing code
    # ------------------------------------------------------------------
    def __init__(self, config_file: str | os.PathLike | None = None) -> None:
        """Optional instance facade with simple attributes.

        Accepts an optional config file path but does not require it. Exposes
        attributes often used by tests: ollama_host and ollama_port.
        """
        # Use class-level configuration from environment variables
        self.ollama_host = self.get_ollama_url()
        self.ollama_port = self.OLLAMA_PORT

    def validate(self) -> bool:
        """Basic configuration validation hook for tests."""
        try:
            return isinstance(self.ollama_host, str) and bool(self.ollama_host)
        except Exception:
            return False

    @classmethod
    def get_ollama_url(cls) -> str:
        """Get the Ollama service base URL.

        Returns:
            Complete Ollama service URL (e.g., 'http://127.0.0.1:11435')
        """
        if cls.OLLAMA_BASE_URL and cls.OLLAMA_BASE_URL != cls.OLLAMA_HOST:
            return cls.OLLAMA_BASE_URL
        return f"{cls.OLLAMA_HOST}:{cls.OLLAMA_PORT}"

    @classmethod
    def get_lmstudio_url(cls) -> str:
        """Get the LM Studio service base URL.

        Returns:
            Complete LM Studio URL (e.g., 'http://10.0.0.172:1234')
        """
        if cls.LMSTUDIO_BASE_URL:
            return cls.LMSTUDIO_BASE_URL
        return f"{cls.LMSTUDIO_HOST}:{cls.LMSTUDIO_PORT}"

    @classmethod
    def get_simulatedverse_url(cls) -> str:
        """Get the SimulatedVerse service base URL.

        Returns:
            Complete SimulatedVerse URL (e.g., 'http://127.0.0.1:5002')
        """
        return f"{cls.SIMULATEDVERSE_HOST}:{cls.SIMULATEDVERSE_PORT}"

    @classmethod
    def get_react_ui_url(cls) -> str:
        """Get the React UI service base URL.

        Returns:
            Complete React UI URL (e.g., 'http://127.0.0.1:3000')
        """
        return f"{cls.REACT_UI_HOST}:{cls.REACT_UI_PORT}"

    @classmethod
    def get_mcp_server_address(cls) -> tuple[str, int]:
        """Get the MCP server address as (host, port) tuple.

        Returns:
            Tuple of (hostname, port) for MCP server connection
        """
        return (cls.MCP_SERVER_HOST, cls.MCP_SERVER_PORT)

    @classmethod
    def get_mcp_server_url(cls) -> str:
        """Get the MCP server base URL.

        Respects MCP_SERVER_URL if provided, otherwise builds from host/port.
        """
        if cls.MCP_SERVER_URL:
            return cls._ensure_scheme(cls.MCP_SERVER_URL.rstrip("/"))

        host, port = cls.get_mcp_server_address()
        parsed = urlparse(cls._ensure_scheme(host))
        base_host = f"{parsed.scheme}://{parsed.hostname}" if parsed.hostname else host
        return f"{base_host}:{port}" if port else base_host

    @classmethod
    def get_n8n_url(cls) -> str:
        """Get the N8N workflow automation service base URL.

        Returns:
            Complete N8N service URL (e.g., 'http://127.0.0.1:5678')
        """
        return cls.N8N_URL or f"http://127.0.0.1:{cls.N8N_PORT}"

    @classmethod
    def _ensure_scheme(cls, url: str) -> str:
        """Ensure a URL has a scheme for safe parsing."""
        return url if "://" in url else f"http://{url}"

    @classmethod
    def get_context_browser_url(cls) -> str:
        """Return the configured Streamlit/Context Browser URL.

        Respects full URL overrides first, then host/port pairs. This prevents
        hardcoded localhost references and keeps launchers consistent.
        """
        if cls.CONTEXT_BROWSER_BASE_URL:
            return cls._ensure_scheme(cls.CONTEXT_BROWSER_BASE_URL.rstrip("/"))

        parsed = urlparse(cls._ensure_scheme(cls.CONTEXT_BROWSER_HOST))
        host = parsed.hostname or "localhost"
        port = parsed.port or cls.CONTEXT_BROWSER_PORT
        scheme = parsed.scheme or "http"
        netloc = f"{host}:{port}" if port else host
        return f"{scheme}://{netloc}"

    @classmethod
    def is_service_available(cls, service_name: str, timeout: float = 2.0) -> bool:
        """Check if a service is available.

        Args:
            service_name: Name of the service (ollama, simulatedverse, mcp_server, n8n)
            timeout: Connection timeout in seconds

        Returns:
            True if service is available, False otherwise
        """
        import requests

        service_urls = {
            "ollama": cls.get_ollama_url() + "/api/tags",
            "lmstudio": cls.get_lmstudio_url() + "/v1/models",
            "simulatedverse": cls.get_simulatedverse_url() + "/health",
            "react_ui": cls.get_react_ui_url() + "/health",
            "n8n": cls.get_n8n_url() + "/api/v1/health",
        }

        if service_name not in service_urls:
            return False

        try:
            response = requests.get(service_urls[service_name], timeout=timeout)
            return bool(response.status_code < 500)
        except (requests.RequestException, ConnectionError):
            return False


def get_service_config() -> ServiceConfig:
    """Get a ServiceConfig instance.

    Returns:
        ServiceConfig instance with environment-based configuration
    """
    return ServiceConfig()
