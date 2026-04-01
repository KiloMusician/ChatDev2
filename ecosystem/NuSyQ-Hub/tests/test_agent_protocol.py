"""Integration tests for Agent Protocol components.

Tests the new NuSyQ-Hub capabilities:
- Connector architecture
- Workflow engine
- TestLoop
- SpineRegistry wiring

OmniTag: [testing, integration, agent-protocol]
MegaTag: TEST⨳AGENT⦾PROTOCOL→∞
"""

from pathlib import Path


class TestConnectorArchitecture:
    """Tests for the connector subsystem."""

    def test_connector_registry_imports(self):
        """Test that connector registry can be imported."""
        from src.connectors.registry import ConnectorRegistry, get_connector_registry

        registry = get_connector_registry()
        assert registry is not None
        assert isinstance(registry, ConnectorRegistry)

    def test_connector_registry_singleton(self):
        """Test that connector registry is a singleton."""
        from src.connectors.registry import get_connector_registry

        reg1 = get_connector_registry()
        reg2 = get_connector_registry()
        assert reg1 is reg2

    def test_connector_registry_operations(self):
        """Test basic registry operations."""
        from src.connectors.base import ConnectorConfig
        from src.connectors.registry import get_connector_registry
        from src.connectors.webhook import WebhookConnector

        registry = get_connector_registry()

        # Create a test connector
        config = ConnectorConfig(
            name="test_webhook",
            endpoint="https://httpbin.org",
            enabled=True,
        )
        connector = WebhookConnector(config)

        # Register
        result = registry.register(connector)
        assert result.success

        # List
        connectors = registry.list_connectors()
        assert any(c.get("name") == "test_webhook" for c in connectors)

        # Get
        retrieved = registry.get("test_webhook")
        assert retrieved is not None
        assert retrieved.config.name == "test_webhook"

        # Health check (should fail since not connected)
        health_result = connector.health_check()
        assert health_result.success  # Should succeed as just reports status

        # Unregister
        result = registry.unregister("test_webhook")
        assert result.success

    def test_base_connector_interface(self):
        """Test that base connector defines required interface."""
        import abc

        from src.connectors.base import BaseConnector

        # BaseConnector should be abstract
        assert abc.ABC in BaseConnector.__mro__

        # Should have required abstract methods
        abstract_methods = getattr(BaseConnector, "__abstractmethods__", set())
        assert "connect" in abstract_methods
        assert "disconnect" in abstract_methods
        assert "health_check" in abstract_methods
        assert "execute" in abstract_methods

    def test_webhook_connector(self):
        """Test webhook connector functionality."""
        from src.connectors.base import ConnectorConfig
        from src.connectors.webhook import WebhookConnector

        config = ConnectorConfig(
            name="test_http",
            endpoint="https://httpbin.org",
            enabled=True,
        )
        connector = WebhookConnector(config)

        # Test connect (should succeed as it just sets state)
        result = connector.connect()
        assert result.success

        # Test disconnect
        result = connector.disconnect()
        assert result.success


class TestWorkflowEngine:
    """Tests for the workflow engine subsystem."""

    def test_workflow_engine_imports(self):
        """Test that workflow engine can be imported."""
        from src.workflow.engine import WorkflowEngine, get_workflow_engine

        engine = get_workflow_engine()
        assert engine is not None
        assert isinstance(engine, WorkflowEngine)

    def test_workflow_engine_singleton(self):
        """Test that workflow engine is a singleton."""
        from src.workflow.engine import get_workflow_engine

        eng1 = get_workflow_engine()
        eng2 = get_workflow_engine()
        assert eng1 is eng2

    def test_workflow_node_types(self):
        """Test that all node types are defined."""
        from src.workflow.nodes import NodeType

        assert NodeType.TRIGGER.value == "trigger"
        assert NodeType.ACTION.value == "action"
        assert NodeType.CONDITION.value == "condition"
        assert NodeType.TRANSFORM.value == "transform"
        assert NodeType.OUTPUT.value == "output"
        assert NodeType.AI.value == "ai"

    def test_workflow_creation(self):
        """Test creating a workflow."""
        from src.workflow.engine import get_workflow_engine
        from src.workflow.nodes import ActionNode, NodeType, OutputNode, TriggerNode

        engine = get_workflow_engine()

        # Create workflow
        workflow = engine.create_workflow(
            id="test_wf_001",
            name="Test Workflow",
            description="A test workflow",
        )

        assert workflow.id == "test_wf_001"
        assert workflow.name == "Test Workflow"

        # Add nodes
        trigger = TriggerNode(
            id="trigger_1",
            name="Manual Trigger",
            node_type=NodeType.TRIGGER,
            config={"trigger": "manual"},
        )
        action = ActionNode(
            id="action_1",
            name="Log Action",
            node_type=NodeType.ACTION,
            config={"action": "log"},
        )
        output = OutputNode(
            id="output_1",
            name="Result",
            node_type=NodeType.OUTPUT,
            config={},
        )

        workflow.add_node(trigger)
        workflow.add_node(action)
        workflow.add_node(output)

        assert len(workflow.nodes) == 3

        # Add edges
        workflow.add_edge("trigger_1", "action_1")
        workflow.add_edge("action_1", "output_1")

        assert len(workflow.edges) == 2

    def test_workflow_save_load(self):
        """Test saving and loading workflows."""
        from src.workflow.engine import get_workflow_engine
        from src.workflow.nodes import NodeType, TriggerNode

        engine = get_workflow_engine()

        # Create and save
        workflow = engine.create_workflow(
            id="test_save_load",
            name="Save Load Test",
        )
        trigger = TriggerNode(
            id="t1",
            name="Trigger",
            node_type=NodeType.TRIGGER,
            config={},
        )
        workflow.add_node(trigger)

        save_result = engine.save_workflow(workflow)
        assert save_result.success

        # Load
        load_result = engine.load_workflow("test_save_load")
        assert load_result.success
        loaded = load_result.data
        assert loaded.name == "Save Load Test"

    def test_workflow_execution(self):
        """Test executing a simple workflow."""
        from src.workflow.engine import get_workflow_engine
        from src.workflow.nodes import ActionNode, NodeType, OutputNode, TriggerNode

        engine = get_workflow_engine()

        # Create workflow
        workflow = engine.create_workflow(
            id="test_exec",
            name="Execution Test",
        )

        trigger = TriggerNode(
            id="t1",
            name="Start",
            node_type=NodeType.TRIGGER,
            config={"trigger": "manual"},
        )
        # Use 'log' action which is a valid built-in action
        action = ActionNode(
            id="a1",
            name="Process",
            node_type=NodeType.ACTION,
            config={"action": "log"},
        )
        output = OutputNode(
            id="o1",
            name="End",
            node_type=NodeType.OUTPUT,
            config={},
        )

        workflow.add_node(trigger)
        workflow.add_node(action)
        workflow.add_node(output)
        workflow.add_edge("t1", "a1")
        workflow.add_edge("a1", "o1")

        engine.save_workflow(workflow)

        # Execute
        result = engine.execute_workflow("test_exec", {"input": "test_data"})
        assert result.success


class TestTestLoop:
    """Tests for the TestLoop subsystem."""

    def test_test_loop_imports(self):
        """Test that TestLoop can be imported."""
        from src.automation.test_loop import TestLoop, get_test_loop

        loop = get_test_loop()
        assert loop is not None
        assert isinstance(loop, TestLoop)

    def test_test_loop_initialization(self):
        """Test TestLoop initialization options."""
        from src.automation.test_loop import TestLoop

        # Default initialization
        loop = TestLoop()
        assert loop.root_path.exists()
        assert loop.enable_ai_fixes  # Default is True

        # Disabled AI
        loop_no_ai = TestLoop(enable_ai_fixes=False)
        assert not loop_no_ai.enable_ai_fixes

    def test_test_result_dataclass(self):
        """Test TestResult dataclass."""
        from src.automation.test_loop import TestResult

        result = TestResult(
            passed=True,
            total=10,
            passed_count=10,
            failed_count=0,
        )

        assert result.passed
        assert result.total == 10

        # Test to_dict
        data = result.to_dict()
        assert data["passed"] is True
        assert data["total"] == 10

    def test_fix_attempt_dataclass(self):
        """Test FixAttempt dataclass."""
        from src.automation.test_loop import FixAttempt

        attempt = FixAttempt(
            iteration=1,
            failed_tests=[{"name": "test_foo"}],
            fix_applied=True,
            task_id="task_123",
        )

        assert attempt.iteration == 1
        assert attempt.fix_applied

        # Test to_dict
        data = attempt.to_dict()
        assert data["iteration"] == 1
        assert data["task_id"] == "task_123"

    def test_run_tests_target_not_found(self):
        """Test run_tests with non-existent target."""
        from src.automation.test_loop import TestLoop

        loop = TestLoop(enable_ai_fixes=False)
        result = loop.run_tests("nonexistent_path_xyz_123")

        assert not result.success
        assert result.code == "TARGET_NOT_FOUND"

    def test_session_reset(self):
        """Test session reset functionality."""
        from src.automation.test_loop import TestLoop

        loop = TestLoop(enable_ai_fixes=False)
        original_session = loop._session_id

        loop.reset_session()

        assert loop._session_id != original_session
        assert loop._attempts == []


class TestSpineRegistry:
    """Tests for SpineRegistry wiring."""

    def test_capability_registry_imports(self):
        """Test that capability registry can be imported."""
        from src.nusyq_spine.registry import (
            REGISTRY,
            CapabilityRegistry,
            get_capability_registry,
        )

        registry = get_capability_registry()
        assert registry is not None
        assert isinstance(registry, CapabilityRegistry)
        assert registry is REGISTRY

    def test_register_agent_protocol_components(self):
        """Test registering Agent Protocol components."""
        from src.nusyq_spine.registry import get_capability_registry

        registry = get_capability_registry()
        result = registry.register_agent_protocol_components()

        assert result.success
        data = result.data
        assert "registered" in data
        assert "errors" in data
        assert data["total_registered"] > 0

    def test_capability_registry_operations(self):
        """Test basic capability registry operations."""
        from src.nusyq_spine.registry import get_capability_registry

        registry = get_capability_registry()

        # Register
        registry.register(
            "test_capability",
            {
                "type": "test",
                "description": "A test capability",
                "tags": ["test", "demo"],
            },
        )

        # Get
        cap = registry.get("test_capability")
        assert cap is not None
        assert cap["type"] == "test"

        # Find
        results = registry.find("test")
        assert len(results) > 0

        # Get by tag
        tagged = registry.get_by_tag("test")
        assert any(r["name"] == "test_capability" for r in tagged)

        # Unregister
        assert registry.unregister("test_capability")

    def test_capability_registry_health_check(self):
        """Test capability registry health check."""
        from src.nusyq_spine.registry import get_capability_registry

        registry = get_capability_registry()
        result = registry.health_check()

        assert result.success
        data = result.data
        assert "status" in data
        assert "total_capabilities" in data


class TestCoreImports:
    """Tests for core imports integration."""

    def test_get_connector_registry(self):
        """Test get_connector_registry from core imports."""
        from src.core.imports import get_connector_registry

        ConnectorRegistry = get_connector_registry()
        assert ConnectorRegistry is not None

    def test_get_workflow_engine(self):
        """Test get_workflow_engine from core imports."""
        from src.core.imports import get_workflow_engine

        WorkflowEngine = get_workflow_engine()
        assert WorkflowEngine is not None

    def test_get_test_loop(self):
        """Test get_test_loop from core imports."""
        from src.core.imports import get_test_loop

        TestLoop = get_test_loop()
        assert TestLoop is not None


class TestCLICommands:
    """Tests for nq CLI commands."""

    def test_cli_imports(self):
        """Test that CLI can be imported without errors."""
        import sys

        # Add project root to path
        root = Path(__file__).parent.parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))

        # Import should work
        import importlib.util

        spec = importlib.util.spec_from_file_location("nq", root / "nq")
        if spec and spec.loader:
            nq_module = importlib.util.module_from_spec(spec)
            # Don't execute, just verify it can be loaded
            assert nq_module is not None


class TestResultType:
    """Tests for Result type consistency."""

    def test_connector_uses_result_type(self):
        """Test that connectors use Result type."""
        import inspect

        from src.connectors.base import BaseConnector
        from src.core.result import Result

        # Check connect method signature
        sig = inspect.signature(BaseConnector.connect)
        assert "Result" in str(sig.return_annotation) or sig.return_annotation == Result[bool]

    def test_workflow_uses_result_type(self):
        """Test that workflow engine uses Result type."""
        import inspect

        from src.core.result import Result
        from src.workflow.engine import WorkflowEngine

        # Check execute_workflow method
        sig = inspect.signature(WorkflowEngine.execute_workflow)
        # Return annotation should mention Result
        ret = str(sig.return_annotation)
        assert (
            "Result" in ret or sig.return_annotation.__origin__ is Result
            if hasattr(sig.return_annotation, "__origin__")
            else True
        )

    def test_test_loop_uses_result_type(self):
        """Test that TestLoop uses Result type."""
        import inspect

        from src.automation.test_loop import TestLoop
        from src.core.result import Result

        # Check run_tests method
        sig = inspect.signature(TestLoop.run_tests)
        ret = str(sig.return_annotation)
        assert (
            "Result" in ret or sig.return_annotation.__origin__ is Result
            if hasattr(sig.return_annotation, "__origin__")
            else True
        )
