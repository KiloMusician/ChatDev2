"""Plugin Registry for dynamic extension management."""

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Central registry for plugins/extensions."""

    def __init__(self):
        self._plugins: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}

    def register(self, name: str, plugin: Any, *, override: bool = False) -> None:
        if name in self._plugins and not override:
            raise ValueError(f"Plugin '{name}' already registered. Use override=True to replace.")
        self._plugins[name] = plugin
        logger.info(f"Registered plugin: {name}")
        try:
            from src.system.agent_awareness import emit as _emit

            _emit(
                "system",
                f"Plugin registered: {name} total={len(self._plugins)}",
                level="INFO",
                source="plugin_registry",
            )
        except Exception:
            pass

    def get(self, name: str) -> Any:
        return self._plugins.get(name)

    def list_plugins(self) -> list[str]:
        return list(self._plugins.keys())

    def register_factory(
        self, name: str, factory: Callable[[], Any], *, override: bool = False
    ) -> None:
        if name in self._factories and not override:
            raise ValueError(
                f"Factory for '{name}' already registered. Use override=True to replace."
            )
        self._factories[name] = factory
        logger.info(f"Registered plugin factory: {name}")

    def create(self, name: str) -> Any:
        if name not in self._factories:
            raise ValueError(f"No factory registered for '{name}'")
        return self._factories[name]()
