from __future__ import annotations

import json
from pathlib import Path

from agents import orchestrator
from scripts import dispatch_task


def _write_task(path: Path, task_id: str, status: str = "pending") -> None:
    path.write_text(json.dumps({
        "id": task_id,
        "title": f"Task {task_id}",
        "details": "details",
        "agent": "implementer.py",
        "status": status,
    }))


def test_dispatch_task_reads_only_legacy_runtime_dir(tmp_path, monkeypatch):
    live_dir = tmp_path / "legacy_runtime"
    live_dir.mkdir()
    _write_task(tmp_path / "task_top_level.json", "top")
    _write_task(live_dir / "task_live.json", "live")

    monkeypatch.setattr(dispatch_task, "FILE_TASKS_DIR", live_dir)

    tasks = dispatch_task.load_tasks()

    assert [task["id"] for task in tasks] == ["live"]


def test_orchestrator_reads_only_legacy_runtime_dir(tmp_path, monkeypatch):
    live_dir = tmp_path / "legacy_runtime"
    live_dir.mkdir()
    _write_task(tmp_path / "task_top_level.json", "top")
    _write_task(live_dir / "task_live.json", "live")

    monkeypatch.setattr(orchestrator, "FILE_TASKS_DIR", live_dir)

    tasks = orchestrator.list_pending_tasks()

    assert [task["id"] for task in tasks] == ["live"]
