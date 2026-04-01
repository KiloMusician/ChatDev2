"""src/orchestration - Multi-LLM and Workflow Orchestration.

THE canonical orchestration layer for NuSyQ-Hub (Sprint 3 consolidation).

Module Hierarchy (Single Authority Pattern):
============================================

TIER 1: CORE ORCHESTRATORS (Primary Authority)
----------------------------------------------
- unified_ai_orchestrator.py   - AI system router (Claude, Ollama, ChatDev)
- agent_orchestration_hub.py   - Task dispatcher with consciousness awareness
- agent_registry.py            - Agent capability discovery & lifecycle

TIER 2: TASK MANAGEMENT
-----------------------
- background_task_orchestrator.py - Async task queue for LLM operations
- agent_task_queue.py            - Task assignment and tracking
- feedback_loop_engine.py        - Error → Quest → Task pipeline

TIER 3: CHATDEV SUBSYSTEM
-------------------------
- chatdev_development_orchestrator.py - Phase-based multi-agent orchestration
- chatdev_testing_chamber.py          - Validation quarantine
- chamber_promotion_manager.py        - Testing → Production promotion
- chatdev_autonomous_router.py        - Task routing (to be merged)

TIER 4: HEALING SUBSYSTEM
-------------------------
- unified_autonomous_healing_pipeline.py - Detect → Fix → Validate cycle
- auto_healing.py                        - Error triggers
- healing_cycle_scheduler.py             - Scheduled healing (to be merged)

TIER 5: QUEST & GAME
--------------------
- autonomous_quest_orchestrator.py - Quest execution
- culture_ship_quest_bridge.py     - Strategy → Quest conversion

TIER 6: ECOSYSTEM COORDINATION
------------------------------
- ecosystem_activator.py           - Master system activation
- workspace_coordinator.py         - Multi-repo coordination
- culture_ship_strategic_advisor.py - Strategic planning

TIER 7: BRIDGES (Consolidated)
------------------------------
- bridges/orchestration_bridges.py - Unified BridgeRegistry
- bridges/__init__.py              - Bridge exports

TIER 8: SUPPORT INFRASTRUCTURE
------------------------------
- suggestion_engine.py       - Autonomous suggestions
- ai_capabilities_enhancer.py - Domain mapping
- ai_council_voting.py       - Multi-agent consensus
- generator_integration.py   - Factory integration

Usage:
    # Primary entry points
    from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator
    from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator
    from src.orchestration.bridges import BridgeRegistry

    # Task submission
    orchestrator = UnifiedAIOrchestrator()
    result = await orchestrator.dispatch_task(task)

    # Background execution
    bg = BackgroundTaskOrchestrator()
    task = bg.submit_task("generate", prompt, ai_system="ollama")
"""

# Core exports for convenience
from src.orchestration.background_task_orchestrator import \
    BackgroundTaskOrchestrator
from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator

__all__ = [
    "BackgroundTaskOrchestrator",
    "DependencyResolver",
    "GitNexus",
    "UnifiedAIOrchestrator",
    "fetch_aggregated_insights",
]


def __getattr__(name: str):
    if name == "DependencyResolver":
        from src.orchestration.dependency_resolver import DependencyResolver

        return DependencyResolver
    if name == "fetch_aggregated_insights":
        from src.orchestration.insights_adapter import \
            fetch_aggregated_insights

        return fetch_aggregated_insights
    if name == "GitNexus":
        from src.orchestration.gitnexus import GitNexus

        return GitNexus
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
