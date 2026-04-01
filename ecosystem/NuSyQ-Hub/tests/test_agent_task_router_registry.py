import asyncio
from pathlib import Path

from src.tools.agent_task_router import AgentTaskRouter


class _StubRouter(AgentTaskRouter):
    def __init__(self) -> None:
        super().__init__(repo_root=Path("."))
        self.calls = []
        self._system_handlers["stub_system"] = self._stub_handler
        # Update _valid_targets to include the stub system
        self._valid_targets = {"auto", *self._system_handlers.keys()}
        # Disable SpecializationLearner so auto-routing always submits to orchestrator
        # (predictable for tests — avoids live Ollama routing based on real disk state)
        self._specialization_learner = False  # sentinel: skip learner lookup

    async def _stub_handler(self, task):
        self.calls.append(task.task_id)
        return {"status": "success", "system": "stub_system", "task_id": task.task_id}


def test_router_registry_dispatch():
    router = _StubRouter()
    result = asyncio.run(
        router.route_task(
            task_type="analyze",
            description="test",
            context={},
            target_system="stub_system",
        )
    )
    assert result["status"] == "success"
    assert result["system"] == "stub_system"
    assert router.calls  # handler was invoked


def test_router_unknown_target():
    router = _StubRouter()
    result = asyncio.run(
        router.route_task(
            task_type="analyze",
            description="test",
            context={},
            target_system="unknown_system",  # type: ignore[arg-type]
        )
    )
    # Unknown systems default to "auto" which submits to orchestrator
    assert result["status"] == "submitted"
    assert "task_id" in result


def test_router_target_aliases_resolve_to_canonical_system():
    router = _StubRouter()
    assert router._resolve_target_alias("vscode_copilot") == "copilot"
    assert router._resolve_target_alias("codex_cli") == "codex"
    assert router._resolve_target_alias("claude") == "claude_cli"


def test_router_auto_submission_includes_success_contract():
    router = _StubRouter()
    result = asyncio.run(
        router.route_task(
            task_type="analyze",
            description="contract check",
            context={},
            target_system="auto",
        )
    )
    assert result["status"] == "submitted"
    assert result["success"] is True
