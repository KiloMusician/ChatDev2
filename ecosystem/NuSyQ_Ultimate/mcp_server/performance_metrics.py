"""
Performance Metrics - System Performance Tracking
=================================================

Collects and analyzes performance metrics across the NuSyQ system:
- Query latency and throughput
- Token usage and costs
- Agent performance
- Cache effectiveness
- System resource usage

Features:
- Real-time metric collection
- Aggregation and statistical analysis
- JSON export for external analysis
- Dashboard-ready data format
"""

import json
import logging
import statistics
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@dataclass
class QueryMetric:
    """Individual query performance metric"""

    timestamp: float
    model: str
    prompt_length: int
    response_length: int
    duration_seconds: float
    cached: bool
    success: bool
    retries: int
    error: Optional[str] = None


@dataclass
class AgentMetric:
    """Agent-specific performance metric"""

    agent_name: str
    task_type: str
    duration_seconds: float
    success: bool
    timestamp: float


class PerformanceMetrics:
    """
    Central performance metrics collector

    Thread-safe metrics collection with aggregation and export.
    """

    def __init__(self, export_dir: Optional[Path] = None):
        """
        Initialize metrics collector

        Args:
            export_dir: Directory for exporting metrics
                (default: Reports/metrics)
        """
        if export_dir is None:
            export_dir = Path("Reports/metrics")

        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Metric storage
        self.query_metrics: List[QueryMetric] = []
        self.agent_metrics: List[AgentMetric] = []

        # Aggregated stats
        self.start_time = time.time()
        self.total_queries = 0
        self.total_errors = 0
        self._lock = threading.Lock()

    def record_query(
        self,
        model: str,
        prompt_length: int,
        response_length: int,
        duration: float,
        cached: bool = False,
        success: bool = True,
        retries: int = 0,
        error: Optional[str] = None,
    ):
        """
        Record a query metric

        Args:
            model: Model name (e.g., 'qwen2.5-coder:7b')
            prompt_length: Input prompt length in characters
            response_length: Response length in characters
            duration: Query duration in seconds
            cached: Whether response was from cache
            success: Whether query succeeded
            retries: Number of retry attempts
            error: Error message if failed
        """
        metric = QueryMetric(
            timestamp=time.time(),
            model=model,
            prompt_length=prompt_length,
            response_length=response_length,
            duration_seconds=duration,
            cached=cached,
            success=success,
            retries=retries,
            error=error,
        )

        with self._lock:
            self.query_metrics.append(metric)
            self.total_queries += 1
            if not success:
                self.total_errors += 1

    def record_agent(self, agent_name: str, task_type: str, duration: float, success: bool):
        """
        Record an agent performance metric

        Args:
            agent_name: Name of agent
            task_type: Type of task handled
            duration: Task duration in seconds
            success: Whether task succeeded
        """
        metric = AgentMetric(
            agent_name=agent_name,
            task_type=task_type,
            duration_seconds=duration,
            success=success,
            timestamp=time.time(),
        )

        with self._lock:
            self.agent_metrics.append(metric)

    def get_query_stats(self, time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Get aggregated query statistics

        Args:
            time_window_minutes: Limit to recent N minutes (None = all time)

        Returns:
            Dictionary with aggregated query stats
        """
        # Filter by time window if specified
        with self._lock:
            query_metrics_list = list(self.query_metrics)
        if time_window_minutes is not None:
            cutoff = time.time() - (time_window_minutes * 60)
            query_metrics_list = [m for m in query_metrics_list if m.timestamp >= cutoff]

        period = (
            f"last {time_window_minutes} min" if time_window_minutes is not None else "all time"
        )

        if not query_metrics_list:
            return {
                "total_queries": 0,
                "period": period,
            }

        # Calculate aggregations
        successful = [m for m in query_metrics_list if m.success]
        failed = [m for m in query_metrics_list if not m.success]
        cached = [m for m in query_metrics_list if m.cached]

        durations = [m.duration_seconds for m in successful]
        response_lengths = [m.response_length for m in successful]

        # Per-model stats
        models = defaultdict(list)
        for m in successful:
            models[m.model].append(m.duration_seconds)

        model_stats: Dict[str, Dict[str, float]] = {}
        for model, durations_list in models.items():
            model_stats[model] = {
                "count": float(len(durations_list)),
                "avg_duration": statistics.mean(durations_list),
                "median_duration": statistics.median(durations_list),
            }

        # p95 calculation with readable branching
        p95_duration = 0.0
        if durations:
            if len(durations) >= 20:
                p95_duration = statistics.quantiles(durations, n=20)[18]
            else:
                p95_duration = max(durations)

        return {
            "period": period,
            "total_queries": len(query_metrics_list),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": (
                len(successful) / len(query_metrics_list) * 100 if query_metrics_list else 0
            ),
            "cache_hits": len(cached),
            "cache_hit_rate": (
                len(cached) / len(query_metrics_list) * 100 if query_metrics_list else 0
            ),
            "avg_duration": statistics.mean(durations) if durations else 0,
            "median_duration": (statistics.median(durations) if durations else 0),
            "p95_duration": p95_duration,
            "avg_response_length": (statistics.mean(response_lengths) if response_lengths else 0),
            "total_retries": sum(m.retries for m in query_metrics_list),
            "models": model_stats,
        }

    def get_agent_stats(self, time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Get aggregated agent performance statistics

        Args:
            time_window_minutes: Limit to recent N minutes

        Returns:
            Dictionary with agent performance stats
        """
        with self._lock:
            agent_metrics_list = list(self.agent_metrics)
        if time_window_minutes is not None:
            cutoff = time.time() - (time_window_minutes * 60)
            agent_metrics_list = [m for m in agent_metrics_list if m.timestamp >= cutoff]

        period = (
            f"last {time_window_minutes} min" if time_window_minutes is not None else "all time"
        )

        if not agent_metrics_list:
            return {
                "total_tasks": 0,
                "period": period,
            }

        # Per-agent stats
        agents: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"tasks": 0, "successes": 0, "durations": []}
        )
        for m in agent_metrics_list:
            agents[m.agent_name]["tasks"] += 1
            if m.success:
                agents[m.agent_name]["successes"] += 1
            agents[m.agent_name]["durations"].append(m.duration_seconds)

        agent_stats = {}
        for agent, data in agents.items():
            agent_stats[agent] = {
                "tasks_handled": data["tasks"],
                "success_rate": data["successes"] / data["tasks"] * 100,
                "avg_duration": statistics.mean(data["durations"]),
                "median_duration": statistics.median(data["durations"]),
            }

        return {
            "period": period,
            "total_tasks": len(agent_metrics_list),
            "agents": agent_stats,
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get current system resource usage

        Returns:
            Dictionary with CPU, memory, disk usage
        """
        # Convert values to floats to satisfy type checkers
        mem = psutil.virtual_memory()
        return {
            "cpu_percent": float(psutil.cpu_percent(interval=0.1)),
            "memory_percent": float(mem.percent),
            "memory_available_gb": float(mem.available) / (1024**3),
            "disk_percent": (float(psutil.disk_usage(Path.cwd().anchor).percent)),
            "uptime_hours": (time.time() - self.start_time) / 3600,
        }

    def get_summary(self, time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comprehensive performance summary

        Args:
            time_window_minutes: Time window for statistics

        Returns:
            Complete performance summary
        """
        period = (
            f"last {time_window_minutes} min" if time_window_minutes is not None else "all time"
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "time_window": period,
            "query_stats": self.get_query_stats(time_window_minutes),
            "agent_stats": self.get_agent_stats(time_window_minutes),
            "system_stats": self.get_system_stats(),
        }

    def export_summary(
        self, filename: Optional[str] = None, time_window_minutes: Optional[int] = None
    ) -> Path:
        """
        Export performance summary to JSON file

        Args:
            filename: Output filename (auto-generated if None)
            time_window_minutes: Time window for statistics

        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_summary_{timestamp}.json"

        filepath = self.export_dir / filename
        summary = self.get_summary(time_window_minutes)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return filepath

    def export_agent_trends(
        self, filename: Optional[str] = None, time_window_minutes: Optional[int] = None
    ) -> Path:
        """
        Export per-agent success/latency trends to JSON

        Args:
            filename: Output filename (auto-generated if None)
            time_window_minutes: Optional time window

        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_trends_{timestamp}.json"

        filepath = self.export_dir / filename
        agent_stats = self.get_agent_stats(time_window_minutes)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(agent_stats, f, indent=2)

        return filepath

    def start_periodic_export(
        self, interval_minutes: int = 10, time_window_minutes: Optional[int] = None
    ) -> threading.Event:
        """
        Start a lightweight background exporter.

        Returns a threading.Event that can be set to stop the exporter.
        """

        stop_event = threading.Event()

        def _export_loop():
            while not stop_event.wait(interval_minutes * 60):
                try:
                    self.export_summary(time_window_minutes=time_window_minutes)
                    self.export_agent_trends(time_window_minutes=time_window_minutes)
                except Exception as exc:  # pylint: disable=broad-except
                    logger.warning("Metrics export failed: %s", exc)

        thread = threading.Thread(target=_export_loop, name="metrics-exporter", daemon=True)
        thread.start()

        return stop_event

    def cleanup_old_metrics(self, keep_hours: int = 24):
        """
        Remove metrics older than specified hours

        Args:
            keep_hours: Keep metrics from last N hours
        """
        cutoff = time.time() - (keep_hours * 3600)

        with self._lock:
            self.query_metrics = [m for m in self.query_metrics if m.timestamp >= cutoff]
            self.agent_metrics = [m for m in self.agent_metrics if m.timestamp >= cutoff]


# Global metrics instance (singleton)
_global_metrics: Optional[PerformanceMetrics] = None


def get_metrics() -> PerformanceMetrics:
    """
    Get global metrics instance

    Returns:
        Global PerformanceMetrics instance
    """
    global _global_metrics  # pylint: disable=global-statement

    if _global_metrics is None:
        _global_metrics = PerformanceMetrics()

    return _global_metrics


if __name__ == "__main__":
    # Demo usage
    print("=" * 60)
    print("Performance Metrics - Demo")
    print("=" * 60)

    pm = PerformanceMetrics()

    # Simulate some queries
    for i in range(10):
        pm.record_query(
            model="qwen2.5-coder:7b",
            prompt_length=100 + i * 10,
            response_length=500 + i * 50,
            duration=1.5 + i * 0.1,
            cached=(i % 3 == 0),
            success=True,
        )

    # Simulate some agent tasks
    for i in range(5):
        pm.record_agent(
            agent_name="qwen2.5-coder:14b",
            task_type="code_generation",
            duration=30.0 + i * 5,
            success=True,
        )

    # Get summary
    summary_data = pm.get_summary()

    print("\nQuery Statistics:")
    print(f"Total: {summary_data['query_stats']['total_queries']}")
    print(f"Success Rate: {summary_data['query_stats']['success_rate']:.1f}%")
    print(f"Cache Hit Rate: {summary_data['query_stats']['cache_hit_rate']:.1f}%")
    print(f"Avg Duration: {summary_data['query_stats']['avg_duration']:.2f}s")

    print("\nAgent Statistics:")
    print(f"Total Tasks: {summary_data['agent_stats']['total_tasks']}")

    print("\nSystem Resources:")
    print(f"CPU: {summary_data['system_stats']['cpu_percent']:.1f}%")
    print(f"Memory: {summary_data['system_stats']['memory_percent']:.1f}%")

    # Export
    path = pm.export_summary()
    print(f"\nExported to: {path}")
