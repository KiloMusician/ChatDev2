"""KILO-FOOLISH Secrets Management
Placeholder for configuration and secrets.
"""

import os

# Placeholder for API keys and configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def get_api_key(service: str) -> str | None:
    """Get API key for a service (reads from environment at call time)."""
    if service.lower() == "openai":
        return os.getenv("OPENAI_API_KEY") or None
    return None


class _SecretsConfig:
    """Minimal secrets accessor consumed by ai_coordinator and similar callers."""

    _ENV_MAP: dict[str, dict[str, str]] = {
        "openai": {"api_key": "OPENAI_API_KEY"},
        "anthropic": {"api_key": "ANTHROPIC_API_KEY"},
        "google": {"api_key": "GOOGLE_API_KEY"},
    }

    def get_secret(self, service: str, key: str) -> str | None:
        """Return a secret value from environment, or None if not set."""
        env_var = self._ENV_MAP.get(service, {}).get(key)
        if env_var:
            return os.getenv(env_var) or None
        return None


config = _SecretsConfig()


class SecretsManager:
    """Singleton secrets manager providing structured access to all service credentials."""

    _DEFAULTS: dict[str, object] = {
        "ollama_host": "http://localhost:11434",
        "debug_mode": False,
        "log_level": "INFO",
    }

    _ENV_KEYS: dict[str, str] = {
        "ollama_host": "OLLAMA_HOST",
        "openai_api_key": "OPENAI_API_KEY",
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "debug_mode": "DEBUG",
        "log_level": "LOG_LEVEL",
    }

    def get_config(self, key: str) -> object:
        """Return a config value by key, reading from environment with fallback."""
        env_var = self._ENV_KEYS.get(key)
        if env_var:
            value = os.getenv(env_var)
            if value is not None:
                return value
        return self._DEFAULTS.get(key)

    def get_ai_service_config(self) -> dict:
        """Return config dict for all AI services."""
        return {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        }

    def validate_configuration(self) -> dict:
        """Validate the current configuration. Returns dict with status and details."""
        issues = []
        if not os.getenv("OPENAI_API_KEY"):
            issues.append("OPENAI_API_KEY not set (optional)")
        return {
            "valid": True,  # configuration is always valid; missing keys are optional
            "issues": issues,
            "ollama_host": self.get_config("ollama_host"),
        }


_secrets_manager: SecretsManager | None = None


def get_secrets_manager() -> SecretsManager:
    """Return the singleton SecretsManager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager
