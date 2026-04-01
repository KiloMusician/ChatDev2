#!/usr/bin/env python3
"""Integration Tests for Autonomous Workflows.

Tests the complete autonomous development infrastructure including:
- Multi-AI orchestration
- Quantum error handling
- Quest generation
- Agent ecosystem
- Adaptive timeouts
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestMultiAIOrchestrator:
    """Test Multi-AI Orchestrator functionality."""

    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        from src.orchestration.multi_ai_orchestrator import get_multi_ai_orchestrator

        orchestrator = get_multi_ai_orchestrator()
        assert orchestrator is not None
        assert hasattr(orchestrator, "systems")
        assert len(orchestrator.systems) == 5

    def test_health_check(self):
        """Test system health check."""
        from src.orchestration.multi_ai_orchestrator import get_multi_ai_orchestrator

        orchestrator = get_multi_ai_orchestrator()
        health = orchestrator.health_check()

        assert isinstance(health, dict)
        assert "ollama" in health
        assert "quantum_resolver" in health
        assert health["quantum_resolver"] is True  # Always active

    def test_request_routing(self):
        """Test intelligent request routing."""
        from src.orchestration.multi_ai_orchestrator import get_multi_ai_orchestrator

        orchestrator = get_multi_ai_orchestrator()

        # Test routing for different task types
        assert orchestrator.route_request("self_healing") == "quantum_resolver"
        assert orchestrator.route_request("quantum_analysis") == "quantum_resolver"

        # Code generation should route to available system
        code_gen_route = orchestrator.route_request("code_generation")
        assert code_gen_route in ["ollama", "chatdev", None]


class TestArchitectureWatcher:
    """Test Architecture Watcher functionality."""

    def test_watcher_initialization(self):
        """Test architecture watcher can be initialized."""
        from src.core.ArchitectureWatcher import get_architecture_watcher

        watcher = get_architecture_watcher()
        assert watcher is not None
        assert hasattr(watcher, "monitored_paths")

    def test_health_check(self):
        """Test architecture health check."""
        from src.core.ArchitectureWatcher import get_architecture_watcher

        watcher = get_architecture_watcher()
        health = watcher.health_check()

        assert isinstance(health, dict)
        assert "healthy" in health
        assert "issues" in health
        assert "stats" in health
        assert isinstance(health["stats"], dict)


class TestQuantumErrorBridge:
    """Test Quantum Error Bridge functionality."""

    @pytest.mark.asyncio
    async def test_bridge_initialization(self):
        """Test quantum error bridge can be initialized."""
        from src.integration.quantum_error_bridge import get_quantum_error_bridge

        bridge = get_quantum_error_bridge()
        assert bridge is not None
        assert hasattr(bridge, "quantum_resolver")
        assert hasattr(bridge, "pu_queue")

    @pytest.mark.asyncio
    async def test_error_handling_syntax_error(self):
        """Test handling of syntax errors."""
        from src.integration.quantum_error_bridge import get_quantum_error_bridge

        bridge = get_quantum_error_bridge()
        error = SyntaxError("missing colon")
        context = {"task": "test", "file": "test.py"}

        result = await bridge.handle_error(error, context, auto_fix=True)

        assert "error_type" in result
        assert result["error_type"] == "SyntaxError"
        assert "quantum_state" in result
        assert "resolution_attempted" in result

    @pytest.mark.asyncio
    async def test_error_handling_import_error(self):
        """Test handling of import errors."""
        from src.integration.quantum_error_bridge import get_quantum_error_bridge

        bridge = get_quantum_error_bridge()
        error = ImportError("No module named 'test'")
        context = {"task": "test", "file": "test.py"}

        result = await bridge.handle_error(error, context, auto_fix=True)

        assert result["error_type"] == "ImportError"
        assert "quantum_state" in result


class TestAutonomousQuestGenerator:
    """Test Autonomous Quest Generator functionality."""

    def test_generator_initialization(self):
        """Test quest generator can be initialized."""
        from src.automation.autonomous_quest_generator import AutonomousQuestGenerator

        generator = AutonomousQuestGenerator()
        assert generator is not None
        assert hasattr(generator, "ecosystem")
        assert hasattr(generator, "pu_queue")
        assert hasattr(generator, "timeout_manager")

    @pytest.mark.asyncio
    async def test_process_pending_pus(self):
        """Test processing of pending PUs."""
        from src.automation.autonomous_quest_generator import AutonomousQuestGenerator

        generator = AutonomousQuestGenerator()
        result = await generator.process_pending_pus()

        assert isinstance(result, dict)
        assert "processed" in result
        assert "created" in result
        assert "failed" in result

    @pytest.mark.asyncio
    async def test_generate_advanced_ai_capability_quests(self, monkeypatch):
        """Missing advanced-AI capabilities should become deduplicated quests."""
        from types import SimpleNamespace

        from src.automation.autonomous_quest_generator import AutonomousQuestGenerator

        class FakeQuest:
            def __init__(self, title, status="pending"):
                self.title = title
                self.status = status

        class FakeEcosystem:
            def __init__(self):
                self.quest_engine = SimpleNamespace(
                    quests={
                        "existing": FakeQuest("Implement Graph Learning capability", status="pending")
                    }
                )
                self.created = []

            def create_quest_for_agent(self, **kwargs):
                self.created.append(kwargs)
                return {"success": True, "quest": {"id": f"quest-{len(self.created)}"}}

        generator = AutonomousQuestGenerator()
        generator.ecosystem = FakeEcosystem()
        monkeypatch.setattr(
            generator,
            "_collect_advanced_ai_readiness",
            lambda: {
                "status": "partial",
                "capabilities": {
                    "causal_inference": {"status": "missing"},
                    "federated_learning": {"status": "missing"},
                    "graph_learning": {"status": "missing"},
                    "ensemble_consensus": {"status": "ready"},
                },
            },
        )

        result = await generator.generate_advanced_ai_capability_quests()

        assert result["created"] == 2
        assert result["skipped"] == 1
        assert result["failed"] == 0
        created_titles = [item["title"] for item in generator.ecosystem.created]
        assert "Implement Causal Inference capability" in created_titles
        assert "Implement Federated Learning capability" in created_titles


class TestUnifiedAgentEcosystem:
    """Test Unified Agent Ecosystem functionality."""

    def test_ecosystem_initialization(self):
        """Test ecosystem can be initialized."""
        from src.agents.unified_agent_ecosystem import get_ecosystem

        ecosystem = get_ecosystem()
        assert ecosystem is not None
        assert hasattr(ecosystem, "agent_hub")
        assert hasattr(ecosystem, "quest_engine")
        assert hasattr(ecosystem, "temple")

    def test_agent_hub_populated(self):
        """Test agent hub has agents."""
        from src.agents.unified_agent_ecosystem import get_ecosystem

        ecosystem = get_ecosystem()
        assert len(ecosystem.agent_hub.agents) > 0

    def test_quest_summary(self):
        """Test getting quest summary."""
        from src.agents.unified_agent_ecosystem import get_ecosystem

        ecosystem = get_ecosystem()
        summary = ecosystem.get_party_quest_summary()

        assert isinstance(summary, dict)
        assert "total_quests" in summary
        assert "quests_by_status" in summary


class TestAdaptiveTimeoutManager:
    """Test Adaptive Timeout Manager functionality."""

    def test_manager_initialization(self):
        """Test timeout manager can be initialized."""
        from src.agents.adaptive_timeout_manager import get_timeout_manager

        manager = get_timeout_manager()
        assert manager is not None
        assert hasattr(manager, "enable_breathing")
        assert hasattr(manager, "breathing_factor")

    def test_get_timeout(self):
        """Test timeout calculation."""
        from src.agents.adaptive_timeout_manager import get_timeout_manager

        manager = get_timeout_manager()
        timeout = manager.get_timeout("ollama", "code_generation", "medium")

        assert isinstance(timeout, (int, float))
        assert timeout > 0

    def test_breathing_adaptation(self):
        """Test breathing factor updates."""
        from src.agents.adaptive_timeout_manager import get_timeout_manager

        manager = get_timeout_manager()
        initial = manager.breathing_factor

        # Test acceleration (high success + backlog)
        manager.update_breathing_factor(success_rate=0.9, backlog_level=0.6)
        assert manager.breathing_factor < initial  # Should accelerate

        # Reset and test deceleration (low success)
        manager.breathing_factor = 1.0
        manager.update_breathing_factor(success_rate=0.2)
        assert manager.breathing_factor > 1.0  # Should decelerate


class TestCompleteWorkflow:
    """Test complete autonomous workflow integration."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow from error to resolution."""
        from src.automation.autonomous_quest_generator import AutonomousQuestGenerator
        from src.integration.quantum_error_bridge import get_quantum_error_bridge

        # Phase 1: Error detection and handling
        bridge = get_quantum_error_bridge()
        error = ValueError("Test error for workflow")
        context = {"task": "workflow_test", "file": "test.py"}

        result = await bridge.handle_error(error, context, auto_fix=False)

        # Should create PU since auto_fix is disabled
        assert result["resolution_attempted"] is False

        # Phase 2: Quest generation
        generator = AutonomousQuestGenerator()
        pu_result = await generator.process_pending_pus()

        # Verify processing occurred
        assert isinstance(pu_result, dict)

    def test_system_integration(self):
        """Test all systems work together."""
        from src.agents.adaptive_timeout_manager import get_timeout_manager
        from src.agents.unified_agent_ecosystem import get_ecosystem
        from src.core.ArchitectureWatcher import get_architecture_watcher
        from src.integration.quantum_error_bridge import get_quantum_error_bridge
        from src.orchestration.multi_ai_orchestrator import get_multi_ai_orchestrator

        # Verify all systems can be initialized together
        orchestrator = get_multi_ai_orchestrator()
        watcher = get_architecture_watcher()
        get_quantum_error_bridge()  # Verify initialization only
        ecosystem = get_ecosystem()
        timeout_mgr = get_timeout_manager()

        # Verify basic functionality
        assert orchestrator.health_check() is not None
        assert watcher.health_check() is not None
        assert len(ecosystem.agent_hub.agents) > 0
        assert timeout_mgr.breathing_factor > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
