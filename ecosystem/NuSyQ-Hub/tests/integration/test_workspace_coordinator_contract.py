"""Contract tests for WorkspaceCoordinator task execution responses."""

from __future__ import annotations

import sys

import pytest
from src.orchestration.workspace_coordinator import WorkspaceCoordinator

pytestmark = [pytest.mark.integration]


def test_run_task_missing_returns_normalized_error(tmp_path) -> None:
    coordinator = WorkspaceCoordinator(hub_root=tmp_path)
    result = coordinator.run_task("missing_task")
    assert result["success"] is False
    assert result["status"] == "error"


def test_run_task_condition_false_returns_skipped_with_success_flag(tmp_path) -> None:
    coordinator = WorkspaceCoordinator(hub_root=tmp_path)
    coordinator.tasks["conditioned_task"] = {
        "condition": lambda: False,
        "args": [sys.executable, "-c", "print('skip')"],
    }
    result = coordinator.run_task("conditioned_task")
    assert result["success"] is False
    assert result["status"] == "skipped"


def test_run_task_success_and_failure_include_success_flag(tmp_path) -> None:
    coordinator = WorkspaceCoordinator(hub_root=tmp_path)
    coordinator.tasks["ok_task"] = {"args": [sys.executable, "-c", "print('ok')"]}
    coordinator.tasks["fail_task"] = {"args": [sys.executable, "-c", "import sys; sys.exit(3)"]}

    ok_result = coordinator.run_task("ok_task")
    assert ok_result["success"] is True
    assert ok_result["status"] == "success"
    assert ok_result["exit_code"] == 0

    fail_result = coordinator.run_task("fail_task")
    assert fail_result["success"] is False
    assert fail_result["status"] == "failed"
    assert fail_result["exit_code"] == 3
