import asyncio

from src.copilot.task_manager import CopilotTaskManager
from src.integration.chatdev_llm_adapter import ChatDevLLMAdapter


def test_handle_response_triggers_task(monkeypatch):
    calls: list[str] = []

    def fake_lint():  # pragma: no cover - simple record
        calls.append("lint")

    manager = CopilotTaskManager(task_router={"lint": fake_lint})
    manager.handle_response("please run lint")
    assert calls == ["lint"]


def test_chatdev_adapter_triggers_task(monkeypatch):
    calls: list[str] = []

    async def mock_offline(role, message, context):
        return "<task:lint>"

    manager = CopilotTaskManager(task_router={"lint": lambda: calls.append("lint")})

    adapter = ChatDevLLMAdapter()
    adapter.task_manager = manager
    monkeypatch.setattr(adapter, "_process_with_offline_models", mock_offline)

    asyncio.run(adapter.process_chatdev_request("Programmer", "msg", {}))
    assert calls == ["lint"]
