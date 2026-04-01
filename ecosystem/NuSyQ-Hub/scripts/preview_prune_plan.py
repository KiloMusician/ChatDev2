#!/usr/bin/env python3
"""Preview or execute prune plan archival in a safe manner.

Usage:
  --plan-path PATH
  --list (default) : lists candidates
  --approve : actually move files to archive (dangerous)
  --archive-dir : directory to archive
  --yes : auto-approve without prompt

This script is intended for maintainers to preview and optionally approve archival.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tools.summary_pruner import archive_pruned_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview or archive prune plan")
    parser.add_argument("--plan-path", type=str, default="docs/Auto/SUMMARY_PRUNE_PLAN.json")
    parser.add_argument("--list", action="store_true", default=True, help="List prune candidates (default)")
    parser.add_argument("--approve", action="store_true", help="Approve archival action")
    parser.add_argument("--archive-dir", type=str, default="docs/Archive/Pruned")
    parser.add_argument("--yes", action="store_true", help="Auto-approve without prompt")

    args = parser.parse_args(argv)
    plan_path = Path(args.plan_path)
    if not plan_path.exists():
        print(f"Plan not found: {plan_path}")
        return 1

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    candidates = plan.get("candidates", [])
    print(f"Prune plan generated at: {plan.get('generated_at')}")
    print(f"Candidates: {len(candidates)}")

    if args.list or not args.approve:
        for idx, c in enumerate(candidates[:50], start=1):
            print(
                f"{idx}. {c.get('path')} [{c.get('category')}] {c.get('reason')} size={c.get('size_bytes')} modified={c.get('modified')}"
            )

    if args.approve:
        if not args.yes:
            confirm = input("Confirm archival of listed files? [y/N] ")
            if confirm.lower() not in ("y", "yes"):
                print("Aborting archival")
                return 1

        archived = archive_pruned_files(plan_path, Path(args.archive_dir))
        print(f"Archived {len(archived)} files to {args.archive_dir}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
