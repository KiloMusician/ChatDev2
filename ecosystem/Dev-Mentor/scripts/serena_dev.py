#!/usr/bin/env python3
"""serena_dev.py — Serena Development Watchdog

Serena monitors the repository continuously during development sessions.
She detects drift, tracks what changed, generates action items from
critical signals, and writes session reports to state/.

Usage:
    python scripts/serena_dev.py               — one-shot report
    python scripts/serena_dev.py --watch       — continuous (polls every 60s)
    python scripts/serena_dev.py --walk        — re-index then report
    python scripts/serena_dev.py --tasks       — auto-create tasks from critical drift
    python scripts/serena_dev.py --align       — alignment check only

The watchdog is intentionally lightweight: all operations are L0 (read-only)
unless --tasks is passed, which creates MASTER_ZETA_TODO.md entries (L2).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from collections import Counter
from datetime import UTC, datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

LOG_DIR = BASE / "var"
STATE_DIR = BASE / "state"
LOG_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] SERENA-DEV %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "serena_dev.log"),
    ],
)
log = logging.getLogger("serena-dev")

# ANSI
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

TODO_FILE = BASE / "MASTER_ZETA_TODO.md"


# ── Redis (optional) ──────────────────────────────────────────────────────────

try:
    import redis as _redis_lib

    _r = _redis_lib.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
    )
    _r.ping()
    REDIS_OK = True
except Exception:
    _r = None
    REDIS_OK = False


def _publish(channel: str, data: dict) -> None:
    if REDIS_OK and _r:
        try:
            _r.publish(
                channel, json.dumps({**data, "_ts": datetime.now(UTC).isoformat()})
            )
        except Exception:
            pass


# ── Serena bootstrap ──────────────────────────────────────────────────────────


def _load_serena():
    from agents.serena import SerenaAgent

    return SerenaAgent(repo_root=BASE)


# ── Task creation from drift ──────────────────────────────────────────────────


def _next_task_id(prefix: str) -> str:
    if not TODO_FILE.exists():
        return f"{prefix}1"
    content = TODO_FILE.read_text()
    nums = [
        int(re.sub(r"\D", "", m.group(1)))
        for m in re.finditer(rf"\*\*({prefix}\d+)\*\*", content)
        if re.sub(r"\D", "", m.group(1)).isdigit()
    ]
    return f"{prefix}{max(nums, default=0) + 1}"


def _append_todo(task_id: str, description: str, priority: str = "P1") -> None:
    if not TODO_FILE.exists():
        TODO_FILE.write_text(f"# MASTER ZETA TODO LIST\n\n## {priority}\n\n")
    content = TODO_FILE.read_text()
    new_line = f"- [ ] **{task_id}**: {description}\n"
    target = f"## {priority}"
    if target in content:
        idx = content.index(target)
        line_end = content.index("\n", idx) + 1
        content = content[:line_end] + "\n" + new_line + content[line_end:]
    else:
        content += f"\n## {priority} — SERENA AUTO\n\n{new_line}\n"
    TODO_FILE.write_text(content)


# ── Core report ───────────────────────────────────────────────────────────────


def run_report(serena, *, walk: bool = False, create_tasks: bool = False) -> dict:
    """Generate a full development session report."""
    from agents.serena.drift import DriftDetector

    ts = datetime.now(UTC).isoformat()
    log.info("Starting Serena development report...")

    # ── Walk if requested or if index is empty ──────────────────────────────
    idx_stats = serena.memory.index_stats()
    if walk or idx_stats.get("total_chunks", 0) == 0:
        log.info("Walking repository (scoped)...")
        walk_result = serena.fast_walk()
        log.info(
            "Walk complete: chunks=%d files=%d elapsed=%.1fs",
            walk_result.get("chunks_added", 0),
            walk_result.get("files_visited", 0),
            walk_result.get("elapsed_s", 0),
        )
        idx_stats = serena.memory.index_stats()

    # ── Drift detection ─────────────────────────────────────────────────────
    det = DriftDetector(BASE, serena.memory._db_path)
    signals = det.detect_all(fast=True)
    sev_counts = Counter(s.severity for s in signals)
    cat_counts = Counter(s.category for s in signals)

    # ── Alignment ───────────────────────────────────────────────────────────
    alignment = det.align_check()

    # ── Git diff ────────────────────────────────────────────────────────────
    try:
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=BASE,
        )
        changed_files = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    except Exception:
        changed_files = []

    # ── Recent observations ─────────────────────────────────────────────────
    recent_obs = serena.memory.recent_observations(limit=10)

    # ── Print report ────────────────────────────────────────────────────────
    score = alignment.get("score", 0.0)
    a_color = GREEN if alignment.get("aligned") else (YELLOW if score > 0.6 else RED)
    verdict = (
        "ALIGNED"
        if alignment.get("aligned")
        else ("NOMINAL" if score > 0.6 else "DRIFTING")
    )

    print(f"\n{BOLD}{CYAN}{'═'*58}")
    print(f"  SERENA DEV REPORT  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═'*58}{RESET}\n")
    print(
        f"  {BOLD}Alignment{RESET}    {a_color}{score:.0%}  [{verdict}]{RESET}"
        f"  ({alignment['passed']}/{alignment['total']} checks)"
    )
    print(
        f"  {BOLD}Drift{RESET}        "
        f"{RED}{sev_counts.get('critical',0)} critical{RESET}  "
        f"{YELLOW}{sev_counts.get('warn',0)} warn{RESET}  "
        f"{DIM}{sev_counts.get('info',0)} info{RESET}"
    )
    print(
        f"  {BOLD}Index{RESET}        {idx_stats.get('total_chunks',0)} chunks  "
        f"{idx_stats.get('indexed_files',0)} files"
    )
    print(f"  {BOLD}Changed{RESET}      {len(changed_files)} file(s) since last commit")

    # ── Top drift signals ───────────────────────────────────────────────────
    critical = [s for s in signals if s.severity == "critical"]
    warnings = [s for s in signals if s.severity == "warn"]

    if critical:
        print(f"\n  {RED}{BOLD}Critical Drift:{RESET}")
        for sig in critical[:8]:
            print(
                f"    {RED}✕{RESET}  {BOLD}{sig.category}{RESET}  "
                f"{DIM}{sig.path}{RESET}"
            )
            print(f"       {sig.message}")

    if warnings[:5]:
        print(f"\n  {YELLOW}Warnings:{RESET}")
        for sig in warnings[:5]:
            print(f"    {YELLOW}⚠{RESET}  {sig.category}  {DIM}{sig.path}{RESET}")
            print(f"       {sig.message}")

    # ── Changed files ───────────────────────────────────────────────────────
    if changed_files:
        print(f"\n  {BOLD}Changed since last commit:{RESET}")
        for f in changed_files[:12]:
            print(f"    {DIM}○{RESET}  {f}")
        if len(changed_files) > 12:
            print(f"    {DIM}... {len(changed_files)-12} more{RESET}")

    # ── Recent observations ─────────────────────────────────────────────────
    if recent_obs:
        print(f"\n  {BOLD}Memory Palace (recent):{RESET}")
        for o in recent_obs[:5]:
            sev = o.get("severity", "info")
            c = {"critical": RED, "warn": YELLOW, "info": CYAN}.get(sev, DIM)
            ts_short = o.get("ts", "?")[:16]
            print(
                f"    {c}◦{RESET}  {DIM}{ts_short}{RESET}  " f"{o.get('subject','?')}"
            )

    # ── Auto-create tasks from critical drift ───────────────────────────────
    created_tasks: list[str] = []
    if create_tasks and critical:
        print(f"\n  {BOLD}Creating tasks from critical drift...{RESET}")
        for sig in critical[:5]:
            task_id = _next_task_id("S")
            desc = f"[Serena] {sig.category}: {sig.message[:80]} ({sig.path})"
            _append_todo(task_id, desc, priority="P1")
            created_tasks.append(task_id)
            print(f"    {GREEN}✓{RESET}  Created task {BOLD}{task_id}{RESET}")
            _publish(
                "lattice.task.created",
                {
                    "task_id": task_id,
                    "priority": "P1",
                    "description": desc,
                    "source": "serena-dev",
                    "drift_category": sig.category,
                    "drift_path": sig.path,
                },
            )

    print()

    # ── Build report dict ───────────────────────────────────────────────────
    report = {
        "ts": ts,
        "alignment": alignment,
        "severity_summary": dict(sev_counts),
        "category_summary": dict(cat_counts),
        "index_stats": idx_stats,
        "changed_files": changed_files,
        "top_signals": [s.to_dict() for s in signals[:20]],
        "created_tasks": created_tasks,
    }

    # Save to state/
    report_path = STATE_DIR / "serena_dev_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    log.info("Report saved → %s", report_path)

    # Record as observation
    serena.observe(
        subject="dev_report",
        note=(
            f"alignment={score:.0%} critical={sev_counts.get('critical',0)} "
            f"warn={sev_counts.get('warn',0)} changed={len(changed_files)}"
        ),
        severity="warn" if sev_counts.get("critical", 0) > 0 else "info",
    )

    _publish("lattice.serena.dev_report", report)

    return report


def run_align_only(serena) -> None:
    """Print alignment check only."""
    from agents.serena.drift import DriftDetector

    det = DriftDetector(BASE, serena.memory._db_path)
    result = det.align_check()
    score = result.get("score", 0.0)
    aligned = result.get("aligned", False)
    a_color = GREEN if aligned else (YELLOW if score > 0.6 else RED)
    verdict = "ALIGNED" if aligned else ("NOMINAL" if score > 0.6 else "DRIFTING")
    print(f"\n  Alignment: {a_color}{BOLD}{score:.0%}  [{verdict}]{RESET}")
    print(f"  {DIM}{result.get('horizon','')}{RESET}\n")
    for c in result.get("checks", []):
        icon = f"{GREEN}✓{RESET}" if c["passed"] else f"{RED}✗{RESET}"
        print(f"  {icon}  {c['name']:<28} {c['message']}")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(
        description="Serena Development Watchdog — always-on code intelligence"
    )
    ap.add_argument(
        "--watch", action="store_true", help="Continuous mode (polls every 60s)"
    )
    ap.add_argument(
        "--walk", action="store_true", help="Re-index repository before reporting"
    )
    ap.add_argument(
        "--tasks",
        action="store_true",
        help="Auto-create MASTER_ZETA_TODO entries from critical drift",
    )
    ap.add_argument("--align", action="store_true", help="Alignment check only (fast)")
    ap.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Watch mode poll interval in seconds (default: 60)",
    )
    args = ap.parse_args()

    log.info("Serena Development Watchdog initialising...")

    try:
        serena = _load_serena()
    except Exception as exc:
        log.error("Could not load Serena: %s", exc)
        sys.exit(1)

    if args.align:
        run_align_only(serena)
        return

    if args.watch:
        log.info("Watch mode — polling every %ds", args.interval)
        cycle = 0
        while True:
            try:
                cycle += 1
                run_report(
                    serena, walk=(cycle == 1 or args.walk), create_tasks=args.tasks
                )
            except KeyboardInterrupt:
                log.info("Watchdog stopped.")
                break
            except Exception as exc:
                log.error("Report cycle failed: %s", exc)
            try:
                time.sleep(args.interval)
            except KeyboardInterrupt:
                log.info("Watchdog stopped.")
                break
    else:
        run_report(serena, walk=args.walk, create_tasks=args.tasks)


if __name__ == "__main__":
    main()
