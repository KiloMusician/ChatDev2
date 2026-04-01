"""Compatibility wrapper for legacy imports.

Prefer src.observability.tracing for new code.
"""

from __future__ import annotations

from src.observability.tracing import (bind_context, bind_correlation_id,
                                       clear_context, clear_correlation_ids,
                                       current_trace_ids, flush_tracing,
                                       get_all_context,
                                       get_all_correlation_ids,
                                       get_context_value, get_correlation_id,
                                       get_tracer, init_tracing,
                                       shutdown_tracing, start_action_span,
                                       start_span, tracing_enabled)

__all__ = [
    "bind_context",
    "bind_correlation_id",
    "clear_context",
    "clear_correlation_ids",
    "current_trace_ids",
    "flush_tracing",
    "get_all_context",
    "get_all_correlation_ids",
    "get_context_value",
    "get_correlation_id",
    "get_tracer",
    "init_tracing",
    "shutdown_tracing",
    "start_action_span",
    "start_span",
    "tracing_enabled",
]
