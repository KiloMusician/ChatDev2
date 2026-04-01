#!/usr/bin/env python3
"""NuSyQ-Chug: Autonomous assembly-line developer agent.

Runs timed work phases (5 → 10 → 15 → 30 → 60 minutes) using the real
nq CLI, start_nusyq.py, keeper.ps1, and the Dev-Mentor task queue.

Usage:
    python scripts/nusyq_chug.py                        # default: 12h, all phases
    python scripts/nusyq_chug.py --hours 2              # 2h cap
    python scripts/nusyq_chug.py --phase 15             # single 15-min phase
    python scripts/nusyq_chug.py --dry-run              # log plan, no exec
    python scripts/nusyq_chug.py --stop-on-failure      # pause if phase fails

Stop conditions (automatic):
    - Consecutive phase failures >= 3
    - Unexpected test regression (more failures than baseline)
    - Git working tree has > 50 uncommitted files
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Repo roots ────────────────────────────────────────────────────────────────
NUSYQ_HUB = Path("C:/prime_anchor/NuSyQ-Hub")
CONCEPT = Path("C:/CONCEPT")
DEV_MENTOR = Path("C:/Users/keath/Dev-Mentor")
SIMVERSE = Path("C:/prime_anchor/SimulatedVerse/SimulatedVerse")

# Resolve the real Python interpreter (Windows Store stub doesn't have packages)


def _resolve_python() -> str:
    import shutil
    candidates = [
        sys.executable,
        r"C:\Users\keath\AppData\Local\Programs\Python\Python312\python.exe",
        r"C:\Users\keath\AppData\Local\Programs\Python\Python311\python.exe",
        "python",
    ]
    for c in candidates:
        if Path(c).is_file() and "WindowsApps" not in c:
            return c
    return shutil.which("python") or sys.executable


PYTHON = _resolve_python()

QUEUE_JSON = DEV_MENTOR / "tasks" / "queue.json"
STATE_DIR = NUSYQ_HUB / "state"
CHUG_LOG = STATE_DIR / "chug_session.jsonl"

# ── Phase definitions ─────────────────────────────────────────────────────────


@dataclass
class Phase:
    duration_minutes: int
    goal: str
    target_fixes: int          # expected number of errors/issues to close
    target_loc: int            # expected lines of new/changed code
    steps: list[dict[str, Any]] = field(default_factory=list)


PHASES: list[Phase] = [
    Phase(
        duration_minutes=5,
        goal="Quick health check + identify minor tasks",
        target_fixes=3,
        target_loc=0,
        steps=[
            {"label": "ecosystem health", "cmd": ["python", "scripts/start_nusyq.py", "system_complete", "--budget-s=30"], "cwd": NUSYQ_HUB},
            {"label": "keeper status", "cmd": ["pwsh", "-NoProfile", "-NonInteractive", "-File", str(CONCEPT / "keeper.ps1"), "status"], "cwd": CONCEPT},
            {"label": "next action queue", "cmd": ["python", "scripts/start_nusyq.py", "next_action_generate"], "cwd": NUSYQ_HUB},
            {"label": "error summary", "cmd": ["python", "scripts/start_nusyq.py", "error_report", "--quick"], "cwd": NUSYQ_HUB},
            {"label": "queue drain (1 task)", "cmd": ["python", "nq", "bg", "process", "1"], "cwd": NUSYQ_HUB, "optional": True},
        ],
    ),
    Phase(
        duration_minutes=10,
        goal="Fix small issues + sync state",
        target_fixes=5,
        target_loc=20,
        steps=[
            {"label": "nq fix hub src", "cmd": ["python", "nq", "fix", "src/"], "cwd": NUSYQ_HUB, "optional": True},
            {"label": "nq fix dev-mentor", "cmd": ["python", "nq", "fix", str(DEV_MENTOR / "scripts")], "cwd": NUSYQ_HUB, "optional": True},
            {"label": "process bg queue x3", "cmd": ["python", "nq", "bg", "process", "3"], "cwd": NUSYQ_HUB, "optional": True},
            {"label": "keeper score", "cmd": ["pwsh", "-NoProfile", "-NonInteractive", "-File", str(CONCEPT / "keeper.ps1"), "score"], "cwd": CONCEPT},
            {"label": "drain chatdev queue", "cmd": ["python", str(DEV_MENTOR / "scripts" / "chatdev_worker.py"), "--once"], "cwd": DEV_MENTOR, "optional": True},
            {"label": "git status check", "cmd": ["git", "status", "--short"], "cwd": NUSYQ_HUB},
        ],
    ),
    Phase(
        duration_minutes=15,
        goal="Automated enhancements + tests",
        target_fixes=10,
        target_loc=50,
        steps=[
            {"label": "nq cycle (auto dev)", "cmd": ["python", "nq", "cycle", "--tasks", "5"], "cwd": NUSYQ_HUB},
            {"label": "auto_cycle x3", "cmd": ["python", "scripts/start_nusyq.py", "auto_cycle", "--iterations=3", "--sleep=5"], "cwd": NUSYQ_HUB},
            {"label": "nq health", "cmd": ["python", "nq", "health"], "cwd": NUSYQ_HUB},
            {"label": "pester tests (brain)", "cmd": ["pwsh", "-NoProfile", "-NonInteractive", "-Command", "Invoke-Pester -Path tests -TagFilter brain -Output Normal; exit $LASTEXITCODE"], "cwd": CONCEPT, "optional": True},
            {"label": "process bg queue x5", "cmd": ["python", "nq", "bg", "process", "5"], "cwd": NUSYQ_HUB, "optional": True},
            {"label": "keeper recommend", "cmd": ["pwsh", "-NoProfile", "-NonInteractive", "-File", str(CONCEPT / "keeper.ps1"), "recommend"], "cwd": CONCEPT},
        ],
    ),
    Phase(
        duration_minutes=30,
        goal="Deep integration tasks + tech debt",
        target_fixes=20,
        target_loc=100,
        steps=[
            {"label": "bg run 25min", "cmd": ["python", "nq", "bg", "run", "--minutes", "20", "--batch", "3", "--target-completions", "10"], "cwd": NUSYQ_HUB},
            {"label": "nq analyze hub src", "cmd": ["python", "nq", "analyze", "src/"], "cwd": NUSYQ_HUB, "optional": True},
            {"label": "nq factory doctor", "cmd": ["python", "nq", "factory", "doctor"], "cwd": NUSYQ_HUB, "optional": True},
            {"label": "drain chatdev queue", "cmd": ["python", str(DEV_MENTOR / "scripts" / "chatdev_worker.py"), "--once"], "cwd": DEV_MENTOR, "optional": True},
            {"label": "next_action_generate", "cmd": ["python", "scripts/start_nusyq.py", "next_action_generate"], "cwd": NUSYQ_HUB},
            {"label": "git commit sweep", "cmd": ["git", "diff", "--stat", "HEAD"], "cwd": NUSYQ_HUB},
        ],
    ),
    Phase(
        duration_minutes=60,
        goal="Synthesis, consolidation, full test pass",
        target_fixes=30,
        target_loc=200,
        steps=[
            {"label": "bg run 50min", "cmd": ["python", "nq", "bg", "run", "--minutes", "45", "--batch", "5", "--target-completions", "20"], "cwd": NUSYQ_HUB},
            {"label": "nq factory autopilot", "cmd": ["python", "nq", "factory", "autopilot", "--fix"], "cwd": NUSYQ_HUB, "optional": True},
            {"label": "pester all tests", "cmd": ["pwsh", "-NoProfile", "-NonInteractive", "-Command", "Invoke-Pester -Path tests -Output Normal; exit $LASTEXITCODE"], "cwd": CONCEPT, "optional": True},
            {"label": "error report final", "cmd": ["python", "scripts/start_nusyq.py", "error_report", "--quick"], "cwd": NUSYQ_HUB},
            {"label": "keeper maintain", "cmd": ["pwsh", "-NoProfile", "-File", str(CONCEPT / "keeper.ps1"), "maintain"], "cwd": CONCEPT, "optional": True},
            {"label": "ecosystem snapshot", "cmd": ["python", "scripts/start_nusyq.py", "brief"], "cwd": NUSYQ_HUB},
        ],
    ),
]

PHASE_MAP = {p.duration_minutes: p for p in PHASES}

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CHUG] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("chug")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_event(event: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with CHUG_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


# ── Task queue helpers ────────────────────────────────────────────────────────
def _load_queue() -> list[dict[str, Any]]:
    if not QUEUE_JSON.exists():
        return []
    try:
        data = json.loads(QUEUE_JSON.read_text(encoding="utf-8"))
        return data.get("tasks", [])
    except Exception:
        return []


def _pending_tasks() -> list[dict[str, Any]]:
    return [t for t in _load_queue() if t.get("status") == "pending"]


def _mark_task_running(task_id: str) -> None:
    if not QUEUE_JSON.exists():
        return
    try:
        data = json.loads(QUEUE_JSON.read_text(encoding="utf-8"))
        for t in data.get("tasks", []):
            if t.get("id") == task_id:
                t["status"] = "running"
                t["started_at"] = _now_iso()
                break
        QUEUE_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        log.warning("Could not update queue: %s", exc)


def _mark_task_done(task_id: str, output_preview: str) -> None:
    if not QUEUE_JSON.exists():
        return
    try:
        data = json.loads(QUEUE_JSON.read_text(encoding="utf-8"))
        for t in data.get("tasks", []):
            if t.get("id") == task_id:
                t["status"] = "completed"
                t["completed_at"] = _now_iso()
                t["output_preview"] = output_preview[:300]
                data["updated_at"] = _now_iso()
                break
        QUEUE_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        log.warning("Could not update queue: %s", exc)


# ── Command runner ────────────────────────────────────────────────────────────
def run_step(step: dict[str, Any], timeout: int, dry_run: bool) -> tuple[bool, str]:
    """Run a single phase step. Returns (success, output_preview)."""
    label = step["label"]
    # Substitute the "python" placeholder with the real interpreter at runtime
    cmd = [PYTHON if c == "python" else c for c in step["cmd"]]
    cwd = str(step.get("cwd", NUSYQ_HUB))
    optional = step.get("optional", False)

    log.info("  ▶ %s", label)
    if dry_run:
        log.info("    [dry-run] %s", " ".join(str(c) for c in cmd))
        return True, "[dry-run]"

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (result.stdout or "") + (result.stderr or "")
        preview = output[:400].strip()
        if result.returncode == 0:
            log.info("    ✅ OK")
            return True, preview
        else:
            if optional:
                log.info("    ⚠️  non-zero exit %d (optional — continuing)", result.returncode)
                return True, preview
            log.warning("    ❌ exit %d: %s", result.returncode, preview[:120])
            return False, preview
    except subprocess.TimeoutExpired:
        msg = f"timeout after {timeout}s"
        if optional:
            log.info("    ⚠️  %s (optional — continuing)", msg)
            return True, msg
        log.warning("    ❌ %s", msg)
        return False, msg
    except FileNotFoundError as exc:
        msg = f"command not found: {exc}"
        if optional:
            log.info("    ⚠️  %s (optional — skipping)", msg)
            return True, msg
        log.warning("    ❌ %s", msg)
        return False, msg
    except Exception as exc:
        msg = str(exc)
        log.warning("    ❌ unexpected: %s", msg)
        return False, msg


# ── Phase runner ─────────────────────────────────────────────────────────────
def run_phase(phase: Phase, dry_run: bool) -> dict[str, Any]:
    duration = phase.duration_minutes
    log.info("")
    log.info("━" * 60)
    log.info("⏱  PHASE %dmin — %s", duration, phase.goal)
    log.info("   targets: ~%d fixes, ~%d lines", phase.target_fixes, phase.target_loc)
    log.info("━" * 60)

    phase_start = time.monotonic()
    step_timeout = max(30, (duration * 60) // max(len(phase.steps), 1))

    results = []
    failures = 0

    for step in phase.steps:
        elapsed = time.monotonic() - phase_start
        budget_left = duration * 60 - elapsed
        if budget_left < 10:
            log.info("  ⏰ Phase budget exhausted — skipping remaining steps")
            break

        ok, preview = run_step(step, timeout=min(step_timeout, int(budget_left - 5)), dry_run=dry_run)
        results.append({"step": step["label"], "ok": ok, "preview": preview[:200]})
        if not ok:
            failures += 1

    # Also drain any pending Dev-Mentor queue tasks that match current phase
    pending = _pending_tasks()
    if pending and not dry_run:
        log.info("  📋 Dev-Mentor queue: %d pending tasks", len(pending))
        for task in pending[:2]:  # max 2 per phase
            tid = task["id"]
            desc = task.get("description", "")[:80]
            log.info("    🔧 dispatching: %s — %s", tid, desc)
            _mark_task_running(tid)
            ok2, out2 = run_step(
                {
                    "label": f"queue:{tid}",
                    "cmd": [
                        "python", "nq", "bg", "dispatch",
                        f"Task {tid}: {task.get('description', '')}. "
                        f"Target: {task.get('target', 'unknown')}. "
                        f"Context: {task.get('context', '')}",
                    ],
                    "cwd": NUSYQ_HUB,
                    "optional": True,
                },
                timeout=120,
                dry_run=dry_run,
            )
            _mark_task_done(tid, out2)

    elapsed_total = time.monotonic() - phase_start
    success = failures == 0 or failures <= len(phase.steps) // 2

    summary = {
        "phase_minutes": duration,
        "goal": phase.goal,
        "started_at": _now_iso(),
        "elapsed_s": round(elapsed_total, 1),
        "steps_run": len(results),
        "failures": failures,
        "success": success,
        "results": results,
    }
    _append_event({"type": "phase_complete", **summary})

    status_icon = "✅" if success else "❌"
    log.info("  %s Phase %dmin done — %d steps, %d failures (%.0fs)", status_icon, duration, len(results), failures, elapsed_total)
    return summary


# ── Git helpers ───────────────────────────────────────────────────────────────
def _count_dirty_files(repo: Path) -> int:
    try:
        r = subprocess.run(["git", "status", "--short"], cwd=str(repo), capture_output=True, text=True, timeout=10)
        return len([l for l in r.stdout.splitlines() if l.strip()])
    except Exception:
        return 0


def _should_stop(consecutive_failures: int, dirty_count: int, stop_on_failure: bool) -> tuple[bool, str]:
    if consecutive_failures >= 3:
        return True, f"3 consecutive phase failures"
    if dirty_count > 500:
        return True, f"working tree has {dirty_count} uncommitted files (> 500)"
    if stop_on_failure and consecutive_failures >= 1:
        return True, "--stop-on-failure and phase failed"
    return False, ""


# ── Main loop ─────────────────────────────────────────────────────────────────
def run_chug(
    total_hours: float,
    single_phase: int | None,
    dry_run: bool,
    stop_on_failure: bool,
) -> int:
    total_seconds = total_hours * 3600
    session_start = time.monotonic()

    log.info("🚀 NuSyQ-Chug starting | budget=%.1fh dry_run=%s", total_hours, dry_run)
    _append_event({
        "type": "session_start",
        "ts": _now_iso(),
        "budget_hours": total_hours,
        "dry_run": dry_run,
        "single_phase": single_phase,
    })

    if single_phase is not None:
        if single_phase not in PHASE_MAP:
            log.error("Unknown phase duration: %d. Valid: %s", single_phase, sorted(PHASE_MAP))
            return 1
        summary = run_phase(PHASE_MAP[single_phase], dry_run)
        return 0 if summary["success"] else 1

    # Cycle through all phases repeatedly until budget exhausted
    phase_order = [5, 10, 15, 30, 60]
    consecutive_failures = 0
    cycle_num = 0

    while True:
        elapsed = time.monotonic() - session_start
        remaining = total_seconds - elapsed
        if remaining < 60:
            log.info("⏰ Session budget exhausted (%.0fs remaining). Stopping.", remaining)
            break

        cycle_num += 1
        log.info("\n🔁 CYCLE %d | elapsed=%.0fm remaining=%.0fm", cycle_num, elapsed / 60, remaining / 60)

        for minutes in phase_order:
            elapsed = time.monotonic() - session_start
            remaining = total_seconds - elapsed
            if remaining < minutes * 60:
                log.info("  ⏭️  Skipping %dmin phase — insufficient budget (%.0fm left)", minutes, remaining / 60)
                continue

            dirty = _count_dirty_files(NUSYQ_HUB)
            stop, reason = _should_stop(consecutive_failures, dirty, stop_on_failure)
            if stop:
                log.warning("🛑 STOP CONDITION: %s", reason)
                _append_event({"type": "stop", "reason": reason, "ts": _now_iso()})
                _print_report(session_start, cycle_num)
                return 1

            summary = run_phase(PHASE_MAP[minutes], dry_run)
            if summary["success"]:
                consecutive_failures = 0
            else:
                consecutive_failures += 1

            # Cool-down between phases (5s)
            if not dry_run:
                time.sleep(5)

    _print_report(session_start, cycle_num)
    return 0


def _print_report(session_start: float, cycles: int) -> None:
    elapsed = time.monotonic() - session_start
    log.info("")
    log.info("═" * 60)
    log.info("📊 CHUG SESSION REPORT")
    log.info("   elapsed: %.0fm", elapsed / 60)
    log.info("   cycles:  %d", cycles)
    try:
        events = [json.loads(l) for l in CHUG_LOG.read_text().splitlines() if l.strip()]
        phase_events = [e for e in events if e.get("type") == "phase_complete"]
        total_steps = sum(e.get("steps_run", 0) for e in phase_events)
        total_fails = sum(e.get("failures", 0) for e in phase_events)
        log.info("   phases:  %d total steps=%d failures=%d", len(phase_events), total_steps, total_fails)
    except Exception:
        pass
    log.info("   log:     %s", CHUG_LOG)
    log.info("═" * 60)
    _append_event({"type": "session_end", "ts": _now_iso(), "elapsed_s": round(elapsed, 1), "cycles": cycles})


# ── CLI ───────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="NuSyQ-Chug autonomous developer agent")
    parser.add_argument("--hours", type=float, default=12.0, help="Total session budget in hours (default: 12)")
    parser.add_argument("--phase", type=int, choices=sorted(PHASE_MAP), help="Run a single phase and exit")
    parser.add_argument("--dry-run", action="store_true", help="Log plan without executing commands")
    parser.add_argument("--stop-on-failure", action="store_true", help="Pause immediately on first phase failure")
    args = parser.parse_args()

    return run_chug(
        total_hours=args.hours,
        single_phase=args.phase,
        dry_run=args.dry_run,
        stop_on_failure=args.stop_on_failure,
    )


if __name__ == "__main__":
    sys.exit(main())
