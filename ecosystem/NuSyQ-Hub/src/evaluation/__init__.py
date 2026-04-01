"""Evaluation subsystem — performance benchmarking tools.

OmniTag: {
    "purpose": "evaluation_subsystem",
    "tags": ["Evaluation", "Benchmark", "Performance"],
    "category": "tooling",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

__all__ = [
    "BenchmarkResult",
    "PerformanceBenchmark",
    "run_performance_benchmark",
]


def __getattr__(name: str) -> object:
    if name in ("BenchmarkResult", "PerformanceBenchmark", "run_performance_benchmark"):
        from src.evaluation.performance_benchmark import (
            BenchmarkResult, PerformanceBenchmark, run_performance_benchmark)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
