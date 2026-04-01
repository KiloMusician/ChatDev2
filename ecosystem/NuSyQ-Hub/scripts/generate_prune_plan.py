"""Runner script for scheduled prune plan generation.

This script reads environment variables for thresholds and invokes the
pruner to generate a dry-run plan. It is safe to run in CI and should
print a clear message when PRUNE_AUTOCOMMIT is enabled but required
tokens are not provided (useful for tests).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    # Prefer canonical implementation when available
    from src.tools.summary_pruner import generate_prune_plan
except Exception:
    # Fallback stub (no-op)
    def generate_prune_plan(
        index_path: Path,
        plan_path: Path | None = None,
        age_days: int = 0,
        size_threshold_bytes: int = 0,
        min_duplicate_group: int = 1,
    ) -> Path | None:
        return None


def _env_int(name: str, default: int) -> int:
    try:
        v = os.getenv(name)
        if v is None:
            return default
        return int(v)
    except (ValueError, TypeError):
        return default


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    index_path = root / "docs" / "Auto" / "SUMMARY_INDEX.json"
    if not index_path.exists():
        print(f"Index not found at {index_path}; generating index is recommended", file=sys.stderr)
    age_days = _env_int("PRUNE_AGE_DAYS", 90)
    size_bytes = _env_int("PRUNE_SIZE_BYTES", 100_000)
    min_dup = _env_int("PRUNE_MIN_DUP_GROUP", 2)

    plan_path: str | None = generate_prune_plan(
        index_path,
        plan_path=index_path.parent / "SUMMARY_PRUNE_PLAN.json",
        age_days=age_days,
        size_threshold_bytes=size_bytes,
        min_duplicate_group=min_dup,
    )
    # Echo autocommit intent for test assertions
    autocommit = os.getenv("PRUNE_AUTOCOMMIT", "false").lower() in ("1", "true", "yes")
    if autocommit:
        print("PRUNE_AUTOCOMMIT enabled")
        github_token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPOSITORY")
        if not github_token or not repo:
            print("PRUNE_AUTOCOMMIT enabled but GITHUB_TOKEN or GITHUB_REPOSITORY not set; skipping autocommit")

    if plan_path:
        print(f"Prune plan generated: {plan_path}")
        return 0
    print("Prune plan generation failed or no index found", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
