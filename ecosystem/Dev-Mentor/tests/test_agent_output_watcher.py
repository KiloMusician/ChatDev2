from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.agent_output_watcher as watcher


def test_sync_agent_rule_updates_completion_when_artifacts_change(tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("ok", encoding="utf-8")
    agent = {
        "status": "active",
        "current_phase": "old-phase",
        "last_checkin_at": "2026-03-21T00:00:00+00:00",
        "phase_output": [],
    }
    rule = {"phase": "new-phase"}

    changed = watcher.sync_agent_rule(agent, rule, [artifact], "2026-03-21T01:00:00+00:00")

    assert changed is True
    assert agent["status"] == "completed"
    assert agent["current_phase"] == "new-phase"
    assert agent["phase_output"] == [str(artifact)]
    assert agent["last_checkin_at"] == "2026-03-21T01:00:00+00:00"


def test_sync_agent_rule_preserves_checkin_when_outputs_are_already_current(tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("ok", encoding="utf-8")
    agent = {
        "status": "completed",
        "current_phase": "new-phase",
        "last_checkin_at": "2026-03-21T01:00:00+00:00",
        "phase_output": [str(artifact)],
    }
    rule = {"phase": "new-phase"}

    changed = watcher.sync_agent_rule(agent, rule, [artifact], "2026-03-21T03:00:00+00:00")

    assert changed is False
    assert agent["last_checkin_at"] == "2026-03-21T01:00:00+00:00"


def test_refresh_agent_health_marks_stale_active_agents(tmp_path, monkeypatch):
    agent_health = tmp_path / "agent_health.json"
    agent_health.write_text(
        json.dumps(
            {
                "updated_at": "2026-03-21T00:00:00+00:00",
                "status": "active",
                "check_interval_minutes": 20,
                "agents": [
                    {
                        "name": "Poincare",
                        "agent_id": "old-id",
                        "status": "active",
                        "idle_alert_after_minutes": 60,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(watcher, "AGENT_HEALTH_PATH", agent_health)

    changed = watcher.refresh_agent_health(
        {
            "poincare": {
                "name": "Poincare",
                "agent_id": "new-id",
                "status": "active",
                "current_task": "Trace import graph",
                "last_checkin_at": "2026-03-21T00:00:00+00:00",
                "next_check_at": "2026-03-21T00:10:00+00:00",
            }
        }
    )

    payload = json.loads(agent_health.read_text(encoding="utf-8"))
    entry = payload["agents"][0]

    assert changed is True
    assert payload["status"] == "degraded"
    assert entry["agent_id"] == "new-id"
    assert entry["status"] == "stale"
    assert "last_checkin_stale" in entry["stale_reasons"]
    assert "next_check_overdue" in entry["stale_reasons"]


def test_ensure_task_does_not_duplicate_entries():
    queue = {"tasks": [{"id": "T1001A"}]}
    rule = {
        "queue_id": "T1001A",
        "description": "x",
        "priority": "P1",
        "category": "review",
    }

    changed = watcher.ensure_task(queue, rule)

    assert changed is False
    assert queue["tasks"] == [{"id": "T1001A"}]
