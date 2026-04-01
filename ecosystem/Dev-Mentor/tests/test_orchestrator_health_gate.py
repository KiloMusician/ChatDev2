from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import agents.orchestrator as orchestrator


def test_read_latest_hub_health_probe_returns_latest_record(tmp_path, monkeypatch):
    state_dir = tmp_path / "state"
    runtime_dir = state_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    probe_log = runtime_dir / "hub_health_probe.jsonl"
    probe_log.write_text(
        "\n".join(
            [
                json.dumps({"healthy": True, "drift_flags": []}),
                json.dumps({"healthy": False, "drift_flags": ["heartbeat_stale"]}),
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(orchestrator, "STATE_DIR", state_dir)

    record = orchestrator.read_latest_hub_health_probe()

    assert record == {"healthy": False, "drift_flags": ["heartbeat_stale"]}


def test_cycle_skips_pending_tasks_when_probe_reports_drift(tmp_path, monkeypatch):
    state_dir = tmp_path / "state"
    runtime_dir = state_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "hub_health_probe.jsonl").write_text(
        json.dumps({"healthy": False, "drift_flags": ["heartbeat_stale"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(orchestrator, "STATE_DIR", state_dir)
    monkeypatch.setattr(orchestrator, "check_server", lambda: {"ok": True, "active_game_sessions": 1})
    monkeypatch.setattr(orchestrator, "ensure_simulatedverse", lambda: {"ok": True, "restarted": False})
    monkeypatch.setattr(orchestrator, "list_pending_tasks", lambda: [{"id": "task-1", "title": "Gate me", "agent": "tester.py", "_path": str(tmp_path / "task.json")}])
    def fake_run_local_script(rel_path: str, *_args, **_kwargs):
        if rel_path == "scripts/health_listener.py":
            return {
                "ok": True,
                "stdout": json.dumps({"ok": True, "critical": True, "drift_flags": ["heartbeat_stale"]}),
                "stderr": "",
            }
        return {"ok": True, "summary": "ok", "stdout": "", "stderr": ""}

    monkeypatch.setattr(orchestrator, "run_local_script", fake_run_local_script)
    monkeypatch.setattr(orchestrator, "write_devlog", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(orchestrator, "log", lambda *args, **kwargs: None)

    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_run_agent(agent_script: str, args: list[str] | None = None) -> dict:
        calls.append((agent_script, tuple(args or [])))
        return {"ok": True, "stdout": "", "stderr": "", "returncode": 0}

    monkeypatch.setattr(orchestrator, "run_agent", fake_run_agent)

    orchestrator.cycle()

    assert ("content_generator.py", ("--batch", "3")) in calls
    assert not any(agent == "tester.py" and args == ("--task", "task-1") for agent, args in calls)


def test_list_pending_tasks_ignores_queue_json(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "queue.json").write_text('{"tasks":[{"id":"T1","status":"open"}]}', encoding="utf-8")
    (tasks_dir / "task_real.json").write_text(
        json.dumps({"id": "task-real", "title": "Real task", "agent": "tester.py", "status": "pending"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(orchestrator, "TASKS_DIR", tasks_dir)
    monkeypatch.setattr(orchestrator, "FILE_TASKS_DIR", tasks_dir)

    tasks = orchestrator.list_pending_tasks()

    assert len(tasks) == 1
    assert tasks[0]["id"] == "task-real"
