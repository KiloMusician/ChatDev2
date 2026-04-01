"""Intelligent Token Budgeting System.

Manages token usage across agents and tasks with budget constraints and optimization.
Tracks patterns, predicts usage, provides cost-aware fallback strategies.

Features:
- Global, per-agent, and per-task-type budgets
- Token usage tracking and trend analysis
- Budget projection and forecasting
- Smart fallback when approaching limits
- Cost optimization recommendations
- Graceful degradation under constraints

OmniTag: [budgeting, cost, tokens, optimization, constraints, efficiency]
"""

import json
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Storage
BUDGETS_FILE = Path("state/budgets/token_budgets.json")
USAGE_HISTORY_FILE = Path("state/budgets/usage_history.jsonl")


@dataclass
class TokenBudget:
    """Budget constraints and thresholds."""

    global_limit: int = 1_000_000  # 1M tokens/day default
    per_agent_limit: dict[str, int] = field(default_factory=dict)
    per_task_limit: dict[str, int] = field(default_factory=dict)
    escalation_threshold: float = 0.8  # Alert at 80% of limit
    critical_threshold: float = 0.95  # Restrict at 95% of limit

    def set_agent_limit(self, agent: str, limit: int):
        """Set per-agent token limit."""
        self.per_agent_limit[agent] = limit
        logger.info(f"Set budget for {agent}: {limit:,} tokens")

    def set_task_limit(self, task_type: str, limit: int):
        """Set per-task-type token limit."""
        self.per_task_limit[task_type] = limit
        logger.info(f"Set budget for {task_type}: {limit:,} tokens")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "global_limit": self.global_limit,
            "per_agent_limit": self.per_agent_limit,
            "per_task_limit": self.per_task_limit,
            "escalation_threshold": self.escalation_threshold,
            "critical_threshold": self.critical_threshold,
            "timestamp": datetime.now().isoformat(),
        }


@dataclass
class TokenUsage:
    """Single token usage record."""

    timestamp: str
    agent: str
    task_type: str
    tokens_used: int
    cost_usd: float = 0.0
    success: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "agent": self.agent,
            "task_type": self.task_type,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "success": self.success,
        }


class TokenTracker:
    """Track and analyze token usage patterns."""

    def __init__(self):
        """Initialize TokenTracker."""
        self.usage_history: list[TokenUsage] = []
        self.agent_totals: dict[str, int] = defaultdict(int)
        self.task_totals: dict[str, int] = defaultdict(int)
        self.daily_totals: dict[str, int] = defaultdict(int)
        self.load_history()

    def load_history(self):
        """Load historical usage data."""
        if USAGE_HISTORY_FILE.exists():
            try:
                with open(USAGE_HISTORY_FILE) as f:
                    for line in f:
                        data = json.loads(line)
                        usage = TokenUsage(**data)
                        self.usage_history.append(usage)
                        self._update_totals(usage)

                logger.info(f"Loaded {len(self.usage_history)} usage records")

            except Exception as e:
                logger.error(f"Failed to load usage history: {e}")

    def record_usage(
        self,
        agent: str,
        task_type: str,
        tokens_used: int,
        success: bool = True,
        cost_usd: float = 0.0,
    ):
        """Record token usage for tracking."""
        usage = TokenUsage(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            task_type=task_type,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            success=success,
        )

        self.usage_history.append(usage)
        self._update_totals(usage)
        self._save_usage(usage)

        logger.debug(f"Recorded: {agent}/{task_type} = {tokens_used} tokens")

    def _update_totals(self, usage: TokenUsage):
        """Update aggregate totals."""
        self.agent_totals[usage.agent] += usage.tokens_used
        self.task_totals[usage.task_type] += usage.tokens_used

        date_key = usage.timestamp[:10]  # YYYY-MM-DD
        self.daily_totals[date_key] += usage.tokens_used

    def _save_usage(self, usage: TokenUsage):
        """Persist usage to file (append-only)."""
        try:
            USAGE_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

            with open(USAGE_HISTORY_FILE, "a") as f:
                f.write(json.dumps(usage.to_dict()) + "\n")

        except Exception as e:
            logger.error(f"Failed to save usage: {e}")

    def get_average_tokens(self, agent: str | None = None, task_type: str | None = None) -> float:
        """Calculate average tokens per task."""
        relevant = self.usage_history

        if agent:
            relevant = [u for u in relevant if u.agent == agent]

        if task_type:
            relevant = [u for u in relevant if u.task_type == task_type]

        if not relevant:
            return 0.0

        return statistics.mean(u.tokens_used for u in relevant)

    def predict_total_for_task(self, agent: str, task_type: str, num_calls: int) -> int:
        """Estimate total tokens needed for multiple calls."""
        avg = self.get_average_tokens(agent=agent, task_type=task_type)
        return int(avg * num_calls)

    def get_usage_trend(self, agent: str, hours: int = 24) -> list[int]:
        """Get usage trend over time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()

        relevant = [u for u in self.usage_history if u.timestamp > cutoff_str and u.agent == agent]
        return [u.tokens_used for u in relevant]

    def get_daily_usage(self, date: str | None = None) -> int:
        """Get total tokens used on a specific date."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        return self.daily_totals.get(date, 0)

    def get_efficiency_score(self, agent: str, task_type: str) -> float:
        """Calculate efficiency score (lower is better).

        Based on tokens per successful task.
        """
        relevant = [
            u
            for u in self.usage_history
            if u.agent == agent and u.task_type == task_type and u.success
        ]

        if not relevant:
            return 0.0

        # Average tokens for successful tasks
        avg_tokens = statistics.mean(u.tokens_used for u in relevant)

        # Success rate bonus (0.5-1.0 factor)
        success_rate = sum(1 for u in relevant if u.success) / len(relevant)

        return avg_tokens * (1.0 / success_rate)

    def recommend_efficient_agent(self, task_type: str) -> str | None:
        """Find most efficient agent for task type."""
        agents_by_efficiency = []

        # Get agents that have done this task type
        agents = {u.agent for u in self.usage_history if u.task_type == task_type}

        for agent in agents:
            score = self.get_efficiency_score(agent, task_type)
            agents_by_efficiency.append((agent, score))

        if not agents_by_efficiency:
            return None

        # Sort by efficiency (lower is better)
        best = min(agents_by_efficiency, key=lambda x: x[1])
        return best[0]


class TokenBudgetManager:
    """Manage token budgets and enforce constraints."""

    def __init__(self):
        """Initialize TokenBudgetManager."""
        self.budget = TokenBudget()
        self.tracker = TokenTracker()
        self.load_budgets()

        # Current period tracking
        self.current_day = datetime.now().strftime("%Y-%m-%d")
        self.period_used = self._get_period_used()

    def load_budgets(self):
        """Load budget configuration from file."""
        if BUDGETS_FILE.exists():
            try:
                with open(BUDGETS_FILE) as f:
                    data = json.load(f)

                self.budget.global_limit = data.get("global_limit", self.budget.global_limit)
                self.budget.per_agent_limit = data.get("per_agent_limit", {})
                self.budget.per_task_limit = data.get("per_task_limit", {})
                self.budget.escalation_threshold = data.get("escalation_threshold", 0.8)
                self.budget.critical_threshold = data.get("critical_threshold", 0.95)

                logger.info("Loaded budget configuration")

            except Exception as e:
                logger.error(f"Failed to load budgets: {e}")

    def save_budgets(self):
        """Save budget configuration to file."""
        try:
            BUDGETS_FILE.parent.mkdir(parents=True, exist_ok=True)

            with open(BUDGETS_FILE, "w") as f:
                json.dump(self.budget.to_dict(), f, indent=2)

            logger.info("Saved budget configuration")

        except Exception as e:
            logger.error(f"Failed to save budgets: {e}")

    def _get_period_used(self) -> int:
        """Get tokens used in current period (day)."""
        return self.tracker.get_daily_usage(self.current_day)

    def _check_and_update_period(self):
        """Check if we've moved to a new day."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.current_day:
            self.current_day = today
            self.period_used = 0

    def can_afford_agent(self, agent: str, task_type: str, estimated_tokens: int) -> bool:
        """Check if agent task is within budget."""
        self._check_and_update_period()

        # Check global budget
        if self.period_used + estimated_tokens > self.budget.global_limit:
            return False

        # Check per-agent budget
        if agent in self.budget.per_agent_limit:
            agent_today = sum(
                u.tokens_used
                for u in self.tracker.usage_history
                if u.agent == agent and u.timestamp.startswith(self.current_day)
            )
            if agent_today + estimated_tokens > self.budget.per_agent_limit[agent]:
                return False

        # Check per-task budget
        if task_type in self.budget.per_task_limit:
            task_today = sum(
                u.tokens_used
                for u in self.tracker.usage_history
                if u.task_type == task_type and u.timestamp.startswith(self.current_day)
            )
            if task_today + estimated_tokens > self.budget.per_task_limit[task_type]:
                return False

        return True

    def get_budget_status(self) -> dict[str, Any]:
        """Get current budget utilization."""
        self._check_and_update_period()

        global_pct = (self.period_used / self.budget.global_limit) * 100
        at_escalation = global_pct >= (self.budget.escalation_threshold * 100)
        at_critical = global_pct >= (self.budget.critical_threshold * 100)

        return {
            "date": self.current_day,
            "global_used": self.period_used,
            "global_limit": self.budget.global_limit,
            "global_percent": round(global_pct, 1),
            "at_escalation": at_escalation,
            "at_critical": at_critical,
            "remaining": self.budget.global_limit - self.period_used,
        }

    def suggest_efficient_agent(self, task_type: str) -> str | None:
        """Recommend most token-efficient agent for task."""
        return self.tracker.recommend_efficient_agent(task_type)

    def handle_budget_constraint(
        self, original_agent: str, task_type: str, available_agents: list[str]
    ) -> str | None:
        """Find alternative agent within budget.

        Strategy:
        1. Check if original agent can fit (check estimates)
        2. Find most efficient among available agents
        3. Return alternative or None if no fit
        """
        # Try original agent first
        avg_tokens = self.tracker.get_average_tokens(agent=original_agent, task_type=task_type)
        if self.can_afford_agent(original_agent, task_type, int(avg_tokens)):
            return original_agent

        # Find efficient alternative within budget
        for agent in available_agents:
            if agent == original_agent:
                continue

            agent_avg = self.tracker.get_average_tokens(agent=agent, task_type=task_type)
            if self.can_afford_agent(agent, task_type, int(agent_avg)):
                logger.info(f"Budget fallback: {original_agent} → {agent}")
                return agent

        # No agent fits budget
        logger.warning(f"Budget constraint: no agent available for {task_type}")
        return None

    def record_task_completion(
        self,
        agent: str,
        task_type: str,
        tokens_used: int,
        success: bool = True,
        cost_usd: float = 0.0,
    ):
        """Record completed task for budget tracking."""
        self.tracker.record_usage(agent, task_type, tokens_used, success, cost_usd)
        self.period_used += tokens_used

        # Check if we hit escalation/critical thresholds
        status = self.get_budget_status()

        if status["at_critical"]:
            logger.warning(f"🚨 CRITICAL budget threshold: {status['global_percent']:.1f}% used")
        elif status["at_escalation"]:
            logger.warning(f"⚠️ Budget escalation: {status['global_percent']:.1f}% used")

    def generate_report(self) -> str:
        """Generate human-readable budget report."""
        status = self.get_budget_status()

        report = ["💰 TOKEN BUDGET REPORT\n"]

        # Current usage
        report.append("[CURRENT PERIOD]")
        report.append(f"  Date: {status['date']}")
        report.append(f"  Used: {status['global_used']:,} / {status['global_limit']:,} tokens")
        report.append(f"  Utilization: {status['global_percent']:.1f}%")
        report.append(f"  Remaining: {status['remaining']:,} tokens\n")

        # Status indicators
        report.append("[STATUS]")
        if status["at_critical"]:
            report.append("  🚨 CRITICAL: >95% of budget used")
        elif status["at_escalation"]:
            report.append("  ⚠️ ESCALATION: >80% of budget used")
        else:
            report.append("  ✅ HEALTHY: Budget available")
        report.append("")

        # Top agents by usage
        if self.tracker.agent_totals:
            report.append("[TOP AGENTS]")
            top_agents = sorted(self.tracker.agent_totals.items(), key=lambda x: x[1], reverse=True)
            for agent, tokens in top_agents[:5]:
                pct = (tokens / sum(self.tracker.agent_totals.values())) * 100
                report.append(f"  {agent:<30} {tokens:>10,} tokens ({pct:>5.1f}%)")
            report.append("")

        # Efficiency recommendations
        report.append("[EFFICIENCY OPPORTUNITIES]")
        for task_type in {u.task_type for u in self.tracker.usage_history}:
            efficient_agent = self.tracker.recommend_efficient_agent(task_type)
            if efficient_agent:
                score = self.tracker.get_efficiency_score(efficient_agent, task_type)
                report.append(
                    f"  {task_type}: Use {efficient_agent} (efficiency: {score:.0f} tokens)"
                )

        return "\n".join(report)


def demo_token_budgeting():
    """Demonstrate token budgeting system."""
    logger.info("💰 TOKEN BUDGETING SYSTEM DEMO\n")

    manager = TokenBudgetManager()

    # Setup budgets
    logger.info("[1] CONFIGURE BUDGETS")
    manager.budget.global_limit = 100_000  # 100K tokens/day demo
    manager.budget.set_agent_limit("fast-agent", 40_000)
    manager.budget.set_agent_limit("slow-agent", 30_000)
    manager.budget.set_task_limit("code_review", 5_000)
    manager.budget.set_task_limit("code_generation", 15_000)
    manager.save_budgets()
    logger.info("Budgets configured\n")

    # Record some usage
    logger.info("[2] RECORD USAGE")
    manager.record_task_completion("fast-agent", "code_review", 800, True, 0.02)
    manager.record_task_completion("fast-agent", "code_review", 750, True, 0.02)
    manager.record_task_completion("slow-agent", "code_review", 1200, True, 0.03)
    manager.record_task_completion("fast-agent", "code_generation", 3500, True, 0.07)
    manager.record_task_completion("slow-agent", "code_generation", 5000, False, 0.10)
    logger.info("Usage recorded\n")

    # Check affordability
    logger.info("[3] CHECK AFFORDABILITY")
    can_afford_fast = manager.can_afford_agent("fast-agent", "code_review", 800)
    can_afford_slow = manager.can_afford_agent("slow-agent", "code_generation", 15000)
    logger.info(f"  fast-agent for code_review (800 tokens): {can_afford_fast}")
    logger.info(f"  slow-agent for code_generation (15K tokens): {can_afford_slow}\n")

    # Get efficiency recommendations
    logger.info("[4] EFFICIENCY RECOMMENDATIONS")
    efficient_review = manager.suggest_efficient_agent("code_review")
    efficient_gen = manager.suggest_efficient_agent("code_generation")
    logger.info(f"  Most efficient for code_review: {efficient_review}")
    logger.info(f"  Most efficient for code_generation: {efficient_gen}\n")

    # Generate report
    logger.info("[5] BUDGET REPORT")
    logger.info(manager.generate_report())


if __name__ == "__main__":
    demo_token_budgeting()
