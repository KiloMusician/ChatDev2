from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import dispatch_task as dispatcher


def test_infer_spawn_role_prefers_explicit_target() -> None:
    task = {"id": "task-1", "type": "spawn_agent", "target": "architect", "title": "Spawn helper"}
    assert dispatcher._infer_spawn_role(task) == "architect"


def test_dispatch_spawn_agent_marks_task_done(tmp_path, monkeypatch) -> None:
    # TASKS_DIR → tmp_path; FILE_TASKS_DIR → tmp_path (task files live there directly)
    monkeypatch.setattr(dispatcher, "TASKS_DIR", tmp_path)
    monkeypatch.setattr(dispatcher, "FILE_TASKS_DIR", tmp_path)
    task = {
        "id": "task-spawn",
        "type": "spawn_agent",
        "title": "Spawn scout agent for exploration",
        "details": "Need a scout to explore hidden nodes",
        "personality": "professional",
    }
    (tmp_path / "task-spawn.json").write_text(json.dumps(task), encoding="utf-8")

    def fake_post(path: str, payload: dict) -> dict:
        assert path == "/api/swarm/spawn"
        assert payload["role"] == "scout"
        return {"ok": True, "agent_id": "swarm_scout_123", "name": "Swift-Rogue-42", "role": "scout"}

    monkeypatch.setattr(dispatcher, "_post", fake_post)

    result = dispatcher.dispatch_task(task)
    updated = json.loads((tmp_path / "task-spawn.json").read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert updated["status"] == "done"
    assert "Swift-Rogue-42" in updated["result"]
