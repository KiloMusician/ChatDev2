"""Contract tests for closed-loop Council→ChatDev execution status semantics."""

from __future__ import annotations

import pytest
from src.orchestration.council_orchestrator_chatdev_loop import CouncilOrchestratorChatDevLoop


@pytest.mark.asyncio
async def test_propose_and_execute_reports_failed_when_chatdev_fails(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loop = CouncilOrchestratorChatDevLoop(auto_vote=True, state_dir=tmp_path / "state")
    monkeypatch.setattr(loop.orchestrator, "submit_task", lambda _task: None)

    async def _fake_execute(*_args, **_kwargs):
        return {"success": False, "status": "failed", "error": "chatdev failure"}

    monkeypatch.setattr(loop, "_execute_chatdev_task", _fake_execute)

    result = await loop.propose_and_execute("Create a calculator", "CODE_GENERATION")

    assert result["success"] is False
    assert result["status"] == "failed"
    assert result["error"] == "chatdev failure"
    assert result["chatdev_result"]["status"] == "failed"


@pytest.mark.asyncio
async def test_propose_and_execute_reports_completed_when_chatdev_succeeds(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loop = CouncilOrchestratorChatDevLoop(auto_vote=True, state_dir=tmp_path / "state")
    monkeypatch.setattr(loop.orchestrator, "submit_task", lambda _task: None)

    async def _fake_execute(*_args, **_kwargs):
        return {"success": True, "status": "success", "task_id": "task-1"}

    monkeypatch.setattr(loop, "_execute_chatdev_task", _fake_execute)

    result = await loop.propose_and_execute("Create a calculator", "CODE_GENERATION")

    assert result["success"] is True
    assert result["status"] == "completed"
    assert result["chatdev_result"]["status"] == "success"
