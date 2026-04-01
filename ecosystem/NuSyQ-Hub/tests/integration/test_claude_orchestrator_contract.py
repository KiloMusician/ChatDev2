"""Contract tests for ClaudeOrchestrator response envelopes."""

from __future__ import annotations

import pytest
from src.orchestration.claude_orchestrator import ClaudeOrchestrator

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_ask_claude_missing_api_key_includes_success_false(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    orchestrator = ClaudeOrchestrator(repo_root=tmp_path)

    result = await orchestrator.ask_claude("hello")
    assert result["success"] is False
    assert result["status"] == "missing_api_key"
    assert "error" in result
    assert "api mode" in result["error"].lower()


class _FakeResponse:
    def __init__(self, status: int, payload: dict | None = None, text: str = "") -> None:
        self.status = status
        self._payload = payload or {}
        self._text = text

    async def text(self) -> str:
        return self._text

    async def json(self) -> dict:
        return self._payload


class _FakePostContext:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    async def __aenter__(self) -> _FakeResponse:
        return self._response

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeSession:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    async def __aenter__(self) -> _FakeSession:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, *_args, **_kwargs) -> _FakePostContext:
        return _FakePostContext(self._response)


async def test_ask_ollama_http_error_includes_success_false(monkeypatch, tmp_path) -> None:
    response = _FakeResponse(status=500, text="ollama down")
    monkeypatch.setattr(
        "src.orchestration.claude_orchestrator.aiohttp.ClientSession",
        lambda: _FakeSession(response),
    )

    orchestrator = ClaudeOrchestrator(repo_root=tmp_path)
    result = await orchestrator.ask_ollama("hello")
    assert result["success"] is False
    assert result["status"] == 500
    assert "error" in result
