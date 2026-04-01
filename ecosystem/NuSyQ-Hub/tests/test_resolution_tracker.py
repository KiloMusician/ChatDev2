"""Tests for src/analytics/resolution_tracker.py — IssueRecord, ResolutionTracker."""

from unittest.mock import patch

import pytest


class TestIssueStatus:
    """Tests for IssueStatus enum."""

    def test_has_detected(self):
        from src.analytics.resolution_tracker import IssueStatus
        assert IssueStatus.DETECTED.value == "detected"

    def test_has_resolved(self):
        from src.analytics.resolution_tracker import IssueStatus
        assert IssueStatus.RESOLVED is not None

    def test_enum_count(self):
        from src.analytics.resolution_tracker import IssueStatus
        assert len(list(IssueStatus)) >= 4


class TestIssueRecord:
    """Tests for IssueRecord dataclass."""

    @pytest.fixture
    def record(self):
        from src.analytics.resolution_tracker import IssueRecord, IssueStatus
        return IssueRecord(
            issue_id="test-001",
            issue_type="lint_error",
            description="Unused import",
            file_path="src/foo.py",
            severity="low",
            detected_at="2026-01-01T00:00:00",
            detected_in_cycle=1,
        )

    def test_fields(self, record):
        assert record.issue_id == "test-001"
        assert record.issue_type == "lint_error"
        assert record.severity == "low"

    def test_default_status(self, record):
        from src.analytics.resolution_tracker import IssueStatus
        assert record.status == IssueStatus.DETECTED.value

    def test_to_dict(self, record):
        d = record.to_dict()
        assert isinstance(d, dict)
        assert d["issue_id"] == "test-001"
        assert "status" in d
        assert "status_history" in d

    def test_from_dict_roundtrip(self, record):
        from src.analytics.resolution_tracker import IssueRecord
        d = record.to_dict()
        restored = IssueRecord.from_dict(d)
        assert restored.issue_id == record.issue_id
        assert restored.issue_type == record.issue_type
        assert restored.severity == record.severity


class TestResolutionMetrics:
    """Tests for ResolutionMetrics dataclass."""

    def test_defaults(self):
        from src.analytics.resolution_tracker import ResolutionMetrics
        m = ResolutionMetrics()
        assert m.total_detected == 0
        assert m.total_resolved == 0
        assert m.resolution_rate == 0.0
        assert m.by_issue_type == {}

    def test_custom(self):
        from src.analytics.resolution_tracker import ResolutionMetrics
        m = ResolutionMetrics(total_detected=10, total_resolved=8, resolution_rate=0.8)
        assert m.total_detected == 10
        assert m.resolution_rate == 0.8


class TestResolutionTracker:
    """Tests for ResolutionTracker with patched DB paths."""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create ResolutionTracker that reads/writes to tmp_path."""
        import src.analytics.resolution_tracker as rt_mod
        with (
            patch.object(rt_mod, "ISSUES_DB", tmp_path / "issues.jsonl"),
            patch.object(rt_mod, "RESOLUTIONS_DB", tmp_path / "resolutions.jsonl"),
            patch.object(rt_mod, "_tracker_instance", None),
        ):
            from src.analytics.resolution_tracker import ResolutionTracker
            yield ResolutionTracker()

    def test_instantiation(self, tracker):
        assert tracker is not None

    def test_empty_on_init(self, tracker):
        assert tracker.issues == {}

    def test_register_detected_issue(self, tracker):
        record = tracker.register_detected_issue(
            issue_id="i1",
            issue_type="mypy_error",
            description="Type mismatch",
            file_path="src/foo.py",
            severity="medium",
            cycle_num=1,
        )
        assert record.issue_id == "i1"
        assert "i1" in tracker.issues

    def test_mark_routed(self, tracker):
        tracker.register_detected_issue("i2", "lint", "desc", "f.py", "low", 1)
        result = tracker.mark_routed("i2", agent="ollama")
        assert result is True
        assert tracker.issues["i2"].routed_to_agent == "ollama"

    def test_mark_routed_missing_returns_false(self, tracker):
        result = tracker.mark_routed("nonexistent", "ollama")
        assert result is False

    def test_mark_in_progress(self, tracker):
        from src.analytics.resolution_tracker import IssueStatus
        tracker.register_detected_issue("i3", "lint", "desc", "f.py", "low", 1)
        result = tracker.mark_in_progress("i3")
        assert result is True
        assert tracker.issues["i3"].status == IssueStatus.IN_PROGRESS.value

    def test_mark_resolved(self, tracker):
        from src.analytics.resolution_tracker import IssueStatus
        tracker.register_detected_issue("i4", "lint", "desc", "f.py", "low", 1)
        result = tracker.mark_resolved("i4", fix_code="removed import", success=True)
        assert result is True
        assert tracker.issues["i4"].status == IssueStatus.RESOLVED.value
        assert tracker.issues["i4"].fix_success is True

    def test_mark_resolved_missing_returns_false(self, tracker):
        result = tracker.mark_resolved("nope", fix_code="x", success=True)
        assert result is False

    def test_get_metrics_empty(self, tracker):
        from src.analytics.resolution_tracker import ResolutionMetrics
        metrics = tracker.get_metrics()
        assert isinstance(metrics, ResolutionMetrics)
        assert metrics.total_detected == 0

    def test_get_metrics_after_issues(self, tracker):
        from src.analytics.resolution_tracker import ResolutionMetrics
        tracker.register_detected_issue("a", "lint", "d", "f.py", "low", 1)
        tracker.register_detected_issue("b", "mypy", "d", "g.py", "high", 1)
        tracker.mark_resolved("a", fix_code="fix", success=True)
        metrics = tracker.get_metrics()
        assert isinstance(metrics, ResolutionMetrics)
        assert metrics.total_detected == 2
        assert metrics.total_resolved == 1

    def test_get_regression_count_returns_int(self, tracker):
        count = tracker.get_regression_count(hours=24)
        assert isinstance(count, int)
        assert count >= 0
