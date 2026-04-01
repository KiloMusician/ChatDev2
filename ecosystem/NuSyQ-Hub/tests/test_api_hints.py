from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api import systems


def create_app():
    app = FastAPI()
    app.include_router(systems.router, prefix="/api")
    return app


def test_hints_and_help_endpoints():
    app = create_app()
    client = TestClient(app)

    resp = client.get("/api/hints")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Accept either dynamic hints from HintEngine or fallback hints
    assert len(data) > 0

    resp = client.get("/api/tutorials")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(t.get("id") == "t1" for t in data)

    resp = client.get("/api/faq")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any("How do I open" in f.get("question", "") for f in data)

    resp = client.get("/api/commands")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Ensure we have at least one command entry
    assert len(data) > 0

    resp = client.get("/api/scripts")
    assert resp.status_code == 200

    resp = client.get("/api/inventory")
    assert resp.status_code == 200

    resp = client.get("/api/ops")
    assert resp.status_code == 200
