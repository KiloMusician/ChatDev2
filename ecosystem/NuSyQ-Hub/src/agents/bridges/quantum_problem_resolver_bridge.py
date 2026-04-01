"""Quantum Problem Resolver Bridge - Hub-aware compatibility layer."""

from pathlib import Path
from typing import Any

from src.agents.agent_orchestration_hub import get_agent_orchestration_hub
from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


class QuantumProblemResolver:
    """Compatibility wrapper that escalates through the hub."""

    def __init__(self, root_path: Path | None = None, hub: Any | None = None) -> None:
        """Initialize QuantumProblemResolver with root_path, hub."""
        self.root_path = root_path or Path.cwd()
        self._hub = hub or get_agent_orchestration_hub(root_path=self.root_path)

    async def resolve_problem(
        self,
        problem_type: str,
        problem_data: dict[str, Any],
        context: dict[str, Any] | None = None,
        initial_service: str = "quantum_resolver",
    ) -> dict[str, Any]:
        """Resolve a problem with healing escalation."""
        context = context or {}
        if context.get("simulate"):
            return {
                "status": "success",
                "service": initial_service,
                "simulated": True,
                "problem_type": problem_type,
            }

        description = problem_data.get("description") or problem_type
        context = {**context, "problem_type": problem_type, "problem_data": problem_data}
        return await self._hub.execute_with_healing(
            task_description=description,
            initial_service=initial_service,
            context=context,
        )


__all__ = ["QuantumProblemResolver"]
