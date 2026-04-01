"""Central spine bootstrap helpers used across NuSyQ-Hub entry points."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


def _load_match_terms(repo_root: Path) -> dict[str, list[str]]:
    cfg = repo_root / "config" / "service_match_terms.json"
    if not cfg.exists():
        return {}
    try:
        data = json.loads(cfg.read_text())
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if isinstance(v, list)}
    except Exception:
        return {}
    return {}


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpineHealth:
    """Summary of the spine bootstrap state."""

    repo_root: Path
    timestamp: str
    status: str
    current_state_excerpt: tuple[str, ...]
    lifecycle_entries: tuple[str, ...]
    signals: dict[str, int]

    def describe(self) -> str:
        """Human-friendly description of the spine status."""
        summary = (
            self.current_state_excerpt[0] if self.current_state_excerpt else "current-state missing"
        )
        summary = summary.replace("\n", " ").strip()
        if len(summary) > 180:
            summary = f"{summary[:177]}..."
        entries = self.lifecycle_entries[:2] or ()
        if entries:
            compact_entries = []
            for entry in entries:
                text = str(entry).replace("\n", " ").strip()
                if len(text) > 80:
                    text = f"{text[:77]}..."
                compact_entries.append(text)
            entries_summary = " | ".join(compact_entries)
        else:
            entries_summary = "no lifecycle entries"
        return f"{summary} · {entries_summary}"


def _read_lines(path: Path, limit: int) -> tuple[str, ...]:
    if not path.exists():
        return ()
    try:
        text = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return ()

    cleaned = [line.strip() for line in text if line.strip()]
    return tuple(cleaned[:limit])


def _sample_lifecycle_entries(path: Path, limit: int) -> tuple[str, ...]:
    if not path.exists():
        return ()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ()

    entries: list[object] = []
    if isinstance(data, dict):
        for key in ("entries", "items", "catalog", "tasks", "steps"):
            candidate = data.get(key)
            if isinstance(candidate, list):
                entries = candidate
                break
        else:
            entries = [data]
    elif isinstance(data, list):
        entries = data
    else:
        entries = [data]

    normalized: list[str] = []
    for entry in entries:
        if isinstance(entry, dict):
            label = entry.get("title") or entry.get("name") or entry.get("summary")
            if label:
                normalized.append(str(label))
            else:
                normalized.append(json.dumps(entry, default=str))
        else:
            normalized.append(str(entry))
        if len(normalized) >= limit:
            break

    return tuple(normalized[:limit])


def _determine_status(current_excerpt: tuple[str, ...], lifecycle_entries: tuple[str, ...]) -> str:
    if current_excerpt and lifecycle_entries:
        return "GREEN"
    if current_excerpt or lifecycle_entries:
        return "YELLOW"
    return "RED"


def _build_spine_health(repo_root: str) -> SpineHealth:
    root = Path(repo_root)
    state_dir = root / "state" / "reports"
    current_state = state_dir / "current_state.md"
    lifecycle = state_dir / "lifecycle_catalog_latest.json"
    match_terms = _load_match_terms(root)

    excerpt = _read_lines(current_state, limit=4)
    lifecycle_entries = _sample_lifecycle_entries(lifecycle, limit=3)

    signals = {
        "current_state_lines": len(excerpt),
        "lifecycle_entries": len(lifecycle_entries),
        "match_terms_loaded": int(bool(match_terms)),
        "match_term_services": len(match_terms),
    }

    status = _determine_status(excerpt, lifecycle_entries)
    timestamp = datetime.utcnow().isoformat()

    return SpineHealth(
        repo_root=root,
        timestamp=timestamp,
        status=status,
        current_state_excerpt=excerpt,
        lifecycle_entries=lifecycle_entries,
        signals=signals,
    )


@lru_cache(maxsize=4)
def _cached_spine_health(repo_root: str) -> SpineHealth:
    return _build_spine_health(repo_root)


def initialize_spine(repo_root: Path | None = None, refresh: bool = False) -> SpineHealth:
    """Ensure the spine snapshot is captured and logged."""
    root = repo_root or Path(__file__).resolve().parents[2]
    root_str = str(root)

    if refresh:
        _cached_spine_health.cache_clear()

    health = _cached_spine_health(root_str)
    logger.info(
        "Spine quick health | status=%s | signals=%s | desc=%s",
        health.status,
        health.signals,
        health.describe(),
    )
    return health


def _health_snapshot(health: SpineHealth) -> dict[str, Any]:
    """Serialize the SpineHealth data into a JSON-friendly dict."""
    return {
        "repo_root": str(health.repo_root),
        "timestamp": health.timestamp,
        "status": health.status,
        "current_state_excerpt": list(health.current_state_excerpt),
        "lifecycle_entries": list(health.lifecycle_entries),
        "signals": health.signals,
    }


def export_spine_health(
    repo_root: Path | None = None,
    refresh: bool = False,
    output_dir: Path | None = None,
) -> Path:
    """Persist the latest spine health snapshot to disk."""
    repo = repo_root or Path(__file__).resolve().parents[2]
    health = initialize_spine(repo_root=repo, refresh=refresh)
    snapshot = _health_snapshot(health)
    dest_dir = output_dir or (health.repo_root / "state" / "reports")
    dest_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = dest_dir / "spine_health_snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    logger.debug("Spine snapshot exported to %s", snapshot_path)
    return snapshot_path
