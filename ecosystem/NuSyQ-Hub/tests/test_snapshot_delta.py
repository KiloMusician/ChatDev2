"""Tests for src/observability/snapshot_delta.py

This module tests the Snapshot Delta Tracking System.

Coverage Target: 70%+
"""

import json
from datetime import datetime, timedelta

import pytest

# =============================================================================
# Module Import Tests
# =============================================================================


class TestModuleImports:
    """Test module-level imports."""

    def test_import_snapshot_metrics(self):
        """Test SnapshotMetrics dataclass can be imported."""
        from src.observability.snapshot_delta import SnapshotMetrics

        assert SnapshotMetrics is not None

    def test_import_snapshot_delta(self):
        """Test SnapshotDelta dataclass can be imported."""
        from src.observability.snapshot_delta import SnapshotDelta

        assert SnapshotDelta is not None

    def test_import_snapshot_delta_tracker(self):
        """Test SnapshotDeltaTracker class can be imported."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        assert SnapshotDeltaTracker is not None


# =============================================================================
# SnapshotMetrics Tests
# =============================================================================


class TestSnapshotMetrics:
    """Test SnapshotMetrics dataclass."""

    def test_create_metrics(self):
        """Test creating snapshot metrics."""
        from src.observability.snapshot_delta import SnapshotMetrics

        metrics = SnapshotMetrics(
            timestamp="2025-01-01 12:00:00",
            dirty_file_count=5,
            commits_ahead=10,
            commits_behind=0,
            quest_status="active",
            quest_title="Test Quest",
            import_failures=2,
            test_failures=1,
            agent_activity={"ollama": 5, "copilot": 10},
        )

        assert metrics.timestamp == "2025-01-01 12:00:00"
        assert metrics.dirty_file_count == 5
        assert metrics.quest_title == "Test Quest"

    def test_to_dict(self):
        """Test metrics serialization to dict."""
        from src.observability.snapshot_delta import SnapshotMetrics

        metrics = SnapshotMetrics(
            timestamp="2025-01-01 12:00:00",
            dirty_file_count=3,
            commits_ahead=5,
            commits_behind=0,
            quest_status="active",
            quest_title="Quest",
            import_failures=0,
            test_failures=0,
            agent_activity={},
        )

        result = metrics.to_dict()

        assert result["timestamp"] == "2025-01-01 12:00:00"
        assert result["dirty_file_count"] == 3

    def test_from_dict(self):
        """Test metrics deserialization from dict."""
        from src.observability.snapshot_delta import SnapshotMetrics

        data = {
            "timestamp": "2025-01-01 12:00:00",
            "dirty_file_count": 3,
            "commits_ahead": 5,
            "commits_behind": 0,
            "quest_status": "active",
            "quest_title": "Quest",
            "import_failures": 0,
            "test_failures": 0,
            "agent_activity": {"ollama": 2},
        }

        metrics = SnapshotMetrics.from_dict(data)

        assert metrics.timestamp == "2025-01-01 12:00:00"
        assert metrics.agent_activity["ollama"] == 2


# =============================================================================
# SnapshotDelta Tests
# =============================================================================


class TestSnapshotDelta:
    """Test SnapshotDelta dataclass."""

    def test_to_markdown_basic(self):
        """Test delta rendering to markdown."""
        from src.observability.snapshot_delta import SnapshotDelta

        delta = SnapshotDelta(
            previous_timestamp="2025-01-01 12:00:00",
            current_timestamp="2025-01-01 14:00:00",
            time_delta_hours=2.0,
            dirty_file_delta=3,
            commits_ahead_delta=5,
            quest_changed=False,
            import_failures_delta=-2,
            test_failures_delta=0,
            agent_activity_delta={},
            insights=["Test insight"],
        )

        md = delta.to_markdown()

        assert "## Snapshot Delta" in md
        assert "2025-01-01 12:00:00" in md
        assert "2.0 hours" in md

    def test_to_markdown_dirty_increase(self):
        """Test markdown shows dirty file increase."""
        from src.observability.snapshot_delta import SnapshotDelta

        delta = SnapshotDelta(
            previous_timestamp="t1",
            current_timestamp="t2",
            time_delta_hours=1.0,
            dirty_file_delta=5,
            commits_ahead_delta=0,
            quest_changed=False,
            import_failures_delta=0,
            test_failures_delta=0,
            agent_activity_delta={},
            insights=[],
        )

        md = delta.to_markdown()

        assert "↑" in md
        assert "5" in md

    def test_to_markdown_dirty_decrease(self):
        """Test markdown shows dirty file decrease."""
        from src.observability.snapshot_delta import SnapshotDelta

        delta = SnapshotDelta(
            previous_timestamp="t1",
            current_timestamp="t2",
            time_delta_hours=1.0,
            dirty_file_delta=-3,
            commits_ahead_delta=0,
            quest_changed=False,
            import_failures_delta=0,
            test_failures_delta=0,
            agent_activity_delta={},
            insights=[],
        )

        md = delta.to_markdown()

        assert "↓" in md
        assert "3" in md

    def test_to_markdown_quest_changed(self):
        """Test markdown shows quest change."""
        from src.observability.snapshot_delta import SnapshotDelta

        delta = SnapshotDelta(
            previous_timestamp="t1",
            current_timestamp="t2",
            time_delta_hours=1.0,
            dirty_file_delta=0,
            commits_ahead_delta=0,
            quest_changed=True,
            import_failures_delta=0,
            test_failures_delta=0,
            agent_activity_delta={},
            insights=[],
        )

        md = delta.to_markdown()

        assert "CHANGED" in md

    def test_to_markdown_import_failures_improved(self):
        """Test markdown shows import improvement."""
        from src.observability.snapshot_delta import SnapshotDelta

        delta = SnapshotDelta(
            previous_timestamp="t1",
            current_timestamp="t2",
            time_delta_hours=1.0,
            dirty_file_delta=0,
            commits_ahead_delta=0,
            quest_changed=False,
            import_failures_delta=-5,
            test_failures_delta=0,
            agent_activity_delta={},
            insights=[],
        )

        md = delta.to_markdown()

        assert "BETTER" in md

    def test_to_markdown_import_failures_worsened(self):
        """Test markdown shows import regression."""
        from src.observability.snapshot_delta import SnapshotDelta

        delta = SnapshotDelta(
            previous_timestamp="t1",
            current_timestamp="t2",
            time_delta_hours=1.0,
            dirty_file_delta=0,
            commits_ahead_delta=0,
            quest_changed=False,
            import_failures_delta=3,
            test_failures_delta=0,
            agent_activity_delta={},
            insights=[],
        )

        md = delta.to_markdown()

        assert "WORSE" in md

    def test_to_markdown_agent_activity(self):
        """Test markdown shows agent activity."""
        from src.observability.snapshot_delta import SnapshotDelta

        delta = SnapshotDelta(
            previous_timestamp="t1",
            current_timestamp="t2",
            time_delta_hours=1.0,
            dirty_file_delta=0,
            commits_ahead_delta=0,
            quest_changed=False,
            import_failures_delta=0,
            test_failures_delta=0,
            agent_activity_delta={"ollama": 5, "copilot": 3},
            insights=[],
        )

        md = delta.to_markdown()

        assert "Agent Activity" in md
        assert "ollama" in md

    def test_to_markdown_insights(self):
        """Test markdown shows insights."""
        from src.observability.snapshot_delta import SnapshotDelta

        delta = SnapshotDelta(
            previous_timestamp="t1",
            current_timestamp="t2",
            time_delta_hours=1.0,
            dirty_file_delta=0,
            commits_ahead_delta=0,
            quest_changed=False,
            import_failures_delta=0,
            test_failures_delta=0,
            agent_activity_delta={},
            insights=["Insight 1", "Insight 2"],
        )

        md = delta.to_markdown()

        assert "### Insights" in md
        assert "Insight 1" in md
        assert "Insight 2" in md


# =============================================================================
# SnapshotDeltaTracker Initialization Tests
# =============================================================================


class TestSnapshotDeltaTrackerInit:
    """Test SnapshotDeltaTracker initialization."""

    def test_init_creates_history_dir(self, tmp_path):
        """Test that init creates history directory."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        assert tracker.history_dir.exists()
        assert tracker.history_dir == tmp_path / "state" / "snapshot_history"

    def test_init_sets_file_paths(self, tmp_path):
        """Test that init sets file paths correctly."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        assert tracker.current_file == tracker.history_dir / "current.json"
        assert tracker.history_file == tracker.history_dir / "history.jsonl"


# =============================================================================
# Save and Load Snapshot Tests
# =============================================================================


class TestSaveLoadSnapshot:
    """Test snapshot save and load operations."""

    def test_save_snapshot(self, tmp_path):
        """Test saving a snapshot."""
        from src.observability.snapshot_delta import (
            SnapshotDeltaTracker,
            SnapshotMetrics,
        )

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        metrics = SnapshotMetrics(
            timestamp="2025-01-01 12:00:00",
            dirty_file_count=3,
            commits_ahead=5,
            commits_behind=0,
            quest_status="active",
            quest_title="Quest",
            import_failures=0,
            test_failures=0,
            agent_activity={},
        )

        tracker.save_snapshot(metrics)

        assert tracker.current_file.exists()
        assert tracker.history_file.exists()

    def test_save_snapshot_appends_to_history(self, tmp_path):
        """Test that saving appends to history."""
        from src.observability.snapshot_delta import (
            SnapshotDeltaTracker,
            SnapshotMetrics,
        )

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        metrics1 = SnapshotMetrics(
            timestamp="2025-01-01 12:00:00",
            dirty_file_count=3,
            commits_ahead=5,
            commits_behind=0,
            quest_status="active",
            quest_title="Quest 1",
            import_failures=0,
            test_failures=0,
            agent_activity={},
        )

        metrics2 = SnapshotMetrics(
            timestamp="2025-01-01 13:00:00",
            dirty_file_count=4,
            commits_ahead=6,
            commits_behind=0,
            quest_status="active",
            quest_title="Quest 2",
            import_failures=0,
            test_failures=0,
            agent_activity={},
        )

        tracker.save_snapshot(metrics1)
        tracker.save_snapshot(metrics2)

        lines = tracker.history_file.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_load_previous_snapshot(self, tmp_path):
        """Test loading previous snapshot."""
        from src.observability.snapshot_delta import (
            SnapshotDeltaTracker,
            SnapshotMetrics,
        )

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        metrics = SnapshotMetrics(
            timestamp="2025-01-01 12:00:00",
            dirty_file_count=3,
            commits_ahead=5,
            commits_behind=0,
            quest_status="active",
            quest_title="Test Quest",
            import_failures=0,
            test_failures=0,
            agent_activity={"ollama": 2},
        )

        tracker.save_snapshot(metrics)

        loaded = tracker.load_previous_snapshot()

        assert loaded is not None
        assert loaded.quest_title == "Test Quest"
        assert loaded.agent_activity["ollama"] == 2

    def test_load_previous_no_history(self, tmp_path):
        """Test loading when no history exists."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        result = tracker.load_previous_snapshot()

        assert result is None

    def test_load_previous_corrupt_file(self, tmp_path):
        """Test loading with corrupt file returns None."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        tracker.current_file.write_text("not valid json")

        result = tracker.load_previous_snapshot()

        assert result is None


# =============================================================================
# Compute Delta Tests
# =============================================================================


class TestComputeDelta:
    """Test compute_delta method."""

    def create_metrics(self, **overrides):
        """Helper to create metrics with defaults."""
        from src.observability.snapshot_delta import SnapshotMetrics

        defaults = {
            "timestamp": "2025-01-01 12:00:00",
            "dirty_file_count": 0,
            "commits_ahead": 0,
            "commits_behind": 0,
            "quest_status": "active",
            "quest_title": "Quest",
            "import_failures": 0,
            "test_failures": 0,
            "agent_activity": {},
        }
        defaults.update(overrides)
        return SnapshotMetrics(**defaults)

    def test_compute_delta_basic(self, tmp_path):
        """Test basic delta computation."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        prev = self.create_metrics(
            timestamp="2025-01-01 12:00:00",
            dirty_file_count=5,
            commits_ahead=10,
        )
        curr = self.create_metrics(
            timestamp="2025-01-01 14:00:00",
            dirty_file_count=8,
            commits_ahead=15,
        )

        delta = tracker.compute_delta(prev, curr)

        assert delta.dirty_file_delta == 3
        assert delta.commits_ahead_delta == 5
        assert delta.time_delta_hours == 2.0

    def test_compute_delta_quest_changed(self, tmp_path):
        """Test delta detects quest change."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        prev = self.create_metrics(quest_title="Quest A")
        curr = self.create_metrics(timestamp="2025-01-01 13:00:00", quest_title="Quest B")

        delta = tracker.compute_delta(prev, curr)

        assert delta.quest_changed is True

    def test_compute_delta_import_improvement(self, tmp_path):
        """Test delta shows import improvement."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        prev = self.create_metrics(import_failures=10)
        curr = self.create_metrics(timestamp="2025-01-01 13:00:00", import_failures=5)

        delta = tracker.compute_delta(prev, curr)

        assert delta.import_failures_delta == -5
        assert any("improved" in i.lower() for i in delta.insights)

    def test_compute_delta_agent_activity(self, tmp_path):
        """Test delta shows agent activity changes."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        prev = self.create_metrics(agent_activity={"ollama": 5})
        curr = self.create_metrics(
            timestamp="2025-01-01 13:00:00", agent_activity={"ollama": 10, "copilot": 3}
        )

        delta = tracker.compute_delta(prev, curr)

        assert delta.agent_activity_delta["ollama"] == 5
        assert delta.agent_activity_delta["copilot"] == 3

    def test_compute_delta_insights_commits(self, tmp_path):
        """Test delta generates commit velocity insight."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        prev = self.create_metrics(commits_ahead=0)
        curr = self.create_metrics(timestamp="2025-01-01 14:00:00", commits_ahead=10)

        delta = tracker.compute_delta(prev, curr)

        assert any("velocity" in i.lower() for i in delta.insights)

    def test_compute_delta_stalled_insight(self, tmp_path):
        """Test delta generates stalled insight."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        # More than 24 hours, no commits
        prev = self.create_metrics(commits_ahead=5)
        curr = self.create_metrics(
            timestamp="2025-01-02 14:00:00",  # 26 hours later
            commits_ahead=5,
        )

        delta = tracker.compute_delta(prev, curr)

        assert any("stalled" in i.lower() for i in delta.insights)

    def test_compute_delta_quest_completed(self, tmp_path):
        """Test delta shows quest completion."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        prev = self.create_metrics(quest_status="active", quest_title="My Quest")
        curr = self.create_metrics(
            timestamp="2025-01-01 13:00:00", quest_status="completed", quest_title="My Quest"
        )

        delta = tracker.compute_delta(prev, curr)

        assert delta.quest_changed is True
        assert any("completed" in i.lower() for i in delta.insights)


# =============================================================================
# Trend Summary Tests
# =============================================================================


class TestTrendSummary:
    """Test get_trend_summary method."""

    def test_no_history(self, tmp_path):
        """Test trends with no history."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        result = tracker.get_trend_summary()

        assert "No historical data" in result[0]

    def test_empty_history_file(self, tmp_path):
        """Test trends with empty history file."""
        from src.observability.snapshot_delta import SnapshotDeltaTracker

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        tracker.history_file.write_text("")

        result = tracker.get_trend_summary()

        assert "No historical snapshots" in result[0]

    def test_insufficient_snapshots(self, tmp_path):
        """Test trends with only one snapshot."""
        from src.observability.snapshot_delta import (
            SnapshotDeltaTracker,
            SnapshotMetrics,
        )

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        # Create one recent snapshot
        now = datetime.now().isoformat()
        metrics = SnapshotMetrics(
            timestamp=now,
            dirty_file_count=0,
            commits_ahead=0,
            commits_behind=0,
            quest_status="active",
            quest_title="Quest",
            import_failures=0,
            test_failures=0,
            agent_activity={},
        )
        tracker.save_snapshot(metrics)

        result = tracker.get_trend_summary()

        assert "snapshot" in result[0].lower()

    def test_trends_with_snapshots(self, tmp_path):
        """Test trends with multiple snapshots."""
        from src.observability.snapshot_delta import (
            SnapshotDeltaTracker,
            SnapshotMetrics,
        )

        tracker = SnapshotDeltaTracker(hub_path=tmp_path)

        now = datetime.now()

        # Create multiple snapshots within window
        for i in range(3):
            timestamp = (now - timedelta(hours=i)).isoformat()
            metrics = SnapshotMetrics(
                timestamp=timestamp,
                dirty_file_count=0,
                commits_ahead=i * 5,
                commits_behind=0,
                quest_status="active",
                quest_title="Quest",
                import_failures=10 - i,
                test_failures=0,
                agent_activity={},
            )
            with open(tracker.history_file, "a") as f:
                f.write(json.dumps(metrics.to_dict()) + "\n")

        result = tracker.get_trend_summary()

        assert len(result) > 1
        assert any("snapshots" in r for r in result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
