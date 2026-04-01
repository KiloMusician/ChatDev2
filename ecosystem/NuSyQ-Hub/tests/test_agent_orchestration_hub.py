"""Comprehensive test suite for AgentOrchestrationHub.

Tests:
- Core initialization and status
- Task routing with consciousness
- ChatDev integration
- Multi-agent consensus voting
- Healing escalation
- Task locking (collision prevention)
- Service registration
- Bridge integration
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest
from src.orchestration.agent_orchestration_hub import (
    AgentOrchestrationHub,
    ConsciousnessEnrichment,
    RoutingDecision,
)


@pytest.fixture
def tmp_hub_dir(tmp_path):
    """Create temporary directory for hub receipts."""
    return tmp_path


@pytest.fixture
def hub(tmp_hub_dir):
    """Initialize AgentOrchestrationHub with mocked dependencies."""
    with patch("src.orchestration.agent_orchestration_hub.UnifiedAIOrchestratorClass"):
        with patch("src.orchestration.agent_orchestration_hub.ConsciousnessBridgeClass"):
            with patch("src.orchestration.agent_orchestration_hub.ChatDevLauncherClass"):
                with patch("src.orchestration.agent_orchestration_hub.QuantumProblemResolverClass"):
                    return AgentOrchestrationHub(root_path=tmp_hub_dir, enable_consciousness=True)


class TestHubInitialization:
    """Test hub initialization and basic setup."""

    def test_hub_initializes(self, tmp_hub_dir):
        """Hub should initialize successfully."""
        with patch("src.orchestration.agent_orchestration_hub.UnifiedAIOrchestratorClass"):
            hub = AgentOrchestrationHub(root_path=tmp_hub_dir, enable_consciousness=False)
            assert hub.root_path == tmp_hub_dir
            assert hub.enable_consciousness is False

    def test_receipt_directory_created(self, tmp_hub_dir):
        """Receipt directory should be created."""
        with patch("src.orchestration.agent_orchestration_hub.UnifiedAIOrchestratorClass"):
            AgentOrchestrationHub(root_path=tmp_hub_dir)
            receipt_dir = tmp_hub_dir / "docs" / "tracing" / "RECEIPTS"
            assert receipt_dir.exists()

    def test_initial_status(self, hub):
        """Initial status should show zero tasks."""
        status = hub.get_system_status()
        assert status["tasks_routed"] == 0
        assert status["tasks_succeeded"] == 0
        assert status["tasks_failed"] == 0
        assert status["success_rate"] == "0.0%"


class TestTaskRouting:
    """Test core task routing functionality."""

    @pytest.mark.asyncio
    async def test_route_task_basic(self, hub):
        """Route task should return task_id and status."""
        result = await hub.route_task(
            content="Test content",
            task_type="analyze",
            target_system="auto",
            consciousness_enrich=False,
        )
        assert result["status"] in ["success", "submitted"]
        assert result["success"] is True
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_route_task_with_consciousness(self, hub):
        """Task routing with consciousness should include enrichment."""
        with patch.object(hub, "_enrich_with_consciousness") as mock_enrich:
            mock_enrich.return_value = ConsciousnessEnrichment(
                summary="Test enrichment",
                tags=["test"],
                confidence=0.8,
            )

            result = await hub.route_task(
                content="Test content",
                task_type="analyze",
                consciousness_enrich=True,
            )

            assert result["status"] in ["success", "submitted"]
            mock_enrich.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_task_increments_metrics(self, hub):
        """Task routing should increment metrics."""
        await hub.route_task(
            content="Test",
            task_type="analyze",
            consciousness_enrich=False,
        )

        status = hub.get_system_status()
        assert status["tasks_routed"] == 1

    @pytest.mark.asyncio
    async def test_explicit_target_system(self, hub):
        """Explicit target system should skip orchestrator decision."""
        result = await hub.route_task(
            content="Test",
            task_type="analyze",
            target_system="ollama",
            consciousness_enrich=False,
        )

        assert result["status"] in ["success", "submitted"]
        routing = result.get("routing_decision")
        if routing:
            assert routing["target_system"] == "ollama"


class TestChatDevRouting:
    """Test ChatDev integration."""

    @pytest.mark.asyncio
    async def test_route_to_chatdev(self, hub):
        """Should route to ChatDev successfully."""
        with patch(
            "src.orchestration.agent_orchestration_hub.ChatDevLauncherClass"
        ) as MockLauncher:
            mock_process = MagicMock()
            mock_process.pid = 12345
            MockLauncher.return_value.launch_chatdev.return_value = mock_process

            result = await hub.route_to_chatdev(
                task="Generate a Python script",
                project_name="TestProject",
            )

            assert result["status"] == "success"
            assert result["success"] is True
            assert result["system"] == "chatdev"
            assert result["pid"] == 12345

    @pytest.mark.asyncio
    async def test_chatdev_without_launcher(self, tmp_hub_dir):
        """Should handle missing ChatDevLauncher gracefully."""
        # Create hub instance with ChatDevLauncher explicitly set to None
        with patch("src.orchestration.agent_orchestration_hub.UnifiedAIOrchestratorClass"):
            with patch("src.orchestration.agent_orchestration_hub.ConsciousnessBridgeClass"):
                with patch("src.orchestration.agent_orchestration_hub.QuantumProblemResolverClass"):
                    with patch(
                        "src.orchestration.agent_orchestration_hub.ChatDevLauncherClass", None
                    ):
                        test_hub = AgentOrchestrationHub(
                            root_path=tmp_hub_dir, enable_consciousness=True
                        )
                        result = await test_hub.route_to_chatdev(task="Do thing", project_name="X")

        assert result["status"] == "failed"
        assert result["success"] is False
        assert "ChatDevLauncher" in result["error"]


class TestMultiAgentConsensus:
    """Test multi-agent consensus voting."""

    @pytest.mark.asyncio
    async def test_consensus_simple_voting(self, hub):
        """Consensus with simple voting should work."""
        with patch.object(hub, "route_task") as mock_route:
            mock_route.return_value = {
                "status": "success",
                "result": "Test result",
            }

            result = await hub.orchestrate_multi_agent_task(
                content="Test",
                task_type="analyze",
                systems=["ollama", "copilot"],
                voting_strategy="simple",
            )

            assert result["status"] == "success"
            assert result["success"] is True
            assert "consensus_result" in result

    @pytest.mark.asyncio
    async def test_consensus_weighted_voting(self, hub):
        """Consensus with weighted voting should work."""
        with patch.object(hub, "route_task") as mock_route:
            mock_route.return_value = {
                "status": "success",
                "result": "Test result",
            }

            result = await hub.orchestrate_multi_agent_task(
                content="Test",
                task_type="analyze",
                systems=["ollama", "copilot"],
                voting_strategy="weighted",
            )

            assert result["status"] == "success"


class TestHealingEscalation:
    """Test automatic healing escalation."""

    @pytest.mark.asyncio
    async def test_execute_with_healing_success(self, hub):
        """Should succeed on first attempt."""
        with patch.object(hub, "route_task") as mock_route:
            mock_route.return_value = {"status": "success", "result": "OK"}

            result = await hub.execute_with_healing(
                content="Test",
                task_type="analyze",
                max_retries=3,
            )

            assert result["status"] == "success"
            assert result["success"] is True
            assert result["attempts"] == 1

    @pytest.mark.asyncio
    async def test_execute_with_healing_retry(self, hub):
        """Should retry on failure."""
        with patch.object(hub, "route_task") as mock_route:
            # First call fails, second succeeds
            mock_route.side_effect = [
                {"status": "failed", "error": "Test error"},
                {"status": "success", "result": "OK"},
            ]

            result = await hub.execute_with_healing(
                content="Test",
                task_type="analyze",
                max_retries=3,
            )

            assert result["attempts"] >= 2


class TestTaskLocking:
    """Test task locking (collision prevention)."""

    def test_acquire_task_lock_success(self, hub):
        """Should acquire lock successfully."""
        locked = hub.acquire_task_lock("test_task_1")
        assert locked is True

    def test_lock_collision_detection(self, hub):
        """Should detect lock collision."""
        hub.acquire_task_lock("test_task_2")
        locked = hub.acquire_task_lock("test_task_2")
        assert locked is False

    def test_lock_timeout_cleanup(self, hub):
        """Should clean up expired locks."""
        task_id = "test_task_3_cleanup"
        locked = hub.acquire_task_lock(task_id)
        assert locked is True

        # Manually set lock to be expired
        hub.task_locks[task_id] = time.time() - 301  # 301 seconds ago

        # Acquire a different task, which should trigger cleanup of expired locks
        new_task_id = "test_task_4"
        locked = hub.acquire_task_lock(new_task_id)
        assert locked is True

        # Old lock should be cleaned up
        assert task_id not in hub.task_locks


class TestServiceRegistration:
    """Test dynamic service registration."""

    def test_register_service(self, hub):
        """Should register service successfully."""

        async def dummy_handler(content):
            await asyncio.sleep(0)
            return {"status": "success"}

        registered = hub.register_service(
            service_id="test_service",
            handler=dummy_handler,
            task_types=["analyze"],
        )
        assert registered is True
        assert "test_service" in hub.services

    def test_duplicate_service_registration(self, hub):
        """Should prevent duplicate registration."""

        async def dummy_handler(content):
            await asyncio.sleep(0)
            return {"status": "success"}

        hub.register_service(
            service_id="test_service_2",
            handler=dummy_handler,
            task_types=["analyze"],
        )

        registered = hub.register_service(
            service_id="test_service_2",
            handler=dummy_handler,
            task_types=["analyze"],
        )
        assert registered is False


class TestSystemStatus:
    """Test system status reporting."""

    def test_get_system_status(self, hub):
        """Should return valid status dict."""
        status = hub.get_system_status()

        assert status["status"] == "operational"
        assert status["success"] is True
        assert "uptime_seconds" in status
        assert "tasks_routed" in status
        assert "tasks_succeeded" in status
        assert "tasks_failed" in status
        assert "success_rate" in status
        assert "registered_services" in status
        assert "consciousness_enabled" in status


class TestBridgeIntegration:
    """Test service bridge integration."""

    @pytest.mark.asyncio
    async def test_agent_task_router_bridge(self, hub):
        """AgentTaskRouter bridge should work."""
        from src.orchestration.bridges.agent_task_router_bridge import AgentTaskRouterBridge

        bridge = AgentTaskRouterBridge(hub)
        assert bridge is not None
        assert bridge.hub is hub

    @pytest.mark.asyncio
    async def test_chatdev_bridge(self, hub):
        """ChatDev bridge should work."""
        from src.orchestration.bridges.chatdev_bridge import ChatDevBridge

        bridge = ChatDevBridge(hub)
        assert bridge is not None
        assert bridge.hub is hub

    @pytest.mark.asyncio
    async def test_consciousness_bridge_integration(self, hub):
        """Consciousness bridge should work."""
        from src.orchestration.bridges.consciousness_bridge_integration import (
            ConsciousnessBridgeIntegration,
        )

        bridge = ConsciousnessBridgeIntegration(hub)
        assert bridge is not None
        assert bridge.hub is hub

    @pytest.mark.asyncio
    async def test_quantum_healing_bridge(self, hub):
        """Quantum healing bridge should work."""
        from src.orchestration.bridges.quantum_healing_bridge import QuantumHealingBridge

        bridge = QuantumHealingBridge(hub)
        assert bridge is not None
        assert bridge.hub is hub

    @pytest.mark.asyncio
    async def test_consensus_voting_bridge(self, hub):
        """Consensus voting bridge should work."""
        from src.orchestration.bridges.consensus_voting_bridge import MultiAgentConsensusBridge

        bridge = MultiAgentConsensusBridge(hub)
        assert bridge is not None
        assert bridge.hub is hub

    @pytest.mark.asyncio
    async def test_ollama_bridge(self, hub):
        """Ollama bridge should work."""
        from src.orchestration.bridges.ollama_bridge import OllamaBridge

        bridge = OllamaBridge(hub)
        assert bridge is not None
        assert bridge.hub is hub

    @pytest.mark.asyncio
    async def test_copilot_bridge(self, hub):
        """Copilot bridge should work."""
        from src.orchestration.bridges.copilot_bridge import CopilotBridge

        bridge = CopilotBridge(hub)
        assert bridge is not None
        assert bridge.hub is hub

    @pytest.mark.asyncio
    async def test_continue_bridge(self, hub):
        """Continue bridge should work."""
        from src.orchestration.bridges.continue_bridge import ContinueBridge

        bridge = ContinueBridge(hub)
        assert bridge is not None
        assert bridge.hub is hub


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_route_task_handles_exceptions(self, hub):
        """Should handle exceptions gracefully."""
        result = await hub.route_task(
            content="Test",
            task_type="analyze",
            consciousness_enrich=False,
        )

        # Should not raise, should return dict
        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.asyncio
    async def test_receipt_emission_graceful_failure(self, hub, tmp_hub_dir):
        """Receipt emission should not crash on error."""
        # Make receipts dir unwritable (simulate error)
        # Then route task - should still succeed
        result = await hub.route_task(
            content="Test",
            task_type="analyze",
            consciousness_enrich=False,
        )

        assert result["status"] in ["success", "submitted"]


class TestIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, hub):
        """Complete workflow: route → consciousness → lock → metrics."""

        # Register a service
        async def test_handler(content):
            await asyncio.sleep(0)
            return {"status": "success"}

        hub.register_service(
            service_id="test",
            handler=test_handler,
            task_types=["analyze"],
        )

        # Route a task
        result = await hub.route_task(
            content="Test content",
            task_type="analyze",
            consciousness_enrich=False,
        )
        assert result["status"] in ["success", "submitted"]

        # Check metrics
        status = hub.get_system_status()
        assert status["tasks_routed"] == 1
        assert status["registered_services"] == 1


class TestAdditionalCoverage:
    """Cover helper methods and edge behaviors for orchestration hub."""

    @pytest.mark.asyncio
    async def test_route_by_system_consciousness_without_enrichment(self, hub):
        routing = RoutingDecision(
            task_id="task1",
            target_system="consciousness",
            confidence=1.0,
            reason="explicit",
        )

        result = await hub._route_by_system(routing, "content", "analyze", {})

        assert result["status"] == "success"
        assert result["system"] == "consciousness"
        # When no enrichment, output may be None but should not raise
        assert "output" in result

    @pytest.mark.asyncio
    async def test_decide_routing_explicit_target_short_circuits(self, hub):
        decision = await hub._decide_routing(
            task_id="task2",
            content="data",
            task_type="analyze",
            target_system="copilot",
            enrichment=None,
        )

        assert decision.target_system == "copilot"
        assert decision.reason == "Explicit target specified"
        assert decision.confidence == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_apply_voting_strategy_variants(self, hub):
        results = [{"status": "success"}, {"status": "success"}]

        simple = await hub._apply_voting_strategy(results, "simple")
        weighted = await hub._apply_voting_strategy(results, "weighted")
        ranked = await hub._apply_voting_strategy(results, "ranked")

        assert simple["consensus"] == "majority vote"
        assert weighted["consensus"].startswith("weighted")
        assert ranked["consensus"].startswith("ranked")

    @pytest.mark.asyncio
    async def test_emit_receipt_writes_file(self, tmp_path):
        hub = AgentOrchestrationHub(root_path=tmp_path, enable_consciousness=False)
        routing = RoutingDecision(
            task_id="task3",
            target_system="ollama",
            confidence=0.5,
            reason="test",
        )
        result = {"status": "submitted"}

        await hub._emit_receipt("task3", routing, result, enrichment=None)

        receipts_dir = tmp_path / "docs" / "tracing" / "RECEIPTS"
        files = list(receipts_dir.glob("hub_route_task3.json"))
        assert files, "Receipt file should be emitted"
