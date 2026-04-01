"""Context subsystem — configuration loading and event history tracking.

Provides:
- load_config, aggregate_context: config aggregation utilities
- EventType, EventSeverity, EventOutcome, EventContext: event model

OmniTag: {
    "purpose": "context_subsystem",
    "tags": ["Context", "Config", "EventTracking"],
    "category": "infrastructure",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

# Lazy re-exports are resolved via __getattr__; pylint cannot infer them statically.
# pylint: disable=import-outside-toplevel,possibly-unused-variable,undefined-all-variable

__all__ = [
    # Event model (lazy)
    "EventContext",
    "EventOutcome",
    "EventSeverity",
    "EventType",
    # Config utilities (lazy)
    "aggregate_context",
    "load_config",
]


def __getattr__(name: str) -> object:
    if name in ("load_config", "aggregate_context"):
        from src.context.context_manager import aggregate_context, load_config

        return locals()[name]
    if name in ("EventType", "EventSeverity", "EventOutcome", "EventContext"):
        from src.context.event_history_tracker import (EventContext,
                                                       EventOutcome,
                                                       EventSeverity,
                                                       EventType)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
