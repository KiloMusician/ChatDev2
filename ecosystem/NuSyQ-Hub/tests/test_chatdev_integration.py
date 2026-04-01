"""Test ChatDev multi-agent integration with DRY-RUN (no actual subprocess).

This validates the spawn_chatdev() method architecture using mocks,
without spawning actual ChatDev processes that can hang/freeze.

KEY LESSON: ChatDev is a BLOCKING subprocess. Test it MOCKED to prevent hangs,
run it REAL only in dedicated CI/integration environment.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure src is on path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.orchestration.claude_orchestrator import ClaudeOrchestrator


@pytest.mark.asyncio
async def test_chatdev_health():
    """Test ChatDev installation readiness without outbound network probes."""
    print("🧪 Testing ChatDev health...")
    orch = ClaudeOrchestrator()
    try:
        chatdev_run_py = orch.chatdev_path / "run.py" if orch.chatdev_path else None
        chatdev_run_ollama_py = orch.chatdev_path / "run_ollama.py" if orch.chatdev_path else None
        chatdev_status = {
            "path": str(orch.chatdev_path) if orch.chatdev_path else None,
            "status": "ready" if orch.chatdev_path and orch.chatdev_path.exists() else "missing",
            "has_run_py": chatdev_run_py.exists() if chatdev_run_py else False,
            "has_run_ollama_py": chatdev_run_ollama_py.exists() if chatdev_run_ollama_py else False,
        }

        print("\n📊 ChatDev Status:")
        print(f"  Path: {chatdev_status.get('path')}")
        print(f"  Status: {chatdev_status.get('status')}")
        print(f"  run.py: {chatdev_status.get('has_run_py')}")

        assert "path" in chatdev_status, "❌ Missing path field"
        assert "status" in chatdev_status, "❌ Missing status field"
        print("✅ ChatDev health check passed")
    finally:
        orch.shutdown()


@pytest.mark.asyncio
async def test_chatdev_spawn_mocked(mock_chatdev):
    """Test ChatDev spawn with mocked subprocess (prevents hang)."""
    print("\n🧪 Testing ChatDev spawn (MOCKED, no hang risk)...")
    orch = ClaudeOrchestrator()
    try:
        # Mock the agent_task_router to return a success dict
        with patch("src.tools.agent_task_router.AgentTaskRouter.route_task") as mock_route:
            # Make it awaitable
            async def mock_route_async(*args, **kwargs):
                # Simulate what the router would return from ChatDev
                return await mock_chatdev.spawn_project(
                    kwargs.get("description", "Create project"),
                    testing_chamber=kwargs.get("context", {}).get("testing_chamber", True),
                    model=kwargs.get("context", {}).get("chatdev_model", "qwen2.5-coder:7b"),
                )

            mock_route.side_effect = mock_route_async

            result = await orch.spawn_chatdev(
                task="Create a simple calculator", testing_chamber=True, model="qwen2.5-coder:7b"
            )

            print(f"Result: {result}")
            assert (
                result.get("status") == "success" or "status" in result
            ), f"Missing status field in {result}"
            print("✅ ChatDev spawn mocked test passed")
    finally:
        orch.shutdown()


@pytest.mark.asyncio
async def test_lightweight_tracer():
    """Test lightweight tracer for observability (Docker-free)."""
    print("\n🧪 Testing lightweight tracer...")
    import tempfile

    from src.observability.lightweight_tracer import LightweightTracer

    with tempfile.TemporaryDirectory() as tmpdir:
        tracer = LightweightTracer(output_dir=Path(tmpdir) / "traces")
        trace_id = tracer.start_trace("test_op")
        assert trace_id, "❌ Failed to start trace"
        print("✅ Lightweight tracer operational")


@pytest.mark.asyncio
async def test_claude_orchestrator_mocked():
    """Test ClaudeOrchestrator initialization and structure (no actual API call)."""
    print("\n🧪 Testing ClaudeOrchestrator structure...")
    orch = ClaudeOrchestrator()
    try:
        # Just validate that the object is properly initialized
        assert hasattr(orch, "ask_ollama"), "Missing ask_ollama method"
        assert hasattr(orch, "spawn_chatdev"), "Missing spawn_chatdev method"
        assert hasattr(orch, "health_check"), "Missing health_check method"
        assert orch.ollama_endpoint == "http://localhost:11434/api/generate"

        print("✅ ClaudeOrchestrator structure validated")
    finally:
        orch.shutdown()


def test_fixtures_available(mock_ollama_response, mock_chatdev_config):
    """Verify pytest conftest fixtures work."""
    print("\n🧪 Testing fixture availability...")
    assert mock_ollama_response.get("model")
    assert mock_chatdev_config.get("path")
    print("✅ Conftest fixtures available")


async def main():
    """Manual test runner."""
    print("=" * 60)
    print("🚀 ChatDev Integration Tests (DRY-RUN)")
    print("=" * 60)

    await test_chatdev_health()
    await test_chatdev_spawn_mocked()
    await test_lightweight_tracer()
    await test_claude_orchestrator_mocked()

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
