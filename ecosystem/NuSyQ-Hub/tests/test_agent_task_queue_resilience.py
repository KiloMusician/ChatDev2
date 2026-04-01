from __future__ import annotations

from datetime import datetime, timedelta

from src.orchestration.agent_task_queue import AgentTaskQueue, TaskPriority, TaskStatus, TaskType


def test_fail_task_schedules_retry_and_defers_pending(tmp_path) -> None:
    queue = AgentTaskQueue(queue_dir=tmp_path / "task_queue")
    queue.register_agent("agent-1", "Agent 1", ["code_fix"])
    queue.create_task(
        task_id="task-1",
        task_type=TaskType.CODE_FIX,
        title="Fix lint",
        description="Resolve lint issue",
        priority=TaskPriority.NORMAL,
        max_retries=2,
    )
    assert queue.assign_task("task-1", "agent-1")
    assert queue.start_task("task-1")
    assert queue.fail_task("task-1", "tool timeout")

    task = queue.get_task("task-1")
    assert task is not None
    assert task.status == TaskStatus.QUEUED
    assert task.retry_count == 1
    assert task.next_retry_at is not None
    assert task.last_error == "tool timeout"
    assert task.assigned_agent is None

    pending_ids = {t.task_id for t in queue.get_pending_tasks()}
    assert "task-1" not in pending_ids

    task.next_retry_at = (datetime.now() - timedelta(seconds=1)).isoformat()
    queue._save_task(task)
    pending_ids = {t.task_id for t in queue.get_pending_tasks()}
    assert "task-1" in pending_ids


def test_fail_task_exhausts_retries_to_failed(tmp_path) -> None:
    queue = AgentTaskQueue(queue_dir=tmp_path / "task_queue")
    queue.create_task(
        task_id="task-2",
        task_type=TaskType.TEST,
        title="Run tests",
        description="Execute suite",
        priority=TaskPriority.HIGH,
        max_retries=1,
    )

    assert queue.fail_task("task-2", "first failure")
    task = queue.get_task("task-2")
    assert task is not None
    assert task.status == TaskStatus.QUEUED
    assert task.retry_count == 1

    assert queue.fail_task("task-2", "second failure")
    task = queue.get_task("task-2")
    assert task is not None
    assert task.status == TaskStatus.FAILED
    assert task.next_retry_at is None
    assert task.last_error == "second failure"


def test_queue_status_reports_retry_waiting(tmp_path) -> None:
    queue = AgentTaskQueue(queue_dir=tmp_path / "task_queue")
    queue.create_task(
        task_id="task-3",
        task_type=TaskType.ANALYSIS,
        title="Analyze diagnostics",
        description="Inspect report",
        priority=TaskPriority.NORMAL,
        max_retries=2,
    )
    assert queue.fail_task("task-3", "temporary issue")

    status = queue.get_queue_status()
    assert status["retry_waiting"] == 1


def test_task_state_checkpoint_created_on_mutation(tmp_path) -> None:
    queue = AgentTaskQueue(queue_dir=tmp_path / "task_queue")
    queue.create_task(
        task_id="task-4",
        task_type=TaskType.DOCUMENTATION,
        title="Write notes",
        description="Update docs",
        priority=TaskPriority.LOW,
    )

    checkpoint_dir = tmp_path / "task_queue" / "checkpoints"
    checkpoint_files = list(checkpoint_dir.glob("*.json"))
    assert checkpoint_files, "expected task queue checkpoint files to be created"
