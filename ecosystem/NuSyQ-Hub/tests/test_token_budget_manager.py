"""Tests for src/budgeting/token_budget_manager.py.

All imports are inside test functions or fixtures to avoid module-level side effects.
External I/O (BUDGETS_FILE, USAGE_HISTORY_FILE) is patched via unittest.mock.patch or
redirected to tmp_path so no real state files are touched.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tracker_no_io(tmp_path: Path):
    """Return a TokenTracker whose history file lives in tmp_path."""
    import src.budgeting.token_budget_manager as mod

    history_file = tmp_path / "usage_history.jsonl"
    with (
        patch.object(mod, "USAGE_HISTORY_FILE", history_file),
        patch.object(mod, "BUDGETS_FILE", tmp_path / "token_budgets.json"),
    ):
        from src.budgeting.token_budget_manager import TokenTracker

        tracker = TokenTracker.__new__(TokenTracker)
        # Manually initialise without touching real filesystem
        from collections import defaultdict

        tracker.usage_history = []
        tracker.agent_totals = defaultdict(int)
        tracker.task_totals = defaultdict(int)
        tracker.daily_totals = defaultdict(int)

    return tracker


def _make_manager_no_io(tmp_path: Path):
    """Return a TokenBudgetManager that writes to tmp_path."""
    import src.budgeting.token_budget_manager as mod

    history_file = tmp_path / "usage_history.jsonl"
    budgets_file = tmp_path / "budgets.json"

    with (
        patch.object(mod, "USAGE_HISTORY_FILE", history_file),
        patch.object(mod, "BUDGETS_FILE", budgets_file),
    ):
        from src.budgeting.token_budget_manager import TokenBudgetManager

        mgr = TokenBudgetManager.__new__(TokenBudgetManager)
        from collections import defaultdict
        from src.budgeting.token_budget_manager import TokenBudget, TokenTracker

        mgr.budget = TokenBudget()
        mgr.tracker = TokenTracker.__new__(TokenTracker)
        mgr.tracker.usage_history = []
        mgr.tracker.agent_totals = defaultdict(int)
        mgr.tracker.task_totals = defaultdict(int)
        mgr.tracker.daily_totals = defaultdict(int)
        mgr.current_day = datetime.now().strftime("%Y-%m-%d")
        mgr.period_used = 0
        mgr._history_file = history_file
        mgr._budgets_file = budgets_file

    return mgr


# ---------------------------------------------------------------------------
# TokenBudget dataclass
# ---------------------------------------------------------------------------


class TestTokenBudgetDataclass:
    def test_default_construction(self):
        from src.budgeting.token_budget_manager import TokenBudget

        b = TokenBudget()
        assert b.global_limit == 1_000_000
        assert b.per_agent_limit == {}
        assert b.per_task_limit == {}
        assert b.escalation_threshold == 0.8
        assert b.critical_threshold == 0.95

    def test_custom_global_limit(self):
        from src.budgeting.token_budget_manager import TokenBudget

        b = TokenBudget(global_limit=500_000)
        assert b.global_limit == 500_000

    def test_set_agent_limit(self):
        from src.budgeting.token_budget_manager import TokenBudget

        b = TokenBudget()
        b.set_agent_limit("claude", 200_000)
        assert b.per_agent_limit["claude"] == 200_000

    def test_set_task_limit(self):
        from src.budgeting.token_budget_manager import TokenBudget

        b = TokenBudget()
        b.set_task_limit("code_review", 5_000)
        assert b.per_task_limit["code_review"] == 5_000

    def test_to_dict_keys(self):
        from src.budgeting.token_budget_manager import TokenBudget

        b = TokenBudget()
        d = b.to_dict()
        assert "global_limit" in d
        assert "per_agent_limit" in d
        assert "per_task_limit" in d
        assert "escalation_threshold" in d
        assert "critical_threshold" in d
        assert "timestamp" in d

    def test_to_dict_values_match(self):
        from src.budgeting.token_budget_manager import TokenBudget

        b = TokenBudget(global_limit=42_000, escalation_threshold=0.7)
        d = b.to_dict()
        assert d["global_limit"] == 42_000
        assert d["escalation_threshold"] == 0.7

    def test_independent_dicts_per_instance(self):
        from src.budgeting.token_budget_manager import TokenBudget

        b1 = TokenBudget()
        b2 = TokenBudget()
        b1.set_agent_limit("x", 1)
        assert "x" not in b2.per_agent_limit


# ---------------------------------------------------------------------------
# TokenUsage dataclass
# ---------------------------------------------------------------------------


class TestTokenUsageDataclass:
    def test_construction_with_defaults(self):
        from src.budgeting.token_budget_manager import TokenUsage

        u = TokenUsage(
            timestamp="2026-03-15T12:00:00",
            agent="ollama",
            task_type="review",
            tokens_used=500,
        )
        assert u.cost_usd == 0.0
        assert u.success is True

    def test_to_dict_roundtrip(self):
        from src.budgeting.token_budget_manager import TokenUsage

        u = TokenUsage(
            timestamp="2026-03-15T12:00:00",
            agent="claude",
            task_type="generate",
            tokens_used=1234,
            cost_usd=0.05,
            success=False,
        )
        d = u.to_dict()
        assert d["agent"] == "claude"
        assert d["tokens_used"] == 1234
        assert d["cost_usd"] == 0.05
        assert d["success"] is False
        assert d["timestamp"] == "2026-03-15T12:00:00"


# ---------------------------------------------------------------------------
# TokenTracker — pure logic (no real file I/O)
# ---------------------------------------------------------------------------


class TestTokenTrackerPure:
    def test_get_average_tokens_empty(self, tmp_path):
        tracker = _make_tracker_no_io(tmp_path)
        assert tracker.get_average_tokens() == 0.0

    def test_get_average_tokens_single(self, tmp_path):
        from src.budgeting.token_budget_manager import TokenUsage

        tracker = _make_tracker_no_io(tmp_path)
        u = TokenUsage(
            timestamp=datetime.now().isoformat(),
            agent="ollama",
            task_type="review",
            tokens_used=300,
        )
        tracker.usage_history.append(u)
        tracker._update_totals(u)

        assert tracker.get_average_tokens(agent="ollama") == 300.0

    def test_get_average_tokens_multiple(self, tmp_path):
        from src.budgeting.token_budget_manager import TokenUsage

        tracker = _make_tracker_no_io(tmp_path)
        now = datetime.now().isoformat()
        for tokens in [100, 200, 300]:
            u = TokenUsage(
                timestamp=now, agent="a", task_type="t", tokens_used=tokens
            )
            tracker.usage_history.append(u)
            tracker._update_totals(u)

        assert tracker.get_average_tokens(agent="a") == 200.0

    def test_get_average_tokens_filters_by_task(self, tmp_path):
        from src.budgeting.token_budget_manager import TokenUsage

        tracker = _make_tracker_no_io(tmp_path)
        now = datetime.now().isoformat()
        u1 = TokenUsage(timestamp=now, agent="a", task_type="review", tokens_used=100)
        u2 = TokenUsage(timestamp=now, agent="a", task_type="generate", tokens_used=900)
        for u in [u1, u2]:
            tracker.usage_history.append(u)
            tracker._update_totals(u)

        assert tracker.get_average_tokens(agent="a", task_type="review") == 100.0

    def test_predict_total_for_task(self, tmp_path):
        from src.budgeting.token_budget_manager import TokenUsage

        tracker = _make_tracker_no_io(tmp_path)
        now = datetime.now().isoformat()
        for tokens in [200, 400]:
            u = TokenUsage(timestamp=now, agent="b", task_type="gen", tokens_used=tokens)
            tracker.usage_history.append(u)
            tracker._update_totals(u)

        # avg = 300, num_calls = 5 → 1500
        result = tracker.predict_total_for_task("b", "gen", 5)
        assert result == 1500

    def test_predict_total_for_task_no_history(self, tmp_path):
        tracker = _make_tracker_no_io(tmp_path)
        assert tracker.predict_total_for_task("unknown", "unknown", 10) == 0

    def test_get_usage_trend_only_recent(self, tmp_path):
        from src.budgeting.token_budget_manager import TokenUsage

        tracker = _make_tracker_no_io(tmp_path)
        recent = datetime.now().isoformat()
        old = (datetime.now() - timedelta(hours=48)).isoformat()

        u_old = TokenUsage(timestamp=old, agent="x", task_type="t", tokens_used=999)
        u_new = TokenUsage(timestamp=recent, agent="x", task_type="t", tokens_used=50)
        for u in [u_old, u_new]:
            tracker.usage_history.append(u)
            tracker._update_totals(u)

        trend = tracker.get_usage_trend("x", hours=24)
        assert 50 in trend
        assert 999 not in trend

    def test_get_daily_usage_today(self, tmp_path):
        from src.budgeting.token_budget_manager import TokenUsage

        tracker = _make_tracker_no_io(tmp_path)
        today = datetime.now().strftime("%Y-%m-%d")
        u = TokenUsage(
            timestamp=f"{today}T10:00:00",
            agent="a",
            task_type="t",
            tokens_used=123,
        )
        tracker.usage_history.append(u)
        tracker._update_totals(u)

        assert tracker.get_daily_usage(today) == 123

    def test_get_daily_usage_missing_date(self, tmp_path):
        tracker = _make_tracker_no_io(tmp_path)
        assert tracker.get_daily_usage("1999-01-01") == 0

    def test_efficiency_score_no_history(self, tmp_path):
        tracker = _make_tracker_no_io(tmp_path)
        assert tracker.get_efficiency_score("nobody", "nothing") == 0.0

    def test_efficiency_score_with_successful_tasks(self, tmp_path):
        from src.budgeting.token_budget_manager import TokenUsage

        tracker = _make_tracker_no_io(tmp_path)
        now = datetime.now().isoformat()
        for tokens in [100, 200]:
            u = TokenUsage(
                timestamp=now,
                agent="ag",
                task_type="t",
                tokens_used=tokens,
                success=True,
            )
            tracker.usage_history.append(u)
            tracker._update_totals(u)

        score = tracker.get_efficiency_score("ag", "t")
        # avg = 150, success_rate = 1.0 → score = 150
        assert score == 150.0

    def test_recommend_efficient_agent_no_history(self, tmp_path):
        tracker = _make_tracker_no_io(tmp_path)
        assert tracker.recommend_efficient_agent("unknown_task") is None

    def test_recommend_efficient_agent_picks_better(self, tmp_path):
        from src.budgeting.token_budget_manager import TokenUsage

        tracker = _make_tracker_no_io(tmp_path)
        now = datetime.now().isoformat()
        cheap = TokenUsage(timestamp=now, agent="cheap", task_type="t", tokens_used=100, success=True)
        expensive = TokenUsage(timestamp=now, agent="expensive", task_type="t", tokens_used=5000, success=True)
        for u in [cheap, expensive]:
            tracker.usage_history.append(u)
            tracker._update_totals(u)

        best = tracker.recommend_efficient_agent("t")
        assert best == "cheap"


# ---------------------------------------------------------------------------
# TokenTracker — load_history with patched file
# ---------------------------------------------------------------------------


class TestTokenTrackerLoadHistory:
    def test_load_history_from_file(self, tmp_path):
        import src.budgeting.token_budget_manager as mod

        history_file = tmp_path / "usage_history.jsonl"
        record = {
            "timestamp": "2026-03-15T10:00:00",
            "agent": "ollama",
            "task_type": "review",
            "tokens_used": 400,
            "cost_usd": 0.01,
            "success": True,
        }
        history_file.write_text(json.dumps(record) + "\n")

        with patch.object(mod, "USAGE_HISTORY_FILE", history_file):
            from src.budgeting.token_budget_manager import TokenTracker

            tracker = TokenTracker()

        assert len(tracker.usage_history) == 1
        assert tracker.usage_history[0].agent == "ollama"
        assert tracker.agent_totals["ollama"] == 400

    def test_load_history_missing_file(self, tmp_path):
        import src.budgeting.token_budget_manager as mod

        missing = tmp_path / "no_such_file.jsonl"
        with patch.object(mod, "USAGE_HISTORY_FILE", missing):
            from src.budgeting.token_budget_manager import TokenTracker

            tracker = TokenTracker()

        assert tracker.usage_history == []


# ---------------------------------------------------------------------------
# TokenTracker — record_usage with patched I/O
# ---------------------------------------------------------------------------


class TestTokenTrackerRecordUsage:
    def test_record_usage_appends_to_history(self, tmp_path):
        import src.budgeting.token_budget_manager as mod

        history_file = tmp_path / "usage_history.jsonl"
        with patch.object(mod, "USAGE_HISTORY_FILE", history_file):
            from src.budgeting.token_budget_manager import TokenTracker

            tracker = TokenTracker()
            tracker.record_usage("claude", "generate", 750)

        assert len(tracker.usage_history) == 1
        assert tracker.agent_totals["claude"] == 750
        assert tracker.task_totals["generate"] == 750

    def test_record_usage_writes_to_file(self, tmp_path):
        import src.budgeting.token_budget_manager as mod

        history_file = tmp_path / "usage_history.jsonl"
        with patch.object(mod, "USAGE_HISTORY_FILE", history_file):
            from src.budgeting.token_budget_manager import TokenTracker

            tracker = TokenTracker()
            tracker.record_usage("ollama", "review", 300, cost_usd=0.01)

        lines = history_file.read_text().strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["agent"] == "ollama"
        assert parsed["tokens_used"] == 300


# ---------------------------------------------------------------------------
# TokenBudgetManager — logic tests
# ---------------------------------------------------------------------------


class TestTokenBudgetManagerLogic:
    def test_can_afford_within_global_limit(self, tmp_path):
        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 1_000_000
        mgr.period_used = 0
        assert mgr.can_afford_agent("claude", "review", 500) is True

    def test_cannot_afford_exceeds_global_limit(self, tmp_path):
        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 1_000
        mgr.period_used = 900
        assert mgr.can_afford_agent("claude", "review", 200) is False

    def test_cannot_afford_exceeds_agent_limit(self, tmp_path):
        from src.budgeting.token_budget_manager import TokenUsage

        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 1_000_000
        mgr.budget.per_agent_limit["ollama"] = 500
        mgr.period_used = 0

        today = mgr.current_day
        u = TokenUsage(
            timestamp=f"{today}T09:00:00",
            agent="ollama",
            task_type="t",
            tokens_used=400,
        )
        mgr.tracker.usage_history.append(u)

        assert mgr.can_afford_agent("ollama", "t", 200) is False

    def test_cannot_afford_exceeds_task_limit(self, tmp_path):
        from src.budgeting.token_budget_manager import TokenUsage

        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 1_000_000
        mgr.budget.per_task_limit["review"] = 300
        mgr.period_used = 0

        today = mgr.current_day
        u = TokenUsage(
            timestamp=f"{today}T09:00:00",
            agent="a",
            task_type="review",
            tokens_used=250,
        )
        mgr.tracker.usage_history.append(u)

        assert mgr.can_afford_agent("a", "review", 100) is False

    def test_get_budget_status_healthy(self, tmp_path):
        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 1_000_000
        mgr.period_used = 100_000

        status = mgr.get_budget_status()
        assert status["global_used"] == 100_000
        assert status["global_limit"] == 1_000_000
        assert status["at_escalation"] is False
        assert status["at_critical"] is False
        assert status["remaining"] == 900_000

    def test_get_budget_status_at_escalation(self, tmp_path):
        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 1_000_000
        mgr.period_used = 850_000  # 85% — above 80% threshold

        status = mgr.get_budget_status()
        assert status["at_escalation"] is True
        assert status["at_critical"] is False

    def test_get_budget_status_at_critical(self, tmp_path):
        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 1_000_000
        mgr.period_used = 960_000  # 96% — above 95% threshold

        status = mgr.get_budget_status()
        assert status["at_critical"] is True

    def test_record_task_completion_increments_period_used(self, tmp_path):
        import src.budgeting.token_budget_manager as mod

        history_file = tmp_path / "usage_history.jsonl"
        with patch.object(mod, "USAGE_HISTORY_FILE", history_file):
            mgr = _make_manager_no_io(tmp_path)
            mgr.tracker._history_file = history_file

            # Patch tracker.record_usage to avoid real file write
            with patch.object(mgr.tracker, "record_usage") as mock_record:
                mgr.record_task_completion("claude", "review", 400)
                mock_record.assert_called_once_with("claude", "review", 400, True, 0.0)

            assert mgr.period_used == 400

    def test_handle_budget_constraint_returns_original_when_affordable(self, tmp_path):
        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 1_000_000
        mgr.period_used = 0

        # get_average_tokens returns 0 for unknown agent → can afford 0 tokens
        result = mgr.handle_budget_constraint("claude", "review", ["ollama", "lmstudio"])
        assert result == "claude"

    def test_handle_budget_constraint_returns_none_when_all_over_budget(self, tmp_path):
        from src.budgeting.token_budget_manager import TokenUsage

        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 100
        mgr.period_used = 50  # room for nothing above 50

        # Give both agents known average usage well above remaining budget
        now = datetime.now().isoformat()
        for agent in ("claude", "ollama"):
            u = TokenUsage(timestamp=now, agent=agent, task_type="review", tokens_used=200)
            mgr.tracker.usage_history.append(u)
            mgr.tracker._update_totals(u)

        result = mgr.handle_budget_constraint("claude", "review", ["ollama"])
        assert result is None

    def test_suggest_efficient_agent_delegates_to_tracker(self, tmp_path):
        mgr = _make_manager_no_io(tmp_path)
        with patch.object(mgr.tracker, "recommend_efficient_agent", return_value="ollama") as mock_rec:
            result = mgr.suggest_efficient_agent("code_review")
            mock_rec.assert_called_once_with("code_review")
            assert result == "ollama"

    def test_generate_report_contains_key_sections(self, tmp_path):
        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 1_000_000
        mgr.period_used = 100_000

        report = mgr.generate_report()
        assert "TOKEN BUDGET REPORT" in report
        assert "CURRENT PERIOD" in report
        assert "STATUS" in report
        assert "HEALTHY" in report

    def test_generate_report_escalation_status(self, tmp_path):
        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 1_000_000
        mgr.period_used = 850_000

        report = mgr.generate_report()
        assert "ESCALATION" in report

    def test_generate_report_critical_status(self, tmp_path):
        mgr = _make_manager_no_io(tmp_path)
        mgr.budget.global_limit = 1_000_000
        mgr.period_used = 970_000

        report = mgr.generate_report()
        assert "CRITICAL" in report


# ---------------------------------------------------------------------------
# TokenBudgetManager — save/load with tmp_path
# ---------------------------------------------------------------------------


class TestTokenBudgetManagerPersistence:
    def test_save_and_load_budgets(self, tmp_path):
        import src.budgeting.token_budget_manager as mod

        budgets_file = tmp_path / "token_budgets.json"
        history_file = tmp_path / "usage_history.jsonl"

        with (
            patch.object(mod, "BUDGETS_FILE", budgets_file),
            patch.object(mod, "USAGE_HISTORY_FILE", history_file),
        ):
            from src.budgeting.token_budget_manager import TokenBudgetManager

            mgr = TokenBudgetManager()
            mgr.budget.global_limit = 55_000
            mgr.budget.set_agent_limit("ollama", 10_000)
            mgr.save_budgets()

            # New instance should load saved config
            mgr2 = TokenBudgetManager()

        assert mgr2.budget.global_limit == 55_000
        assert mgr2.budget.per_agent_limit.get("ollama") == 10_000

    def test_load_budgets_missing_file_uses_defaults(self, tmp_path):
        import src.budgeting.token_budget_manager as mod

        budgets_file = tmp_path / "no_budgets.json"
        history_file = tmp_path / "no_history.jsonl"

        with (
            patch.object(mod, "BUDGETS_FILE", budgets_file),
            patch.object(mod, "USAGE_HISTORY_FILE", history_file),
        ):
            from src.budgeting.token_budget_manager import TokenBudgetManager

            mgr = TokenBudgetManager()

        assert mgr.budget.global_limit == 1_000_000
