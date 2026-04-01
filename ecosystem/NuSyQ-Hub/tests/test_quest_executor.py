"""Tests for src/quest/quest_executor.py."""

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_executor(tmp_path: Path):
    """Create a QuestExecutor rooted at tmp_path."""
    from src.quest.quest_executor import QuestExecutor
    return QuestExecutor(tmp_path)


def _write_quest_log(tmp_path: Path, lines: list) -> Path:
    quest_log = tmp_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    quest_log.parent.mkdir(parents=True, exist_ok=True)
    quest_log.write_text("\n".join(json.dumps(entry) for entry in lines) + "\n", encoding="utf-8")
    return quest_log


def _write_action_catalog(tmp_path: Path, wired_actions: dict) -> Path:
    catalog = tmp_path / "config" / "action_catalog.json"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(json.dumps({"wired_actions": wired_actions}), encoding="utf-8")
    return catalog


# ===========================================================================
# Quest dataclass
# ===========================================================================

class TestQuestDataclass:
    def test_from_jsonl_line_valid(self):
        from src.quest.quest_executor import Quest
        line = json.dumps({
            "timestamp": "2026-01-01T00:00:00",
            "task_type": "analyze",
            "description": "Analyze code quality",
            "status": "active",
        })
        q = Quest.from_jsonl_line(line)
        assert q is not None
        assert q.task_type == "analyze"
        assert q.status == "active"
        assert q.result is None

    def test_from_jsonl_line_with_result(self):
        from src.quest.quest_executor import Quest
        line = json.dumps({
            "timestamp": "2026-01-01T00:00:00",
            "task_type": "test",
            "description": "Run tests",
            "status": "completed",
            "result": {"exit_code": 0},
        })
        q = Quest.from_jsonl_line(line)
        assert q is not None
        assert q.result == {"exit_code": 0}

    def test_from_jsonl_line_invalid_json(self):
        from src.quest.quest_executor import Quest
        q = Quest.from_jsonl_line("{not valid json")
        assert q is None

    def test_from_jsonl_line_empty_string(self):
        from src.quest.quest_executor import Quest
        q = Quest.from_jsonl_line("")
        assert q is None

    def test_from_jsonl_line_missing_fields_defaults(self):
        from src.quest.quest_executor import Quest
        line = json.dumps({})
        q = Quest.from_jsonl_line(line)
        assert q is not None
        assert q.task_type == ""
        assert q.status == "unknown"

    def test_quest_dataclass_fields(self):
        from src.quest.quest_executor import Quest
        q = Quest(
            timestamp="ts",
            task_type="debug",
            description="Fix bug",
            status="active",
        )
        assert q.timestamp == "ts"
        assert q.description == "Fix bug"


# ===========================================================================
# Action dataclass
# ===========================================================================

class TestActionDataclass:
    def test_action_fields(self):
        from src.quest.quest_executor import Action
        a = Action(
            name="brief",
            invocation="python scripts/start_nusyq.py brief",
            safety_level="safe",
            description="Run brief",
            expected_outputs=["status"],
        )
        assert a.name == "brief"
        assert a.safety_level == "safe"
        assert "brief" in a.invocation
        assert a.expected_outputs == ["status"]


# ===========================================================================
# QuestExecutor.load_active_quests
# ===========================================================================

class TestLoadActiveQuests:
    def test_returns_empty_when_no_file(self, tmp_path):
        executor = _make_executor(tmp_path)
        assert executor.load_active_quests() == []

    def test_loads_active_status(self, tmp_path):
        _write_quest_log(tmp_path, [
            {"task_type": "analyze", "description": "d", "status": "active"},
            {"task_type": "test", "description": "d2", "status": "completed"},
        ])
        executor = _make_executor(tmp_path)
        quests = executor.load_active_quests()
        assert len(quests) == 1
        assert quests[0].task_type == "analyze"

    def test_loads_in_progress_status(self, tmp_path):
        _write_quest_log(tmp_path, [
            {"task_type": "review", "description": "d", "status": "in_progress"},
        ])
        executor = _make_executor(tmp_path)
        quests = executor.load_active_quests()
        assert len(quests) == 1

    def test_skips_failed_and_blocked(self, tmp_path):
        _write_quest_log(tmp_path, [
            {"task_type": "x", "description": "d", "status": "failed"},
            {"task_type": "y", "description": "d", "status": "blocked"},
        ])
        executor = _make_executor(tmp_path)
        assert executor.load_active_quests() == []

    def test_skips_invalid_lines(self, tmp_path):
        log_path = tmp_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            "not-json\n" + json.dumps({"task_type": "t", "description": "d", "status": "active"}),
            encoding="utf-8",
        )
        executor = _make_executor(tmp_path)
        quests = executor.load_active_quests()
        assert len(quests) == 1

    def test_returns_most_recent_first(self, tmp_path):
        _write_quest_log(tmp_path, [
            {"task_type": "first", "description": "d", "status": "active"},
            {"task_type": "second", "description": "d", "status": "active"},
        ])
        executor = _make_executor(tmp_path)
        quests = executor.load_active_quests()
        # reversed() → second entry comes first
        assert quests[0].task_type == "second"


# ===========================================================================
# QuestExecutor.load_action_catalog
# ===========================================================================

class TestLoadActionCatalog:
    def test_returns_empty_when_no_file(self, tmp_path):
        executor = _make_executor(tmp_path)
        assert executor.load_action_catalog() == {}

    def test_parses_wired_actions(self, tmp_path):
        _write_action_catalog(tmp_path, {
            "brief": {"safety": "safe", "desc": "Run brief", "outputs": ["status"]},
        })
        executor = _make_executor(tmp_path)
        catalog = executor.load_action_catalog()
        assert "brief" in catalog
        assert catalog["brief"].safety_level == "safe"
        assert "brief" in catalog["brief"].invocation

    def test_safety_defaults_to_moderate(self, tmp_path):
        _write_action_catalog(tmp_path, {
            "mystery": {"desc": "Unknown action"},
        })
        executor = _make_executor(tmp_path)
        catalog = executor.load_action_catalog()
        assert catalog["mystery"].safety_level == "moderate"

    def test_invalid_json_returns_empty(self, tmp_path):
        catalog_path = tmp_path / "config" / "action_catalog.json"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text("{corrupt json", encoding="utf-8")
        executor = _make_executor(tmp_path)
        assert executor.load_action_catalog() == {}


# ===========================================================================
# QuestExecutor.match_quest_to_action
# ===========================================================================

class TestMatchQuestToAction:
    def _make_action(self, name, desc=""):
        from src.quest.quest_executor import Action
        return Action(
            name=name,
            invocation=f"python scripts/start_nusyq.py {name}",
            safety_level="safe",
            description=desc,
            expected_outputs=[],
        )

    def test_direct_task_type_match(self, tmp_path):
        from src.quest.quest_executor import Quest
        executor = _make_executor(tmp_path)
        quest = Quest(timestamp="", task_type="brief", description="Run brief", status="active")
        actions = {"brief": self._make_action("brief")}
        matched = executor.match_quest_to_action(quest, actions)
        assert matched is not None
        assert matched.name == "brief"

    def test_fuzzy_match_by_description_keyword(self, tmp_path):
        from src.quest.quest_executor import Quest
        executor = _make_executor(tmp_path)
        quest = Quest(timestamp="", task_type="generic", description="run brief now", status="active")
        actions = {"brief": self._make_action("brief")}
        matched = executor.match_quest_to_action(quest, actions)
        assert matched is not None
        assert matched.name == "brief"

    def test_no_match_returns_none(self, tmp_path):
        from src.quest.quest_executor import Quest
        executor = _make_executor(tmp_path)
        quest = Quest(timestamp="", task_type="unknown_xyz", description="totally unrelated", status="active")
        # action name "zzznotpresent" won't appear in the quest description
        actions = {"zzznotpresent": self._make_action("zzznotpresent", desc="zzznotpresent action")}
        matched = executor.match_quest_to_action(quest, actions)
        assert matched is None

    def test_empty_actions_returns_none(self, tmp_path):
        from src.quest.quest_executor import Quest
        executor = _make_executor(tmp_path)
        quest = Quest(timestamp="", task_type="analyze", description="d", status="active")
        assert executor.match_quest_to_action(quest, {}) is None


# ===========================================================================
# QuestExecutor.execute_action
# ===========================================================================

class TestExecuteAction:
    def _make_safe_action(self, name="brief"):
        from src.quest.quest_executor import Action
        return Action(
            name=name,
            invocation=f"python scripts/start_nusyq.py {name}",
            safety_level="safe",
            description="Test action",
            expected_outputs=[],
        )

    def _make_quest(self, task_type="brief", description="run brief"):
        from src.quest.quest_executor import Quest
        return Quest(timestamp="", task_type=task_type, description=description, status="active")

    def test_successful_execution(self, tmp_path):
        executor = _make_executor(tmp_path)
        action = self._make_safe_action()
        quest = self._make_quest()
        fake_result = MagicMock()
        fake_result.returncode = 0
        fake_result.stdout = "ok"
        fake_result.stderr = ""
        with patch("src.quest.quest_executor.subprocess.run", return_value=fake_result):
            result = executor.execute_action(action, quest)
        assert result["status"] == "completed"
        assert result["exit_code"] == 0

    def test_failed_execution_nonzero_exit(self, tmp_path):
        executor = _make_executor(tmp_path)
        action = self._make_safe_action()
        quest = self._make_quest()
        fake_result = MagicMock()
        fake_result.returncode = 1
        fake_result.stdout = ""
        fake_result.stderr = "error text"
        with patch("src.quest.quest_executor.subprocess.run", return_value=fake_result):
            result = executor.execute_action(action, quest)
        assert result["status"] == "failed"

    def test_timeout_returns_failed(self, tmp_path):
        import subprocess
        executor = _make_executor(tmp_path)
        action = self._make_safe_action()
        quest = self._make_quest()
        with patch("src.quest.quest_executor.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 120)):
            result = executor.execute_action(action, quest)
        assert result["status"] == "failed"
        assert "Timeout" in result["error"]

    def test_exception_returns_failed(self, tmp_path):
        executor = _make_executor(tmp_path)
        action = self._make_safe_action()
        quest = self._make_quest()
        with patch("src.quest.quest_executor.subprocess.run", side_effect=OSError("boom")):
            result = executor.execute_action(action, quest)
        assert result["status"] == "failed"
        assert "boom" in result["error"]

    def test_action_name_included_in_result(self, tmp_path):
        executor = _make_executor(tmp_path)
        action = self._make_safe_action("myaction")
        quest = self._make_quest()
        fake_result = MagicMock()
        fake_result.returncode = 0
        fake_result.stdout = ""
        fake_result.stderr = ""
        with patch("src.quest.quest_executor.subprocess.run", return_value=fake_result):
            result = executor.execute_action(action, quest)
        assert result["action"] == "myaction"

    def test_file_path_appended_for_analyze_action(self, tmp_path):
        executor = _make_executor(tmp_path)
        from src.quest.quest_executor import Action
        action = Action(
            name="analyze",
            invocation="python scripts/start_nusyq.py analyze",
            safety_level="safe",
            description="",
            expected_outputs=[],
        )
        from src.quest.quest_executor import Quest
        quest = Quest(timestamp="", task_type="analyze", description="review file src/foo.py", status="active")
        captured = {}

        def fake_run(cmd, **_kw):
            captured["cmd"] = cmd
            m = MagicMock()
            m.returncode = 0
            m.stdout = ""
            m.stderr = ""
            return m
        with patch("src.quest.quest_executor.subprocess.run", side_effect=fake_run):
            executor.execute_action(action, quest)
        assert "src/foo.py" in captured["cmd"]


# ===========================================================================
# QuestExecutor.log_quest_result
# ===========================================================================

class TestLogQuestResult:
    def test_appends_to_quest_log(self, tmp_path):
        _write_quest_log(tmp_path, [
            {"task_type": "analyze", "description": "original", "status": "active"},
        ])
        executor = _make_executor(tmp_path)
        from src.quest.quest_executor import Quest
        quest = Quest(timestamp="ts", task_type="analyze", description="original", status="active")
        executor.log_quest_result(quest, {"status": "completed", "action": "brief"})
        lines = executor.quest_log_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        last = json.loads(lines[-1])
        assert last["status"] == "completed"
        assert last["automated"] is True
        assert "AUTO-EXECUTED" in last["description"]

    def test_log_entry_has_timestamp(self, tmp_path):
        _write_quest_log(tmp_path, [])
        executor = _make_executor(tmp_path)
        from src.quest.quest_executor import Quest
        quest = Quest(timestamp="", task_type="test", description="run tests", status="active")
        executor.log_quest_result(quest, {"status": "completed", "action": "test"})
        lines = executor.quest_log_path.read_text(encoding="utf-8").strip().splitlines()
        entry = json.loads(lines[-1])
        assert "timestamp" in entry


# ===========================================================================
# QuestExecutor.execute_next_safe_quest
# ===========================================================================

class TestExecuteNextSafeQuest:
    def test_returns_no_quests_when_log_empty(self, tmp_path):
        executor = _make_executor(tmp_path)
        result = executor.execute_next_safe_quest()
        assert result is not None
        assert result["status"] == "no_quests"

    def test_returns_no_actions_when_catalog_missing(self, tmp_path):
        _write_quest_log(tmp_path, [
            {"task_type": "brief", "description": "run brief", "status": "active"},
        ])
        executor = _make_executor(tmp_path)
        result = executor.execute_next_safe_quest()
        assert result is not None
        assert result["status"] == "no_actions"

    def test_returns_no_safe_quests_when_all_moderate(self, tmp_path):
        _write_quest_log(tmp_path, [
            {"task_type": "dangerous", "description": "do something risky", "status": "active"},
        ])
        _write_action_catalog(tmp_path, {
            "dangerous": {"safety": "risky", "desc": "risky action", "outputs": []},
        })
        executor = _make_executor(tmp_path)
        result = executor.execute_next_safe_quest()
        assert result is not None
        assert result["status"] == "no_safe_quests"

    def test_executes_first_safe_quest(self, tmp_path):
        _write_quest_log(tmp_path, [
            {"task_type": "brief", "description": "run brief", "status": "active"},
        ])
        _write_action_catalog(tmp_path, {
            "brief": {"safety": "safe", "desc": "Brief check", "outputs": ["status"]},
        })
        executor = _make_executor(tmp_path)
        fake_run = MagicMock()
        fake_run.returncode = 0
        fake_run.stdout = "ok"
        fake_run.stderr = ""
        with patch("src.quest.quest_executor.subprocess.run", return_value=fake_run):
            result = executor.execute_next_safe_quest()
        assert result is not None
        assert result["status"] == "executed"
        assert result["action"] == "brief"

    def test_execute_logs_result_to_file(self, tmp_path):
        _write_quest_log(tmp_path, [
            {"task_type": "brief", "description": "run brief", "status": "active"},
        ])
        _write_action_catalog(tmp_path, {
            "brief": {"safety": "safe", "desc": "Brief check", "outputs": ["status"]},
        })
        executor = _make_executor(tmp_path)
        fake_run = MagicMock()
        fake_run.returncode = 0
        fake_run.stdout = ""
        fake_run.stderr = ""
        with patch("src.quest.quest_executor.subprocess.run", return_value=fake_run):
            executor.execute_next_safe_quest()
        lines = executor.quest_log_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2  # original + appended result


# ===========================================================================
# main() entrypoint
# ===========================================================================

class TestMainEntrypoint:
    def test_main_returns_0_on_no_quests(self, tmp_path):
        from src.quest.quest_executor import QuestExecutor
        with patch("src.quest.quest_executor.Path") as mock_path_cls:
            mock_path_cls.return_value.__truediv__ = lambda s, o: tmp_path / o
            mock_path_cls.return_value.resolve.return_value = tmp_path
            # Directly instantiate and call
            executor = QuestExecutor(tmp_path)
            result = executor.execute_next_safe_quest()
        assert result["status"] == "no_quests"
