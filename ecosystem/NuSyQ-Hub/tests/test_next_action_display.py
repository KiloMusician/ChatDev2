"""Unit tests for next_action_display.py action queue interface."""

import json
from pathlib import Path

from src.tools.next_action_display import display_human_readable, display_json, load_action_queue


def test_load_action_queue_missing_file(tmp_path: Path) -> None:
    """Loading action queue from missing file should return error dict."""
    repo_root = tmp_path
    queue = load_action_queue(repo_root)
    assert "error" in queue
    assert "No action queue" in queue["error"]


def test_load_action_queue_valid_file(tmp_path: Path) -> None:
    """Loading valid action queue file should parse correctly."""
    queue_dir = tmp_path / "state"
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_file = queue_dir / "next_action_queue.json"

    test_queue = {
        "generated_at": "2026-01-02T13:00:00",
        "refresh_interval_minutes": 30,
        "actions": [{"title": "Action 1", "priority": "HIGH", "type": "lint"}],
        "by_priority": {"HIGH": 1},
    }
    queue_file.write_text(json.dumps(test_queue))

    queue = load_action_queue(tmp_path)
    assert queue["generated_at"] == "2026-01-02T13:00:00"
    assert len(queue["actions"]) == 1


def test_display_json_no_error(capsys, tmp_path: Path) -> None:
    """Display JSON should output valid JSON structure."""
    queue = {
        "generated_at": "2026-01-02",
        "actions": [{"title": "Test", "priority": "HIGH"}],
    }
    display_json(queue)
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["generated_at"] == "2026-01-02"


def test_display_human_readable_with_error(capsys) -> None:
    """Display human readable should show error message."""
    queue = {"error": "No action queue generated yet"}
    display_human_readable(queue)
    captured = capsys.readouterr()
    assert "No action queue" in captured.out


def test_display_human_readable_empty_actions(capsys) -> None:
    """Display should show success message when no actions pending."""
    queue = {
        "generated_at": "2026-01-02T13:00:00",
        "refresh_interval_minutes": 30,
        "actions": [],
        "by_priority": {},
    }
    display_human_readable(queue)
    captured = capsys.readouterr()
    assert "good state" in captured.out or "No pending" in captured.out


def test_display_human_readable_with_actions(capsys) -> None:
    """Display should show actions with priority emojis."""
    queue = {
        "generated_at": "2026-01-02T13:00:00",
        "refresh_interval_minutes": 30,
        "actions": [
            {
                "title": "Critical Task",
                "priority": "CRITICAL",
                "effort": "2h",
                "type": "heal",
                "source": "system",
                "context": {"file": "src/main.py"},
            },
            {
                "title": "High Priority Task",
                "priority": "HIGH",
                "effort": "1h",
                "type": "test",
                "source": "agent",
            },
        ],
        "by_priority": {"CRITICAL": 1, "HIGH": 1},
    }
    display_human_readable(queue)
    captured = capsys.readouterr()
    assert "NEXT ACTIONS" in captured.out
    assert "Critical Task" in captured.out
    assert "🔴" in captured.out  # CRITICAL emoji
    assert "High Priority Task" in captured.out


def test_display_human_readable_priority_summary(capsys) -> None:
    """Display should show summary by priority."""
    queue = {
        "generated_at": "2026-01-02T13:00:00",
        "refresh_interval_minutes": 30,
        "actions": [
            {
                "title": "Task 1",
                "priority": "CRITICAL",
                "type": "fix",
                "effort": "1h",
                "source": "test",
            },
            {
                "title": "Task 2",
                "priority": "CRITICAL",
                "type": "fix",
                "effort": "1h",
                "source": "test",
            },
            {
                "title": "Task 3",
                "priority": "HIGH",
                "type": "test",
                "effort": "30m",
                "source": "test",
            },
        ],
        "by_priority": {"CRITICAL": 2, "HIGH": 1},
    }
    display_human_readable(queue)
    captured = capsys.readouterr()
    assert "Summary:" in captured.out
    assert "CRITICAL" in captured.out
    assert "HIGH" in captured.out
