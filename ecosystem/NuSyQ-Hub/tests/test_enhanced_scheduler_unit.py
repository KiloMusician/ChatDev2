"""Unit tests for EnhancedTaskScheduler and DiversityQuota.

Targets the ~18% of uncovered branches:
- categorize_task keyword branches (LINT/BUGFIX/REFACTOR/TEST/DOCS/PERF/DEP/FEATURE/SECURITY)
- DiversityQuota.can_select consecutive limit + variety enforcement
- DiversityQuota.record_selection same-category / batch-reset paths
- DiversityQuota.get_diversity_boost all three count buckets
- calculate_urgency_score age, deadline, security branches
- calculate_task_value priority tier selection (CRITICAL/HIGH/LOW/DEFERRED)
- select_next_batch empty list, error handling, diversity rejection
- record_execution_result learning disabled early-return
- get_scheduler_stats with populated history
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, UTC
from unittest.mock import MagicMock, patch

import pytest

from src.orchestration.enhanced_task_scheduler import (
    DiversityQuota,
    EnhancedTaskScheduler,
    PriorityTier,
    TaskCategory,
    TaskMetrics,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task(
    prompt: str = "", meta_cat: str | None = None, priority_val: int | None = None
) -> MagicMock:
    """Return a minimal task-like mock."""
    t = MagicMock(spec=[])  # empty spec → no auto-attributes
    t.prompt = prompt
    t.description = ""
    t.metadata = {"category": meta_cat} if meta_cat else {}
    if priority_val is not None:
        t.priority = MagicMock()
        t.priority.value = priority_val
    return t


def _sched(diversity: bool = True, learning: bool = True) -> EnhancedTaskScheduler:
    return EnhancedTaskScheduler(
        orchestrator=MagicMock(), enable_diversity=diversity, learning_enabled=learning
    )


# ---------------------------------------------------------------------------
# categorize_task — keyword branches
# ---------------------------------------------------------------------------


class TestCategorizeTask:
    """Cover each keyword-dispatch branch individually."""

    def test_metadata_category_takes_priority(self):
        s = _sched()
        t = _task("fix everything", meta_cat="SECURITY")
        assert s.categorize_task(t) == TaskCategory.SECURITY

    def test_metadata_unknown_key_falls_through_to_keywords(self):
        s = _sched()
        t = _task("lint this file", meta_cat="NOPE")
        assert s.categorize_task(t) == TaskCategory.LINT

    def test_security_keyword(self):
        s = _sched()
        assert s.categorize_task(_task("fix cve-2025-1234")) == TaskCategory.SECURITY
        assert s.categorize_task(_task("address vulnerability in auth")) == TaskCategory.SECURITY

    def test_lint_keyword(self):
        s = _sched()
        assert s.categorize_task(_task("run ruff check")) == TaskCategory.LINT
        assert s.categorize_task(_task("format with black")) == TaskCategory.LINT

    def test_bugfix_keyword(self):
        s = _sched()
        assert s.categorize_task(_task("fix import error")) == TaskCategory.BUGFIX
        assert s.categorize_task(_task("resolve bug in routing")) == TaskCategory.BUGFIX

    def test_refactor_keyword(self):
        s = _sched()
        assert s.categorize_task(_task("refactor scheduler logic")) == TaskCategory.REFACTOR
        assert s.categorize_task(_task("optimize db queries")) == TaskCategory.REFACTOR

    def test_test_keyword(self):
        s = _sched()
        # "improve" matches REFACTOR before TEST — use unambiguous TEST keywords
        assert s.categorize_task(_task("add coverage report")) == TaskCategory.TEST
        assert s.categorize_task(_task("add unittest for api")) == TaskCategory.TEST

    def test_docs_keyword(self):
        s = _sched()
        assert s.categorize_task(_task("update readme")) == TaskCategory.DOCS
        assert s.categorize_task(_task("add doc string")) == TaskCategory.DOCS

    def test_performance_keyword(self):
        s = _sched()
        # "improve" matches REFACTOR first — use unambiguous PERFORMANCE keywords
        assert s.categorize_task(_task("performance benchmark run")) == TaskCategory.PERFORMANCE
        assert s.categorize_task(_task("increase speed of load")) == TaskCategory.PERFORMANCE

    def test_dependency_keyword(self):
        s = _sched()
        assert s.categorize_task(_task("upgrade httpx")) == TaskCategory.DEPENDENCY
        assert s.categorize_task(_task("update all dependencies")) == TaskCategory.DEPENDENCY

    def test_feature_keyword(self):
        s = _sched()
        assert s.categorize_task(_task("implement dark mode")) == TaskCategory.FEATURE
        assert s.categorize_task(_task("add new api endpoint")) == TaskCategory.FEATURE
        assert s.categorize_task(_task("create auth flow")) == TaskCategory.FEATURE

    def test_unknown_fallback(self):
        s = _sched()
        assert s.categorize_task(_task("do something random")) == TaskCategory.UNKNOWN


# ---------------------------------------------------------------------------
# DiversityQuota
# ---------------------------------------------------------------------------


class TestDiversityQuotaCanSelect:
    """DiversityQuota.can_select branch coverage."""

    def test_security_always_allowed_regardless_of_consecutive(self):
        dq = DiversityQuota(max_consecutive_same_category=1)
        dq.last_category = TaskCategory.SECURITY
        dq.consecutive_count = 5
        assert dq.can_select(TaskCategory.SECURITY) is True

    def test_consecutive_limit_blocks_selection(self):
        dq = DiversityQuota(max_consecutive_same_category=2)
        dq.last_category = TaskCategory.LINT
        dq.consecutive_count = 2  # Already at limit
        assert dq.can_select(TaskCategory.LINT) is False

    def test_consecutive_limit_not_yet_reached(self):
        dq = DiversityQuota(max_consecutive_same_category=3)
        dq.last_category = TaskCategory.LINT
        dq.consecutive_count = 2  # One under limit
        assert dq.can_select(TaskCategory.LINT) is True

    def test_variety_enforcement_blocks_overrepresented_category(self):
        # batch_size=3, min_variety=2 — all 3 recent slots are LINT → only 1 unique category
        dq = DiversityQuota(batch_size=3, min_category_variety_per_batch=2)
        dq.recent_categories = [TaskCategory.LINT, TaskCategory.LINT, TaskCategory.LINT]
        dq.batch_categories = {TaskCategory.LINT}  # 1 < min_variety=2
        # LINT IS in recent_categories[-3:], so should return False
        assert dq.can_select(TaskCategory.LINT) is False

    def test_variety_enforcement_allows_new_category(self):
        dq = DiversityQuota(batch_size=3, min_category_variety_per_batch=2)
        dq.recent_categories = [TaskCategory.LINT, TaskCategory.LINT, TaskCategory.LINT]
        dq.batch_categories = {TaskCategory.LINT}  # 1 < min_variety=2
        # BUGFIX is NOT in recent_categories[-3:], so should return True
        assert dq.can_select(TaskCategory.BUGFIX) is True

    def test_no_restriction_when_batch_not_full(self):
        dq = DiversityQuota(batch_size=5, min_category_variety_per_batch=2)
        dq.recent_categories = [TaskCategory.LINT]  # Only 1, batch_size=5 not reached
        assert dq.can_select(TaskCategory.LINT) is True


class TestDiversityQuotaRecordSelection:
    """DiversityQuota.record_selection branch coverage."""

    def test_consecutive_count_increments_for_same_category(self):
        dq = DiversityQuota()
        dq.last_category = TaskCategory.LINT
        dq.consecutive_count = 1
        dq.record_selection(TaskCategory.LINT)
        assert dq.consecutive_count == 2

    def test_consecutive_count_resets_for_new_category(self):
        dq = DiversityQuota()
        dq.last_category = TaskCategory.LINT
        dq.consecutive_count = 3
        dq.record_selection(TaskCategory.BUGFIX)
        assert dq.consecutive_count == 1
        assert dq.last_category == TaskCategory.BUGFIX

    def test_recent_categories_trimmed_to_batch_size(self):
        dq = DiversityQuota(batch_size=3)
        # Pre-fill with exactly batch_size entries so adding one triggers trim
        dq.recent_categories = [TaskCategory.LINT, TaskCategory.LINT, TaskCategory.LINT]
        dq.record_selection(TaskCategory.BUGFIX)
        assert len(dq.recent_categories) == 3  # trimmed back to batch_size

    def test_batch_categories_cleared_when_multiple_of_batch_size(self):
        dq = DiversityQuota(batch_size=3)
        # After recording 3rd item, len % batch_size == 0 → clear
        dq.record_selection(TaskCategory.LINT)
        dq.record_selection(TaskCategory.BUGFIX)
        dq.record_selection(TaskCategory.TEST)  # 3rd — triggers clear
        assert len(dq.batch_categories) == 0


class TestDiversityQuotaGetDiversityBoost:
    """DiversityQuota.get_diversity_boost all three count buckets."""

    def test_empty_recent_returns_zero(self):
        dq = DiversityQuota()
        assert dq.get_diversity_boost(TaskCategory.LINT) == 0.0

    def test_category_count_zero_gives_strong_boost(self):
        dq = DiversityQuota(batch_size=5)
        dq.recent_categories = [TaskCategory.BUGFIX, TaskCategory.BUGFIX]
        boost = dq.get_diversity_boost(TaskCategory.LINT)  # LINT not in recent
        assert boost == 0.3

    def test_category_count_one_gives_mild_boost(self):
        dq = DiversityQuota(batch_size=5)
        dq.recent_categories = [TaskCategory.LINT]
        boost = dq.get_diversity_boost(TaskCategory.LINT)
        assert boost == 0.1

    def test_category_count_two_gives_penalty(self):
        dq = DiversityQuota(batch_size=5)
        dq.recent_categories = [TaskCategory.LINT, TaskCategory.LINT]
        boost = dq.get_diversity_boost(TaskCategory.LINT)
        assert boost == pytest.approx(-0.1)

    def test_category_count_three_gives_larger_penalty(self):
        dq = DiversityQuota(batch_size=5)
        dq.recent_categories = [TaskCategory.LINT, TaskCategory.LINT, TaskCategory.LINT]
        boost = dq.get_diversity_boost(TaskCategory.LINT)
        assert boost == pytest.approx(-0.2)


# ---------------------------------------------------------------------------
# calculate_urgency_score — date/deadline/security branches
# ---------------------------------------------------------------------------


class TestCalculateUrgencyScore:
    """Cover deadline and age-based urgency branches."""

    def test_age_days_adds_urgency(self):
        s = _sched()
        t = _task()
        metrics = TaskMetrics(age_days=7.0)  # 1 week → +0.1
        urgency = s.calculate_urgency_score(t, metrics)
        assert urgency >= 0.1

    def test_overdue_deadline_adds_urgency(self):
        s = _sched()
        t = _task()
        past = datetime.now(UTC) - timedelta(days=1)
        metrics = TaskMetrics(deadline=past)
        urgency = s.calculate_urgency_score(t, metrics)
        assert urgency >= 0.5  # overdue adds 0.5

    def test_deadline_within_one_day_adds_urgency(self):
        s = _sched()
        t = _task()
        soon = datetime.now(UTC) + timedelta(hours=6)
        metrics = TaskMetrics(deadline=soon)
        urgency = s.calculate_urgency_score(t, metrics)
        assert urgency >= 0.3

    def test_deadline_within_one_week_adds_urgency(self):
        s = _sched()
        t = _task()
        one_week = datetime.now(UTC) + timedelta(days=3)
        metrics = TaskMetrics(deadline=one_week)
        urgency = s.calculate_urgency_score(t, metrics)
        assert urgency >= 0.2

    def test_high_security_impact_adds_urgency(self):
        s = _sched()
        t = _task()
        metrics = TaskMetrics(security_impact=0.8)  # > 0.5 → +0.4
        urgency = s.calculate_urgency_score(t, metrics)
        assert urgency >= 0.4

    def test_security_impact_below_threshold_no_boost(self):
        s = _sched()
        t = _task()
        metrics = TaskMetrics(security_impact=0.4)  # <= 0.5 → no boost
        urgency = s.calculate_urgency_score(t, metrics)
        assert urgency < 0.4  # no security urgency added

    def test_no_deadline_no_age_zero_urgency(self):
        s = _sched()
        t = _task()
        metrics = TaskMetrics()  # defaults
        urgency = s.calculate_urgency_score(t, metrics)
        assert urgency == 0.0


# ---------------------------------------------------------------------------
# calculate_task_value — priority tier selection
# ---------------------------------------------------------------------------


class TestCalculateTaskValuePriorityTiers:
    """Verify all 5 PriorityTier branches in calculate_task_value."""

    def _value_with_score(self, score: float) -> TaskValue:
        s = _sched(diversity=False)
        t = _task()
        # Patch calculate_*_score methods to return controlled values
        # weights: impact=0.35, urgency=0.25, feasibility=0.25, diversity=0.15
        # We need: impact*0.35 + urgency*0.25 + feasibility*0.25 + diversity*0.15 ≈ score
        # Simplest: make all equal → score = x*(0.35+0.25+0.25+0.15) = x*1.0 = x
        with (
            patch.object(s, "calculate_impact_score", return_value=score),
            patch.object(s, "calculate_urgency_score", return_value=score),
            patch.object(s, "calculate_feasibility_score", return_value=score),
        ):
            return s.calculate_task_value(t)

    def test_score_above_0_8_is_critical(self):
        # Weighted: impact*0.35 + urgency*0.25 + feasibility*0.25 + diversity_neutral*0.15
        # With component=0.95: 0.95*0.85 + 0.5*0.15 = 0.8075 + 0.075 = 0.8825 >= 0.8 → CRITICAL
        v = self._value_with_score(0.95)
        assert v.priority_tier == PriorityTier.CRITICAL

    def test_score_at_0_6_is_high(self):
        v = self._value_with_score(0.65)
        assert v.priority_tier == PriorityTier.HIGH

    def test_score_at_0_4_is_medium(self):
        v = self._value_with_score(0.45)
        assert v.priority_tier == PriorityTier.MEDIUM

    def test_score_at_0_2_is_low(self):
        v = self._value_with_score(0.25)
        assert v.priority_tier == PriorityTier.LOW

    def test_score_below_0_2_is_deferred(self):
        v = self._value_with_score(0.05)
        assert v.priority_tier == PriorityTier.DEFERRED

    def test_high_security_impact_forces_critical(self):
        s = _sched(diversity=False)
        t = _task()
        metrics = TaskMetrics(security_impact=0.9)  # > 0.7 → CRITICAL regardless of score
        v = s.calculate_task_value(t, metrics=metrics)
        assert v.priority_tier == PriorityTier.CRITICAL


# ---------------------------------------------------------------------------
# select_next_batch — empty list, error handling, diversity rejection
# ---------------------------------------------------------------------------


class TestSelectNextBatch:
    """Cover select_next_batch edge cases."""

    def test_empty_available_returns_empty(self):
        s = _sched()
        result = s.select_next_batch([])
        assert result == []

    def test_error_in_value_calculation_is_skipped(self):
        s = _sched(diversity=False)
        t1 = _task("implement feature a")
        t2 = _task("fix this bug")
        with patch.object(
            s,
            "calculate_task_value",
            side_effect=[
                Exception("boom"),
                MagicMock(final_score=0.5, category=TaskCategory.BUGFIX),
            ],
        ):
            result = s.select_next_batch([t1, t2])
        # t1 failed, t2 succeeded — result should have 1 entry
        assert len(result) == 1

    def test_diversity_quota_rejects_over_represented_category(self):
        s = _sched(diversity=True)
        # Override the quota to always reject
        s.diversity_quota.can_select = MagicMock(return_value=False)
        tasks = [_task("lint code"), _task("lint more"), _task("lint again")]
        result = s.select_next_batch(tasks)
        # All rejected by diversity quota
        assert result == []

    def test_batch_size_limit_honoured(self):
        s = _sched(diversity=False)
        tasks = [_task(f"implement feature {i}") for i in range(20)]
        result = s.select_next_batch(tasks, batch_size=5)
        assert len(result) <= 5

    def test_sorted_by_score_descending(self):
        s = _sched(diversity=False)
        high = _task("security cve fix")  # Gets urgency + security boost
        low = _task("update readme")  # DOCS, low urgency
        result = s.select_next_batch([low, high])
        assert len(result) == 2
        # Higher scoring task should come first
        _, val0 = result[0]
        _, val1 = result[1]
        assert val0.final_score >= val1.final_score


# ---------------------------------------------------------------------------
# record_execution_result — learning disabled
# ---------------------------------------------------------------------------


class TestRecordExecutionResult:
    """Cover learning_enabled=False early return."""

    def test_learning_disabled_does_not_record(self):
        s = _sched(learning=False)
        t = _task("fix bug")
        from src.orchestration.enhanced_task_scheduler import TaskValue

        tv = TaskValue(task_id=1, category=TaskCategory.BUGFIX, priority_tier=PriorityTier.MEDIUM)
        s.record_execution_result(t, tv, success=True, duration_seconds=5.0)
        assert len(s.execution_history) == 0

    def test_learning_enabled_records_result(self):
        s = _sched(learning=True)
        t = _task("fix bug")
        from src.orchestration.enhanced_task_scheduler import TaskValue

        tv = TaskValue(task_id=1, category=TaskCategory.BUGFIX, priority_tier=PriorityTier.MEDIUM)
        s.record_execution_result(t, tv, success=True, duration_seconds=5.0)
        assert len(s.execution_history) == 1
        assert s.execution_history[0]["success"] is True

    def test_category_success_rate_updated(self):
        s = _sched(learning=True)
        from src.orchestration.enhanced_task_scheduler import TaskValue

        tv = TaskValue(task_id=1, category=TaskCategory.BUGFIX, priority_tier=PriorityTier.MEDIUM)
        s.record_execution_result(MagicMock(), tv, success=True, duration_seconds=1.0)
        s.record_execution_result(MagicMock(), tv, success=False, duration_seconds=2.0)
        rate = s.category_success_rates[TaskCategory.BUGFIX]
        assert rate == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# get_scheduler_stats — with populated history
# ---------------------------------------------------------------------------


class TestGetSchedulerStats:
    """Cover get_scheduler_stats with data."""

    def test_stats_with_empty_history(self):
        s = _sched()
        stats = s.get_scheduler_stats()
        assert stats["total_executions"] == 0
        assert stats["diversity_enabled"] is True
        assert stats["learning_enabled"] is True

    def test_stats_with_executions(self):
        s = _sched()
        from src.orchestration.enhanced_task_scheduler import TaskValue

        tv = TaskValue(task_id=1, category=TaskCategory.TEST, priority_tier=PriorityTier.HIGH)
        s.record_execution_result(MagicMock(), tv, success=True, duration_seconds=3.0)
        stats = s.get_scheduler_stats()
        assert stats["total_executions"] == 1
        assert "test" in stats["category_success_rates"]

    def test_stats_diversity_disabled(self):
        s = _sched(diversity=False)
        stats = s.get_scheduler_stats()
        assert stats["diversity_enabled"] is False
        assert stats["recent_categories"] == []  # No quota → empty list


# ---------------------------------------------------------------------------
# integrate_enhanced_scheduler (async top-level factory)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_integrate_enhanced_scheduler_returns_scheduler():
    from src.orchestration.enhanced_task_scheduler import integrate_enhanced_scheduler

    orch = MagicMock()
    scheduler = await integrate_enhanced_scheduler(orch)
    assert isinstance(scheduler, EnhancedTaskScheduler)
    assert scheduler.enable_diversity is True
    assert scheduler.learning_enabled is True
