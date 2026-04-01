"""Async Task Wrapper - Prevents Softlock in Task Execution.

========================================================

Provides timeout-aware, output-capturing wrappers for VS Code tasks
and terminal commands to prevent workflow stalls.

ANTI-SOFTLOCK PATTERNS:
1. Always set timeouts (default 60s)
2. Actively poll for completion
3. Return partial results on timeout
4. Log all state transitions
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskState(Enum):
    """Task execution states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    FAILED = "failed"


@dataclass
class TaskResult:
    """Structured task result with metadata."""

    state: TaskState
    output: str
    duration: float
    exit_code: int | None = None
    error: str | None = None


class AsyncTaskExecutor:
    """Executes VS Code tasks with timeout and active polling.

    Prevents softlocks by:
    - Setting reasonable timeouts
    - Polling for completion instead of blocking
    - Returning partial results
    - Comprehensive logging
    """

    def __init__(self, default_timeout: float = 60.0) -> None:
        self.default_timeout = default_timeout
        self.active_tasks: dict[str, float] = {}

    async def run_task_with_timeout(
        self, task_id: str, workspace_folder: str = "", timeout: float | None = None
    ) -> TaskResult:
        """Run a VS Code task with active polling and timeout.

        Args:
            task_id: Task identifier from tasks.json
            workspace_folder: Workspace folder path (unused in current implementation)
            timeout: Custom timeout in seconds (uses default if None)

        Returns:
            TaskResult with state and output
        """
        _ = workspace_folder  # Currently unused, reserved for future VS Code integration
        timeout = timeout or self.default_timeout
        start_time = time.time()
        self.active_tasks[task_id] = start_time

        logger.info(f"🚀 Starting task '{task_id}' (timeout: {timeout}s)")

        try:
            # Initiate task (would use run_task tool in real implementation)
            # This is a template - actual VS Code API integration needed

            # Poll for completion with timeout
            poll_interval = 1.0  # Poll every second
            elapsed = 0.0

            while elapsed < timeout:
                await asyncio.sleep(poll_interval)
                elapsed = time.time() - start_time

                # Check task status (would use get_task_output tool)
                # Placeholder for demonstration
                task_output = self._check_task_output()

                if task_output.get("completed", False):
                    duration = time.time() - start_time
                    logger.info(f"✅ Task '{task_id}' completed in {duration:.2f}s")
                    return TaskResult(
                        state=TaskState.COMPLETED,
                        output=task_output.get("output", ""),
                        duration=duration,
                        exit_code=task_output.get("exit_code", 0),
                    )

            # Timeout reached
            duration = time.time() - start_time
            logger.warning(f"⏱️ Task '{task_id}' timed out after {duration:.2f}s")
            return TaskResult(
                state=TaskState.TIMEOUT,
                output="Task exceeded timeout limit",
                duration=duration,
                error=f"Timeout after {timeout}s",
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            duration = time.time() - start_time
            logger.error(f"❌ Task '{task_id}' failed: {e}")
            return TaskResult(
                state=TaskState.FAILED,
                output="",
                duration=duration,
                error=str(e),
            )
        finally:
            self.active_tasks.pop(task_id, None)

    def _check_task_output(self) -> dict[str, Any]:
        """Placeholder for task output checking.

        In real implementation, would use get_task_output tool.
        """
        # This would integrate with VS Code's task API
        return {"completed": False, "output": "", "exit_code": None}

    async def run_multiple_tasks(
        self, tasks: list[tuple[str, str]], timeout: float | None = None
    ) -> list[TaskResult]:
        """Run multiple tasks concurrently with timeout.

        Args:
            tasks: List of (task_id, workspace_folder) tuples
            timeout: Timeout for each task

        Returns:
            List of TaskResult objects
        """
        logger.info(f"🔄 Running {len(tasks)} tasks concurrently")

        # Run tasks concurrently
        results = await asyncio.gather(
            *[
                self.run_task_with_timeout(task_id, workspace, timeout)
                for task_id, workspace in tasks
            ],
            return_exceptions=True,
        )

        # Convert exceptions to TaskResult
        final_results = []
        for res in results:
            if isinstance(res, Exception):
                final_results.append(
                    TaskResult(
                        state=TaskState.FAILED,
                        output="",
                        duration=0.0,
                        error=str(res),
                    )
                )
            else:
                final_results.append(res)

        return final_results


# Convenience function for synchronous contexts
def run_task_safe(task_id: str, workspace_folder: str, timeout: float = 60.0) -> TaskResult:
    """Synchronous wrapper for async task execution.

    Use this in non-async contexts.
    """
    executor = AsyncTaskExecutor(default_timeout=timeout)
    return asyncio.run(executor.run_task_with_timeout(task_id, workspace_folder))


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    result = run_task_safe(
        "shell: NuSyQ-Hub: Quick Pytest",
        "c:\\Users\\keath\\Desktop\\Legacy\\NuSyQ-Hub",
        timeout=30.0,
    )
    logger.info(f"Task completed with state: {result.state}")
    logger.info(f"Output: {result.output}")
