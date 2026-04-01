"""scripts/content_scheduler.py — Background autonomous content generation.

Runs as a daemon thread (launched by the server) or standalone process.
Schedules:
  • Every 6h  — generate_challenge_batch (10 new challenges)
  • Every 12h — generate_lore_batch (20 new lore fragments)
  • Every 24h — generate_story_beats (5 new beats)
  • Every 24h — generate_node_batch (3 new world nodes)
  • Every 24h — reflect.py (daily reflection + task queue)
  • Every 6h  — git push (auto-commit generated content)
  • Every 24h — git_create_issue.py (create GitHub issues from task queue)
  • Every 24h — nusyq_bridge sync-quests (mirror challenges to quest log)

Usage (standalone):
    python scripts/content_scheduler.py               # run forever
    python scripts/content_scheduler.py --once        # run one cycle immediately
    python scripts/content_scheduler.py --status      # show schedule

Usage (from server):
    from scripts.content_scheduler import start_scheduler
    start_scheduler()  # launches daemon thread
"""

from __future__ import annotations

import json
import sys
import threading
import time
from datetime import UTC, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCHEDULE_FILE = ROOT / "state" / "scheduler_state.json"
(ROOT / "state").mkdir(exist_ok=True)


SCHEDULE: dict[str, dict] = {
    "challenges": {
        "interval_h": 6,
        "script": "generate_challenge_batch.py",
        "args": ["--count", "10"],
        "last_run": 0,
    },
    "lore": {
        "interval_h": 12,
        "script": "generate_lore_batch.py",
        "args": ["--count", "20"],
        "last_run": 0,
    },
    "story": {
        "interval_h": 24,
        "script": "generate_story_beats.py",
        "args": ["--count", "5"],
        "last_run": 0,
    },
    "nodes": {
        "interval_h": 24,
        "script": "scripts/generate_node_batch.py",
        "args": ["--count", "3"],
        "last_run": 0,
    },
    "reflect": {"interval_h": 24, "script": "reflect.py", "args": [], "last_run": 0},
    "issues": {
        "interval_h": 24,
        "script": "scripts/git_create_issue.py",
        "args": ["--limit", "5"],
        "last_run": 0,
    },
    "git": {
        "interval_h": 6,
        "script": "scripts/git_auto_push.py",
        "args": [],
        "last_run": 0,
    },
    "quest_sync": {
        "interval_h": 12,
        "script": "nusyq_bridge.py",
        "args": ["sync-quests"],
        "last_run": 0,
    },
}


def _load_state() -> dict:
    if SCHEDULE_FILE.exists():
        try:
            return json.loads(SCHEDULE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_state() -> None:
    SCHEDULE_FILE.write_text(
        json.dumps(
            {k: {"last_run": v["last_run"]} for k, v in SCHEDULE.items()},
            indent=2,
        )
    )


def _restore_state() -> None:
    state = _load_state()
    now = time.time()
    for key in SCHEDULE:
        if key in state:
            SCHEDULE[key]["last_run"] = state[key].get("last_run", 0)
        else:
            # No saved state for this job — treat as just-run so the first
            # execution is deferred by one full interval. This prevents all
            # jobs (especially `git`) from firing immediately on server restart.
            SCHEDULE[key]["last_run"] = now


def _run_script(name: str, job: dict) -> bool:
    import subprocess

    script = str(ROOT / job["script"])
    cmd = [sys.executable, script] + job["args"]
    print(f"[scheduler] Running {name}: {' '.join(cmd[-3:])}", flush=True)
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, cwd=str(ROOT)
        )  # nosec B603
        if r.returncode == 0:
            print(f"[scheduler] ✓ {name} complete", flush=True)
        else:
            print(f"[scheduler] ✗ {name} failed: {r.stderr[:200]}", flush=True)
        return r.returncode == 0
    except Exception as exc:
        print(f"[scheduler] ✗ {name} exception: {exc}", flush=True)
        return False


def _due(job: dict) -> bool:
    interval_s = job["interval_h"] * 3600
    return (time.time() - job["last_run"]) >= interval_s


def run_once() -> dict[str, bool]:
    """Run all overdue jobs immediately."""
    results = {}
    for name, job in SCHEDULE.items():
        ok = _run_script(name, job)
        job["last_run"] = time.time()
        results[name] = ok
    _save_state()
    return results


def loop(check_interval_s: int = 300) -> None:
    """Infinite scheduling loop — run in a daemon thread."""
    _restore_state()
    print("[scheduler] Content scheduler started", flush=True)
    while True:
        now = time.time()
        for name, job in SCHEDULE.items():
            if _due(job):
                _run_script(name, job)
                job["last_run"] = now
                _save_state()
        time.sleep(check_interval_s)


def status() -> list[dict]:
    """Return schedule status for all jobs."""
    _restore_state()
    now = time.time()
    rows = []
    for name, job in SCHEDULE.items():
        last = job["last_run"]
        elapsed_h = (now - last) / 3600 if last > 0 else float("inf")
        remaining_h = max(0, job["interval_h"] - elapsed_h)
        rows.append(
            {
                "job": name,
                "interval_h": job["interval_h"],
                "last_run": (
                    datetime.fromtimestamp(last, tz=UTC).isoformat()
                    if last > 0
                    else "never"
                ),
                "next_run_h": round(remaining_h, 1),
                "overdue": elapsed_h >= job["interval_h"],
            }
        )
    return rows


def start_scheduler(check_interval_s: int = 300) -> threading.Thread:
    """Launch scheduler as a background daemon thread."""
    t = threading.Thread(
        target=loop, args=(check_interval_s,), daemon=True, name="content-scheduler"
    )
    t.start()
    return t


if __name__ == "__main__":
    if "--once" in sys.argv:
        results = run_once()
        for k, v in results.items():
            print(f"  {k:<15} {'OK' if v else 'FAILED'}")
    elif "--status" in sys.argv:
        rows = status()
        print(
            f"{'Job':<15} {'Interval':>10} {'Last Run':<22} {'Next In':>8} {'Overdue':>8}"
        )
        print("-" * 70)
        for r in rows:
            print(
                f"{r['job']:<15} {r['interval_h']:>8}h  {r['last_run']:<22} {r['next_run_h']:>6}h  {'YES' if r['overdue'] else 'no':>8}"
            )
    else:
        loop()
