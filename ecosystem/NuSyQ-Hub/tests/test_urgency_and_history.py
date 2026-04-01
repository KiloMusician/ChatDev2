"""Tests for urgency scoring and history retention in aggregators.

Validates:
- Urgency score computation reflects severity weights
- History JSONL files are created and trimmed to retention limit
- Delta structures include urgency scores
- Insights adapter exposes urgency and history data
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from src.orchestration.insights_adapter import _load_history
from src.tools.multi_repo_aggregator import (
    MultiRepoAggregated,
    RepoInsights,
    _append_multi_history,
    _compute_cross_repo_urgency,
)
from src.tools.report_aggregator import (
    AggregatedInsights,
    SeverityCounts,
    append_history,
    compute_delta,
)


@pytest.fixture
def sample_insights() -> AggregatedInsights:
    """Create sample insights with known severity counts."""
    return AggregatedInsights(
        generated_at="2025-01-01T00:00:00Z",
        action_plan_present=True,
        issue_stubs_present=True,
        features_doc_present=True,
        summary_json_present=True,
        latest_session_log=None,
        latest_session_log_path=None,
        total_session_logs=10,
        action_plan_counts=SeverityCounts(critical=2, high=5, medium=10, low=3, info=1),
        issue_stub_counts=SeverityCounts(critical=1, high=3, medium=8, low=2, info=0),
        prioritized_next_actions=["Test action"],
        missing_components=[],
        notes=["Test note"],
    )


@pytest.fixture
def sample_multi_repo() -> MultiRepoAggregated:
    """Create sample multi-repo aggregated data."""
    repo1 = RepoInsights(
        name="TestRepo1",
        path="/test/repo1",
        action_plan_present=True,
        issue_stubs_present=True,
        features_doc_present=True,
        scan_summary_present=True,
        action_plan_counts=SeverityCounts(critical=1, high=2, medium=3),
        issue_stub_counts=SeverityCounts(critical=1, high=1, medium=2),
        missing=[],
    )
    return MultiRepoAggregated(
        generated_at="2025-01-01T00:00:00Z",
        repos=[repo1],
        cross_repo={
            "total_action_plan_counts": {
                "critical": 1,
                "high": 2,
                "medium": 3,
                "low": 0,
                "info": 0,
            },
            "total_issue_stub_counts": {
                "critical": 1,
                "high": 1,
                "medium": 2,
                "low": 0,
                "info": 0,
            },
            "prioritized_next_actions": ["Test"],
            "repos_missing_artifacts": {},
        },
    )


def test_single_repo_urgency_scoring(sample_insights: AggregatedInsights) -> None:
    """Test that urgency score reflects severity weights correctly."""
    delta = compute_delta(sample_insights, None)
    urgency = delta["urgency_score"]

    # Expected: action_critical*100 + issue_critical*90 + (action_high+issue_high)*40 + (action_medium+issue_medium)*10
    # = 2*100 + 1*90 + (5+3)*40 + (10+8)*10 = 200 + 90 + 320 + 180 = 790
    expected_base = 2 * 100 + 1 * 90 + (5 + 3) * 40 + (10 + 8) * 10
    assert urgency >= expected_base  # May include artifact/session factors
    assert isinstance(urgency, int)


def test_urgency_with_missing_artifacts(sample_insights: AggregatedInsights) -> None:
    """Test urgency increases with newly missing artifacts."""
    sample_insights.missing_components = ["test_artifact"]
    previous = sample_insights.to_dict()
    previous["missing_components"] = []

    delta = compute_delta(sample_insights, previous)
    # Should have penalty for newly missing artifact (25 points)
    assert delta["urgency_score"] > 0
    assert "test_artifact" in delta["newly_missing_artifacts"]


def test_history_append_and_trim(sample_insights: AggregatedInsights, tmp_path: Path) -> None:
    """Test history JSONL appending and trimming to retention limit."""
    # Temporarily override HISTORY_FILE
    import src.tools.report_aggregator as ra

    original_history = ra.HISTORY_FILE
    test_history = tmp_path / "test_history.jsonl"
    ra.HISTORY_FILE = test_history

    try:
        delta = compute_delta(sample_insights, None)
        # Append multiple records
        for i in range(35):
            curr_insights = AggregatedInsights(
                generated_at=f"2025-01-01T{i:02d}:00:00Z",
                action_plan_present=sample_insights.action_plan_present,
                issue_stubs_present=sample_insights.issue_stubs_present,
                features_doc_present=sample_insights.features_doc_present,
                summary_json_present=sample_insights.summary_json_present,
                latest_session_log=None,
                latest_session_log_path=None,
                total_session_logs=sample_insights.total_session_logs,
                action_plan_counts=sample_insights.action_plan_counts,
                issue_stub_counts=sample_insights.issue_stub_counts,
                prioritized_next_actions=sample_insights.prioritized_next_actions,
                missing_components=sample_insights.missing_components,
                notes=sample_insights.notes,
            )
            delta["generated_at"] = curr_insights.generated_at
            append_history(curr_insights, delta, retention=30)

        # Check retention limit enforced
        lines = test_history.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 30

        # Verify parseable JSON
        for line in lines:
            record = json.loads(line)
            assert "ts" in record
            assert "urgency" in record
    finally:
        ra.HISTORY_FILE = original_history


def test_multi_repo_urgency_scoring(sample_multi_repo: MultiRepoAggregated) -> None:
    """Test multi-repo urgency computation with cross-repo factors."""
    urgency = _compute_cross_repo_urgency(sample_multi_repo, [], [])
    # Expected: action_crit*100 + issue_crit*90 + (action_high+issue_high)*40 + (action_med+issue_med)*10
    # = 1*100 + 1*90 + (2+1)*40 + (3+2)*10 = 100 + 90 + 120 + 50 = 360
    expected = 1 * 100 + 1 * 90 + (2 + 1) * 40 + (3 + 2) * 10
    assert urgency == expected
    assert isinstance(urgency, int)


def test_multi_repo_history_retention(
    sample_multi_repo: MultiRepoAggregated, tmp_path: Path
) -> None:
    """Test multi-repo history appending and retention."""
    import src.tools.multi_repo_aggregator as mra

    original_history = mra.HISTORY_FILE
    test_history = tmp_path / "test_multi_history.jsonl"
    mra.HISTORY_FILE = test_history

    try:
        # Append records with varying urgency
        for i in range(35):
            test_data = MultiRepoAggregated(
                generated_at=f"2025-01-{i + 1:02d}T00:00:00Z",
                repos=sample_multi_repo.repos,
                cross_repo=sample_multi_repo.cross_repo,
            )
            _append_multi_history(test_data, urgency=100 + i, retention=30)

        lines = test_history.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 30

        # Verify structure
        for line in lines:
            record = json.loads(line)
            assert "ts" in record
            assert "urgency" in record
            assert "repos_with_missing" in record
    finally:
        mra.HISTORY_FILE = original_history


def test_adapter_load_history(tmp_path: Path) -> None:
    """Test insights adapter history loading with tail limit."""
    test_file = tmp_path / "adapter_history.jsonl"
    records = [{"ts": f"2025-01-{i:02d}", "urgency": i * 10} for i in range(1, 11)]
    test_file.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")

    # Load last 5
    loaded = _load_history(test_file, tail=5)
    assert len(loaded) == 5
    assert loaded[0]["urgency"] == 60  # 6th record
    assert loaded[-1]["urgency"] == 100  # 10th record


def test_adapter_history_missing_file() -> None:
    """Test adapter handles missing history file gracefully."""
    nonexistent = Path("/tmp/nonexistent_history.jsonl")
    loaded = _load_history(nonexistent, tail=5)
    assert loaded == []
