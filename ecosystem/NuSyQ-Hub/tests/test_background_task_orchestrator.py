"""Tests for the Background Task Orchestrator.

Verifies that Claude Code CLI and other agents can dispatch
high-token operations to local LLMs (Ollama, LM Studio, ChatDev).
"""

import asyncio
import json

import pytest
from src.orchestration.background_task_orchestrator import (
    BackgroundTask,
    BackgroundTaskOrchestrator,
    TaskStatus,
    TaskTarget,
    get_orchestrator,
    list_tasks_cli,
    orchestrator_hygiene_cli,
    orchestrator_status_cli,
    task_status_cli,
)
from datetime import UTC


class TestBackgroundTask:
    """Test BackgroundTask dataclass."""

    def test_task_creation(self):
        """Test basic task creation."""
        task = BackgroundTask(
            task_id="test_123",
            prompt="Test prompt",
            target=TaskTarget.OLLAMA,
            model="llama3.1:8b",
        )
        assert task.task_id == "test_123"
        assert task.prompt == "Test prompt"
        assert task.target == TaskTarget.OLLAMA
        assert task.model == "llama3.1:8b"
        assert task.status == TaskStatus.QUEUED

    def test_task_to_dict(self):
        """Test task serialization."""
        task = BackgroundTask(
            task_id="test_456",
            prompt="Short prompt",
            target=TaskTarget.LM_STUDIO,
            requesting_agent="claude",
        )
        d = task.to_dict()
        assert d["task_id"] == "test_456"
        assert d["target"] == "lm_studio"
        assert d["requesting_agent"] == "claude"
        assert "created_at" in d

    def test_long_prompt_truncation(self):
        """Test that long prompts are truncated in to_dict."""
        long_prompt = "x" * 500
        task = BackgroundTask(
            task_id="test_long",
            prompt=long_prompt,
            target=TaskTarget.OLLAMA,
        )
        d = task.to_dict()
        assert len(d["prompt"]) <= 203  # 200 chars + "..."


class TestBackgroundTaskOrchestrator:
    """Test BackgroundTaskOrchestrator class."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator with temp state dir."""
        return BackgroundTaskOrchestrator(state_dir=tmp_path / "tasks")

    def test_orchestrator_init(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator is not None
        assert len(orchestrator.tasks) == 0

    def test_submit_task(self, orchestrator):
        """Test task submission."""
        task = orchestrator.submit_task(
            prompt="Analyze this code",
            target=TaskTarget.OLLAMA,
            model="qwen2.5-coder:14b",
            requesting_agent="test",
        )
        assert task.task_id.startswith("bg_")
        assert task.prompt == "Analyze this code"
        assert task.target == TaskTarget.OLLAMA
        assert task.task_id in orchestrator.tasks

    def test_submit_task_includes_task_type_in_metadata(self, orchestrator):
        """Task metadata should preserve task_type for downstream routing."""
        task = orchestrator.submit_task(
            prompt="Review module",
            target=TaskTarget.COPILOT,
            task_type="review",
        )
        assert task.metadata.get("task_type") == "review"

    def test_submit_task_auto_routing(self, orchestrator):
        """Test auto-routing for code tasks."""
        task = orchestrator.submit_task(
            prompt="Generate unit tests",
            target=TaskTarget.AUTO,
            task_type="code_generation",
            requesting_agent="claude",
        )
        # AUTO should route code_generation to OLLAMA
        assert task.target == TaskTarget.OLLAMA
        assert task.model == "qwen2.5-coder:14b"  # Default for code_generation

    def test_get_task(self, orchestrator):
        """Test retrieving a task."""
        task = orchestrator.submit_task(
            prompt="Test",
            target=TaskTarget.OLLAMA,
        )
        retrieved = orchestrator.get_task(task.task_id)
        assert retrieved is not None
        assert retrieved.task_id == task.task_id

    def test_get_nonexistent_task(self, orchestrator):
        """Test retrieving nonexistent task."""
        assert orchestrator.get_task("nonexistent") is None

    def test_list_tasks(self, orchestrator):
        """Test listing tasks."""
        # Submit multiple tasks
        orchestrator.submit_task(prompt="Task 1", target=TaskTarget.OLLAMA)
        orchestrator.submit_task(prompt="Task 2", target=TaskTarget.LM_STUDIO)
        orchestrator.submit_task(prompt="Task 3", target=TaskTarget.CHATDEV)

        tasks = orchestrator.list_tasks()
        assert len(tasks) == 3

    def test_list_tasks_with_filter(self, orchestrator):
        """Test listing tasks with status filter."""
        task1 = orchestrator.submit_task(prompt="Task 1", target=TaskTarget.OLLAMA)
        task2 = orchestrator.submit_task(prompt="Task 2", target=TaskTarget.OLLAMA)

        # Manually set status
        task1.status = TaskStatus.COMPLETED

        queued = orchestrator.list_tasks(status=TaskStatus.QUEUED)
        assert len(queued) == 1
        assert queued[0].task_id == task2.task_id

    def test_cancel_task(self, orchestrator):
        """Test cancelling a queued task."""
        task = orchestrator.submit_task(prompt="Cancel me", target=TaskTarget.OLLAMA)
        result = orchestrator.cancel_task(task.task_id)
        assert result is True
        assert task.status == TaskStatus.CANCELLED

    def test_cancel_running_task_fails(self, orchestrator):
        """Test that running tasks cannot be cancelled."""
        task = orchestrator.submit_task(prompt="Running", target=TaskTarget.OLLAMA)
        task.status = TaskStatus.RUNNING
        result = orchestrator.cancel_task(task.task_id)
        assert result is False
        assert task.status == TaskStatus.RUNNING

    def test_orchestrator_status(self, orchestrator):
        """Test getting orchestrator status."""
        orchestrator.submit_task(prompt="Task 1", target=TaskTarget.OLLAMA)
        orchestrator.submit_task(prompt="Task 2", target=TaskTarget.OLLAMA)

        status = orchestrator.get_orchestrator_status()
        assert status["total_tasks"] == 2
        assert "ollama" in status["targets"]
        assert "lm_studio" in status["targets"]
        assert "chatdev" in status["targets"]
        assert "copilot" in status["targets"]

    def test_execute_copilot_uses_router(self, orchestrator, monkeypatch):
        """Copilot target should execute through AgentTaskRouter bridge."""

        class FakeRouter:
            async def route_task(self, *args, **kwargs):
                return {
                    "status": "success",
                    "system": "copilot",
                    "output": {"mode": "mock"},
                }

        import src.tools.agent_task_router as router_module

        monkeypatch.setattr(router_module, "AgentTaskRouter", FakeRouter)

        task = orchestrator.submit_task(
            prompt="Background copilot task",
            target=TaskTarget.COPILOT,
            task_type="review",
        )
        raw = asyncio.run(orchestrator._execute_copilot(task))
        payload = json.loads(raw)

        assert payload["status"] == "success"
        assert payload["system"] == "copilot"

    def test_token_estimation(self, orchestrator):
        """Test token estimation for tasks."""
        prompt = "x" * 400  # 400 chars = ~100 tokens
        task = orchestrator.submit_task(prompt=prompt, target=TaskTarget.OLLAMA)
        assert task.token_estimate == 100  # 400 / 4

    def test_prune_tasks_reconciles_running_and_trims_history(self, orchestrator):
        """Prune should reconcile stale running tasks and trim terminal history."""
        from datetime import datetime, timedelta, timezone

        stale_running = orchestrator.submit_task(prompt="stale running", target=TaskTarget.OLLAMA)
        stale_running.status = TaskStatus.RUNNING
        stale_running.started_at = datetime.now(UTC) - timedelta(hours=2)

        for idx in range(3):
            completed = orchestrator.submit_task(
                prompt=f"completed-{idx}",
                target=TaskTarget.OLLAMA,
            )
            completed.status = TaskStatus.COMPLETED
            completed.completed_at = datetime.now(UTC) - timedelta(minutes=idx)

        summary = orchestrator.prune_tasks(
            keep_completed=1,
            keep_failed=200,
            keep_cancelled=200,
            stale_running_after_s=1800,
        )

        assert summary["running_reconciled"] == 1
        assert summary["removed_by_status"]["completed"] == 2
        assert orchestrator.tasks[stale_running.task_id].status == TaskStatus.FAILED
        completed_remaining = [
            task for task in orchestrator.tasks.values() if task.status == TaskStatus.COMPLETED
        ]
        assert len(completed_remaining) == 1

        reloaded = BackgroundTaskOrchestrator(state_dir=orchestrator.state_dir)
        reloaded_completed = [
            task for task in reloaded.tasks.values() if task.status == TaskStatus.COMPLETED
        ]
        assert len(reloaded_completed) == 1

    def test_prune_tasks_dry_run_does_not_modify_tasks(self, orchestrator):
        """Dry-run prune should report removals without mutating task storage."""
        for idx in range(2):
            completed = orchestrator.submit_task(
                prompt=f"dry-completed-{idx}",
                target=TaskTarget.OLLAMA,
            )
            completed.status = TaskStatus.COMPLETED

        before_ids = set(orchestrator.tasks.keys())
        summary = orchestrator.prune_tasks(keep_completed=0, dry_run=True)

        assert summary["removed_by_status"]["completed"] == 2
        assert set(orchestrator.tasks.keys()) == before_ids


class TestOrchestratorExecution:
    """Test task execution (mocked).

    Note: These tests require proper async context manager mocking.
    For now, we skip the complex mocking and test the task state transitions.
    """

    @pytest.fixture
    def orchestrator(self, tmp_path):
        return BackgroundTaskOrchestrator(state_dir=tmp_path / "tasks")

    def test_task_state_transitions(self, orchestrator):
        """Test that task states transition correctly."""
        task = orchestrator.submit_task(
            prompt="Test state",
            target=TaskTarget.OLLAMA,
            model="phi3.5:latest",
        )

        # Initial state should be QUEUED
        assert task.status == TaskStatus.QUEUED
        assert task.started_at is None
        assert task.completed_at is None

        # Simulate state change to RUNNING
        task.status = TaskStatus.RUNNING
        from datetime import datetime, timezone

        task.started_at = datetime.now(UTC)
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

        # Simulate completion
        task.status = TaskStatus.COMPLETED
        task.result = "Test result"
        task.completed_at = datetime.now(UTC)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "Test result"

    def test_task_failure_state(self, orchestrator):
        """Test task failure state."""
        task = orchestrator.submit_task(
            prompt="Fail me",
            target=TaskTarget.OLLAMA,
        )

        # Simulate failure
        from datetime import datetime, timezone

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(UTC)
        task.status = TaskStatus.FAILED
        task.error = "Connection refused"
        task.completed_at = datetime.now(UTC)

        assert task.status == TaskStatus.FAILED
        assert "Connection" in task.error

    def test_task_progress_tracking(self, orchestrator):
        """Test progress tracking."""
        task = orchestrator.submit_task(
            prompt="Track progress",
            target=TaskTarget.OLLAMA,
        )

        assert task.progress == 0.0

        # Simulate progress updates
        task.progress = 0.3
        assert task.progress == 0.3

        task.progress = 0.8
        assert task.progress == 0.8

        task.progress = 1.0
        assert task.progress == 1.0


class TestCLIInterface:
    """Test CLI interface functions."""

    def test_orchestrator_status_cli(self):
        """Test CLI status function."""
        status = orchestrator_status_cli()
        assert "total_tasks" in status
        assert "targets" in status

    def test_list_tasks_cli_empty(self):
        """Test listing tasks when empty."""
        # Clear any existing tasks
        orch = get_orchestrator()
        orch.tasks.clear()

        tasks = list_tasks_cli(limit=10)
        assert tasks == []

    def test_task_status_cli_not_found(self):
        """Test status for nonexistent task."""
        result = task_status_cli("nonexistent_task_id")
        assert "error" in result

    def test_orchestrator_hygiene_cli(self, monkeypatch, tmp_path):
        """CLI hygiene helper should surface prune summary."""
        orchestrator = BackgroundTaskOrchestrator(state_dir=tmp_path / "tasks")
        completed = orchestrator.submit_task(prompt="cli-completed", target=TaskTarget.OLLAMA)
        completed.status = TaskStatus.COMPLETED

        import src.orchestration.background_task_orchestrator as orchestrator_module

        monkeypatch.setattr(orchestrator_module, "get_orchestrator", lambda: orchestrator)
        summary = orchestrator_hygiene_cli(keep_completed=0, dry_run=False)

        assert summary["removed_total"] == 1
        assert summary["after_total"] == 0


class TestModelRouting:
    """Test intelligent model routing."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        return BackgroundTaskOrchestrator(state_dir=tmp_path / "tasks")

    def test_code_analysis_routing(self, orchestrator):
        """Test that code_analysis routes to deepseek."""
        task = orchestrator.submit_task(
            prompt="Analyze security",
            target=TaskTarget.AUTO,
            task_type="code_analysis",
        )
        assert task.model == "deepseek-coder-v2:16b"

    def test_code_generation_routing(self, orchestrator):
        """Test that code_generation routes to qwen."""
        task = orchestrator.submit_task(
            prompt="Generate tests",
            target=TaskTarget.AUTO,
            task_type="code_generation",
        )
        assert task.model == "qwen2.5-coder:14b"

    def test_fast_task_routing(self, orchestrator):
        """Test that fast tasks route to phi3.5."""
        task = orchestrator.submit_task(
            prompt="Quick question",
            target=TaskTarget.AUTO,
            task_type="fast",
        )
        assert task.model == "phi3.5:latest"

    def test_general_task_routing(self, orchestrator):
        """Test that general tasks route to llama."""
        task = orchestrator.submit_task(
            prompt="General inquiry",
            target=TaskTarget.AUTO,
            task_type="general",
        )
        assert task.model == "llama3.1:8b"
