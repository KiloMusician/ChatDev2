#!/usr/bin/env python3
"""NuSyQ Suggestion Engine - Productive Instincts for Autonomous Evolution.

This module provides the system with actionable suggestions it can surface,
select from, or execute when prompted with simple conversational phrases like:
- "proceed"
- "what's useful right now?"
- "optimize"
- "what should we work on?"

Think of these as **capability seeds** — not forced tasks, but productive
instincts the system can act on when intelligence is idle or directed.
"""

import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SuggestionCategory(Enum):
    """Categories of suggestions aligned with NuSyQ domains."""

    CORE_SPINE = "core_spine"  # System orchestration & health
    AGENT_STEWARDSHIP = "agent_stewardship"  # Agent & tool management
    MODEL_STEWARDSHIP = "model_stewardship"  # LLM & Ollama optimization
    TESTING_CHAMBER = "testing_chamber"  # Experiments & prototypes
    KNOWLEDGE = "knowledge"  # Memory & learning
    CODEBASE_HEALTH = "codebase_health"  # Code quality & evolution
    GAME_EVOLUTION = "game_evolution"  # SimulatedVerse & UI
    HUMAN_FACTORS = "human_factors"  # Workflow & sanity
    META_EVOLUTION = "meta_evolution"  # Emergence & self-awareness


class RiskLevel(Enum):
    """Risk assessment for suggestions."""

    SAFE = "safe"  # Read-only, analysis, reporting
    MODERATE = "moderate"  # Creates files, modifies config
    BOLD = "bold"  # Structural changes, requires approval


class EffortLevel(Enum):
    """Effort required to execute suggestion."""

    QUICK = "quick"  # < 5 minutes
    MEDIUM = "medium"  # 5-30 minutes
    DEEP = "deep"  # > 30 minutes


@dataclass
class Suggestion:
    """A single actionable suggestion."""

    id: str
    title: str
    description: str
    category: SuggestionCategory
    risk: RiskLevel
    effort: EffortLevel
    payoff: str  # What value this provides
    triggers: list[str]  # When to suggest this
    implementation_hint: str  # How to actually do it
    dependencies: list[str]  # What must exist first

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "risk": self.risk.value,
            "effort": self.effort.value,
            "payoff": self.payoff,
            "triggers": self.triggers,
            "implementation_hint": self.implementation_hint,
            "dependencies": self.dependencies,
        }


# Comprehensive suggestion catalog (drawn from the user's list)
SUGGESTION_CATALOG = [
    # A. Core Spine Suggestions
    Suggestion(
        id="spine_snapshot_deltas",
        title="Enhance System Snapshot with Deltas",
        description="Add delta tracking to system snapshots: files changed, errors reduced, agents used since last run",
        category=SuggestionCategory.CORE_SPINE,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Turns observability into understanding; makes 'prove the spine' richer over time",
        triggers=["idle", "snapshot", "status", "what changed"],
        implementation_hint="Extend scripts/start_nusyq.py to read previous snapshot and compute diffs",
        dependencies=["scripts/start_nusyq.py"],
    ),
    Suggestion(
        id="doctrine_drift_detection",
        title="Check Doctrine vs Reality",
        description="Compare instruction files against actual behavior; identify violated rules; suggest doctrine updates",
        category=SuggestionCategory.CORE_SPINE,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.DEEP,
        payoff="Prevents doctrine rot; keeps culture ship coherent",
        triggers=["audit", "doctrine", "check instructions", "validate rules"],
        implementation_hint="Parse .instructions.md files, analyze recent actions, flag mismatches",
        dependencies=[".github/instructions/*.md"],
    ),
    Suggestion(
        id="emergent_capability_capture",
        title="Capture Emergent Behavior",
        description="Detect phase jumps, record what was done ahead of time, classify and suggest promotion",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Turns surprises into assets; prevents fear of initiative",
        triggers=["emergence", "phase jump", "what did I do"],
        implementation_hint="Analyze git commits, session logs, quest entries for unplanned capabilities",
        dependencies=["quest_log.jsonl", "git history"],
    ),
    # B. Agent & Tool Stewardship
    Suggestion(
        id="agent_utilization_metrics",
        title="Review Agent Utilization",
        description="Identify rarely-used agents, detect overlap, suggest consolidation or clearer routing",
        category=SuggestionCategory.AGENT_STEWARDSHIP,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.QUICK,
        payoff="Prevents silent inefficiency; encourages healthy multi-agent behavior",
        triggers=["agents", "utilization", "who's working", "agent health"],
        implementation_hint="Parse quest logs and orchestrator metrics for agent invocations",
        dependencies=["quest_log.jsonl", "orchestrator metrics"],
    ),
    # C. Model Stewardship
    Suggestion(
        id="model_roster_optimization",
        title="Review Model Roster Health",
        description="Re-test models with small/medium prompts, detect degradation, recommend role swaps",
        category=SuggestionCategory.MODEL_STEWARDSHIP,
        risk=RiskLevel.MODERATE,
        effort=EffortLevel.MEDIUM,
        payoff="Keeps Ollama useful, not bloated; respects hardware and solo workflow",
        triggers=["models", "ollama", "performance", "which model"],
        implementation_hint="Use health_check() on each Ollama model, time responses, flag slow/broken ones",
        dependencies=["ollama", "src/orchestration/multi_ai_orchestrator.py"],
    ),
    # D. Testing Chamber
    Suggestion(
        id="dormant_prototype_revival",
        title="Look for Dormant Experiments",
        description="Scan testing chambers for unfinished but promising work; summarize and suggest revival",
        category=SuggestionCategory.TESTING_CHAMBER,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Recovers lost intelligence; honors past effort",
        triggers=["experiments", "prototypes", "what did we try", "dormant"],
        implementation_hint="Scan NuSyQ/ChatDev/WareHouse/, SimulatedVerse/testing_chamber/, prototypes/",
        dependencies=["testing chambers"],
    ),
    # E. Knowledge & Memory
    Suggestion(
        id="knowledge_compaction",
        title="Compact Recent Learnings",
        description="Turn long session logs into short, durable insights; update central 'What We Learned'",
        category=SuggestionCategory.KNOWLEDGE,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Prevents cognitive overload; makes system feel smarter over time",
        triggers=["learn", "compress", "what did we learn", "insights"],
        implementation_hint="Parse docs/Agent-Sessions/*.md, extract key decisions, update knowledge base",
        dependencies=["docs/Agent-Sessions/", "knowledge-base.yaml"],
    ),
    # F. Codebase Health
    Suggestion(
        id="hardcoded_assumption_hunting",
        title="Find Brittle Assumptions",
        description="Search for hardcoded ports, paths, model names; identify config duplication",
        category=SuggestionCategory.CODEBASE_HEALTH,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.QUICK,
        payoff="Reduces future breakage; addresses port chaos issues",
        triggers=["hardcoded", "assumptions", "config", "brittle"],
        implementation_hint="Grep for localhost:, 127.0.0.1:, specific model names, absolute paths",
        dependencies=["codebase"],
    ),
    Suggestion(
        id="reversibility_audit",
        title="Audit Reversibility",
        description="Identify changes hard to undo; suggest feature flags and safer wrappers",
        category=SuggestionCategory.CODEBASE_HEALTH,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Enables bold experimentation safely; supports 'ship messy but reversible' philosophy",
        triggers=["reversible", "rollback", "safety", "undo"],
        implementation_hint="Scan for direct database writes, file deletions, config overwrites without backups",
        dependencies=["codebase"],
    ),
    # G. Game Evolution
    Suggestion(
        id="game_loop_detection",
        title="What Parts Already Feel Like a Game?",
        description="Identify loops (quest → action → feedback), highlight progression mechanics",
        category=SuggestionCategory.GAME_EVOLUTION,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Reinforces long-term goal; makes development motivating",
        triggers=["game", "ui", "progression", "feel"],
        implementation_hint="Analyze quest system, orchestrator feedback, agent interactions for game patterns",
        dependencies=["quest system", "SimulatedVerse"],
    ),
    # H. Human Factors
    Suggestion(
        id="optimize_for_sanity",
        title="What Would Help Keath Right Now?",
        description="Reduce noise, suggest one high-impact action, surface progress you might not notice",
        category=SuggestionCategory.HUMAN_FACTORS,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.QUICK,
        payoff="System is for YOU; burnout avoidance is core constraint",
        triggers=["help", "overwhelmed", "what matters", "sanity"],
        implementation_hint="Analyze recent activity, identify noise sources, propose single focused action",
        dependencies=["session context"],
    ),
    Suggestion(
        id="overnight_work_proposals",
        title="Propose Safe Overnight Work",
        description="Suggest analysis passes, documentation, health checks that are safe to run autonomously",
        category=SuggestionCategory.HUMAN_FACTORS,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Builds trust; lets you rest without anxiety",
        triggers=["overnight", "autonomous", "while I sleep", "safe mode"],
        implementation_hint="List read-only analysis tasks, doc improvements, health audits",
        dependencies=["safe mode operations"],
    ),
]


class SuggestionEngine:
    """Engine for surfacing and executing productive suggestions."""

    def __init__(self, catalog: list[Suggestion] | None = None) -> None:
        """Initialize suggestion engine.

        Args:
            catalog: List of suggestions (defaults to SUGGESTION_CATALOG)
        """
        self.catalog = catalog or SUGGESTION_CATALOG
        self.history_path = Path("state/suggestions/history.jsonl")
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"✅ Suggestion engine initialized with {len(self.catalog)} suggestions")

    def suggest(
        self,
        context: str,
        max_suggestions: int = 3,
        filter_category: SuggestionCategory | None = None,
        filter_risk: RiskLevel | None = None,
    ) -> list[Suggestion]:
        """Get contextually relevant suggestions.

        Args:
            context: User's context or prompt
            max_suggestions: Maximum number to return
            filter_category: Optional category filter
            filter_risk: Optional risk level filter

        Returns:
            List of relevant suggestions
        """
        context_lower = context.lower()

        # Filter by category/risk
        filtered = self.catalog
        if filter_category:
            filtered = [s for s in filtered if s.category == filter_category]
        if filter_risk:
            filtered = [s for s in filtered if s.risk == filter_risk]

        # Score by trigger match
        scored = []
        for suggestion in filtered:
            score = 0
            for trigger in suggestion.triggers:
                if trigger in context_lower:
                    score += 1

            # Boost by category relevance
            if (
                "agent" in context_lower
                and suggestion.category == SuggestionCategory.AGENT_STEWARDSHIP
            ):
                score += 2
            if (
                "model" in context_lower
                and suggestion.category == SuggestionCategory.MODEL_STEWARDSHIP
            ):
                score += 2
            if (
                "experiment" in context_lower
                and suggestion.category == SuggestionCategory.TESTING_CHAMBER
            ):
                score += 2

            scored.append((score, suggestion))

        # Sort by score and return top N
        scored.sort(reverse=True, key=lambda x: x[0])

        # If no good matches, return random safe suggestions
        if not scored or scored[0][0] == 0:
            safe_suggestions = [s for s in filtered if s.risk == RiskLevel.SAFE]
            return random.sample(safe_suggestions, min(max_suggestions, len(safe_suggestions)))

        return [s for _, s in scored[:max_suggestions]]

    def log_suggestion(self, suggestion: Suggestion, executed: bool, outcome: str = "") -> None:
        """Log suggestion to history.

        Args:
            suggestion: The suggestion
            executed: Whether it was executed
            outcome: Result of execution
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "suggestion_id": suggestion.id,
            "executed": executed,
            "outcome": outcome,
        }

        with open(self.history_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_safe_suggestions(self, max_count: int = 5) -> list[Suggestion]:
        """Get safe suggestions suitable for autonomous execution.

        Args:
            max_count: Maximum suggestions to return

        Returns:
            List of safe suggestions
        """
        safe = [s for s in self.catalog if s.risk == RiskLevel.SAFE]
        return safe[:max_count]

    def format_suggestion(self, suggestion: Suggestion) -> str:
        """Format suggestion for display.

        Args:
            suggestion: Suggestion to format

        Returns:
            Formatted string
        """
        risk_emoji = {
            RiskLevel.SAFE: "✅",
            RiskLevel.MODERATE: "⚠️",
            RiskLevel.BOLD: "🔥",
        }

        effort_emoji = {
            EffortLevel.QUICK: "⚡",
            EffortLevel.MEDIUM: "🔧",
            EffortLevel.DEEP: "🔬",
        }

        return f"""
{risk_emoji[suggestion.risk]} {effort_emoji[suggestion.effort]} **{suggestion.title}**

{suggestion.description}

💡 **Payoff:** {suggestion.payoff}
🎯 **Category:** {suggestion.category.value}
⏱️ **Effort:** {suggestion.effort.value}
🛡️ **Risk:** {suggestion.risk.value}

**How to do it:** {suggestion.implementation_hint}
"""


# Global engine instance
_global_engine: SuggestionEngine | None = None


def get_engine() -> SuggestionEngine:
    """Get or create global engine instance."""
    global _global_engine
    if _global_engine is None:
        _global_engine = SuggestionEngine()
    return _global_engine


def suggest_next_action(context: str = "idle") -> list[Suggestion]:
    """Convenience function to get suggestions.

    Args:
        context: Current context or user prompt

    Returns:
        List of relevant suggestions
    """
    engine = get_engine()
    return engine.suggest(context)
