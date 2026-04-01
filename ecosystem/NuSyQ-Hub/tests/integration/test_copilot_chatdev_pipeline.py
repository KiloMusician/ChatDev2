"""Integration test for the Copilot-ChatDev code fix pipeline."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.integration.chatdev_llm_adapter import ChatDevLLMAdapter
from src.integration.copilot_chatdev_bridge import CopilotChatDevBridge


def test_copilot_chatdev_pipeline_code_fix():
    """End-to-end simulation of a code fix via Copilot-ChatDev pipeline."""
    bridge = CopilotChatDevBridge()
    session = bridge.create_agent_collaboration_session(
        "Fix arithmetic bug", collaboration_mode="enhanced"
    )

    buggy_code = "def add(a, b):\n    return a - b\n"
    request = bridge.request_chatdev_assistance(session["id"], buggy_code, assistance_type="debug")

    assert request["next_action"] == "launch_chatdev_with_task"

    fake_patch = "diff --git a/math.py b/math.py\n@@\n-def add(a, b):\n-    return a - b\n+def add(a, b):\n+    return a + b\n"

    with (
        patch.object(ChatDevLLMAdapter, "_initialize_adapter", lambda self: None),
        patch.object(
            ChatDevLLMAdapter,
            "_process_with_offline_models",
            AsyncMock(return_value=fake_patch),
        ) as ollama_mock,
    ):
        adapter = ChatDevLLMAdapter()
        patch_text = asyncio.run(adapter.process_chatdev_request("Programmer", request["task"]))

    assert patch_text == fake_patch
    ollama_mock.assert_awaited_once()
