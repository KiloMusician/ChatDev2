import asyncio

from src.copilot.extension.copilot_extension import CopilotExtension


def test_resolve_api_endpoint_prefers_bridge_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("NUSYQ_COPILOT_BRIDGE_ENDPOINT", "http://bridge.local/query")
    monkeypatch.setenv("GITHUB_COPILOT_API_ENDPOINT", "http://github.local/query")

    ext = CopilotExtension()

    assert ext.api_endpoint == "http://bridge.local/query"


def test_send_query_returns_none_when_endpoint_missing(monkeypatch) -> None:
    monkeypatch.delenv("NUSYQ_COPILOT_BRIDGE_ENDPOINT", raising=False)
    monkeypatch.delenv("GITHUB_COPILOT_API_ENDPOINT", raising=False)
    monkeypatch.delenv("NUSYQ_COPILOT_API_ENDPOINT", raising=False)
    monkeypatch.setenv("GITHUB_COPILOT_API_KEY", "token")

    ext = CopilotExtension()
    ext.api_client = object()  # bypass initialization guard for this focused test

    result = asyncio.run(ext.send_query("hello"))
    assert result is None
