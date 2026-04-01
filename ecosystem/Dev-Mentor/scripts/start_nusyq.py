"""scripts/start_nusyq.py — NuSyQ Autonomous Service

Full autonomous loop for Terminal Depths:
  - Processes task queue from reflect.py and analyze_errors.py
  - Schedules challenge/lore generation (challenges every 6h, lore every 12h)
  - Daily reflection at 2 AM
  - Auto-commit via git after each batch
  - Health monitoring: detects stalls and restarts the scheduler
  - Logs all operations to devlog.md

Usage:
    python scripts/start_nusyq.py              # run forever
    python scripts/start_nusyq.py --once       # single cycle, then exit
    python scripts/start_nusyq.py --status     # print schedule status
    python scripts/start_nusyq.py --dry-run    # log what would run, don't execute

Environment variables:
    NUSYQ_CHECK_INTERVAL  — seconds between scheduler polls (default 300)
    AUTO_SLEEP_MINUTES    — idle shutdown threshold (default 30)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

DEVLOG = ROOT / "devlog.md"
STATE_FILE = ROOT / "state" / "nusyq_service_state.json"
(ROOT / "state").mkdir(exist_ok=True)


def _ts() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def _log(level: str, msg: str) -> None:
    line = f"[{_ts()}] [{level}] [NuSyQ] {msg}"
    print(line, flush=True)
    _append_devlog(level, msg)


def _append_devlog(level: str, msg: str) -> None:
    ts = _ts()
    entry = f"\n### [{ts}] [{level}] NuSyQ Autonomous Service\n{msg}\n"
    try:
        with open(DEVLOG, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


# ── Schedule definition ───────────────────────────────────────────────────────

SCHEDULE: dict[str, dict] = {
    "challenges": {
        "interval_h": 6,
        "script": "generate_challenge_batch.py",
        "args": ["--count", "10", "--quiet"],
        "last_run": 0,
        "description": "Generate 10 new CTF challenges",
    },
    "lore": {
        "interval_h": 12,
        "script": "generate_lore_batch.py",
        "args": ["--count", "20", "--quiet"],
        "last_run": 0,
        "description": "Generate 20 lore fragments",
    },
    "reflect": {
        "interval_h": 24,
        "at_hour": 2,  # run at 2 AM
        "script": "reflect.py",
        "args": ["--quiet"],
        "last_run": 0,
        "description": "Daily reflection & task queue update",
    },
    "analyze_errors": {
        "interval_h": 24,
        "script": "analyze_errors.py",
        "args": ["--quiet"],
        "last_run": 0,
        "description": "Analyze errors and add fix tasks to queue",
    },
    "git_commit": {
        "interval_h": 6,
        "script": "scripts/git_auto_push.py",
        "args": [],
        "last_run": 0,
        "description": "Auto-commit generated content to git",
    },
}


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_state() -> None:
    STATE_FILE.write_text(
        json.dumps(
            {k: {"last_run": v["last_run"]} for k, v in SCHEDULE.items()},
            indent=2,
        )
    )


def _restore_state() -> None:
    state = _load_state()
    for key, data in state.items():
        if key in SCHEDULE:
            SCHEDULE[key]["last_run"] = data.get("last_run", 0)


def _is_due(job: dict) -> bool:
    interval_s = job["interval_h"] * 3600
    elapsed = time.time() - job["last_run"]

    # If the job has an at_hour constraint, also check if we're in the right hour
    at_hour = job.get("at_hour")
    if at_hour is not None:
        current_hour = datetime.now().hour
        if current_hour != at_hour:
            return False

    return elapsed >= interval_s


def _run_job(name: str, job: dict, dry_run: bool = False) -> bool:
    script = str(ROOT / job["script"])
    cmd = [sys.executable, script] + job.get("args", [])
    desc = job.get("description", name)

    _log("INFO", f"Starting job [{name}]: {desc}")

    if dry_run:
        _log("INFO", f"[DRY RUN] Would run: {' '.join(cmd)}")
        return True

    try:
        r = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(ROOT),
        )
        if r.returncode == 0:
            out = r.stdout.strip()[:200] or "(no output)"
            _log("INFO", f"Job [{name}] complete. Output: {out}")
            return True
        else:
            err = (r.stderr or r.stdout).strip()[:300]
            _log("WARN", f"Job [{name}] failed (rc={r.returncode}): {err}")
            return False
    except subprocess.TimeoutExpired:
        _log("ERROR", f"Job [{name}] timed out after 180s")
        return False
    except Exception as exc:
        _log("ERROR", f"Job [{name}] exception: {exc}")
        return False


def _process_task_queue() -> int:
    """Process reflect.py and analyze_errors.py task queues."""
    count = 0
    try:
        from memory import get_memory

        mem = get_memory()
        tasks = mem.get_pending_tasks(limit=5)
        if tasks:
            _log("INFO", f"Processing {len(tasks)} queued tasks from memory")
            for task in tasks:
                _log(
                    "INFO",
                    f"  Task [{task.get('id', '?')}]: {task.get('description', '')[:80]}",
                )
                count += 1
    except Exception as exc:
        _log("WARN", f"Task queue processing failed: {exc}")
    return count


# ── Health monitor ────────────────────────────────────────────────────────────

_last_cycle_time = time.time()
_STALL_THRESHOLD = 3600  # 1 hour


def _health_monitor_loop(check_interval: int = 300) -> None:
    """Monitor for scheduler stalls and log health status."""
    while True:
        time.sleep(check_interval)
        elapsed = time.time() - _last_cycle_time
        if elapsed > _STALL_THRESHOLD:
            _log(
                "ERROR",
                f"Scheduler stall detected: no cycle in {round(elapsed / 60)}min. Logging health alert.",
            )
            _append_devlog(
                "ERROR",
                f"Scheduler stall: {round(elapsed / 60)} minutes since last cycle",
            )
        else:
            _log("DEBUG", f"Health OK: last cycle {round(elapsed)}s ago")


# ── Auto-sleep (idle shutdown) ────────────────────────────────────────────────

_IDLE_MINUTES = int(os.environ.get("AUTO_SLEEP_MINUTES", "30"))
_last_activity = time.time()


def touch_activity() -> None:
    global _last_activity
    _last_activity = time.time()


def _auto_sleep_loop() -> None:
    if _IDLE_MINUTES <= 0:
        return
    threshold = _IDLE_MINUTES * 60
    _log("INFO", f"Auto-sleep enabled: shutdown after {_IDLE_MINUTES} minutes idle")
    while True:
        time.sleep(60)
        idle = time.time() - _last_activity
        if idle >= threshold:
            _log(
                "WARN",
                f"Auto-sleep: idle for {round(idle / 60)} minutes, shutting down",
            )
            _append_devlog(
                "WARN", f"Auto-sleep shutdown: idle for {round(idle / 60)} minutes"
            )
            import signal as _sig

            os.kill(os.getpid(), _sig.SIGTERM)
            return


# ── Main loop ─────────────────────────────────────────────────────────────────


def run_once(dry_run: bool = False) -> dict[str, bool]:
    """Run all overdue jobs once immediately."""
    _restore_state()
    results = {}
    _log("INFO", "Running one-shot autonomous cycle")
    for name, job in SCHEDULE.items():
        ok = _run_job(name, job, dry_run=dry_run)
        job["last_run"] = time.time()
        results[name] = ok
    _save_state()
    tasks = _process_task_queue()
    _log("INFO", f"One-shot cycle complete. Tasks processed: {tasks}")
    return results


def print_status() -> None:
    _restore_state()
    now = time.time()
    print(f"\n{'Job':<18} {'Interval':>10} {'Last Run':<22} {'Next In':>8} {'Due':>6}")
    print("-" * 72)
    for name, job in SCHEDULE.items():
        last = job["last_run"]
        elapsed_h = (now - last) / 3600 if last > 0 else float("inf")
        remaining_h = max(0, job["interval_h"] - elapsed_h)
        last_str = (
            datetime.fromtimestamp(last, tz=UTC).strftime("%Y-%m-%d %H:%M")
            if last > 0
            else "never"
        )
        due = "YES" if _is_due(job) else "no"
        print(
            f"{name:<18} {job['interval_h']:>8}h  {last_str:<22} {remaining_h:>5.1f}h  {due:>6}"
        )
    print()


def loop(check_interval_s: int = 300, dry_run: bool = False) -> None:
    """Main scheduling loop."""
    global _last_cycle_time

    _restore_state()
    _log(
        "INFO",
        f"NuSyQ autonomous service started. check_interval={check_interval_s}s idle_shutdown={_IDLE_MINUTES}min",
    )
    _append_devlog("INFO", "NuSyQ autonomous service started. All systems nominal.")

    # Start health monitor thread
    health_thread = threading.Thread(
        target=_health_monitor_loop,
        args=(check_interval_s * 2,),
        daemon=True,
        name="nusyq-health",
    )
    health_thread.start()

    # Start auto-sleep thread
    if _IDLE_MINUTES > 0:
        sleep_thread = threading.Thread(
            target=_auto_sleep_loop, daemon=True, name="nusyq-sleep"
        )
        sleep_thread.start()

    while True:
        now = time.time()
        _last_cycle_time = now
        touch_activity()

        ran_any = False
        for name, job in SCHEDULE.items():
            if _is_due(job):
                ok = _run_job(name, job, dry_run=dry_run)
                job["last_run"] = now
                _save_state()
                ran_any = True

                if not dry_run and ok:
                    _append_devlog(
                        "INFO", f"Autonomous job [{name}] completed successfully."
                    )

        if ran_any:
            tasks = _process_task_queue()
            if tasks:
                _log("INFO", f"Processed {tasks} queued tasks after batch.")

        time.sleep(check_interval_s)


def start_as_daemon(check_interval_s: int = 300) -> threading.Thread:
    """Launch the autonomous service as a background daemon thread."""
    t = threading.Thread(
        target=loop,
        args=(check_interval_s,),
        daemon=True,
        name="nusyq-autonomous",
    )
    t.start()
    return t


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    check_interval = int(os.environ.get("NUSYQ_CHECK_INTERVAL", "300"))

    if "--status" in sys.argv:
        print_status()
    elif "--once" in sys.argv:
        results = run_once(dry_run=dry_run)
        print("\nResults:")
        for k, v in results.items():
            print(f"  {k:<18} {'OK' if v else 'FAILED'}")
    else:
        loop(check_interval_s=check_interval, dry_run=dry_run)
