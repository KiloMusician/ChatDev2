"""Orchestration Metrics Dashboard Backend.

FastAPI service for orchestration performance metrics visualization.
Serves metrics from JSON files and quest log with filtering and aggregation.

OmniTag: [metrics, dashboard, fastapi, observability, performance, charts]
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Data models
class MetricEntry(BaseModel):
    timestamp: str
    agent: str
    task_type: str
    latency: float
    tokens: int
    success: bool


class PerformanceMetrics(BaseModel):
    total_tasks: int
    avg_latency: float
    p95_latency: float
    p99_latency: float
    success_rate: float
    avg_tokens: int
    total_tokens: int


class AgentStats(BaseModel):
    agent: str
    total_tasks: int
    success_rate: float
    avg_latency: float
    avg_tokens: int


class TaskTypeStats(BaseModel):
    task_type: str
    total_tasks: int
    success_rate: float
    avg_latency: float
    avg_tokens: int


class CacheStats(BaseModel):
    hit_rate: float
    total_hits: int
    total_misses: int
    entries_cached: int


# Initialize FastAPI app
app = FastAPI(
    title="NuSyQ Orchestration Metrics Dashboard API",
    description="Real-time performance metrics and observability for AI orchestration system",
    version="1.0.0",
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path configuration
REPO_ROOT = Path(__file__).parent.parent.parent
METRICS_FILE = REPO_ROOT / "state" / "reports" / "orchestration_metrics.json"
CACHE_FILE = REPO_ROOT / "state" / "cache" / "response_cache.jsonl"
QUEST_LOG = REPO_ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"


class MetricsStore:
    """Store and manage orchestration metrics."""

    def __init__(self):
        """Initialize MetricsStore."""
        self.metrics: list[dict[str, Any]] = []
        self.load_metrics()

    def load_metrics(self):
        """Load metrics from JSON file and quest log."""
        # Try to load from metrics JSON file
        if METRICS_FILE.exists():
            try:
                with open(METRICS_FILE) as f:
                    data = json.load(f)
                    self.metrics = data.get("metrics", [])
                    logger.info(f"Loaded {len(self.metrics)} metric entries from metrics file")
            except Exception as e:
                logger.warning(f"Failed to load metrics file: {e}")

        # Also load from quest log if not already loaded
        if not self.metrics and QUEST_LOG.exists():
            self._load_from_quest_log()

    def _load_from_quest_log(self):
        """Parse orchestration events from quest log."""
        try:
            with open(QUEST_LOG) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("event_type") in [
                            "orchestration_task",
                            "async_orchestration_test",
                        ]:
                            metric = {
                                "timestamp": entry.get("timestamp", datetime.now().isoformat()),
                                "agent": entry.get("agent", "unknown"),
                                "task_type": entry.get("task_type", "general"),
                                "latency": float(entry.get("latency", 0)),
                                "tokens": int(entry.get("tokens", 0)),
                                "success": entry.get("success", True),
                            }
                            self.metrics.append(metric)
                    except (json.JSONDecodeError, ValueError):
                        continue
            logger.info(f"Loaded {len(self.metrics)} orchestration events from quest log")
        except Exception as e:
            logger.warning(f"Failed to load quest log: {e}")

    def get_metrics(
        self, agent: str | None = None, task_type: str | None = None, hours: int = 24
    ) -> list[dict[str, Any]]:
        """Get filtered metrics."""
        cutoff = datetime.now() - timedelta(hours=hours)

        filtered = []
        for metric in self.metrics:
            try:
                metric_time = datetime.fromisoformat(metric.get("timestamp", ""))
                if metric_time < cutoff:
                    continue
            except (ValueError, TypeError):
                logger.debug("Suppressed TypeError/ValueError", exc_info=True)

            if agent and metric.get("agent") != agent:
                continue
            if task_type and metric.get("task_type") != task_type:
                continue

            filtered.append(metric)

        return filtered

    def calculate_stats(self, metrics: list[dict[str, Any]]) -> PerformanceMetrics:
        """Calculate performance statistics."""
        if not metrics:
            return PerformanceMetrics(
                total_tasks=0,
                avg_latency=0,
                p95_latency=0,
                p99_latency=0,
                success_rate=0,
                avg_tokens=0,
                total_tokens=0,
            )

        latencies = sorted([m.get("latency", 0) for m in metrics])
        successes = sum(1 for m in metrics if m.get("success", True))
        total_tokens = sum(m.get("tokens", 0) for m in metrics)

        return PerformanceMetrics(
            total_tasks=len(metrics),
            avg_latency=sum(latencies) / len(latencies) if latencies else 0,
            p95_latency=(
                latencies[int(len(latencies) * 0.95)]
                if len(latencies) > 20
                else max(latencies or [0])
            ),
            p99_latency=(
                latencies[int(len(latencies) * 0.99)]
                if len(latencies) > 100
                else max(latencies or [0])
            ),
            success_rate=successes / len(metrics) if metrics else 0,
            avg_tokens=int(total_tokens / len(metrics)) if metrics else 0,
            total_tokens=int(total_tokens),
        )

    def get_agent_stats(self, metrics: list[dict[str, Any]]) -> list[AgentStats]:
        """Calculate per-agent statistics."""
        agent_metrics: dict[str, list] = {}

        for metric in metrics:
            agent = metric.get("agent", "unknown")
            if agent not in agent_metrics:
                agent_metrics[agent] = []
            agent_metrics[agent].append(metric)

        stats = []
        for agent, agent_data in agent_metrics.items():
            successes = sum(1 for m in agent_data if m.get("success", True))
            total_tokens = sum(m.get("tokens", 0) for m in agent_data)
            latencies = [m.get("latency", 0) for m in agent_data]

            stats.append(
                AgentStats(
                    agent=agent,
                    total_tasks=len(agent_data),
                    success_rate=successes / len(agent_data) if agent_data else 0,
                    avg_latency=sum(latencies) / len(latencies) if latencies else 0,
                    avg_tokens=int(total_tokens / len(agent_data)) if agent_data else 0,
                )
            )

        return sorted(stats, key=lambda x: x.total_tasks, reverse=True)

    def get_task_type_stats(self, metrics: list[dict[str, Any]]) -> list[TaskTypeStats]:
        """Calculate per-task-type statistics."""
        task_metrics: dict[str, list] = {}

        for metric in metrics:
            task_type = metric.get("task_type", "general")
            if task_type not in task_metrics:
                task_metrics[task_type] = []
            task_metrics[task_type].append(metric)

        stats = []
        for task_type, task_data in task_metrics.items():
            successes = sum(1 for m in task_data if m.get("success", True))
            total_tokens = sum(m.get("tokens", 0) for m in task_data)
            latencies = [m.get("latency", 0) for m in task_data]

            stats.append(
                TaskTypeStats(
                    task_type=task_type,
                    total_tasks=len(task_data),
                    success_rate=successes / len(task_data) if task_data else 0,
                    avg_latency=sum(latencies) / len(latencies) if latencies else 0,
                    avg_tokens=int(total_tokens / len(task_data)) if task_data else 0,
                )
            )

        return sorted(stats, key=lambda x: x.total_tasks, reverse=True)

    def get_cache_stats(self) -> CacheStats:
        """Calculate cache statistics."""
        hit_count = 0
        miss_count = 0
        entries_cached = 0

        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE) as f:
                    entries_cached = sum(1 for _ in f)
            except Exception as e:
                logger.warning(f"Failed to count cache entries: {e}")

        # Look for cache stats in metrics
        for metric in self.metrics:
            if metric.get("task_type") == "cache":
                if metric.get("success"):
                    hit_count += 1
                else:
                    miss_count += 1

        total = hit_count + miss_count
        return CacheStats(
            hit_rate=hit_count / total if total > 0 else 0,
            total_hits=hit_count,
            total_misses=miss_count,
            entries_cached=entries_cached,
        )


# Global metrics store
metrics_store = MetricsStore()


# API Endpoints
@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "orchestration-metrics-dashboard"}


@app.get("/metrics/overview", tags=["Metrics"])
async def get_overview(
    agent: str | None = Query(None, description="Filter by agent name"),
    task_type: str | None = Query(None, description="Filter by task type"),
    hours: int = Query(24, description="Hours to look back"),
) -> dict[str, Any]:
    """Get overview of orchestration performance."""
    metrics = metrics_store.get_metrics(agent=agent, task_type=task_type, hours=hours)
    stats = metrics_store.calculate_stats(metrics)

    return {
        "timestamp": datetime.now().isoformat(),
        "filters": {"agent": agent, "task_type": task_type, "hours": hours},
        "summary": stats.dict(),
        "metrics_count": len(metrics),
    }


@app.get("/metrics/agents", tags=["Metrics"])
async def get_agent_stats(
    hours: int = Query(24, description="Hours to look back"),
) -> dict[str, Any]:
    """Get per-agent statistics."""
    metrics = metrics_store.get_metrics(hours=hours)
    agent_stats = metrics_store.get_agent_stats(metrics)

    return {
        "timestamp": datetime.now().isoformat(),
        "agents": [stat.dict() for stat in agent_stats],
        "total_agents": len(agent_stats),
    }


@app.get("/metrics/task-types", tags=["Metrics"])
async def get_task_type_stats(
    hours: int = Query(24, description="Hours to look back"),
) -> dict[str, Any]:
    """Get per-task-type statistics."""
    metrics = metrics_store.get_metrics(hours=hours)
    task_stats = metrics_store.get_task_type_stats(metrics)

    return {
        "timestamp": datetime.now().isoformat(),
        "task_types": [stat.dict() for stat in task_stats],
        "total_types": len(task_stats),
    }


@app.get("/metrics/cache", tags=["Metrics"])
async def get_cache_stats() -> dict[str, Any]:
    """Get cache performance statistics."""
    cache_stats = metrics_store.get_cache_stats()

    return {"timestamp": datetime.now().isoformat(), "cache": cache_stats.dict()}


@app.get("/metrics/timeseries", tags=["Metrics"])
async def get_timeseries(
    agent: str | None = Query(None, description="Filter by agent name"),
    task_type: str | None = Query(None, description="Filter by task type"),
    hours: int = Query(24, description="Hours to look back"),
    metric: str = Query("latency", description="Metric to plot: latency, tokens, success"),
) -> dict[str, Any]:
    """Get time series data for plotting."""
    metrics = metrics_store.get_metrics(agent=agent, task_type=task_type, hours=hours)

    if metric == "latency":
        data = [(m.get("timestamp"), m.get("latency")) for m in metrics]
    elif metric == "tokens":
        data = [(m.get("timestamp"), m.get("tokens")) for m in metrics]
    elif metric == "success":
        data = [(m.get("timestamp"), 1 if m.get("success") else 0) for m in metrics]
    else:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")

    return {
        "timestamp": datetime.now().isoformat(),
        "metric": metric,
        "filters": {"agent": agent, "task_type": task_type, "hours": hours},
        "data": [{"time": t, "value": v} for t, v in data],
        "count": len(data),
    }


@app.get("/metrics/raw", tags=["Metrics"])
async def get_raw_metrics(
    agent: str | None = Query(None, description="Filter by agent name"),
    task_type: str | None = Query(None, description="Filter by task type"),
    hours: int = Query(24, description="Hours to look back"),
    limit: int = Query(100, description="Maximum results"),
) -> dict[str, Any]:
    """Get raw metric entries."""
    metrics = metrics_store.get_metrics(agent=agent, task_type=task_type, hours=hours)
    metrics = metrics[-limit:]  # Last N entries

    return {
        "timestamp": datetime.now().isoformat(),
        "filters": {"agent": agent, "task_type": task_type, "hours": hours},
        "metrics": metrics,
        "count": len(metrics),
    }


# HTML Dashboard
@app.get("/", tags=["Dashboard"])
async def dashboard():
    """Serve dashboard HTML."""
    return {
        "message": "NuSyQ Orchestration Metrics Dashboard API",
        "api_docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/health",
            "overview": "/metrics/overview",
            "agents": "/metrics/agents",
            "task_types": "/metrics/task-types",
            "cache": "/metrics/cache",
            "timeseries": "/metrics/timeseries",
            "raw": "/metrics/raw",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
