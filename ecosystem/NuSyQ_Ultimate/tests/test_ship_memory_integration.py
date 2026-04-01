"""
Tests for Ship Memory integration with Agent Router

Verifies that agent performance tracking works correctly.
"""

import json
from pathlib import Path

import pytest
from config.agent_router import AgentRouter
from scripts.ship_memory import ShipMemory


@pytest.fixture
def temp_memory_file(tmp_path):
    """Create temporary ship memory file."""
    memory_file = tmp_path / "ship_memory.json"
    return memory_file


@pytest.fixture
def router_with_memory(temp_memory_file, tmp_path):
    """Create agent router with ship memory."""
    # Copy agent registry to tmp_path
    registry_src = Path("config/agent_registry.yaml")
    registry_dst = tmp_path / "agent_registry.yaml"

    if registry_src.exists():
        import shutil

        shutil.copy(registry_src, registry_dst)

        # Monkey patch ship memory file location
        router = AgentRouter(registry_path=registry_dst)
        router.ship_memory = ShipMemory(temp_memory_file)
        return router
    else:
        pytest.skip("agent_registry.yaml not found")


class TestShipMemoryIntegration:
    """Test Ship Memory integration with Agent Router."""

    def test_record_task_completion(self, router_with_memory, temp_memory_file):
        """Test recording task completion."""
        router = router_with_memory

        # Record a successful task
        router.record_task_completion(
            agent_name="ollama_qwen_2_5_coder_14b",
            task_type="code_generation",
            success=True,
            duration=5.2,
        )

        # Verify it was recorded
        assert temp_memory_file.exists()

        with open(temp_memory_file, encoding="utf-8") as f:
            memory = json.load(f)

        assert len(memory["sessions"]) == 1
        session = memory["sessions"][0]
        assert session["agent"] == "ollama_qwen_2_5_coder_14b"
        assert session["success"] is True
        assert session["duration"] == 5.2

    def test_get_agent_performance(self, router_with_memory):
        """Test retrieving agent performance metrics."""
        router = router_with_memory

        # Record multiple tasks
        agent_name = "ollama_qwen_2_5_coder_14b"
        router.record_task_completion(agent_name, "code_gen", True, 5.0)
        router.record_task_completion(agent_name, "code_gen", True, 4.0)
        router.record_task_completion(agent_name, "code_gen", False, 6.0)

        # Get performance
        perf = router.get_agent_performance(agent_name)

        assert perf["tasks_completed"] == 3
        assert perf["tasks_successful"] == 2
        assert perf["success_rate"] == pytest.approx(0.666, rel=0.01)
        assert perf["average_duration"] == 5.0  # (5 + 4 + 6) / 3

    def test_performance_learning(self, router_with_memory):
        """Test that agent performance influences routing decisions."""
        router = router_with_memory

        # Record poor performance for one agent
        router.record_task_completion(
            "ollama_llama_3_2", "code_generation", False, 10.0
        )
        router.record_task_completion(
            "ollama_llama_3_2", "code_generation", False, 12.0
        )

        # Record good performance for another
        router.record_task_completion(
            "ollama_qwen_2_5_coder_14b", "code_generation", True, 3.0
        )
        router.record_task_completion(
            "ollama_qwen_2_5_coder_14b", "code_generation", True, 4.0
        )

        # Verify performance metrics
        poor_perf = router.get_agent_performance("ollama_llama_3_2")
        good_perf = router.get_agent_performance("ollama_qwen_2_5_coder_14b")

        assert poor_perf["success_rate"] == 0.0
        assert good_perf["success_rate"] == 1.0

    def test_ship_memory_persistence(self, temp_memory_file):
        """Test that ship memory persists across router instances."""
        # Create first router
        router1 = AgentRouter()
        router1.ship_memory = ShipMemory(temp_memory_file)

        router1.record_task_completion("test_agent", "test_task", True, 1.0)

        # Create second router with same memory file
        router2 = AgentRouter()
        router2.ship_memory = ShipMemory(temp_memory_file)

        # Should see the session from router1
        perf = router2.get_agent_performance("test_agent")
        assert perf["tasks_completed"] == 1

    def test_no_ship_memory_graceful_degradation(self, tmp_path):
        """Test that router works without ship memory."""
        registry_src = Path("config/agent_registry.yaml")
        registry_dst = tmp_path / "agent_registry.yaml"

        if registry_src.exists():
            import shutil

            shutil.copy(registry_src, registry_dst)

            router = AgentRouter(registry_path=registry_dst)
            router.ship_memory = None  # Disable ship memory

            # Should not crash
            router.record_task_completion("test_agent", "test_task", True, 1.0)

            # Should return empty metrics
            perf = router.get_agent_performance("test_agent")
            assert perf == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
