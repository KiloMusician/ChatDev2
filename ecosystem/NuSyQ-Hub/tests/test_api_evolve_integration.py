from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api import systems


def create_app():
    app = FastAPI()
    app.include_router(systems.router, prefix="/api")
    return app


def test_evolve_integration_creates_artifact(tmp_path):
    app = create_app()
    client = TestClient(app)

    resp = client.post("/api/evolve", json={"prompt": "integration test prompt"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "file" in data and "content" in data

    # Ensure file path exists on disk (rosetta runner writes to Reports/rosetta)
    file_path = Path(data["file"]).resolve()
    assert file_path.exists()
    # Clean up created file
    try:
        file_path.unlink()
    except Exception:
        pass
