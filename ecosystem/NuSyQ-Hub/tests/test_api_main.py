import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# App import helpers — import once and reuse across all tests
# ---------------------------------------------------------------------------

def _get_app():
    from src.api.main import app
    return app


@pytest.fixture
def client(tmp_path, monkeypatch):
    import src.system.status as status_module
    import src.api.main as api_main

    isolated_status = tmp_path / "state" / "system_status.json"
    monkeypatch.setattr(status_module, "STATUS_FILE", isolated_status)
    monkeypatch.setattr(api_main, "STATUS_FILE", isolated_status, raising=False)

    app = _get_app()
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers — shared mock factories
# ---------------------------------------------------------------------------

def _mock_status(status="on", health="healthy", last_heartbeat=None):
    if last_heartbeat is None:
        last_heartbeat = datetime.now().isoformat()
    return {
        "status": status,
        "health": health,
        "details": {
            "uptime": 123,
            "last_heartbeat": last_heartbeat,
        },
    }


def _mock_problems(total=5, errors=2, warnings=3, assessment="healthy"):
    return {
        "total_counts": {"total": total, "errors": errors, "warnings": warnings},
        "health_assessment": assessment,
        "items": [],
    }


# ===========================================================================
# Root endpoint
# ===========================================================================

class TestRoot:
    def test_root_returns_200(self, client):
        with patch("src.api.main.is_system_on", return_value=True):
            resp = client.get("/")
        assert resp.status_code == 200

    def test_root_structure(self, client):
        with patch("src.api.main.is_system_on", return_value=True):
            data = client.get("/").json()
        assert data["service"] == "NuSyQ-Hub Reactive API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "documentation" in data

    def test_root_status_operational_when_on(self, client):
        with patch("src.api.main.is_system_on", return_value=True):
            data = client.get("/").json()
        assert data["status"] == "operational"

    def test_root_status_offline_when_off(self, client):
        with patch("src.api.main.is_system_on", return_value=False):
            data = client.get("/").json()
        assert data["status"] == "offline"

    def test_root_endpoints_keys(self, client):
        with patch("src.api.main.is_system_on", return_value=True):
            data = client.get("/").json()
        assert "status" in data["endpoints"]
        assert "problems" in data["endpoints"]
        assert "health" in data["endpoints"]
        assert "docs" in data["endpoints"]


# ===========================================================================
# GET /api/status
# ===========================================================================

class TestGetStatus:
    def test_status_503_when_system_off(self, client):
        with patch("src.api.main.is_system_on", return_value=False):
            resp = client.get("/api/status")
        assert resp.status_code == 503
        assert "offline" in resp.json()["detail"].lower()

    def test_status_200_when_system_on(self, client):
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_system_status", return_value=_mock_status()):
            resp = client.get("/api/status")
        assert resp.status_code == 200

    def test_status_contains_agent_check(self, client):
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_system_status", return_value=_mock_status()):
            data = client.get("/api/status").json()
        assert "agent_check" in data
        ac = data["agent_check"]
        assert "is_on" in ac
        assert "is_healthy" in ac
        assert "heartbeat_stale" in ac
        assert "safe_to_proceed" in ac

    def test_status_is_on_when_status_on(self, client):
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_system_status", return_value=_mock_status("on", "healthy")):
            data = client.get("/api/status").json()
        assert data["agent_check"]["is_on"] is True

    def test_status_is_on_false_when_status_off(self, client):
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_system_status", return_value=_mock_status("off", "healthy")):
            data = client.get("/api/status").json()
        assert data["agent_check"]["is_on"] is False

    def test_status_safe_to_proceed_true(self, client):
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_system_status", return_value=_mock_status("on", "healthy")):
            data = client.get("/api/status").json()
        assert data["agent_check"]["safe_to_proceed"] is True

    def test_status_safe_to_proceed_false_when_degraded_health_not_ok(self, client):
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_system_status", return_value=_mock_status("on", "critical")):
            data = client.get("/api/status").json()
        assert data["agent_check"]["safe_to_proceed"] is False

    def test_status_treats_degraded_health_as_proceedable(self, client):
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_system_status", return_value=_mock_status("on", "degraded")):
            data = client.get("/api/status").json()
        assert data["agent_check"]["is_healthy"] is False
        assert data["agent_check"]["safe_to_proceed"] is True

    def test_status_prefers_details_health_over_top_level_health(self, client):
        payload = {
            "status": "on",
            "health": "critical",
            "details": {
                "health": "healthy",
                "last_heartbeat": datetime.now().isoformat(),
                "uptime": 123,
            },
        }
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_system_status", return_value=payload):
            data = client.get("/api/status").json()
        assert data["agent_check"]["is_healthy"] is True
        assert data["agent_check"]["safe_to_proceed"] is True

    def test_status_invalid_payload_returns_unknown(self, client):
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_system_status", return_value="not-a-dict"):
            data = client.get("/api/status").json()
        assert data["status"] == "unknown"
        assert "error" in data

    def test_status_heartbeat_stale_when_old(self, client):
        old_time = (datetime.now() - timedelta(minutes=5)).isoformat()
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_system_status", return_value=_mock_status("on", "healthy", old_time)):
            data = client.get("/api/status").json()
        assert data["agent_check"]["heartbeat_stale"] is True

    def test_status_heartbeat_fresh(self, client):
        recent = datetime.now().isoformat()
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_system_status", return_value=_mock_status("on", "healthy", recent)):
            data = client.get("/api/status").json()
        assert data["agent_check"]["heartbeat_stale"] is False


# ===========================================================================
# GET /api/problems
# ===========================================================================

class TestGetProblems:
    def test_problems_503_when_system_off(self, client):
        with patch("src.api.main.is_system_on", return_value=False):
            resp = client.get("/api/problems")
        assert resp.status_code == 503

    def test_problems_501_when_api_not_callable(self, client):
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_problems_api", None):
            resp = client.get("/api/problems")
        assert resp.status_code == 501

    def test_problems_501_when_api_returns_none(self, client):
        mock_factory = MagicMock(return_value=None)
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_problems_api", mock_factory):
            resp = client.get("/api/problems")
        assert resp.status_code == 501

    def test_problems_200_with_valid_api(self, client):
        mock_api = MagicMock()
        mock_api.get_current_problems.return_value = _mock_problems()
        mock_factory = MagicMock(return_value=mock_api)
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_problems_api", mock_factory):
            resp = client.get("/api/problems")
        assert resp.status_code == 200

    def test_problems_passes_query_params(self, client):
        mock_api = MagicMock()
        mock_api.get_current_problems.return_value = _mock_problems()
        mock_factory = MagicMock(return_value=mock_api)
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_problems_api", mock_factory):
            client.get("/api/problems?repo=nusyq-hub&source=ruff&include_details=true")
        mock_api.get_current_problems.assert_called_once_with(
            repo="nusyq-hub", source="ruff", include_details=True
        )

    def test_problems_invalid_payload_returns_error(self, client):
        mock_api = MagicMock()
        mock_api.get_current_problems.return_value = "not-a-dict"
        mock_factory = MagicMock(return_value=mock_api)
        with patch("src.api.main.is_system_on", return_value=True), \
             patch("src.api.main.get_problems_api", mock_factory):
            data = client.get("/api/problems").json()
        assert "error" in data


# ===========================================================================
# POST /api/problems/snapshot
# ===========================================================================

class TestCreateProblemSnapshot:
    def test_snapshot_501_when_api_not_callable(self, client):
        with patch("src.api.main.get_problems_api", None):
            resp = client.post("/api/problems/snapshot")
        assert resp.status_code == 501

    def test_snapshot_501_when_api_returns_none(self, client):
        mock_factory = MagicMock(return_value=None)
        with patch("src.api.main.get_problems_api", mock_factory):
            resp = client.post("/api/problems/snapshot")
        assert resp.status_code == 501

    def test_snapshot_200_with_valid_api(self, client):
        mock_api = MagicMock()
        mock_api.generate_snapshot_file.return_value = "/tmp/snapshot.md"
        mock_factory = MagicMock(return_value=mock_api)
        with patch("src.api.main.get_problems_api", mock_factory):
            resp = client.post("/api/problems/snapshot")
        assert resp.status_code == 200

    def test_snapshot_response_structure(self, client):
        mock_api = MagicMock()
        mock_api.generate_snapshot_file.return_value = "/tmp/snapshot.md"
        mock_factory = MagicMock(return_value=mock_api)
        with patch("src.api.main.get_problems_api", mock_factory):
            data = client.post("/api/problems/snapshot?format_=json").json()
        assert data["message"] == "Snapshot created"
        assert "path" in data
        assert "format" in data
        assert "timestamp" in data
        assert data["format"] == "json"


# ===========================================================================
# GET /api/health
# ===========================================================================

class TestHealthCheck:
    def test_health_returns_200(self, client):
        with patch("src.api.main.get_system_status", return_value=_mock_status()):
            resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_structure(self, client):
        with patch("src.api.main.get_system_status", return_value=_mock_status()):
            data = client.get("/api/health").json()
        assert "timestamp" in data
        assert "overall_status" in data
        assert "system" in data
        assert "components" in data

    def test_health_api_server_always_healthy(self, client):
        with patch("src.api.main.get_system_status", return_value=_mock_status()):
            data = client.get("/api/health").json()
        assert data["components"]["api_server"] == "healthy"

    def test_health_includes_problems_when_api_available(self, client):
        mock_api = MagicMock()
        mock_api.get_current_problems.return_value = _mock_problems()
        mock_factory = MagicMock(return_value=mock_api)
        with patch("src.api.main.get_system_status", return_value=_mock_status()), \
             patch("src.api.main.get_problems_api", mock_factory):
            data = client.get("/api/health").json()
        assert "problems" in data
        assert data["problems"]["total"] == 5
        assert data["problems"]["errors"] == 2

    def test_health_problems_error_when_api_raises(self, client):
        mock_api = MagicMock()
        mock_api.get_current_problems.side_effect = RuntimeError("boom")
        mock_factory = MagicMock(return_value=mock_api)
        with patch("src.api.main.get_system_status", return_value=_mock_status()), \
             patch("src.api.main.get_problems_api", mock_factory):
            data = client.get("/api/health").json()
        assert "error" in data.get("problems", {})

    def test_health_status_file_missing(self, client):
        with patch("src.api.main.get_system_status", return_value=_mock_status()), \
             patch("src.api.main._status_file_exists", return_value=False):
            data = client.get("/api/health").json()
        assert data["components"]["status_file"] == "missing"

    def test_health_status_file_present(self, client):
        with patch("src.api.main.get_system_status", return_value=_mock_status()), \
             patch("src.api.main._status_file_exists", return_value=True):
            data = client.get("/api/health").json()
        assert data["components"]["status_file"] == "healthy"


# ===========================================================================
# GET /api/heartbeat
# ===========================================================================

class TestHeartbeat:
    def test_heartbeat_200(self, client):
        with patch("src.api.main.update_heartbeat"):
            resp = client.get("/api/heartbeat")
        assert resp.status_code == 200

    def test_heartbeat_structure(self, client):
        with patch("src.api.main.update_heartbeat"):
            data = client.get("/api/heartbeat").json()
        assert data["alive"] is True
        assert data["service"] == "nusyq-hub"
        assert "timestamp" in data

    def test_heartbeat_calls_update(self, client):
        with patch("src.api.main.update_heartbeat") as mock_hb:
            client.get("/api/heartbeat")
        mock_hb.assert_called_once()


# ===========================================================================
# POST /api/status/set
# ===========================================================================

class TestSetStatus:
    def test_set_status_200(self, client):
        with patch("src.api.main.set_system_status"):
            resp = client.post("/api/status/set?status=on")
        assert resp.status_code == 200

    def test_set_status_response_structure(self, client):
        with patch("src.api.main.set_system_status"):
            data = client.post("/api/status/set?status=on&health=healthy&message=ok").json()
        assert data["message"] == "Status updated"
        assert data["status"] == "on"
        assert data["health"] == "healthy"
        assert "timestamp" in data

    def test_set_status_calls_set_system_status(self, client):
        with patch("src.api.main.set_system_status") as mock_set:
            client.post("/api/status/set?status=error&health=critical")
        mock_set.assert_called_once()
        args, kwargs = mock_set.call_args
        assert args == ("error",)
        assert kwargs["run_id"] == "manual-api"
        assert kwargs["details"]["health"] == "critical"
        assert kwargs["details"]["message"] is None
        assert kwargs["details"]["service"] == "reactive-api"
        assert "last_heartbeat" in kwargs["details"]

    def test_set_status_with_message(self, client):
        with patch("src.api.main.set_system_status") as mock_set:
            client.post("/api/status/set?status=stopping&message=shutdown+in+progress")
        mock_set.assert_called_once()
        args, kwargs = mock_set.call_args
        assert args == ("stopping",)
        assert kwargs["run_id"] == "manual-api"
        assert kwargs["details"]["health"] == "healthy"
        assert kwargs["details"]["message"] == "shutdown in progress"
        assert kwargs["details"]["service"] == "reactive-api"
        assert "last_heartbeat" in kwargs["details"]


# ===========================================================================
# GET /healthz  and  GET /readyz
# ===========================================================================

class TestK8sEndpoints:
    def test_healthz_returns_ok(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_readyz_200_when_system_on(self, client):
        with patch("src.api.main.is_system_on", return_value=True):
            resp = client.get("/readyz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"

    def test_readyz_503_when_system_off(self, client):
        with patch("src.api.main.is_system_on", return_value=False):
            resp = client.get("/readyz")
        assert resp.status_code == 503
        assert resp.json()["status"] == "not_ready"
