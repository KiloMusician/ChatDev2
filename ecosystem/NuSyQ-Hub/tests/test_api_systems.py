import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from src.api import systems

# Build a minimal FastAPI app for tests that only mounts the systems router
app = FastAPI()
app.include_router(systems.router, prefix="/api")
REQUEST_TIMEOUT_SECONDS = 15.0


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_get_metrics(client):
    resp = await client.get("/api/metrics", timeout=REQUEST_TIMEOUT_SECONDS)
    assert resp.status_code == 200
    data = resp.json()
    assert "agents_online" in data
    assert "active_quests" in data
    assert "system_utilization" in data


@pytest.mark.asyncio
async def test_list_agents(client):
    resp = await client.get("/api/agents", timeout=REQUEST_TIMEOUT_SECONDS)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(a.get("id") == "copilot" for a in data)


@pytest.mark.asyncio
async def test_list_quests(client):
    resp = await client.get("/api/quests", timeout=REQUEST_TIMEOUT_SECONDS)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any("title" in q for q in data)


@pytest.mark.asyncio
async def test_list_systems_and_status(client):
    resp = await client.get("/api/systems", timeout=REQUEST_TIMEOUT_SECONDS)
    assert resp.status_code == 200
    systems = resp.json()
    assert isinstance(systems, list)
    # pick one system id to check its status endpoint
    resp2 = await client.get("/api/systems/culture_ship/status", timeout=REQUEST_TIMEOUT_SECONDS)
    assert resp2.status_code == 200
    s = resp2.json()
    assert s.get("name") == "Culture Ship"


def test_antigravity_probe_requires_runtime_when_strict(tmp_path, monkeypatch):
    scene = tmp_path / "scene-router.js"
    scene.write_text(
        "this.scenes.set('antigravity', {});\nsystemId: 'antigravity'\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        systems,
        "_build_system_probes",
        lambda: {
            "antigravity": {
                "required_paths": [scene],
                "optional_paths": [],
                "urls": [],
                "process_keywords": ["modular-window-server"],
                "strict_runtime": True,
                "content_markers": [
                    {
                        "path": scene,
                        "patterns": ["this.scenes.set('antigravity'", "systemId: 'antigravity'"],
                    }
                ],
            }
        },
    )
    monkeypatch.setattr(systems, "_process_running", lambda _keywords: False)
    monkeypatch.setattr(systems, "_http_healthy", lambda _url, timeout_seconds=0.8: False)

    status, detail = systems._probe_system_status("antigravity")
    assert status == "degraded"
    assert "strict_runtime yes" in detail


def test_antigravity_probe_online_with_runtime_process(tmp_path, monkeypatch):
    scene = tmp_path / "scene-router.js"
    scene.write_text(
        "this.scenes.set('antigravity', {});\nsystemId: 'antigravity'\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        systems,
        "_build_system_probes",
        lambda: {
            "antigravity": {
                "required_paths": [scene],
                "optional_paths": [],
                "urls": [],
                "process_keywords": ["modular-window-server"],
                "strict_runtime": True,
                "content_markers": [
                    {
                        "path": scene,
                        "patterns": ["this.scenes.set('antigravity'", "systemId: 'antigravity'"],
                    }
                ],
            }
        },
    )
    monkeypatch.setattr(systems, "_process_running", lambda _keywords: True)
    monkeypatch.setattr(systems, "_http_healthy", lambda _url, timeout_seconds=0.8: False)

    status, detail = systems._probe_system_status("antigravity")
    assert status == "online"
    assert "process yes" in detail


def test_antigravity_probe_keywords_are_specific():
    probes = systems._build_system_probes()
    antigravity = probes.get("antigravity", {})
    keywords = antigravity.get("process_keywords", [])
    assert "npm run dev" not in keywords
    assert "vite" not in keywords


def test_antigravity_probe_includes_health_urls_and_requires_health():
    probes = systems._build_system_probes()
    antigravity = probes.get("antigravity", {})
    urls = antigravity.get("urls", [])
    assert any(str(url).endswith("/health") for url in urls)
    assert antigravity.get("require_health_url") is True


# Note: /api/health and /api/heartbeat are part of the full app (src.api.main)
# and are not mounted in the minimal test app used here. Those endpoints are
# covered by integration tests that run the full application.
