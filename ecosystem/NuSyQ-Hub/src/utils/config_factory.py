#!/usr/bin/env python3
"""Config factory for lazy-loading and fallback configuration.

Provides a centralized, type-safe way to access ServiceConfig without
scattered try/except blocks throughout the codebase.

OmniTag: {
    "purpose": "config_factory",
    "tags": ["Python", "configuration", "factory_pattern"],
    "category": "infrastructure",
    "evolution_stage": "v1.0_typed_production"
}
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.config.service_config import ServiceConfig


class ConfigProxy:
    """Proxy for ServiceConfig with graceful fallback.

    Provides attribute access to ServiceConfig if available,
    otherwise returns safe default values.
    """

    def __init__(self) -> None:
        """Initialize config proxy with lazy loading."""
        self._config: type[ServiceConfig] | None = None
        self._checked = False

    def _ensure_loaded(self) -> bool:
        """Ensure config is loaded if available."""
        if self._checked:
            return self._config is not None

        self._checked = True
        try:
            from src.config.service_config import ServiceConfig

            self._config = ServiceConfig
            return True
        except (ImportError, AttributeError):
            self._config = None
            return False

    def __getattr__(self, name: str) -> Any:
        """Get attribute from ServiceConfig or return safe default."""
        if self._ensure_loaded() and self._config is not None:
            return getattr(self._config, name, None)
        return None

    def __bool__(self) -> bool:
        """Check if config is available."""
        return self._ensure_loaded()


_state: dict[str, ConfigProxy | bool | None] = {
    "config_instance": None,
    "config_available": None,
}


def get_service_config() -> ConfigProxy:
    """Get service config instance with lazy loading.

    Returns:
        ConfigProxy that provides access to ServiceConfig if available,
        otherwise returns None for all attributes.

    Example:
        config = get_service_config()
        if config:
            ollama_host = config.OLLAMA_HOST
        else:
            ollama_host = "http://localhost:11434"
    """
    instance = _state["config_instance"]
    if not isinstance(instance, ConfigProxy):
        instance = ConfigProxy()
        _state["config_instance"] = instance
    return instance


def is_config_available() -> bool:
    """Check if ServiceConfig is available without loading.

    Returns:
        True if ServiceConfig can be imported, False otherwise.
    """
    available = _state["config_available"]
    if available is not None:
        return bool(available)

    try:
        from src.config.service_config import ServiceConfig

        available = True
        del ServiceConfig
    except ImportError:
        available = False

    _state["config_available"] = available
    return bool(available)
