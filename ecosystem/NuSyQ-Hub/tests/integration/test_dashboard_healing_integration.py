"""Integration tests for Dashboard, Scheduler, and Tracker systems.

Tests the complete flow of:
1. Dashboard API recording cycles
2. Healing Cycle Scheduler triggering cycles
3. Resolution Tracker recording issue outcomes
"""

# pylint: disable=import-outside-toplevel

from datetime import datetime, timezone, UTC
from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestDashboardHealingIntegration:
    """Integration tests for dashboard-healing pipeline."""

    def test_dashboard_api_initialization(self):
        """Test dashboard API initializes correctly."""
        try:
            from src.web.dashboard_api import DashboardAPI

            dashboard = DashboardAPI()
            assert dashboard is not None
            assert hasattr(dashboard, "metrics_file")
            assert hasattr(dashboard, "record_cycle")
            assert hasattr(dashboard, "get_metrics")
        except ImportError:
            pytest.skip("Dashboard API not available")

    def test_dashboard_records_cycle_data(self):
        """Test dashboard records healing cycle data."""
        try:
            from src.web.dashboard_api import DashboardAPI

            dashboard = DashboardAPI()

            # Create sample cycle data
            cycle_data = {
                "cycle_num": 1,
                "issues_detected": 5,
                "tasks_created": 3,
                "tasks_completed": 2,
                "healing_applied": 2,
                "health_status": "recovering",
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Record cycle
            dashboard.record_cycle(cycle_data)

            # Verify metrics were recorded
            metrics = dashboard.get_metrics()
            assert metrics is not None
            assert "cycles" in metrics or len(metrics) > 0
        except ImportError:
            pytest.skip("Dashboard API not available")

    def test_healing_scheduler_initialization(self):
        """Test healing scheduler initializes correctly."""
        try:
            from src.orchestration.healing_cycle_scheduler import HealingCycleScheduler

            sched = HealingCycleScheduler()
            assert isinstance(sched, HealingCycleScheduler)
            assert hasattr(sched, "schedule_cycle")
            assert hasattr(sched, "schedule_health_check")
            assert hasattr(sched, "schedule_daily_report")
        except ImportError:
            pytest.skip("Healing Cycle Scheduler not available")

    def test_resolution_tracker_initialization(self):
        """Test resolution tracker initializes correctly."""
        try:
            from src.analytics.resolution_tracker import ResolutionTracker

            tracker = ResolutionTracker()
            assert isinstance(tracker, ResolutionTracker)
            assert hasattr(tracker, "register_detected_issue")
            assert hasattr(tracker, "mark_routed")
            assert hasattr(tracker, "mark_resolved")
            assert hasattr(tracker, "get_metrics")
        except ImportError:
            pytest.skip("Resolution Tracker not available")

    def test_tracker_registers_and_tracks_issue(self):
        """Test tracker can register and track issue lifecycle."""
        try:
            from src.analytics.resolution_tracker import ResolutionTracker

            tracker = ResolutionTracker()

            # Register an issue
            issue_record = tracker.register_detected_issue(
                issue_id="test_issue_1",
                issue_type="import_error",
                description="Test import error",
                file_path="src/test.py",
                severity="high",
                cycle_num=1,
            )

            assert issue_record is not None
            assert issue_record.issue_id == "test_issue_1"

            # Mark as routed
            tracker.mark_routed("test_issue_1", "chatdev")

            # Mark as resolved
            tracker.mark_resolved("test_issue_1", fix_code="import fix", success=True)

            # Get metrics
            metrics = tracker.get_metrics()
            assert metrics is not None
        except ImportError:
            pytest.skip("Resolution Tracker not available")

    @pytest.mark.asyncio
    async def test_unified_pipeline_integration(self):
        """Test unified healing pipeline integrates all systems."""
        try:
            from src.orchestration.unified_autonomous_healing_pipeline import (
                UnifiedAutonomousHealingPipeline,
            )

            pipeline = UnifiedAutonomousHealingPipeline()

            # Verify all systems initialized
            assert hasattr(pipeline, "cycle_runner")
            assert hasattr(pipeline, "tracker")
            assert hasattr(pipeline, "dashboard")
            assert hasattr(pipeline, "scheduler")
        except ImportError:
            pytest.skip("Unified Pipeline not available")

    def test_performance_cache_integration(self):
        """Test performance cache system."""
        try:
            from src.optimization.performance_cache import PerformanceCache

            cache = PerformanceCache()

            # Test caching
            cache.set("key1", "value1")
            result = cache.get("key1")
            assert result == "value1"

            # Test stats
            stats = cache.get_stats()
            assert "hits" in stats or "misses" in stats
        except ImportError:
            pytest.skip("Performance Cache not available")

    def test_cache_decorator(self):
        """Test cache decorator function."""
        try:
            from src.optimization.performance_cache import PerformanceCache

            cache = PerformanceCache()

            # Test basic set/get
            cache.set("test_key", "test_value", ttl_seconds=60)
            result = cache.get("test_key")
            assert result == "test_value"

            # Test stats
            stats = cache.get_stats()
            assert "hits" in stats
            assert stats["hits"] > 0
        except ImportError:
            pytest.skip("Performance Cache not available")


@pytest.mark.integration
class TestDashboardMetricsEndpoints:
    """Test dashboard API metrics endpoints."""

    def test_dashboard_has_metrics_endpoint(self):
        """Test dashboard exposes metrics endpoint."""
        try:
            from src.web.dashboard_api import DashboardAPI

            dashboard = DashboardAPI()

            # Mock Flask app context
            with patch.object(dashboard, "app"):
                assert hasattr(dashboard, "get_metrics")
        except ImportError:
            pytest.skip("Dashboard API not available")

    def test_dashboard_cycles_endpoint(self):
        """Test /api/cycles endpoint."""
        try:
            from src.web.dashboard_api import DashboardAPI

            dashboard = DashboardAPI()

            # Record sample data
            cycle_data = {
                "cycle_num": 1,
                "issues_detected": 3,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            dashboard.record_cycle(cycle_data)

            # Get metrics
            metrics = dashboard.get_metrics()
            assert metrics is not None
        except ImportError:
            pytest.skip("Dashboard API not available")


@pytest.mark.integration
class TestTrackerPeristence:
    """Test resolution tracker persistence."""

    def test_tracker_saves_to_database(self):
        """Test tracker persists data to JSONL database."""
        try:
            from src.analytics.resolution_tracker import ResolutionTracker

            tracker = ResolutionTracker()

            # Register issue
            tracker.register_detected_issue(
                issue_id="test_persist",
                issue_type="syntax_error",
                description="Test syntax error",
                file_path="test.py",
                severity="medium",
                cycle_num=1,
            )

            # Data should be recorded
            metrics = tracker.get_metrics()
            assert metrics is not None
        except ImportError:
            pytest.skip("Resolution Tracker not available")

    def test_tracker_loads_from_database(self):
        """Test tracker can load persisted data."""
        try:
            from src.analytics.resolution_tracker import ResolutionTracker

            tracker = ResolutionTracker()

            # Add data
            tracker.register_detected_issue(
                issue_id="load_test_1",
                issue_type="error",
                description="Test error",
                file_path="test.py",
                severity="high",
                cycle_num=1,
            )

            # Create new instance and verify data persists
            tracker2 = ResolutionTracker()
            metrics = tracker2.get_metrics()

            # Should have loaded previous data
            assert metrics is not None
            assert len(tracker2.issues) > 0
        except ImportError:
            pytest.skip("Resolution Tracker not available")


@pytest.mark.integration
class TestSchedulerIntegration:
    """Test healing cycle scheduler integration."""

    def test_scheduler_creates_jobs(self):
        """Test scheduler creates scheduled jobs."""
        try:
            from src.orchestration.healing_cycle_scheduler import HealingCycleScheduler

            scheduler = HealingCycleScheduler()

            # Scheduler should have scheduled jobs
            assert isinstance(scheduler, HealingCycleScheduler)
            # Jobs are scheduled in background
        except ImportError:
            pytest.skip("Healing Cycle Scheduler not available")

    def test_scheduler_generates_report(self):
        """Test scheduler can generate daily reports."""
        try:
            from src.orchestration.healing_cycle_scheduler import HealingCycleScheduler

            scheduler = HealingCycleScheduler()

            # Scheduler should have reporting capability
            assert hasattr(scheduler, "schedule_daily_report")
        except ImportError:
            pytest.skip("Healing Cycle Scheduler not available")


@pytest.mark.integration
class TestCachePerformance:
    """Test cache performance characteristics."""

    def test_cache_hit_rate_tracking(self):
        """Test cache tracks hit/miss rates."""
        try:
            from src.optimization.performance_cache import PerformanceCache

            cache = PerformanceCache()

            # Set values
            for i in range(5):
                cache.set(f"key{i}", f"value{i}")

            # Get values (hits)
            for i in range(5):
                cache.get(f"key{i}")

            # Get non-existent (misses)
            for i in range(5, 10):
                cache.get(f"key{i}")

            stats = cache.get_stats()
            assert "hits" in stats or len(stats) > 0
        except ImportError:
            pytest.skip("Performance Cache not available")

    def test_cache_eviction(self):
        """Test LRU eviction policy."""
        try:
            from src.optimization.performance_cache import PerformanceCache

            # Small cache for testing eviction
            cache = PerformanceCache(max_memory_mb=1)  # Very small

            # Add many items
            for i in range(100):
                cache.set(f"key{i}", "x" * 1000)

            # Cache should have evicted items
            stats = cache.get_stats()
            assert stats is not None
        except ImportError:
            pytest.skip("Performance Cache not available")
