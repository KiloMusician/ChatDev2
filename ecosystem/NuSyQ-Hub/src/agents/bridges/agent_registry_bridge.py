"""Agent Registry Bridge - Sync registry entries with the hub."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from src.agents.agent_orchestration_hub import get_agent_orchestration_hub
from src.agents.agent_orchestration_types import ServiceCapability
from src.LOGGING.modular_logging_system import get_logger
from src.orchestration.agent_registry import (AgentCapability, AgentRegistry,
                                              RegisteredAgent)

logger = get_logger(__name__)


class AgentRegistryBridge:
    """Bridge between AgentRegistry and AgentOrchestrationHub."""

    def __init__(
        self,
        root_path: Path | None = None,
        registry_path: Path | None = None,
        hub: Any | None = None,
    ) -> None:
        """Initialize registry bridge with optional paths and hub instance."""
        self.root_path = root_path or Path.cwd()
        self.registry = AgentRegistry(registry_path=registry_path)
        self._hub = hub or get_agent_orchestration_hub(root_path=self.root_path)

    def _normalize_capabilities(
        self, capabilities: Iterable[AgentCapability | dict[str, Any] | str]
    ) -> list[AgentCapability]:
        normalized: list[AgentCapability] = []
        for cap in capabilities:
            if isinstance(cap, AgentCapability):
                normalized.append(cap)
            elif isinstance(cap, dict):
                normalized.append(AgentCapability(**cap))
            else:
                name = str(cap)
                normalized.append(
                    AgentCapability(
                        name=name,
                        description=name,
                        tags=["bridged"],
                    )
                )
        return normalized

    def register_agent(
        self,
        agent_id: str,
        name: str,
        agent_type: str,
        capabilities: Iterable[AgentCapability | dict[str, Any] | str],
        endpoint: str | None = None,
        metadata: dict[str, Any] | None = None,
        override: bool = False,
    ) -> bool:
        """Register an agent in both registry and hub."""
        metadata = metadata or {}
        caps = self._normalize_capabilities(capabilities)
        agent = RegisteredAgent(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type,
            capabilities=caps,
            endpoint=endpoint,
            metadata=metadata,
        )

        if not self.registry.register_agent(agent, override=override):
            return False

        service_caps = [
            ServiceCapability(
                name=cap.name,
                description=cap.description,
                priority=5,
                metadata={"source": "agent_registry"},
            )
            for cap in caps
        ]
        self._hub.register_service(
            service_id=agent_id,
            name=name,
            capabilities=service_caps,
            endpoint=endpoint,
            metadata=metadata,
        )

        return True

    def get_agent(self, agent_id: str) -> RegisteredAgent | None:
        """Fetch an agent from the registry."""
        return self.registry.get_agent(agent_id)

    def find_agents_by_capability(
        self, capability_name: str, status_filter: str | None = None
    ) -> list[RegisteredAgent]:
        """Proxy capability search to the registry."""
        result = self.registry.find_agents_by_capability(capability_name, status_filter)
        if isinstance(result, list):
            return [agent for agent in result if isinstance(agent, RegisteredAgent)]
        return []


__all__ = ["AgentRegistryBridge"]
