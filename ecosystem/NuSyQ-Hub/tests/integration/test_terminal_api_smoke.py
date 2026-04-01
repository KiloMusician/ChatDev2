"""Runtime smoke suite for terminal API endpoint contracts.

Runs endpoint callables directly to validate runtime wiring without relying on
in-process ASGI client behavior in this pytest environment.
"""

from __future__ import annotations

import pytest
from fastapi.routing import APIRoute
from src.system import terminal_api

pytestmark = [pytest.mark.integration, pytest.mark.smoke]


class _FakeTerminalManager:
    def __init__(self) -> None:
        self._channels: dict[str, list[dict]] = {}

    def send(self, channel: str, level: str, message: str, meta: dict | None = None) -> dict:
        entry = {
            "channel": channel,
            "level": level,
            "message": message,
            "meta": meta or {},
        }
        self._channels.setdefault(channel, []).append(entry)
        return entry

    def list_channels(self) -> list[str]:
        return list(self._channels.keys())

    def recent(self, channel: str, n: int = 100) -> list[dict]:
        return self._channels.get(channel, [])[-n:]


class _FakeEnhancedTerminalManager:
    def __init__(self) -> None:
        self._last_session = "session-smoke-1"

    def get_session_summary(self) -> dict:
        return {"active_sessions": 1}

    def create_session(self) -> str:
        return self._last_session

    def execute_command(self, command: str, session_id: str) -> dict:
        return {"status": "completed", "command": command, "session_id": session_id}

    def get_session_output(self, session_id: str, command_index: int = -1) -> dict:
        return {"session_id": session_id, "command_index": command_index, "stdout": "ok"}


class _FakeEnhancedTerminalEcosystem:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def start_terminal(self, _terminal_type) -> bool:
        return True

    def stop_terminal(self, _terminal_type) -> bool:
        return True


def _endpoint(app, path: str):
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path:
            return route.endpoint
    raise AssertionError(f"Endpoint not found: {path}")


def test_terminal_api_health_and_message_flow_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.system.terminal_manager.EnhancedTerminalManager",
        _FakeEnhancedTerminalManager,
    )

    app = terminal_api.create_app()
    fake_tm = _FakeTerminalManager()

    health = _endpoint(app, "/health")()
    assert health.status == "ok"

    send = _endpoint(app, "/api/terminals/send")(
        terminal_api.TerminalSendRequest(
            channel="errors",
            level="warning",
            message="smoke test entry",
            meta={"source": "smoke"},
        ),
        tm=fake_tm,
    )
    assert send.status == "ok"
    assert send.payload["channel"] == "errors"

    terminals = _endpoint(app, "/api/terminals")(tm=fake_tm)
    assert terminals.status == "ok"
    assert "errors" in terminals.payload["channels"]

    recent = _endpoint(app, "/api/terminals/{channel}/recent")("errors", n=5, tm=fake_tm)
    assert recent.status == "ok"
    assert recent.payload["count"] >= 1


def test_terminal_api_runtime_controls_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.system.terminal_manager.EnhancedTerminalManager",
        _FakeEnhancedTerminalManager,
    )
    monkeypatch.setattr(
        "src.system.enhanced_terminal_ecosystem.EnhancedTerminalEcosystem",
        _FakeEnhancedTerminalEcosystem,
    )

    app = terminal_api.create_app()

    start = _endpoint(app, "/api/terminals/start")("claude")
    assert start.status == "ok"
    assert start.payload["started"] is True

    command = _endpoint(app, "/api/terminals/send_command")("claude", "echo smoke")
    assert command.status == "ok"
    assert command.payload["result"]["status"] == "completed"

    session_id = command.payload["session_id"]
    output = _endpoint(app, "/api/terminals/output/{session_id}")(session_id)
    assert output.status == "ok"

    stop = _endpoint(app, "/api/terminals/stop")("claude")
    assert stop.status == "ok"
    assert stop.payload["stopped"] is True
