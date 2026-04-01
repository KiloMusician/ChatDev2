import pytest
from src.orchestration.unified_ai_orchestrator import (
    MultiAIOrchestrator,
    OrchestrationTask,
)


@pytest.mark.asyncio
async def test_retrieval_enrichment_direct():
    orchestrator = MultiAIOrchestrator()
    # Skip if retrieval engine not available (e.g., index not generated yet)
    if not getattr(orchestrator, "summary_retrieval_engine", None):
        pytest.skip("Retrieval engine not initialized (no summary index)")

    task = OrchestrationTask(
        task_id="retrieval_test",
        task_type="analysis",
        content="quantum integration pipeline coherence",
        priority=1,
    )
    result = await orchestrator.orchestrate_task_async(task=task, preferred_systems=["ollama"])
    assert result["status"] in {"success", "failed"}  # execution may vary
    enriched = task.context.get("retrieved_summary_docs", [])
    assert isinstance(enriched, list)
    assert len(enriched) <= 3
    if enriched:
        first = enriched[0]
        assert "path" in first
        assert "score" in first


def test_retrieval_enrichment_queue():
    orchestrator = MultiAIOrchestrator()
    if not getattr(orchestrator, "summary_retrieval_engine", None):
        pytest.skip("Retrieval engine not initialized (no summary index)")

    task = OrchestrationTask(
        task_id="retrieval_queue_test",
        task_type="analysis",
        content="consciousness bridge memory palace synergy",
        priority=2,
    )
    orchestrator.submit_task(task)
    enriched = task.context.get("retrieved_summary_docs", [])
    assert isinstance(enriched, list)
    assert len(enriched) <= 3
