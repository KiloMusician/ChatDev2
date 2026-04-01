#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent.parent
STATE_DIR = BASE / "state"
AGENT_STATE_DIR = STATE_DIR / "agent_state"
AGENT_HEALTH_PATH = STATE_DIR / "agent_health.json"
QUEUE_PATH = BASE / "tasks" / "queue.json"
STALE_ACTIVE_STATUSES = {"active", "in_progress", "running", "busy"}
TERMINAL_STATUSES = {"completed", "done", "closed", "idle", "stale"}


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


ARTIFACT_RULES = {
    "godel": {
        "artifacts": [BASE / "rimworld_mod" / "Source" / "Patches" / "ChatAdapter.cs"],
        "queue_id": "T1001A",
        "description": "Review and compile RimWorld chat adapter bridge patch",
        "category": "review",
        "priority": "P1",
        "phase": "chat-adapter-prototype",
    },
    "nietzsche": {
        "artifacts": [STATE_DIR / "playbook_completionist.json"],
        "queue_id": "T1005A",
        "description": "Add Terminal Depths playbook command that reads machine-readable hint data",
        "category": "feature",
        "priority": "P1",
        "phase": "completionist-playbook",
    },
    "plato": {
        "artifacts": [
            BASE / "rimworld_mod" / "README.md",
            BASE / "rimworld_mod" / "About" / "About.xml",
        ],
        "queue_id": "T1001B",
        "description": "Compile and smoke-test generated RimWorld mod scaffold",
        "category": "verification",
        "priority": "P1",
        "phase": "mod-skeleton-generated",
    },
    "chandrasekhar": {
        "artifacts": [STATE_DIR / "runtime" / "hub_health_probe.jsonl"],
        "queue_id": "T1002A",
        "description": "Wire Hub health listener into orchestrator task gating",
        "category": "orchestration",
        "priority": "P1",
        "phase": "probe-artifact-ready",
    },
}


def ensure_task(queue: dict[str, Any], rule: dict[str, Any]) -> bool:
    tasks = queue.setdefault("tasks", [])
    if any(task.get("id") == rule["queue_id"] for task in tasks):
        return False
    tasks.append(
        {
            "id": rule["queue_id"],
            "description": rule["description"],
            "priority": rule["priority"],
            "category": rule["category"],
            "assigned_to": None,
            "status": "open",
        }
    )
    return True


def sync_agent_rule(
    agent: dict[str, Any],
    rule: dict[str, Any],
    artifacts: list[Path],
    stamp: str,
) -> bool:
    changed = False
    artifact_paths = [str(p) for p in artifacts]

    if agent.get("status") != "completed":
        agent["status"] = "completed"
        changed = True

    if agent.get("current_phase") != rule["phase"]:
        agent["current_phase"] = rule["phase"]
        changed = True

    if agent.get("phase_output") != artifact_paths:
        agent["phase_output"] = artifact_paths
        agent["last_checkin_at"] = stamp
        changed = True
    elif not agent.get("last_checkin_at"):
        agent["last_checkin_at"] = stamp
        changed = True

    return changed


def refresh_agent_health(agent_snapshots: dict[str, dict[str, Any]]) -> bool:
    if not AGENT_HEALTH_PATH.exists():
        return False

    health = read_json(AGENT_HEALTH_PATH)
    now = datetime.now(UTC)
    existing = {
        (entry.get("name") or "").strip().lower(): entry
        for entry in health.get("agents", [])
        if entry.get("name")
    }

    refreshed = []
    stale_count = 0
    for stem, agent in sorted(agent_snapshots.items()):
        name = agent.get("name") or stem.title()
        key = name.strip().lower()
        current = existing.get(key, {})
        idle_alert = int(current.get("idle_alert_after_minutes", 60))
        last_checkin = parse_iso(agent.get("last_checkin_at"))
        next_check = parse_iso(agent.get("next_check_at"))
        status = str(agent.get("status") or current.get("status") or "unknown")
        stale_reasons: list[str] = []

        if status in STALE_ACTIVE_STATUSES:
            if not last_checkin:
                stale_reasons.append("last_checkin_missing")
            elif now - last_checkin > timedelta(minutes=idle_alert):
                stale_reasons.append("last_checkin_stale")

        if status not in TERMINAL_STATUSES and next_check and next_check < now:
            stale_reasons.append("next_check_overdue")

        if stale_reasons:
            status = "stale"
            stale_count += 1

        entry = {
            "name": name,
            "agent_id": agent.get("agent_id", current.get("agent_id")),
            "status": status,
            "focus": agent.get("current_task")
            or agent.get("domain")
            or current.get("focus"),
            "last_checkin_at": agent.get("last_checkin_at"),
            "next_check_at": agent.get("next_check_at"),
            "idle_alert_after_minutes": idle_alert,
        }
        if stale_reasons:
            entry["stale_reasons"] = stale_reasons
        refreshed.append(entry)

    payload = {
        "updated_at": now_iso(),
        "status": "degraded" if stale_count else "active",
        "check_interval_minutes": health.get("check_interval_minutes", 20),
        "agents": refreshed,
    }
    if payload == health:
        return False
    write_json(AGENT_HEALTH_PATH, payload)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update agent state and queue from generated artifacts."
    )
    parser.add_argument("--once", action="store_true", help="Run one pass and exit.")
    args = parser.parse_args()
    _ = args

    queue = read_json(QUEUE_PATH)
    changed = False
    agent_snapshots: dict[str, dict[str, Any]] = {}
    stamp = now_iso()

    for agent_file in AGENT_STATE_DIR.glob("*.json"):
        agent = read_json(agent_file)
        stem = agent_file.stem
        agent_snapshots[stem] = agent
        rule = ARTIFACT_RULES.get(stem)
        if not rule:
            continue
        artifacts = [p for p in rule["artifacts"] if p.exists()]
        if not artifacts:
            continue
        agent_changed = sync_agent_rule(agent, rule, artifacts, stamp)
        if agent_changed:
            write_json(agent_file, agent)
            agent_snapshots[stem] = agent
            changed = True
        if ensure_task(queue, rule):
            changed = True

    if refresh_agent_health(agent_snapshots):
        changed = True

    if changed:
        queue["updated_at"] = now_iso()
        write_json(QUEUE_PATH, queue)
    print(json.dumps({"ok": True, "changed": changed, "updated_at": now_iso()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
