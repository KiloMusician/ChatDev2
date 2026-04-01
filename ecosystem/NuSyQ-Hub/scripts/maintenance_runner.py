#!/usr/bin/env python3
"""Maintenance runner for common repo tasks: index, generate prune plan, preview, archive, and run tests.

This central runner aggregates several existing scripts and library functions so a maintainer
can run a single command to perform common repository maintenance tasks. It is intentionally
conservative: archival is opt-in and requires explicit --archive with --yes to proceed.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tools.summary_indexer import save_summary_index
from src.tools.summary_pruner import generate_prune_plan
from src.tools.summary_retrieval import build_engine


def _run_pytest(args: list[str] | None = None) -> int:
    cmd = [sys.executable, "-m", "pytest"] + (args or [])
    proc = subprocess.run(cmd)
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Maintenance runner: index, prune plan, preview, archive, tests")
    parser.add_argument("--index", action="store_true", help="(Re)build the retrieval engine/index")
    parser.add_argument("--generate-plan", action="store_true", help="Generate prune plan JSON")
    parser.add_argument("--preview", action="store_true", help="List prune candidates (default if no flags)")
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Move prune candidates to archive; requires --yes to confirm",
    )
    parser.add_argument(
        "--archive-dir",
        type=str,
        default="docs/Archive/Pruned",
        help="Archive destination directory",
    )
    parser.add_argument("--tests", action="store_true", help="Run pytest after operations")
    parser.add_argument(
        "--scan-src",
        action="store_true",
        help="Scan for stray src directories across repos (fails on unexpected)",
    )
    parser.add_argument("--yes", action="store_true", help="Auto-approve archival (dangerous)")
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run index, generate plan, preview (no archive), then tests",
    )

    args = parser.parse_args(argv)
    root = ROOT
    index_path = root / "docs" / "Auto" / "SUMMARY_INDEX.json"
    plan_path = index_path.parent / "SUMMARY_PRUNE_PLAN.json"

    # Default behavior: preview plan
    if not any(
        [
            args.index,
            args.generate_plan,
            args.preview,
            args.archive,
            args.tests,
            args.run_all,
            args.scan_src,
        ]
    ):
        args.preview = True

    if args.run_all:
        args.index = True
        args.generate_plan = True
        args.preview = True
        args.scan_src = True
        args.archive = False
        args.tests = True

    if args.index:
        print("[maintenance] Rebuilding summary index")
        index_file = save_summary_index(root)
        print(f"[maintenance] Summary index rebuilt: {index_file}")
        print("[maintenance] Building retrieval engine (index)")
        engine = build_engine(root)
        if engine:
            print("[maintenance] Retrieval engine built successfully.")
        else:
            print("[maintenance] Retrieval engine build returned None (no index or failed).")

    if args.generate_plan:
        if not args.index:
            print("[maintenance] Refreshing summary index before plan generation")
            index_file = save_summary_index(root)
            print(f"[maintenance] Summary index refreshed: {index_file}")
        print("[maintenance] Generating prune plan...")
        try:
            age_days = int(os.getenv("PRUNE_AGE_DAYS", "90") or 90)
        except ValueError:
            age_days = 90
        try:
            size_bytes = int(os.getenv("PRUNE_SIZE_BYTES", "100000") or 100000)
        except ValueError:
            size_bytes = 100000
        try:
            min_dup_group = int(os.getenv("PRUNE_MIN_DUP_GROUP", "2") or 2)
        except ValueError:
            min_dup_group = 2
        plan = generate_prune_plan(
            index_path,
            plan_path=plan_path,
            age_days=max(1, age_days),
            size_threshold_bytes=max(1, size_bytes),
            min_duplicate_group=max(2, min_dup_group),
        )
        print(
            f"[maintenance] Thresholds: age_days={max(1, age_days)} "
            f"size_bytes={max(1, size_bytes)} min_duplicate_group={max(2, min_dup_group)}"
        )
        if plan:
            print(f"[maintenance] Prune plan generated: {plan}")
        else:
            print("[maintenance] No plan generated (index may be missing).", file=sys.stderr)

    if args.preview:
        # Delegate to preview script for listing; do not import to prevent side effects
        cmd = [
            sys.executable,
            str(root / "scripts" / "preview_prune_plan.py"),
            "--plan-path",
            str(plan_path),
            "--list",
        ]
        print("[maintenance] Previewing prune plan (list)...")
        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            print("[maintenance] Preview failed or no plan available", file=sys.stderr)

    if args.scan_src:
        cmd = [sys.executable, str(root / "scripts" / "check_src_dirs.py"), "--fail-on-unexpected"]
        print("[maintenance] Scanning for stray src directories...")
        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            print("[maintenance] Unexpected src directories detected", file=sys.stderr)
            return proc.returncode

    if args.archive:
        if not args.yes:
            print("[maintenance] Archival requires --yes confirmation. Skipping.")
        else:
            cmd = [
                sys.executable,
                str(root / "scripts" / "preview_prune_plan.py"),
                "--plan-path",
                str(plan_path),
                "--approve",
                "--archive-dir",
                args.archive_dir,
                "--yes",
            ]
            print(f"[maintenance] Archiving plan candidates to {args.archive_dir} (this will move files)")
            proc = subprocess.run(cmd)
            if proc.returncode == 0:
                print("[maintenance] Archival complete.")
            else:
                print("[maintenance] Archival failed or aborted", file=sys.stderr)

    if args.tests:
        print("[maintenance] Running pytest (this may take a while)...")
        rc = _run_pytest(["-q", "-k", "not integration and not llm_testing"])  # conservative short-run
        print(f"[maintenance] pytest exit code: {rc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
