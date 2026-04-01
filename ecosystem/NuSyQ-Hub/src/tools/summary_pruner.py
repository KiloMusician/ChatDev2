#!/usr/bin/env python3
"""Summary Pruner: generate prune recommendations for summary/report/analysis docs.

Heuristics included (configurable):
- Age: files older than a threshold (days)
- Size: files larger than a size threshold (bytes)
- Duplicate title: files with identical titles

Generates a dry-run JSON plan in `docs/Auto/SUMMARY_PRUNE_PLAN.json` by default.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_PLAN_PATH = Path("docs/Auto/SUMMARY_PRUNE_PLAN.json")


@dataclass
class PruneCandidate:
    path: str
    title: str | None
    category: str
    reason: str
    score: float
    size_bytes: int
    modified: str


def load_index(index_path: Path) -> dict[str, Any] | None:
    try:
        if not index_path.exists():
            return None
        loaded_data: dict[str, Any] = json.loads(index_path.read_text(encoding="utf-8"))
        return loaded_data
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def compute_prune_candidates(
    index: dict[str, Any],
    age_days: int = 90,
    size_threshold_bytes: int = 100_000,
    min_duplicate_group: int = 2,
) -> list[PruneCandidate]:
    files = index.get("files", [])
    candidates: list[PruneCandidate] = []
    now = datetime.now()

    # Map for duplicates by content hash
    hash_map: dict[str, list[dict[str, Any]]] = {}
    for meta in files:
        path = Path(meta.get("path", ""))
        content_hash = None
        try:
            if path.exists():
                # read file in binary to compute hash
                with path.open("rb") as fh:
                    h = hashlib.sha256()
                    for chunk in iter(lambda: fh.read(8192), b""):
                        h.update(chunk)
                content_hash = h.hexdigest()
        except (FileNotFoundError, OSError, PermissionError):
            content_hash = None
        if content_hash:
            hash_map.setdefault(content_hash, []).append(meta)

    # Age & size candidates
    for meta in files:
        mod = meta.get("modified")
        try:
            mod_dt = datetime.fromisoformat(mod) if mod else None
        except (ValueError, TypeError):
            mod_dt = None

        # Age
        if mod_dt and (now - mod_dt) > timedelta(days=age_days):
            candidates.append(
                PruneCandidate(
                    path=meta.get("path", ""),
                    title=meta.get("title"),
                    category=meta.get("category", "unknown"),
                    reason=f"age>{age_days}d",
                    score=1.0,
                    size_bytes=meta.get("size_bytes", 0),
                    modified=meta.get("modified", ""),
                ),
            )
            continue

        # Size
        if meta.get("size_bytes", 0) >= size_threshold_bytes:
            candidates.append(
                PruneCandidate(
                    path=meta.get("path", ""),
                    title=meta.get("title"),
                    category=meta.get("category", "unknown"),
                    reason=f"size>={size_threshold_bytes}",
                    score=0.9,
                    size_bytes=meta.get("size_bytes", 0),
                    modified=meta.get("modified", ""),
                ),
            )

    # Duplicate content groups by hash
    for content_hash, group in hash_map.items():
        if len(group) >= min_duplicate_group:
            # Mark all but the newest as candidates
            group_sorted = sorted(
                group,
                key=lambda m: m.get("modified") or "",
                reverse=True,
            )
            # Keep the newest, prune the rest
            for meta in group_sorted[1:]:
                candidates.append(
                    PruneCandidate(
                        path=meta.get("path", ""),
                        title=meta.get("title"),
                        category=meta.get("category", "unknown"),
                        reason=f"duplicate_content:{content_hash}",
                        score=0.8,
                        size_bytes=meta.get("size_bytes", 0),
                        modified=meta.get("modified", ""),
                    ),
                )

    # dedupe candidates by path
    unique: dict[str, PruneCandidate] = {}
    for c in candidates:
        if c.path and c.path not in unique:
            unique[c.path] = c
        else:
            # keep highest score
            existing = unique.get(c.path)
            if existing and c.score > existing.score:
                unique[c.path] = c

    # rank and return sorted by (score desc, size desc, modified asc)
    result = list(unique.values())
    result.sort(key=lambda x: (-x.score, -x.size_bytes, x.modified or ""))
    return result


def generate_prune_plan(
    index_path: Path,
    plan_path: Path = DEFAULT_PLAN_PATH,
    age_days: int = 90,
    size_threshold_bytes: int = 100_000,
    min_duplicate_group: int = 2,
) -> Path | None:
    index = load_index(index_path)
    if index is None:
        return None
    candidates = compute_prune_candidates(
        index,
        age_days=age_days,
        size_threshold_bytes=size_threshold_bytes,
        min_duplicate_group=min_duplicate_group,
    )

    # Build plan JSON
    plan = {
        "generated_at": datetime.now().isoformat(),
        "index_path": str(index_path),
        "candidate_count": len(candidates),
        "candidates": [c.__dict__ for c in candidates],
        "heuristics": {
            "age_days": age_days,
            "size_threshold_bytes": size_threshold_bytes,
            "min_duplicate_group": min_duplicate_group,
        },
    }
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan_path


def archive_pruned_files(plan_path: Path, archive_dir: Path) -> list[Path]:
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

    archived: list[Path] = []
    workspace_root = plan_path.resolve().parents[2]
    archive_dir.mkdir(parents=True, exist_ok=True)
    for c in plan.get("candidates", []):
        src = _normalize_candidate_path(str(c.get("path", "")), workspace_root)
        if not src.exists():
            continue
        dst = archive_dir / src.name
        # Ensure unique naming
        if dst.exists():
            dst = archive_dir / f"{src.stem}_{int(datetime.now().timestamp())}{src.suffix}"
        try:
            shutil.move(str(src), str(dst))
            archived.append(dst)
        except (OSError, PermissionError, shutil.Error):
            continue
    return archived


def _normalize_candidate_path(raw_path: str, workspace_root: Path) -> Path:
    """Resolve candidate path across Windows/WSL/relative formats."""
    cleaned = (raw_path or "").strip()
    if not cleaned:
        return Path(cleaned)

    candidate = Path(cleaned)
    if candidate.exists():
        return candidate

    # Windows drive path (e.g. C:\repo\file.md) when running in WSL.
    drive_match = re.match(r"^([A-Za-z]):[\\/](.*)$", cleaned)
    if drive_match:
        drive = drive_match.group(1).lower()
        tail = drive_match.group(2).replace("\\", "/")
        wsl_path = Path("/mnt") / drive / tail
        if wsl_path.exists():
            return wsl_path

    # Normalize absolute-ish path strings copied from another root.
    normalized = cleaned.replace("\\", "/")
    hub_marker = "/NuSyQ-Hub/"
    if hub_marker in normalized:
        rel = normalized.split(hub_marker, 1)[1]
        workspace_guess = workspace_root / rel
        if workspace_guess.exists():
            return workspace_guess

    # Fallback to workspace-relative candidate for relative plan entries.
    workspace_relative = workspace_root / cleaned
    if workspace_relative.exists():
        return workspace_relative

    # Last resort: keep original.
    return candidate


if __name__ == "__main__":  # pragma: no cover
    repo_root = Path(__file__).resolve().parents[2]
    index_path = repo_root / "docs" / "Auto" / "SUMMARY_INDEX.json"
    plan_path = generate_prune_plan(index_path)
    if plan_path:
        pass
    else:
        pass
