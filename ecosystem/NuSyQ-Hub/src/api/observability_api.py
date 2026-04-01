"""Observability API endpoints for tracing/log status."""

import logging
from typing import Any

from fastapi import APIRouter

try:
    from src.observability import tracing
except ImportError:
    tracing = None

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/observability/tracing_status")
def tracing_status() -> dict[str, Any]:
    """Report tracing status, exporter, and recent trace IDs."""
    if not tracing or not getattr(tracing, "tracing_enabled", None):
        return {"enabled": False, "error": "Tracing not available"}
    enabled = tracing.tracing_enabled()
    trace_id, span_id = tracing.current_trace_ids() if enabled else ("n/a", "n/a")
    exporter = None
    try:
        exporter = getattr(tracing, "_PROVIDER", None)
        if exporter and hasattr(exporter, "__class__"):
            exporter = exporter.__class__.__name__
    except Exception:
        exporter = None
    return {
        "enabled": enabled,
        "trace_id": trace_id,
        "span_id": span_id,
        "exporter": exporter,
    }
