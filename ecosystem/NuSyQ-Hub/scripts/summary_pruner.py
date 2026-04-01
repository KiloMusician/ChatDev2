#!/usr/bin/env python3
'''"""CLI wrapper around `src.tools.summary_pruner` for managing legacy docs."""'''

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.tools.summary_pruner import (
    DEFAULT_PLAN_PATH,
    archive_pruned_files,
    generate_prune_plan,
)


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summary pruning utilities for docs and reports.")
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Generate a prune plan (defaults to docs/Auto/SUMMARY_PRUNE_PLAN.json).",
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Move files referenced in the plan into the archive folder.",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("docs/Auto/SUMMARY_INDEX.json"),
        help="Path to the summary index used for candidates.",
    )
    parser.add_argument(
        "--plan-path",
        type=Path,
        default=DEFAULT_PLAN_PATH,
        help="Path where the plan JSON is (or will be) written.",
    )
    parser.add_argument(
        "--age-days",
        type=int,
        default=365,
        help="Age threshold in days for old summaries.",
    )
    parser.add_argument(
        "--size-threshold-bytes",
        type=int,
        default=100_000,
        help="Size threshold (bytes) for large summary files.",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=Path("docs/Auto/pruned"),
        help="Destination directory for archived summaries.",
    )
    parser.add_argument(
        "--min-duplicate-group",
        type=int,
        default=2,
        help="Minimum duplicate group size to trigger pruning.",
    )
    parsed = parser.parse_args(args=args)
    if not (parsed.plan or parsed.archive):
        parser.error("Specify at least one of --plan or --archive.")
    return parsed


def main() -> int:
    args = _parse_args()
    plan_path = args.plan_path
    if args.plan:
        plan = generate_prune_plan(
            index_path=args.index,
            plan_path=plan_path,
            age_days=args.age_days,
            size_threshold_bytes=args.size_threshold_bytes,
            min_duplicate_group=args.min_duplicate_group,
        )
        if plan is None:
            print(f"⚠️  Unable to build plan: {args.index} missing or invalid.")
        else:
            print(f"✅ Plan written to {plan}")
    if args.archive:
        if not plan_path.exists():
            print(f"⚠️  Plan file {plan_path} missing; run --plan first.")
            return 1
        archived = archive_pruned_files(plan_path, args.archive_dir)
        print(f"📦 Archived {len(archived)} files to {args.archive_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
