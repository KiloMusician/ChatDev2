"""Optimization subsystem — performance caching utilities.

OmniTag: {
    "purpose": "optimization_subsystem",
    "tags": ["Optimization", "Cache", "Performance"],
    "category": "infrastructure",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

__all__ = [
    "CacheEntry",
    "PerformanceCache",
    "get_cache",
    "initialize_cache",
]


def __getattr__(name: str) -> object:
    if name in ("CacheEntry", "PerformanceCache", "initialize_cache", "get_cache"):
        from src.optimization.performance_cache import (CacheEntry,
                                                        PerformanceCache,
                                                        get_cache,
                                                        initialize_cache)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
