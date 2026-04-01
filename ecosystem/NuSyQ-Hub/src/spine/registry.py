"""Spine Registry: Central Service Registry and Dependency Injection.

The SpineRegistry provides centralized service discovery, registration,
and dependency injection for all NuSyQ-Hub modules.

[OmniTag: spine_registry, service_discovery, dependency_injection, module_wiring]
"""

from __future__ import annotations

import importlib
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SpineRegistry:
    """Central registry for all NuSyQ-Hub modules and services.

    The SpineRegistry acts as the central nervous system, managing:
    - Service registration and discovery
    - Lazy loading of modules
    - Dependency resolution
    - Module health validation

    Example:
        >>> spine = SpineRegistry()
        >>> spine.register("orchestration.hub", orchestrator_instance)
        >>> orchestrator = spine.get("orchestration.hub")
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize the spine registry.

        Args:
            config_path: Path to module_registry.json. Defaults to src/spine/module_registry.json
        """
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}
        self._config: dict[str, Any] = {"modules": {}}
        self._lazy_loaded: set[str] = set()

        # Default config path
        if config_path is None:
            config_path = Path(__file__).parent / "module_registry.json"
        self._config_path = config_path

        self._load_config()

    def _load_config(self) -> None:
        """Load module configuration from spine registry."""
        if self._config_path.exists():
            try:
                with open(self._config_path) as f:
                    self._config = json.load(f)
                logger.info(f"Loaded spine config: {len(self._config.get('modules', {}))} modules")
            except Exception as e:
                logger.error(f"Failed to load spine config from {self._config_path}: {e}")
                self._config = {"modules": {}}
        else:
            logger.warning(f"Spine config not found at {self._config_path}")
            self._config = {"modules": {}}

    def register(self, name: str, service: Any, *, override: bool = False) -> None:
        """Register a service with the spine.

        Args:
            name: Service identifier (e.g., "orchestration.hub")
            service: Service instance or class
            override: Allow replacing existing service

        Raises:
            ValueError: If service already registered and override=False
        """
        if name in self._services and not override:
            raise ValueError(f"Service '{name}' already registered. Use override=True to replace.")

        self._services[name] = service
        logger.debug(f"Registered service: {name}")

    def register_factory(
        self, name: str, factory: Callable[[], Any], *, override: bool = False
    ) -> None:
        """Register a factory function for lazy service creation.

        Args:
            name: Service identifier
            factory: Callable that creates and returns the service
            override: Allow replacing existing factory

        Raises:
            ValueError: If factory already registered and override=False
        """
        if name in self._factories and not override:
            raise ValueError(
                f"Factory for '{name}' already registered. Use override=True to replace."
            )

        self._factories[name] = factory
        logger.debug(f"Registered factory: {name}")

    def get(self, name: str, *, default: Any = None) -> Any:
        """Get a service from the spine registry.

        Args:
            name: Service identifier
            default: Value to return if service not found

        Returns:
            Service instance or default
        """
        # Check if already instantiated
        if name in self._services:
            return self._services[name]

        # Check if factory exists
        if name in self._factories:
            service = self._factories[name]()
            self._services[name] = service
            return service

        # Try lazy loading from config
        if name in self._config.get("modules", {}):
            try:
                service = self._lazy_load(name)
                return service
            except Exception as e:
                logger.error(f"Failed to lazy load '{name}': {e}")

        return default

    def _lazy_load(self, name: str) -> Any:
        """Lazily load a service based on module_registry.json configuration.

        Args:
            name: Module name from registry

        Returns:
            Loaded service instance

        Raises:
            KeyError: If service not found in registry
            ImportError: If module cannot be imported
            AttributeError: If class not found in module
        """
        if name in self._lazy_loaded:
            # Already attempted, return from cache or fail
            if name in self._services:
                return self._services[name]
            raise KeyError(f"Service '{name}' failed to load previously")

        module_spec = self._config["modules"].get(name, {})
        if not module_spec:
            raise KeyError(f"Service '{name}' not found in registry")

        # Check if lazy loading is disabled
        if module_spec.get("lazy_load") is False:
            raise ValueError(f"Service '{name}' has lazy_load disabled in config")

        module_path = module_spec.get("module_path")
        class_name = module_spec.get("class_name")

        if not module_path or not class_name:
            raise ValueError(f"Service '{name}' missing 'module_path' or 'class_name' in config")

        try:
            # Import module
            module = importlib.import_module(module_path)  # nosemgrep
            service_class = getattr(module, class_name)

            # Instantiate service
            instance = service_class()

            # Register and mark as loaded
            self.register(name, instance, override=True)
            self._lazy_loaded.add(name)

            logger.info(f"Lazy loaded service: {name}")
            return instance

        except Exception as e:
            self._lazy_loaded.add(name)  # Mark to prevent retry loops
            logger.error(f"Failed to lazy load '{name}': {e}")
            raise

    def has(self, name: str) -> bool:
        """Check if a service is registered or available.

        Args:
            name: Service identifier

        Returns:
            True if service is registered or can be lazy loaded
        """
        return (
            name in self._services
            or name in self._factories
            or name in self._config.get("modules", {})
        )

    def get_public_api(self, module_name: str) -> list[str]:
        """Get the public API for a module from the registry.

        Args:
            module_name: Name of the module

        Returns:
            List of public API symbols
        """
        public_api: list[str] = (
            self._config.get("modules", {}).get(module_name, {}).get("public_api", [])
        )
        return public_api

    def get_dependencies(self, module_name: str) -> list[str]:
        """Get the dependencies for a module from the registry.

        Args:
            module_name: Name of the module

        Returns:
            List of dependency module names
        """
        dependencies: list[str] = (
            self._config.get("modules", {}).get(module_name, {}).get("dependencies", [])
        )
        return dependencies

    def validate_dependencies(self) -> dict[str, list[str]]:
        """Validate that all declared dependencies exist in the registry.

        Returns:
            Dictionary of modules with missing dependencies
        """
        missing: dict[str, list[str]] = {}

        for module_name, spec in self._config.get("modules", {}).items():
            deps = spec.get("dependencies", [])
            for dep in deps:
                if dep not in self._config.get("modules", {}):
                    if module_name not in missing:
                        missing[module_name] = []
                    missing[module_name].append(dep)

        return missing

    def get_all_modules(self) -> list[str]:
        """Get list of all registered module names.

        Returns:
            List of module identifiers
        """
        return list(self._config.get("modules", {}).keys())

    def get_module_spec(self, module_name: str) -> dict[str, Any]:
        """Get the full specification for a module.

        Args:
            module_name: Name of the module

        Returns:
            Module specification dict or empty dict if not found
        """
        module_spec: dict[str, Any] = self._config.get("modules", {}).get(module_name, {})
        return module_spec

    def health_check(self) -> dict[str, Any]:
        """Perform health check on all spine-wired modules.

        Returns:
            Health check results including:
            - total_modules: Total modules in registry
            - wired_modules: Modules marked as spine_wired
            - loaded_services: Services currently loaded
            - missing_dependencies: Modules with missing deps
            - healthy: Overall health status
        """
        total = len(self._config.get("modules", {}))
        wired = sum(
            1 for spec in self._config.get("modules", {}).values() if spec.get("spine_wired")
        )
        loaded = len(self._services)
        missing_deps = self.validate_dependencies()

        return {
            "total_modules": total,
            "wired_modules": wired,
            "loaded_services": loaded,
            "missing_dependencies": missing_deps,
            "healthy": len(missing_deps) == 0,
        }


# Singleton instance
_spine: SpineRegistry | None = None


def get_spine() -> SpineRegistry:
    """Get the global spine registry singleton.

    Returns:
        Global SpineRegistry instance
    """
    global _spine
    if _spine is None:
        _spine = SpineRegistry()
    return _spine


def get_service(name: str, *, default: Any = None) -> Any:
    """Get a service from the global spine registry.

    Args:
        name: Service identifier
        default: Value to return if service not found

    Returns:
        Service instance or default
    """
    return get_spine().get(name, default=default)


def register_service(name: str, service: Any, *, override: bool = False) -> None:
    """Register a service with the global spine registry.

    Args:
        name: Service identifier
        service: Service instance or class
        override: Allow replacing existing service
    """
    get_spine().register(name, service, override=override)


def register_factory(name: str, factory: Callable[[], Any], *, override: bool = False) -> None:
    """Register a factory function with the global spine registry.

    Args:
        name: Service identifier
        factory: Callable that creates and returns the service
        override: Allow replacing existing factory
    """
    get_spine().register_factory(name, factory, override=override)
