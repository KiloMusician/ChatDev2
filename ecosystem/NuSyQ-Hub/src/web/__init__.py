"""Web subsystem — dashboard API and system status monitoring.

OmniTag: {
    "purpose": "web_subsystem",
    "tags": ["Web", "Dashboard", "API", "Metrics"],
    "category": "observability",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

__all__ = [
    "CycleMetrics",
    "DashboardAPI",
    "DashboardMetricsCollector",
    "SystemStatus",
]


def __getattr__(name: str) -> object:
    if name in ("DashboardAPI", "CycleMetrics", "SystemStatus", "DashboardMetricsCollector"):
        from src.web.dashboard_api import (CycleMetrics, DashboardAPI,
                                           DashboardMetricsCollector,
                                           SystemStatus)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
