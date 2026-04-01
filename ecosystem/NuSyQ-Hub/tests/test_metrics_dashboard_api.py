"""Tests for src/observability/metrics_dashboard_api.py

This module tests the Orchestration Metrics Dashboard FastAPI service.

Coverage Target: 70%+
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

# =============================================================================
# Module Import Tests
# =============================================================================


class TestModuleImports:
    """Test module-level imports."""

    def test_import_metric_entry(self):
        """Test MetricEntry model can be imported."""
        from src.observability.metrics_dashboard_api import MetricEntry

        assert MetricEntry is not None

    def test_import_performance_metrics(self):
        """Test PerformanceMetrics model can be imported."""
        from src.observability.metrics_dashboard_api import PerformanceMetrics

        assert PerformanceMetrics is not None

    def test_import_agent_stats(self):
        """Test AgentStats model can be imported."""
        from src.observability.metrics_dashboard_api import AgentStats

        assert AgentStats is not None

    def test_import_task_type_stats(self):
        """Test TaskTypeStats model can be imported."""
        from src.observability.metrics_dashboard_api import TaskTypeStats

        assert TaskTypeStats is not None

    def test_import_cache_stats(self):
        """Test CacheStats model can be imported."""
        from src.observability.metrics_dashboard_api import CacheStats

        assert CacheStats is not None

    def test_import_metrics_store(self):
        """Test MetricsStore can be imported."""
        from src.observability.metrics_dashboard_api import MetricsStore

        assert MetricsStore is not None

    def test_import_app(self):
        """Test FastAPI app can be imported."""
        from src.observability.metrics_dashboard_api import app

        assert app is not None


# =============================================================================
# Pydantic Model Tests
# =============================================================================


class TestMetricEntry:
    """Test MetricEntry model."""

    def test_create_metric_entry(self):
        """Test creating a valid metric entry."""
        from src.observability.metrics_dashboard_api import MetricEntry

        entry = MetricEntry(
            timestamp="2025-01-01T00:00:00",
            agent="ollama",
            task_type="code_review",
            latency=1.5,
            tokens=500,
            success=True,
        )

        assert entry.agent == "ollama"
        assert entry.latency == 1.5
        assert entry.success is True

    def test_metric_entry_to_dict(self):
        """Test model_dump produces dict."""
        from src.observability.metrics_dashboard_api import MetricEntry

        entry = MetricEntry(
            timestamp="2025-01-01T00:00:00",
            agent="chatdev",
            task_type="generation",
            latency=2.0,
            tokens=1000,
            success=False,
        )

        data = entry.model_dump()

        assert data["agent"] == "chatdev"
        assert data["success"] is False


class TestPerformanceMetrics:
    """Test PerformanceMetrics model."""

    def test_create_performance_metrics(self):
        """Test creating performance metrics."""
        from src.observability.metrics_dashboard_api import PerformanceMetrics

        metrics = PerformanceMetrics(
            total_tasks=100,
            avg_latency=1.5,
            p95_latency=3.0,
            p99_latency=5.0,
            success_rate=0.95,
            avg_tokens=500,
            total_tokens=50000,
        )

        assert metrics.total_tasks == 100
        assert metrics.success_rate == 0.95

    def test_empty_performance_metrics(self):
        """Test creating empty metrics."""
        from src.observability.metrics_dashboard_api import PerformanceMetrics

        metrics = PerformanceMetrics(
            total_tasks=0,
            avg_latency=0,
            p95_latency=0,
            p99_latency=0,
            success_rate=0,
            avg_tokens=0,
            total_tokens=0,
        )

        assert metrics.total_tasks == 0


class TestAgentStats:
    """Test AgentStats model."""

    def test_create_agent_stats(self):
        """Test creating agent stats."""
        from src.observability.metrics_dashboard_api import AgentStats

        stats = AgentStats(
            agent="ollama",
            total_tasks=50,
            success_rate=0.98,
            avg_latency=1.2,
            avg_tokens=450,
        )

        assert stats.agent == "ollama"
        assert stats.success_rate == 0.98


class TestTaskTypeStats:
    """Test TaskTypeStats model."""

    def test_create_task_type_stats(self):
        """Test creating task type stats."""
        from src.observability.metrics_dashboard_api import TaskTypeStats

        stats = TaskTypeStats(
            task_type="code_review",
            total_tasks=30,
            success_rate=0.90,
            avg_latency=2.5,
            avg_tokens=800,
        )

        assert stats.task_type == "code_review"
        assert stats.avg_tokens == 800


class TestCacheStats:
    """Test CacheStats model."""

    def test_create_cache_stats(self):
        """Test creating cache stats."""
        from src.observability.metrics_dashboard_api import CacheStats

        stats = CacheStats(
            hit_rate=0.75,
            total_hits=150,
            total_misses=50,
            entries_cached=200,
        )

        assert stats.hit_rate == 0.75
        assert stats.entries_cached == 200


# =============================================================================
# MetricsStore Tests
# =============================================================================


class TestMetricsStore:
    """Test MetricsStore class."""

    def test_create_metrics_store(self):
        """Test creating a metrics store."""
        from src.observability.metrics_dashboard_api import MetricsStore

        # Mock file paths to not load real data
        with patch("src.observability.metrics_dashboard_api.METRICS_FILE") as mock_file:
            mock_file.exists.return_value = False
            with patch("src.observability.metrics_dashboard_api.QUEST_LOG") as mock_quest:
                mock_quest.exists.return_value = False

                store = MetricsStore()

        assert store.metrics == []

    def test_get_metrics_empty(self):
        """Test getting metrics from empty store."""
        from src.observability.metrics_dashboard_api import MetricsStore

        with patch("src.observability.metrics_dashboard_api.METRICS_FILE") as mock_file:
            mock_file.exists.return_value = False
            with patch("src.observability.metrics_dashboard_api.QUEST_LOG") as mock_quest:
                mock_quest.exists.return_value = False

                store = MetricsStore()

        metrics = store.get_metrics()

        assert metrics == []

    def test_calculate_stats_empty(self):
        """Test calculating stats from empty metrics."""
        from src.observability.metrics_dashboard_api import MetricsStore

        with patch("src.observability.metrics_dashboard_api.METRICS_FILE") as mock_file:
            mock_file.exists.return_value = False
            with patch("src.observability.metrics_dashboard_api.QUEST_LOG") as mock_quest:
                mock_quest.exists.return_value = False

                store = MetricsStore()

        stats = store.calculate_stats([])

        assert stats.total_tasks == 0
        assert stats.avg_latency == 0

    def test_calculate_stats_with_metrics(self):
        """Test calculating stats with real metrics."""
        from src.observability.metrics_dashboard_api import MetricsStore

        with patch("src.observability.metrics_dashboard_api.METRICS_FILE") as mock_file:
            mock_file.exists.return_value = False
            with patch("src.observability.metrics_dashboard_api.QUEST_LOG") as mock_quest:
                mock_quest.exists.return_value = False

                store = MetricsStore()

        test_metrics = [
            {"latency": 1.0, "tokens": 100, "success": True},
            {"latency": 2.0, "tokens": 200, "success": True},
            {"latency": 3.0, "tokens": 300, "success": False},
        ]

        stats = store.calculate_stats(test_metrics)

        assert stats.total_tasks == 3
        assert stats.avg_latency == 2.0
        assert stats.success_rate == pytest.approx(2 / 3)
        assert stats.total_tokens == 600

    def test_get_agent_stats(self):
        """Test getting per-agent stats."""
        from src.observability.metrics_dashboard_api import MetricsStore

        with patch("src.observability.metrics_dashboard_api.METRICS_FILE") as mock_file:
            mock_file.exists.return_value = False
            with patch("src.observability.metrics_dashboard_api.QUEST_LOG") as mock_quest:
                mock_quest.exists.return_value = False

                store = MetricsStore()

        test_metrics = [
            {"agent": "ollama", "latency": 1.0, "tokens": 100, "success": True},
            {"agent": "ollama", "latency": 2.0, "tokens": 200, "success": True},
            {"agent": "chatdev", "latency": 3.0, "tokens": 300, "success": False},
        ]

        stats = store.get_agent_stats(test_metrics)

        assert len(stats) == 2
        # Sorted by total_tasks descending
        assert stats[0].agent == "ollama"
        assert stats[0].total_tasks == 2
        assert stats[1].agent == "chatdev"
        assert stats[1].total_tasks == 1

    def test_get_task_type_stats(self):
        """Test getting per-task-type stats."""
        from src.observability.metrics_dashboard_api import MetricsStore

        with patch("src.observability.metrics_dashboard_api.METRICS_FILE") as mock_file:
            mock_file.exists.return_value = False
            with patch("src.observability.metrics_dashboard_api.QUEST_LOG") as mock_quest:
                mock_quest.exists.return_value = False

                store = MetricsStore()

        test_metrics = [
            {"task_type": "review", "latency": 1.0, "tokens": 100, "success": True},
            {"task_type": "review", "latency": 2.0, "tokens": 200, "success": True},
            {"task_type": "generate", "latency": 3.0, "tokens": 300, "success": True},
        ]

        stats = store.get_task_type_stats(test_metrics)

        assert len(stats) == 2
        assert stats[0].task_type == "review"
        assert stats[0].total_tasks == 2

    def test_get_cache_stats(self):
        """Test getting cache stats."""
        from src.observability.metrics_dashboard_api import MetricsStore

        with patch("src.observability.metrics_dashboard_api.METRICS_FILE") as mock_file:
            mock_file.exists.return_value = False
            with patch("src.observability.metrics_dashboard_api.QUEST_LOG") as mock_quest:
                mock_quest.exists.return_value = False

                store = MetricsStore()

        # Mock CACHE_FILE for get_cache_stats call
        with patch("src.observability.metrics_dashboard_api.CACHE_FILE") as mock_cache:
            mock_cache.exists.return_value = False
            stats = store.get_cache_stats()

        assert stats.hit_rate == 0.0
        assert stats.entries_cached == 0


# =============================================================================
# FastAPI Endpoint Tests
# =============================================================================


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health endpoint returns healthy status."""
        from src.observability.metrics_dashboard_api import health_check

        result = await health_check()

        assert result["status"] == "healthy"
        assert "orchestration-metrics-dashboard" in result["service"]


class TestMetricsEndpoints:
    """Test metrics API endpoints."""

    @pytest.mark.asyncio
    async def test_get_overview(self):
        """Test overview endpoint."""
        from src.observability.metrics_dashboard_api import get_overview

        # Mock the global metrics_store
        with patch("src.observability.metrics_dashboard_api.metrics_store") as mock_store:
            mock_store.get_metrics.return_value = []
            from src.observability.metrics_dashboard_api import PerformanceMetrics

            mock_store.calculate_stats.return_value = PerformanceMetrics(
                total_tasks=0,
                avg_latency=0,
                p95_latency=0,
                p99_latency=0,
                success_rate=0,
                avg_tokens=0,
                total_tokens=0,
            )

            result = await get_overview()

        assert "timestamp" in result
        assert "summary" in result
        assert "metrics_count" in result

    @pytest.mark.asyncio
    async def test_get_agent_stats_endpoint(self):
        """Test agent stats endpoint."""
        from src.observability.metrics_dashboard_api import get_agent_stats

        with patch("src.observability.metrics_dashboard_api.metrics_store") as mock_store:
            mock_store.get_metrics.return_value = []
            mock_store.get_agent_stats.return_value = []

            result = await get_agent_stats()

        assert "agents" in result
        assert "total_agents" in result

    @pytest.mark.asyncio
    async def test_get_task_type_stats_endpoint(self):
        """Test task type stats endpoint."""
        from src.observability.metrics_dashboard_api import get_task_type_stats

        with patch("src.observability.metrics_dashboard_api.metrics_store") as mock_store:
            mock_store.get_metrics.return_value = []
            mock_store.get_task_type_stats.return_value = []

            result = await get_task_type_stats()

        assert "task_types" in result
        assert "total_types" in result

    @pytest.mark.asyncio
    async def test_get_cache_stats_endpoint(self):
        """Test cache stats endpoint."""
        from src.observability.metrics_dashboard_api import get_cache_stats

        with patch("src.observability.metrics_dashboard_api.metrics_store") as mock_store:
            from src.observability.metrics_dashboard_api import CacheStats

            mock_store.get_cache_stats.return_value = CacheStats(
                hit_rate=0.5,
                total_hits=100,
                total_misses=100,
                entries_cached=50,
            )

            result = await get_cache_stats()

        # Result structure is {"timestamp": ..., "cache": {...}}
        assert "cache" in result
        assert result["cache"]["hit_rate"] == 0.5


# =============================================================================
# Filter Tests
# =============================================================================


class TestMetricsFiltering:
    """Test metrics filtering functionality."""

    def test_filter_by_agent(self):
        """Test filtering metrics by agent."""
        from src.observability.metrics_dashboard_api import MetricsStore

        with patch("src.observability.metrics_dashboard_api.METRICS_FILE") as mock_file:
            mock_file.exists.return_value = False
            with patch("src.observability.metrics_dashboard_api.QUEST_LOG") as mock_quest:
                mock_quest.exists.return_value = False

                store = MetricsStore()

        # Inject test metrics with recent timestamps
        now = datetime.now()
        store.metrics = [
            {"agent": "ollama", "timestamp": now.isoformat()},
            {"agent": "chatdev", "timestamp": now.isoformat()},
            {"agent": "ollama", "timestamp": now.isoformat()},
        ]

        filtered = store.get_metrics(agent="ollama", hours=24)

        assert len(filtered) == 2
        assert all(m["agent"] == "ollama" for m in filtered)

    def test_filter_by_task_type(self):
        """Test filtering metrics by task type."""
        from src.observability.metrics_dashboard_api import MetricsStore

        with patch("src.observability.metrics_dashboard_api.METRICS_FILE") as mock_file:
            mock_file.exists.return_value = False
            with patch("src.observability.metrics_dashboard_api.QUEST_LOG") as mock_quest:
                mock_quest.exists.return_value = False

                store = MetricsStore()

        now = datetime.now()
        store.metrics = [
            {"task_type": "review", "timestamp": now.isoformat()},
            {"task_type": "generate", "timestamp": now.isoformat()},
            {"task_type": "review", "timestamp": now.isoformat()},
        ]

        filtered = store.get_metrics(task_type="review", hours=24)

        assert len(filtered) == 2

    def test_filter_by_hours(self):
        """Test filtering metrics by time window."""
        from src.observability.metrics_dashboard_api import MetricsStore

        with patch("src.observability.metrics_dashboard_api.METRICS_FILE") as mock_file:
            mock_file.exists.return_value = False
            with patch("src.observability.metrics_dashboard_api.QUEST_LOG") as mock_quest:
                mock_quest.exists.return_value = False

                store = MetricsStore()

        now = datetime.now()
        old = now - timedelta(hours=48)

        store.metrics = [
            {"timestamp": now.isoformat()},
            {"timestamp": old.isoformat()},
        ]

        filtered = store.get_metrics(hours=24)

        # Only recent metrics included
        assert len(filtered) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
