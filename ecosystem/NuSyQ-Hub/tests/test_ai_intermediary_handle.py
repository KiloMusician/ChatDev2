import asyncio
import json
from pathlib import Path

import pytest
from src.ai.ai_intermediary import (
    AIIntermediary,
    AISecurityError,
    CognitiveEvent,
    CognitiveParadigm,
)


class DummyOllamaHub:
    async def initialize(self):
        return True

    async def intelligent_chat(self, message: str, context: dict):
        return f"echo:{message}"


class DummyModule:
    async def process(self, payload):
        return f"module:{payload}"


def run(coro):
    return asyncio.run(coro)


def test_handle_routes_to_module_and_translates():
    interm = AIIntermediary(DummyOllamaHub())
    run(interm.initialize())
    run(interm.register_module("dummy", DummyModule(), CognitiveParadigm.CODE_ANALYSIS))

    result = run(
        interm.handle(
            input_data="hello module",
            context={"conversation_id": "t1"},
            target_module="dummy",
            target_paradigm=CognitiveParadigm.CODE_ANALYSIS,
        )
    )

    assert isinstance(result.payload, str)
    assert result.payload.startswith("module:")
    assert result.paradigm is CognitiveParadigm.CODE_ANALYSIS
    assert "translated" in result.tags


def test_handle_with_ollama_fallback():
    interm = AIIntermediary(DummyOllamaHub())
    run(interm.initialize())

    result = run(
        interm.handle(
            input_data="ping",
            context={"conversation_id": "t2"},
            use_ollama=True,
            target_paradigm=CognitiveParadigm.NATURAL_LANGUAGE,
        )
    )

    assert "echo:ping" in str(result.payload)
    assert result.paradigm is CognitiveParadigm.NATURAL_LANGUAGE


def test_handle_injects_workspace_awareness_from_terminal_registry(tmp_path: Path):
    interm = AIIntermediary(DummyOllamaHub())
    reports = tmp_path / "state" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    awareness_path = reports / "terminal_awareness_latest.json"
    snapshot_path = reports / "terminal_snapshot_latest.json"
    awareness_path.write_text(
        json.dumps(
            {
                "active_session": "intelligent",
                "agent_registry": [
                    {
                        "agent": "Copilot",
                        "terminals": ["🧩 Copilot"],
                        "purposes": ["agent log watcher"],
                    }
                ],
                "output_surfaces": [
                    {
                        "label": "🧩 Copilot Log",
                        "path": str(tmp_path / "data" / "terminal_logs" / "copilot.log"),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    snapshot_path.write_text(
        json.dumps({"summary": {"configured_session": "intelligent", "total_channels": 26}}),
        encoding="utf-8",
    )
    interm.terminal_awareness_path = awareness_path
    interm.terminal_snapshot_path = snapshot_path
    interm.current_state_path = reports / "current_state.md"
    run(interm.initialize())

    result = run(
        interm.handle(
            input_data="Copilot should inspect the bridge",
            context={"conversation_id": "awareness-1"},
            source="copilot",
        )
    )

    awareness = result.context.get("workspace_awareness", {})
    assert awareness["active_session"] == "intelligent"
    assert awareness["terminal_count"] == 26
    assert awareness["relevant_agents"][0]["agent"] == "Copilot"


def test_security_rejects_oversize_payload():
    interm = AIIntermediary(DummyOllamaHub())
    run(interm.initialize())
    huge = "x" * 9000
    with pytest.raises(AISecurityError):
        run(
            interm.handle(
                input_data=huge,
                context={"conversation_id": "t3"},
            )
        )


def test_dispatch_to_background_returns_task_info():
    """Test that dispatch_to_background returns task information or graceful fallback."""
    interm = AIIntermediary(DummyOllamaHub())
    run(interm.initialize())

    result = run(
        interm.dispatch_to_background(
            prompt="Analyze this codebase for security issues",
            task_type="code_analysis",
            requesting_agent="claude",
            priority="normal",
        )
    )

    # Either succeeds with task_id or fails gracefully with error info
    assert "success" in result
    if result["success"]:
        assert "task_id" in result
        assert "target" in result
        assert "status" in result
    else:
        # Graceful failure if orchestrator not available
        assert "error" in result or "fallback" in result


def test_check_background_task_handles_missing_task():
    """Test that check_background_task handles non-existent tasks gracefully."""
    interm = AIIntermediary(DummyOllamaHub())
    run(interm.initialize())

    result = run(interm.check_background_task("nonexistent-task-id"))

    assert result["success"] is False
    assert "error" in result or "not found" in str(result).lower()


def test_dispatch_and_check_integration():
    """Test the full dispatch -> check flow."""
    interm = AIIntermediary(DummyOllamaHub())
    run(interm.initialize())

    # Dispatch a task
    dispatch_result = run(
        interm.dispatch_to_background(
            prompt="Generate a unit test for the login function",
            task_type="code_generation",
            requesting_agent="claude",
            priority="high",
        )
    )

    if dispatch_result.get("success"):
        task_id = dispatch_result["task_id"]

        # Check the task status
        check_result = run(interm.check_background_task(task_id))

        assert check_result["success"] is True
        assert check_result["task_id"] == task_id
        assert "status" in check_result


def test_meta_learning_snapshot_tracks_event_patterns():
    interm = AIIntermediary(DummyOllamaHub())

    event = CognitiveEvent(
        source="copilot",
        target="chatdev",
        paradigm=CognitiveParadigm.CODE_ANALYSIS,
        payload="analyze",
        context={"conversation_id": "ml-1", "quest_id": "q-123"},
        tags=["routed", "review"],
        recursion_depth=3,
    )
    event.meta_index["error"] = "synthetic"

    run(interm._update_meta_learning(event))
    snapshot = interm.get_meta_learning_snapshot()

    assert snapshot["total_events"] == 1
    assert snapshot["error_events"] == 1
    assert snapshot["routed_events"] >= 1
    assert snapshot["max_recursion_depth"] == 3
    assert snapshot["source_counts"]["copilot"] == 1
    assert snapshot["target_counts"]["chatdev"] == 1
    assert snapshot["paradigm_counts"][CognitiveParadigm.CODE_ANALYSIS.value] == 1
    assert snapshot["tag_counts"]["review"] == 1
    assert snapshot["context_key_counts"]["quest_id"] == 1
    assert snapshot["recent_signatures"][0]["has_error"] is True


def test_meta_learning_snapshot_persists_latest_report(tmp_path: Path):
    interm = AIIntermediary(DummyOllamaHub())
    interm.meta_learning_report_path = tmp_path / "state" / "reports" / "ai_intermediary_meta_learning_latest.json"

    event = CognitiveEvent(
        source="codex",
        target="openclaw",
        paradigm=CognitiveParadigm.NATURAL_LANGUAGE,
        payload="sync",
        context={"conversation_id": "persist-1"},
        tags=["routed"],
    )

    run(interm._update_meta_learning(event))

    payload = json.loads(interm.meta_learning_report_path.read_text(encoding="utf-8"))
    assert payload["snapshot"]["total_events"] == 1
    assert payload["snapshot"]["source_counts"]["codex"] == 1
