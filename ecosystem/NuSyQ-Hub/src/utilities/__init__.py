"""Utilities subsystem — performance analysis and system profiling.

Provides performance metrics collection and analysis tools for profiling
NuSyQ subsystem operations: latency tracking, throughput measurement,
and bottleneck identification.

OmniTag: {
    "purpose": "utilities_subsystem",
    "tags": ["Utilities", "Performance", "Profiling", "Metrics"],
    "category": "observability",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = ["PerformanceAnalyzer", "PerformanceMetric"]


def __getattr__(name: str):
    if name in ("PerformanceMetric", "PerformanceAnalyzer"):
        from src.utilities.performance_analyzer import (PerformanceAnalyzer,
                                                        PerformanceMetric)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
