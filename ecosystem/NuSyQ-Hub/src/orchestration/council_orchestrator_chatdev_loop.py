"""Council → ChatDev closed-loop execution orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class _SimpleOrchestrator:
    """Minimal orchestrator stub used by the council loop."""

    def submit_task(self, task: Any) -> None:
        pass


class CouncilOrchestratorChatDevLoop:
    """Coordinates council voting with ChatDev task execution."""

    def __init__(
        self,
        auto_vote: bool = False,
        state_dir: Path | str | None = None,
    ) -> None:
        self.auto_vote = auto_vote
        self.state_dir = Path(state_dir) if state_dir else Path("state") / "council"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.orchestrator = _SimpleOrchestrator()

    async def propose_and_execute(
        self, task_description: str, task_type: str = "CODE_GENERATION"
    ) -> dict[str, Any]:
        """Submit task to council, then execute via ChatDev. Returns normalized result."""
        self.orchestrator.submit_task({"description": task_description, "type": task_type})
        chatdev_result = await self._execute_chatdev_task(task_description, task_type)
        if not chatdev_result.get("success"):
            return {
                "success": False,
                "status": chatdev_result.get("status", "failed"),
                "error": chatdev_result.get("error", "unknown"),
                "chatdev_result": chatdev_result,
            }
        return {
            "success": True,
            "status": "completed",
            "chatdev_result": chatdev_result,
        }

    async def _execute_chatdev_task(self, task_description: str, task_type: str) -> dict[str, Any]:
        """Override in subclasses or monkeypatch in tests."""
        return {"success": False, "status": "not_implemented"}
