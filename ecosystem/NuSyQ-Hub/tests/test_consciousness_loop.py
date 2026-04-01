"""Tests for ConsciousnessLoop adapter - graceful degradation and caching."""

import time
from unittest.mock import MagicMock

import pytest
from src.orchestration.consciousness_loop import ConsciousnessLoop


def test_breathing_factor_defaults_to_one_when_bridge_unavailable():
    """When SimulatedVerse is unreachable, factor must be 1.0 (no-op)."""
    loop = ConsciousnessLoop()
    loop._bridge = None  # simulate unavailable
    assert loop.breathing_factor == 1.0


def test_breathing_factor_cached_for_30s():
    """Factor should not re-query the bridge within the cache TTL."""
    loop = ConsciousnessLoop()
    mock_bridge = MagicMock()
    mock_bridge.get_breathing_factor.return_value = 0.85
    loop._bridge = mock_bridge
    loop._factor_expires_at = time.monotonic() + 60  # cache valid
    loop._cached_factor = 0.85

    _ = loop.breathing_factor
    _ = loop.breathing_factor
    mock_bridge.get_breathing_factor.assert_not_called()  # cached


def test_approval_auto_approves_when_bridge_unavailable():
    """Culture Ship veto must auto-approve when bridge is down."""
    loop = ConsciousnessLoop()
    loop._bridge = None
    approval = loop.request_approval("execute_task", {"task_id": "t1"})
    assert approval.approved is True
    assert "unavailable" in approval.reason.lower()


def test_emit_event_does_not_raise_when_bridge_unavailable():
    """Fire-and-forget event logging must never raise."""
    loop = ConsciousnessLoop()
    loop._bridge = None
    # Must not raise
    loop.emit_event_sync("task_started", {"task_id": "t1"})


def test_consciousness_state_returns_dormant_when_unavailable():
    """Brief state must return a dormant snapshot when bridge is down."""
    loop = ConsciousnessLoop()
    loop._bridge = None
    state = loop.get_brief_state()
    assert state["available"] is False
    assert state["stage"] == "dormant"


def test_adaptive_timeout_scales_with_factor():
    """_get_adaptive_timeout must multiply base by breathing_factor."""
    import time

    from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator
    from src.orchestration.consciousness_loop import ConsciousnessLoop

    orch = BackgroundTaskOrchestrator.__new__(BackgroundTaskOrchestrator)
    loop = ConsciousnessLoop()
    loop._bridge = None  # unavailable -> factor = 1.0
    orch._consciousness_loop = loop
    assert orch._get_adaptive_timeout(600) == pytest.approx(600.0)

    # Simulate accelerating factor
    loop._cached_factor = 0.85
    loop._factor_expires_at = time.monotonic() + 60
    assert orch._get_adaptive_timeout(600) == pytest.approx(510.0)


def test_veto_blocks_requires_approval_task():
    """Culture Ship veto should set task to FAILED and return early."""
    import asyncio
    from unittest.mock import MagicMock

    from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator
    from src.orchestration.consciousness_loop import ShipApproval

    orch = BackgroundTaskOrchestrator.__new__(BackgroundTaskOrchestrator)
    # Set up minimal required attributes
    orch._consciousness_loop = MagicMock()
    orch._consciousness_loop.request_approval.return_value = ShipApproval(
        approved=False, reason="test veto"
    )
    # Mock required methods/attributes that execute_task will call
    orch._save_tasks = MagicMock()

    # Import task-related classes
    from src.orchestration.background_task_orchestrator import (
        BackgroundTask,
        TaskStatus,
        TaskTarget,
    )

    task = BackgroundTask(
        task_id="t-veto-test",
        prompt="fix security vulnerability",
        target=TaskTarget.OLLAMA,
        metadata={"requires_approval": True},
    )
    task.status = TaskStatus.QUEUED

    result = asyncio.run(orch.execute_task(task))
    assert result.status == TaskStatus.FAILED
    assert "veto" in result.error.lower()
