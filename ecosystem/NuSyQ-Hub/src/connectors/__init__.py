"""NuSyQ-Hub Connector Architecture.

Provides a plugin system for external service integrations.
Connectors follow the n8n-style pattern for easy service integration.

OmniTag: [connector, integration, plugin, external_service]
MegaTag: CONNECTOR⨳ARCHITECTURE⦾INTEGRATION→∞

Usage:
    from src.connectors import ConnectorRegistry, BaseConnector, ConnectorConfig
    from src.connectors.webhook import WebhookConnector

    # Create and register a connector
    registry = ConnectorRegistry()
    config = ConnectorConfig(name="my_webhook", endpoint="https://api.example.com")
    connector = WebhookConnector(config)
    registry.register(connector)

    # Execute an action
    result = connector.execute("send", {"payload": {"message": "Hello"}})
"""

from src.connectors.base import BaseConnector, ConnectorConfig
from src.connectors.registry import ConnectorRegistry

__all__ = [
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorRegistry",
]
