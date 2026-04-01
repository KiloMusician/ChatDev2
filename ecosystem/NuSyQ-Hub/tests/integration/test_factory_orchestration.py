"""
Factory-Orchestration Integration Tests

Validates factory routing through agent task router and orchestrator.
Tests conversational triggers, provider selection, artifact registry integration.

NOTE: Factory integration work is incomplete.These tests are temporarily skipped pending
consolidation campaign that integrates factory modules with agent_task_router.
See: docs/migrations/FACTORY_INTEGRATION_ROADMAP.md
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.orchestration.unified_ai_orchestrator import OrchestrationTask
from src.tools.agent_task_router import AgentTaskRouter, create_project_with_factory


@pytest.mark.skip(reason="Factory integration incomplete - awaiting consolidation campaign")
class TestFactoryOrchestratorIntegration:
    """Integration tests for factory + orchestrator."""

    @pytest.fixture
    def temp_registry(self):
        """Create temporary registry for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_factory_routing_via_task_router(self, temp_registry):
        """Test routing factory task through agent task router."""
        router = AgentTaskRouter()

        context = {
            "project_name": "TestGame",
            "template": "default_game",
            "ai_provider": "auto",
        }

        # Mock ProjectFactory.create()
        with patch("src.tools.agent_task_router.ProjectFactory") as mock_factory:
            mock_result = MagicMock()
            mock_result.name = "TestGame"
            mock_result.type = "game"
            mock_result.version = "1.0.0"
            mock_result.output_path = Path("/tmp/test_game")
            mock_result.ai_provider = "chatdev"
            mock_result.model_used = "qwen2.5-coder:7b"
            mock_result.token_cost = 0.0245
            mock_result.chatdev_warehouse_path = Path("/warehouse/test")

            mock_factory_inst = MagicMock()
            mock_factory_inst.create.return_value = mock_result
            mock_factory.return_value = mock_factory_inst

            # Route task to factory
            result = await router.route_task(
                task_type="create_project",
                description="Create a test game",
                context=context,
                target_system="factory",
            )

            assert result["status"] == "success"
            assert result["system"] == "factory"
            assert result["output"]["name"] == "TestGame"
            assert result["output"]["ai_provider"] == "chatdev"

    @pytest.mark.asyncio
    async def test_create_project_convenience_function(self):
        """Test convenience function for project creation."""
        with patch("src.tools.agent_task_router.ProjectFactory") as mock_factory:
            mock_result = MagicMock()
            mock_result.name = "MyCLI"
            mock_result.type = "cli"
            mock_result.version = "1.0.0"
            mock_result.output_path = Path("/tmp/my_cli")
            mock_result.ai_provider = "ollama"
            mock_result.model_used = "qwen2.5-coder:7b"
            mock_result.token_cost = 0.0
            mock_result.chatdev_warehouse_path = None

            mock_factory_inst = MagicMock()
            mock_factory_inst.create.return_value = mock_result
            mock_factory.return_value = mock_factory_inst

            result = await create_project_with_factory(
                name="MyCLI",
                template="default_cli",
                description="Test CLI tool",
                ai_provider="ollama",
            )

            assert result["status"] == "success"
            assert result["output"]["type"] == "cli"

    @pytest.mark.asyncio
    async def test_factory_error_handling_missing_template(self):
        """Test factory error handling for missing templates."""
        router = AgentTaskRouter()

        context = {
            "project_name": "BadGame",
            "template": "nonexistent_template",
        }

        with patch("src.tools.agent_task_router.ProjectFactory") as mock_factory:
            mock_factory_inst = MagicMock()
            mock_factory_inst.create.side_effect = FileNotFoundError("Template not found")
            mock_factory.return_value = mock_factory_inst

            result = await router.route_task(
                task_type="create_project",
                description="Create project",
                context=context,
                target_system="factory",
            )

            assert result["status"] == "failed"
            assert "Template not found" in result["error"]

    @pytest.mark.asyncio
    async def test_factory_ai_provider_selection_routing(self):
        """Test factory routes to correct AI provider."""
        router = AgentTaskRouter()

        # Test ChatDev selection for complex game
        with patch("src.factories.AIOrchestrator.select_provider") as mock_select:
            mock_select.return_value = "chatdev"

            context = {
                "project_name": "ComplexGame",
                "template": "default_game",
            }

            with patch("src.tools.agent_task_router.ProjectFactory") as mock_factory:
                mock_result = MagicMock()
                mock_result.name = "ComplexGame"
                mock_result.type = "game"
                mock_result.version = "1.0.0"
                mock_result.output_path = Path("/tmp/complex_game")
                mock_result.ai_provider = "chatdev"
                mock_result.model_used = "qwen2.5-coder:14b"
                mock_result.token_cost = 0.0500
                mock_result.chatdev_warehouse_path = None

                mock_factory_inst = MagicMock()
                mock_factory_inst.create.return_value = mock_result
                mock_factory.return_value = mock_factory_inst

                result = await router.route_task(
                    "create_project",
                    "Create complex game",
                    context,
                    "factory",
                )

                assert result["output"]["ai_provider"] == "chatdev"

    @pytest.mark.asyncio
    async def test_factory_metadata_tracking(self):
        """Test factory metadata (costs, provider, model) are tracked."""
        router = AgentTaskRouter()

        with patch("src.tools.agent_task_router.ProjectFactory") as mock_factory:
            mock_result = MagicMock()
            mock_result.name = "TrackingTest"
            mock_result.type = "library"
            mock_result.version = "1.0.1"
            mock_result.output_path = Path("/tmp/tracking_test")
            mock_result.ai_provider = "claude"
            mock_result.model_used = "claude-3-opus"
            mock_result.token_cost = 0.0750
            mock_result.chatdev_warehouse_path = Path("/wh/tracking")

            mock_factory_inst = MagicMock()
            mock_factory_inst.create.return_value = mock_result
            mock_factory.return_value = mock_factory_inst

            result = await router.route_task(
                "create_project",
                "Create library",
                {"project_name": "TrackingTest", "template": "default_library"},
                "factory",
            )

            output = result["output"]
            assert output["model_used"] == "claude-3-opus"
            assert output["token_cost"] == 0.0750
            assert output["warehouse_path"] == "/wh/tracking"

    def test_factory_task_type_validation(self):
        """Test factory only accepts create_project task type."""
        router = AgentTaskRouter()

        # Non-create_project task should fail
        task = OrchestrationTask(
            task_id="test_task",
            task_type="generate",  # Wrong type for factory
            content="Generate something",
        )

        # Synchronous test of handler
        result = asyncio.run(router._route_to_factory(task))

        assert result["status"] == "failed"
        assert "create_project" in result["error"]

    @pytest.mark.asyncio
    async def test_factory_unavailable_graceful_fallback(self):
        """Test graceful error when factory modules unavailable."""
        router = AgentTaskRouter()

        context = {
            "project_name": "FallbackTest",
            "template": "default_game",
        }

        with patch.dict("sys.modules", {"src.factories": None}):
            # Mock import failure
            with patch(
                "src.tools.agent_task_router.ProjectFactory",
                side_effect=ImportError("Factory not found"),
            ):
                result = await router.route_task(
                    "create_project",
                    "Create project",
                    context,
                    "factory",
                )

                assert result["status"] == "failed"
                assert "unavailable" in result["error"].lower()

    def test_factory_in_system_handlers(self):
        """Test factory handler is registered in system handlers."""
        router = AgentTaskRouter()
        assert "factory" in router._system_handlers
        assert callable(router._system_handlers["factory"])


class TestFactoryConversationalPatterns:
    """Test conversational patterns that trigger factory."""

    @pytest.mark.asyncio
    async def test_generate_game_pattern(self):
        """Test 'generate game' conversational pattern."""
        router = AgentTaskRouter()

        with patch("src.tools.agent_task_router.ProjectFactory") as mock_factory:
            mock_result = MagicMock()
            mock_result.name = "MyGame"
            mock_result.type = "game"
            mock_result.version = "1.0.0"
            mock_result.output_path = Path("/tmp/my_game")
            mock_result.ai_provider = "chatdev"
            mock_result.model_used = "qwen2.5-coder:7b"
            mock_result.token_cost = 0.0245
            mock_result.chatdev_warehouse_path = None

            mock_factory_inst = MagicMock()
            mock_factory_inst.create.return_value = mock_result
            mock_factory.return_value = mock_factory_inst

            # Simulate user message: "Generate a Godot game called MyGame"
            result = await router.route_task(
                "create_project",
                "Generate a Godot game called MyGame",
                {
                    "project_name": "MyGame",
                    "template": "default_game",
                },
                "factory",
            )

            assert result["status"] == "success"
            assert result["output"]["name"] == "MyGame"

    @pytest.mark.asyncio
    async def test_create_cli_pattern(self):
        """Test 'create CLI' conversational pattern."""
        router = AgentTaskRouter()

        with patch("src.tools.agent_task_router.ProjectFactory") as mock_factory:
            mock_result = MagicMock()
            mock_result.name = "MyCLI"
            mock_result.type = "cli"
            mock_result.version = "1.0.0"
            mock_result.output_path = Path("/tmp/my_cli")
            mock_result.ai_provider = "ollama"
            mock_result.model_used = "qwen2.5-coder:7b"
            mock_result.token_cost = 0.0
            mock_result.chatdev_warehouse_path = None

            mock_factory_inst = MagicMock()
            mock_factory_inst.create.return_value = mock_result
            mock_factory.return_value = mock_factory_inst

            result = await router.route_task(
                "create_project",
                "Create a CLI tool for file processing",
                {
                    "project_name": "MyCLI",
                    "template": "default_cli",
                },
                "factory",
            )

            assert result["status"] == "success"
            assert result["output"]["type"] == "cli"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
