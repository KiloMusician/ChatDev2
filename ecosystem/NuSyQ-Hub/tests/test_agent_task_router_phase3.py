#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.agent_task_router import AgentTaskRouter
from src.orchestration.unified_ai_orchestrator import OrchestrationTask, TaskPriority


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_router(tmp_path: Path) -> AgentTaskRouter:
    router = AgentTaskRouter(repo_root=tmp_path)
    router.orchestrator = MagicMock()
    router.orchestrator.submit_task.return_value = "submitted-id"
    router.quest_log_path = tmp_path / "quest_log.jsonl"
    router.quest_log_path.parent.mkdir(parents=True, exist_ok=True)
    router.quest_log_path.touch()
    return router


def _make_task(
    task_type: str = "analyze",
    content: str = "test content",
    context: dict[str, Any] | None = None,
    task_id: str = "task-001",
) -> OrchestrationTask:
    return OrchestrationTask(
        task_id=task_id,
        task_type=task_type,
        content=content,
        context=context if context is not None else {},
    )


# ---------------------------------------------------------------------------
# route_task (lines 1370-1447)
# ---------------------------------------------------------------------------


class TestRouteTask:
    @pytest.mark.asyncio
    async def test_route_task_success_returns_dict(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router._route_by_system = AsyncMock(
            return_value={"status": "success", "system": "ollama", "output": "ok"}
        )
        result = await router.route_task("analyze", "review the code", target_system="ollama")
        assert result["status"] == "success"
        assert result["system"] == "ollama"

    @pytest.mark.asyncio
    async def test_route_task_failed_result_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router._route_by_system = AsyncMock(
            return_value={"status": "failed", "error": "something went wrong"}
        )
        result = await router.route_task("analyze", "review", target_system="ollama")
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_route_task_with_file_context(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router._route_by_system = AsyncMock(
            return_value={"status": "success", "system": "ollama", "output": "done"}
        )
        result = await router.route_task(
            "analyze",
            "check file",
            context={"file": "src/main.py"},
            target_system="ollama",
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_route_task_submitted_status_counts_as_success(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router._route_by_system = AsyncMock(
            return_value={"status": "submitted", "system": "background"}
        )
        result = await router.route_task("generate", "queue task", target_system="auto")
        assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_route_task_ready_status_counts_as_success(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router._route_by_system = AsyncMock(
            return_value={"status": "ready", "system": "auto"}
        )
        result = await router.route_task("analyze", "go", target_system="auto")
        assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_route_task_exception_returns_failed_dict(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router._route_by_system = AsyncMock(side_effect=RuntimeError("router crash"))
        result = await router.route_task("analyze", "crash test", target_system="ollama")
        assert result["status"] == "failed"
        assert "router crash" in result["error"]

    @pytest.mark.asyncio
    async def test_route_task_workspace_awareness_propagated(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router._route_by_system = AsyncMock(
            return_value={"status": "success", "system": "ollama", "output": "ok"}
        )
        awareness = {"active_session": "main", "reports": {}}
        result = await router.route_task(
            "analyze",
            "workspace-aware task",
            context={"workspace_awareness": awareness},
            target_system="ollama",
        )
        assert result.get("workspace_awareness_used") is True

    @pytest.mark.asyncio
    async def test_route_task_priority_high(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router._route_by_system = AsyncMock(
            return_value={"status": "success", "system": "ollama", "output": "ok"}
        )
        result = await router.route_task(
            "analyze", "urgent review", priority="HIGH", target_system="ollama"
        )
        assert result["status"] == "success"


# ---------------------------------------------------------------------------
# analyze_system (lines 1458-1517)
# ---------------------------------------------------------------------------


class TestAnalyzeSystem:
    @pytest.mark.asyncio
    async def test_analyze_system_success_path(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        (tmp_path / "state" / "reports").mkdir(parents=True, exist_ok=True)

        mock_analyzer = MagicMock()
        mock_analyzer.quick_scan = MagicMock()
        mock_analyzer.results = {
            "working_files": ["a.py", "b.py"],
            "broken_files": [],
            "launch_pad_files": ["main.py"],
            "enhancement_candidates": ["c.py"],
        }

        with patch(
            "src.tools.agent_task_router.AgentTaskRouter.analyze_system.__wrapped__",
            None,
            create=True,
        ):
            with patch.dict(
                "sys.modules",
                {
                    "src.diagnostics.quick_system_analyzer": MagicMock(
                        QuickSystemAnalyzer=MagicMock(return_value=mock_analyzer)
                    )
                },
            ):
                result = await router.analyze_system()

        assert result["status"] == "success"
        assert result["system"] == "QuickSystemAnalyzer"
        assert result["summary"]["working_files"] == 2
        assert result["summary"]["broken_files"] == 0

    @pytest.mark.asyncio
    async def test_analyze_system_import_error_uses_fallback(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        (tmp_path / "state" / "reports").mkdir(parents=True, exist_ok=True)

        fallback_data = {
            "summary": {"working_files": 5, "broken_files": 1},
            "files": [],
        }
        router._basic_workspace_scan = MagicMock(return_value=fallback_data)

        with patch.dict("sys.modules", {"src.diagnostics.quick_system_analyzer": None}):
            result = await router.analyze_system()

        assert result["status"] == "success"
        assert result["system"] == "QuickSystemAnalyzerFallback"
        assert "Fallback" in result.get("note", "")

    @pytest.mark.asyncio
    async def test_analyze_system_fallback_also_fails_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router._basic_workspace_scan = MagicMock(side_effect=RuntimeError("scan failed"))

        with patch.dict("sys.modules", {"src.diagnostics.quick_system_analyzer": None}):
            result = await router.analyze_system()

        assert result["status"] == "failed"
        assert "scan failed" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_system_with_target(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        fallback_data = {"summary": {}, "files": []}
        router._basic_workspace_scan = MagicMock(return_value=fallback_data)

        with patch.dict("sys.modules", {"src.diagnostics.quick_system_analyzer": None}):
            result = await router.analyze_system(target="src/")

        assert result["status"] == "success"


# ---------------------------------------------------------------------------
# heal_system (lines 1531-1587)
# ---------------------------------------------------------------------------


class TestHealSystem:
    @pytest.mark.asyncio
    async def test_heal_system_import_error_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)

        with patch.dict(
            "sys.modules",
            {
                "ecosystem_health_checker": None,
                "src.healing.repository_health_restorer": None,
            },
        ):
            result = await router.heal_system()

        assert result["status"] == "failed"
        assert result["system"] == "RepositoryHealthRestorer"

    @pytest.mark.asyncio
    async def test_heal_system_readonly_mode_skips_actions(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        (tmp_path / "state" / "reports").mkdir(parents=True, exist_ok=True)

        mock_health_checker = MagicMock()
        mock_health_checker.check_ollama_health = MagicMock()
        mock_health_checker.repos = {}
        mock_health_checker.health_report = {"healthy": True}

        mock_restorer = MagicMock()

        mock_ehc = MagicMock(EcosystemHealthChecker=MagicMock(return_value=mock_health_checker))
        mock_rhr = MagicMock(RepositoryHealthRestorer=MagicMock(return_value=mock_restorer))

        with patch.dict(
            "sys.modules",
            {
                "ecosystem_health_checker": mock_ehc,
                "src.healing.repository_health_restorer": mock_rhr,
            },
        ):
            result = await router.heal_system(auto_confirm=False)

        assert result["status"] == "success"
        assert "analysis_only" in result["actions_taken"]

    @pytest.mark.asyncio
    async def test_heal_system_auto_confirm_runs_actions(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        (tmp_path / "state" / "reports").mkdir(parents=True, exist_ok=True)

        mock_health_checker = MagicMock()
        mock_health_checker.check_ollama_health = MagicMock()
        mock_health_checker.repos = {}
        mock_health_checker.health_report = {"healthy": True}

        mock_restorer = MagicMock()
        mock_restorer.install_missing_dependencies = MagicMock(return_value=True)
        mock_restorer.create_missing_modules = MagicMock(return_value=True)

        mock_ehc = MagicMock(EcosystemHealthChecker=MagicMock(return_value=mock_health_checker))
        mock_rhr = MagicMock(RepositoryHealthRestorer=MagicMock(return_value=mock_restorer))

        with patch.dict(
            "sys.modules",
            {
                "ecosystem_health_checker": mock_ehc,
                "src.healing.repository_health_restorer": mock_rhr,
            },
        ):
            result = await router.heal_system(auto_confirm=True)

        assert result["status"] == "success"
        assert "dependencies_installed" in result["actions_taken"]
        assert "modules_created" in result["actions_taken"]


# ---------------------------------------------------------------------------
# _maybe_heal (lines 1658-1671)
# ---------------------------------------------------------------------------


class TestMaybeHeal:
    @pytest.mark.asyncio
    async def test_no_broken_files_skips_healing(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        result = await router._maybe_heal(0, halt_on_error=False)
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_broken_files_triggers_heal(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router.heal_system = AsyncMock(
            return_value={"status": "success", "actions_taken": ["deps_installed"]}
        )
        result = await router._maybe_heal(3, halt_on_error=False)
        assert result["status"] == "success"
        router.heal_system.assert_called_once_with(auto_confirm=False)

    @pytest.mark.asyncio
    async def test_heal_failed_with_halt_on_error(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router.heal_system = AsyncMock(
            return_value={"status": "failed", "actions_taken": []}
        )
        result = await router._maybe_heal(2, halt_on_error=True)
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_heal_returns_actions(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        router.heal_system = AsyncMock(
            return_value={"status": "success", "actions_taken": ["modules_created"]}
        )
        result = await router._maybe_heal(1, halt_on_error=False)
        assert "modules_created" in result["actions"]


# ---------------------------------------------------------------------------
# _capture_intent (lines 1673-1695)
# ---------------------------------------------------------------------------


class TestCaptureIntent:
    def test_returns_none_when_broken_files_nonzero(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        result = router._capture_intent(
            broken_count=2,
            iteration_index=1,
            current_state={"broken_files": 2, "working_files": 10, "timestamp": "now"},
            heal_log={"actions": []},
        )
        assert result is None

    def test_returns_intent_event_when_healthy(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        current_state = {"broken_files": 0, "working_files": 15, "timestamp": "2026-01-01T00:00:00"}
        result = router._capture_intent(
            broken_count=0,
            iteration_index=2,
            current_state=current_state,
            heal_log={"actions": ["deps_installed"]},
        )
        assert result is not None
        assert result["type"] == "system_health_achieved"
        assert result["iteration"] == 2
        assert result["actions_that_helped"] == ["deps_installed"]
        assert result["state"] is current_state


# ---------------------------------------------------------------------------
# _build_plan (lines 1697-1723)
# ---------------------------------------------------------------------------


class TestBuildPlan:
    def test_healthy_state_no_prev_returns_healthy(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        plan = router._build_plan(broken_count=0, prev_state=None)
        assert plan["status"] == "healthy"
        assert plan["max_items"] == 3

    def test_recovered_state_when_prev_had_broken_files(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        plan = router._build_plan(
            broken_count=0,
            prev_state={"broken_files": 5, "timestamp": "2026-01-01"},
        )
        assert plan["status"] == "recovered"

    def test_healing_in_progress_when_broken_count_nonzero(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        plan = router._build_plan(broken_count=3, prev_state=None)
        assert plan["status"] == "healing_in_progress"
        assert plan["max_items"] == 1

    def test_suggested_items_are_non_empty(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        plan = router._build_plan(broken_count=0, prev_state=None)
        assert len(plan["suggested_items"]) == 3


# ---------------------------------------------------------------------------
# _wire_intent_to_quest (lines 1830-1872)
# ---------------------------------------------------------------------------


class TestWireIntentToQuest:
    @pytest.mark.asyncio
    async def test_empty_list_returns_zero(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        count = await router._wire_intent_to_quest([])
        assert count == 0

    @pytest.mark.asyncio
    async def test_single_event_appended_to_quest_log(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        event = {
            "type": "system_health_achieved",
            "iteration": 1,
            "timestamp": "2026-01-01T00:00:00",
            "message": "healthy",
            "state": {"broken_files": 0, "working_files": 10},
            "actions_that_helped": [],
        }
        count = await router._wire_intent_to_quest([event])
        assert count == 1
        lines = router.quest_log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["task_type"] == "cultivation_intent"
        assert entry["status"] == "completed"

    @pytest.mark.asyncio
    async def test_multiple_events_all_written(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        events = [
            {
                "type": "system_health_achieved",
                "iteration": i,
                "timestamp": "2026-01-01T00:00:00",
                "message": f"healthy {i}",
                "state": {},
                "actions_that_helped": [],
            }
            for i in range(3)
        ]
        count = await router._wire_intent_to_quest(events)
        assert count == 3
        lines = router.quest_log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 3


# ---------------------------------------------------------------------------
# _promote_plans_to_work_queue (lines 1874-1942)
# ---------------------------------------------------------------------------


class TestPromotePlansToWorkQueue:
    @pytest.mark.asyncio
    async def test_no_plans_returns_zero_promoted(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        iterations: list[dict[str, Any]] = [{"cultivation": {}}]
        result = await router._promote_plans_to_work_queue(iterations)
        assert result["items_promoted"] == 0

    @pytest.mark.asyncio
    async def test_plans_promoted_to_new_queue(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        iterations = [
            {
                "cultivation": {
                    "ten_minute_plan": {
                        "status": "healthy",
                        "suggested_items": [
                            "1. Document recovery actions",
                            "2. Validate key workflows",
                        ],
                    }
                }
            }
        ]
        result = await router._promote_plans_to_work_queue(iterations)
        assert result["items_promoted"] == 2
        assert result["total_items_in_queue"] == 2
        queue_path = Path(result["work_queue_path"])
        assert queue_path.exists()
        data = json.loads(queue_path.read_text(encoding="utf-8"))
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_duplicate_items_not_added_twice(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        plan = {
            "ten_minute_plan": {
                "status": "healthy",
                "suggested_items": ["1. Document recovery actions"],
            }
        }
        iterations = [{"cultivation": plan}, {"cultivation": plan}]
        result = await router._promote_plans_to_work_queue(iterations)
        assert result["items_promoted"] == 1
        assert result["total_items_in_queue"] == 1

    @pytest.mark.asyncio
    async def test_existing_queue_loaded_and_appended(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        work_queue_dir = tmp_path / "docs" / "Work-Queue"
        work_queue_dir.mkdir(parents=True, exist_ok=True)
        existing_queue = {
            "version": "1.0",
            "created": "2026-01-01",
            "items": [
                {"id": "existing_0_0", "title": "Existing item", "source": "manual"}
            ],
        }
        (work_queue_dir / "WORK_QUEUE.json").write_text(
            json.dumps(existing_queue), encoding="utf-8"
        )
        iterations = [
            {
                "cultivation": {
                    "ten_minute_plan": {
                        "status": "healthy",
                        "suggested_items": ["1. New item from cultivation"],
                    }
                }
            }
        ]
        result = await router._promote_plans_to_work_queue(iterations)
        assert result["items_promoted"] == 1
        assert result["total_items_in_queue"] == 2


# ---------------------------------------------------------------------------
# _document_in_session_log (lines 1944-2026)
# ---------------------------------------------------------------------------


class TestDocumentInSessionLog:
    @pytest.mark.asyncio
    async def test_session_log_created(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        intent_events = [
            {
                "type": "system_health_achieved",
                "iteration": 1,
                "timestamp": "2026-01-01T00:00:00",
                "message": "healthy",
                "state": {"broken_files": 0, "working_files": 10},
                "actions_that_helped": ["deps_installed"],
            }
        ]
        work_queue_updates = {
            "items_promoted": 2,
            "total_items_in_queue": 3,
            "work_queue_path": str(tmp_path / "docs" / "Work-Queue" / "WORK_QUEUE.json"),
        }
        session_log_path = await router._document_in_session_log(
            intent_events, work_queue_updates, str(tmp_path / "develop_log.json")
        )
        assert session_log_path.exists()
        content = session_log_path.read_text(encoding="utf-8")
        assert "Cultivation Session Report" in content
        assert "SYSTEM_HEALTH_ACHIEVED" in content

    @pytest.mark.asyncio
    async def test_session_log_no_events(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        work_queue_updates = {
            "items_promoted": 0,
            "total_items_in_queue": 0,
            "work_queue_path": str(tmp_path / "docs" / "Work-Queue" / "WORK_QUEUE.json"),
        }
        session_log_path = await router._document_in_session_log(
            [], work_queue_updates, str(tmp_path / "develop_log.json")
        )
        assert session_log_path.exists()
        content = session_log_path.read_text(encoding="utf-8")
        assert "0** intent events" in content


# ---------------------------------------------------------------------------
# develop_system (lines 1742-1828) — integration via mocked sub-methods
# ---------------------------------------------------------------------------


class TestDevelopSystem:
    @pytest.mark.asyncio
    async def test_develop_system_healthy_on_first_iteration(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        (tmp_path / "state" / "reports").mkdir(parents=True, exist_ok=True)

        iteration_log = {
            "iteration": 1,
            "timestamp": "2026-01-01T00:00:00",
            "steps": {"analyze": {"status": "success", "summary": {}}, "heal": {"status": "skipped"}},
            "cultivation": {
                "intent_captured": {
                    "type": "system_health_achieved",
                    "iteration": 1,
                    "timestamp": "2026-01-01T00:00:00",
                    "message": "healthy",
                    "state": {"broken_files": 0, "working_files": 10},
                    "actions_that_helped": [],
                },
                "ten_minute_plan": {
                    "status": "healthy",
                    "max_items": 3,
                    "suggested_items": ["1. Validate workflows"],
                },
            },
        }
        intent_event = iteration_log["cultivation"]["intent_captured"]

        router._perform_iteration = AsyncMock(
            return_value=(iteration_log, intent_event, 0, False)
        )

        result = await router.develop_system(max_iterations=3, halt_on_error=False)

        assert result["status"] == "success"
        assert result["iterations"] == 1
        assert result["intent_events"] == 1
        assert Path(result["log_path"]).exists()

    @pytest.mark.asyncio
    async def test_develop_system_halted_on_analyze_fail(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        (tmp_path / "state" / "reports").mkdir(parents=True, exist_ok=True)

        halted_log = {
            "iteration": 1,
            "timestamp": "2026-01-01T00:00:00",
            "steps": {},
            "cultivation": {},
            "halted": True,
            "halt_reason": "analyze_failed",
        }
        router._perform_iteration = AsyncMock(
            return_value=(halted_log, None, 0, True)
        )

        result = await router.develop_system(max_iterations=3, halt_on_error=True)

        assert result["status"] == "success"
        assert result["iterations"] == 1

    @pytest.mark.asyncio
    async def test_develop_system_runs_multiple_iterations(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        (tmp_path / "state" / "reports").mkdir(parents=True, exist_ok=True)

        broken_log = {
            "iteration": 1,
            "timestamp": "2026-01-01T00:00:00",
            "steps": {},
            "cultivation": {
                "ten_minute_plan": {
                    "status": "healing_in_progress",
                    "max_items": 1,
                    "suggested_items": ["1. Continue heal cycle"],
                }
            },
        }
        router._perform_iteration = AsyncMock(
            return_value=(broken_log, None, 2, False)
        )

        result = await router.develop_system(max_iterations=2, halt_on_error=False)

        assert result["status"] == "success"
        assert result["iterations"] == 2
        assert router._perform_iteration.call_count == 2


# ---------------------------------------------------------------------------
# _perform_iteration (lines 1589-1656)
# ---------------------------------------------------------------------------


class TestPerformIteration:
    @pytest.mark.asyncio
    async def test_healthy_result_returns_intent_event(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)

        router.analyze_system = AsyncMock(
            return_value={
                "status": "success",
                "summary": {"working_files": 10, "broken_files": 0},
            }
        )
        router._maybe_heal = AsyncMock(return_value={"status": "skipped"})

        log, intent_event, broken_count, halted = await router._perform_iteration(
            iteration_index=1, halt_on_error=False, prev_state=None
        )

        assert not halted
        assert broken_count == 0
        assert intent_event is not None
        assert intent_event["type"] == "system_health_achieved"
        assert log["steps"]["analyze"]["status"] == "success"

    @pytest.mark.asyncio
    async def test_analyze_failed_with_halt_on_error_halts(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)

        router.analyze_system = AsyncMock(
            return_value={"status": "failed", "summary": {}}
        )

        _log, _intent_event, _broken_count, halted = await router._perform_iteration(
            iteration_index=1, halt_on_error=True, prev_state=None
        )

        assert halted is True
        assert _log.get("halt_reason") == "analyze_failed"
        assert _intent_event is None

    @pytest.mark.asyncio
    async def test_analyze_failed_without_halt_continues(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)

        router.analyze_system = AsyncMock(
            return_value={"status": "failed", "summary": {}}
        )
        router._maybe_heal = AsyncMock(return_value={"status": "skipped"})

        _log2, _intent2, _broken2, halted = await router._perform_iteration(
            iteration_index=1, halt_on_error=False, prev_state=None
        )

        assert not halted

    @pytest.mark.asyncio
    async def test_iteration_exception_returns_halted_based_on_flag(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)

        router.analyze_system = AsyncMock(side_effect=RuntimeError("analyzer exploded"))

        log, _intent_event, _broken_count, halted = await router._perform_iteration(
            iteration_index=1, halt_on_error=True, prev_state=None
        )

        assert halted is True
        assert "error" in log
        assert _intent_event is None

    @pytest.mark.asyncio
    async def test_iteration_with_broken_files_calls_heal(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)

        router.analyze_system = AsyncMock(
            return_value={
                "status": "success",
                "summary": {"working_files": 8, "broken_files": 3},
            }
        )
        router._maybe_heal = AsyncMock(
            return_value={"status": "success", "actions": ["deps_installed"]}
        )

        _log3, _intent3, broken_count, _halted3 = await router._perform_iteration(
            iteration_index=2, halt_on_error=False, prev_state={"broken_files": 5}
        )

        assert broken_count == 3
        assert _intent3 is None
        router._maybe_heal.assert_called_once_with(3, False)
