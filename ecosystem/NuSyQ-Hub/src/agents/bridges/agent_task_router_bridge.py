"""AgentTaskRouter Bridge - Legacy Compatibility Wrapper.

This module provides backward compatibility for code using the old AgentTaskRouter.
All routing now goes through the AgentOrchestrationHub.

Canonical implementation: src/agents/agent_orchestration_hub.py
"""

from pathlib import Path
from typing import Any

from src.agents.agent_orchestration_hub import (TaskPriority,
                                                get_agent_orchestration_hub)
from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


class AgentTaskRouter:
    """Legacy compatibility wrapper for AgentTaskRouter.

    DEPRECATED: Use AgentOrchestrationHub.route_task() instead.

    This class redirects all calls to the AgentOrchestrationHub while
    maintaining the old interface for backward compatibility.
    """

    def __init__(self, repository_path: str | Path | None = None):
        """Initialize the legacy router (redirects to hub).

        Args:
            repository_path: Repository root path
        """
        self.repository_path = Path(repository_path) if repository_path else Path.cwd()
        self._hub = get_agent_orchestration_hub(root_path=self.repository_path)

        logger.warning(
            "AgentTaskRouter is deprecated. Use AgentOrchestrationHub instead.",
            extra={"caller": "AgentTaskRouter.__init__"},
        )

    async def route_task(
        self,
        task_type: str,
        description: str,
        context: dict[str, Any] | None = None,
        priority: str = "NORMAL",
        target_system: str | None = None,
    ) -> dict[str, Any]:
        """Route a task (legacy interface).

        Args:
            task_type: Type of task
            description: Task description
            context: Task context
            priority: Priority level (NORMAL, HIGH, etc.)
            target_system: Target service ID

        Returns:
            Task result
        """
        # Convert priority string to enum
        try:
            priority_enum = TaskPriority[priority.upper()]
        except KeyError:
            priority_enum = TaskPriority.NORMAL

        # Route through hub
        result = await self._hub.route_task(
            task_type=task_type,
            description=description,
            context=context,
            priority=priority_enum,
            target_service=target_system,
        )

        return result


__all__ = ["AgentTaskRouter"]
