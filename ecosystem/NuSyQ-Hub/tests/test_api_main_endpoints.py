"""Tests for src/api/main.py endpoints.

Codex-identified highest-ROI coverage targets (2026-03-03):
  1. /api/status — offline (503) vs online + heartbeat freshness
  2. /api/problems — system offline (503), problems API missing (501), happy path
  3. /api/problems/snapshot — no API (501), happy path
  4. /api/health — status file present/missing, problems aggregation
  5. /api/heartbeat — always succeeds, updates heartbeat
  6. /api/status/set — updates status and returns correct payload
  7. /healthz — always returns ok
  8. /readyz — offline (503) vs online (200)
  9. _is_heartbeat_stale helper
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Guard: skip all tests if fastapi / httpx not installed
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient


def _make_client(
    is_on: bool = True,
    system_status: dict[str, Any] | None = None,
    problems_api=None,
    status_file_exists: bool = True,
) -> TestClient:
    """Build a TestClient with fully mocked system-level helpers."""
    status_payload = system_status or {
        "status": "on",
        "health": "healthy",
        "details": {
            "last_heartbeat": datetime.now().isoformat(),
            "uptime": 42,
        },
    }

    patches = {
        "src.api.main.is_system_on": MagicMock(return_value=is_on),
        "src.api.main.get_system_status": MagicMock(return_value=status_payload),
        "src.api.main.set_system_status": MagicMock(),
        "src.api.main.update_heartbeat": MagicMock(),
        "src.api.main.get_problems_api": MagicMock(return_value=problems_api),
        "src.api.main._status_file_exists": MagicMock(return_value=status_file_exists),
    }

    with (
        patch("src.api.main.is_system_on", patches["src.api.main.is_system_on"]),
        patch("src.api.main.get_system_status", patches["src.api.main.get_system_status"]),
        patch("src.api.main.set_system_status", patches["src.api.main.set_system_status"]),
        patch("src.api.main.update_heartbeat", patches["src.api.main.update_heartbeat"]),
    ):
        # Import app fresh so decorators pick up patches
        import importlib
        import src.api.main as api_module

        importlib.reload(api_module)
        if api_module.app is None:
            pytest.skip("FastAPI app not available")

        client = TestClient(api_module.app, raise_server_exceptions=False)
        # Store patches for test bodies to access
        client._patches = patches  # type: ignore[attr-defined]
        client._api_module = api_module  # type: ignore[attr-defined]
        return client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_module():
    import src.api.main as m

    if m.app is None:
        pytest.skip("FastAPI not installed")
    return m


@pytest.fixture
def client_online(api_module):
    """TestClient with system ONLINE."""
    with (
        patch.object(api_module, "is_system_on", return_value=True),
        patch.object(
            api_module,
            "get_system_status",
            return_value={
                "status": "on",
                "health": "healthy",
                "details": {
                    "last_heartbeat": datetime.now().isoformat(),
                    "uptime": 120,
                },
            },
        ),
        patch.object(api_module, "set_system_status"),
        patch.object(api_module, "update_heartbeat"),
        patch.object(api_module, "get_problems_api", return_value=None),
        patch.object(api_module, "_status_file_exists", return_value=True),
    ):
        yield TestClient(api_module.app, raise_server_exceptions=False)


@pytest.fixture
def client_offline(api_module):
    """TestClient with system OFFLINE."""
    with (
        patch.object(api_module, "is_system_on", return_value=False),
        patch.object(
            api_module, "get_system_status", return_value={"status": "off", "health": "unknown"}
        ),
        patch.object(api_module, "set_system_status"),
        patch.object(api_module, "update_heartbeat"),
        patch.object(api_module, "get_problems_api", return_value=None),
        patch.object(api_module, "_status_file_exists", return_value=False),
    ):
        yield TestClient(api_module.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# /healthz — Kubernetes liveness probe (always 200)
# ---------------------------------------------------------------------------


class TestHealthz:
    def test_healthz_always_200(self, client_online) -> None:
        resp = client_online.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_healthz_200_even_when_system_offline(self, client_offline) -> None:
        resp = client_offline.get("/healthz")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /readyz — Kubernetes readiness probe
# ---------------------------------------------------------------------------


class TestReadyz:
    def test_readyz_200_when_online(self, client_online) -> None:
        resp = client_online.get("/readyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"

    def test_readyz_503_when_offline(self, client_offline) -> None:
        resp = client_offline.get("/readyz")
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "not_ready"


# ---------------------------------------------------------------------------
# GET /api/status
# ---------------------------------------------------------------------------


class TestGetStatus:
    def test_status_503_when_system_offline(self, client_offline) -> None:
        resp = client_offline.get("/api/status")
        assert resp.status_code == 503

    def test_status_200_when_system_online(self, client_online) -> None:
        resp = client_online.get("/api/status")
        assert resp.status_code == 200

    def test_status_includes_agent_check(self, client_online) -> None:
        resp = client_online.get("/api/status")
        data = resp.json()
        assert "agent_check" in data
        agent_check = data["agent_check"]
        assert "is_on" in agent_check
        assert "is_healthy" in agent_check
        assert "heartbeat_stale" in agent_check
        assert "safe_to_proceed" in agent_check

    def test_status_heartbeat_stale_when_old(self, api_module) -> None:
        """Old heartbeat => heartbeat_stale: true in agent_check."""
        old_time = (datetime.now() - timedelta(minutes=5)).isoformat()
        with (
            patch.object(api_module, "is_system_on", return_value=True),
            patch.object(
                api_module,
                "get_system_status",
                return_value={
                    "status": "on",
                    "health": "healthy",
                    "details": {"last_heartbeat": old_time, "uptime": 0},
                },
            ),
            patch.object(api_module, "get_problems_api", return_value=None),
            patch.object(api_module, "_status_file_exists", return_value=True),
        ):
            client = TestClient(api_module.app, raise_server_exceptions=False)
            resp = client.get("/api/status")

        data = resp.json()
        assert data["agent_check"]["heartbeat_stale"] is True
        assert data["agent_check"]["safe_to_proceed"] is False


# ---------------------------------------------------------------------------
# GET /api/problems
# ---------------------------------------------------------------------------


class TestGetProblems:
    def test_problems_503_when_system_offline(self, client_offline) -> None:
        resp = client_offline.get("/api/problems")
        assert resp.status_code == 503

    def test_problems_501_when_api_unavailable(self, client_online) -> None:
        # get_problems_api already patched to return None in client_online
        resp = client_online.get("/api/problems")
        assert resp.status_code == 501

    def test_problems_happy_path(self, api_module) -> None:
        mock_api = MagicMock()
        mock_api.get_current_problems = MagicMock(
            return_value={"total_counts": {"total": 3, "errors": 1, "warnings": 2}}
        )
        mock_problems_factory = MagicMock(return_value=mock_api)

        with (
            patch.object(api_module, "is_system_on", return_value=True),
            patch.object(api_module, "get_system_status", return_value={"status": "on"}),
            patch.object(api_module, "get_problems_api", mock_problems_factory),
            patch.object(api_module, "_status_file_exists", return_value=True),
        ):
            client = TestClient(api_module.app, raise_server_exceptions=False)
            resp = client.get("/api/problems")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_counts"]["total"] == 3

    def test_problems_repo_filter_passed_through(self, api_module) -> None:
        """Query param `repo` is forwarded to get_current_problems."""
        captured: dict = {}
        mock_api = MagicMock()

        def capture(repo=None, source="all", include_details=False):
            captured["repo"] = repo
            return {"total_counts": {"total": 0, "errors": 0, "warnings": 0}}

        mock_api.get_current_problems = capture
        mock_problems_factory = MagicMock(return_value=mock_api)

        with (
            patch.object(api_module, "is_system_on", return_value=True),
            patch.object(api_module, "get_system_status", return_value={"status": "on"}),
            patch.object(api_module, "get_problems_api", mock_problems_factory),
            patch.object(api_module, "_status_file_exists", return_value=True),
        ):
            client = TestClient(api_module.app, raise_server_exceptions=False)
            client.get("/api/problems?repo=nusyq-hub")

        assert captured.get("repo") == "nusyq-hub"


# ---------------------------------------------------------------------------
# POST /api/problems/snapshot
# ---------------------------------------------------------------------------


class TestCreateProblemSnapshot:
    def test_snapshot_501_when_api_unavailable(self, client_online) -> None:
        resp = client_online.post("/api/problems/snapshot")
        assert resp.status_code == 501

    def test_snapshot_returns_path_and_format(self, api_module) -> None:
        mock_api = MagicMock()
        mock_api.generate_snapshot_file = MagicMock(return_value="/tmp/snapshot.md")
        mock_problems_factory = MagicMock(return_value=mock_api)

        with (
            patch.object(api_module, "is_system_on", return_value=True),
            patch.object(api_module, "get_system_status", return_value={"status": "on"}),
            patch.object(api_module, "get_problems_api", mock_problems_factory),
        ):
            client = TestClient(api_module.app, raise_server_exceptions=False)
            resp = client.post("/api/problems/snapshot?format=markdown")

        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Snapshot created"
        assert data["format"] == "markdown"
        assert "timestamp" in data


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------


class TestHealthCheck:
    def test_health_includes_status_file_component(self, client_online) -> None:
        resp = client_online.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["components"]["status_file"] == "healthy"

    def test_health_missing_status_file_is_flagged(self, api_module) -> None:
        with (
            patch.object(api_module, "is_system_on", return_value=True),
            patch.object(
                api_module,
                "get_system_status",
                return_value={"status": "on", "health": "healthy", "details": {}},
            ),
            patch.object(api_module, "get_problems_api", return_value=None),
            patch.object(api_module, "_status_file_exists", return_value=False),
        ):
            client = TestClient(api_module.app, raise_server_exceptions=False)
            resp = client.get("/api/health")

        data = resp.json()
        assert data["components"]["status_file"] == "missing"

    def test_health_problems_aggregated(self, api_module) -> None:
        mock_api = MagicMock()
        mock_api.get_current_problems = MagicMock(
            return_value={
                "total_counts": {"total": 5, "errors": 2, "warnings": 3},
                "health_assessment": "degraded",
            }
        )
        mock_problems_factory = MagicMock(return_value=mock_api)

        with (
            patch.object(api_module, "is_system_on", return_value=True),
            patch.object(
                api_module,
                "get_system_status",
                return_value={"status": "on", "health": "healthy", "details": {}},
            ),
            patch.object(api_module, "get_problems_api", mock_problems_factory),
            patch.object(api_module, "_status_file_exists", return_value=True),
        ):
            client = TestClient(api_module.app, raise_server_exceptions=False)
            resp = client.get("/api/health")

        data = resp.json()
        assert data["problems"]["total"] == 5
        assert data["problems"]["health_assessment"] == "degraded"


# ---------------------------------------------------------------------------
# GET /api/heartbeat
# ---------------------------------------------------------------------------


class TestHeartbeat:
    def test_heartbeat_always_alive(self, client_online) -> None:
        resp = client_online.get("/api/heartbeat")
        assert resp.status_code == 200
        data = resp.json()
        assert data["alive"] is True
        assert data["service"] == "nusyq-hub"
        assert "timestamp" in data

    def test_heartbeat_alive_even_when_offline(self, client_offline) -> None:
        """Heartbeat endpoint never raises — it's the liveness pulse."""
        resp = client_offline.get("/api/heartbeat")
        assert resp.status_code == 200
        assert resp.json()["alive"] is True


# ---------------------------------------------------------------------------
# POST /api/status/set
# ---------------------------------------------------------------------------


class TestSetStatus:
    def test_set_status_returns_updated_payload(self, client_online) -> None:
        resp = client_online.post("/api/status/set?status=on&health=healthy")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "on"
        assert data["health"] == "healthy"
        assert "timestamp" in data

    def test_set_status_error(self, client_online) -> None:
        resp = client_online.post("/api/status/set?status=error&health=critical")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
        assert data["health"] == "critical"


# ---------------------------------------------------------------------------
# GET / — root
# ---------------------------------------------------------------------------


class TestRoot:
    def test_root_returns_service_info(self, client_online) -> None:
        resp = client_online.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "NuSyQ-Hub Reactive API"
        assert "/api/status" in data["endpoints"]["status"]

    def test_root_status_offline_when_system_off(self, client_offline) -> None:
        resp = client_offline.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "offline"
