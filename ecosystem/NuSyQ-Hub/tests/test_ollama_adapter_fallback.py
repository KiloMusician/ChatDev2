import sys

import pytest


@pytest.mark.asyncio
async def test_ollama_adapter_fallback(monkeypatch):
    """Ensure AgentTaskRouter falls back to OllamaAdapter when integrator import fails."""
    # Remove the integrator module so it can't be imported
    integrator_mod = "src.ai.ollama_chatdev_integrator"
    monkeypatch.setitem(sys.modules, integrator_mod, None)
    # Also remove sub-modules that might exist
    for key in list(sys.modules.keys()):
        if key.startswith(integrator_mod):
            monkeypatch.setitem(sys.modules, key, None)

    # Patch OllamaAdapter.query to return a simple string
    from src.integration.ollama_adapter import OllamaAdapter

    monkeypatch.setattr(OllamaAdapter, "query", lambda self, prompt, model: "fallback-output")

    from src.orchestration.unified_ai_orchestrator import OrchestrationTask, TaskPriority
    from src.tools.agent_task_router import AgentTaskRouter

    router = AgentTaskRouter()

    task = OrchestrationTask(
        task_id="t-fallback-1",
        task_type="analyze",
        content="Please analyze this code",
        priority=TaskPriority.NORMAL,
        context={},
    )

    result = await router._route_to_ollama(task)

    assert result["system"] == "ollama"
    assert result["status"] == "success"
    # Adapter returns string normalized to {'output': 'fallback-output'}
    assert isinstance(result["output"], dict)
    assert result["output"].get("output") == "fallback-output"
