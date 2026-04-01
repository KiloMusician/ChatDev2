"""
NuSyQ Central Orchestrator
===========================
Implements the CHUG cycle: Cultivate → Harvest → Upgrade → Grow
Wires all 6 ecosystem repos into a single living system.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Activate PYTHONPATH before any ecosystem imports
from ecosystem.activate import activate as _activate
_activate()

from ecosystem.shared.db import get_conn, init_schema
from ecosystem.shared.memory import write as mem_write, read as mem_read, snapshot as mem_snapshot
from ecosystem.shared.task_queue import enqueue, dequeue, complete, fail, queue_stats
from ecosystem.shared.tool_registry import list_tools, seed_defaults as seed_tools
from ecosystem.shared.agent_registry import list_agents, heartbeat, seed_defaults as seed_agents
from ecosystem.shared.execution_log import log_action, recent_logs

ECOSYSTEM_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ECOSYSTEM_DIR.parent


# ── Initialization ─────────────────────────────────────────────────────────

def bootstrap() -> dict:
    """Run once on startup — seed registries, write initial state."""
    init_schema()
    seed_tools()
    seed_agents()
    mem_write("orchestrator.started_at", datetime.utcnow().isoformat(), namespace="system")
    mem_write("orchestrator.version", "1.0.0", namespace="system")
    # Sync Dev-Mentor quests into shared memory on every bootstrap
    quests_synced = _sync_devmentor_quests()
    log_action("bootstrap", "success", repo="ChatDev", agent="orchestrator")
    return {"status": "bootstrapped", "at": datetime.utcnow().isoformat(), "quests_synced": quests_synced}


def _sync_devmentor_quests() -> int:
    """Read Dev-Mentor CTF quests and write summary into shared memory."""
    import json as _json
    from pathlib import Path as _Path
    quest_files = [
        _Path(__file__).parent / "Dev-Mentor" / "challenges" / "ctf" / f
        for f in ("crypto.json", "forensics.json", "network.json",
                  "reverse_engineering.json", "web.json")
    ]
    all_quests: list = []
    for p in quest_files:
        if not p.exists():
            continue
        try:
            raw = _json.loads(p.read_text())
            if isinstance(raw, list):
                all_quests.extend(raw)
            elif isinstance(raw, dict):
                all_quests.extend(raw.values())
        except Exception:
            pass
    by_cat: Dict[str, int] = {}
    total_xp = 0
    for q in all_quests:
        if isinstance(q, dict):
            cat = q.get("category", "unknown")
            by_cat[cat] = by_cat.get(cat, 0) + 1
            total_xp += q.get("xp", 0)
    mem_write("devmentor.quests.synced", str(len(all_quests)), namespace="bridge")
    mem_write("devmentor.quests.summary", _json.dumps({
        "total": len(all_quests), "by_category": by_cat,
        "total_xp": total_xp, "synced_at": datetime.utcnow().isoformat(),
    }), namespace="bridge")
    log_action("quest.sync", "success", repo="Dev-Mentor", agent="orchestrator")
    return len(all_quests)


# ── CHUG Cycle ─────────────────────────────────────────────────────────────

def _get_cycle_num() -> int:
    row = get_conn().execute(
        "SELECT MAX(cycle_num) as mx FROM chug_cycles"
    ).fetchone()
    return (row["mx"] or 0) + 1


def _scan_system() -> Dict[str, Any]:
    """Phase 1: ASSESS — survey the entire ecosystem state."""
    scan = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "tasks": queue_stats(),
        "agents": len(list_agents()),
        "tools": len(list_tools()),
        "memory_keys": len(mem_snapshot()),
        "issues": [],
        "opportunities": [],
    }

    # Probe services
    import urllib.request
    probes = {
        "chatdev_backend": "http://localhost:6400/health",
        "dev_mentor": "http://localhost:8008/api/manifest",
        "concept_samurai": "http://localhost:3002/",
    }
    for name, url in probes.items():
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                scan["services"][name] = {"online": True, "code": r.status}
        except Exception as e:
            scan["services"][name] = {"online": False, "error": str(e)[:60]}
            scan["issues"].append(f"{name} offline: {str(e)[:40]}")

    # Check queued tasks
    queued = queue_stats().get("by_status", {}).get("queued", 0)
    if queued > 0:
        scan["opportunities"].append(f"{queued} tasks waiting to be processed")

    failed = queue_stats().get("by_status", {}).get("failed", 0)
    if failed > 0:
        scan["issues"].append(f"{failed} tasks in failed state")

    return scan


def _cultivate(cycle: int, scan: Dict) -> List[Dict]:
    """Phase 2: CULTIVATE — generate tasks based on scan findings."""
    tasks_created = []

    # Create tasks for discovered opportunities
    for opp in scan.get("opportunities", []):
        tid = enqueue(
            action="process_opportunity",
            repo="ecosystem",
            agent="orchestrator",
            payload={"opportunity": opp, "scan_at": scan["timestamp"]},
            priority=5,
        )
        tasks_created.append({"task_id": tid, "action": "process_opportunity", "trigger": opp})

    # Auto-enqueue memory snapshot
    tid = enqueue(
        action="snapshot_memory",
        repo="ecosystem",
        agent="orchestrator",
        payload={"cycle": cycle},
        priority=8,
    )
    tasks_created.append({"task_id": tid, "action": "snapshot_memory"})

    # Heartbeat for all known agents
    for agent in list_agents():
        if agent.get("endpoint"):
            tid = enqueue(
                action="agent_heartbeat",
                repo=agent.get("repo", "unknown"),
                agent=agent["agent_id"],
                payload={"endpoint": agent["endpoint"]},
                priority=9,
            )
            tasks_created.append({"task_id": tid, "action": "agent_heartbeat", "agent": agent["name"]})

    log_action("cultivate", "success", repo="ecosystem", agent="orchestrator", cycle=cycle,
               notes=f"created {len(tasks_created)} tasks")
    return tasks_created


def _harvest(cycle: int) -> List[Dict]:
    """Phase 3: HARVEST — execute pending tasks."""
    results = []
    batch = dequeue(limit=20)

    for task in batch:
        start = time.monotonic()
        try:
            result = _execute_task(task)
            complete(task["task_id"], result)
            duration_ms = int((time.monotonic() - start) * 1000)
            log_action(task["action"], "success", repo=task["repo"], agent=task.get("agent"),
                       cycle=cycle, duration_ms=duration_ms)
            results.append({"task_id": task["task_id"], "action": task["action"], "status": "done"})
        except Exception as e:
            fail(task["task_id"], str(e))
            log_action(task["action"], "error", repo=task["repo"], agent=task.get("agent"),
                       cycle=cycle, notes=str(e)[:100])
            results.append({"task_id": task["task_id"], "action": task["action"], "status": "failed", "error": str(e)[:60]})

    return results


def _execute_task(task: dict) -> Any:
    """Execute a single queued task."""
    action = task["action"]
    payload = task.get("payload", {})

    if action == "snapshot_memory":
        snapshot = mem_snapshot()
        mem_write("last_snapshot", {"count": len(snapshot), "at": datetime.utcnow().isoformat()},
                  namespace="system")
        return {"snapshot_keys": len(snapshot)}

    elif action == "agent_heartbeat":
        import urllib.request
        ep = payload.get("endpoint", "")
        if ep:
            try:
                with urllib.request.urlopen(ep + "/health" if not ep.endswith("/") else ep + "health", timeout=2) as r:
                    heartbeat(task["agent"], status="active")
                    return {"status": "active"}
            except Exception:
                heartbeat(task["agent"], status="unreachable")
                return {"status": "unreachable"}
        return {"status": "no_endpoint"}

    elif action == "process_opportunity":
        opp = payload.get("opportunity", "")
        log_action(f"opportunity:{opp[:50]}", "processed", repo="ecosystem", agent="orchestrator")
        return {"processed": opp}

    elif action == "chug_dev_mentor":
        return _run_dev_mentor_chug()

    else:
        return {"skipped": f"no handler for {action}"}


def _run_dev_mentor_chug() -> dict:
    """Run Dev-Mentor's CHUG engine."""
    chug_path = ECOSYSTEM_DIR / "Dev-Mentor" / "chug_engine.py"
    if not chug_path.exists():
        return {"error": "chug_engine.py not found"}
    try:
        result = subprocess.run(
            ["python", str(chug_path), "--phase", "1"],
            cwd=str(ECOSYSTEM_DIR / "Dev-Mentor"),
            capture_output=True, text=True, timeout=30,
        )
        return {"success": result.returncode == 0, "stdout": result.stdout[-500:]}
    except Exception as e:
        return {"error": str(e)}


def _upgrade(cycle: int, scan: Dict, harvest_results: List[Dict]) -> Dict:
    """Phase 4: UPGRADE — write improvements back to shared memory."""
    upgrades = {}

    # Record system health
    online_count = sum(1 for s in scan["services"].values() if s.get("online"))
    upgrades["system_health"] = {
        "online_services": online_count,
        "total_services": len(scan["services"]),
        "health_pct": round(online_count / max(len(scan["services"]), 1) * 100, 1),
    }

    # Record task throughput
    done = sum(1 for r in harvest_results if r["status"] == "done")
    failed = sum(1 for r in harvest_results if r["status"] == "failed")
    upgrades["task_throughput"] = {"done": done, "failed": failed, "total": len(harvest_results)}

    for k, v in upgrades.items():
        mem_write(f"cycle.{cycle}.{k}", v, namespace="chug")

    log_action("upgrade", "success", repo="ecosystem", agent="orchestrator", cycle=cycle,
               notes=json.dumps(upgrades)[:200])
    return upgrades


def _grow(cycle: int, upgrades: Dict, scan: Dict) -> Dict:
    """Phase 5: GROW — determine next actions and update cycle record."""
    next_actions = []

    if scan.get("issues"):
        next_actions.append("investigate_and_fix_issues")
    if upgrades.get("system_health", {}).get("health_pct", 100) < 80:
        next_actions.append("restart_degraded_services")
    if upgrades.get("task_throughput", {}).get("failed", 0) > 0:
        next_actions.append("retry_failed_tasks")

    # Auto-enqueue Dev-Mentor CHUG if we've run 3 cycles
    if cycle % 3 == 0:
        enqueue("chug_dev_mentor", repo="Dev-Mentor", agent="gordon", priority=3)
        next_actions.append("dev_mentor_chug_scheduled")

    mem_write(f"cycle.{cycle}.next_actions", next_actions, namespace="chug")
    mem_write("orchestrator.last_cycle", cycle, namespace="system")
    return {"next_actions": next_actions, "cycle": cycle}


def run_cycle() -> Dict[str, Any]:
    """Execute a full CHUG cycle. Returns cycle report."""
    cycle = _get_cycle_num()
    started_at = datetime.utcnow().isoformat()

    get_conn().execute(
        "INSERT INTO chug_cycles (cycle_num, phase, status, started_at) VALUES (?, ?, ?, ?)",
        (cycle, "ASSESS", "running", started_at),
    )
    get_conn().commit()

    try:
        # ASSESS
        scan = _scan_system()
        _update_cycle(cycle, "CULTIVATE", scan_result=json.dumps(scan)[:1000])

        # CULTIVATE
        tasks = _cultivate(cycle, scan)
        _update_cycle(cycle, "HARVEST")

        # HARVEST
        results = _harvest(cycle)
        _update_cycle(cycle, "UPGRADE")

        # UPGRADE
        upgrades = _upgrade(cycle, scan, results)
        _update_cycle(cycle, "GROW")

        # GROW
        growth = _grow(cycle, upgrades, scan)
        _update_cycle(cycle, "COMPLETE", status="done", improvements=json.dumps(upgrades))

        report = {
            "cycle": cycle,
            "started_at": started_at,
            "completed_at": datetime.utcnow().isoformat(),
            "scan": scan,
            "tasks_created": len(tasks),
            "tasks_harvested": len(results),
            "upgrades": upgrades,
            "growth": growth,
        }
        log_action("chug_cycle", "success", repo="ecosystem", agent="orchestrator", cycle=cycle,
                   notes=f"cycle {cycle} complete")
        return report

    except Exception as e:
        _update_cycle(cycle, "FAILED", status="failed")
        log_action("chug_cycle", "error", repo="ecosystem", agent="orchestrator", cycle=cycle,
                   notes=str(e)[:200])
        raise


def _update_cycle(cycle: int, phase: str, status: str = "running",
                  scan_result: str = None, improvements: str = None) -> None:
    q = "UPDATE chug_cycles SET phase=?, status=?"
    args = [phase, status]
    if scan_result:
        q += ", scan_result=?"
        args.append(scan_result)
    if improvements:
        q += ", improvements=?"
        args.append(improvements)
    if phase == "COMPLETE" or status == "done":
        q += ", completed_at=?"
        args.append(datetime.utcnow().isoformat())
    q += " WHERE cycle_num=?"
    args.append(cycle)
    get_conn().execute(q, args)
    get_conn().commit()


# ── Reporting ──────────────────────────────────────────────────────────────

def get_status() -> Dict[str, Any]:
    """Return full orchestrator status snapshot."""
    last_cycle = mem_read("orchestrator.last_cycle")
    started_at = mem_read("orchestrator.started_at")
    cycles = [
        dict(r) for r in get_conn().execute(
            "SELECT * FROM chug_cycles ORDER BY cycle_num DESC LIMIT 5"
        ).fetchall()
    ]
    return {
        "orchestrator": {
            "started_at": started_at,
            "last_cycle": last_cycle,
            "version": "1.0.0",
        },
        "agents": list_agents(),
        "tools": {"total": len(list_tools()), "by_repo": _tools_by_repo()},
        "tasks": queue_stats(),
        "recent_cycles": cycles,
        "memory": mem_snapshot(),
        "recent_logs": recent_logs(limit=20),
    }


def _tools_by_repo() -> Dict[str, int]:
    rows = get_conn().execute(
        "SELECT repo, COUNT(*) as cnt FROM tool_registry WHERE enabled=1 GROUP BY repo"
    ).fetchall()
    return {r["repo"]: r["cnt"] for r in rows}


# ── Bootstrap on import ───────────────────────────────────────────────────
bootstrap()
