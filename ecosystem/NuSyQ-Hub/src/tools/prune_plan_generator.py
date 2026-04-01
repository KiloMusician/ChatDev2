from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def generate_prune_plan_with_index(
    *, age_days: int = 365, size_threshold_bytes: int = 200_000, min_duplicate_group: int = 2
) -> Path | None:
    """Minimal prune plan generator used as a safe placeholder.

    This implementation is intentionally conservative: it doesn't delete or
    examine user files aggressively. It writes a JSON prune plan containing an
    empty candidates list (safe default) to ``<repo_root>/state/prune_plans/``
    and returns the file path. Real implementations should replace this with
    duplicate detection, hashing, and safe candidate selection.
    """
    try:
        repo_root = Path(__file__).parent.parent.parent
        out_dir = repo_root / "state" / "prune_plans"
        out_dir.mkdir(parents=True, exist_ok=True)
        plan = {
            "generated_at": datetime.now().isoformat(),
            "age_days": age_days,
            "size_threshold_bytes": size_threshold_bytes,
            "min_duplicate_group": min_duplicate_group,
            "candidates": [],
            "note": "placeholder prune plan - no candidates selected; replace with real generator",
        }
        filename = f"prune_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = out_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)
        return path
    except Exception:
        return None
