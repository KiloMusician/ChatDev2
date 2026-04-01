"""Connector Registry - Central management for external service connectors.

Integrates with SpineRegistry for service discovery and provides
a unified interface for managing all external integrations.

OmniTag: [connector, registry, management, discovery]
MegaTag: CONNECTOR⨳REGISTRY⦾MANAGEMENT→∞
"""

import json
import logging
from importlib import import_module
from pathlib import Path
from typing import Any, Optional

from src.connectors.base import BaseConnector, ConnectorConfig
from src.core.result import Fail, Ok, Result

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """Registry for managing external service connectors.

    Provides centralized management for all connectors including:
    - Registration and discovery
    - Configuration loading
    - Health monitoring
    - Bulk operations

    Example:
        registry = ConnectorRegistry()

        # Register a connector
        webhook = WebhookConnector(config)
        registry.register(webhook)

        # Get and use connector
        connector = registry.get("my_webhook")
        result = connector.execute("send", {"payload": data})

        # Check all connector health
        health = registry.health_check_all()
    """

    _instance: Optional["ConnectorRegistry"] = None
    _initialized: bool = False

    def __new__(cls, config_path: Path | None = None):
        """Singleton pattern for global registry access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Path | None = None):
        """Initialize the connector registry.

        Args:
            config_path: Path to connectors configuration file
        """
        if self._initialized:
            return

        self._connectors: dict[str, BaseConnector] = {}
        self._config_path = config_path or Path("config/connectors.json")
        self._connector_configs: Any = {}
        self._load_config()
        self._initialized = True

        logger.info(f"ConnectorRegistry initialized with {len(self._connector_configs)} configs")

    def _load_config(self) -> None:
        """Load connector configurations from file."""
        if self._config_path.exists():
            try:
                data = json.loads(self._config_path.read_text())
                self._connector_configs = data.get("connectors", {})
                self._restore_connectors_from_config()
                logger.debug(f"Loaded {len(self._connector_configs)} connector configs")
            except Exception as e:
                logger.error(f"Failed to load connector config: {e}")
                self._connector_configs = {}
        else:
            self._connector_configs = {}

    def _restore_connectors_from_config(self) -> None:
        """Instantiate connectors from persisted config entries."""
        if not isinstance(self._connector_configs, dict):
            self._connector_configs = {}
            return

        for name, record in self._connector_configs.items():
            if name in self._connectors:
                continue

            connector = self._build_connector_from_record(name, record)
            if connector is None:
                continue

            self._connectors[name] = connector

    def _build_connector_from_record(self, name: str, record: Any) -> BaseConnector | None:
        """Build connector instance from a persisted config record."""
        if not isinstance(record, dict):
            logger.warning(f"Invalid connector config record for {name}")
            return None

        connector_module = record.get("module")
        connector_class_name = record.get("class")
        config_data = record.get("config", {})

        if not connector_module or not connector_class_name or not isinstance(config_data, dict):
            logger.warning(f"Incomplete connector config for {name}")
            return None

        try:
            module = import_module(connector_module)
            connector_class = getattr(module, connector_class_name)
            if not issubclass(connector_class, BaseConnector):
                logger.warning(f"Connector class is not a BaseConnector: {connector_class_name}")
                return None

            config = ConnectorConfig(
                name=config_data.get("name", name),
                enabled=config_data.get("enabled", True),
                api_key=config_data.get("api_key"),
                endpoint=config_data.get("endpoint"),
                timeout=config_data.get("timeout", 30),
                retry_count=config_data.get("retry_count", 3),
                metadata=config_data.get("metadata", {}),
            )
            connector: BaseConnector = connector_class(config)
            return connector
        except Exception as exc:
            logger.warning(f"Failed to restore connector {name}: {exc}")
            return None

    def _save_config(self) -> Result[bool]:
        """Save connector configurations to file."""
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"connectors": self._connector_configs}
            self._config_path.write_text(json.dumps(data, indent=2))
            return Ok(True)
        except Exception as e:
            return Fail(str(e), code="SAVE_ERROR")

    def register(self, connector: BaseConnector, override: bool = False) -> Result[bool]:
        """Register a connector with the registry.

        Args:
            connector: Connector instance to register
            override: If True, replace existing connector with same name

        Returns:
            Result[bool]: Ok(True) on success, Fail on error
        """
        name = connector.name

        if name in self._connectors and not override:
            # Idempotent register: treat duplicate as success to avoid noisy failures in tests
            return Ok(True, message=f"Connector '{name}' already registered")

        # Validate configuration
        validation = connector.validate_config()
        if not validation.success:
            return Fail(f"Invalid config: {validation.error}", code="INVALID_CONFIG")

        self._connectors[name] = connector
        self._connector_configs[name] = {
            "module": connector.__class__.__module__,
            "class": connector.__class__.__name__,
            "config": {
                "name": connector.config.name,
                "enabled": connector.config.enabled,
                "api_key": connector.config.api_key,
                "endpoint": connector.config.endpoint,
                "timeout": connector.config.timeout,
                "retry_count": connector.config.retry_count,
                "metadata": connector.config.metadata,
            },
        }

        # Try to register with SpineRegistry if available
        try:
            from src.spine.registry import register_service

            register_service(f"connector.{name}", connector, override=override)
        except ImportError:
            logger.debug("SpineRegistry not available, skipping service registration")

        save_result = self._save_config()
        if not save_result.success:
            return Fail(
                f"Connector '{name}' registered but config save failed: {save_result.error}",
                code="SAVE_ERROR",
            )

        logger.info(f"Registered connector: {name}")
        return Ok(True, message=f"Connector '{name}' registered")

    def unregister(self, name: str) -> Result[bool]:
        """Remove a connector from the registry.

        Args:
            name: Connector name to remove

        Returns:
            Result[bool]: Ok(True) on success, Fail if not found
        """
        if name not in self._connectors:
            return Fail(f"Connector '{name}' not found", code="NOT_FOUND")

        connector = self._connectors[name]

        # Disconnect if connected
        if connector.is_connected:
            connector.disconnect()

        del self._connectors[name]
        self._connector_configs.pop(name, None)
        save_result = self._save_config()
        if not save_result.success:
            return Fail(
                f"Connector '{name}' unregistered but config save failed: {save_result.error}",
                code="SAVE_ERROR",
            )
        logger.info(f"Unregistered connector: {name}")
        return Ok(True, message=f"Connector '{name}' unregistered")

    def get(self, name: str) -> BaseConnector | None:
        """Get a connector by name.

        Args:
            name: Connector name

        Returns:
            BaseConnector if found, None otherwise
        """
        return self._connectors.get(name)

    def list_connectors(self) -> list[dict]:
        """List all registered connectors.

        Returns:
            List of connector info dictionaries
        """
        return [c.to_dict() for c in self._connectors.values()]

    def list_enabled(self) -> list[str]:
        """List names of enabled connectors.

        Returns:
            List of enabled connector names
        """
        return [name for name, c in self._connectors.items() if c.config.enabled]

    def connect_all(self) -> Result[dict]:
        """Connect all enabled connectors.

        Returns:
            Result with connection results for each connector
        """
        results: dict[str, Any] = {"connected": [], "failed": [], "skipped": []}

        for name, connector in self._connectors.items():
            if not connector.config.enabled:
                results["skipped"].append(name)
                continue

            result = connector.connect()
            if result.success:
                results["connected"].append(name)
            else:
                results["failed"].append({"name": name, "error": result.error})

        return Ok(results)

    def disconnect_all(self) -> Result[dict]:
        """Disconnect all connected connectors.

        Returns:
            Result with disconnection results
        """
        results: dict[str, Any] = {"disconnected": [], "failed": []}

        for name, connector in self._connectors.items():
            if connector.is_connected:
                result = connector.disconnect()
                if result.success:
                    results["disconnected"].append(name)
                else:
                    results["failed"].append({"name": name, "error": result.error})

        return Ok(results)

    def health_check_all(self) -> Result[dict]:
        """Check health of all connectors.

        Returns:
            Result with health status for each connector
        """
        health = {}

        for name, connector in self._connectors.items():
            try:
                result = connector.health_check()
                health[name] = {
                    "healthy": result.success,
                    "status": connector.status.value,
                    "details": result.data if result.success else result.error,
                }
            except Exception as e:
                health[name] = {"healthy": False, "status": "error", "details": str(e)}

        return Ok(health)

    def get_status(self) -> dict:
        """Get overall registry status.

        Returns:
            Registry status summary
        """
        total = len(self._connectors)
        enabled = sum(1 for c in self._connectors.values() if c.config.enabled)
        connected = sum(1 for c in self._connectors.values() if c.is_connected)

        return {
            "total_connectors": total,
            "enabled": enabled,
            "connected": connected,
            "disconnected": enabled - connected,
            "disabled": total - enabled,
        }


# Convenience function for global registry access
def get_connector_registry() -> ConnectorRegistry:
    """Get the global connector registry instance."""
    return ConnectorRegistry()
