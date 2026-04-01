"""Integration tests for protocol wiring surfaces.

These tests validate that recently added protocol capabilities are wired into
existing infrastructure without introducing new architectural seams.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from src.connectors.base import ConnectorConfig
from src.connectors.registry import ConnectorRegistry
from src.connectors.webhook import WebhookConnector
from src.core.imports import (
    get_connector_registry,
    get_sns_converter,
    get_test_loop,
    get_workflow_engine,
    get_zero_token_bridge,
)
from src.factories.templates import BaseWebApp, load_template
from src.workflow.engine import WorkflowEngine
from src.workflow.nodes import ActionNode, NodeType, OutputNode, TriggerNode

pytestmark = pytest.mark.timeout(120)


def test_import_helpers_resolve_protocol_surfaces() -> None:
    """Import helpers should resolve protocol components."""
    assert get_connector_registry() is not None
    assert get_workflow_engine() is not None
    assert get_test_loop() is not None
    assert get_zero_token_bridge() is not None
    assert get_sns_converter() is not None


def test_webapp_templates_load() -> None:
    """Web app templates should load through existing template loader."""
    repo_root = Path(__file__).resolve().parents[1]

    flask_template = load_template(repo_root / "config/templates/flask_api.yaml")
    fastapi_template = load_template(repo_root / "config/templates/fastapi_service.yaml")

    assert isinstance(flask_template, BaseWebApp)
    assert isinstance(fastapi_template, BaseWebApp)
    assert flask_template.type == "webapp"
    assert fastapi_template.type == "webapp"
    assert flask_template.framework == "flask"
    assert fastapi_template.framework == "fastapi"


def test_connector_registry_register_connect_disconnect(tmp_path: Path) -> None:
    """Connector registry should register and operate a webhook connector."""
    ConnectorRegistry._instance = None
    registry = ConnectorRegistry(config_path=tmp_path / "connectors.json")

    connector = WebhookConnector(
        ConnectorConfig(name="test_webhook", endpoint="https://example.com/webhook")
    )

    register_result = registry.register(connector, override=True)
    assert register_result.success
    assert registry.get("test_webhook") is connector

    connectors = registry.list_connectors()
    assert any(item["name"] == "test_webhook" for item in connectors)

    connect_result = connector.connect()
    assert connect_result.success
    assert connector.is_connected

    disconnect_result = connector.disconnect()
    assert disconnect_result.success
    assert not connector.is_connected


def test_connector_registry_persists_and_reconnects(tmp_path: Path) -> None:
    """Connector configs should persist and support reconnect after reload."""
    config_path = tmp_path / "connectors.json"

    ConnectorRegistry._instance = None
    registry = ConnectorRegistry(config_path=config_path)
    connector = WebhookConnector(
        ConnectorConfig(name="persisted_webhook", endpoint="https://example.com/hook")
    )

    register_result = registry.register(connector, override=True)
    assert register_result.success
    assert config_path.exists()

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert "connectors" in payload
    assert "persisted_webhook" in payload["connectors"]

    ConnectorRegistry._instance = None
    reloaded_registry = ConnectorRegistry(config_path=config_path)
    restored = reloaded_registry.get("persisted_webhook")
    assert restored is not None
    assert restored.name == "persisted_webhook"

    connect_result = reloaded_registry.connect_all()
    assert connect_result.success
    assert "persisted_webhook" in connect_result.data["connected"]


def test_workflow_engine_executes_minimal_workflow(tmp_path: Path) -> None:
    """Workflow engine should execute a minimal trigger->action->output flow."""
    WorkflowEngine._instance = None
    engine = WorkflowEngine(workflows_dir=tmp_path)

    workflow_id = f"protocol_{uuid.uuid4().hex[:8]}"
    workflow = engine.create_workflow(
        id=workflow_id,
        name="Protocol Smoke Workflow",
        description="Minimal workflow for protocol verification",
    )

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
        name="Output",
        node_type=NodeType.OUTPUT,
        config={"format": "summary"},
    )

    workflow.add_node(trigger)
    workflow.add_node(action)
    workflow.add_node(output)
    workflow.add_edge("trigger_1", "action_1")
    workflow.add_edge("action_1", "output_1")

    save_result = engine.save_workflow(workflow)
    assert save_result.success

    run_result = engine.execute_workflow(workflow_id, {"seed": "ok"})
    assert run_result.success
    assert run_result.data is not None
    assert len(run_result.data.get("nodes_executed", [])) == 3

    history = engine.get_execution_history(workflow_id=workflow_id, limit=5)
    assert history
    assert history[0]["workflow_id"] == workflow_id
    assert history[0]["status"] == "completed"

    WorkflowEngine._instance = None
    reloaded_engine = WorkflowEngine(workflows_dir=tmp_path)
    reloaded_history = reloaded_engine.get_execution_history(workflow_id=workflow_id, limit=5)
    assert reloaded_history
    assert reloaded_history[0]["workflow_id"] == workflow_id
