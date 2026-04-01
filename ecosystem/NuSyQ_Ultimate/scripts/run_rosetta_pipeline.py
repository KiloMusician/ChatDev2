#!/usr/bin/env python
"""CLI runner for the RosettaStone pipeline.

Usage (from repo root):
    .venv/Scripts/python.exe scripts/run_rosetta_pipeline.py \
        --task "Fix a simple bug" \
        --type BUG_FIX \
        --complexity SIMPLE
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repo root on path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# pylint: disable=wrong-import-position
from config.agent_router import TaskComplexity, TaskType  # noqa: E402
from src.pipeline.rosetta_stone import run_pipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for pipeline execution."""
    p = argparse.ArgumentParser(description="Run RosettaStone pipeline")
    p.add_argument("--task", required=True, help="Task description")
    p.add_argument("--type", default="CODE_GENERATION", help="TaskType enum name")
    p.add_argument("--complexity", default="MODERATE", help="TaskComplexity enum name")
    return p.parse_args()


def main() -> int:
    """Execute RosettaStone pipeline with user-specified task parameters."""
    args = parse_args()

    try:
        task_type = TaskType[args.type]
    except KeyError:
        print(f"Unknown TaskType {args.type}. Options: {[e.name for e in TaskType]}")
        return 2

    try:
        complexity = TaskComplexity[args.complexity]
    except KeyError:
        print(
            "Unknown TaskComplexity "
            f"{args.complexity}. Options: {[e.name for e in TaskComplexity]}"
        )
        return 2

    result = run_pipeline(args.task, task_type=task_type, complexity=complexity)

    print("Pipeline completed. Artifacts:")
    for k, v in result.persisted_paths.items():
        print(f" - {k}: {v}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
