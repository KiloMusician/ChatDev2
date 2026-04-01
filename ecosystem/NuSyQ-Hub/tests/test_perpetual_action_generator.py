"""Tests for perpetual next-action quest signal quality."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone, UTC
from pathlib import Path

from src.tools.perpetual_action_generator import (
    ActionGenerator,
    ActionType,
    Priority,
    SignalAnalyzer,
)


def _write_quest_log(repo_root: Path, rows: list[dict]) -> None:
    quest_log = repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    quest_log.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(json.dumps(row) for row in rows) + "\n"
    quest_log.write_text(content, encoding="utf-8")


def test_analyze_quest_system_compacts_duplicate_titles_and_keeps_recent(
    monkeypatch, tmp_path: Path
) -> None:
    now = datetime.now(UTC)
    _write_quest_log(
        tmp_path,
        [
            {
                "timestamp": (now - timedelta(days=30)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-old", "title": "Duplicate Quest", "status": "active"},
            },
            {
                "timestamp": (now - timedelta(days=2)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-new", "title": "Duplicate Quest", "status": "active"},
            },
            {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-pending", "title": "Pending Quest", "status": "pending"},
            },
            {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-done", "title": "Completed Quest", "status": "completed"},
            },
        ],
    )
    monkeypatch.setenv("NUSYQ_NEXT_ACTION_QUEST_WINDOW_DAYS", "7")

    analyzer = SignalAnalyzer(tmp_path)
    quests = analyzer.analyze_quest_system()

    assert quests["active_recent_count"] == 1
    assert quests["pending_recent_count"] == 1
    assert quests["stale_backlog_count"] == 0
    assert quests["active_total_count"] == 1
    assert "Duplicate Quest" in quests["active"]


def test_analyze_quest_system_marks_old_items_as_stale(monkeypatch, tmp_path: Path) -> None:
    now = datetime.now(UTC)
    _write_quest_log(
        tmp_path,
        [
            {
                "timestamp": (now - timedelta(days=45)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-stale", "title": "Stale Quest", "status": "active"},
            }
        ],
    )
    monkeypatch.setenv("NUSYQ_NEXT_ACTION_QUEST_WINDOW_DAYS", "14")

    analyzer = SignalAnalyzer(tmp_path)
    quests = analyzer.analyze_quest_system()

    assert quests["active_recent_count"] == 0
    assert quests["active_total_count"] == 1
    assert quests["stale_backlog_count"] == 1
    assert "Stale Quest" in quests["stale_sample"]


def test_generate_actions_uses_recent_quest_counts(tmp_path: Path) -> None:
    generator = ActionGenerator(tmp_path)
    generator.analyzer.analyze_coverage = lambda: {"gap": 0}  # type: ignore[method-assign]
    generator.analyzer.analyze_module_availability = lambda: {}  # type: ignore[method-assign]
    generator.analyzer.analyze_lifecycle_catalog = lambda: {}  # type: ignore[method-assign]
    generator.analyzer.analyze_quest_system = lambda: {  # type: ignore[method-assign]
        "active": ["Quest A", "Quest B"],
        "pending": ["Quest C"],
        "active_recent_count": 2,
        "pending_recent_count": 1,
        "stale_backlog_count": 9,
        "quest_window_days": 21,
    }

    actions = generator.generate_actions()
    resolve_action = next(
        action for action in actions if action.action_type == ActionType.RESOLVE_QUEST
    )
    payload = resolve_action.to_dict()

    assert resolve_action.priority == Priority.HIGH
    assert "(3 recent)" in resolve_action.title
    assert payload["context"]["stale_backlog_count"] == 9
    assert payload["context"]["window_days"] == 21


def test_generate_actions_surfaces_stale_backlog_when_no_recent(tmp_path: Path) -> None:
    generator = ActionGenerator(tmp_path)
    generator.analyzer.analyze_coverage = lambda: {"gap": 0}  # type: ignore[method-assign]
    generator.analyzer.analyze_module_availability = lambda: {}  # type: ignore[method-assign]
    generator.analyzer.analyze_lifecycle_catalog = lambda: {}  # type: ignore[method-assign]
    generator.analyzer.analyze_quest_system = lambda: {  # type: ignore[method-assign]
        "active": [],
        "pending": [],
        "active_recent_count": 0,
        "pending_recent_count": 0,
        "stale_backlog_count": 4,
        "quest_window_days": 21,
        "stale_sample": ["Quest Old"],
    }

    actions = generator.generate_actions()
    resolve_action = next(
        action for action in actions if action.action_type == ActionType.RESOLVE_QUEST
    )
    payload = resolve_action.to_dict()

    assert resolve_action.priority == Priority.MEDIUM
    assert "stale quest backlog" in resolve_action.title.lower()
    assert payload["context"]["stale_sample"] == ["Quest Old"]


def test_analyze_diagnostics_reads_gate_and_error_artifacts(tmp_path: Path) -> None:
    reports_dir = tmp_path / "state" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "system_complete_gate_latest.json").write_text(
        json.dumps(
            {
                "status": "failed",
                "checks": [
                    {"name": "chatdev_e2e", "passed": False, "cmd": ["python", "scripts/e2e.py"]},
                    {"name": "lint_threshold", "passed": False, "skipped": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    diagnostics_dir = tmp_path / "docs" / "Reports" / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    (diagnostics_dir / "unified_error_report_latest.json").write_text(
        json.dumps(
            {
                "ground_truth": {"errors": 2, "warnings": 1, "infos": 0},
                "by_repo": {"hub": {"by_source": {"ruff": 7}}},
                "diagnostic_details": [{"message": "cannot import name X"}],
            }
        ),
        encoding="utf-8",
    )

    analyzer = SignalAnalyzer(tmp_path)
    diagnostics = analyzer.analyze_diagnostics()

    assert diagnostics["errors"] == 2
    assert diagnostics["warnings"] == 1
    assert diagnostics["ruff_count"] == 7
    assert diagnostics["import_like_count"] == 1
    assert diagnostics["gate_skipped_count"] == 1
    assert diagnostics["gate_failed_checks"][0]["name"] == "chatdev_e2e"


def test_generate_actions_includes_fix_error_from_gate_failures(tmp_path: Path) -> None:
    generator = ActionGenerator(tmp_path)
    generator.analyzer.analyze_coverage = lambda: {"gap": 0}  # type: ignore[method-assign]
    generator.analyzer.analyze_module_availability = lambda: {}  # type: ignore[method-assign]
    generator.analyzer.analyze_lifecycle_catalog = lambda: {}  # type: ignore[method-assign]
    generator.analyzer.analyze_quest_system = lambda: {  # type: ignore[method-assign]
        "active": [],
        "pending": [],
        "active_recent_count": 0,
        "pending_recent_count": 0,
        "stale_backlog_count": 0,
        "quest_window_days": 21,
    }
    generator.analyzer.analyze_diagnostics = lambda: {  # type: ignore[method-assign]
        "errors": 0,
        "warnings": 0,
        "ruff_count": 0,
        "gate_failed_checks": [{"name": "chatdev_e2e", "cmd": ["python", "scripts/e2e.py"]}],
        "gate_skipped_count": 0,
    }

    actions = generator.generate_actions()
    fix_action = next(action for action in actions if action.action_type == ActionType.FIX_ERROR)

    assert fix_action.priority == Priority.CRITICAL
    assert "chatdev_e2e" in fix_action.title
    assert "python scripts/e2e.py" in str(fix_action.context.get("recommended_command"))
