"""Fast contract smoke for both orchestration hub variants."""

from __future__ import annotations

import pytest
from src.agents.agent_orchestration_hub import AgentOrchestrationHub as LegacyAgentHub
from src.orchestration.agent_orchestration_hub import AgentOrchestrationHub as CoreAgentHub

pytestmark = pytest.mark.smoke


@pytest.mark.parametrize("hub_cls", [LegacyAgentHub, CoreAgentHub])
def test_normalize_contract_adds_success_when_missing(hub_cls: type) -> None:
    normalized = hub_cls._normalize_response_contract({"status": "success"})
    assert normalized["status"] == "success"
    assert normalized["success"] is True


@pytest.mark.parametrize("hub_cls", [LegacyAgentHub, CoreAgentHub])
def test_normalize_contract_derives_failed_status(hub_cls: type) -> None:
    normalized = hub_cls._normalize_response_contract({"success": False, "error": "boom"})
    assert normalized["status"] in {"failed", "error"}
    assert normalized["success"] is False
