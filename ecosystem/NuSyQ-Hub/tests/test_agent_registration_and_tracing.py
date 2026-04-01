import importlib
from pathlib import Path

import pytest

@pytest.mark.smoke
def test_metaclaw_and_hermes_agent_registered():
    """MetaClaw and Hermes-Agent should be represented in the agent role surface."""
    hub_module = importlib.import_module("src.agents.agent_communication_hub")
    roles = getattr(hub_module, "AgentRole", None)
    assert roles is not None, "AgentRole enum missing"
    assert hasattr(roles, "METACLAW"), "MetaClaw not registered"
    assert hasattr(roles, "HERMES_AGENT"), "Hermes-Agent not registered"

@pytest.mark.smoke
def test_lightweight_tracing_enabled_and_utilized(tmp_path: Path):
    """Lightweight tracer should support starting traces and spans without telemetry infra."""
    tracing = importlib.import_module("src.observability.lightweight_tracer")
    tracer = tracing.LightweightTracer(output_dir=tmp_path)
    trace_id = tracer.start_trace("test_trace_utilization")
    span_id = tracer.start_span(trace_id, "test_trace", {"test": True})
    tracer.set_attribute(span_id, "agent", "codex")
    tracer.end_span(span_id)
    trace_path = tracer.end_trace(trace_id)

    assert trace_path.exists()
    assert trace_path.parent == tmp_path
