#!/usr/bin/env python3
"""Centralized configuration helper for NuSyQ-Hub.

Provides consistent access to configuration values with environment variable fallbacks.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .settings import load_settings

try:
    from src.config.service_config import ServiceConfig

    SERVICE_CONFIG_AVAILABLE = True
except ImportError:
    SERVICE_CONFIG_AVAILABLE = False
    ServiceConfig = None  # type: ignore[assignment,misc]


@lru_cache(maxsize=1)
def get_config() -> dict[str, Any]:
    """Load configuration with caching."""
    config_path = Path(__file__).parents[2] / "config" / "settings.json"
    return load_settings(str(config_path))


def _ensure_scheme(url: str) -> str:
    return url if "://" in url else f"http://{url}"


def _resolve_ollama_url() -> str:
    """Resolve Ollama base URL from ServiceConfig/env with safe defaults."""
    if SERVICE_CONFIG_AVAILABLE and ServiceConfig:  # type: ignore[truthy-function]
        return ServiceConfig.get_ollama_url().rstrip("/")

    base = os.getenv("OLLAMA_BASE_URL")
    if base:
        return base.rstrip("/") if "://" in base else f"http://{base.rstrip('/')}"

    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1")
    port = os.getenv("OLLAMA_PORT", "11434")
    parsed = urlparse(_ensure_scheme(host))
    if parsed.port:
        return parsed.geturl().rstrip("/")
    netloc = f"{parsed.hostname}:{port}" if parsed.hostname else f"127.0.0.1:{port}"
    return f"{parsed.scheme}://{netloc}"


def get_ollama_host() -> str:
    """Get Ollama host URL from config or environment."""
    # Priority: ServiceConfig > Environment variable > config file > default
    candidate: Any = get_config().get("ollama", {}).get("host")
    if candidate:
        result: str = str(candidate).rstrip("/")
        return result
    return _resolve_ollama_url()


def get_ollama_endpoint(path: str = "") -> str:
    """Get Ollama API endpoint URL."""
    base = get_ollama_host().rstrip("/")
    return f"{base}/{path.lstrip('/')}" if path else base


def get_chatdev_path() -> str:
    """Get ChatDev installation path from config or environment."""
    return os.getenv("CHATDEV_PATH") or get_config().get("chatdev", {}).get("path", "")


def get_timeout(key: str, default: int = 30) -> int:
    """Get timeout value from config."""
    timeouts: dict[str, Any] = get_config().get("timeouts", {})
    timeout_val: int = int(timeouts.get(key.lower().replace("_timeout", ""), default))
    return timeout_val


def get_feature_flag(flag: str, default: bool = False) -> bool:
    """Get feature flag value from config."""
    flags: dict[str, Any] = get_config().get("feature_flags", {})
    flag_val: bool = bool(flags.get(flag, default))
    return flag_val


__all__ = [
    "get_chatdev_path",
    "get_config",
    "get_feature_flag",
    "get_ollama_endpoint",
    "get_ollama_host",
    "get_timeout",
]
