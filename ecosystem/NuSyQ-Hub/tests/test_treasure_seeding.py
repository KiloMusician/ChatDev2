"""Tests for multi-repo treasure artifact seeding."""

from pathlib import Path

from src.tools.treasure_pipeline import (
    ACTION_PLAN_FILENAME,
    ISSUE_STUBS_FILENAME,
    seed_repo_artifacts,
)


def test_seed_repo_artifacts_creates_missing(tmp_path: Path):
    repo_root = tmp_path / "SampleRepo"
    repo_root.mkdir(parents=True)
    result: dict[str, dict[str, bool]] = seed_repo_artifacts(repo_root)  # type: ignore[assignment]
    created_map = result["created"]
    assert created_map[ACTION_PLAN_FILENAME] is True
    assert created_map[ISSUE_STUBS_FILENAME] is True
    # idempotent second run
    second = seed_repo_artifacts(repo_root)
    second_map = second["created"]
    assert second_map[ACTION_PLAN_FILENAME] is False
    assert second_map[ISSUE_STUBS_FILENAME] is False
