"""Contract tests for OllamaAdapter response normalization."""

from __future__ import annotations

import io
import urllib.error

from src.integration.ollama_adapter import OllamaAdapter


class _FakeResponse:
    def __init__(self, body: str, status: int = 200) -> None:
        self._body = body.encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_query_base_url_missing_has_success_false() -> None:
    adapter = OllamaAdapter(base_url="")
    result = adapter.query("hello")
    assert result["success"] is False
    assert result["status"] == "error"


def test_query_normalizes_dict_without_status(monkeypatch) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: _FakeResponse('{"response":"ok"}'),
    )
    adapter = OllamaAdapter(base_url="http://localhost:11434")
    result = adapter.query("hello")
    assert result["success"] is True
    assert result["response"] == "ok"


def test_query_non_json_body_is_success_ok(monkeypatch) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: _FakeResponse("plain text"),
    )
    adapter = OllamaAdapter(base_url="http://localhost:11434")
    result = adapter.query("hello")
    assert result["success"] is True
    assert result["status"] == "ok"
    assert result["raw"] == "plain text"


def test_query_http_error_has_success_false(monkeypatch) -> None:
    def _raise(*_args, **_kwargs):
        raise urllib.error.HTTPError(
            url="http://localhost:11434/v1/complete",
            code=500,
            msg="server error",
            hdrs=None,
            fp=io.BytesIO(b"boom"),
        )

    monkeypatch.setattr("urllib.request.urlopen", _raise)
    adapter = OllamaAdapter(base_url="http://localhost:11434")
    result = adapter.query("hello")
    assert result["success"] is False
    assert result["status"] == "error"
    assert result["code"] == 500
