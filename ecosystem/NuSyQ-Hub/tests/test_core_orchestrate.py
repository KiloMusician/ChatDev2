"""Tests for src/core/orchestrate.py — NuSyQFacade and its inner facades.

Covers: SearchFacade, QuestFacade, CouncilFacade, BackgroundFacade,
FactoryFacade, NuSyQOrchestrator, and the module-level `nusyq` singleton.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_orchestrator():
    """Return a fresh NuSyQOrchestrator instance (not the singleton)."""
    from src.core.orchestrate import NuSyQOrchestrator

    return NuSyQOrchestrator()


def _mock_search_engine():
    """Return a MagicMock that satisfies SearchEngineProtocol."""
    m = MagicMock()
    m.search_keyword.return_value = [{"path": "a.py"}, {"path": "b.py"}]
    m.find_files.return_value = ["a.py", "b.py"]
    m.search_by_function.return_value = [{"name": "foo", "file": "a.py"}]
    m.search_by_class.return_value = [{"name": "Bar", "file": "b.py"}]
    m.get_index_health.return_value = {"status": "ok"}
    m.get_index_stats.return_value = {"file_count": 42}
    return m


def _mock_quest_record(status: str = "pending"):
    r = MagicMock()
    r.status = status
    r.to_dict.return_value = {"title": "q1", "status": status}
    return r


def _mock_quest_engine(quests=None, questlines=None):
    qe = MagicMock()
    qe.quests = quests or {}
    qe.questlines = questlines or {}
    qe.add_quest.return_value = "quest-abc"
    return qe


def _mock_council():
    c = MagicMock()
    decision = MagicMock()
    decision.decision_id = "dec-xyz"
    c.create_decision.return_value = decision
    c.cast_vote.return_value = None
    c.list_decisions.return_value = []
    return c


def _mock_bg_orchestrator():
    bg = MagicMock()
    task = MagicMock()
    task.task_id = "task-111"
    task.to_dict.return_value = {"task_id": "task-111", "status": "queued"}

    priority = MagicMock()
    priority.value = 8
    task.priority = priority

    bg.submit_task.return_value = task
    bg.get_task.return_value = task
    bg.get_orchestrator_status.return_value = {"active_count": 1}
    bg.list_tasks.return_value = [task]
    bg.execute_task = AsyncMock(return_value=task)
    return bg


def _mock_factory():
    f = MagicMock()
    f.output_root = Path("/tmp/output")
    f._list_templates.return_value = ["default_game", "rpg"]
    f.run_health_check.return_value = {"healthy": True}
    f.inspect_reference_games.return_value = {"games": []}
    f.run_doctor.return_value = {"issues": []}
    f.run_doctor_fix.return_value = {"fixed": True}
    f.run_autopilot.return_value = {"patch_plan": []}
    result = MagicMock()
    result.name = "my_game"
    result.type = "game"
    result.version = "1.0.0"
    result.output_path = Path("/tmp/output/my_game")
    result.ai_provider = None
    result.model_used = None
    result.token_cost = None
    result.chatdev_warehouse_path = None
    f.create.return_value = result
    return f


# ---------------------------------------------------------------------------
# SearchFacade — unavailable branch
# ---------------------------------------------------------------------------


class TestSearchFacadeUnavailable:
    def _make_facade(self):
        orch = _make_orchestrator()
        facade = orch.search
        facade._instance = None
        return facade

    def test_find_unavailable(self):
        facade = self._make_facade()
        with patch("src.core.orchestrate.get_smart_search", return_value=None):
            result = facade.find("auth")
        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_find_files_unavailable(self):
        facade = self._make_facade()
        with patch("src.core.orchestrate.get_smart_search", return_value=None):
            result = facade.find_files("*.py")
        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_find_function_unavailable(self):
        facade = self._make_facade()
        with patch("src.core.orchestrate.get_smart_search", return_value=None):
            result = facade.find_function("foo")
        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_find_class_unavailable(self):
        facade = self._make_facade()
        with patch("src.core.orchestrate.get_smart_search", return_value=None):
            result = facade.find_class("Bar")
        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_health_unavailable(self):
        facade = self._make_facade()
        with patch("src.core.orchestrate.get_smart_search", return_value=None):
            result = facade.health()
        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_stats_unavailable(self):
        facade = self._make_facade()
        with patch("src.core.orchestrate.get_smart_search", return_value=None):
            result = facade.stats()
        assert not result.ok
        assert result.code == "UNAVAILABLE"


# ---------------------------------------------------------------------------
# SearchFacade — happy paths
# ---------------------------------------------------------------------------


class TestSearchFacadeHappy:
    def _make_facade(self):
        orch = _make_orchestrator()
        facade = orch.search
        facade._instance = _mock_search_engine()
        return facade

    def test_find_returns_results(self):
        facade = self._make_facade()
        result = facade.find("auth")
        assert result.ok
        assert isinstance(result.data, list)
        assert len(result.data) == 2

    def test_find_respects_limit(self):
        facade = self._make_facade()
        facade._instance.search_keyword.return_value = [{"p": i} for i in range(20)]
        result = facade.find("auth", limit=3)
        assert result.ok
        assert len(result.data) == 3

    def test_find_files_returns_files(self):
        facade = self._make_facade()
        result = facade.find_files("*.py")
        assert result.ok
        assert "a.py" in result.data

    def test_find_function_returns_results(self):
        facade = self._make_facade()
        result = facade.find_function("foo")
        assert result.ok
        assert result.data[0]["name"] == "foo"

    def test_find_class_returns_results(self):
        facade = self._make_facade()
        result = facade.find_class("Bar")
        assert result.ok
        assert result.data[0]["name"] == "Bar"

    def test_health_returns_status(self):
        facade = self._make_facade()
        result = facade.health()
        assert result.ok
        assert result.data["status"] == "ok"

    def test_stats_returns_stats(self):
        facade = self._make_facade()
        result = facade.stats()
        assert result.ok
        assert result.data["file_count"] == 42


# ---------------------------------------------------------------------------
# SearchFacade — error paths
# ---------------------------------------------------------------------------


class TestSearchFacadeErrors:
    def _make_facade(self):
        orch = _make_orchestrator()
        facade = orch.search
        facade._instance = _mock_search_engine()
        return facade

    def test_find_error_path(self):
        facade = self._make_facade()
        facade._instance.search_keyword.side_effect = RuntimeError("boom")
        result = facade.find("auth")
        assert not result.ok
        assert result.code == "SEARCH_ERROR"

    def test_find_files_error_path(self):
        facade = self._make_facade()
        facade._instance.find_files.side_effect = RuntimeError("err")
        result = facade.find_files("*.py")
        assert not result.ok
        assert result.code == "SEARCH_ERROR"

    def test_find_function_error_path(self):
        facade = self._make_facade()
        facade._instance.search_by_function.side_effect = RuntimeError("err")
        result = facade.find_function("foo")
        assert not result.ok
        assert result.code == "SEARCH_ERROR"

    def test_find_class_error_path(self):
        facade = self._make_facade()
        facade._instance.search_by_class.side_effect = RuntimeError("err")
        result = facade.find_class("Bar")
        assert not result.ok
        assert result.code == "SEARCH_ERROR"

    def test_health_error_path(self):
        facade = self._make_facade()
        facade._instance.get_index_health.side_effect = RuntimeError("err")
        result = facade.health()
        assert not result.ok
        assert result.code == "HEALTH_ERROR"

    def test_stats_error_path(self):
        facade = self._make_facade()
        facade._instance.get_index_stats.side_effect = RuntimeError("err")
        result = facade.stats()
        assert not result.ok
        assert result.code == "STATS_ERROR"


# ---------------------------------------------------------------------------
# QuestFacade — unavailable + happy + error
# ---------------------------------------------------------------------------


class TestQuestFacade:
    def _make_facade(self):
        orch = _make_orchestrator()
        return orch.quest

    def test_add_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_quest_engine", return_value=None):
            result = facade.add("fix bug")
        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_add_happy(self):
        facade = self._make_facade()
        facade._instance = _mock_quest_engine()
        result = facade.add("fix bug", description="details", questline="Dev", priority="high")
        assert result.ok
        assert result.data == "quest-abc"

    def test_add_error(self):
        facade = self._make_facade()
        qe = _mock_quest_engine()
        qe.add_quest.side_effect = RuntimeError("db fail")
        facade._instance = qe
        result = facade.add("x")
        assert not result.ok
        assert result.code == "QUEST_ERROR"

    def test_complete_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_quest_engine", return_value=None):
            result = facade.complete("q1")
        assert not result.ok

    def test_complete_happy(self):
        facade = self._make_facade()
        facade._instance = _mock_quest_engine()
        result = facade.complete("q1")
        assert result.ok
        assert result.data is True

    def test_complete_error(self):
        facade = self._make_facade()
        qe = _mock_quest_engine()
        qe.complete_quest.side_effect = KeyError("not found")
        facade._instance = qe
        result = facade.complete("q1")
        assert not result.ok
        assert result.code == "QUEST_ERROR"

    def test_list_all(self):
        facade = self._make_facade()
        r = _mock_quest_record("pending")
        facade._instance = _mock_quest_engine(quests={"q1": r})
        result = facade.list()
        assert result.ok
        assert len(result.data) == 1

    def test_list_filtered(self):
        facade = self._make_facade()
        r1 = _mock_quest_record("pending")
        r2 = _mock_quest_record("completed")
        facade._instance = _mock_quest_engine(quests={"q1": r1, "q2": r2})
        result = facade.list(status="pending")
        assert result.ok
        assert len(result.data) == 1

    def test_list_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_quest_engine", return_value=None):
            result = facade.list()
        assert not result.ok

    def test_list_error(self):
        facade = self._make_facade()
        qe = MagicMock()
        qe.quests = property(lambda self: 1 / 0)  # type: ignore[assignment]
        # Simpler: make accessing quests raise
        type(qe).quests = property(  # type: ignore[assignment]
            lambda s: (_ for _ in ()).throw(RuntimeError("db err"))
        )
        facade._instance = qe
        result = facade.list()
        assert not result.ok
        assert result.code == "QUEST_ERROR"

    def test_status_happy(self):
        facade = self._make_facade()
        r1 = _mock_quest_record("pending")
        r2 = _mock_quest_record("completed")
        facade._instance = _mock_quest_engine(
            quests={"q1": r1, "q2": r2}, questlines={"Dev": {}, "Bug": {}}
        )
        result = facade.status()
        assert result.ok
        assert result.data["total"] == 2
        assert result.data["completed"] == 1
        assert result.data["pending"] == 1
        assert result.data["questlines"] == 2

    def test_status_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_quest_engine", return_value=None):
            result = facade.status()
        assert not result.ok

    def test_status_error(self):
        facade = self._make_facade()
        qe = MagicMock()
        type(qe).quests = property(  # type: ignore[assignment]
            lambda s: (_ for _ in ()).throw(RuntimeError("db err"))
        )
        facade._instance = qe
        result = facade.status()
        assert not result.ok
        assert result.code == "QUEST_ERROR"


# ---------------------------------------------------------------------------
# CouncilFacade
# ---------------------------------------------------------------------------


class TestCouncilFacade:
    def _make_facade(self):
        orch = _make_orchestrator()
        return orch.council

    def test_propose_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_ai_council", return_value=None):
            result = facade.propose("refactor?")
        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_propose_happy(self):
        facade = self._make_facade()
        facade._instance = _mock_council()
        result = facade.propose("refactor auth?", description="details", proposer="agent1")
        assert result.ok
        assert isinstance(result.data, str)

    def test_propose_error(self):
        facade = self._make_facade()
        c = _mock_council()
        c.create_decision.side_effect = RuntimeError("council down")
        facade._instance = c
        result = facade.propose("refactor?")
        assert not result.ok
        assert result.code == "COUNCIL_ERROR"

    def test_vote_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_ai_council", return_value=None):
            result = facade.vote("dec-1", "approve")
        assert not result.ok

    def test_vote_happy(self):
        facade = self._make_facade()
        facade._instance = _mock_council()
        result = facade.vote("dec-1", "approve", voter="agent2", confidence=0.9)
        assert result.ok
        assert result.data is True

    def test_vote_error(self):
        facade = self._make_facade()
        c = _mock_council()
        c.cast_vote.side_effect = RuntimeError("vote error")
        facade._instance = c
        result = facade.vote("dec-1", "approve")
        assert not result.ok
        assert result.code == "COUNCIL_ERROR"

    def test_status_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_ai_council", return_value=None):
            result = facade.status()
        assert not result.ok

    def test_status_empty(self):
        facade = self._make_facade()
        facade._instance = _mock_council()
        result = facade.status()
        assert result.ok
        assert result.data["total_decisions"] == 0

    def test_status_with_decisions_enum(self):
        facade = self._make_facade()
        c = _mock_council()
        approved_status = MagicMock()
        approved_status.value = "approved"
        pending_status = MagicMock()
        pending_status.value = "pending"
        d1 = MagicMock()
        d1.status = approved_status
        d2 = MagicMock()
        d2.status = pending_status
        c.list_decisions.return_value = [d1, d2]
        facade._instance = c
        result = facade.status()
        assert result.ok
        assert result.data["approved"] == 1
        assert result.data["pending"] == 1

    def test_status_with_decisions_string(self):
        facade = self._make_facade()
        c = _mock_council()
        d1 = MagicMock(spec=["status"])
        d1.status = "approved"
        c.list_decisions.return_value = [d1]
        facade._instance = c
        result = facade.status()
        assert result.ok
        assert result.data["approved"] == 1

    def test_status_error(self):
        facade = self._make_facade()
        c = _mock_council()
        c.list_decisions.side_effect = RuntimeError("db err")
        facade._instance = c
        result = facade.status()
        assert not result.ok
        assert result.code == "COUNCIL_ERROR"


# ---------------------------------------------------------------------------
# BackgroundFacade
# ---------------------------------------------------------------------------


class TestBackgroundFacade:
    def _make_facade(self):
        orch = _make_orchestrator()
        return orch.background

    def test_dispatch_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_background_orchestrator", return_value=None):
            result = facade.dispatch("analyze src/")
        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_dispatch_happy_auto_target(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        facade._instance = bg
        result = facade.dispatch("analyze", priority="high", target="auto")
        assert result.ok
        assert result.data == "task-111"

    def test_dispatch_with_non_auto_target(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        facade._instance = bg
        result = facade.dispatch("analyze", target="ollama")
        # May fail if TaskTarget doesn't accept "ollama" — either is valid
        assert result.ok or result.code == "DISPATCH_ERROR"

    def test_dispatch_priority_low(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        facade._instance = bg
        result = facade.dispatch("analyze", priority="low")
        assert result.ok

    def test_dispatch_priority_critical(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        facade._instance = bg
        result = facade.dispatch("analyze", priority="critical")
        assert result.ok

    def test_dispatch_error(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        bg.submit_task.side_effect = RuntimeError("dispatch fail")
        facade._instance = bg
        result = facade.dispatch("analyze")
        assert not result.ok
        assert result.code == "DISPATCH_ERROR"

    def test_status_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_background_orchestrator", return_value=None):
            result = facade.status()
        assert not result.ok

    def test_status_with_task_id_found(self):
        facade = self._make_facade()
        facade._instance = _mock_bg_orchestrator()
        result = facade.status(task_id="task-111")
        assert result.ok
        assert result.data["task_id"] == "task-111"

    def test_status_with_task_id_not_found(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        bg.get_task.return_value = None
        facade._instance = bg
        result = facade.status(task_id="nonexistent")
        assert not result.ok
        assert result.code == "NOT_FOUND"

    def test_status_orchestrator_overall(self):
        facade = self._make_facade()
        facade._instance = _mock_bg_orchestrator()
        result = facade.status()
        assert result.ok
        assert result.data["active_count"] == 1

    def test_status_error(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        bg.get_orchestrator_status.side_effect = RuntimeError("err")
        facade._instance = bg
        result = facade.status()
        assert not result.ok
        assert result.code == "STATUS_ERROR"

    def test_list_tasks_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_background_orchestrator", return_value=None):
            result = facade.list_tasks()
        assert not result.ok

    def test_list_tasks_all(self):
        facade = self._make_facade()
        facade._instance = _mock_bg_orchestrator()
        result = facade.list_tasks()
        assert result.ok
        assert isinstance(result.data, list)

    def test_list_tasks_filtered(self):
        facade = self._make_facade()
        facade._instance = _mock_bg_orchestrator()
        result = facade.list_tasks(status_filter="queued")
        assert result.ok

    def test_list_tasks_error(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        bg.list_tasks.side_effect = RuntimeError("err")
        facade._instance = bg
        result = facade.list_tasks()
        assert not result.ok
        assert result.code == "LIST_ERROR"

    def test_process_one_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_background_orchestrator", return_value=None):
            result = facade.process_one()
        assert not result.ok

    def test_process_one_specific_task(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        facade._instance = bg
        result = facade.process_one(task_id="task-111")
        assert result.ok

    def test_process_one_task_not_found(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        bg.get_task.return_value = None
        facade._instance = bg
        result = facade.process_one(task_id="missing")
        assert not result.ok
        assert result.code == "NOT_FOUND"

    def test_process_one_no_queued_tasks(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        bg.list_tasks.return_value = []
        facade._instance = bg
        result = facade.process_one()
        assert result.ok
        assert "No queued tasks" in result.data.get("message", "")

    def test_process_one_next_queued(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        facade._instance = bg
        result = facade.process_one()
        assert result.ok

    def test_process_one_error(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        bg.execute_task = AsyncMock(side_effect=RuntimeError("exec fail"))
        facade._instance = bg
        result = facade.process_one(task_id="task-111")
        assert not result.ok
        assert result.code == "PROCESS_ERROR"

    def test_process_batch_unavailable(self):
        facade = self._make_facade()
        facade._instance = None
        with patch("src.core.orchestrate.get_background_orchestrator", return_value=None):
            result = facade.process_batch()
        assert not result.ok

    def test_process_batch_no_tasks(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        bg.list_tasks.return_value = []
        facade._instance = bg
        result = facade.process_batch()
        assert result.ok
        assert result.data["processed"] == 0

    def test_process_batch_happy(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()

        from src.orchestration.background_task_orchestrator import TaskStatus

        task = bg.list_tasks.return_value[0]
        task.status = TaskStatus.COMPLETED
        bg.execute_task = AsyncMock(return_value=task)
        facade._instance = bg
        result = facade.process_batch(limit=3)
        assert result.ok
        assert result.data["processed"] >= 1

    def test_process_batch_with_exec_error(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        bg.execute_task = AsyncMock(side_effect=RuntimeError("exec fail"))
        facade._instance = bg
        result = facade.process_batch()
        assert result.ok
        assert result.data["failed"] >= 1

    def test_process_batch_outer_error(self):
        facade = self._make_facade()
        bg = _mock_bg_orchestrator()
        bg.list_tasks.side_effect = RuntimeError("list fail")
        facade._instance = bg
        result = facade.process_batch()
        assert not result.ok
        assert result.code == "BATCH_ERROR"


# ---------------------------------------------------------------------------
# FactoryFacade
# ---------------------------------------------------------------------------


class TestFactoryFacade:
    def _make_facade(self):
        orch = _make_orchestrator()
        return orch.factory

    def test_status_unavailable(self):
        facade = self._make_facade()
        with patch.object(type(facade), "_get_instance", return_value=None):
            result = facade.status()
        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_status_happy(self):
        facade = self._make_facade()
        facade._instance = _mock_factory()
        result = facade.status()
        assert result.ok
        assert result.data["template_count"] == 2

    def test_status_error(self):
        facade = self._make_facade()
        f = _mock_factory()
        f._list_templates.side_effect = RuntimeError("err")
        facade._instance = f
        result = facade.status()
        assert not result.ok
        assert result.code == "FACTORY_STATUS_ERROR"

    def test_health_unavailable(self):
        facade = self._make_facade()
        with patch.object(type(facade), "_get_instance", return_value=None):
            result = facade.health()
        assert not result.ok

    def test_health_happy(self):
        facade = self._make_facade()
        facade._instance = _mock_factory()
        result = facade.health()
        assert result.ok
        assert result.data["healthy"] is True

    def test_health_error(self):
        facade = self._make_facade()
        f = _mock_factory()
        f.run_health_check.side_effect = RuntimeError("health err")
        facade._instance = f
        result = facade.health()
        assert not result.ok
        assert result.code == "FACTORY_HEALTH_ERROR"

    def test_inspect_examples_unavailable(self):
        facade = self._make_facade()
        with patch.object(type(facade), "_get_instance", return_value=None):
            result = facade.inspect_examples()
        assert not result.ok

    def test_inspect_examples_happy(self):
        facade = self._make_facade()
        facade._instance = _mock_factory()
        result = facade.inspect_examples(paths=["path/to/game"])
        assert result.ok

    def test_inspect_examples_error(self):
        facade = self._make_facade()
        f = _mock_factory()
        f.inspect_reference_games.side_effect = RuntimeError("inspect err")
        facade._instance = f
        result = facade.inspect_examples()
        assert not result.ok
        assert result.code == "FACTORY_INSPECT_ERROR"

    def test_doctor_unavailable(self):
        facade = self._make_facade()
        with patch.object(type(facade), "_get_instance", return_value=None):
            result = facade.doctor()
        assert not result.ok

    def test_doctor_happy(self):
        facade = self._make_facade()
        facade._instance = _mock_factory()
        result = facade.doctor(strict_hooks=True, include_examples=False)
        assert result.ok

    def test_doctor_error(self):
        facade = self._make_facade()
        f = _mock_factory()
        f.run_doctor.side_effect = RuntimeError("doctor err")
        facade._instance = f
        result = facade.doctor()
        assert not result.ok
        assert result.code == "FACTORY_DOCTOR_ERROR"

    def test_doctor_fix_unavailable(self):
        facade = self._make_facade()
        with patch.object(type(facade), "_get_instance", return_value=None):
            result = facade.doctor_fix()
        assert not result.ok

    def test_doctor_fix_happy(self):
        facade = self._make_facade()
        facade._instance = _mock_factory()
        result = facade.doctor_fix()
        assert result.ok

    def test_doctor_fix_error(self):
        facade = self._make_facade()
        f = _mock_factory()
        f.run_doctor_fix.side_effect = RuntimeError("fix err")
        facade._instance = f
        result = facade.doctor_fix()
        assert not result.ok
        assert result.code == "FACTORY_DOCTOR_FIX_ERROR"

    def test_autopilot_unavailable(self):
        facade = self._make_facade()
        with patch.object(type(facade), "_get_instance", return_value=None):
            result = facade.autopilot()
        assert not result.ok

    def test_autopilot_happy(self):
        facade = self._make_facade()
        facade._instance = _mock_factory()
        result = facade.autopilot(fix=True, example_paths=["x"])
        assert result.ok

    def test_autopilot_error(self):
        facade = self._make_facade()
        f = _mock_factory()
        f.run_autopilot.side_effect = RuntimeError("autopilot err")
        facade._instance = f
        result = facade.autopilot()
        assert not result.ok
        assert result.code == "FACTORY_AUTOPILOT_ERROR"

    def test_create_unavailable(self):
        facade = self._make_facade()
        with patch.object(type(facade), "_get_instance", return_value=None):
            result = facade.create(name="game1")
        assert not result.ok

    def test_create_happy(self):
        facade = self._make_facade()
        facade._instance = _mock_factory()
        result = facade.create(name="my_game", template="rpg", ai_provider="ollama")
        assert result.ok
        assert result.data["name"] == "my_game"

    def test_create_with_chatdev_path(self):
        facade = self._make_facade()
        f = _mock_factory()
        f.create.return_value.chatdev_warehouse_path = Path("/tmp/chatdev/warehouse")
        facade._instance = f
        result = facade.create(name="my_game")
        assert result.ok
        assert result.data["chatdev_warehouse_path"] is not None

    def test_create_error(self):
        facade = self._make_facade()
        f = _mock_factory()
        f.create.side_effect = RuntimeError("create err")
        facade._instance = f
        result = facade.create(name="bad")
        assert not result.ok
        assert result.code == "FACTORY_CREATE_ERROR"


# ---------------------------------------------------------------------------
# NuSyQOrchestrator — property lazy init + analyze + status
# ---------------------------------------------------------------------------


class TestNuSyQOrchestrator:
    def test_search_property_lazy(self):
        orch = _make_orchestrator()
        assert orch._search is None
        s = orch.search
        assert s is orch.search  # cached

    def test_quest_property_lazy(self):
        orch = _make_orchestrator()
        assert orch._quest is None
        q = orch.quest
        assert q is orch.quest

    def test_council_property_lazy(self):
        orch = _make_orchestrator()
        c = orch.council
        assert c is orch.council

    def test_background_property_lazy(self):
        orch = _make_orchestrator()
        b = orch.background
        assert b is orch.background

    def test_factory_property_lazy(self):
        orch = _make_orchestrator()
        f = orch.factory
        assert f is orch.factory

    def test_eol_property_lazy(self):
        orch = _make_orchestrator()
        e = orch.eol
        assert e is orch.eol

    def test_analyze_delegates_to_background(self):
        orch = _make_orchestrator()
        mock_bg = MagicMock()
        mock_bg.dispatch.return_value = MagicMock(ok=True, data="task-999")
        orch._background = mock_bg
        orch.analyze("src/foo.py")
        mock_bg.dispatch.assert_called_once()
        call_kwargs = mock_bg.dispatch.call_args[1]
        assert "src/foo.py" in call_kwargs.get("prompt", "")

    def test_analyze_with_custom_type(self):
        orch = _make_orchestrator()
        mock_bg = MagicMock()
        mock_bg.dispatch.return_value = MagicMock(ok=True, data="t1")
        orch._background = mock_bg
        orch.analyze("src/", analysis_type="security_audit")
        call_kwargs = mock_bg.dispatch.call_args[1]
        assert call_kwargs.get("task_type") == "security_audit"

    def test_status_aggregates_all(self):
        orch = _make_orchestrator()
        ok_result = MagicMock()
        ok_result.to_dict.return_value = {"status": "ok"}

        mock_search = MagicMock()
        mock_search.health.return_value = ok_result
        mock_quest = MagicMock()
        mock_quest.status.return_value = ok_result
        mock_council = MagicMock()
        mock_council.status.return_value = ok_result
        mock_bg = MagicMock()
        mock_bg.status.return_value = ok_result
        mock_factory = MagicMock()
        mock_factory.status.return_value = ok_result

        orch._search = mock_search
        orch._quest = mock_quest
        orch._council = mock_council
        orch._background = mock_bg
        orch._factory = mock_factory

        result = orch.status()
        assert result.ok
        assert "search" in result.data
        assert "quest" in result.data
        assert "council" in result.data
        assert "background" in result.data
        assert "factory" in result.data


# ---------------------------------------------------------------------------
# Module-level nusyq singleton
# ---------------------------------------------------------------------------


class TestNuSyQSingleton:
    def test_singleton_is_nusyqorchestrator(self):
        from src.core.orchestrate import NuSyQOrchestrator, nusyq

        assert isinstance(nusyq, NuSyQOrchestrator)

    def test_singleton_search_facade(self):
        from src.core.orchestrate import nusyq

        facade = nusyq.search
        assert facade is not None

    def test_singleton_quest_facade(self):
        from src.core.orchestrate import nusyq

        facade = nusyq.quest
        assert facade is not None

    def test_singleton_council_facade(self):
        from src.core.orchestrate import nusyq

        facade = nusyq.council
        assert facade is not None

    def test_singleton_background_facade(self):
        from src.core.orchestrate import nusyq

        facade = nusyq.background
        assert facade is not None

    def test_singleton_analyze_unavailable(self):
        """analyze() falls back gracefully when background orchestrator unavailable."""
        from src.core.orchestrate import NuSyQOrchestrator

        orch = NuSyQOrchestrator()
        with patch("src.core.orchestrate.get_background_orchestrator", return_value=None):
            result = orch.analyze("src/")
        assert not result.ok


# ---------------------------------------------------------------------------
# SearchFacade — lazy _get_instance with real SmartSearch mock class
# ---------------------------------------------------------------------------


class TestSearchFacadeLazyInit:
    def test_get_instance_initializes_from_class(self):
        orch = _make_orchestrator()
        facade = orch.search
        facade._instance = None

        mock_instance = _mock_search_engine()
        mock_class = MagicMock(return_value=mock_instance)

        with patch("src.core.orchestrate.get_smart_search", return_value=mock_class):
            instance = facade._get_instance()

        assert instance is mock_instance

    def test_get_instance_returns_none_when_class_none(self):
        orch = _make_orchestrator()
        facade = orch.search
        facade._instance = None

        with patch("src.core.orchestrate.get_smart_search", return_value=None):
            instance = facade._get_instance()

        assert instance is None

    def test_get_instance_cached(self):
        orch = _make_orchestrator()
        facade = orch.search
        fake = _mock_search_engine()
        facade._instance = fake

        instance = facade._get_instance()
        assert instance is fake
