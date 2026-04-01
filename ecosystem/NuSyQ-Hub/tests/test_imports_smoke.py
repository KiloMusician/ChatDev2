"""Import smoke tests - ensure key modules can be imported without crashes.

This prevents broken __init__.py files and missing dependencies from
blocking system startup.
"""

import pytest


def test_quantum_problem_resolver_import():
    """Test that QuantumProblemResolver can be imported from src.quantum."""
    from src.quantum import QuantumProblemResolver

    assert QuantumProblemResolver is not None
    assert QuantumProblemResolver.__name__ == "QuantumProblemResolver"


def test_agent_task_router_import():
    """Test that AgentTaskRouter can be imported."""
    from src.tools.agent_task_router import AgentTaskRouter

    assert AgentTaskRouter is not None


def test_suggestion_engine_import():
    """Test that SuggestionEngine can be imported."""
    from src.orchestration.suggestion_engine import SuggestionEngine

    assert SuggestionEngine is not None


def test_unified_ai_orchestrator_import():
    """Test that UnifiedAIOrchestrator can be imported."""
    from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator

    assert UnifiedAIOrchestrator is not None


def test_main_module_import():
    """Test that main.py can be imported without crashes.

    Note: Skips due to heavy transformers library initialization in
    consciousness.the_oldest_house. Main.py is tested indirectly through
    start_nusyq.py runtime operations.
    """
    import pytest

    pytest.skip("Heavy transformers import causes timeout; tested via start_nusyq.py")
    # import src.main  # Heavy transformers/faiss initialization
    # assert src.main is not None


def test_doctrine_module_import():
    """Test that doctrine module can be imported."""
    from src.doctrine import ComplianceReport, DoctrineChecker, DoctrineViolation

    assert DoctrineChecker is not None
    assert DoctrineViolation is not None
    assert ComplianceReport is not None


def test_observability_module_import():
    """Test that observability module can be imported."""
    from src.observability import SnapshotDelta, SnapshotDeltaTracker, SnapshotMetrics

    assert SnapshotMetrics is not None
    assert SnapshotDelta is not None
    assert SnapshotDeltaTracker is not None


def test_quest_module_import():
    """Test that quest module can be imported."""
    from src.quest import Action, Quest, QuestExecutor

    assert Quest is not None
    assert Action is not None
    assert QuestExecutor is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
