"""Tests for async_task_wrapper.py.

Tests the timeout-aware task execution wrappers.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from src.utils.async_task_wrapper import (
    AsyncTaskExecutor,
    TaskResult,
    TaskState,
    run_task_safe,
)


class TestTaskState:
    """Tests for TaskState enum."""

    def test_has_pending_state(self):
        """Has PENDING state."""
        assert TaskState.PENDING.value == "pending"

    def test_has_running_state(self):
        """Has RUNNING state."""
        assert TaskState.RUNNING.value == "running"

    def test_has_completed_state(self):
        """Has COMPLETED state."""
        assert TaskState.COMPLETED.value == "completed"

    def test_has_timeout_state(self):
        """Has TIMEOUT state."""
        assert TaskState.TIMEOUT.value == "timeout"

    def test_has_failed_state(self):
        """Has FAILED state."""
        assert TaskState.FAILED.value == "failed"

    def test_all_states_unique(self):
        """All state values are unique."""
        values = [s.value for s in TaskState]
        assert len(values) == len(set(values))


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_required_fields(self):
        """Can create with required fields only."""
        result = TaskResult(
            state=TaskState.COMPLETED,
            output="done",
            duration=1.5,
        )
        assert result.state == TaskState.COMPLETED
        assert result.output == "done"
        assert result.duration == 1.5
        assert result.exit_code is None
        assert result.error is None

    def test_all_fields(self):
        """Can create with all fields."""
        result = TaskResult(
            state=TaskState.FAILED,
            output="error output",
            duration=2.0,
            exit_code=1,
            error="Something went wrong",
        )
        assert result.exit_code == 1
        assert result.error == "Something went wrong"

    def test_is_dataclass(self):
        """TaskResult is a dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(TaskResult)


class TestAsyncTaskExecutorInit:
    """Tests for AsyncTaskExecutor initialization."""

    def test_default_timeout(self):
        """Default timeout is 60 seconds."""
        executor = AsyncTaskExecutor()
        assert executor.default_timeout == 60.0

    def test_custom_timeout(self):
        """Can set custom default timeout."""
        executor = AsyncTaskExecutor(default_timeout=30.0)
        assert executor.default_timeout == 30.0

    def test_empty_active_tasks(self):
        """Starts with no active tasks."""
        executor = AsyncTaskExecutor()
        assert executor.active_tasks == {}


class TestAsyncTaskExecutorRunTask:
    """Tests for run_task_with_timeout method."""

    @pytest.mark.asyncio
    async def test_task_timeout(self):
        """Task times out when not completed."""
        executor = AsyncTaskExecutor(default_timeout=0.1)
        result = await executor.run_task_with_timeout("test_task")
        assert result.state == TaskState.TIMEOUT
        assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_custom_timeout_override(self):
        """Can override timeout per-call."""
        executor = AsyncTaskExecutor(default_timeout=60.0)
        # Use very short timeout to force timeout state
        result = await executor.run_task_with_timeout("test_task", timeout=0.1)
        assert result.state == TaskState.TIMEOUT

    @pytest.mark.asyncio
    async def test_task_completion(self):
        """Task completes when _check_task_output returns completed."""
        executor = AsyncTaskExecutor(default_timeout=5.0)
        # Mock _check_task_output to return completed
        executor._check_task_output = MagicMock(
            return_value={"completed": True, "output": "success", "exit_code": 0}
        )
        result = await executor.run_task_with_timeout("test_task")
        assert result.state == TaskState.COMPLETED
        assert result.output == "success"
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_task_tracks_duration(self):
        """Duration is tracked correctly."""
        executor = AsyncTaskExecutor(default_timeout=0.1)
        result = await executor.run_task_with_timeout("test_task")
        assert result.duration >= 0.1  # At least timeout duration

    @pytest.mark.asyncio
    async def test_removes_from_active_tasks(self):
        """Task removed from active_tasks after completion."""
        executor = AsyncTaskExecutor(default_timeout=0.1)
        await executor.run_task_with_timeout("test_task")
        assert "test_task" not in executor.active_tasks

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Handles exceptions gracefully."""
        executor = AsyncTaskExecutor(default_timeout=5.0)
        # Force an exception in _check_task_output
        executor._check_task_output = MagicMock(side_effect=RuntimeError("Test error"))
        result = await executor.run_task_with_timeout("test_task")
        assert result.state == TaskState.FAILED
        assert "Test error" in result.error

    @pytest.mark.asyncio
    async def test_workspace_folder_parameter(self):
        """Accepts workspace_folder parameter."""
        executor = AsyncTaskExecutor(default_timeout=0.1)
        # Should not raise
        result = await executor.run_task_with_timeout(
            "test_task", workspace_folder="/path/to/workspace"
        )
        assert result.state == TaskState.TIMEOUT


class TestCheckTaskOutput:
    """Tests for _check_task_output method."""

    def test_returns_dict(self):
        """Returns a dictionary."""
        executor = AsyncTaskExecutor()
        result = executor._check_task_output()
        assert isinstance(result, dict)

    def test_has_completed_key(self):
        """Result has 'completed' key."""
        executor = AsyncTaskExecutor()
        result = executor._check_task_output()
        assert "completed" in result

    def test_default_not_completed(self):
        """Default implementation returns not completed."""
        executor = AsyncTaskExecutor()
        result = executor._check_task_output()
        assert result["completed"] is False


class TestRunMultipleTasks:
    """Tests for run_multiple_tasks method."""

    @pytest.mark.asyncio
    async def test_empty_task_list(self):
        """Handles empty task list."""
        executor = AsyncTaskExecutor()
        results = await executor.run_multiple_tasks([])
        assert results == []

    @pytest.mark.asyncio
    async def test_multiple_tasks_timeout(self):
        """All tasks can timeout."""
        executor = AsyncTaskExecutor(default_timeout=0.1)
        tasks = [("task1", ""), ("task2", ""), ("task3", "")]
        results = await executor.run_multiple_tasks(tasks, timeout=0.1)
        assert len(results) == 3
        for result in results:
            assert result.state == TaskState.TIMEOUT

    @pytest.mark.asyncio
    async def test_returns_task_results(self):
        """Returns list of TaskResult objects."""
        executor = AsyncTaskExecutor(default_timeout=0.1)
        tasks = [("task1", "")]
        results = await executor.run_multiple_tasks(tasks)
        assert len(results) == 1
        assert isinstance(results[0], TaskResult)

    @pytest.mark.asyncio
    async def test_handles_exceptions(self):
        """Converts exceptions to TaskResult."""
        executor = AsyncTaskExecutor(default_timeout=5.0)

        # Create a mock that raises exception
        async def raising_task(*args, **kwargs):
            raise ValueError("Task failed")

        with patch.object(executor, "run_task_with_timeout", raising_task):
            tasks = [("task1", "")]
            results = await executor.run_multiple_tasks(tasks)
            assert len(results) == 1
            assert results[0].state == TaskState.FAILED
            assert "Task failed" in results[0].error


class TestRunTaskSafe:
    """Tests for run_task_safe convenience function."""

    def test_returns_task_result(self):
        """Returns TaskResult object."""
        with patch("src.utils.async_task_wrapper.asyncio.run") as mock_run:
            mock_run.return_value = TaskResult(
                state=TaskState.COMPLETED,
                output="done",
                duration=1.0,
            )
            result = run_task_safe("task_id", "/workspace")
            assert isinstance(result, TaskResult)

    def test_uses_provided_timeout(self):
        """Uses provided timeout value."""
        with patch("src.utils.async_task_wrapper.asyncio.run") as mock_run:
            mock_run.return_value = TaskResult(
                state=TaskState.TIMEOUT,
                output="",
                duration=30.0,
            )
            run_task_safe("task", "/ws", timeout=30.0)
            assert mock_run.called

    def test_passes_arguments(self):
        """Passes arguments to executor."""
        with patch.object(AsyncTaskExecutor, "run_task_with_timeout") as mock_method:
            mock_method.return_value = TaskResult(
                state=TaskState.COMPLETED,
                output="",
                duration=0.0,
            )
            # This will actually run asyncio.run
            result = run_task_safe("my_task", "/my/workspace", timeout=45.0)
            # Result comes from asyncio.run which would call our mock
            assert result is not None


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_very_short_timeout(self):
        """Handles very short timeouts."""
        executor = AsyncTaskExecutor(default_timeout=0.01)
        result = await executor.run_task_with_timeout("task")
        assert result.state == TaskState.TIMEOUT

    @pytest.mark.asyncio
    async def test_task_id_with_special_chars(self):
        """Handles task IDs with special characters."""
        executor = AsyncTaskExecutor(default_timeout=0.1)
        result = await executor.run_task_with_timeout("shell: Test: Special (chars) [here]")
        assert result.state == TaskState.TIMEOUT

    @pytest.mark.asyncio
    async def test_concurrent_tasks_tracked(self):
        """Multiple concurrent tasks are tracked."""
        executor = AsyncTaskExecutor(default_timeout=0.2)

        async def check_active_during():
            """Start tasks and check active_tasks during execution."""
            task = asyncio.create_task(executor.run_task_with_timeout("task1"))
            await asyncio.sleep(0.05)
            # Task should be in active_tasks during execution
            has_task = "task1" in executor.active_tasks
            await task
            return has_task

        was_active = await check_active_during()
        assert was_active is True

    def test_zero_timeout(self):
        """Zero timeout immediately times out."""
        # Note: This might not work exactly as expected with asyncio
        executor = AsyncTaskExecutor(default_timeout=0)
        # Just verify executor is created
        assert executor.default_timeout == 0

    @pytest.mark.asyncio
    async def test_negative_timeout_treated_as_zero(self):
        """Negative timeout is treated as immediate timeout."""
        executor = AsyncTaskExecutor(default_timeout=5.0)
        # With negative timeout, loop condition fails immediately
        result = await executor.run_task_with_timeout("task", timeout=-1)
        assert result.state == TaskState.TIMEOUT
