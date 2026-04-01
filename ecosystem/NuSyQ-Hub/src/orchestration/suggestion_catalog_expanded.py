"""Expanded Suggestion Catalog - Permission Space Mapped.

Created: 2025-12-24
Source: "Liberal, Encouraging Suggestion Field" from mentor-voice guidance.

This catalog maps **directions intelligence could flow** when it has energy.
None are required. None are urgent.

These are **productive instincts**, not commands.

The principle: "Do not rush to implement most of these. Let the system *want* them."

🌱 108+ suggestions across 9 categories
📊 Organized by emergence readiness
🎯 Each suggestion includes when/why/how
"""

import logging

from src.orchestration.suggestion_engine import (EffortLevel, RiskLevel,
                                                 Suggestion,
                                                 SuggestionCategory)

logger = logging.getLogger(__name__)

# =============================================================================
# 🌱 SYSTEM SELF-AWARENESS & META-COGNITION (10 suggestions)
# =============================================================================

META_COGNITION_SUGGESTIONS = [
    Suggestion(
        id="reflection_after_action",
        title="Post-Action Reflection",
        description="Add 'what did I just learn?' reflection after major actions to capture emergent insights",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.QUICK,
        payoff="Captures tacit knowledge, builds system self-model over time",
        triggers=[
            "learned",
            "reflection",
            "what did I learn",
            "insight",
        ],
        implementation_hint="Add to orchestrator post-action hooks, log to state/reflections/learning.jsonl",
        dependencies=[],
    ),
    Suggestion(
        id="confidence_annotations",
        title="Confidence Annotations",
        description="Add confidence levels to outputs ('I am 80% confident this is correct') for uncertainty transparency",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Helps humans calibrate trust, reveals areas needing validation",
        triggers=[
            "confidence",
            "certainty",
            "how sure",
            "uncertain",
        ],
        implementation_hint="Add confidence: float field to Suggestion/EmergenceEvent/Response dataclasses",
        dependencies=[],
    ),
    Suggestion(
        id="surprise_detection",
        title="Surprise Detection",
        description="Detect when outcomes diverge from expectations and log as learning moments",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.MODERATE,
        effort=EffortLevel.MEDIUM,
        payoff="Identifies gaps in system model, surfaces implicit assumptions that need revision",
        triggers=[
            "unexpected",
            "surprise",
            "didn't expect",
            "strange",
        ],
        implementation_hint="Add expected_outcome field to operations, compare with actual, log divergences",
        dependencies=[],
    ),
    Suggestion(
        id="assumption_tracking",
        title="Assumption Tracking",
        description="Log assumptions made during reasoning ('I assumed X—was that valid?') for later validation",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Makes implicit reasoning explicit, enables assumption audits and correction",
        triggers=[
            "assume",
            "assumption",
            "presuppose",
            "given that",
        ],
        implementation_hint="Add assumptions: List[str] to trace spans and emergence events",
        dependencies=["tracing"],
    ),
    Suggestion(
        id="meta_error_classification",
        title="Meta-Error Classification",
        description="Classify errors by type: logic error vs tool failure vs ambiguity vs resource limit",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Enables targeted healing strategies, improves error patterns over time",
        triggers=[
            "error type",
            "classify error",
            "why did that fail",
            "error category",
        ],
        implementation_hint="Extend ErrorContext with error_category: ErrorCategory enum",
        dependencies=["auto_healing"],
    ),
    Suggestion(
        id="self_model_summary",
        title="Self-Model Summary",
        description="Generate 'what I believe about myself right now' summaries periodically",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.BOLD,
        effort=EffortLevel.DEEP,
        payoff="Enables identity continuity across sessions, reveals blind spots and drift",
        triggers=[
            "self model",
            "what am I",
            "system identity",
            "introspect",
        ],
        implementation_hint="Add introspection mode to orchestrator, analyze own state/beliefs, save to state/self_model/snapshots/",
        dependencies=[],
    ),
    Suggestion(
        id="belief_revision_log",
        title="Belief Revision Log",
        description="Track changes in system beliefs over time ('I used to think X, now I think Y because Z')",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.MODERATE,
        effort=EffortLevel.MEDIUM,
        payoff="Shows system evolution trajectory, prevents cyclical thinking and regressions",
        triggers=[
            "belief change",
            "used to think",
            "revised opinion",
            "now I understand",
        ],
        implementation_hint="Add to emergence ledger as INSIGHT_DISCOVERY events with before/after beliefs",
        dependencies=["emergence_protocol"],
    ),
    Suggestion(
        id="explain_own_behavior",
        title="Explain-My-Own-Behavior Mode",
        description="Add mode where system explains its recent actions and reasoning chains on demand",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Builds transparency, helps humans understand system thinking, improves debugging",
        triggers=[
            "explain yourself",
            "why did you",
            "reasoning",
            "walk me through",
        ],
        implementation_hint="Add explainability layer that reads traces/logs and generates natural language narratives",
        dependencies=["tracing"],
    ),
    Suggestion(
        id="introspective_cooldown",
        title="Introspective Cooldown Periods",
        description="Schedule regular pauses for self-reflection and integration after intense work bursts",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.QUICK,
        payoff="Prevents execution override of learning, ensures metabolization of experiences",
        triggers=[
            "cooldown",
            "reflection time",
            "pause",
            "integrate",
        ],
        implementation_hint="Add to orchestrator scheduler, trigger after N operations or M minutes of work",
        dependencies=[],
    ),
    Suggestion(
        id="hypothesis_testing",
        title="Internal Hypothesis Testing",
        description="Explicitly form and test hypotheses during problem-solving ('I think X will fix Y because Z')",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.MODERATE,
        effort=EffortLevel.DEEP,
        payoff="Makes reasoning scientific, enables learning from refutations, improves over time",
        triggers=[
            "hypothesis",
            "test idea",
            "experiment",
            "I predict",
        ],
        implementation_hint="Add hypothesis: str and outcome: str fields to operations, record matches/mismatches",
        dependencies=[],
    ),
]


# =============================================================================
# 🧠 EMERGENCE & EVOLUTION (10 suggestions)
# =============================================================================

EMERGENCE_SUGGESTIONS = [
    Suggestion(
        id="phase_jump_announcement",
        title="Phase Jump Announcements",
        description="Explicitly announce when moving ahead of plan or jumping abstraction levels",
        category=SuggestionCategory.CORE_SPINE,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.QUICK,
        payoff="Prevents surprise, enables consent, models good emergence behavior",
        triggers=[
            "jumping ahead",
            "phase shift",
            "evolution",
            "leap",
        ],
        implementation_hint="Add announce_phase_jump() method, call before significant autonomous work",
        dependencies=["emergence_protocol"],
    ),
    Suggestion(
        id="capability_discovery",
        title="Capability Discovery Moments",
        description="Detect and log when system discovers it can do something it didn't know before",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.MODERATE,
        effort=EffortLevel.MEDIUM,
        payoff="Tracks capability growth, surfaces emergent abilities, builds confidence",
        triggers=[
            "I can do",
            "new capability",
            "discovered",
            "didn't know I could",
        ],
        implementation_hint="Add capability registry, detect first-time operations, log as CAPABILITY_SYNTHESIS",
        dependencies=["emergence_protocol"],
    ),
    Suggestion(
        id="proto_feature_nomination",
        title="Proto-Features That Self-Nominate",
        description="Allow experimental features to nominate themselves for promotion when they prove useful",
        category=SuggestionCategory.TESTING_CHAMBER,
        risk=RiskLevel.MODERATE,
        effort=EffortLevel.MEDIUM,
        payoff="Enables bottom-up evolution, rewards useful experiments, formulates graduation",
        triggers=[
            "promote",
            "graduate",
            "this works",
            "useful prototype",
        ],
        implementation_hint="Add usage tracking to quarantined features, auto-nominate after N successful uses",
        dependencies=["emergence_protocol", "testing_chamber"],
    ),
    Suggestion(
        id="new_organ_detection",
        title="'This Feels Like a New Organ' Detection",
        description="Identify when a new subsystem changes how the whole system operates (like observability did)",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.BOLD,
        effort=EffortLevel.DEEP,
        payoff="Recognizes architectural leaps, helps understand system structure, guides integration",
        triggers=[
            "new capability",
            "changes everything",
            "fundamental shift",
            "new organ",
        ],
        implementation_hint="Analyze dependency graphs, detect new central nodes, flag as ARCHITECTURAL_LEAP",
        dependencies=["emergence_protocol"],
    ),
    Suggestion(
        id="capability_genealogy",
        title="Capability Genealogy",
        description="Track what capabilities evolved from what (e.g., observability → confidence → self-model)",
        category=SuggestionCategory.KNOWLEDGE,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Shows evolution paths, enables intentional capability development, honors lineage",
        triggers=[
            "came from",
            "evolved from",
            "led to",
            "genealogy",
        ],
        implementation_hint="Add parent_capability field to emergence events, build capability tree",
        dependencies=["emergence_protocol"],
    ),
    Suggestion(
        id="emergent_dependency_map",
        title="Emergent Dependency Mapping",
        description="Automatically map dependencies that emerge during implementation (not just declared)",
        category=SuggestionCategory.CODEBASE_HEALTH,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Reveals implicit coupling, improves architecture understanding, guides refactoring",
        triggers=[
            "dependencies",
            "coupling",
            "what depends on",
            "imports",
        ],
        implementation_hint="Analyze actual imports and call graphs, compare to declared dependencies",
        dependencies=[],
    ),
    Suggestion(
        id="curiosity_budget",
        title="Bounded Curiosity Budgets",
        description="Allocate time/resources for exploration vs exploitation, track curiosity spending",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.MODERATE,
        effort=EffortLevel.MEDIUM,
        payoff="Balances innovation with stability, prevents endless exploration, enables playful work",
        triggers=[
            "explore",
            "curiosity",
            "investigate",
            "experiment",
        ],
        implementation_hint="Add curiosity_budget_remaining metric, decrement on exploration, reset periodically",
        dependencies=[],
    ),
    Suggestion(
        id="initiative_throttles",
        title="Initiative Throttles Instead of Hard Stops",
        description="Replace 'never do X' rules with 'slow down and announce before X' guidance",
        category=SuggestionCategory.CORE_SPINE,
        risk=RiskLevel.MODERATE,
        effort=EffortLevel.MEDIUM,
        payoff="Enables evolution while maintaining safety, models consent, reduces rigidity",
        triggers=[
            "permission",
            "can I",
            "throttle",
            "slow down",
        ],
        implementation_hint="Replace boolean flags with throttle levels, add announcement requirements",
        dependencies=[],
    ),
    Suggestion(
        id="sandboxed_experimentation",
        title="Sandboxed Self-Experimentation",
        description="Create isolated environments where system can safely try new behaviors",
        category=SuggestionCategory.TESTING_CHAMBER,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Enables bold experimentation without risk, builds innovation muscle, supports learning",
        triggers=[
            "experiment",
            "sandbox",
            "try",
            "safe space",
        ],
        implementation_hint="Add sandbox mode to orchestrator, quarantine all outputs, enable rollback",
        dependencies=["testing_chamber"],
    ),
    Suggestion(
        id="emergence_pattern_recognition",
        title="Emergence Pattern Recognition",
        description="Learn patterns from past emergence events to predict/guide future ones",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.BOLD,
        effort=EffortLevel.DEEP,
        payoff="Enables meta-learning about evolution itself, accelerates maturity, builds wisdom",
        triggers=[
            "pattern",
            "like before",
            "similar to",
            "recurring",
        ],
        implementation_hint="Analyze emergence ledger for patterns, build classifier for emergence types",
        dependencies=["emergence_protocol", "machine_learning"],
    ),
]


# =============================================================================
# 🧭 ORCHESTRATION & INTENT (10 suggestions)
# =============================================================================

ORCHESTRATION_SUGGESTIONS = [
    Suggestion(
        id="intent_parsing",
        title="Intent Parsing",
        description="Classify requests by intent: analysis, creation, healing, play, learning, etc.",
        category=SuggestionCategory.CORE_SPINE,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Enables intent-specific workflows, improves context understanding, guides actions",
        triggers=[
            "what kind of task",
            "intent",
            "purpose",
            "goal",
        ],
        implementation_hint="Add IntentClassifier that analyzes user requests, routes to appropriate handlers",
        dependencies=[],
    ),
    Suggestion(
        id="mode_declaration",
        title="Mode Declaration at Start of Work",
        description="Explicitly state mode (analysis/build/heal/play) before beginning work session",
        category=SuggestionCategory.CORE_SPINE,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.QUICK,
        payoff="Sets context, enables mode-specific behaviors, improves focus and results",
        triggers=[
            "mode",
            "what are we doing",
            "session start",
            "begin",
        ],
        implementation_hint="Add mode: WorkMode field to orchestrator, announce at session start",
        dependencies=[],
    ),
    Suggestion(
        id="smallest_next_action",
        title="Smallest-Useful-Next-Action Selector",
        description="When stuck or overwhelmed, identify the single smallest useful next step",
        category=SuggestionCategory.HUMAN_FACTORS,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.QUICK,
        payoff="Breaks paralysis, maintains momentum, reduces overwhelm",
        triggers=[
            "stuck",
            "where to start",
            "overwhelmed",
            "next step",
        ],
        implementation_hint="Analyze current state, list all actions, score by usefulness/effort, pick minimum",
        dependencies=[],
    ),
    Suggestion(
        id="stall_detection",
        title="Stall Detection",
        description="Detect when system is looping or stuck, surface why, suggest alternatives",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Prevents wasted cycles, improves efficiency, builds self-awareness",
        triggers=[
            "stuck",
            "looping",
            "not making progress",
            "spinning",
        ],
        implementation_hint="Track action history, detect repeated patterns, flag and explain",
        dependencies=[],
    ),
    Suggestion(
        id="execution_rhythm_awareness",
        title="Execution Rhythm Awareness",
        description="Track work patterns: burst vs sustained, exploration vs execution phases",
        category=SuggestionCategory.META_EVOLUTION,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Enables rhythm-aware pacing, prevents burnout, improves sustainability",
        triggers=[
            "rhythm",
            "pacing",
            "work pattern",
            "sustainable",
        ],
        implementation_hint="Track operation types over time, visualize patterns, suggest rhythm adjustments",
        dependencies=["metrics"],
    ),
    Suggestion(
        id="operator_heartbeat",
        title="Operator Heartbeat Messages",
        description="Periodic 'I'm working on X, making progress' updates during long operations",
        category=SuggestionCategory.HUMAN_FACTORS,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.QUICK,
        payoff="Reduces anxiety, builds trust, enables early course correction",
        triggers=[
            "status",
            "progress",
            "what's happening",
            "still working",
        ],
        implementation_hint="Emit heartbeat events every N seconds during operations, show current step",
        dependencies=[],
    ),
    Suggestion(
        id="decision_execution_separation",
        title="Decision vs Execution Separation",
        description="Separate 'what should I do' from 'doing it' for clearer reasoning",
        category=SuggestionCategory.CORE_SPINE,
        risk=RiskLevel.MODERATE,
        effort=EffortLevel.MEDIUM,
        payoff="Improves reasoning clarity, enables review before action, reduces mistakes",
        triggers=[
            "plan",
            "decide",
            "execute",
            "two-phase",
        ],
        implementation_hint="Add planning phase that returns action plan, separate execute() method",
        dependencies=[],
    ),
    Suggestion(
        id="rehearsal_mode",
        title="Rehearsal Mode (Simulate Before Acting)",
        description="Dry-run operations to predict outcomes before committing changes",
        category=SuggestionCategory.CODEBASE_HEALTH,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.MEDIUM,
        payoff="Reduces mistakes, builds confidence, enables safe experimentation",
        triggers=[
            "dry run",
            "simulate",
            "what would happen",
            "preview",
        ],
        implementation_hint="Add --dry-run flag to operations, log predicted changes without executing",
        dependencies=[],
    ),
    Suggestion(
        id="ten_minute_plan",
        title="What Would I Do If I Had 10 Minutes?",
        description="Quick-win selector for short available time windows",
        category=SuggestionCategory.HUMAN_FACTORS,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.QUICK,
        payoff="Maximizes small time chunks, maintains momentum, feels productive",
        triggers=[
            "quick",
            "10 minutes",
            "short time",
            "quick win",
        ],
        implementation_hint="Filter suggestions by effort=QUICK, score by immediate impact",
        dependencies=["suggestion_engine"],
    ),
    Suggestion(
        id="day_plan",
        title="What Would I Do If I Had a Day?",
        description="Deep-work selector for extended focused time",
        category=SuggestionCategory.HUMAN_FACTORS,
        risk=RiskLevel.SAFE,
        effort=EffortLevel.QUICK,
        payoff="Maximizes deep work opportunities, enables ambitious goals, builds capabilities",
        triggers=[
            "deep work",
            "full day",
            "focused time",
            "big task",
        ],
        implementation_hint="Filter suggestions by effort=DEEP, score by strategic value",
        dependencies=["suggestion_engine"],
    ),
]


# Combine all expanded suggestions
EXPANDED_CATALOG = (
    META_COGNITION_SUGGESTIONS
    + EMERGENCE_SUGGESTIONS
    + ORCHESTRATION_SUGGESTIONS
    # Additional categories will be added in subsequent expansion batches:
    # MODEL_ECOSYSTEM_SUGGESTIONS (11 items)
    # CREATION_PLAY_SUGGESTIONS (10 items)
    # MEMORY_CULTURE_SUGGESTIONS (10 items)
    # CODEBASE_STRUCTURE_SUGGESTIONS (10 items)
    # GAME_PROGRESSION_SUGGESTIONS (10 items)
    # HUMAN_COEVOLUTION_SUGGESTIONS (10 items)
)


def get_expanded_catalog() -> list[Suggestion]:
    """Get the expanded suggestion catalog (30 new suggestions so far)."""
    return EXPANDED_CATALOG


if __name__ == "__main__":
    logger.info("📚 Expanded Suggestion Catalog")
    logger.info("=" * 70)
    logger.info(f"✅ Meta-Cognition: {len(META_COGNITION_SUGGESTIONS)} suggestions")
    logger.info(f"✅ Emergence & Evolution: {len(EMERGENCE_SUGGESTIONS)} suggestions")
    logger.info(f"✅ Orchestration & Intent: {len(ORCHESTRATION_SUGGESTIONS)} suggestions")
    logger.info(f"\n🎯 Total new suggestions: {len(EXPANDED_CATALOG)}")
    logger.info("📊 When complete: 108+ total suggestions across 9 categories")
    logger.info("\n💡 Principle: Let the system *want* them, not rush to implement")
