"""Multi AI Orchestrator Bridge - Hub-backed compatibility wrapper."""

from pathlib import Path
from typing import Any

from src.agents.agent_orchestration_hub import get_agent_orchestration_hub
from src.agents.agent_orchestration_types import TaskPriority
from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


class MultiAIOrchestrator:
    """Compatibility wrapper for legacy MultiAIOrchestrator usage."""

    def __init__(self, root_path: Path | None = None, hub: Any | None = None) -> None:
        """Initialize MultiAIOrchestrator with root_path, hub."""
        self.root_path = root_path or Path.cwd()
        self._hub = hub or get_agent_orchestration_hub(root_path=self.root_path)

    async def orchestrate_task(
        self,
        task_type: str,
        content: str,
        context: dict[str, Any] | None = None,
        priority: TaskPriority | str = TaskPriority.NORMAL,
        target_service: str | None = None,
    ) -> dict[str, Any]:
        """Route a task through the hub."""
        context = context or {}
        if isinstance(priority, str):
            try:
                priority = TaskPriority[priority.upper()]
            except KeyError:
                priority = TaskPriority.NORMAL

        return await self._hub.route_task(
            task_type=task_type,
            description=content,
            context=context,
            priority=priority,
            target_service=target_service,
        )


__all__ = ["MultiAIOrchestrator"]
