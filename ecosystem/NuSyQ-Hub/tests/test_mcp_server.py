import types

import pytest
from src.integration import mcp_server


class DummyLauncher:
    def __init__(self, *_, **__):
        self._status = {
            "chatdev_installed": True,
            "chatdev_path": "/tmp/chatdev",
            "runner": "run.py",
        }

    def check_status(self):
        return self._status

    def setup_api_key(self):
        return True

    def setup_environment(self):
        return None

    def launch_chatdev(self, *_, **__):
        DummyProc = types.SimpleNamespace(pid=12345)
        return DummyProc


class FailingLauncher(DummyLauncher):
    def launch_chatdev(self, *_, **__):
        raise RuntimeError("Cannot connect to Ollama at http://localhost:11434")


@pytest.fixture(autouse=True)
def patch_launcher(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp_server, "ChatDevLauncher", DummyLauncher)
    monkeypatch.setenv("NUSYQ_CHATDEV_RUNS_FILE", str(tmp_path / "chatdev_runs.json"))


def test_manifest_includes_chatdev_tools(monkeypatch):
    monkeypatch.setenv("MCP_SERVER_NAME", "TestMCP")
    server = mcp_server.MCPServer(host="127.0.0.1", port=0)
    client = server.app.test_client()
    resp = client.get("/manifest")
    assert resp.status_code == 200
    data = resp.get_json()
    tool_names = {t["name"] for t in data["tools"]}
    assert {"chatdev_run", "chatdev_status"} <= tool_names


def test_chatdev_run_executes(monkeypatch):
    monkeypatch.setenv("MCP_SERVER_NAME", "TestMCP")
    server = mcp_server.MCPServer(host="127.0.0.1", port=0)
    client = server.app.test_client()
    resp = client.post(
        "/execute",
        json={"tool": "chatdev_run", "parameters": {"task": "demo", "name": "demo"}},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["result"]["pid"] == 12345
    assert data["result"]["run_id"].startswith("chatdev_")


def test_chatdev_status_with_run_id(monkeypatch):
    monkeypatch.setenv("MCP_SERVER_NAME", "TestMCP")
    server = mcp_server.MCPServer(host="127.0.0.1", port=0)
    client = server.app.test_client()

    run_resp = client.post(
        "/execute",
        json={"tool": "chatdev_run", "parameters": {"task": "demo", "name": "demo"}},
    )
    run_data = run_resp.get_json()
    run_id = run_data["result"]["run_id"]

    status_resp = client.post(
        "/execute",
        json={"tool": "chatdev_status", "parameters": {"run_id": run_id}},
    )
    assert status_resp.status_code == 200
    status_data = status_resp.get_json()
    assert status_data["success"] is True
    assert status_data["result"]["run_id"] == run_id
    assert "run" in status_data["result"]


def test_get_context_uses_load_api(monkeypatch):
    class DummyContextManager:
        def load(self, name: str):
            return {"context_id": name, "source": "dummy"}

    from src.tools import agent_context_manager

    monkeypatch.setattr(agent_context_manager, "AgentContextManager", DummyContextManager)

    server = mcp_server.MCPServer(host="127.0.0.1", port=0)
    payload = server._handle_get_context({"context_id": "ctx-123"})

    assert payload["context_id"] == "ctx-123"
    assert payload["source"] == "dummy"


def test_chatdev_run_degraded_mode_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp_server, "ChatDevLauncher", FailingLauncher)
    monkeypatch.setenv("NUSYQ_CHATDEV_DEGRADED_ROOT", str(tmp_path / "chatdev_degraded"))

    server = mcp_server.MCPServer(host="127.0.0.1", port=0)
    client = server.app.test_client()
    resp = client.post(
        "/execute",
        json={
            "tool": "chatdev_run",
            "parameters": {"task": "demo", "name": "demo", "degraded_mode": True},
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["result"]["degraded"] is True
    assert data["result"]["status"] == "degraded_completed"
    assert (tmp_path / "chatdev_degraded").exists()
