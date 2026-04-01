"""Contract tests for QuestTempleBridge compatibility responses."""

from __future__ import annotations

import pytest
from src.integration.quest_temple_bridge import QuestTempleBridge, sync_progress

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_module_sync_progress_includes_success_flag() -> None:
    result = await sync_progress("quest-1", progress=50)
    assert result["success"] is True
    assert result["status"] == "stub"


async def test_instance_sync_progress_includes_success_flag() -> None:
    bridge = QuestTempleBridge()
    result = await bridge.sync_progress("quest-2", progress=75)
    assert result["success"] is True
    assert result["status"] == "stub"
