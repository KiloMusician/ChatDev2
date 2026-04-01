"""Tests for delta aggregation logic.

Focuses on compute_delta for single-repo aggregator and presence of multi-repo
delta artifacts after write_outputs.
"""

from pathlib import Path
from typing import Any

from src.tools.multi_repo_aggregator import aggregate_multi_repo, write_outputs
from src.tools.report_aggregator import (
    AggregatedInsights,
    SeverityCounts,
    compute_delta,
)


def _make_insights(
    action_counts: dict[str, int], issue_counts: dict[str, int], missing: list[str]
) -> AggregatedInsights:
    return AggregatedInsights(
        generated_at="2025-01-01T00:00:00Z",
        action_plan_present=True,
        issue_stubs_present=True,
        features_doc_present=True,
        summary_json_present=True,
        latest_session_log=None,
        latest_session_log_path=None,
        total_session_logs=5,
        action_plan_counts=SeverityCounts(**action_counts),
        issue_stub_counts=SeverityCounts(**issue_counts),
        prioritized_next_actions=["noop"],
        missing_components=missing,
        notes=[],
    )


def test_compute_delta_first_run():
    curr = _make_insights(
        {"critical": 1, "high": 2, "medium": 0, "low": 0, "info": 0},
        {"critical": 0, "high": 1, "medium": 0, "low": 0, "info": 0},
        [],
    )
    delta = compute_delta(curr, None)
    assert delta["first_run"] is True
    assert delta["action_plan_severity_delta"]["critical"] == 1
    assert delta["issue_stub_severity_delta"]["high"] == 1


def test_compute_delta_with_previous_changes():
    prev_snapshot: dict[str, Any] = {
        "generated_at": "2024-12-31T23:59:59Z",
        "action_plan_counts": {
            "critical": 2,
            "high": 1,
            "medium": 0,
            "low": 0,
            "info": 0,
        },
        "issue_stub_counts": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        },
        "missing_components": ["TREASURE_PIPELINE_FEATURES.md"],
        "total_session_logs": 4,
    }
    curr = _make_insights(
        {"critical": 3, "high": 1, "medium": 0, "low": 0, "info": 0},
        {"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
        [],
    )
    delta = compute_delta(curr, prev_snapshot)
    assert delta["first_run"] is False
    # critical increased by 1 in action plan
    assert delta["action_plan_severity_delta"]["critical"] == 1
    # issue critical increased from 0 to 1
    assert delta["issue_stub_severity_delta"]["critical"] == 1
    # recovered artifact
    assert "TREASURE_PIPELINE_FEATURES.md" in delta["recovered_artifacts"]
    # session logs delta
    assert delta["session_logs_delta"] == 1


def test_multi_repo_delta_file_written(tmp_path):
    # Run multi-repo aggregation and write outputs into temporary docs/Reports
    # by monkeypatching Path.cwd if necessary; simplest is to chdir temporarily.
    # However for simplicity we just invoke write_outputs which writes to repo root.
    data = aggregate_multi_repo()
    write_outputs(data, write_markdown=True, write_json=True)
    delta_file = Path("docs/Reports/multi_repo_aggregated_insights_delta.json")
    assert delta_file.exists(), "Delta JSON file should be created on write_outputs"
