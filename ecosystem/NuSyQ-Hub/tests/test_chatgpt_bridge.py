import asyncio
import sys
import types

import src.system.chatgpt_bridge as bridge


def test_parse_command_name_splits_inline_tail() -> None:
    name, tail = bridge._parse_command_name("analyze src/main.py")
    assert name == "analyze"
    assert tail == "src/main.py"


def test_run_start_nusyq_rejects_invalid_action() -> None:
    result = bridge._run_start_nusyq({"action": "bad;rm"})
    assert result["status"] == "failed"
    assert result["success"] is False
    assert result["reason"] == "invalid_action"


def test_execute_bridge_command_uses_start_nusyq_common_action(monkeypatch) -> None:
    calls: list[tuple[dict | None, str | None]] = []

    def fake_run_start_nusyq(args: dict | None, inferred_action: str | None = None) -> dict:
        calls.append((args, inferred_action))
        return {"status": "success", "executor": "start_nusyq"}

    monkeypatch.setattr(bridge, "_run_start_nusyq", fake_run_start_nusyq)

    result = asyncio.run(bridge._execute_bridge_command("queue", {}))

    assert result["status"] == "success"
    assert result["success"] is True
    assert calls and calls[0][1] == "queue"


def test_execute_bridge_command_prefers_router(monkeypatch) -> None:
    async def fake_router(command_name: str, inline_tail: str, args: dict | None) -> dict:
        assert command_name == "analyze"
        assert inline_tail == "src/app.py"
        assert isinstance(args, dict)
        return {"status": "ok", "executor": "agent_task_router", "result": {"status": "success"}}

    monkeypatch.setattr(bridge, "_try_router_execute", fake_router)
    monkeypatch.setattr(
        bridge,
        "_try_orchestrator_execute",
        lambda *_args, **_kwargs: {"status": "unhandled"},
    )

    result = asyncio.run(bridge._execute_bridge_command("analyze src/app.py", {"context": {}}))

    assert result["status"] == "ok"
    assert result["success"] is True
    assert result["executor"] == "agent_task_router"


def test_execute_bridge_command_falls_back_to_orchestrator(monkeypatch) -> None:
    async def fake_router(_command_name: str, _inline_tail: str, _args: dict | None) -> dict:
        return {"status": "unhandled", "reason": "unsupported_router_command"}

    monkeypatch.setattr(bridge, "_try_router_execute", fake_router)
    monkeypatch.setattr(
        bridge,
        "_try_orchestrator_execute",
        lambda *_args, **_kwargs: {"status": "ok", "result": {"handled": True}},
    )

    result = asyncio.run(bridge._execute_bridge_command("unknown_command", {}))

    assert result["status"] == "ok"
    assert result["success"] is True
    assert result["executor"] == "unified_orchestrator"


def test_execute_bridge_command_terminals_channels(monkeypatch) -> None:
    monkeypatch.setattr(
        bridge,
        "_terminal_channels",
        lambda: {
            "status": "ok",
            "executor": "terminal_manager",
            "channels": ["Copilot"],
            "count": 1,
        },
    )

    result = asyncio.run(bridge._execute_bridge_command("terminals_channels", {}))

    assert result["status"] == "ok"
    assert result["success"] is True
    assert result["executor"] == "terminal_manager"
    assert result["channels"] == ["Copilot"]


def test_execute_bridge_command_terminals_recent(monkeypatch) -> None:
    monkeypatch.setattr(
        bridge,
        "_terminal_recent",
        lambda channel, limit=50: {
            "status": "ok",
            "executor": "terminal_manager",
            "channel": channel,
            "count": limit,
            "entries": [],
        },
    )

    result = asyncio.run(
        bridge._execute_bridge_command("terminals_recent", {"channel": "Copilot", "limit": 7})
    )

    assert result["status"] == "ok"
    assert result["success"] is True
    assert result["channel"] == "Copilot"
    assert result["count"] == 7


def test_execute_bridge_command_terminal_snapshot(monkeypatch) -> None:
    monkeypatch.setattr(
        bridge,
        "_terminal_snapshot",
        lambda limit_per_channel=20: {
            "status": "ok",
            "executor": "terminal_manager",
            "summary": {"total_channels": 1},
            "limit": limit_per_channel,
        },
    )

    result = asyncio.run(
        bridge._execute_bridge_command(
            "terminal_snapshot",
            {"limit": 9},
        )
    )

    assert result["status"] == "ok"
    assert result["success"] is True
    assert result["executor"] == "terminal_manager"
    assert result["limit"] == 9


def test_execute_bridge_command_background_task_status(monkeypatch) -> None:
    monkeypatch.setattr(
        bridge,
        "_background_task_status",
        lambda limit=10, status=None: {
            "status": "ok",
            "executor": "background_task_orchestrator",
            "count": limit,
            "filter": status,
        },
    )
    result = asyncio.run(
        bridge._execute_bridge_command(
            "background_task_status",
            {"limit": 4, "status": "queued"},
        )
    )
    assert result["status"] == "ok"
    assert result["success"] is True
    assert result["count"] == 4
    assert result["filter"] == "queued"


def test_execute_bridge_command_pu_queue_status(monkeypatch) -> None:
    monkeypatch.setattr(
        bridge,
        "_pu_queue_status",
        lambda limit=10, status=None: {
            "status": "ok",
            "executor": "unified_pu_queue",
            "count": limit,
            "filter": status,
        },
    )
    result = asyncio.run(
        bridge._execute_bridge_command(
            "pu_queue_status",
            {"limit": 6, "status": "approved"},
        )
    )
    assert result["status"] == "ok"
    assert result["success"] is True
    assert result["count"] == 6
    assert result["filter"] == "approved"


def test_execute_bridge_command_uses_async_orchestrator_adapter(monkeypatch) -> None:
    async def fake_router(_command_name: str, _inline_tail: str, _args: dict | None) -> dict:
        return {"status": "unhandled", "reason": "unsupported_router_command"}

    async def fake_async_orchestrator(_command_name: str, _args: dict | None) -> dict:
        return {
            "status": "ok",
            "adapter": "orchestrate_task_async",
            "result": {"status": "success"},
        }

    monkeypatch.setattr(bridge, "_try_router_execute", fake_router)
    monkeypatch.setattr(bridge, "_try_orchestrator_execute_async", fake_async_orchestrator)
    monkeypatch.setattr(
        bridge,
        "_try_orchestrator_execute",
        lambda *_args, **_kwargs: {"status": "unhandled"},
    )

    result = asyncio.run(
        bridge._execute_bridge_command("orchestrate_task", {"task_type": "analysis"})
    )

    assert result["status"] == "ok"
    assert result["success"] is True
    assert result["executor"] == "unified_orchestrator"
    assert result["result"]["adapter"] == "orchestrate_task_async"


def test_try_orchestrator_execute_async_orchestrate_task(monkeypatch) -> None:
    fake_module = types.ModuleType("fake_unified_orchestrator")

    class FakePriority:
        NORMAL = "NORMAL"

    class FakeOrchestrator:
        async def orchestrate_task_async(self, **kwargs):
            assert kwargs["task_type"] == "analysis"
            assert kwargs["content"] == "run now"
            return {"status": "success", "task_id": "run-1"}

    fake_module.UnifiedAIOrchestrator = FakeOrchestrator
    fake_module.TaskPriority = FakePriority
    monkeypatch.setitem(sys.modules, "src.orchestration.unified_ai_orchestrator", fake_module)

    result = asyncio.run(
        bridge._try_orchestrator_execute_async(
            "orchestrate_task",
            {"task_type": "analysis", "description": "run now"},
        )
    )

    assert result["status"] == "ok"
    assert result["success"] is True
    assert result["adapter"] == "orchestrate_task_async"
    assert result["result"]["status"] == "success"


def test_try_orchestrator_execute_uses_adapter_status(monkeypatch) -> None:
    fake_module = types.ModuleType("fake_unified_orchestrator")

    class FakePriority:
        NORMAL = "NORMAL"

    class FakeTask:
        def __init__(self, **kwargs) -> None:
            self.task_id = kwargs.get("task_id", "")

    class FakeOrchestrator:
        def get_system_status(self) -> dict:
            return {"ok": True}

    fake_module.UnifiedAIOrchestrator = FakeOrchestrator
    fake_module.OrchestrationTask = FakeTask
    fake_module.TaskPriority = FakePriority
    monkeypatch.setitem(sys.modules, "src.orchestration.unified_ai_orchestrator", fake_module)

    result = bridge._try_orchestrator_execute("orchestrator_status", {})
    assert result["status"] == "ok"
    assert result["success"] is True
    assert result["adapter"] == "get_system_status"
    assert result["result"]["ok"] is True


def test_try_orchestrator_execute_submit_task_adapter(monkeypatch) -> None:
    fake_module = types.ModuleType("fake_unified_orchestrator")

    class FakePriority:
        NORMAL = "NORMAL"
        HIGH = "HIGH"

    class FakeTask:
        def __init__(self, **kwargs) -> None:
            self.task_id = kwargs.get("task_id", "")
            self.task_type = kwargs.get("task_type", "")
            self.content = kwargs.get("content", "")
            self.context = kwargs.get("context", {})
            self.priority = kwargs.get("priority", "NORMAL")
            self.preferred_systems = kwargs.get("preferred_systems", [])

    class FakeOrchestrator:
        def _normalize_services(self, services):
            return services or []

        def submit_task(self, task):
            assert task.task_type == "analysis"
            assert task.content == "check this"
            return "task-123"

    fake_module.UnifiedAIOrchestrator = FakeOrchestrator
    fake_module.OrchestrationTask = FakeTask
    fake_module.TaskPriority = FakePriority
    monkeypatch.setitem(sys.modules, "src.orchestration.unified_ai_orchestrator", fake_module)

    result = bridge._try_orchestrator_execute(
        "submit_task",
        {"task_type": "analysis", "description": "check this", "priority": "HIGH"},
    )
    assert result["status"] == "ok"
    assert result["success"] is True
    assert result["adapter"] == "submit_task"
    assert result["result"]["task_id"] == "task-123"


def test_build_plugin_manifest_without_token(monkeypatch) -> None:
    monkeypatch.delenv("NUSYQ_BRIDGE_TOKEN", raising=False)
    manifest = bridge._build_plugin_manifest("http://127.0.0.1:8765")
    assert manifest["auth"]["type"] == "none"
    assert manifest["api"]["url"] == "http://127.0.0.1:8765/openapi.json"


def test_build_plugin_manifest_with_token(monkeypatch) -> None:
    monkeypatch.setenv("NUSYQ_BRIDGE_TOKEN", "x")
    manifest = bridge._build_plugin_manifest("http://127.0.0.1:8765")
    assert manifest["auth"]["type"] == "service_http"
    assert manifest["api"]["is_user_authenticated"] is True
