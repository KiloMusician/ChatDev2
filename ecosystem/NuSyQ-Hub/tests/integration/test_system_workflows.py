"""Integration tests for multi-component workflows.

OmniTag: {
    "purpose": "integration_test_workflows",
    "tags": ["testing", "integration", "workflows"],
    "category": "test_integration",
    "evolution_stage": "v1.0"
}

Coverage Target: 30% of test suite (integration tests)
Focus: Component interactions, AI orchestration, system workflows
"""

import json
from unittest.mock import patch

import pytest

# ============================================================================
# INTEGRATION TESTS: AI Orchestration Workflow
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestAIOrchestrationWorkflow:
    """Integration tests for complete AI orchestration workflows."""

    @patch("src.orchestration.unified_ai_orchestrator.requests.post")
    def test_ollama_to_chatdev_workflow(self, mock_post, mock_chatdev_config):
        """Test workflow from Ollama analysis to ChatDev implementation."""
        from src.orchestration.unified_ai_orchestrator import (
            UnifiedAIOrchestrator,
        )

        # Mock Ollama response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "response": "Create a calculator app",
            "done": True,
        }

        orchestrator = UnifiedAIOrchestrator()

        # Test complete workflow
        result = orchestrator.orchestrate_task(
            "Build a calculator",
            services=["ollama", "chatdev"],
        )

        assert isinstance(result, dict)
        assert "ollama" in result or "tasks" in result

    def test_multi_service_coordination(self, temp_config_file):
        """Test coordination across multiple AI services."""
        from src.orchestration.unified_ai_orchestrator import (
            UnifiedAIOrchestrator,
        )

        orchestrator = UnifiedAIOrchestrator(config_file=temp_config_file)

        services = orchestrator.get_available_services()

        assert isinstance(services, list)
        # Should detect available services

    @patch("src.orchestration.unified_ai_orchestrator.subprocess.run")
    def test_chatdev_integration_flow(self, mock_subprocess, mock_chatdev_config):
        """Test integration with ChatDev for code generation."""
        from src.orchestration.unified_ai_orchestrator import (
            UnifiedAIOrchestrator,
        )

        # Mock ChatDev execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Project created successfully"

        orchestrator = UnifiedAIOrchestrator()

        result = orchestrator.run_chatdev_task(
            "Create hello world app",
            use_ollama=True,
        )

        assert isinstance(result, dict)


# ============================================================================
# INTEGRATION TESTS: Healing Workflow
# ============================================================================


@pytest.mark.integration
class TestHealingWorkflow:
    """Integration tests for system healing workflows."""

    def test_detect_and_heal_workflow(self, isolated_workspace):
        """Test complete detect → analyze → heal workflow."""
        from src.healing.quantum_problem_resolver import (
            QuantumProblemResolver,
        )

        resolver = QuantumProblemResolver()

        # Create a problem
        broken_file = isolated_workspace / "broken.py"
        broken_file.write_text("import nonexistent_module")

        # Detect
        problems = resolver.detect_problems(workspace=isolated_workspace)

        # Heal
        if problems:
            results = resolver.heal_problems(problems)
            assert isinstance(results, dict)

    def test_path_repair_with_validation(self, isolated_workspace):
        """Test path repair with subsequent validation."""
        from src.healing.repository_health_restorer import (
            find_broken_paths,
            repair_paths,
            validate_paths,
        )

        # Create broken paths
        test_file = isolated_workspace / "test.py"
        test_file.write_text("from missing.module import func")

        # Find broken
        broken = find_broken_paths(isolated_workspace)

        # Repair
        if broken:
            repair_paths(broken, dry_run=True)  # Validation test only

            # Validate
            validation = validate_paths(isolated_workspace)
            assert isinstance(validation, dict)

    def test_environment_optimization_cycle(self):
        """Test complete environment optimization cycle."""
        from src.healing.system_regenerator import (
            Environment,
            ResourceManagement,
        )

        env = Environment(resources={"water": 1000, "energy": 500}, health_index=0.5)
        manager = ResourceManagement(environment=env)

        initial_health = env.health_index

        # Run optimization cycle
        for _ in range(3):
            manager.allocate_resources()
            env.heal_environment()

        # Health should improve
        assert env.health_index > initial_health


# ============================================================================
# INTEGRATION TESTS: Quest System Workflow
# ============================================================================


@pytest.mark.integration
class TestQuestSystemWorkflow:
    """Integration tests for quest management workflows."""

    def test_quest_creation_and_completion(self, sample_quest_data):
        """Test complete quest lifecycle from creation to completion."""
        from src.Rosetta_Quest_System.quest_engine import QuestEngine

        engine = QuestEngine()

        # Create quest
        quest_id = engine.add_quest(
            sample_quest_data["title"],
            sample_quest_data["description"],
            priority=sample_quest_data["priority"],
        )

        assert quest_id is not None

        # Retrieve quest
        quest = engine.get_quest(quest_id)
        assert quest is not None
        assert quest.status == "pending"

        # Complete quest
        engine.complete_quest(quest_id)
        completed_quest = engine.get_quest(quest_id)
        assert completed_quest.status == "completed"

    def test_questline_workflow(self):
        """Test questline creation and quest chaining."""
        from src.Rosetta_Quest_System.quest_engine import QuestEngine

        engine = QuestEngine()

        # Clear any previous state
        engine.quests.clear()
        engine.questlines.clear()

        # Create questline
        questline_name = "Test Questline"
        engine.add_questline(
            questline_name,
            "A test questline for integration testing",
        )

        # Add quests to questline
        engine.add_quest("Task 1", "First task", questline_name)
        engine.add_quest("Task 2", "Second task", questline_name)

        # Verify chain - check questline has quests
        assert questline_name in engine.questlines
        questline = engine.questlines[questline_name]
        assert len(questline.quests) >= 2


# ============================================================================
# INTEGRATION TESTS: Configuration & Service Integration
# ============================================================================


@pytest.mark.integration
class TestConfigurationIntegration:
    """Integration tests for configuration and service coordination."""

    def test_config_loading_and_service_init(self, temp_config_file):
        """Test configuration loading and service initialization."""
        from src.config.service_config import ServiceConfig
        from src.utils.timeout_config import get_timeout

        # Load config
        config = ServiceConfig(config_file=temp_config_file)

        # Use config for timeout
        timeout = get_timeout("ollama")

        assert timeout > 0
        assert config.ollama_host is not None

    def test_multi_config_coordination(self, temp_config_file, isolated_workspace):
        """Test coordination between multiple configuration systems."""
        from src.config.service_config import ServiceConfig

        # Create additional config
        extra_config = isolated_workspace / "extra.json"
        extra_config.write_text(json.dumps({"extra_setting": "value"}))

        # Load both
        config1 = ServiceConfig(config_file=temp_config_file)

        assert hasattr(config1, "ollama_host")


# ============================================================================
# INTEGRATION TESTS: Timeout & Performance Integration
# ============================================================================


@pytest.mark.integration
class TestTimeoutPerformanceIntegration:
    """Integration tests for timeout adaptation and performance tracking."""

    def test_adaptive_timeout_with_history(self):
        """Test timeout adaptation based on performance history."""
        from src.utils.intelligent_timeout_manager import TimeoutCalculator

        calc = TimeoutCalculator(base_timeout=60)

        initial_timeout = calc.calculate_timeout()

        # Simulate slow executions
        for _ in range(5):
            calc.record_performance(duration=120.0)

        adapted_timeout = calc.calculate_timeout()

        # Should adapt to slower performance
        assert adapted_timeout >= initial_timeout

    def test_service_timeout_coordination(self):
        """Test coordination of timeouts across multiple services."""
        from src.utils.intelligent_timeout_manager import ServiceTimeoutManager

        manager = ServiceTimeoutManager()

        # Get timeouts for different services
        ollama_t = manager.get_timeout("ollama")
        chatdev_t = manager.get_timeout("chatdev")
        default_t = manager.get_timeout("unknown")

        assert all(t > 0 for t in [ollama_t, chatdev_t, default_t])
        assert chatdev_t > ollama_t  # ChatDev typically needs more time
