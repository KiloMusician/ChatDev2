"""Unit tests for background task CLI action handlers."""

from __future__ import annotations

import json

from scripts.nusyq_actions import background_task_actions


def test_task_status_treats_null_error_as_non_failure(monkeypatch, capsys) -> None:
    """A payload with error=None should not be treated as a failure."""
    from src.orchestration import background_task_orchestrator as orchestrator

    monkeypatch.setattr(
        orchestrator,
        "task_status_cli",
        lambda _task_id: {
            "task_id": "bg_test",
            "status": "queued",
            "error": None,
        },
    )
    monkeypatch.setattr(
        background_task_actions, "emit_action_receipt", lambda *args, **kwargs: None
    )

    rc = background_task_actions.handle_task_status(["bg_test"])
    captured = capsys.readouterr().out

    assert rc == 0
    assert '"success": true' in captured


def test_task_status_returns_failure_on_error_message(monkeypatch) -> None:
    """A payload with a real error message should return non-zero."""
    from src.orchestration import background_task_orchestrator as orchestrator

    monkeypatch.setattr(
        orchestrator,
        "task_status_cli",
        lambda _task_id: {"task_id": "bg_test", "status": "failed", "error": "boom"},
    )
    monkeypatch.setattr(
        background_task_actions, "emit_action_receipt", lambda *args, **kwargs: None
    )

    rc = background_task_actions.handle_task_status(["bg_test"])
    assert rc == 1


def test_list_background_tasks_supports_json_mode(monkeypatch, capsys) -> None:
    """list_background_tasks should emit machine-readable JSON when requested."""
    from src.orchestration import background_task_orchestrator as orchestrator

    monkeypatch.setattr(
        orchestrator,
        "list_tasks_cli",
        lambda status=None, limit=20: [
            {
                "task_id": "bg_json_1",
                "status": "queued",
                "target": "ollama",
                "requesting_agent": "test",
                "created_at": "2026-02-26T00:00:00Z",
            }
        ],
    )
    monkeypatch.setattr(
        background_task_actions, "emit_action_receipt", lambda *args, **kwargs: None
    )

    rc = background_task_actions.handle_list_background_tasks(
        ["--status=queued", "--limit=1"], json_mode=True
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["action"] == "list_background_tasks"
    assert payload["status"] == "ok"
    assert payload["count"] == 1
    assert payload["filter"] == "queued"
    assert payload["tasks"][0]["task_id"] == "bg_json_1"
