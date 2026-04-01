# Auto-generated from task: bg_20260213_065402_a14d1630
# Prompt: Create pytest suite for BackgroundTaskOrchestrator submit_task dedup and queue stats behavior. Retur...

"""Auto-generated draft test.

Requires manual review before enabling in CI.
"""

import pytest

pytest.skip("Auto-generated draft test; enable after review.", allow_module_level=True)

# src/background_task_orchestrator/tests/test_dedup_queue_stats.py

from unittest.mock import patch

import pytest

from background_task_orchestrator.background_task_orchestrator import \
    BackgroundTaskOrchestrator


@pytest.fixture
def orchestrator():
    return BackgroundTaskOrchestrator()


def test_submit_task_dedup(orchestrator):
    with patch.object(orchestrator.task_queue, "add") as mock_add:
        task_id = "task123"
        result = orchestrator.submit_task(task_id)
        assert result
        mock_add.assert_called_once_with(task_id)


def test_submit_task_dedup_duplicate(orchestrator):
    with patch.object(orchestrator.task_queue, "add") as mock_add:
        task_id = "task123"
        orchestrator.submit_task(task_id)
        result = orchestrator.submit_task(task_id)
        assert not result
        mock_add.assert_called_once_with(task_id)


def test_get_queue_stats(orchestrator):
    with patch.object(orchestrator.task_queue, "size") as mock_size:
        mock_size.return_value = 5
        stats = orchestrator.get_queue_stats()
        assert stats == {"queue_size": 5}
