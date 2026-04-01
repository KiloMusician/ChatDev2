"""Contract tests for unified orchestration bridge response normalization."""

from __future__ import annotations

from pathlib import Path

import pytest
from src.orchestration.agent_registry import AgentCapability, RegisteredAgent
from src.orchestration.unified_orchestration_bridge import TaskStatus, UnifiedOrchestrationBridge

pytestmark = pytest.mark.smoke


class _FakeRegistry:
    def __init__(self, agent: RegisteredAgent) -> None:
        self._agent = agent
        self.status_updates: list[tuple[str, str]] = []
        self.execution_records: list[tuple[str, bool]] = []

    def find_best_agent_for_task(
        self,
        required_capabilities: list[str],
        task_complexity: str = "medium",
        prefer_local: bool = True,
    ) -> RegisteredAgent | None:
        del required_capabilities, task_complexity, prefer_local
        return self._agent

    def update_agent_status(self, agent_id: str, status: str, metadata: dict | None = None) -> bool:
        del metadata
        self.status_updates.append((agent_id, status))
        return True

    def record_execution(self, agent_id: str, success: bool, duration_seconds: float) -> None:
        del duration_seconds
        self.execution_records.append((agent_id, success))

    def get_agent(self, agent_id: str) -> RegisteredAgent | None:
        if agent_id == self._agent.agent_id:
            return self._agent
        return None


@pytest.fixture
def bridge(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> UnifiedOrchestrationBridge:
    agent = RegisteredAgent(
        agent_id="docker-test",
        name="Docker Test Agent",
        agent_type="docker",
        capabilities=[AgentCapability(name="containers", description="Container operations")],
        status="idle",
    )
    fake_registry = _FakeRegistry(agent)
    monkeypatch.setattr(
        "src.orchestration.unified_orchestration_bridge.get_agent_registry",
        lambda: fake_registry,
    )
    return UnifiedOrchestrationBridge(execution_log_path=tmp_path / "orchestration-log.jsonl")


def test_normalize_response_contract_adds_status_and_success() -> None:
    normalized = UnifiedOrchestrationBridge._normalize_response_contract({"output": "ok"})
    assert normalized["status"] == "success"
    assert normalized["success"] is True

    failed = UnifiedOrchestrationBridge._normalize_response_contract({"error": "boom"})
    assert failed["status"] == "failed"
    assert failed["success"] is False


def test_execute_task_normalizes_status_only_payload(bridge: UnifiedOrchestrationBridge) -> None:
    bridge.executors["docker"] = lambda *_args: {"status": "success", "message": "done"}
    task = bridge.create_task(
        description="Check docker status",
        required_capabilities=["containers"],
        input_data={"action": "status"},
    )

    result = bridge.execute_task(task)

    assert result.success is True
    assert isinstance(result.output, dict)
    assert result.output["status"] == "success"
    assert result.output["success"] is True
    assert task.status == TaskStatus.COMPLETED


def test_execute_task_respects_failure_contract(bridge: UnifiedOrchestrationBridge) -> None:
    bridge.executors["docker"] = lambda *_args: {"status": "failed", "error": "docker offline"}
    task = bridge.create_task(
        description="Check docker status",
        required_capabilities=["containers"],
        input_data={"action": "status"},
    )

    result = bridge.execute_task(task)

    assert result.success is False
    assert isinstance(result.output, dict)
    assert result.output["status"] == "failed"
    assert result.output["success"] is False
    assert result.error == "docker offline"
    assert task.status == TaskStatus.FAILED
