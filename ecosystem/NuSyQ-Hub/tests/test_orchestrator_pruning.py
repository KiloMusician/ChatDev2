import pytest
from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator


def test_orchestrator_generate_prune_plan():
    orchestrator = UnifiedAIOrchestrator()
    plan_path = orchestrator.generate_prune_plan(
        age_days=365, size_threshold_bytes=200_000, min_duplicate_group=2
    )
    # The plan may be None if the pruner isn't available, skip in that case
    if plan_path is None:
        pytest.skip("Pruner module unavailable or index not found")
    assert plan_path
    assert orchestrator.context_bridge.get("pruning") is not None
    assert "candidate_count" in orchestrator.context_bridge.get("pruning")
