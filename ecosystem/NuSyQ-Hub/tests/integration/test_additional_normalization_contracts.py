"""Additional response-contract normalization tests for integration surfaces."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from src.integration.chatdev_integration import ChatDevIntegrationManager
from src.integration.n8n_integration import N8NClient
from src.orchestration.integrated_multi_agent_system import IntegratedMultiAgentSystem

pytestmark = [pytest.mark.integration]


def test_n8n_trigger_workflow_normalizes_success_for_json_payload() -> None:
    session = MagicMock()
    response = MagicMock()
    response.headers = {"content-type": "application/json"}
    response.raise_for_status.return_value = None
    response.json.return_value = {"status": "ok", "result": {"id": "wf-1"}}
    session.post.return_value = response

    client = N8NClient(base_url="http://example.com", session=session)
    result = client.trigger_workflow("test", {"a": 1})
    assert result["success"] is True
    assert result["status"] == "ok"


def test_n8n_trigger_workflow_normalizes_non_dict_payload() -> None:
    session = MagicMock()
    response = MagicMock()
    response.status_code = 202
    response.headers = {"content-type": "application/json"}
    response.raise_for_status.return_value = None
    response.json.return_value = ["queued"]
    session.post.return_value = response

    client = N8NClient(base_url="http://example.com", session=session)
    result = client.trigger_workflow("test", {"a": 1})
    assert result["success"] is True
    assert result["status"] == 202
    assert result["payload"] == ["queued"]


class _FakeCouncil:
    def list_decisions(self):
        return []


class _FakeTaskQueue:
    def __init__(self) -> None:
        self._agent_registry = {}

    def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        capabilities: list[str],
        max_concurrent_tasks: int,
    ) -> None:
        self._agent_registry[agent_id] = {
            "id": agent_id,
            "name": agent_name,
            "capabilities": capabilities,
            "max_concurrent_tasks": max_concurrent_tasks,
            "current_load": 0,
        }

    def get_queue_status(self) -> dict:
        return {"pending": 0}


class _FakeFeedbackLoop:
    def __init__(self, errors: list[SimpleNamespace]) -> None:
        self._error_queue = errors
        self._loops = {}

    def ingest_errors_from_report(self, _path) -> int:
        return len(self._error_queue)

    def process_error_queue(self, max_errors: int) -> int:
        return 0

    def get_engine_status(self) -> dict:
        return {"queue": len(self._error_queue)}


def test_integrated_system_no_errors_includes_success() -> None:
    system = IntegratedMultiAgentSystem(
        council=_FakeCouncil(),
        task_queue=_FakeTaskQueue(),
        feedback_loop=_FakeFeedbackLoop(errors=[]),
    )
    result = system.process_errors_with_voting()
    assert result["success"] is True
    assert result["status"] == "no_errors"


def test_integrated_system_complete_includes_success(monkeypatch) -> None:
    system = IntegratedMultiAgentSystem(
        council=_FakeCouncil(),
        task_queue=_FakeTaskQueue(),
        feedback_loop=_FakeFeedbackLoop(errors=[SimpleNamespace(error_type="ruff")]),
    )
    monkeypatch.setattr(system, "_group_errors_by_type", lambda: {})

    result = system.process_errors_with_voting()
    assert result["success"] is True
    assert result["status"] == "complete"


def test_chatdev_autofix_contract_flags(monkeypatch) -> None:
    manager = object.__new__(ChatDevIntegrationManager)

    monkeypatch.setattr(
        "src.integration.chatdev_integration.is_feature_enabled", lambda _flag: False
    )
    disabled = ChatDevIntegrationManager.launch_autofix(manager, "fix imports")
    assert disabled["success"] is False
    assert disabled["status"] == "disabled"

    # Mock launch_chatdev_session to avoid actually launching ChatDev
    monkeypatch.setattr(
        "src.integration.chatdev_integration.launch_chatdev_session",
        lambda **kwargs: {"success": True, "status": "launched"},
    )
    monkeypatch.setattr(
        "src.integration.chatdev_integration.is_feature_enabled", lambda _flag: True
    )
    enabled = ChatDevIntegrationManager.launch_autofix(manager, "fix imports")
    assert enabled["success"] is True
    assert enabled["status"] == "launched"
    assert enabled["autofix_enabled"] is True


def test_chatdev_initialize_missing_launcher_has_success_false() -> None:
    manager = object.__new__(ChatDevIntegrationManager)
    manager.launcher = None
    manager.session_active = False
    manager.integration_status = {}
    manager.repo_root = None
    manager.copilot_bridge = None
    manager.bridge_available = False
    manager.timeout_manager = None

    result = ChatDevIntegrationManager.initialize_chatdev_integration(manager)
    assert result["success"] is False
    assert result["status"] == "unavailable"
