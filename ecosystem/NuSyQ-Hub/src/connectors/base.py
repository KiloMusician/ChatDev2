"""Base Connector class for external service integrations.

Connectors follow the NuSyQ plugin pattern and integrate with:
- SpineRegistry for service discovery
- AgentOrchestrationHub for task routing
- Result type for consistent responses

OmniTag: [connector, base, integration, plugin]
MegaTag: CONNECTOR⨳BASE⦾EXTERNAL_SERVICE→∞

Pattern follows: src/culture_ship/plugins/ruff_fixer.py
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.core.result import Fail, Ok, Result

logger = logging.getLogger(__name__)


class ConnectorStatus(Enum):
    """Status of a connector."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ConnectorConfig:
    """Configuration for a connector.

    Attributes:
        name: Unique connector identifier
        enabled: Whether the connector is active
        api_key: Optional API key for authentication
        endpoint: Service endpoint URL
        timeout: Request timeout in seconds
        retry_count: Number of retries on failure
        metadata: Additional configuration data
    """

    name: str
    enabled: bool = True
    api_key: str | None = None
    endpoint: str | None = None
    timeout: int = 30
    retry_count: int = 3
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize config to dict (excluding sensitive data)."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "endpoint": self.endpoint,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "has_api_key": bool(self.api_key),
            "metadata": self.metadata,
        }


class BaseConnector(ABC):
    """Base class for all external service connectors.

    Connectors provide a standardized interface for integrating
    with external services like webhooks, APIs, and third-party
    platforms (Stripe, Notion, Slack, etc.).

    Implementation follows the plugin pattern from
    src/culture_ship/plugins/ruff_fixer.py.

    Example:
        class MyConnector(BaseConnector):
            def connect(self) -> Result[bool]:
                # Establish connection
                self._status = ConnectorStatus.CONNECTED
                return Ok(True)

            def execute(self, action: str, params: dict) -> Result[Any]:
                if action == "fetch":
                    return self._fetch_data(params)
                return Fail(f"Unknown action: {action}")
    """

    def __init__(self, config: ConnectorConfig):
        """Initialize the connector with configuration.

        Args:
            config: Connector configuration object
        """
        self.config = config
        self.name = config.name
        self._status = ConnectorStatus.DISCONNECTED
        self._last_error: str | None = None

    @property
    def status(self) -> ConnectorStatus:
        """Get current connector status."""
        return self._status

    @property
    def is_connected(self) -> bool:
        """Check if connector is connected and ready."""
        return self._status == ConnectorStatus.CONNECTED

    @abstractmethod
    def connect(self) -> Result[bool]:
        """Establish connection to the service.

        Returns:
            Result[bool]: Ok(True) on success, Fail on error
        """
        pass

    @abstractmethod
    def disconnect(self) -> Result[bool]:
        """Disconnect from the service.

        Returns:
            Result[bool]: Ok(True) on success, Fail on error
        """
        pass

    @abstractmethod
    def health_check(self) -> Result[dict]:
        """Check service health and connectivity.

        Returns:
            Result[dict]: Health status information
        """
        pass

    @abstractmethod
    def execute(self, action: str, params: dict) -> Result[Any]:
        """Execute an action on the service.

        Args:
            action: Action name (e.g., "send", "fetch", "create")
            params: Action parameters

        Returns:
            Result[Any]: Action result or error
        """
        pass

    def validate_config(self) -> Result[bool]:
        """Validate connector configuration.

        Returns:
            Result[bool]: Ok(True) if valid, Fail with details if invalid
        """
        if not self.config.name:
            return Fail("Connector name is required", code="INVALID_CONFIG")
        return Ok(True)

    def to_dict(self) -> dict:
        """Serialize connector state to dict.

        Returns:
            dict: Connector information
        """
        return {
            "name": self.name,
            "enabled": self.config.enabled,
            "status": self._status.value,
            "is_connected": self.is_connected,
            "last_error": self._last_error,
            "config": self.config.to_dict(),
        }

    def __repr__(self) -> str:
        """Return debug representation."""
        return f"<{self.__class__.__name__}(name={self.name}, status={self._status.value})>"
