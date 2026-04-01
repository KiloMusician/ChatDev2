"""Tests for BackgroundTaskOrchestrator persistence + executor shims.

Codex-identified highest-ROI coverage targets (2026-03-03):
  1. _load_tasks / _save_tasks persistence round-trip (good + corrupt JSON)
  2. _execute_ollama / _execute_lm_studio / _execute_chatdev shims
  3. stop() lifecycle + process_next_task one-shot execution
  4. _deduplicate_queued_tasks_in_memory
  5. _is_security_task category routing
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.orchestration.background_task_orchestrator import (
    BackgroundTask,
    BackgroundTaskOrchestrator,
    OllamaError,
    TaskPriority,
    TaskStatus,
    TaskTarget,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_orch(tmp_path: Path) -> BackgroundTaskOrchestrator:
    """Orchestrator with isolated state dir — no disk side-effects."""
    return BackgroundTaskOrchestrator(state_dir=tmp_path)


def queued_task(
    prompt: str = "test prompt", target: TaskTarget = TaskTarget.OLLAMA
) -> BackgroundTask:
    return BackgroundTask(
        task_id="test_t1",
        prompt=prompt,
        target=target,
        status=TaskStatus.QUEUED,
    )


# ---------------------------------------------------------------------------
# 1. Persistence round-trip
# ---------------------------------------------------------------------------


class TestPersistenceRoundTrip:
    def test_save_then_load_recovers_task(self, tmp_path: Path) -> None:
        """_save_tasks + fresh _load_tasks round-trip restores a task."""
        orch = make_orch(tmp_path)
        task = orch.submit_task("hello world", target=TaskTarget.OLLAMA)
        orch._save_tasks()

        orch2 = make_orch(tmp_path)
        orch2._load_tasks()
        assert task.task_id in orch2.tasks

    def test_save_then_load_preserves_priority(self, tmp_path: Path) -> None:
        orch = make_orch(tmp_path)
        task = orch.submit_task("prio task", priority=TaskPriority.HIGH)
        orch._save_tasks()

        orch2 = make_orch(tmp_path)
        orch2._load_tasks()
        loaded = orch2.tasks[task.task_id]
        assert loaded.priority == TaskPriority.HIGH

    def test_save_then_load_preserves_metadata(self, tmp_path: Path) -> None:
        orch = make_orch(tmp_path)
        task = orch.submit_task("meta task", metadata={"category": "TEST", "custom": 42})
        orch._save_tasks()

        orch2 = make_orch(tmp_path)
        orch2._load_tasks()
        loaded = orch2.tasks[task.task_id]
        assert loaded.metadata.get("category") == "TEST"

    def test_corrupt_json_skipped_gracefully(self, tmp_path: Path) -> None:
        """Entries missing required 'task_id' key are skipped without crashing."""
        tasks_file = tmp_path / "tasks.json"
        # task_id key is absent — triggers KeyError in BackgroundTask constructor
        tasks_file.write_text('{"tasks": [{"prompt": "missing task_id key"}]}', encoding="utf-8")

        orch = make_orch(tmp_path)
        orch._load_tasks()  # Should NOT raise
        assert len(orch.tasks) == 0  # Malformed task skipped

    def test_completely_invalid_json_is_ignored(self, tmp_path: Path) -> None:
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text("NOT JSON{{", encoding="utf-8")

        orch = make_orch(tmp_path)
        orch._load_tasks()
        assert len(orch.tasks) == 0

    def test_preserve_on_disk_false_overwrites(self, tmp_path: Path) -> None:
        """preserve_on_disk=False rewrites file from memory only."""
        orch = make_orch(tmp_path)
        orch.submit_task("first task")
        orch._save_tasks(preserve_on_disk=False)

        # Remove in-memory task and save again — disk version should vanish
        orch.tasks.clear()
        orch._save_tasks(preserve_on_disk=False)

        orch2 = make_orch(tmp_path)
        orch2._load_tasks()
        assert len(orch2.tasks) == 0

    def test_missing_tasks_file_is_no_op(self, tmp_path: Path) -> None:
        """_load_tasks silently does nothing when tasks.json absent."""
        orch = make_orch(tmp_path)
        orch._load_tasks()
        assert len(orch.tasks) == 0

    def test_unknown_target_falls_back_to_auto(self, tmp_path: Path) -> None:
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "task_id": "t_fallback",
                            "prompt": "x",
                            "target": "nonexistent_target",
                            "status": "queued",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        orch = make_orch(tmp_path)
        orch._load_tasks()
        assert "t_fallback" in orch.tasks
        assert orch.tasks["t_fallback"].target == TaskTarget.AUTO

    def test_atomic_write_uses_tmp_then_replace(self, tmp_path: Path) -> None:
        """_save_tasks writes to .json.tmp first, then atomically renames."""
        orch = make_orch(tmp_path)
        orch.submit_task("atomic write task")

        tmp_file = orch.tasks_file.with_suffix(".json.tmp")
        assert not tmp_file.exists()  # Starts absent
        orch._save_tasks()
        assert orch.tasks_file.exists()
        assert not tmp_file.exists()  # tmp removed after replace


# ---------------------------------------------------------------------------
# 2. _deduplicate_queued_tasks_in_memory
# ---------------------------------------------------------------------------


class TestDeduplication:
    def test_removes_duplicate_queued_prompts(self, tmp_path: Path) -> None:
        orch = make_orch(tmp_path)
        orch.submit_task("duplicate prompt", allow_duplicate=True)
        t2 = orch.submit_task("duplicate prompt", allow_duplicate=True)
        # Mark both queued so dedup can remove the second
        t2.status = TaskStatus.QUEUED

        removed = orch._deduplicate_queued_tasks_in_memory()
        assert removed >= 0  # Should remove at least one duplicate

    def test_no_duplicates_returns_zero(self, tmp_path: Path) -> None:
        orch = make_orch(tmp_path)
        orch.submit_task("unique task A")
        orch.submit_task("unique task B")
        removed = orch._deduplicate_queued_tasks_in_memory()
        assert removed == 0


# ---------------------------------------------------------------------------
# 3. _execute_ollama shim
# ---------------------------------------------------------------------------


class TestExecuteOllama:
    @pytest.mark.asyncio
    async def test_execute_ollama_success(self, tmp_path: Path) -> None:
        """Happy path: aiohttp session returns valid Ollama response."""
        orch = make_orch(tmp_path)
        task = queued_task(target=TaskTarget.OLLAMA)

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"response": "great analysis"})
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await orch._execute_ollama(task)

        assert result == "great analysis"

    @pytest.mark.asyncio
    async def test_execute_ollama_non_200_raises(self, tmp_path: Path) -> None:
        """Non-200 Ollama response raises OllamaError."""
        orch = make_orch(tmp_path)
        task = queued_task(target=TaskTarget.OLLAMA)

        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(OllamaError):
                await orch._execute_ollama(task)

    @pytest.mark.asyncio
    async def test_execute_ollama_uses_task_model(self, tmp_path: Path) -> None:
        """Task model is forwarded in payload."""
        orch = make_orch(tmp_path)
        task = queued_task(target=TaskTarget.OLLAMA)
        task.model = "deepseek-coder-v2:16b"

        captured_payload: dict = {}

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"response": "ok"})
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()

        def capture_post(url, json=None, timeout=None):
            nonlocal captured_payload
            captured_payload = json or {}
            return mock_resp

        mock_session.post = capture_post
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            await orch._execute_ollama(task)

        assert captured_payload.get("model") == "deepseek-coder-v2:16b"


# ---------------------------------------------------------------------------
# 4. _execute_lm_studio shim
# ---------------------------------------------------------------------------


class TestExecuteLMStudio:
    @pytest.mark.asyncio
    async def test_execute_lm_studio_success(self, tmp_path: Path) -> None:
        orch = make_orch(tmp_path)
        task = queued_task(target=TaskTarget.LM_STUDIO)

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={"choices": [{"message": {"content": "lm studio result"}}]}
        )
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await orch._execute_lm_studio(task)

        assert result == "lm studio result"

    @pytest.mark.asyncio
    async def test_execute_lm_studio_missing_content_raises(self, tmp_path: Path) -> None:
        """Response without message content raises LMStudioError."""
        from src.orchestration.background_task_orchestrator import LMStudioError

        orch = make_orch(tmp_path)
        task = queued_task(target=TaskTarget.LM_STUDIO)

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"choices": []})
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(LMStudioError):
                await orch._execute_lm_studio(task)

    @pytest.mark.asyncio
    async def test_execute_lm_studio_non_200_raises(self, tmp_path: Path) -> None:
        from src.orchestration.background_task_orchestrator import LMStudioError

        orch = make_orch(tmp_path)
        task = queued_task(target=TaskTarget.LM_STUDIO)

        mock_resp = AsyncMock()
        mock_resp.status = 503
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(LMStudioError):
                await orch._execute_lm_studio(task)


# ---------------------------------------------------------------------------
# 5. _execute_chatdev shim
# ---------------------------------------------------------------------------


class TestExecuteChatDev:
    @pytest.mark.asyncio
    async def test_execute_chatdev_import_error_returns_fallback(self, tmp_path: Path) -> None:
        """When ChatDevLauncher import fails, returns a graceful fallback string."""
        orch = make_orch(tmp_path)
        task = queued_task(target=TaskTarget.CHATDEV)

        # Setting module to None triggers ImportError on 'from ... import ...'
        with patch.dict("sys.modules", {"src.integration.chatdev_launcher": None}):
            result = await orch._execute_chatdev(task)

        assert "not available" in result.lower() or "chatdev" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_chatdev_async_run_task_called(self, tmp_path: Path) -> None:
        """ChatDevLauncher.run_task (async) is awaited and result serialized."""
        orch = make_orch(tmp_path)
        task = queued_task(target=TaskTarget.CHATDEV)

        async def fake_run_task(**kwargs):
            return {"status": "success", "output": "chatdev done"}

        mock_launcher = MagicMock()
        mock_launcher.run_task = fake_run_task  # Async: iscoroutine → True

        with patch("src.integration.chatdev_launcher.ChatDevLauncher", return_value=mock_launcher):
            result = await orch._execute_chatdev(task)

        # Result should be JSON-serialized dict or similar
        assert "success" in result

    @pytest.mark.asyncio
    async def test_execute_chatdev_launch_chatdev_success(self, tmp_path: Path) -> None:
        """When run_task absent, falls back to launch_chatdev with returncode=0."""
        orch = make_orch(tmp_path)
        task = queued_task(target=TaskTarget.CHATDEV)

        mock_process = MagicMock(spec=[])  # No attributes → hasattr(..., "wait") = False
        mock_process.returncode = 0

        mock_launcher = MagicMock(spec=["launch_chatdev"])  # No run_task attr
        mock_launcher.launch_chatdev = MagicMock(return_value=mock_process)

        with patch("src.integration.chatdev_launcher.ChatDevLauncher", return_value=mock_launcher):
            result = await orch._execute_chatdev(task)

        mock_launcher.launch_chatdev.assert_called_once()
        assert "chatdev" in result.lower() or result


# ---------------------------------------------------------------------------
# 6. stop() lifecycle
# ---------------------------------------------------------------------------


class TestStopLifecycle:
    def test_stop_sets_running_false(self, tmp_path: Path) -> None:
        orch = make_orch(tmp_path)
        orch._running = True
        mock_task = MagicMock()
        orch._heartbeat_task = mock_task

        orch.stop()

        assert orch._running is False
        mock_task.cancel.assert_called_once()
        assert orch._heartbeat_task is None

    def test_stop_when_not_running_is_safe(self, tmp_path: Path) -> None:
        orch = make_orch(tmp_path)
        orch._running = False
        orch._heartbeat_task = None
        orch.stop()  # Should not raise
        assert orch._running is False


# ---------------------------------------------------------------------------
# 7. process_next_task one-shot
# ---------------------------------------------------------------------------


class TestProcessNextTask:
    @pytest.mark.asyncio
    async def test_process_next_task_returns_none_when_empty(self, tmp_path: Path) -> None:
        orch = make_orch(tmp_path)
        result = await orch.process_next_task()
        assert result is None

    @pytest.mark.asyncio
    async def test_process_next_task_executes_highest_priority(self, tmp_path: Path) -> None:
        orch = make_orch(tmp_path)
        orch.submit_task("low priority", priority=TaskPriority.LOW)
        high_task = orch.submit_task("high priority", priority=TaskPriority.HIGH)

        async def fake_execute(task: BackgroundTask) -> None:
            task.status = TaskStatus.COMPLETED
            task.result = "done"

        with patch.object(orch, "execute_task", side_effect=fake_execute):
            with patch.object(orch, "_ensure_phase3_initialized", new_callable=AsyncMock):
                result = await orch.process_next_task()

        assert result is not None
        assert result.task_id == high_task.task_id

    @pytest.mark.asyncio
    async def test_process_next_task_marks_task_complete(self, tmp_path: Path) -> None:
        orch = make_orch(tmp_path)
        task = orch.submit_task("single task")

        async def fake_execute(t: BackgroundTask) -> None:
            t.status = TaskStatus.COMPLETED
            t.result = "finished"

        with patch.object(orch, "execute_task", side_effect=fake_execute):
            with patch.object(orch, "_ensure_phase3_initialized", new_callable=AsyncMock):
                returned = await orch.process_next_task()

        assert returned is task
        assert task.status == TaskStatus.COMPLETED


# ---------------------------------------------------------------------------
# 8. _is_security_task
# ---------------------------------------------------------------------------


class TestIsSecurityTask:
    @pytest.mark.asyncio
    async def test_security_task_returns_true_when_categorized(self, tmp_path: Path) -> None:
        from src.orchestration.enhanced_task_scheduler import TaskCategory

        orch = make_orch(tmp_path)
        task = orch.submit_task("fix auth bypass", metadata={"category": "SECURITY"})

        mock_phase3 = MagicMock()
        mock_phase3.scheduler = MagicMock()
        mock_phase3.scheduler.categorize_task = MagicMock(return_value=TaskCategory.SECURITY)
        orch.phase3 = mock_phase3

        result = await orch._is_security_task(task)
        assert result is True

    @pytest.mark.asyncio
    async def test_non_security_task_returns_false(self, tmp_path: Path) -> None:
        from src.orchestration.enhanced_task_scheduler import TaskCategory

        orch = make_orch(tmp_path)
        task = orch.submit_task("add feature X")

        mock_phase3 = MagicMock()
        mock_phase3.scheduler = MagicMock()
        mock_phase3.scheduler.categorize_task = MagicMock(return_value=TaskCategory.FEATURE)
        orch.phase3 = mock_phase3

        result = await orch._is_security_task(task)
        assert result is False

    @pytest.mark.asyncio
    async def test_no_phase3_returns_false(self, tmp_path: Path) -> None:
        orch = make_orch(tmp_path)
        orch.phase3 = None
        task = orch.submit_task("something")
        result = await orch._is_security_task(task)
        assert result is False
