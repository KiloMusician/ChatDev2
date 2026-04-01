"""Focused tests for AgentCoordinationLayer normalization and locks."""

import asyncio

import pytest
from src.system.agent_coordination_layer import AgentCoordinationLayer, TaskLockStatus


def test_coerce_agent_accepts_string(tmp_path):
    """String agent IDs should normalize to AgentType."""
    layer = AgentCoordinationLayer(state_dir=tmp_path / "coord")
    assert layer._coerce_agent("copilot").value == "copilot"
    assert layer._coerce_agent("CODEX").value == "codex"


def test_coerce_agent_rejects_unknown(tmp_path):
    """Invalid agent strings should fail clearly."""
    layer = AgentCoordinationLayer(state_dir=tmp_path / "coord")
    with pytest.raises(ValueError):
        layer._coerce_agent("unknown-agent")


def test_request_release_lock_with_string_agents(tmp_path, monkeypatch):
    """Lock APIs should work when callers pass string agent IDs."""
    layer = AgentCoordinationLayer(state_dir=tmp_path / "coord")

    async def fake_init() -> None:
        return None

    async def fake_emit(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr(layer, "init", fake_init)
    monkeypatch.setattr(layer, "_emit_lock_event", fake_emit)

    status, lock = asyncio.run(layer.request_task_lock("task-1", "copilot"))
    assert status == TaskLockStatus.GRANTED
    assert lock is not None
    assert lock.locked_by.value == "copilot"

    released = asyncio.run(layer.release_task_lock("task-1", "copilot"))
    assert released is True
