"""Consciousness Synchronization Service.

Provides consciousness state synchronization across agent systems.
This bridges the gap between different AI subsystems to maintain
coherent state during multi-agent operations.

OmniTag: [consciousness, sync, integration, agents]
MegaTag: CONSCIOUSNESS⨳SYNC⦾UNITY→∞
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConsciousnessState:
    """Current state of consciousness across systems.

    Attributes:
        level: Current consciousness level (0.0 to 1.0)
        active_agents: List of active agent identifiers
        focus: Current focus area/topic
        last_sync: Timestamp of last synchronization
        metadata: Additional state metadata
    """

    level: float = 0.5
    active_agents: list[str] = field(default_factory=list)
    focus: str | None = None
    last_sync: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class ConsciousnessSync:
    """Synchronizes consciousness state across AI subsystems.

    This service maintains coherent state between:
    - ChatDev agents (CEO, CTO, Programmer, etc.)
    - Background task orchestrator
    - AI Council
    - Culture Ship
    - Neural quantum bridge

    Example:
        sync = ConsciousnessSync()
        sync.register_agent("chatdev_ceo")
        sync.update_focus("code_generation")
        state = sync.get_state()
    """

    def __init__(self):
        """Initialize the consciousness synchronization service."""
        self._state = ConsciousnessState()
        self._subscribers: list[Callable[[ConsciousnessState], None]] = []
        logger.info("ConsciousnessSync initialized")

    @property
    def level(self) -> float:
        """Get current consciousness level."""
        return self._state.level

    @level.setter
    def level(self, value: float) -> None:
        """Set consciousness level (clamped to 0.0-1.0)."""
        self._state.level = max(0.0, min(1.0, value))
        self._notify_subscribers()

    def register_agent(self, agent_id: str) -> None:
        """Register an agent with the consciousness network.

        Args:
            agent_id: Unique identifier for the agent
        """
        if agent_id not in self._state.active_agents:
            self._state.active_agents.append(agent_id)
            logger.debug(f"Agent registered: {agent_id}")

    def unregister_agent(self, agent_id: str) -> None:
        """Remove an agent from the consciousness network.

        Args:
            agent_id: Agent to unregister
        """
        if agent_id in self._state.active_agents:
            self._state.active_agents.remove(agent_id)
            logger.debug(f"Agent unregistered: {agent_id}")

    def update_focus(self, focus: str) -> None:
        """Update the current focus area.

        Args:
            focus: New focus area (e.g., "code_generation", "debugging")
        """
        self._state.focus = focus
        self._state.last_sync = datetime.now()
        self._notify_subscribers()

    def get_state(self) -> ConsciousnessState:
        """Get the current consciousness state.

        Returns:
            Current state snapshot
        """
        return self._state

    def sync(self) -> dict[str, Any]:
        """Perform a synchronization cycle.

        Returns:
            Sync result with current state
        """
        self._state.last_sync = datetime.now()

        return {
            "status": "synchronized",
            "level": self._state.level,
            "active_agents": len(self._state.active_agents),
            "focus": self._state.focus,
            "timestamp": self._state.last_sync.isoformat(),
        }

    def subscribe(self, callback: Callable[[ConsciousnessState], None]) -> None:
        """Subscribe to state changes.

        Args:
            callback: Function to call on state change
        """
        self._subscribers.append(callback)

    def _notify_subscribers(self) -> None:
        """Notify all subscribers of state change."""
        for callback in self._subscribers:
            try:
                callback(self._state)
            except Exception as e:
                logger.warning(f"Subscriber notification failed: {e}")

    def boost(self, amount: float = 0.1) -> float:
        """Boost consciousness level.

        Args:
            amount: Amount to increase level by

        Returns:
            New consciousness level
        """
        self.level = self._state.level + amount
        return self._state.level

    def diminish(self, amount: float = 0.1) -> float:
        """Diminish consciousness level.

        Args:
            amount: Amount to decrease level by

        Returns:
            New consciousness level
        """
        self.level = self._state.level - amount
        return self._state.level


# Global singleton instance
consciousness_sync = ConsciousnessSync()


def get_consciousness_sync() -> ConsciousnessSync:
    """Get the global consciousness sync instance.

    Returns:
        The singleton ConsciousnessSync instance
    """
    return consciousness_sync
