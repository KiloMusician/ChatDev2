import asyncio

import pytest
from src.tools import agent_task_router as at


def test_spine_disabled_by_default():
    # default config should keep spine disabled (opt-in)
    router = at.AgentTaskRouter()
    assert router._spine_enabled() is False


def test_emit_spine_noop_does_not_raise():
    # emitting when disabled should be a no-op and not raise
    router = at.AgentTaskRouter()
    try:
        asyncio.run(router._emit_spine_event({"name": "unit-test-event", "meta": {"foo": "bar"}}))
    except Exception as exc:  # pragma: no cover - defensive
        pytest.fail(f"_emit_spine_event raised: {exc}")
    # result is best-effort; successful if no exception raised
