"""Contract tests for ZenCodexBridge response envelopes."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from src.integration.zen_codex_bridge import ZenCodexBridge

pytestmark = [pytest.mark.integration]


def test_zen_agent_query_ecosystem_includes_success_flag() -> None:
    bridge = ZenCodexBridge()
    result = bridge.zen_agent_query_ecosystem(
        agent_name="copilot",
        capability="analyze_code",
        parameters={"path": "src/main.py"},
    )
    assert result["success"] is True
    assert result["status"] == "acknowledged"


def test_zen_learning_error_paths_include_success_false() -> None:
    bridge = ZenCodexBridge()

    learn_result = bridge.learn_from_error("ImportError", "module missing")
    assert learn_result["success"] is False
    assert learn_result["status"] == "error"

    success_feedback = bridge.learn_from_success("ImportError", "fixed import")
    assert success_feedback["success"] is False
    assert success_feedback["status"] == "error"

    orchestration = bridge.orchestrate_multi_agent_task("Refactor module")
    assert orchestration["success"] is False
    assert orchestration["status"] == "error"


@dataclass
class _FakeEvent:
    id: str


class _FakeObserver:
    def observe_error(self, **_kwargs):
        return _FakeEvent(id="evt-123")


class _FakeBuilder:
    def learn_from_events(self, **_kwargs):
        return {"rules_saved": 2}


def test_zen_learning_success_path_includes_success_true(monkeypatch) -> None:
    bridge = ZenCodexBridge()
    bridge.initialized = True
    bridge.error_observer = _FakeObserver()
    bridge.codex_builder = _FakeBuilder()
    monkeypatch.setattr(
        bridge,
        "get_wisdom_for_error",
        lambda *_args, **_kwargs: {"matched_rules": [{"id": "r-1"}], "suggestions": []},
    )

    result = bridge.learn_from_error("ValueError", "bad value")
    assert result["success"] is True
    assert result["status"] == "learned"
    assert result["event_id"] == "evt-123"

    feedback = bridge.learn_from_success("ValueError", "validated input")
    assert feedback["success"] is True
    assert feedback["status"] == "recorded"

    orchestration = bridge.orchestrate_multi_agent_task("Stabilize bridge")
    assert orchestration["success"] is True
    assert orchestration["status"] == "planned"
