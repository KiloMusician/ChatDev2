import pytest
from fastapi.testclient import TestClient
from src.api.main import app

if app is None:  # pragma: no cover - FastAPI missing in environment
    pytest.skip("FastAPI not available", allow_module_level=True)


client = TestClient(app)


def test_hints_returns_list():
    resp = client.get("/api/hints")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_ops_search_returns_matches():
    resp = client.get("/api/ops", params={"q": "quest"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data, "Expected at least one smart search result"
    assert any(
        "quest" in item.get("command", "").lower() or "quest" in item.get("description", "").lower()
        for item in data
    )


def test_commands_include_work():
    resp = client.get("/api/commands")
    assert resp.status_code == 200
    data = resp.json()
    assert any(cmd.get("command") == "start_nusyq.py work" for cmd in data)


def test_metrics_includes_quest_and_queue_fields():
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    data = resp.json()
    util = data["system_utilization"]
    for key in [
        "actionable_quests",
        "blocked_quests",
        "total_quests",
        "queued_pus",
        "executing_pus",
        "completed_pus",
    ]:
        assert key in util
    assert "cpu_percent" in util and "mem_percent" in util
