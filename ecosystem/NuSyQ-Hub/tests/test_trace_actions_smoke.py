import json
import sys
import types
from contextlib import contextmanager
from pathlib import Path

import scripts.nusyq_actions.trace_actions as trace_actions


class _StubOtel:
    def __init__(self) -> None:
        self._trace_ids = ("trace-id", "span-id")

    def init_tracing(self, _name: str) -> bool:
        return True

    @contextmanager
    def start_action_span(self, *_args, **_kwargs):
        yield

    def current_trace_ids(self):
        return self._trace_ids

    def shutdown_tracing(self):
        return None


class _RepoPaths:
    def __init__(self, hub: Path) -> None:
        self.nusyq_hub = hub


def _install_stub_spine(tmp_path: Path) -> None:
    spine = types.ModuleType("scripts.start_nusyq")

    def load_trace_config(_hub: Path) -> dict:
        return {"enabled": True, "endpoint": "http://localhost:4318", "service_name": "test"}

    def apply_trace_config(_config: dict) -> None:
        return None

    def ensure_run_id() -> str:
        return "run-test"

    def _write_json_report(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def _trace_endpoint_check(_endpoint: str) -> tuple[bool, str]:
        return True, "ok"

    def save_trace_config(_hub: Path, _config: dict) -> None:
        return None

    def _receipt_dir(hub: Path) -> Path:
        rec = hub / "docs" / "tracing" / "RECEIPTS"
        rec.mkdir(parents=True, exist_ok=True)
        return rec

    spine.load_trace_config = load_trace_config  # type: ignore[attr-defined]
    spine.apply_trace_config = apply_trace_config  # type: ignore[attr-defined]
    spine.ensure_run_id = ensure_run_id  # type: ignore[attr-defined]
    spine._write_json_report = _write_json_report  # type: ignore[attr-defined]
    spine._trace_endpoint_check = _trace_endpoint_check  # type: ignore[attr-defined]
    spine.save_trace_config = save_trace_config  # type: ignore[attr-defined]
    spine._receipt_dir = _receipt_dir  # type: ignore[attr-defined]

    sys.modules["scripts.start_nusyq"] = spine


def test_trace_actions_smoke(tmp_path, monkeypatch):
    # Install stub spine/otel modules
    _install_stub_spine(tmp_path)
    stub_otel = _StubOtel()
    sys.modules["otel"] = stub_otel
    # Ensure trace_actions picks up stub even if already imported
    trace_actions.otel = stub_otel

    paths = _RepoPaths(tmp_path)

    # Service status should succeed with stub endpoint
    status_code = trace_actions.handle_trace_service_status(paths)
    assert status_code == 0

    # Smoke should emit a span and succeed
    smoke_code = trace_actions.handle_trace_smoke(paths)
    assert smoke_code == 0

    # Reports should be written
    assert (tmp_path / "state" / "reports" / "trace_service_status.json").exists()
    smoke_report_path = tmp_path / "state" / "reports" / "trace_smoke.json"
    assert smoke_report_path.exists()
    smoke_report = json.loads(smoke_report_path.read_text(encoding="utf-8"))
    assert smoke_report["failure_reason"] == "none"
    assert smoke_report["module_available"] is True


def test_trace_status_cleans_stale_pid_record(tmp_path, monkeypatch):
    _install_stub_spine(tmp_path)
    stub_otel = _StubOtel()
    sys.modules["otel"] = stub_otel
    trace_actions.otel = stub_otel

    paths = _RepoPaths(tmp_path)
    pid_path = trace_actions._trace_service_pid_path(tmp_path)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(
        '{"pid": 999999, "started_at": "2026-01-01T00:00:00+00:00"}', encoding="utf-8"
    )

    status_code = trace_actions.handle_trace_service_status(paths)
    assert status_code == 0
    assert not pid_path.exists()

    report = json.loads(
        (tmp_path / "state" / "reports" / "trace_service_status.json").read_text(encoding="utf-8")
    )
    assert report["stale_pid_file"] is True


def test_trace_healthcheck_ok_without_otel_backend(tmp_path, monkeypatch):
    _install_stub_spine(tmp_path)
    # Simulate environment where tracer backend is optional/unavailable.
    trace_actions.otel = None

    paths = _RepoPaths(tmp_path)
    rc = trace_actions.handle_trace_service_healthcheck(paths)
    assert rc == 0


def test_trace_smoke_reports_otel_bridge_unavailable(tmp_path, monkeypatch):
    _install_stub_spine(tmp_path)
    trace_actions.otel = None
    trace_actions._OTEL_SOURCE = "unavailable"
    trace_actions._OTEL_IMPORT_ERROR = "missing"
    monkeypatch.setattr(
        trace_actions,
        "load_otel_bridge",
        lambda: (None, "unavailable", "missing"),
    )

    paths = _RepoPaths(tmp_path)
    rc = trace_actions.handle_trace_smoke(paths)
    assert rc == 1

    report = json.loads((tmp_path / "state" / "reports" / "trace_smoke.json").read_text("utf-8"))
    assert report["config_enabled"] is True
    assert report["module_available"] is False
    assert report["failure_reason"] == "otel_module_unavailable"


def test_trace_doctor_writes_structured_json_report(tmp_path, monkeypatch):
    _install_stub_spine(tmp_path)
    stub_otel = _StubOtel()
    sys.modules["otel"] = stub_otel
    trace_actions.otel = stub_otel

    paths = _RepoPaths(tmp_path)
    rc = trace_actions.handle_trace_doctor(paths)
    assert rc == 0

    report = json.loads(
        (tmp_path / "state" / "reports" / "trace_doctor.json").read_text(encoding="utf-8")
    )
    assert report["module_available"] is True
    assert report["runtime_enabled"] is True
    assert report["diagnosis"] == "healthy"


def test_collector_health_infers_reachable_when_policy_blocks_socket(monkeypatch):
    monkeypatch.setattr(
        trace_actions,
        "_trace_endpoint_check",
        lambda _endpoint: (False, "unreachable: [Errno 1] Operation not permitted"),
    )
    monkeypatch.setattr(trace_actions, "_is_wsl", lambda: True)
    monkeypatch.setattr(trace_actions, "_is_local_endpoint", lambda _endpoint: True)
    monkeypatch.setattr(
        trace_actions,
        "_trace_endpoint_check_windows",
        lambda _endpoint: (False, "windows_probe unavailable"),
    )

    health = trace_actions._collector_health(
        "http://localhost:4318",
        managed_running=True,
    )
    assert health["reachable"] is True
    assert health["probe_method"] == "inferred-managed-pid"
    assert health["inferred_from_managed_pid"] is True


def test_trace_service_status_uses_inferred_health_when_policy_blocked(tmp_path, monkeypatch):
    _install_stub_spine(tmp_path)
    paths = _RepoPaths(tmp_path)

    pid_path = trace_actions._trace_service_pid_path(tmp_path)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(
        '{"pid": 4242, "started_at": "2026-01-01T00:00:00+00:00"}', encoding="utf-8"
    )

    monkeypatch.setattr(trace_actions, "_pid_alive", lambda pid: pid == 4242)
    monkeypatch.setattr(
        trace_actions,
        "_trace_endpoint_check",
        lambda _endpoint: (
            False,
            "http://localhost:4318 unreachable: [Errno 1] Operation not permitted",
        ),
    )
    monkeypatch.setattr(trace_actions, "_is_wsl", lambda: True)
    monkeypatch.setattr(trace_actions, "_is_local_endpoint", lambda _endpoint: True)
    monkeypatch.setattr(
        trace_actions,
        "_trace_endpoint_check_windows",
        lambda _endpoint: (False, "windows_probe unavailable"),
    )

    rc = trace_actions.handle_trace_service_status(paths)
    assert rc == 0

    report = json.loads(
        (tmp_path / "state" / "reports" / "trace_service_status.json").read_text(encoding="utf-8")
    )
    assert report["reachable"] is True
    assert report["probe_method"] == "inferred-managed-pid"
    assert report["inferred_from_managed_pid"] is True
