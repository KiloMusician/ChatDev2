"""Lightweight spine integration test.

This test creates a temporary config file that represents enabling the NuSyQ
spine and asserts that the file can be created and read. It's intentionally
minimal and avoids importing runtime spine modules so it stays safe in CI.
"""

import os
import tempfile


def test_create_and_read_spine_config():
    data = "enabled: true\nendpoint: http://localhost:9000\n"
    td = tempfile.mkdtemp(prefix="nusyq_spine_test_")
    cfg_path = os.path.join(td, "nusyq_spine.yaml")
    with open(cfg_path, "w", encoding="utf-8") as fh:
        fh.write(data)

    with open(cfg_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    assert "enabled" in content
    assert "endpoint" in content


from src.tools import agent_task_router as router


def test_spine_emit_on_route(monkeypatch):
    """Verify that when spine is enabled, `_emit_spine_event` is called during routing."""

    called = {}

    def fake_spine_enabled() -> bool:
        return True

    def fake_emit(channel: str, payload: dict):
        called["channel"] = channel
        called["payload"] = payload

    # Patch internals
    monkeypatch.setattr(router, "_spine_enabled", fake_spine_enabled)
    monkeypatch.setattr(router, "_emit_spine_event", fake_emit)

    # Build a minimal task payload; route_task should attempt to emit
    task = {
        "task_id": "test-1",
        "target": "ollama",
        "input": "Say hello",
    }

    # Call route_task; ensure it completes without raising and that emit was called
    router.route_task(task)

    assert "channel" in called and isinstance(called["channel"], str)
    assert "payload" in called and isinstance(called["payload"], dict)
