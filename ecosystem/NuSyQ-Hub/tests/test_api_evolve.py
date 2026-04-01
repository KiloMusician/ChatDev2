import os

from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api import systems


def create_app():
    app = FastAPI()
    app.include_router(systems.router, prefix="/api")
    return app


def test_evolve_endpoints(tmp_path):
    app = create_app()
    client = TestClient(app)

    # Ensure listing works (may be empty)
    resp = client.get("/api/evolve")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # Trigger evolve (POST)
    resp2 = client.post("/api/evolve", json={"prompt": "Test evolve run"})
    assert resp2.status_code == 200
    data = resp2.json()
    assert "file" in data and "content" in data
    # File should exist on disk
    assert os.path.exists(data["file"]) or os.path.exists(data.get("file", ""))
