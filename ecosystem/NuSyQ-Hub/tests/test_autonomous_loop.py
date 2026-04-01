"""Tests for src/automation/autonomous_loop.py.

All imports are inside test functions to avoid module-level side effects.
Heavy dependencies (orchestrators, monitors, quest engines) are patched.
"""

import json
import os
import sys
import types
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_loop(tmp_path: Path, **kwargs: Any):
    """Create an AutonomousLoop with all heavy dependencies stubbed."""

    # Build a minimal stub for UnifiedAIOrchestrator
    mock_orchestrator_cls = MagicMock()
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator_instance.orchestration_active = False
    mock_orchestrator_cls.return_value = mock_orchestrator_instance

    # Patch at the module level so __init__ picks them up
    with (
        patch("src.automation.autonomous_loop.UnifiedAIOrchestrator", mock_orchestrator_cls),
        patch("src.automation.autonomous_loop.AutonomousMonitor", None),
        patch("src.automation.autonomous_loop.QuestEngine", None),
        patch("src.automation.autonomous_loop.QUEST_ENGINE_AVAILABLE", False),
        patch("src.automation.autonomous_loop.BackgroundTaskOrchestrator", None),
        patch("src.automation.autonomous_loop.BACKGROUND_ORCHESTRATOR_AVAILABLE", False),
        patch("src.automation.autonomous_loop.ResultApplier", None),
        patch("src.automation.autonomous_loop.RESULT_APPLIER_AVAILABLE", False),
    ):
        from src.automation.autonomous_loop import AutonomousLoop

        loop = AutonomousLoop(**kwargs)

    # Redirect file paths to tmp_path so tests don't touch the real repo
    loop.pu_queue_path = tmp_path / "pu_queue.json"
    loop.metrics_path = tmp_path / "execution_metrics.json"
    loop.quest_log_path = tmp_path / "quest_log.jsonl"
    loop.autonomous_feedback_path = tmp_path / "autonomous_feedback.json"
    loop.root = tmp_path

    return loop


# ---------------------------------------------------------------------------
# 1. Module-level constants
# ---------------------------------------------------------------------------

def test_module_imports():
    """Module can be imported without errors."""
    import src.automation.autonomous_loop as mod

    assert mod is not None


def test_quest_engine_available_is_bool():
    """QUEST_ENGINE_AVAILABLE is a boolean."""
    import src.automation.autonomous_loop as mod

    assert isinstance(mod.QUEST_ENGINE_AVAILABLE, bool)


def test_background_orchestrator_available_is_bool():
    """BACKGROUND_ORCHESTRATOR_AVAILABLE is a boolean."""
    import src.automation.autonomous_loop as mod

    assert isinstance(mod.BACKGROUND_ORCHESTRATOR_AVAILABLE, bool)


# ---------------------------------------------------------------------------
# 2. AutonomousLoop.__init__ defaults
# ---------------------------------------------------------------------------

def test_init_defaults(tmp_path: Path):
    """AutonomousLoop initialises with correct defaults."""
    loop = _make_loop(tmp_path)

    assert loop.interval == 30 * 60  # 30 minutes → seconds
    assert loop.mode == "normal"
    assert loop.max_tasks == 3
    assert loop.max_cycles is None
    assert loop.running is False
    assert loop.cycle_count == 0
    assert loop.enable_quest_integration is True
    assert loop.enable_quest_execution is True
    assert loop.enable_background_delegation is True
    assert loop.quest_engine is None
    assert loop.background_orchestrator is None
    assert loop.monitor is None


def test_init_custom_params(tmp_path: Path):
    """AutonomousLoop respects custom constructor arguments."""
    loop = _make_loop(tmp_path, interval_minutes=60, mode="overnight", max_tasks_per_cycle=5, max_cycles=2)

    assert loop.interval == 3600
    assert loop.mode == "overnight"
    assert loop.max_tasks == 5
    assert loop.max_cycles == 2


def test_init_interval_conversion(tmp_path: Path):
    """interval_minutes is converted to seconds."""
    loop = _make_loop(tmp_path, interval_minutes=15)
    assert loop.interval == 900


def test_init_quest_config_defaults(tmp_path: Path):
    """Quest-related config fields have expected defaults."""
    loop = _make_loop(tmp_path)
    assert loop.quest_chapter_name == "Autonomous"
    assert loop.max_quests_per_cycle == 5
    assert "pending" in loop.quest_execution_statuses
    assert "active" in loop.quest_execution_statuses


def test_init_apply_mode_default(tmp_path: Path, monkeypatch: Any):
    """result_apply_mode defaults to 'stage'."""
    monkeypatch.delenv("NUSYQ_AUTONOMOUS_APPLY_MODE", raising=False)
    loop = _make_loop(tmp_path)
    assert loop.result_apply_mode == "stage"


def test_init_apply_mode_env_valid(tmp_path: Path, monkeypatch: Any):
    """result_apply_mode respects a valid env var."""
    monkeypatch.setenv("NUSYQ_AUTONOMOUS_APPLY_MODE", "preview")
    loop = _make_loop(tmp_path)
    assert loop.result_apply_mode == "preview"


def test_init_apply_mode_env_invalid_falls_back(tmp_path: Path, monkeypatch: Any):
    """result_apply_mode falls back to 'stage' for invalid env var."""
    monkeypatch.setenv("NUSYQ_AUTONOMOUS_APPLY_MODE", "bad_value")
    loop = _make_loop(tmp_path)
    assert loop.result_apply_mode == "stage"


def test_init_apply_limit_default(tmp_path: Path, monkeypatch: Any):
    """result_apply_limit defaults to 20."""
    monkeypatch.delenv("NUSYQ_AUTONOMOUS_APPLY_LIMIT", raising=False)
    loop = _make_loop(tmp_path)
    assert loop.result_apply_limit == 20


def test_init_apply_limit_env(tmp_path: Path, monkeypatch: Any):
    """result_apply_limit can be set via env var."""
    monkeypatch.setenv("NUSYQ_AUTONOMOUS_APPLY_LIMIT", "7")
    loop = _make_loop(tmp_path)
    assert loop.result_apply_limit == 7


def test_init_validation_timeout_default(tmp_path: Path, monkeypatch: Any):
    """validation_timeout_seconds defaults to 180."""
    monkeypatch.delenv("NUSYQ_AUTONOMOUS_VALIDATION_TIMEOUT", raising=False)
    loop = _make_loop(tmp_path)
    assert loop.validation_timeout_seconds == 180


# ---------------------------------------------------------------------------
# 3. _map_pu_type
# ---------------------------------------------------------------------------

def test_map_pu_type_known(tmp_path: Path):
    """_map_pu_type maps known types correctly."""
    loop = _make_loop(tmp_path)
    assert loop._map_pu_type("RefactorPU") == "code_refactoring"
    assert loop._map_pu_type("FeaturePU") == "feature_development"
    assert loop._map_pu_type("DocPU") == "documentation"
    assert loop._map_pu_type("TestPU") == "test_generation"
    assert loop._map_pu_type("BugPU") == "bug_fix"


def test_map_pu_type_unknown(tmp_path: Path):
    """_map_pu_type returns 'general_task' for unknown types."""
    loop = _make_loop(tmp_path)
    assert loop._map_pu_type("UnknownPU") == "general_task"
    assert loop._map_pu_type("") == "general_task"


# ---------------------------------------------------------------------------
# 4. _map_priority
# ---------------------------------------------------------------------------

def test_map_priority_known(tmp_path: Path):
    """_map_priority maps known strings to TaskPriority members."""
    from src.orchestration.unified_ai_orchestrator import TaskPriority

    loop = _make_loop(tmp_path)
    assert loop._map_priority("high") == TaskPriority.HIGH
    assert loop._map_priority("medium") == TaskPriority.NORMAL
    assert loop._map_priority("low") == TaskPriority.LOW
    assert loop._map_priority("critical") == TaskPriority.CRITICAL


def test_map_priority_unknown_falls_back(tmp_path: Path):
    """_map_priority returns NORMAL for unknown strings."""
    from src.orchestration.unified_ai_orchestrator import TaskPriority

    loop = _make_loop(tmp_path)
    assert loop._map_priority("bogus") == TaskPriority.NORMAL
    assert loop._map_priority("") == TaskPriority.NORMAL


def test_map_priority_none_falls_back(tmp_path: Path):
    """_map_priority returns NORMAL when passed None."""
    from src.orchestration.unified_ai_orchestrator import TaskPriority

    loop = _make_loop(tmp_path)
    # None triggers AttributeError branch → NORMAL
    assert loop._map_priority(None) == TaskPriority.NORMAL  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 5. _get_questline_for_pu
# ---------------------------------------------------------------------------

def test_get_questline_for_pu_known(tmp_path: Path):
    """_get_questline_for_pu returns correct questline for known PU types."""
    loop = _make_loop(tmp_path)
    assert loop._get_questline_for_pu("BugFixPU") == "Bug Fixes"
    assert loop._get_questline_for_pu("RefactorPU") == "Refactoring"
    assert loop._get_questline_for_pu("FeaturePU") == "Features"
    assert loop._get_questline_for_pu("DocPU") == "Documentation"
    assert loop._get_questline_for_pu("AnalysisPU") == "Analysis & Audits"
    assert loop._get_questline_for_pu("TestPU") == "Testing"


def test_get_questline_for_pu_unknown(tmp_path: Path):
    """_get_questline_for_pu falls back to quest_chapter_name."""
    loop = _make_loop(tmp_path)
    assert loop._get_questline_for_pu("UnknownPU") == loop.quest_chapter_name


# ---------------------------------------------------------------------------
# 6. _count_issues_in_output
# ---------------------------------------------------------------------------

def test_count_issues_mypy(tmp_path: Path):
    """_count_issues_in_output counts mypy error: lines."""
    loop = _make_loop(tmp_path)
    output = "src/foo.py:10: error: Argument missing\nsrc/bar.py:20: error: Type mismatch"
    assert loop._count_issues_in_output("mypy", output) == 2


def test_count_issues_ruff(tmp_path: Path):
    """_count_issues_in_output counts ruff violations."""
    loop = _make_loop(tmp_path)
    output = "src/foo.py:1:1: E501 line too long\nsrc/bar.py:2:3: F401 imported but unused"
    assert loop._count_issues_in_output("ruff", output) == 2


def test_count_issues_empty(tmp_path: Path):
    """_count_issues_in_output returns 0 for empty output."""
    loop = _make_loop(tmp_path)
    assert loop._count_issues_in_output("mypy", "") == 0
    assert loop._count_issues_in_output("ruff", "") == 0
    assert loop._count_issues_in_output("pytest_collect", "") == 0


def test_count_issues_unknown_check(tmp_path: Path):
    """_count_issues_in_output returns 0 for unknown check names."""
    loop = _make_loop(tmp_path)
    assert loop._count_issues_in_output("somethingelse", "error: lots of errors") == 0


# ---------------------------------------------------------------------------
# 7. _score_feedback_loop
# ---------------------------------------------------------------------------

def test_score_feedback_loop_high_band(tmp_path: Path):
    """_score_feedback_loop returns 'high' band for perfect execution."""
    loop = _make_loop(tmp_path)
    score_result = loop._score_feedback_loop(
        execution_results={"success_rate": 1.0},
        apply_results={"applied_file_count": 5, "preview": {}},
        validation_results={"checks_run": 4, "checks_passed": 4, "issue_count": 0},
        audit_results={"findings": 10},
    )
    assert score_result["band"] == "high"
    assert 0.0 <= score_result["score"] <= 1.0


def test_score_feedback_loop_low_band(tmp_path: Path):
    """_score_feedback_loop returns 'low' band when nothing passes."""
    loop = _make_loop(tmp_path)
    score_result = loop._score_feedback_loop(
        execution_results={"success_rate": 0.0},
        apply_results={"applied_file_count": 0, "preview": {}},
        validation_results={"checks_run": 0, "checks_passed": 0, "issue_count": 0},
        audit_results={"findings": 0},
    )
    assert score_result["band"] == "low"


def test_score_feedback_loop_output_keys(tmp_path: Path):
    """_score_feedback_loop result contains all expected keys."""
    loop = _make_loop(tmp_path)
    result = loop._score_feedback_loop(
        execution_results={"success_rate": 0.5},
        apply_results={"applied_file_count": 2, "preview": {"applicable_results": 3}},
        validation_results={"checks_run": 2, "checks_passed": 1, "issue_count": 1},
        audit_results={"findings": 5},
    )
    expected_keys = {
        "score", "band", "execution_success_rate", "validation_pass_rate",
        "apply_activity", "error_reduction", "applied_file_count",
        "preview_applicable_results", "checks_run", "checks_passed",
        "audit_findings", "post_validation_issues",
    }
    assert expected_keys.issubset(result.keys())


def test_score_feedback_loop_score_clamped(tmp_path: Path):
    """_score_feedback_loop score is always in [0.0, 1.0]."""
    loop = _make_loop(tmp_path)
    result = loop._score_feedback_loop(
        execution_results={"success_rate": 999.0},
        apply_results={"applied_file_count": 9999, "preview": {}},
        validation_results={"checks_run": 1, "checks_passed": 1, "issue_count": 0},
        audit_results={"findings": 100},
    )
    assert 0.0 <= result["score"] <= 1.0


# ---------------------------------------------------------------------------
# 8. _get_next_tasks (file-based, uses tmp_path)
# ---------------------------------------------------------------------------

def test_get_next_tasks_no_file(tmp_path: Path):
    """_get_next_tasks returns [] when PU queue file does not exist."""
    loop = _make_loop(tmp_path)
    # File does not exist
    result = loop._get_next_tasks()
    assert result == []


def test_get_next_tasks_empty_queue(tmp_path: Path):
    """_get_next_tasks returns [] for an empty PU queue."""
    loop = _make_loop(tmp_path)
    loop.pu_queue_path.write_text("[]", encoding="utf-8")
    result = loop._get_next_tasks()
    assert result == []


def test_get_next_tasks_filters_by_status(tmp_path: Path):
    """_get_next_tasks returns only tasks with eligible statuses."""
    loop = _make_loop(tmp_path)
    queue_data = [
        {"id": "PU-1", "type": "RefactorPU", "description": "Fix foo", "priority": "high", "status": "approved"},
        {"id": "PU-2", "type": "FeaturePU", "description": "Add bar", "priority": "low", "status": "completed"},
        {"id": "PU-3", "type": "DocPU", "description": "Doc baz", "priority": "medium", "status": "pending"},
    ]
    loop.pu_queue_path.write_text(json.dumps(queue_data), encoding="utf-8")

    result = loop._get_next_tasks()
    task_ids = [t.task_id for t in result]
    assert "PU-1" in task_ids
    assert "PU-3" in task_ids
    assert "PU-2" not in task_ids


def test_get_next_tasks_respects_max(tmp_path: Path):
    """_get_next_tasks respects max_tasks limit."""
    loop = _make_loop(tmp_path, max_tasks_per_cycle=2)
    queue_data = [
        {"id": f"PU-{i}", "type": "RefactorPU", "description": f"Task {i}", "priority": "medium", "status": "approved"}
        for i in range(10)
    ]
    loop.pu_queue_path.write_text(json.dumps(queue_data), encoding="utf-8")
    result = loop._get_next_tasks()
    assert len(result) <= 2


# ---------------------------------------------------------------------------
# 9. _apply_task_results when ResultApplier is unavailable
# ---------------------------------------------------------------------------

def test_apply_task_results_skipped_when_unavailable(tmp_path: Path):
    """_apply_task_results returns skipped status when ResultApplier is absent."""
    loop = _make_loop(tmp_path)
    # conftest.py adds workspace root to sys.path, making scripts/result_applier.py
    # importable in the full suite.  After _make_loop's patch context exits the
    # module-level RESULT_APPLIER_AVAILABLE is restored to True.  Re-apply the
    # patch here so the method sees the unavailable state we want to test.
    with patch("src.automation.autonomous_loop.RESULT_APPLIER_AVAILABLE", False):
        result = loop._apply_task_results()
    assert result["status"] == "skipped"
    assert result["applied_file_count"] == 0


# ---------------------------------------------------------------------------
# 10. _save_metrics / _save_feedback_metrics (file I/O)
# ---------------------------------------------------------------------------

def test_save_metrics_creates_file(tmp_path: Path):
    """_save_metrics writes a JSON file with the expected shape."""
    loop = _make_loop(tmp_path)
    loop.metrics_path = tmp_path / "data" / "metrics.json"
    sample = {"cycle": 1, "timestamp": "2026-01-01T00:00:00", "phases": {}}
    loop._save_metrics(sample)
    assert loop.metrics_path.exists()
    payload = json.loads(loop.metrics_path.read_text(encoding="utf-8"))
    assert payload["total_cycles"] == 1
    assert payload["cycles"][0] == sample


def test_save_metrics_appends_across_calls(tmp_path: Path):
    """Calling _save_metrics twice accumulates two cycles."""
    loop = _make_loop(tmp_path)
    loop.metrics_path = tmp_path / "data" / "metrics.json"
    loop._save_metrics({"cycle": 1, "timestamp": "2026-01-01T00:00:00", "phases": {}})
    loop._save_metrics({"cycle": 2, "timestamp": "2026-01-01T00:00:01", "phases": {}})
    payload = json.loads(loop.metrics_path.read_text(encoding="utf-8"))
    assert payload["total_cycles"] == 2


def test_save_feedback_metrics_creates_file(tmp_path: Path):
    """_save_feedback_metrics persists a snapshot."""
    loop = _make_loop(tmp_path)
    snapshot = {
        "cycle": 1,
        "timestamp": "2026-01-01T00:00:00",
        "mode": "stage",
        "apply": {"applied_file_count": 0},
        "validation": {"checks_run": 0},
        "impact": {"score": 0.5, "band": "medium"},
    }
    loop._save_feedback_metrics(snapshot)
    assert loop.autonomous_feedback_path.exists()
    payload = json.loads(loop.autonomous_feedback_path.read_text(encoding="utf-8"))
    assert payload["total_cycles"] == 1
    assert payload["average_feedback_score"] == 0.5


# ---------------------------------------------------------------------------
# 11. _handle_shutdown
# ---------------------------------------------------------------------------

def test_handle_shutdown_sets_running_false(tmp_path: Path):
    """_handle_shutdown sets running=False."""
    loop = _make_loop(tmp_path)
    loop.running = True
    loop._handle_shutdown(2, None)
    assert loop.running is False


# ---------------------------------------------------------------------------
# 12. _convert_pu_to_quest when quest_engine is None
# ---------------------------------------------------------------------------

def test_convert_pu_to_quest_no_engine(tmp_path: Path):
    """_convert_pu_to_quest returns None when quest_engine is not set."""
    loop = _make_loop(tmp_path)
    assert loop.quest_engine is None
    result = loop._convert_pu_to_quest({"id": "PU-1", "type": "RefactorPU"})
    assert result is None


# ---------------------------------------------------------------------------
# 13. _sync_quest_execution_status when quest_engine is None
# ---------------------------------------------------------------------------

def test_sync_quest_execution_status_no_engine(tmp_path: Path):
    """_sync_quest_execution_status returns 0 with no quest engine."""
    loop = _make_loop(tmp_path)
    result = loop._sync_quest_execution_status({"execution_results": [{"quest_id": "q1", "status": "submitted"}]})
    assert result == 0


# ---------------------------------------------------------------------------
# 14. _create_quests_from_pu_results when integration disabled
# ---------------------------------------------------------------------------

def test_create_quests_from_pu_results_disabled(tmp_path: Path):
    """_create_quests_from_pu_results returns empty result when integration is off."""
    loop = _make_loop(tmp_path)
    loop.enable_quest_integration = False
    result = loop._create_quests_from_pu_results()
    assert result == {"quests_created": 0, "quests_failed": 0}


# ---------------------------------------------------------------------------
# 15. _get_quests_for_execution when disabled
# ---------------------------------------------------------------------------

def test_get_quests_for_execution_disabled(tmp_path: Path):
    """_get_quests_for_execution returns [] when execution is disabled."""
    loop = _make_loop(tmp_path)
    loop.enable_quest_execution = False
    assert loop._get_quests_for_execution() == []


# ---------------------------------------------------------------------------
# 16. _execute_quests returns early when no quests
# ---------------------------------------------------------------------------

def test_execute_quests_no_quests(tmp_path: Path):
    """_execute_quests returns zero counts when no quests are available."""
    loop = _make_loop(tmp_path)
    loop.enable_quest_execution = False  # force empty list
    result = loop._execute_quests()
    assert result["quests_submitted"] == 0
    assert result["quests_failed"] == 0
    assert result["execution_results"] == []


# ---------------------------------------------------------------------------
# 17. _submit_to_background_orchestrator when orchestrator is None
# ---------------------------------------------------------------------------

def test_submit_to_background_orchestrator_no_orchestrator(tmp_path: Path):
    """_submit_to_background_orchestrator returns None with no orchestrator."""
    loop = _make_loop(tmp_path)
    assert loop.background_orchestrator is None
    result = loop._submit_to_background_orchestrator({"id": "PU-1", "type": "RefactorPU"})
    assert result is None


# ---------------------------------------------------------------------------
# 18. _delegate_heavy_tasks_to_background with no orchestrator
# ---------------------------------------------------------------------------

def test_delegate_heavy_tasks_no_orchestrator(tmp_path: Path):
    """_delegate_heavy_tasks_to_background returns 0 with no orchestrator."""
    loop = _make_loop(tmp_path)
    result = loop._delegate_heavy_tasks_to_background()
    assert result == 0


# ---------------------------------------------------------------------------
# 19. _convert_quest_to_task
# ---------------------------------------------------------------------------

def test_convert_quest_to_task_valid(tmp_path: Path):
    """_convert_quest_to_task creates an OrchestrationTask from quest data."""
    from src.orchestration.unified_ai_orchestrator import OrchestrationTask, TaskPriority

    loop = _make_loop(tmp_path)
    quest_data = {
        "id": "q-123",
        "title": "Fix the thing",
        "description": "Please fix it",
        "priority": "high",
        "questline": "Bug Fixes",
        "tags": [],
    }
    task = loop._convert_quest_to_task(quest_data)
    assert task is not None
    assert isinstance(task, OrchestrationTask)
    assert task.task_id == "q-123"
    assert task.task_type == "quest_execution"
    assert task.priority == TaskPriority.HIGH


def test_convert_quest_to_task_unknown_priority(tmp_path: Path):
    """_convert_quest_to_task uses NORMAL priority for unknown values."""
    from src.orchestration.unified_ai_orchestrator import TaskPriority

    loop = _make_loop(tmp_path)
    quest_data = {
        "id": "q-999",
        "title": "Mystery",
        "description": "",
        "priority": "ultra",
        "questline": "General",
    }
    task = loop._convert_quest_to_task(quest_data)
    assert task is not None
    assert task.priority == TaskPriority.NORMAL
