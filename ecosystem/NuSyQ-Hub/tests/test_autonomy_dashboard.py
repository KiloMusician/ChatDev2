"""Tests for src/observability/autonomy_dashboard.py

This module tests the Autonomy Dashboard metrics collection system.

Coverage Target: 70%+
"""

from datetime import datetime
import json

import pytest

# =============================================================================
# Module Import Tests
# =============================================================================


class TestModuleImports:
    """Test module-level imports."""

    def test_import_metric_type(self):
        """Test MetricType enum can be imported."""
        from src.observability.autonomy_dashboard import MetricType

        assert MetricType is not None

    def test_import_metric_event(self):
        """Test MetricEvent dataclass can be imported."""
        from src.observability.autonomy_dashboard import MetricEvent

        assert MetricEvent is not None

    def test_import_dashboard_metrics(self):
        """Test DashboardMetrics dataclass can be imported."""
        from src.observability.autonomy_dashboard import DashboardMetrics

        assert DashboardMetrics is not None

    def test_import_metrics_collector(self):
        """Test MetricsCollector class can be imported."""
        from src.observability.autonomy_dashboard import MetricsCollector

        assert MetricsCollector is not None


# =============================================================================
# MetricType Tests
# =============================================================================


class TestMetricType:
    """Test MetricType enum."""

    def test_all_metric_types_exist(self):
        """Test all expected metric types exist."""
        from src.observability.autonomy_dashboard import MetricType

        expected = [
            "TASK_COMPLETION",
            "PR_CREATED",
            "PR_MERGED",
            "PR_REJECTED",
            "RISK_ASSESSMENT",
            "MODEL_INVOCATION",
            "SCHEDULER_DECISION",
            "SYSTEM_HEALTH",
        ]

        for name in expected:
            assert hasattr(MetricType, name)

    def test_metric_type_values(self):
        """Test metric type values."""
        from src.observability.autonomy_dashboard import MetricType

        assert MetricType.TASK_COMPLETION.value == "task_completion"
        assert MetricType.PR_MERGED.value == "pr_merged"


# =============================================================================
# MetricEvent Tests
# =============================================================================


class TestMetricEvent:
    """Test MetricEvent dataclass."""

    def test_create_event(self):
        """Test creating a metric event."""
        from src.observability.autonomy_dashboard import MetricEvent, MetricType

        event = MetricEvent(
            metric_type=MetricType.TASK_COMPLETION,
            timestamp=datetime.now(),
            data={"success": True, "duration": 10.0},
            task_id=123,
        )

        assert event.metric_type == MetricType.TASK_COMPLETION
        assert event.task_id == 123
        assert event.data["success"] is True

    def test_event_defaults(self):
        """Test event optional fields default to None."""
        from src.observability.autonomy_dashboard import MetricEvent, MetricType

        event = MetricEvent(
            metric_type=MetricType.SYSTEM_HEALTH,
            timestamp=datetime.now(),
            data={},
        )

        assert event.task_id is None
        assert event.pr_number is None


# =============================================================================
# DashboardMetrics Tests
# =============================================================================


class TestDashboardMetrics:
    """Test DashboardMetrics dataclass."""

    def test_create_default_metrics(self):
        """Test creating metrics with defaults."""
        from src.observability.autonomy_dashboard import DashboardMetrics

        metrics = DashboardMetrics()

        assert metrics.total_tasks == 0
        assert metrics.completed_tasks == 0
        assert metrics.failed_tasks == 0
        assert metrics.prs_created_today == 0
        assert metrics.diversity_score == 0.0

    def test_create_metrics_with_values(self):
        """Test creating metrics with custom values."""
        from src.observability.autonomy_dashboard import DashboardMetrics

        metrics = DashboardMetrics(
            total_tasks=100,
            completed_tasks=80,
            failed_tasks=5,
            pending_tasks=15,
            ollama_invocations=50,
        )

        assert metrics.total_tasks == 100
        assert metrics.completed_tasks == 80
        assert metrics.ollama_invocations == 50

    def test_metrics_category_distribution(self):
        """Test category distribution field."""
        from src.observability.autonomy_dashboard import DashboardMetrics

        metrics = DashboardMetrics(category_distribution={"BUGFIX": 10, "FEATURE": 5})

        assert metrics.category_distribution["BUGFIX"] == 10


# =============================================================================
# MetricsCollector Initialization Tests
# =============================================================================


class TestMetricsCollectorInit:
    """Test MetricsCollector initialization."""

    def test_init_creates_storage_dir(self, tmp_path):
        """Test that init creates storage directory."""
        from src.observability.autonomy_dashboard import MetricsCollector

        storage = tmp_path / "metrics" / "dashboard"
        MetricsCollector(storage_path=storage)

        assert storage.exists()

    def test_init_default_retention(self, tmp_path):
        """Test default retention period."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        assert collector.retention_days == 30

    def test_init_custom_retention(self, tmp_path):
        """Test custom retention period."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(
            storage_path=tmp_path,
            retention_days=7,
        )

        assert collector.retention_days == 7

    def test_init_aggregation_interval(self, tmp_path):
        """Test aggregation interval setting."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(
            storage_path=tmp_path,
            aggregation_interval_minutes=10,
        )

        assert collector.aggregation_interval == 10

    def test_init_empty_event_buffer(self, tmp_path):
        """Test event buffer starts empty."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        assert len(collector.event_buffer) == 0

    def test_init_advanced_ai_report_paths(self, tmp_path):
        """Collector should point at canonical AI status and meta-learning reports."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        assert collector.ai_status_report.name == "ai_status_latest.json"
        assert collector.meta_learning_report.name == "ai_intermediary_meta_learning_latest.json"


# =============================================================================
# Record Event Tests
# =============================================================================


class TestRecordEvent:
    """Test event recording methods."""

    @pytest.mark.asyncio
    async def test_record_event(self, tmp_path):
        """Test recording a generic event."""
        from src.observability.autonomy_dashboard import (
            MetricEvent,
            MetricsCollector,
            MetricType,
        )

        collector = MetricsCollector(storage_path=tmp_path)
        event = MetricEvent(
            metric_type=MetricType.SYSTEM_HEALTH,
            timestamp=datetime.now(),
            data={"status": "healthy"},
        )

        await collector.record_event(event)

        assert len(collector.event_buffer) == 1
        assert collector.event_buffer[0].metric_type == MetricType.SYSTEM_HEALTH

    @pytest.mark.asyncio
    async def test_aggregate_metrics_reads_advanced_ai_intelligence(self, tmp_path):
        """Aggregation should overlay persisted advanced-AI and meta-learning signals."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path / "metrics")
        collector.ai_status_report = tmp_path / "ai_status_latest.json"
        collector.meta_learning_report = tmp_path / "ai_intermediary_meta_learning_latest.json"

        collector.ai_status_report.write_text(
            json.dumps(
                {
                    "capability_intelligence": {
                        "advanced_ai_readiness": {
                            "capabilities": {
                                "ensemble_consensus": {"status": "ready"},
                                "meta_learning": {"status": "partial"},
                                "graph_learning": {"status": "missing"},
                            }
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        collector.meta_learning_report.write_text(
            json.dumps(
                {
                    "snapshot": {
                        "total_events": 9,
                        "error_events": 2,
                        "routed_events": 5,
                        "max_recursion_depth": 4,
                    }
                }
            ),
            encoding="utf-8",
        )

        snapshot = await collector.aggregate_metrics()

        assert snapshot.advanced_ai_ready_count == 1
        assert snapshot.advanced_ai_partial_count == 1
        assert snapshot.advanced_ai_missing_count == 1
        assert snapshot.meta_learning_total_events == 9
        assert snapshot.meta_learning_error_events == 2
        assert snapshot.meta_learning_routed_events == 5
        assert snapshot.meta_learning_max_recursion_depth == 4
        assert collector.latest_report_path.exists()

    @pytest.mark.asyncio
    async def test_record_task_completion(self, tmp_path):
        """Test recording task completion."""
        from src.observability.autonomy_dashboard import MetricsCollector, MetricType

        collector = MetricsCollector(storage_path=tmp_path)

        await collector.record_task_completion(
            task_id=1,
            success=True,
            duration_seconds=60.0,
            category="BUGFIX",
        )

        assert len(collector.event_buffer) == 1
        event = collector.event_buffer[0]
        assert event.metric_type == MetricType.TASK_COMPLETION
        assert event.data["success"] is True
        assert event.data["category"] == "BUGFIX"

    @pytest.mark.asyncio
    async def test_record_pr_created(self, tmp_path):
        """Test recording PR creation."""
        from src.observability.autonomy_dashboard import MetricsCollector, MetricType

        collector = MetricsCollector(storage_path=tmp_path)

        await collector.record_pr_created(
            pr_number=42,
            task_id=1,
            risk_score=0.25,
            risk_level="AUTO",
            approval_policy="auto_merge",
        )

        assert len(collector.event_buffer) == 1
        event = collector.event_buffer[0]
        assert event.metric_type == MetricType.PR_CREATED
        assert event.pr_number == 42
        assert event.data["risk_score"] == 0.25

    @pytest.mark.asyncio
    async def test_record_pr_merged(self, tmp_path):
        """Test recording PR merge."""
        from src.observability.autonomy_dashboard import MetricsCollector, MetricType

        collector = MetricsCollector(storage_path=tmp_path)

        await collector.record_pr_merged(
            pr_number=42,
            auto_merged=True,
            merge_time_hours=0.5,
        )

        event = collector.event_buffer[0]
        assert event.metric_type == MetricType.PR_MERGED
        assert event.data["auto_merged"] is True

    @pytest.mark.asyncio
    async def test_record_model_invocation(self, tmp_path):
        """Test recording model invocation."""
        from src.observability.autonomy_dashboard import MetricsCollector, MetricType

        collector = MetricsCollector(storage_path=tmp_path)

        await collector.record_model_invocation(
            model_name="ollama-qwen",
            task_id=5,
        )

        event = collector.event_buffer[0]
        assert event.metric_type == MetricType.MODEL_INVOCATION
        assert event.data["model"] == "ollama-qwen"

    @pytest.mark.asyncio
    async def test_record_risk_assessment(self, tmp_path):
        """Test recording risk assessment."""
        from src.observability.autonomy_dashboard import MetricsCollector, MetricType

        collector = MetricsCollector(storage_path=tmp_path)

        await collector.record_risk_assessment(
            task_id=10,
            risk_score=0.45,
            risk_level="REVIEW",
        )

        event = collector.event_buffer[0]
        assert event.metric_type == MetricType.RISK_ASSESSMENT
        assert event.data["risk_level"] == "REVIEW"


# =============================================================================
# Aggregate Metrics Tests
# =============================================================================


class TestAggregateMetrics:
    """Test metrics aggregation."""

    @pytest.mark.asyncio
    async def test_aggregate_empty_buffer(self, tmp_path):
        """Test aggregation with no events."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        snapshot = await collector.aggregate_metrics()

        assert snapshot.completed_tasks == 0
        assert snapshot.prs_created_today == 0

    @pytest.mark.asyncio
    async def test_aggregate_task_completions(self, tmp_path):
        """Test aggregation counts task completions."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        # Record several task completions
        for i in range(5):
            await collector.record_task_completion(
                task_id=i,
                success=i != 2,  # One failure
                duration_seconds=60.0,
                category="BUGFIX",
            )

        snapshot = await collector.aggregate_metrics()

        assert snapshot.completed_tasks == 5
        assert snapshot.failed_tasks == 1

    @pytest.mark.asyncio
    async def test_aggregate_category_distribution(self, tmp_path):
        """Test category distribution aggregation."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        await collector.record_task_completion(1, True, 60, "BUGFIX")
        await collector.record_task_completion(2, True, 60, "BUGFIX")
        await collector.record_task_completion(3, True, 60, "FEATURE")

        snapshot = await collector.aggregate_metrics()

        assert snapshot.category_distribution.get("BUGFIX") == 2
        assert snapshot.category_distribution.get("FEATURE") == 1

    @pytest.mark.asyncio
    async def test_aggregate_risk_distribution(self, tmp_path):
        """Test risk distribution aggregation."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        await collector.record_risk_assessment(1, 0.1, "AUTO")  # < 0.3
        await collector.record_risk_assessment(2, 0.5, "REVIEW")  # 0.3-0.6
        await collector.record_risk_assessment(3, 0.7, "PROPOSAL")  # 0.6-0.8
        await collector.record_risk_assessment(4, 0.9, "BLOCKED")  # > 0.8

        snapshot = await collector.aggregate_metrics()

        assert snapshot.risk_auto_count == 1
        assert snapshot.risk_review_count == 1
        assert snapshot.risk_proposal_count == 1
        assert snapshot.risk_blocked_count == 1

    @pytest.mark.asyncio
    async def test_aggregate_model_invocations(self, tmp_path):
        """Test model invocation counting."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        await collector.record_model_invocation("ollama-qwen")
        await collector.record_model_invocation("ollama-llama")
        await collector.record_model_invocation("lm-studio-model")
        await collector.record_model_invocation("chatdev-ceo")
        await collector.record_model_invocation("copilot-suggestion")

        snapshot = await collector.aggregate_metrics()

        assert snapshot.ollama_invocations == 2
        assert snapshot.lm_studio_invocations == 1
        assert snapshot.chatdev_invocations == 1
        assert snapshot.copilot_invocations == 1

    @pytest.mark.asyncio
    async def test_aggregate_pr_metrics(self, tmp_path):
        """Test PR metrics aggregation."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        await collector.record_pr_created(1, 1, 0.2, "AUTO", "auto_merge")
        await collector.record_pr_created(2, 2, 0.5, "REVIEW", "manual")
        await collector.record_pr_merged(1, True, 0.5)

        snapshot = await collector.aggregate_metrics()

        assert snapshot.prs_created_today == 2
        assert snapshot.prs_merged_today == 1
        assert snapshot.prs_auto_merged_today == 1

    @pytest.mark.asyncio
    async def test_aggregate_success_rates(self, tmp_path):
        """Test success rate calculation."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        # Create 2 PRs, merge 1
        await collector.record_pr_created(1, 1, 0.2, "AUTO", "auto")
        await collector.record_pr_created(2, 2, 0.5, "REVIEW", "manual")
        await collector.record_pr_merged(1, True, 1.0)

        snapshot = await collector.aggregate_metrics()

        assert snapshot.pr_success_rate == 0.5  # 1/2

    @pytest.mark.asyncio
    async def test_aggregate_diversity_score(self, tmp_path):
        """Test diversity score calculation."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        # Add tasks with diverse categories
        await collector.record_task_completion(1, True, 60, "BUGFIX")
        await collector.record_task_completion(2, True, 60, "FEATURE")
        await collector.record_task_completion(3, True, 60, "TEST")
        await collector.record_task_completion(4, True, 60, "DOCS")

        snapshot = await collector.aggregate_metrics()

        # With 4 equally distributed categories, diversity should be high
        assert snapshot.diversity_score > 0.9

    @pytest.mark.asyncio
    async def test_aggregate_low_diversity(self, tmp_path):
        """Test low diversity score when all same category."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        # All same category
        for i in range(4):
            await collector.record_task_completion(i, True, 60, "BUGFIX")

        snapshot = await collector.aggregate_metrics()

        # Single category = 0 diversity
        assert snapshot.diversity_score == 0.0


# =============================================================================
# Snapshot Persistence Tests
# =============================================================================


class TestSnapshotPersistence:
    """Test snapshot save/load functionality."""

    @pytest.mark.asyncio
    async def test_snapshot_saved_to_disk(self, tmp_path):
        """Test that aggregation saves snapshot to disk."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)
        await collector.record_task_completion(1, True, 60, "TEST")

        await collector.aggregate_metrics()

        # Check that a snapshot file was created
        snapshots = list(tmp_path.glob("snapshot_*.json"))
        assert len(snapshots) == 1

    @pytest.mark.asyncio
    async def test_get_current_snapshot(self, tmp_path):
        """Test getting current snapshot."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)
        await collector.record_task_completion(1, True, 60, "TEST")
        await collector.aggregate_metrics()

        snapshot = collector.get_current_snapshot()

        assert snapshot.completed_tasks == 1

    @pytest.mark.asyncio
    async def test_get_historical_snapshots(self, tmp_path):
        """Test loading historical snapshots."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        # Create a few snapshots
        await collector.record_task_completion(1, True, 60, "A")
        await collector.aggregate_metrics()

        await collector.record_task_completion(2, True, 60, "B")
        await collector.aggregate_metrics()

        historical = await collector.get_historical_snapshots(hours=24)

        # Should have 2 snapshots (if not filtered out by timestamp)
        assert len(historical) >= 1


# =============================================================================
# Text Dashboard Tests
# =============================================================================


class TestTextDashboard:
    """Test text dashboard generation."""

    def test_generate_text_dashboard(self, tmp_path):
        """Test generating text dashboard."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        dashboard = collector.generate_text_dashboard()

        assert "NuSyQ Autonomy Dashboard" in dashboard
        assert "Task Queue Status" in dashboard
        assert "Risk Distribution" in dashboard
        assert "PR Metrics" in dashboard
        assert "Model Utilization" in dashboard

    @pytest.mark.asyncio
    async def test_dashboard_shows_metrics(self, tmp_path):
        """Test dashboard shows collected metrics."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        await collector.record_model_invocation("ollama-test")
        await collector.aggregate_metrics()

        dashboard = collector.generate_text_dashboard()

        # Dashboard should show the invocation
        assert "Ollama" in dashboard


# =============================================================================
# Event Buffer Tests
# =============================================================================


class TestEventBuffer:
    """Test event buffer behavior."""

    @pytest.mark.asyncio
    async def test_buffer_max_size(self, tmp_path):
        """Test buffer respects max size."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path)

        # Record more than buffer size
        for i in range(1100):
            await collector.record_task_completion(i, True, 1.0, "TEST")

        # Buffer should be capped at 1000
        assert len(collector.event_buffer) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
