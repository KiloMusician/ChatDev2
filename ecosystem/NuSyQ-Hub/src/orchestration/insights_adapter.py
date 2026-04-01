"""Insights Adapter for MultiAI Orchestrator.

Provides a lightweight, decoupled way for orchestration layers to fetch
aggregated repository insights without hard dependency on the treasure
pipeline implementation.

Usage:
    from src.orchestration.insights_adapter import fetch_aggregated_insights
    data = fetch_aggregated_insights()

If aggregation artifacts do not exist, returns a minimal structure and suggests
running the aggregator.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable

# Dynamic imports with narrow exception handling keep resilience while
# avoiding overbroad 'except Exception' catches.
_get_single_insights: Callable[[], dict[str, Any]] | None = None
try:  # narrow import for resilience
    from src.tools.report_aggregator import get_insights as _gi

    _get_single_insights = _gi
except ImportError:
    _get_single_insights = None

_aggregate_multi_repo: Callable[..., Any] | None = None
try:  # narrow import for resilience
    from src.tools.multi_repo_aggregator import aggregate_multi_repo as _amr

    _aggregate_multi_repo = _amr
except ImportError:
    _aggregate_multi_repo = None


AGG_SINGLE_DELTA = Path("docs/Reports/aggregated_insights_delta.json")
AGG_MULTI_DELTA = Path("docs/Reports/multi_repo_aggregated_insights_delta.json")
AGG_SINGLE_HISTORY = Path("docs/Reports/aggregated_history.jsonl")
AGG_MULTI_HISTORY = Path("docs/Reports/multi_repo_aggregated_history.jsonl")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return None


def _load_history(path: Path, tail: int = 5) -> list[dict[str, Any]]:
    """Load last N JSONL records from history file."""
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        records: list[dict[str, Any]] = []
        for line in lines[-tail:]:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records
    except OSError:
        return []


def _enrich_single_data(
    data: dict[str, Any],
    include_delta: bool,
    include_history: bool,
    history_tail: int,
) -> None:
    """Enrich single-repo data with delta and history in-place."""
    if include_delta:
        single_delta = _load_json(AGG_SINGLE_DELTA)
        if single_delta:
            data["delta"] = single_delta
            data["urgency_score"] = single_delta.get("urgency_score", 0)
    if include_history:
        single_history = _load_history(AGG_SINGLE_HISTORY, tail=history_tail)
        if single_history:
            data["history"] = single_history


def _enrich_multi_data(
    include_delta: bool,
    include_history: bool,
    history_tail: int,
) -> dict[str, Any]:
    """Build and enrich multi-repo data with delta and history."""
    if _aggregate_multi_repo is None:
        return {"available": False, "reason": "multi_repo_aggregator not present"}
    multi_current: dict[str, Any] = _aggregate_multi_repo().to_dict()
    if include_delta:
        multi_delta = _load_json(AGG_MULTI_DELTA)
        if multi_delta:
            multi_current["delta"] = multi_delta
            multi_current["urgency_score"] = multi_delta.get("urgency_score", 0)
    if include_history:
        multi_history = _load_history(AGG_MULTI_HISTORY, tail=history_tail)
        if multi_history:
            multi_current["history"] = multi_history
    return multi_current


def fetch_aggregated_insights(
    include_multi: bool = True,
    include_delta: bool = True,
    include_history: bool = True,
    history_tail: int = 5,
) -> dict[str, Any]:
    """Return aggregated insights; optionally include multi-repo breakdown, delta, and history.

    Parameters
    ----------
    include_multi: bool
        If True and multi-repo aggregator is available, append multi_repo key.
    include_delta: bool
        If True, include delta JSON artifacts (with urgency scores).
    include_history: bool
        If True, include recent history records (JSONL tail).
    history_tail: int
        Number of recent history records to include (default 5).

    """
    if _get_single_insights is not None:
        data = _get_single_insights()
        data["available"] = True
    else:
        data = {
            "available": False,
            "reason": "report_aggregator not available",
            "next_step": "Run: python src/tools/report_aggregator.py --markdown --json",
        }
    _enrich_single_data(data, include_delta, include_history, history_tail)
    if include_multi:
        data["multi_repo"] = _enrich_multi_data(include_delta, include_history, history_tail)
    return data
