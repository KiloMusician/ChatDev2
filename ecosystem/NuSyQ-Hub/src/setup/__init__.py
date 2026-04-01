"""Setup subsystem — secure config, secrets management, and env loading.

OmniTag: {
    "purpose": "setup_subsystem",
    "tags": ["Setup", "Secrets", "Config", "Environment"],
    "category": "infrastructure",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

__all__ = [
    # Secrets + config
    "ConfigurationError",
    "SecretsManager",
    "SecureConfig",
    "get_config",
    # Env loading
    "load_dotenv",
]


def __getattr__(name: str) -> object:
    if name in ("ConfigurationError", "SecureConfig", "SecretsManager", "get_config"):
        from src.setup.secrets import (ConfigurationError, SecretsManager,
                                       SecureConfig, get_config)

        return locals()[name]
    if name == "load_dotenv":
        from src.setup.env_loader import load_dotenv

        return load_dotenv
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
