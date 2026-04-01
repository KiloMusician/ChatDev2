#!/usr/bin/env python3
"""NuSyQ Autonomous Development Runner
====================================
Runs the autonomous development loop for a specified duration.

Usage:
    python run_autonomous.py                  # Run for 4 hours (default)
    python run_autonomous.py --hours 2        # Run for 2 hours
    python run_autonomous.py --cycles 10      # Run exactly 10 cycles
    python run_autonomous.py --tasks 20       # Process 20 tasks per cycle
"""

import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent))


def _queue_stats(queue_path: Path) -> dict[str, int]:
    """Load simple queue stats from unified_pu_queue.json."""
    if not queue_path.exists():
        return {"total": 0, "pending": 0, "completed": 0, "failed": 0}

    with open(queue_path, encoding="utf-8") as f:
        pus = json.load(f)

    pending = sum(1 for p in pus if p.get("status") in {"approved", "queued", "pending"})
    completed = sum(1 for p in pus if p.get("status") == "completed")
    failed = sum(1 for p in pus if p.get("status") == "failed")
    return {"total": len(pus), "pending": pending, "completed": completed, "failed": failed}


def _normalize_queue_schema(queue_path: Path) -> int:
    """Normalize queue entries to UnifiedPUQueue dataclass schema."""
    if not queue_path.exists():
        return 0

    try:
        raw = json.loads(queue_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0

    if not isinstance(raw, list):
        return 0

    allowed = {
        "id",
        "type",
        "title",
        "description",
        "source_repo",
        "priority",
        "proof_criteria",
        "metadata",
        "status",
        "created_at",
        "votes",
        "assigned_agents",
        "execution_results",
    }
    changed = 0
    normalized: list[dict[str, Any]] = []

    for entry in raw:
        if not isinstance(entry, dict):
            changed += 1
            continue

        pu = dict(entry)
        if "source" in pu and "source_repo" not in pu:
            pu["source_repo"] = pu.pop("source")
            changed += 1

        clean = {k: pu[k] for k in allowed if k in pu}
        clean.setdefault("id", "")
        clean.setdefault("type", "AnalysisPU")
        clean.setdefault("title", "(untitled)")
        clean.setdefault("description", "")
        clean.setdefault("source_repo", "nusyq-hub")
        clean.setdefault("priority", "medium")
        clean.setdefault("proof_criteria", ["diagnose", "resolve", "verify"])
        clean.setdefault("metadata", {})
        clean.setdefault("status", "approved")
        clean.setdefault("created_at", datetime.now().isoformat())
        clean.setdefault("votes", {})
        clean.setdefault("assigned_agents", [])
        clean.setdefault("execution_results", {})

        if set(pu.keys()) != set(clean.keys()):
            changed += 1
        normalized.append(clean)

    if changed > 0:
        queue_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    return changed


def _refill_queue_from_audit(mode: str) -> dict[str, Any]:
    """Refill queue by running the autonomous loop audit pass once."""
    from src.automation.autonomous_loop import AutonomousLoop

    loop = AutonomousLoop(
        interval_minutes=5,
        mode=mode,
        # This instance is used for `_run_audit()` only, but avoid zero-task
        # initialization logs because they look like a runtime misconfiguration.
        max_tasks_per_cycle=1,
        max_cycles=1,
    )
    return loop._run_audit()


def _refill_queue_from_sector_gaps(queue_path: Path, min_pending: int) -> int:
    """Create approved PUs from detected sector gaps until queue reaches min_pending."""
    from src.automation.autonomous_monitor import AutonomousMonitor

    try:
        queue = json.loads(queue_path.read_text(encoding="utf-8")) if queue_path.exists() else []
    except (OSError, ValueError):
        queue = []

    pending = sum(1 for p in queue if p.get("status") in {"approved", "queued", "pending"})
    needed = max(0, min_pending - pending)
    if needed == 0:
        return 0

    monitor = AutonomousMonitor(audit_interval=300, enable_sector_awareness=True)
    gaps = monitor.get_sector_gaps()
    if not gaps:
        return 0

    # Only dedupe against active queue items, so completed historical entries
    # don't block future refill cycles for the same gap signature.
    existing_titles = {
        p.get("title", "") for p in queue if p.get("status") in {"approved", "queued", "pending"}
    }
    created = 0
    ts = int(datetime.now().timestamp())

    for index, gap in enumerate(gaps):
        if created >= needed:
            break

        sector = gap.get("sector", "unknown")
        component = gap.get("component") or gap.get("type", "gap")
        title = f"Close sector gap: {sector} / {component}"
        if title in existing_titles:
            continue

        severity = str(gap.get("severity", "medium")).lower()
        priority = "high" if severity in {"critical", "high"} else "medium"
        pu_type = "BugFixPU" if severity in {"critical", "high"} else "RefactorPU"

        queue.append(
            {
                "id": f"PU-gap-{ts}-{created}-{index}",
                "type": pu_type,
                "title": title,
                "description": gap.get("description", "Autonomous sector gap remediation"),
                "source_repo": "nusyq-hub",
                "priority": priority,
                "proof_criteria": ["diagnose", "resolve", "verify"],
                "metadata": {"gap": gap},
                "status": "approved",
                "created_at": datetime.now().isoformat(),
                "votes": {},
                "assigned_agents": [],
                "execution_results": {"note": "seeded from sector gap refill"},
            }
        )
        existing_titles.add(title)
        created += 1

    if created > 0:
        queue_path.write_text(json.dumps(queue, indent=2), encoding="utf-8")
    return created


def _run_doctor_preflight(
    strict_hooks: bool,
    include_examples: bool,
    workspace_integrity: bool,
) -> dict[str, Any]:
    """Run factory doctor preflight before starting long autonomous loops."""
    from src.factories.project_factory import ProjectFactory

    factory = ProjectFactory()
    return factory.run_doctor(
        strict_hooks=strict_hooks,
        include_examples=include_examples,
        include_workspace=workspace_integrity,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run NuSyQ autonomous development loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_autonomous.py                    # 4 hours, 10 tasks/cycle
    python run_autonomous.py --hours 1          # 1 hour run
    python run_autonomous.py --cycles 5         # Just 5 cycles
    python run_autonomous.py --dry-run          # Show what would happen
        """,
    )
    parser.add_argument("--hours", type=float, default=4.0, help="Duration in hours (default: 4)")
    parser.add_argument(
        "--interval", type=int, default=5, help="Minutes between cycles (default: 5)"
    )
    parser.add_argument("--tasks", type=int, default=10, help="Tasks per cycle (default: 10)")
    parser.add_argument(
        "--cycles", type=int, default=0, help="Exact number of cycles (overrides --hours)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show configuration without running")
    parser.add_argument(
        "--mode", choices=["normal", "overnight"], default="normal", help="Operation mode"
    )
    parser.add_argument(
        "--min-pending",
        type=int,
        default=10,
        help="Minimum pending PUs to keep in queue before loop starts (default: 10)",
    )
    parser.add_argument(
        "--refill-mode",
        choices=["none", "audit", "audit+gaps"],
        default="audit+gaps",
        help="How to refill queue when pending is below --min-pending (default: audit+gaps)",
    )
    parser.add_argument(
        "--doctor-preflight",
        action="store_true",
        help="Run factory doctor preflight before starting loop",
    )
    parser.add_argument(
        "--doctor-strict-hooks",
        action="store_true",
        help="Use strict hook checks during --doctor-preflight",
    )
    parser.add_argument(
        "--doctor-workspace-integrity",
        action="store_true",
        help="Probe VS Code workspace contention during --doctor-preflight",
    )
    parser.add_argument(
        "--doctor-include-examples",
        action="store_true",
        help="Include reference-game inspection during --doctor-preflight",
    )
    parser.add_argument(
        "--live-execution",
        action="store_true",
        help="Enable opt-in live adapters (Ollama/ChatDev/etc.) during this run",
    )

    args = parser.parse_args()

    # Calculate cycles
    if args.cycles > 0:
        max_cycles = args.cycles
    else:
        max_cycles = int((args.hours * 60) / args.interval)

    total_minutes = max_cycles * args.interval
    total_hours = total_minutes / 60

    print("=" * 60)
    print("NuSyQ AUTONOMOUS DEVELOPMENT LOOP")
    print("=" * 60)
    print(f"Start time:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:        ~{total_hours:.1f} hours ({total_minutes} minutes)")
    print(f"Cycles:          {max_cycles}")
    print(f"Interval:        {args.interval} minutes")
    print(f"Tasks/cycle:     {args.tasks}")
    print(f"Max tasks:       {max_cycles * args.tasks}")
    print(f"Mode:            {args.mode}")
    print(f"Live execution:  {'enabled' if args.live_execution else 'disabled'}")
    print("=" * 60)

    # Check queue status
    queue_path = Path(__file__).parent / "data" / "unified_pu_queue.json"
    normalized_count = _normalize_queue_schema(queue_path)
    if normalized_count > 0:
        print(f"Queue normalize:  {normalized_count} entry updates applied")
    stats = _queue_stats(queue_path)
    print(
        "Queue status:    "
        f"{stats['pending']} pending, {stats['completed']} completed, {stats['failed']} failed"
    )
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN] Would start autonomous loop with above config.")
        print("Remove --dry-run to actually run.")
        return 0

    if args.doctor_preflight:
        print("\nRunning factory doctor preflight...")
        doctor = _run_doctor_preflight(
            strict_hooks=args.doctor_strict_hooks,
            include_examples=args.doctor_include_examples,
            workspace_integrity=args.doctor_workspace_integrity,
        )
        print(
            "Doctor status:   "
            f"{doctor.get('status', 'unknown')} (healthy={doctor.get('healthy', False)})"
        )
        issues = doctor.get("issues", [])
        print(f"Doctor issues:   {len(issues)}")

    if args.refill_mode != "none" and stats["pending"] < args.min_pending:
        print(
            "\nQueue pending below threshold "
            f"({stats['pending']} < {args.min_pending}). Running refill: {args.refill_mode}"
        )
        if args.refill_mode in {"audit", "audit+gaps"}:
            refill_result = _refill_queue_from_audit(args.mode)
            print(
                "Audit refill:    "
                f"status={refill_result.get('status', 'unknown')}, "
                f"findings={refill_result.get('findings', 0)}, "
                f"pus_created={len(refill_result.get('pus_created', []))}"
            )
        if args.refill_mode == "audit+gaps":
            stats_after_audit = _queue_stats(queue_path)
            if stats_after_audit["pending"] < args.min_pending:
                created_from_gaps = _refill_queue_from_sector_gaps(queue_path, args.min_pending)
                print(f"Gap refill:      created={created_from_gaps}")
        stats = _queue_stats(queue_path)
        print(
            "Queue status:    "
            f"{stats['pending']} pending, {stats['completed']} completed, {stats['failed']} failed"
        )

    print("\nStarting autonomous loop...\n")

    if args.live_execution:
        os.environ["NUSYQ_LIVE_EXECUTION"] = "1"
    else:
        os.environ.pop("NUSYQ_LIVE_EXECUTION", None)

    from src.automation.autonomous_loop import AutonomousLoop

    loop = AutonomousLoop(
        interval_minutes=args.interval,
        mode=args.mode,
        max_tasks_per_cycle=args.tasks,
        max_cycles=max_cycles,
    )

    try:
        loop.start()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Shutting down gracefully...")
    except Exception as exc:
        print(f"\n\nAutonomous loop crashed: {exc}")
        traceback.print_exc()

    # Final stats
    print("\n" + "=" * 60)
    print("RUN COMPLETE")
    print("=" * 60)
    print(f"End time:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Cycles run:      {loop.cycle_count}")

    # Re-check queue
    stats = _queue_stats(queue_path)
    print(
        "Queue status:    "
        f"{stats['pending']} pending, {stats['completed']} completed, {stats['failed']} failed"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
