"""Observability subsystem - system awareness and introspection."""

from __future__ import annotations

import contextlib
import logging
import os

logger = logging.getLogger(__name__)

# Attempt a safe, best-effort tracing initialization when the package is imported.
# This should not raise if OpenTelemetry or other tracing dependencies are missing.

try:
    from . import tracing as _tracing

    _SERVICE_NAME = (
        os.environ.get("OTEL_SERVICE_NAME") or os.environ.get("NUSYQ_SERVICE_NAME") or "nusyq-hub"
    )
    with contextlib.suppress(Exception):  # Non-fatal; tracing is best-effort
        _tracing.init_tracing(service_name=_SERVICE_NAME)
except Exception:
    # Best-effort only; swallow any import-time errors.
    logger.debug("Suppressed Exception", exc_info=True)

from .snapshot_delta import (SnapshotDelta, SnapshotDeltaTracker,
                             SnapshotMetrics)

__all__ = [
    "SnapshotDelta",
    "SnapshotDeltaTracker",
    "SnapshotMetrics",
]
