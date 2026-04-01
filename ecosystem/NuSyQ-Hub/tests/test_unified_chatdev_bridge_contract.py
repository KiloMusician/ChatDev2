"""Contract tests for unified ChatDev bridge response shape."""

import pytest
from src.integration.unified_chatdev_bridge import ChatDevOrchestrator

pytestmark = pytest.mark.smoke


def test_execute_task_success_includes_success_flag() -> None:
    orchestrator = ChatDevOrchestrator()
    assert orchestrator.initialize() is True

    result = orchestrator.execute_task("generate_code", {"task": "Create function"})

    assert result["status"] == "success"
    assert result["success"] is True
    assert result["task_type"] == "generate_code"


def test_execute_task_error_includes_success_false() -> None:
    orchestrator = ChatDevOrchestrator()
    assert orchestrator.initialize() is True

    result = orchestrator.execute_task("unknown_task", {})

    assert result["status"] == "error"
    assert result["success"] is False
    assert "Unknown task type" in result["error"]


def test_normalize_contract_derives_success_from_status() -> None:
    payload = ChatDevOrchestrator._normalize_response_contract({"status": "completed"})
    assert payload["status"] == "completed"
    assert payload["success"] is True


def test_response_succeeded_prefers_explicit_success_flag() -> None:
    payload = {"status": "success", "success": False}
    assert ChatDevOrchestrator._response_succeeded(payload) is False
