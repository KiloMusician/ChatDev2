import shutil

import pytest

from src.orchestration.unified_ai_orchestrator import OrchestrationTask
from src.tools.agent_task_router import AgentTaskRouter


@pytest.mark.asyncio
async def test_codex_fallback_to_ollama_on_rate_limit(monkeypatch):
    """When Codex hits rate limits, router should fallback to Ollama (auto mode)."""

    router = AgentTaskRouter()

    # Pretend codex exists on PATH
    monkeypatch.setattr(shutil, "which", lambda x: "/usr/bin/codex")

    # Make Codex CLI return a rate-limit-like error message
    async def fake_run_cli(cmd, prompt, timeout_seconds):
        return 1, "Error: Rate limit exceeded", ""

    monkeypatch.setattr(router, "_run_cli_command", fake_run_cli)

    # Ensure fallback uses Ollama (simulate a successful Ollama result)
    async def fake_ollama(task):
        return {"status": "success", "system": "ollama", "task_id": task.task_id, "output": "ollama"}

    monkeypatch.setattr(router, "_route_to_ollama", fake_ollama)

    task = OrchestrationTask(task_id="test", task_type="analyze", content="Hello")

    result = await router._route_to_codex(task)

    assert result["system"] == "ollama"
    assert result.get("output") == "ollama"
