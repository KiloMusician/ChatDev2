#!/usr/bin/env python3
"""Utility helpers for repository configuration settings."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from src.config.service_config import \
        ServiceConfig as ImportedServiceConfig
except ImportError:
    ImportedServiceConfig = None

ServiceConfig: Any | None = ImportedServiceConfig
SERVICE_CONFIG_AVAILABLE = ServiceConfig is not None


def _ensure_scheme(url: str) -> str:
    return url if "://" in url else f"http://{url}"


def _default_ollama_url() -> str:
    if SERVICE_CONFIG_AVAILABLE and ServiceConfig:
        return str(ServiceConfig.get_ollama_url()).rstrip("/")

    base = os.getenv("OLLAMA_BASE_URL")
    if base:
        return base.rstrip("/") if "://" in base else f"http://{base.rstrip('/')}"

    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1")
    port = os.getenv("OLLAMA_PORT", "11435")
    parsed = urlparse(_ensure_scheme(host))
    if parsed.port:
        return parsed.geturl().rstrip("/")
    netloc = f"{parsed.hostname}:{port}" if parsed.hostname else f"127.0.0.1:{port}"
    return f"{parsed.scheme}://{netloc}"


DEFAULT_SETTINGS: dict[str, Any] = {
    "chatdev": {"path": ""},
    "ollama": {
        "host": _default_ollama_url(),
        "path": "",
    },
    "vscode": {"path": ""},
    "context_server": {"host": "127.0.0.1", "port": 11435},
    "timeouts": {"default": 30, "long": 300},
    "feature_flags": {
        "enable_chatdev": True,
        "enable_ollama": True,
        "experimental_mode": False,
    },
}


def load_settings(config_path: str = "config/settings.json") -> dict[str, Any]:
    """Load configuration settings with defaults.

    Parameters
    ----------
    config_path: str
        Path to the JSON configuration file.

    Returns:
    -------
    dict[str, Any]
        Settings dictionary with default values applied for missing fields.

    """
    path = Path(config_path)
    data: dict[str, Any] = {}
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    def merge(defaults: Any, provided: Any) -> Any:
        if isinstance(defaults, dict):
            result: dict[str, Any] = {}
            provided = provided or {}
            for key, value in defaults.items():
                result[key] = merge(value, provided.get(key))
            for key, value in (provided or {}).items():
                if key not in result:
                    result[key] = value
            return result
        return provided if provided is not None else defaults

    merged_result: dict[str, Any] = merge(DEFAULT_SETTINGS, data)
    return merged_result


__all__ = ["DEFAULT_SETTINGS", "load_settings"]
