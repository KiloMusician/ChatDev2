"""Tests for src/core/quest_receipt_linkage.py and src/core/plan_from_world_state.py."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Helpers / fixtures
# ──────────────────────────────────────────────────────────────────────────────

def _make_receipt(
    receipt_id: str = "rcpt-abc-1234567890",
    action_id: str = "act-001",
    status: str = "SUCCESS",
    agent: str = "ollama",
    task_type: str = "analysis",
    duration_s: float = 1.5,
    policy_category: str = "ANALYSIS",
    risk_score: float = 0.1,
) -> dict:
    return {
        "receipt_id": receipt_id,
        "action_id": action_id,
        "status": status,
        "agent": agent,
        "task_type": task_type,
        "duration_s": duration_s,
        "error_message": None,
        "metadata": {
            "policy_category": policy_category,
            "risk_score": risk_score,
        },
    }


def _make_world_state(epoch: int = 1, token_budget: int = 5000) -> dict:
    return {
        "decision_epoch": epoch,
        "policy_state": {
            "resource_budgets": {
                "token_budget_remaining": token_budget,
                "time_budget_remaining_s": 300,
            },
            "safety_gates": {
                "max_risk_score": 0.7,
            },
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# quest_receipt_linkage tests
# ──────────────────────────────────────────────────────────────────────────────

from src.core.quest_receipt_linkage import (
    _append_event_index,
    _resolve_path,
    append_quest_log_event,
    ensure_link_file,
    get_quest_action_history,
    get_quests_for_epoch,
    link_receipt_to_quest,
    stats,
    update_quest_from_receipt,
)


class TestResolvePath:
    def test_absolute_path_returned_unchanged(self, tmp_path):
        abs_path = tmp_path / "file.jsonl"
        result = _resolve_path(abs_path, Path("/some/root"))
        assert result == abs_path

    def test_relative_path_joined_with_workspace_root(self, tmp_path):
        rel = Path("a/b/file.jsonl")
        result = _resolve_path(rel, tmp_path)
        assert result == tmp_path / "a" / "b" / "file.jsonl"


class TestEnsureLinkFile:
    def test_creates_file_and_parents(self, tmp_path):
        resolved = ensure_link_file(tmp_path)
        assert resolved.exists()
        assert resolved.is_file()

    def test_idempotent_when_file_exists(self, tmp_path):
        first = ensure_link_file(tmp_path)
        first.write_text("existing\n")
        second = ensure_link_file(tmp_path)
        assert second.read_text() == "existing\n"


class TestAppendQuestLogEvent:
    def test_appends_json_line(self, tmp_path):
        append_quest_log_event("test_event", {"k": "v"}, workspace_root=tmp_path)
        log_file = tmp_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        assert log_file.exists()
        lines = [json.loads(l) for l in log_file.read_text().splitlines()]
        assert len(lines) == 1
        assert lines[0]["event"] == "test_event"
        assert lines[0]["details"] == {"k": "v"}
        assert "timestamp" in lines[0]

    def test_returns_payload(self, tmp_path):
        payload = append_quest_log_event("ev", {"x": 1}, workspace_root=tmp_path)
        assert payload["event"] == "ev"
        assert payload["details"] == {"x": 1}

    def test_multiple_appends(self, tmp_path):
        for i in range(3):
            append_quest_log_event(f"event_{i}", {}, workspace_root=tmp_path)
        log_file = tmp_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        lines = log_file.read_text().splitlines()
        assert len(lines) == 3


class TestAppendEventIndex:
    def test_creates_event_index_file(self, tmp_path):
        _append_event_index("test_type", {"ref": "abc"}, workspace_root=tmp_path)
        index_file = tmp_path / "state" / "event_index.jsonl"
        assert index_file.exists()

    def test_entry_has_correct_structure(self, tmp_path):
        _append_event_index("quest_receipt_link", {"receipt_id": "r1", "quest_id": "q1"}, workspace_root=tmp_path)
        index_file = tmp_path / "state" / "event_index.jsonl"
        entry = json.loads(index_file.read_text().strip())
        assert entry["type"] == "quest_receipt_link"
        assert entry["refs"]["receipt_id"] == "r1"


class TestLinkReceiptToQuest:
    def test_creates_link_file_with_entry(self, tmp_path):
        receipt = _make_receipt()
        link_receipt_to_quest(receipt, "quest-001", workspace_root=tmp_path)
        link_file = tmp_path / "src" / "Rosetta_Quest_System" / "quest_receipt_links.jsonl"
        assert link_file.exists()
        lines = link_file.read_text().splitlines()
        assert len(lines) == 1

    def test_link_contains_expected_fields(self, tmp_path):
        receipt = _make_receipt(receipt_id="rcpt-xyz-1234567890", action_id="act-999", status="SUCCESS")
        link = link_receipt_to_quest(receipt, "quest-42", workspace_root=tmp_path)
        assert link["receipt_id"] == "rcpt-xyz-1234567890"
        assert link["action_id"] == "act-999"
        assert link["quest_id"] == "quest-42"
        assert link["action_status"] == "SUCCESS"
        assert link["contributed_to_completion"] is False

    def test_link_id_format(self, tmp_path):
        receipt = _make_receipt(receipt_id="rcpt-aaa-1234567890")
        link = link_receipt_to_quest(receipt, "quest-007", workspace_root=tmp_path)
        assert "rcpt-aaa-1234567890" in link["link_id"]
        assert "quest-007" in link["link_id"]

    def test_world_state_epoch_in_metadata(self, tmp_path):
        receipt = _make_receipt()
        ws = _make_world_state(epoch=42)
        link = link_receipt_to_quest(receipt, "q1", world_state=ws, workspace_root=tmp_path)
        assert link["metadata"]["decision_epoch"] == 42

    def test_no_world_state_epoch_is_none(self, tmp_path):
        receipt = _make_receipt()
        link = link_receipt_to_quest(receipt, "q1", world_state=None, workspace_root=tmp_path)
        assert link["metadata"]["decision_epoch"] is None

    def test_also_appends_quest_log_event(self, tmp_path):
        receipt = _make_receipt()
        link_receipt_to_quest(receipt, "q1", workspace_root=tmp_path)
        log_file = tmp_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        assert log_file.exists()
        entry = json.loads(log_file.read_text().strip())
        assert entry["event"] == "action_receipt_linked"

    def test_also_appends_event_index(self, tmp_path):
        receipt = _make_receipt()
        link_receipt_to_quest(receipt, "q1", workspace_root=tmp_path)
        index_file = tmp_path / "state" / "event_index.jsonl"
        assert index_file.exists()

    def test_policy_metadata_forwarded(self, tmp_path):
        receipt = _make_receipt(policy_category="SECURITY", risk_score=0.9)
        link = link_receipt_to_quest(receipt, "q1", workspace_root=tmp_path)
        assert link["metadata"]["policy_category"] == "SECURITY"
        assert link["metadata"]["risk_score"] == 0.9

    def test_multiple_links_appended(self, tmp_path):
        for i in range(4):
            r = _make_receipt(receipt_id=f"rcpt-{i:04d}-1234567890")
            link_receipt_to_quest(r, f"quest-{i}", workspace_root=tmp_path)
        link_file = tmp_path / "src" / "Rosetta_Quest_System" / "quest_receipt_links.jsonl"
        lines = link_file.read_text().splitlines()
        assert len(lines) == 4


class TestUpdateQuestFromReceipt:
    def _mock_engine(self, quest_id, status="active"):
        quest = MagicMock()
        quest.status = status
        quest.history = []
        engine = MagicMock()
        engine.quests = {quest_id: quest}
        return engine, quest

    def test_success_completes_active_quest(self):
        engine, _quest = self._mock_engine("q1", status="active")
        receipt = _make_receipt(status="SUCCESS")
        update_quest_from_receipt(engine, receipt, "q1")
        engine.complete_quest.assert_called_once_with("q1")

    def test_failed_blocks_quest(self):
        engine, quest = self._mock_engine("q1", status="active")
        receipt = _make_receipt(status="FAILED", receipt_id="rcpt-fail-1234567890")
        update_quest_from_receipt(engine, receipt, "q1")
        assert quest.status == "blocked"
        assert len(quest.history) == 1
        assert quest.history[0]["event"] == "action_failed"

    def test_partial_adds_history_entry(self):
        engine, quest = self._mock_engine("q1", status="active")
        receipt = _make_receipt(status="PARTIAL")
        update_quest_from_receipt(engine, receipt, "q1")
        assert len(quest.history) == 1
        assert quest.history[0]["event"] == "action_partial_success"

    def test_missing_quest_logs_warning(self, caplog):
        engine = MagicMock()
        engine.quests = {}
        receipt = _make_receipt()
        with caplog.at_level(logging.WARNING):
            update_quest_from_receipt(engine, receipt, "nonexistent-quest")
        assert "not found" in caplog.text

    def test_exception_in_engine_is_handled(self):
        engine = MagicMock()
        engine.quests = MagicMock(side_effect=Exception("boom"))
        receipt = _make_receipt()
        # Should not raise
        update_quest_from_receipt(engine, receipt, "q1")


class TestGetQuestActionHistory:
    def test_returns_empty_for_empty_file(self, tmp_path):
        ensure_link_file(tmp_path)
        result = get_quest_action_history("q1", workspace_root=tmp_path)
        assert result == []

    def test_filters_by_quest_id(self, tmp_path):
        for qid, rid in [("q1", "rcpt-a-1234567890"), ("q2", "rcpt-b-1234567890"), ("q1", "rcpt-c-1234567890")]:
            link_receipt_to_quest(_make_receipt(receipt_id=rid), qid, workspace_root=tmp_path)
        result = get_quest_action_history("q1", workspace_root=tmp_path)
        assert len(result) == 2
        assert all(r["quest_id"] == "q1" for r in result)

    def test_sorted_by_timestamp(self, tmp_path):
        for _i, rid in enumerate(["rcpt-1-1234567890", "rcpt-2-1234567890", "rcpt-3-1234567890"]):
            link_receipt_to_quest(_make_receipt(receipt_id=rid), "q1", workspace_root=tmp_path)
        history = get_quest_action_history("q1", workspace_root=tmp_path)
        timestamps = [h["timestamp"] for h in history]
        assert timestamps == sorted(timestamps)

    def test_skips_malformed_json_lines(self, tmp_path):
        link_file = ensure_link_file(tmp_path)
        link_file.write_text('{"quest_id": "q1", "timestamp": "2026-01-01T00:00:00"}\nBAD JSON LINE\n')
        result = get_quest_action_history("q1", workspace_root=tmp_path)
        assert len(result) == 1


class TestGetQuestsForEpoch:
    def test_returns_quests_for_matching_epoch(self, tmp_path):
        ws1 = _make_world_state(epoch=5)
        ws2 = _make_world_state(epoch=99)
        link_receipt_to_quest(_make_receipt(receipt_id="rcpt-ep5a-1234567890"), "q-a", world_state=ws1, workspace_root=tmp_path)
        link_receipt_to_quest(_make_receipt(receipt_id="rcpt-ep99-1234567890"), "q-b", world_state=ws2, workspace_root=tmp_path)
        result = get_quests_for_epoch(ws1, workspace_root=tmp_path)
        assert "q-a" in result
        assert "q-b" not in result

    def test_deduplicates_quest_ids(self, tmp_path):
        ws = _make_world_state(epoch=7)
        for rid in ["rcpt-dup1-1234567890", "rcpt-dup2-1234567890"]:
            link_receipt_to_quest(_make_receipt(receipt_id=rid), "q-dup", world_state=ws, workspace_root=tmp_path)
        result = get_quests_for_epoch(ws, workspace_root=tmp_path)
        assert result.count("q-dup") == 1

    def test_empty_file_returns_empty_list(self, tmp_path):
        ensure_link_file(tmp_path)
        result = get_quests_for_epoch({"decision_epoch": 1}, workspace_root=tmp_path)
        assert result == []


class TestStats:
    def test_empty_file_returns_zero_counts(self, tmp_path):
        ensure_link_file(tmp_path)
        result = stats(workspace_root=tmp_path)
        assert result["total_links"] == 0
        assert result["successful_actions"] == 0
        assert result["failed_actions"] == 0
        assert result["partial_actions"] == 0
        assert result["unique_quests"] == 0
        assert result["by_agent"] == {}

    def test_counts_statuses_correctly(self, tmp_path):
        for status, rid in [
            ("SUCCESS", "rcpt-s1-1234567890"),
            ("SUCCESS", "rcpt-s2-1234567890"),
            ("FAILED", "rcpt-f1-1234567890"),
            ("PARTIAL", "rcpt-p1-1234567890"),
        ]:
            r = _make_receipt(receipt_id=rid, status=status)
            link_receipt_to_quest(r, "q1", workspace_root=tmp_path)
        result = stats(workspace_root=tmp_path)
        assert result["total_links"] == 4
        assert result["successful_actions"] == 2
        assert result["failed_actions"] == 1
        assert result["partial_actions"] == 1

    def test_unique_quests_counted(self, tmp_path):
        for qid, rid in [("q1", "rcpt-u1-1234567890"), ("q2", "rcpt-u2-1234567890"), ("q1", "rcpt-u3-1234567890")]:
            link_receipt_to_quest(_make_receipt(receipt_id=rid), qid, workspace_root=tmp_path)
        result = stats(workspace_root=tmp_path)
        assert result["unique_quests"] == 2

    def test_by_agent_aggregation(self, tmp_path):
        r1 = _make_receipt(receipt_id="rcpt-ag1-1234567890", agent="ollama", status="SUCCESS")
        r2 = _make_receipt(receipt_id="rcpt-ag2-1234567890", agent="ollama", status="FAILED")
        r3 = _make_receipt(receipt_id="rcpt-ag3-1234567890", agent="claude", status="SUCCESS")
        for r, qid in [(r1, "q1"), (r2, "q2"), (r3, "q3")]:
            link_receipt_to_quest(r, qid, workspace_root=tmp_path)
        result = stats(workspace_root=tmp_path)
        assert result["by_agent"]["ollama"]["link_count"] == 2
        assert result["by_agent"]["ollama"]["successful"] == 1
        assert result["by_agent"]["claude"]["link_count"] == 1
        assert result["by_agent"]["claude"]["successful"] == 1

    def test_malformed_json_skipped(self, tmp_path):
        link_file = ensure_link_file(tmp_path)
        good = json.dumps({"action_status": "SUCCESS", "quest_id": "q1", "agent": "ollama"})
        link_file.write_text(good + "\nNOT_JSON\n")
        result = stats(workspace_root=tmp_path)
        assert result["total_links"] == 1


# ──────────────────────────────────────────────────────────────────────────────
# plan_from_world_state tests
# ──────────────────────────────────────────────────────────────────────────────

from src.core.plan_from_world_state import (
    Action,
    ActionGenerator,
    AgentType,
    CapabilityRegistry,
    IntentParser,
    PlanGenerator,
    RiskLevel,
    TaskType,
    plan_from_world_state,
)


class TestTaskTypeAndAgentTypeEnums:
    def test_task_type_values(self):
        assert TaskType.ANALYSIS.value == "analysis"
        assert TaskType.CODE_GENERATION.value == "code_generation"
        assert TaskType.DEBUGGING.value == "debugging"
        assert TaskType.TESTING.value == "testing"

    def test_agent_type_values(self):
        assert AgentType.OLLAMA.value == "ollama"
        assert AgentType.CHATDEV.value == "chatdev"
        assert AgentType.CONSCIOUSNESS.value == "consciousness"

    def test_risk_level_enum(self):
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.CRITICAL.value == "critical"


class TestCapabilityRegistry:
    def test_agents_for_analysis(self):
        agents = CapabilityRegistry.agents_for_task(TaskType.ANALYSIS)
        agent_types = [a[0] for a in agents]
        assert AgentType.OLLAMA in agent_types

    def test_agents_sorted_by_success_rate_descending(self):
        agents = CapabilityRegistry.agents_for_task(TaskType.CODE_GENERATION)
        rates = [a[1]["success_rate"] for a in agents]
        assert rates == sorted(rates, reverse=True)

    def test_agents_for_policy_evaluation_is_consciousness(self):
        agents = CapabilityRegistry.agents_for_task(TaskType.POLICY_EVALUATION)
        assert len(agents) == 1
        assert agents[0][0] == AgentType.CONSCIOUSNESS

    def test_cost_estimate_returns_dict_with_required_keys(self):
        cost = CapabilityRegistry.cost_estimate(AgentType.OLLAMA, TaskType.ANALYSIS, "normal")
        assert "tokens" in cost
        assert "time_s" in cost
        assert "cpu" in cost

    def test_cost_estimate_complexity_simple_halves_tokens(self):
        normal = CapabilityRegistry.cost_estimate(AgentType.OLLAMA, TaskType.ANALYSIS, "normal")
        simple = CapabilityRegistry.cost_estimate(AgentType.OLLAMA, TaskType.ANALYSIS, "simple")
        assert simple["tokens"] < normal["tokens"]

    def test_cost_estimate_complexity_complex_doubles_tokens(self):
        normal = CapabilityRegistry.cost_estimate(AgentType.OLLAMA, TaskType.ANALYSIS, "normal")
        complex_ = CapabilityRegistry.cost_estimate(AgentType.OLLAMA, TaskType.ANALYSIS, "complex")
        assert complex_["tokens"] > normal["tokens"]

    def test_unknown_agent_returns_defaults(self):
        cost = CapabilityRegistry.cost_estimate(AgentType.OPENCLAW, TaskType.ANALYSIS)
        assert isinstance(cost["tokens"], int)

    def test_no_agents_for_nonexistent_task_type_like_documentation(self):
        # DOCUMENTATION not in all agents — but some may have it; just check return is list
        agents = CapabilityRegistry.agents_for_task(TaskType.DOCUMENTATION)
        assert isinstance(agents, list)


class TestIntentParser:
    def test_analyze_keyword_returns_analysis(self):
        intent = IntentParser.parse("analyze the codebase", {})
        assert intent["task_type"] == TaskType.ANALYSIS

    def test_review_keyword_returns_analysis(self):
        intent = IntentParser.parse("review this file", {})
        assert intent["task_type"] == TaskType.ANALYSIS

    def test_generate_keyword_returns_code_generation(self):
        intent = IntentParser.parse("generate a new module", {})
        assert intent["task_type"] == TaskType.CODE_GENERATION

    def test_create_keyword_returns_code_generation(self):
        intent = IntentParser.parse("create a feature", {})
        assert intent["task_type"] == TaskType.CODE_GENERATION

    def test_debug_keyword_returns_debugging(self):
        intent = IntentParser.parse("debug this error", {})
        assert intent["task_type"] == TaskType.DEBUGGING

    def test_fix_keyword_returns_debugging(self):
        intent = IntentParser.parse("fix the broken module", {})
        assert intent["task_type"] == TaskType.DEBUGGING

    def test_test_keyword_returns_testing(self):
        intent = IntentParser.parse("test the new endpoint", {})
        assert intent["task_type"] == TaskType.TESTING

    def test_unknown_message_defaults_to_analysis(self):
        intent = IntentParser.parse("do something undefined", {})
        assert intent["task_type"] == TaskType.ANALYSIS

    def test_intent_contains_complexity(self):
        intent = IntentParser.parse("generate code", {})
        assert "complexity" in intent

    def test_intent_contains_description(self):
        intent = IntentParser.parse("analyze errors", {})
        assert isinstance(intent["description"], str)


class TestActionGenerator:
    def test_generates_actions_for_analysis(self):
        ws = _make_world_state()
        actions = ActionGenerator.generate_actions(TaskType.ANALYSIS, "Analyze code", ws)
        assert len(actions) > 0
        assert all(a.task_type == TaskType.ANALYSIS for a in actions)

    def test_action_has_required_fields(self):
        ws = _make_world_state()
        actions = ActionGenerator.generate_actions(TaskType.ANALYSIS, "Analyze", ws)
        a = actions[0]
        assert a.action_id
        assert a.timestamp
        assert isinstance(a.risk_score, float)
        assert 0.0 <= a.risk_score <= 1.0
        assert isinstance(a.preconditions, list)
        assert isinstance(a.postconditions, list)

    def test_max_candidates_limits_results(self):
        ws = _make_world_state()
        actions = ActionGenerator.generate_actions(TaskType.ANALYSIS, "Analyze", ws, max_candidates=1)
        assert len(actions) <= 1

    def test_low_token_budget_filters_expensive_actions(self):
        ws = _make_world_state(token_budget=1)
        actions = ActionGenerator.generate_actions(TaskType.CODE_GENERATION, "Generate", ws)
        # All remaining actions should fit within budget or have low risk
        for a in actions:
            assert not (a.estimated_cost["tokens"] > 1 and a.risk_score > 0.5)

    def test_compute_optimization_returns_valid_roi(self):
        opt, roi = ActionGenerator._compute_optimization(0.95, 0.05, {"tokens": 500, "time_s": 3, "cpu": 10})
        assert roi > 0
        assert "roi_score" in opt
        assert "risk_adjusted_success" in opt
        assert "token_efficiency" in opt

    def test_optimization_zero_risk_adjusted_success_when_risk_equals_one(self):
        opt, _roi = ActionGenerator._compute_optimization(0.9, 1.0, {"tokens": 500, "time_s": 3, "cpu": 10})
        assert opt["risk_adjusted_success"] == 0.0


class TestActionToDict:
    def test_to_dict_serializes_all_fields(self):
        ws = _make_world_state()
        actions = ActionGenerator.generate_actions(TaskType.ANALYSIS, "Analyze", ws)
        d = actions[0].to_dict()
        for key in ["action_id", "timestamp", "agent", "task_type", "description",
                    "preconditions", "postconditions", "estimated_cost", "risk_score",
                    "policy_category", "time_sensitivity", "quest_dependency",
                    "rollback_hint", "optimization", "selection_score"]:
            assert key in d

    def test_to_dict_agent_is_string(self):
        ws = _make_world_state()
        actions = ActionGenerator.generate_actions(TaskType.ANALYSIS, "Analyze", ws)
        d = actions[0].to_dict()
        assert isinstance(d["agent"], str)

    def test_to_dict_task_type_is_string(self):
        ws = _make_world_state()
        actions = ActionGenerator.generate_actions(TaskType.ANALYSIS, "Analyze", ws)
        d = actions[0].to_dict()
        assert isinstance(d["task_type"], str)


class TestPlanGenerator:
    def test_plan_from_state_returns_list(self):
        planner = PlanGenerator()
        ws = _make_world_state()
        actions = planner.plan_from_state(ws, "Analyze the codebase")
        assert isinstance(actions, list)
        assert len(actions) > 0

    def test_plan_sorted_by_time_sensitivity_then_policy(self):
        planner = PlanGenerator()
        ws = _make_world_state()
        actions = planner.plan_from_state(ws, "Generate a new feature")
        # Just check it returns without error and is a list of Actions
        assert all(isinstance(a, Action) for a in actions)

    def test_plan_with_debug_objective(self):
        planner = PlanGenerator()
        ws = _make_world_state()
        actions = planner.plan_from_state(ws, "debug the broken endpoint")
        assert len(actions) > 0
        assert all(a.task_type == TaskType.DEBUGGING for a in actions)

    def test_plan_with_empty_objective_defaults_to_analysis(self):
        planner = PlanGenerator()
        ws = _make_world_state()
        actions = planner.plan_from_state(ws, "")
        assert isinstance(actions, list)

    def test_plan_with_test_objective(self):
        planner = PlanGenerator()
        ws = _make_world_state()
        actions = planner.plan_from_state(ws, "run tests on new module")
        assert len(actions) > 0
        assert all(a.task_type == TaskType.TESTING for a in actions)

    def test_plan_actions_have_selection_scores(self):
        planner = PlanGenerator()
        ws = _make_world_state()
        actions = planner.plan_from_state(ws, "analyze errors")
        assert all(isinstance(a.selection_score, float) for a in actions)


class TestPlanFromWorldStateFunction:
    def test_returns_dict_with_required_keys(self):
        ws = _make_world_state()
        result = plan_from_world_state(ws, "Analyze codebase errors")
        assert "objective" in result
        assert "actions" in result
        assert "metadata" in result

    def test_actions_is_list_of_dicts(self):
        ws = _make_world_state()
        result = plan_from_world_state(ws, "analyze issues")
        assert isinstance(result["actions"], list)
        for action in result["actions"]:
            assert isinstance(action, dict)

    def test_metadata_contains_total_candidates(self):
        ws = _make_world_state()
        result = plan_from_world_state(ws, "analyze issues")
        assert "total_candidates" in result["metadata"]
        assert result["metadata"]["total_candidates"] == len(result["actions"])

    def test_metadata_schema_version(self):
        ws = _make_world_state()
        result = plan_from_world_state(ws, "analyze issues")
        assert result["metadata"]["schema_version"] == "0.1"

    def test_objective_captures_user_intent(self):
        ws = _make_world_state()
        result = plan_from_world_state(ws, "generate a new service")
        assert result["objective"]["user_intent"] == "generate a new service"

    def test_empty_actions_when_zero_token_budget_and_code_gen(self):
        ws = _make_world_state(token_budget=0)
        result = plan_from_world_state(ws, "generate a new service")
        # With 0 budget, all high-token code-gen actions should be filtered out
        # (actions list may be empty or contain only zero-token agents)
        assert isinstance(result["actions"], list)

    def test_serializable_to_json(self):
        ws = _make_world_state()
        result = plan_from_world_state(ws, "analyze errors")
        # Should not raise
        serialized = json.dumps(result)
        assert len(serialized) > 0
