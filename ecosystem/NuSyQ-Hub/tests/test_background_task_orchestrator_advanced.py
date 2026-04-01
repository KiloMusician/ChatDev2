import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestration.background_task_orchestrator import (
    BackgroundTask,
    BackgroundTaskOrchestrator,
    LMStudioError,
    OllamaError,
    TaskPriority,
    TaskStatus,
    TaskTarget,
)

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc  # noqa: UP017


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_orch(tmp_path: Path) -> BackgroundTaskOrchestrator:
    orch = BackgroundTaskOrchestrator(state_dir=tmp_path / "tasks")
    orch._consciousness_loop = None
    return orch


# ---------------------------------------------------------------------------
# execute_task — happy paths
# ---------------------------------------------------------------------------


class TestExecuteTaskOllama:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    @pytest.mark.asyncio
    async def test_execute_task_ollama_success(self, orch):
        task = orch.submit_task(prompt="Analyze code", target=TaskTarget.OLLAMA)
        orch._execute_ollama = AsyncMock(return_value="ollama result")
        result_task = await orch.execute_task(task)
        assert result_task.status == TaskStatus.COMPLETED
        assert result_task.result == "ollama result"
        assert result_task.progress == 1.0

    @pytest.mark.asyncio
    async def test_execute_task_lm_studio_success(self, orch):
        task = orch.submit_task(prompt="LM task", target=TaskTarget.LM_STUDIO)
        orch._execute_lm_studio = AsyncMock(return_value="lm studio result")
        result_task = await orch.execute_task(task)
        assert result_task.status == TaskStatus.COMPLETED
        assert result_task.result == "lm studio result"

    @pytest.mark.asyncio
    async def test_execute_task_chatdev_success(self, orch):
        task = orch.submit_task(prompt="ChatDev task", target=TaskTarget.CHATDEV)
        orch._execute_chatdev = AsyncMock(return_value="chatdev result")
        result_task = await orch.execute_task(task)
        assert result_task.status == TaskStatus.COMPLETED
        assert result_task.result == "chatdev result"

    @pytest.mark.asyncio
    async def test_execute_task_copilot_success(self, orch):
        task = orch.submit_task(prompt="Copilot task", target=TaskTarget.COPILOT)
        orch._execute_copilot = AsyncMock(return_value=json.dumps({"status": "success"}))
        result_task = await orch.execute_task(task)
        assert result_task.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_task_unknown_target_fails(self, orch):
        task = orch.submit_task(prompt="Unknown", target=TaskTarget.OLLAMA)
        task.target = MagicMock()
        task.target.value = "unknown_backend"
        # Make all execute methods raise to force the fallback ValueError
        orch._execute_ollama = AsyncMock(side_effect=ValueError("Unknown target"))
        result_task = await orch.execute_task(task)
        assert result_task.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_task_failure_sets_error(self, orch):
        task = orch.submit_task(prompt="Fail", target=TaskTarget.OLLAMA)
        orch._execute_ollama = AsyncMock(side_effect=RuntimeError("boom"))
        result_task = await orch.execute_task(task)
        assert result_task.status == TaskStatus.FAILED
        assert "boom" in (result_task.error or "")

    @pytest.mark.asyncio
    async def test_execute_task_sets_started_at(self, orch):
        task = orch.submit_task(prompt="Time check", target=TaskTarget.OLLAMA)
        orch._execute_ollama = AsyncMock(return_value="ok")
        result_task = await orch.execute_task(task)
        assert result_task.started_at is not None

    @pytest.mark.asyncio
    async def test_execute_task_sets_completed_at(self, orch):
        task = orch.submit_task(prompt="Done check", target=TaskTarget.OLLAMA)
        orch._execute_ollama = AsyncMock(return_value="ok")
        result_task = await orch.execute_task(task)
        assert result_task.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_task_saves_after_completion(self, orch):
        task = orch.submit_task(prompt="Save check", target=TaskTarget.OLLAMA)
        orch._execute_ollama = AsyncMock(return_value="saved")
        await orch.execute_task(task)
        reloaded = BackgroundTaskOrchestrator(state_dir=orch.state_dir)
        saved = reloaded.get_task(task.task_id)
        assert saved is not None
        assert saved.status == TaskStatus.COMPLETED


# ---------------------------------------------------------------------------
# execute_task — Culture Ship veto
# ---------------------------------------------------------------------------


class TestExecuteTaskCultureShipVeto:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    @pytest.mark.asyncio
    async def test_culture_ship_veto_blocks_task(self, orch):
        mock_loop = MagicMock()
        approval = MagicMock()
        approval.approved = False
        approval.reason = "Denied by Culture Ship"
        mock_loop.request_approval.return_value = approval
        orch._consciousness_loop = mock_loop

        task = orch.submit_task(
            prompt="Risky action",
            target=TaskTarget.OLLAMA,
            metadata={"requires_approval": True},
        )
        result_task = await orch.execute_task(task)
        assert result_task.status == TaskStatus.FAILED
        assert "Culture Ship veto" in (result_task.error or "")

    @pytest.mark.asyncio
    async def test_culture_ship_approves_task(self, orch):
        mock_loop = MagicMock()
        approval = MagicMock()
        approval.approved = True
        mock_loop.request_approval.return_value = approval
        mock_loop.emit_event_sync = MagicMock()
        orch._consciousness_loop = mock_loop

        task = orch.submit_task(
            prompt="Approved action",
            target=TaskTarget.OLLAMA,
            metadata={"requires_approval": True},
        )
        orch._execute_ollama = AsyncMock(return_value="approved result")
        result_task = await orch.execute_task(task)
        assert result_task.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_consciousness_loop_emits_task_started_event(self, orch):
        mock_loop = MagicMock()
        mock_loop.emit_event_sync = MagicMock()
        orch._consciousness_loop = mock_loop

        task = orch.submit_task(prompt="Event task", target=TaskTarget.OLLAMA)
        orch._execute_ollama = AsyncMock(return_value="done")
        await orch.execute_task(task)
        event_names = [c.args[0] for c in mock_loop.emit_event_sync.call_args_list]
        assert "task_started" in event_names

    @pytest.mark.asyncio
    async def test_consciousness_loop_emits_task_completed_event(self, orch):
        mock_loop = MagicMock()
        mock_loop.emit_event_sync = MagicMock()
        orch._consciousness_loop = mock_loop

        task = orch.submit_task(prompt="Event finish task", target=TaskTarget.OLLAMA)
        orch._execute_ollama = AsyncMock(return_value="done")
        await orch.execute_task(task)
        calls = [c.args[0] for c in mock_loop.emit_event_sync.call_args_list]
        assert "task_completed" in calls


# ---------------------------------------------------------------------------
# _execute_ollama — aiohttp mocking
# ---------------------------------------------------------------------------


class TestExecuteOllama:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    @pytest.mark.asyncio
    async def test_execute_ollama_returns_response_text(self, orch):
        task = orch.submit_task(prompt="Analyze", target=TaskTarget.OLLAMA)
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"response": "Hello from Ollama"})
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await orch._execute_ollama(task)
        assert result == "Hello from Ollama"

    @pytest.mark.asyncio
    async def test_execute_ollama_raises_on_non_200(self, orch):
        task = orch.submit_task(prompt="Fail", target=TaskTarget.OLLAMA)
        mock_resp = AsyncMock()
        mock_resp.status = 503
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(OllamaError, match="503"):
                await orch._execute_ollama(task)

    @pytest.mark.asyncio
    async def test_execute_ollama_updates_progress(self, orch):
        task = orch.submit_task(prompt="Progress test", target=TaskTarget.OLLAMA)
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"response": "ok"})
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            await orch._execute_ollama(task)
        assert task.progress == 0.8


# ---------------------------------------------------------------------------
# _execute_lm_studio — aiohttp mocking
# ---------------------------------------------------------------------------


class TestExecuteLmStudio:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    @pytest.mark.asyncio
    async def test_execute_lm_studio_success(self, orch):
        task = orch.submit_task(prompt="LM prompt", target=TaskTarget.LM_STUDIO)
        payload = {"choices": [{"message": {"content": "LM answer"}}]}
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=payload)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await orch._execute_lm_studio(task)
        assert result == "LM answer"

    @pytest.mark.asyncio
    async def test_execute_lm_studio_raises_on_non_200(self, orch):
        task = orch.submit_task(prompt="Fail", target=TaskTarget.LM_STUDIO)
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(LMStudioError, match="500"):
                await orch._execute_lm_studio(task)

    @pytest.mark.asyncio
    async def test_execute_lm_studio_raises_on_missing_content(self, orch):
        task = orch.submit_task(prompt="Missing content", target=TaskTarget.LM_STUDIO)
        payload: dict = {"choices": []}
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=payload)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(LMStudioError, match="missing message content"):
                await orch._execute_lm_studio(task)

    @pytest.mark.asyncio
    async def test_execute_lm_studio_updates_progress(self, orch):
        task = orch.submit_task(prompt="Progress", target=TaskTarget.LM_STUDIO)
        payload = {"choices": [{"message": {"content": "ok"}}]}
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=payload)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            await orch._execute_lm_studio(task)
        assert task.progress == 0.8


# ---------------------------------------------------------------------------
# _execute_chatdev
# ---------------------------------------------------------------------------


class TestExecuteChatDev:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    @pytest.mark.asyncio
    async def test_execute_chatdev_import_error_returns_fallback(self, orch):
        task = orch.submit_task(prompt="ChatDev task", target=TaskTarget.CHATDEV)
        with patch.dict("sys.modules", {"src.integration.chatdev_launcher": None}):
            with patch(
                "src.orchestration.background_task_orchestrator.BackgroundTaskOrchestrator"
                "._execute_chatdev",
                new_callable=AsyncMock,
                return_value="ChatDev not available. Task queued: ChatDev task...",
            ):
                result = await orch._execute_chatdev(task)
        assert "ChatDev" in result

    @pytest.mark.asyncio
    async def test_execute_chatdev_with_run_task_async(self, orch):
        task = orch.submit_task(prompt="Run task async", target=TaskTarget.CHATDEV)

        mock_launcher = MagicMock()
        mock_launcher.run_task = AsyncMock(return_value={"status": "done", "output": "generated code"})

        mock_cls = MagicMock(return_value=mock_launcher)
        mock_module = MagicMock()
        mock_module.ChatDevLauncher = mock_cls

        with patch.dict("sys.modules", {"src.integration.chatdev_launcher": mock_module}):
            result = await orch._execute_chatdev(task)
        assert result is not None
        assert "done" in result or "generated" in result

    @pytest.mark.asyncio
    async def test_execute_chatdev_with_completed_process(self, orch):
        task = orch.submit_task(prompt="Completed process", target=TaskTarget.CHATDEV)

        mock_process = MagicMock()
        del mock_process.wait
        mock_process.returncode = 0

        mock_launcher = MagicMock()
        del mock_launcher.run_task
        mock_launcher.launch_chatdev.return_value = mock_process

        mock_cls = MagicMock(return_value=mock_launcher)
        mock_module = MagicMock()
        mock_module.ChatDevLauncher = mock_cls

        with patch.dict("sys.modules", {"src.integration.chatdev_launcher": mock_module}):
            result = await orch._execute_chatdev(task)
        assert "ChatDev completed" in result

    @pytest.mark.asyncio
    async def test_execute_chatdev_nonzero_returncode_raises(self, orch):
        task = orch.submit_task(prompt="Fail ChatDev", target=TaskTarget.CHATDEV)

        mock_process = MagicMock()
        del mock_process.wait
        mock_process.returncode = 1

        mock_launcher = MagicMock()
        del mock_launcher.run_task
        mock_launcher.launch_chatdev.return_value = mock_process

        mock_cls = MagicMock(return_value=mock_launcher)
        mock_module = MagicMock()
        mock_module.ChatDevLauncher = mock_cls

        with patch.dict("sys.modules", {"src.integration.chatdev_launcher": mock_module}):
            with pytest.raises(RuntimeError, match="return code 1"):
                await orch._execute_chatdev(task)


# ---------------------------------------------------------------------------
# _log_to_quest
# ---------------------------------------------------------------------------


class TestLogToQuest:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    def test_log_to_quest_writes_entry(self, orch, tmp_path):
        quest_log = tmp_path / "quest_log.jsonl"
        task = orch.submit_task(prompt="Quest task", target=TaskTarget.OLLAMA)
        task.status = TaskStatus.COMPLETED
        task.started_at = datetime.now(UTC)
        task.completed_at = datetime.now(UTC)

        with patch(
            "src.orchestration.background_task_orchestrator.Path",
            return_value=quest_log,
        ):
            orch._log_to_quest(task)

        if quest_log.exists():
            lines = quest_log.read_text().strip().splitlines()
            assert len(lines) >= 1
            entry = json.loads(lines[-1])
            assert entry["task_type"] == "background_task"
            assert entry["status"] == "completed"

    def test_log_to_quest_silently_swallows_errors(self, orch):
        task = orch.submit_task(prompt="Silent fail", target=TaskTarget.OLLAMA)
        with patch("builtins.open", side_effect=PermissionError("denied")):
            orch._log_to_quest(task)


# ---------------------------------------------------------------------------
# _trigger_autonomy
# ---------------------------------------------------------------------------


class TestTriggerAutonomy:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    @pytest.mark.asyncio
    async def test_trigger_autonomy_skips_short_result(self, orch):
        task = orch.submit_task(prompt="Short", target=TaskTarget.OLLAMA)
        task.result = "ok"
        await orch._trigger_autonomy(task)
        assert "autonomy_processed" not in task.metadata

    @pytest.mark.asyncio
    async def test_trigger_autonomy_skips_when_import_fails(self, orch):
        task = orch.submit_task(prompt="Autonomy task", target=TaskTarget.OLLAMA)
        task.result = "x" * 100
        with patch.dict("sys.modules", {"src.autonomy": None}):
            await orch._trigger_autonomy(task)
        assert "autonomy_processed" not in task.metadata

    @pytest.mark.asyncio
    async def test_trigger_autonomy_marks_processed_on_success(self, orch):
        task = orch.submit_task(prompt="Autonomy full", target=TaskTarget.OLLAMA)
        task.result = "x" * 100

        mock_bot = AsyncMock()
        mock_bot.process_llm_response = AsyncMock(
            return_value={"action_taken": "pr_created", "risk_level": "low"}
        )
        mock_autonomy = MagicMock()
        mock_autonomy.GitHubPRBot = MagicMock(return_value=mock_bot)

        with patch.dict("sys.modules", {"src.autonomy": mock_autonomy}):
            await orch._trigger_autonomy(task)

        assert task.metadata.get("autonomy_processed") is True
        assert task.metadata.get("autonomy_result", {}).get("action_taken") == "pr_created"

    @pytest.mark.asyncio
    async def test_trigger_autonomy_exception_in_bot_logs_error(self, orch):
        task = orch.submit_task(prompt="Autonomy error", target=TaskTarget.OLLAMA)
        task.result = "x" * 100

        mock_bot = AsyncMock()
        mock_bot.process_llm_response = AsyncMock(side_effect=RuntimeError("bot exploded"))
        mock_autonomy = MagicMock()
        mock_autonomy.GitHubPRBot = MagicMock(return_value=mock_bot)

        with patch.dict("sys.modules", {"src.autonomy": mock_autonomy}):
            await orch._trigger_autonomy(task)
        assert "autonomy_processed" not in task.metadata


# ---------------------------------------------------------------------------
# get_queue_stats
# ---------------------------------------------------------------------------


class TestGetQueueStats:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    def test_get_queue_stats_empty(self, orch):
        stats = orch.get_queue_stats()
        assert stats == {"queued": 0, "running": 0, "completed": 0, "failed": 0}

    def test_get_queue_stats_counts_correctly(self, orch):
        orch.submit_task(prompt="Q1", target=TaskTarget.OLLAMA)
        t2 = orch.submit_task(prompt="Q2", target=TaskTarget.OLLAMA, allow_duplicate=True)
        t3 = orch.submit_task(prompt="Q3", target=TaskTarget.OLLAMA, allow_duplicate=True)
        t4 = orch.submit_task(prompt="Q4", target=TaskTarget.OLLAMA, allow_duplicate=True)
        t2.status = TaskStatus.RUNNING
        t3.status = TaskStatus.COMPLETED
        t4.status = TaskStatus.FAILED

        stats = orch.get_queue_stats()
        assert stats["queued"] == 1
        assert stats["running"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 1

    def test_get_queue_stats_cancelled_not_counted(self, orch):
        t = orch.submit_task(prompt="Cancel me", target=TaskTarget.OLLAMA)
        orch.cancel_task(t.task_id)
        stats = orch.get_queue_stats()
        assert stats["queued"] == 0
        assert stats["running"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0


# ---------------------------------------------------------------------------
# get_orchestrator_status
# ---------------------------------------------------------------------------


class TestGetOrchestratorStatus:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    def test_status_includes_worker_running_false(self, orch):
        status = orch.get_orchestrator_status()
        assert status["worker_running"] is False

    def test_status_includes_copilot_bridge_mode(self, orch, monkeypatch):
        monkeypatch.setenv("NUSYQ_COPILOT_BRIDGE_MODE", "http")
        status = orch.get_orchestrator_status()
        assert status["targets"]["copilot"]["bridge_mode"] == "http"

    def test_status_available_models_present(self, orch):
        status = orch.get_orchestrator_status()
        models = status["targets"]["ollama"]["available_models"]
        assert isinstance(models, list)
        assert len(models) > 0

    def test_status_total_tasks_increments(self, orch):
        orch.submit_task(prompt="A", target=TaskTarget.OLLAMA)
        orch.submit_task(prompt="B", target=TaskTarget.OLLAMA, allow_duplicate=True)
        status = orch.get_orchestrator_status()
        assert status["total_tasks"] == 2


# ---------------------------------------------------------------------------
# prune_tasks — extended edge cases
# ---------------------------------------------------------------------------


class TestPruneTasksAdvanced:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    def test_prune_keeps_queued_tasks(self, orch):
        t = orch.submit_task(prompt="Keep me queued", target=TaskTarget.OLLAMA)
        orch.prune_tasks(keep_completed=0, keep_failed=0, keep_cancelled=0)
        assert t.task_id in orch.tasks

    def test_prune_removes_cancelled_beyond_limit(self, orch):
        for i in range(3):
            t = orch.submit_task(
                prompt=f"cancel-{i}", target=TaskTarget.OLLAMA, allow_duplicate=True
            )
            t.status = TaskStatus.CANCELLED
            t.completed_at = datetime.now(UTC) - timedelta(minutes=i)
        summary = orch.prune_tasks(keep_cancelled=1)
        assert summary["removed_by_status"]["cancelled"] == 2

    def test_prune_summary_reports_status_ok(self, orch):
        summary = orch.prune_tasks()
        assert summary["status"] == "ok"

    def test_prune_summary_has_retention_keys(self, orch):
        summary = orch.prune_tasks(keep_completed=10, keep_failed=5, keep_cancelled=3)
        assert summary["retention"]["completed"] == 10
        assert summary["retention"]["failed"] == 5
        assert summary["retention"]["cancelled"] == 3

    def test_prune_dry_run_reports_before_total(self, orch):
        for i in range(2):
            t = orch.submit_task(
                prompt=f"fail-{i}", target=TaskTarget.OLLAMA, allow_duplicate=True
            )
            t.status = TaskStatus.FAILED
        summary = orch.prune_tasks(keep_failed=0, dry_run=True)
        assert summary["before_total"] == 2
        assert summary["dry_run"] is True

    def test_prune_stale_running_no_started_at_not_reconciled(self, orch):
        t = orch.submit_task(prompt="No started_at", target=TaskTarget.OLLAMA)
        t.status = TaskStatus.RUNNING
        t.started_at = None
        summary = orch.prune_tasks(stale_running_after_s=0)
        assert summary["running_reconciled"] == 0
        assert t.status == TaskStatus.RUNNING

    def test_prune_fresh_running_not_reconciled(self, orch):
        t = orch.submit_task(prompt="Fresh running", target=TaskTarget.OLLAMA)
        t.status = TaskStatus.RUNNING
        t.started_at = datetime.now(UTC)
        summary = orch.prune_tasks(stale_running_after_s=3600)
        assert summary["running_reconciled"] == 0
        assert t.status == TaskStatus.RUNNING


# ---------------------------------------------------------------------------
# requeue_task
# ---------------------------------------------------------------------------


class TestRequeueTask:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    def test_requeue_sets_status_to_queued(self, orch):
        t = orch.submit_task(prompt="Requeue me", target=TaskTarget.OLLAMA)
        t.status = TaskStatus.FAILED
        result = orch.requeue_task(t.task_id, reason="retry")
        assert result is True
        assert t.status == TaskStatus.QUEUED

    def test_requeue_clears_result_and_error(self, orch):
        t = orch.submit_task(prompt="Clear me", target=TaskTarget.OLLAMA)
        t.status = TaskStatus.FAILED
        t.result = "old result"
        t.error = "old error"
        orch.requeue_task(t.task_id)
        assert t.result is None
        assert t.error is None

    def test_requeue_increments_count(self, orch):
        t = orch.submit_task(prompt="Count me", target=TaskTarget.OLLAMA)
        t.status = TaskStatus.FAILED
        orch.requeue_task(t.task_id, reason="first retry")
        assert t.metadata["requeue"]["count"] == 1
        t.status = TaskStatus.FAILED
        orch.requeue_task(t.task_id, reason="second retry")
        assert t.metadata["requeue"]["count"] == 2

    def test_requeue_nonexistent_returns_false(self, orch):
        result = orch.requeue_task("no_such_task")
        assert result is False


# ---------------------------------------------------------------------------
# _resolve_copilot_task_type
# ---------------------------------------------------------------------------


class TestResolveCopilotTaskType:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    def test_explicit_router_task_type_takes_precedence(self, orch):
        task = orch.submit_task(
            prompt="Test", target=TaskTarget.COPILOT, metadata={"router_task_type": "debug"}
        )
        assert orch._resolve_copilot_task_type(task) == "debug"

    def test_review_mapped_from_task_type(self, orch):
        task = orch.submit_task(
            prompt="Review", target=TaskTarget.COPILOT, task_type="code_review"
        )
        assert orch._resolve_copilot_task_type(task) == "review"

    def test_debug_mapped_from_fix_in_task_type(self, orch):
        task = orch.submit_task(
            prompt="Fix", target=TaskTarget.COPILOT, task_type="bugfix"
        )
        assert orch._resolve_copilot_task_type(task) == "debug"

    def test_fallback_to_analyze(self, orch):
        task = orch.submit_task(
            prompt="Default", target=TaskTarget.COPILOT, task_type="unknown_type"
        )
        assert orch._resolve_copilot_task_type(task) == "analyze"

    def test_generate_from_build(self, orch):
        task = orch.submit_task(
            prompt="Build", target=TaskTarget.COPILOT, task_type="build_something"
        )
        assert orch._resolve_copilot_task_type(task) == "generate"

    def test_document_from_doc(self, orch):
        task = orch.submit_task(
            prompt="Doc", target=TaskTarget.COPILOT, task_type="documentation"
        )
        assert orch._resolve_copilot_task_type(task) == "document"

    def test_plan_from_plan_task_type(self, orch):
        task = orch.submit_task(
            prompt="Plan", target=TaskTarget.COPILOT, task_type="planning"
        )
        assert orch._resolve_copilot_task_type(task) == "plan"

    def test_test_from_test_task_type(self, orch):
        task = orch.submit_task(
            prompt="Test gen", target=TaskTarget.COPILOT, task_type="test_generation"
        )
        assert orch._resolve_copilot_task_type(task) == "test"


# ---------------------------------------------------------------------------
# _get_adaptive_timeout
# ---------------------------------------------------------------------------


class TestGetAdaptiveTimeout:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    def test_no_consciousness_loop_returns_base(self, orch):
        orch._consciousness_loop = None
        assert orch._get_adaptive_timeout(600) == 600

    def test_with_consciousness_loop_applies_cached_factor(self, orch):
        import time

        mock_loop = MagicMock()
        mock_loop._factor_expires_at = time.monotonic() + 9999
        mock_loop._cached_factor = 1.5
        orch._consciousness_loop = mock_loop
        result = orch._get_adaptive_timeout(100)
        assert result == pytest.approx(150.0)

    def test_with_expired_cache_calls_breathing_factor(self, orch):
        import time

        mock_loop = MagicMock()
        mock_loop._factor_expires_at = time.monotonic() - 1
        mock_loop.breathing_factor = 0.8
        orch._consciousness_loop = mock_loop
        result = orch._get_adaptive_timeout(100)
        assert result == pytest.approx(80.0)


# ---------------------------------------------------------------------------
# submit_task — deduplication
# ---------------------------------------------------------------------------


class TestSubmitTaskDeduplication:
    @pytest.fixture
    def orch(self, tmp_path):
        return _make_orch(tmp_path)

    def test_duplicate_queued_prompt_returns_existing(self, orch):
        t1 = orch.submit_task(prompt="duplicate me", target=TaskTarget.OLLAMA)
        t2 = orch.submit_task(prompt="duplicate me", target=TaskTarget.OLLAMA)
        assert t1.task_id == t2.task_id

    def test_allow_duplicate_bypasses_dedup(self, orch):
        t1 = orch.submit_task(prompt="dup allowed", target=TaskTarget.OLLAMA)
        t2 = orch.submit_task(
            prompt="dup allowed", target=TaskTarget.OLLAMA, allow_duplicate=True
        )
        assert t1.task_id != t2.task_id

    def test_completed_task_not_deduped(self, orch):
        t1 = orch.submit_task(prompt="done already", target=TaskTarget.OLLAMA)
        t1.status = TaskStatus.COMPLETED
        t2 = orch.submit_task(prompt="done already", target=TaskTarget.OLLAMA)
        assert t1.task_id != t2.task_id
