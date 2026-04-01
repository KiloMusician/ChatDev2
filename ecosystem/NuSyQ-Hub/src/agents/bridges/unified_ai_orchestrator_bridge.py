"""Unified AI Orchestrator Bridge - Hub-backed compatibility layer.

Routes orchestration calls through AgentOrchestrationHub while preserving
familiar entry points for legacy integrations.
"""

from pathlib import Path
from typing import Any

from src.agents.agent_orchestration_hub import get_agent_orchestration_hub
from src.agents.agent_orchestration_types import ExecutionMode, TaskPriority
from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


class UnifiedAIOrchestrator:
    """Compatibility wrapper for unified orchestration calls."""

    def __init__(self, root_path: Path | None = None, hub: Any | None = None) -> None:
        """Initialize UnifiedAIOrchestrator with root_path, hub."""
        self.root_path = root_path or Path.cwd()
        self._hub = hub or get_agent_orchestration_hub(root_path=self.root_path)

    async def orchestrate_task(
        self,
        content: str,
        task_type: str = "analysis",
        context: dict[str, Any] | None = None,
        services: list[str] | None = None,
        execution_mode: ExecutionMode | str = ExecutionMode.PARALLEL,
        priority: TaskPriority | str = TaskPriority.NORMAL,
    ) -> dict[str, Any]:
        """Orchestrate a task via the hub."""
        context = context or {}
        if isinstance(execution_mode, str):
            try:
                execution_mode = ExecutionMode[execution_mode.upper()]
            except KeyError:
                execution_mode = ExecutionMode.PARALLEL
        if isinstance(priority, str):
            try:
                priority = TaskPriority[priority.upper()]
            except KeyError:
                priority = TaskPriority.NORMAL

        if services:
            return await self._hub.orchestrate_multi_agent_task(
                task_description=content,
                services=services,
                mode=execution_mode,
                context=context,
            )

        return await self._hub.route_task(
            task_type=task_type,
            description=content,
            context=context,
            priority=priority,
        )


__all__ = ["UnifiedAIOrchestrator"]
