"""Performance analyzer utility module.

Provides tools for analyzing system performance metrics.
"""

import logging
from dataclasses import dataclass
from datetime import timezone

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - Python 3.10 compatibility
    UTC = timezone.utc  # noqa: UP017

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance metric measurement."""

    name: str
    value: float
    unit: str
    timestamp: str


class PerformanceAnalyzer:
    """Analyzes system performance metrics."""

    def __init__(self):
        """Initialize performance analyzer."""
        self.metrics: list[PerformanceMetric] = []
        logger.info("PerformanceAnalyzer initialized")

    def add_metric(self, name: str, value: float, unit: str = "ms") -> None:
        """Add a performance metric.

        Args:
            name: Metric name (e.g., 'response_time')
            value: Metric value
            unit: Measurement unit (default: ms)
        """
        from datetime import datetime

        metric = PerformanceMetric(
            name=name, value=value, unit=unit, timestamp=datetime.now(UTC).isoformat()
        )
        self.metrics.append(metric)
        logger.debug(f"Added metric: {name}={value}{unit}")

    def get_average(self, metric_name: str) -> float | None:
        """Get average value for a metric.

        Args:
            metric_name: Name of metric to average

        Returns:
            Average value or None if not found
        """
        matching = [m.value for m in self.metrics if m.name == metric_name]
        if not matching:
            return None
        return sum(matching) / len(matching)

    def get_stats(self) -> dict:
        """Get statistics for all metrics.

        Returns:
            Dictionary with aggregated statistics
        """
        stats = {}
        metric_names = {m.name for m in self.metrics}

        for name in metric_names:
            values = [m.value for m in self.metrics if m.name == name]
            stats[name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

        return stats
