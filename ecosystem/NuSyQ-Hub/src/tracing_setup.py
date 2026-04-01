"""Tracing status adapter for health_cli.

Uses src.observability.tracing when available, otherwise reports stub status.
"""

from __future__ import annotations

import logging
import os
from typing import Any

try:
    from src.observability import tracing as tracing_mod
except Exception:
    tracing_mod = None

STUB_MESSAGE = "Tracing is disabled or unavailable; stub tracing_setup is active."
logger = logging.getLogger(__name__)


def tracing_status() -> dict[str, Any]:
    """Return tracing status payload and print a human-friendly note."""
    if tracing_mod is None:
        logger.info(STUB_MESSAGE)
        return {
            "configured": False,
            "implementation": "stub",
            "message": STUB_MESSAGE,
        }

    enabled = tracing_mod.tracing_enabled()
    env_enabled = os.environ.get("NUSYQ_TRACING") or os.environ.get("NUSYQ_TRACE")

    status = {
        "configured": bool(env_enabled is None or env_enabled != "0"),
        "implementation": "observability.tracing",
        "enabled": enabled,
        "exporter": os.environ.get("OTEL_TRACES_EXPORTER", "otlp"),
        "endpoint": os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318"),
    }
    logger.info("Tracing status: enabled=%s exporter=%s", enabled, status["exporter"])
    return status


def start_tracing(*_: Any, **__: Any) -> None:
    """Backward-compatible no-op for callers that expect a setup hook."""
    return None
