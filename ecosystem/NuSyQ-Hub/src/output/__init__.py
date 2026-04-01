"""Output subsystem — signal routing, metrics broadcasting, and terminal integration.

Provides:
- OutputTier, SignalSeverity, ExecutionContext, Signal: output signal model
- MetricsTerminalBroadcaster: live metrics to terminal
- Channel, emit_route: terminal routing channel abstraction

OmniTag: {
    "purpose": "output_subsystem",
    "tags": ["Output", "Signals", "Terminal", "Metrics", "Routing"],
    "category": "observability",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

__all__ = [
    # Channel routing
    "Channel",
    # Signal model
    "ExecutionContext",
    # Terminal broadcaster
    "MetricsTerminalBroadcaster",
    "OutputTier",
    "Signal",
    "SignalSeverity",
    "emit_route",
]


def __getattr__(name: str) -> object:
    if name in ("OutputTier", "SignalSeverity", "ExecutionContext", "Signal"):
        from src.output.metasynthesis_output_system import (ExecutionContext,
                                                            OutputTier, Signal,
                                                            SignalSeverity)

        return locals()[name]
    if name == "MetricsTerminalBroadcaster":
        from src.output.metrics_terminal_broadcaster import \
            MetricsTerminalBroadcaster

        return MetricsTerminalBroadcaster
    if name in ("Channel", "emit_route"):
        from src.output.terminal_router import Channel, emit_route

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
