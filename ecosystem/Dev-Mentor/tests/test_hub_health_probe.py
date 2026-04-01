from __future__ import annotations

import json
import threading
import time as _time_module
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.hub_health_probe as probe


# ── File I/O ──────────────────────────────────────────────────────────────

def test_read_json_file_missing(tmp_path):
    assert probe._read_json_file(tmp_path / "missing.json") is None


def test_read_json_file_valid(tmp_path):
    path = tmp_path / "status.json"
    path.write_text(json.dumps({"status": "ok"}), encoding="utf-8")
    assert probe._read_json_file(path) == {"status": "ok"}


def test_read_json_file_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{{not-json", encoding="utf-8")
    assert probe._read_json_file(path) is None


def test_read_json_file_empty(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("", encoding="utf-8")
    assert probe._read_json_file(path) is None


# ── HTTP retries ───────────────────────────────────────────────────────────

def test_read_url_retries_then_succeeds(monkeypatch):
    calls = {"count": 0}

    class DummyResponse:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def read(self): return b'{"overall_status": "healthy"}'

    def fake_urlopen(url, timeout=5):
        calls["count"] += 1
        if calls["count"] < 2:
            raise OSError("temporary failure")
        return DummyResponse()

    monkeypatch.setattr(probe, "urlopen", fake_urlopen)
    monkeypatch.setattr(probe.time, "sleep", lambda *_: None)
    assert probe._read_url("http://example.test", attempts=2) == {"overall_status": "healthy"}


def test_read_url_all_retries_fail(monkeypatch):
    monkeypatch.setattr(probe, "urlopen", lambda *_,**__: (_ for _ in ()).throw(OSError("always fails")))
    monkeypatch.setattr(probe.time, "sleep", lambda *_: None)
    assert probe._read_url("http://example.test", attempts=3) is None


def test_read_url_invalid_json_returns_none(monkeypatch):
    class BadResponse:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def read(self): return b"not-json"

    monkeypatch.setattr(probe, "urlopen", lambda *_,**__: BadResponse())
    assert probe._read_url("http://example.test", attempts=1) is None


# ── Heartbeat stale checks ─────────────────────────────────────────────────

def test_heartbeat_stale_on_none():
    assert probe._heartbeat_stale(None) is True


def test_heartbeat_stale_on_missing_details():
    assert probe._heartbeat_stale({}) is True


def test_heartbeat_fresh():
    ts = datetime.now(timezone.utc).isoformat()
    payload = {"details": {"last_heartbeat": ts}}
    assert probe._heartbeat_stale(payload, max_age_seconds=120) is False


def test_heartbeat_old():
    ts = (datetime.now(timezone.utc) - timedelta(seconds=200)).isoformat()
    payload = {"details": {"last_heartbeat": ts}}
    assert probe._heartbeat_stale(payload, max_age_seconds=120) is True


def test_heartbeat_z_suffix_handled():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {"details": {"last_heartbeat": ts}}
    assert probe._heartbeat_stale(payload, max_age_seconds=120) is False


def test_heartbeat_malformed_timestamp():
    payload = {"details": {"last_heartbeat": "not-a-date"}}
    assert probe._heartbeat_stale(payload) is True


# ── ProbeState restart throttling ─────────────────────────────────────────

def test_probe_state_can_restart_initially():
    state = probe.ProbeState()
    assert state.can_restart(_time_module.time()) is True


def test_probe_state_cannot_restart_within_cooldown():
    state = probe.ProbeState()
    now = _time_module.time()
    state.mark_restart(now)
    assert state.can_restart(now + 10) is False


def test_probe_state_can_restart_after_cooldown():
    state = probe.ProbeState()
    # Must be both past cooldown AND past the 1-hour rate limit window
    past = _time_module.time() - max(probe.RESTART_COOLDOWN_SECONDS, 3600) - 1
    state.mark_restart(past)
    assert state.can_restart(_time_module.time()) is True


def test_probe_state_rate_limited_to_max_per_hour():
    state = probe.ProbeState()
    now = _time_module.time()
    for i in range(probe.MAX_RESTARTS_PER_HOUR):
        state.restart_history.append(now - i * 100)
    state.last_restart_at = now - probe.RESTART_COOLDOWN_SECONDS - 1
    assert state.can_restart(now) is False


def test_probe_state_old_history_pruned():
    state = probe.ProbeState()
    now = _time_module.time()
    state.restart_history = [now - 7200, now - 5000]  # both > 1 hour
    state.last_restart_at = now - probe.RESTART_COOLDOWN_SECONDS - 1
    assert state.can_restart(now) is True


# ── Main / daemon ──────────────────────────────────────────────────────────

def test_main_once_calls_probe_once(monkeypatch):
    calls = {"count": 0}

    def fake_probe_once(state):
        calls["count"] += 1
        return 0

    monkeypatch.setattr(probe, "probe_once", fake_probe_once)
    assert probe.main(["--once"]) == 0
    assert calls["count"] == 1


def test_run_daemon_stops_on_signal(monkeypatch):
    stop_event = threading.Event()
    monkeypatch.setattr(probe, "_STOP_EVENT", stop_event)
    monkeypatch.setattr(probe, "_install_signal_handlers", lambda: None)

    calls = {"count": 0}

    def fake_probe_once(state):
        calls["count"] += 1
        stop_event.set()
        return 0

    monkeypatch.setattr(probe, "probe_once", fake_probe_once)
    assert probe.run_daemon(0, probe.ProbeState()) == 0
    assert calls["count"] == 1


def test_main_daemon_flag_calls_run_daemon(monkeypatch):
    calls = {"count": 0}

    def fake_run_daemon(interval, state):
        calls["count"] += 1
        return 0

    monkeypatch.setattr(probe, "run_daemon", fake_run_daemon)
    result = probe.main(["--daemon", "--interval", "1"])
    assert result == 0
    assert calls["count"] == 1


# ── probe_once integration ─────────────────────────────────────────────────

def _healthy_payload():
    ts = datetime.now(timezone.utc).isoformat()
    health = {"overall_status": "healthy", "system": {"status": "running"}}
    status = {"details": {"last_heartbeat": ts}}
    file_st = {"status": "running"}
    return health, status, file_st


def test_probe_once_healthy(monkeypatch, tmp_path):
    health, status, file_st = _healthy_payload()
    log_calls = []

    def fake_read_url(url, **kwargs):
        return health if "health" in url else status

    monkeypatch.setattr(probe, "_read_url", fake_read_url)
    monkeypatch.setattr(probe, "_read_json_file", lambda p: file_st)
    monkeypatch.setattr(probe, "_append_log", lambda r: log_calls.append(r))

    state = probe.ProbeState()
    code = probe.probe_once(state)
    assert code == 0
    assert state.consecutive_failures == 0
    assert log_calls[-1]["healthy"] is True


def test_probe_once_unhealthy_increments_failures(monkeypatch):
    monkeypatch.setattr(probe, "_read_url", lambda *_,**__: None)
    monkeypatch.setattr(probe, "_read_json_file", lambda p: None)
    monkeypatch.setattr(probe, "_append_log", lambda r: None)

    state = probe.ProbeState()
    code = probe.probe_once(state)
    assert code == 1
    assert state.consecutive_failures == 1


def test_probe_once_triggers_restart_at_threshold(monkeypatch):
    monkeypatch.setattr(probe, "_read_url", lambda *_,**__: None)
    monkeypatch.setattr(probe, "_read_json_file", lambda p: None)
    monkeypatch.setattr(probe, "_append_log", lambda r: None)
    monkeypatch.setattr(probe.time, "sleep", lambda *_: None)

    restart_calls = []
    monkeypatch.setattr(probe, "_restart_hub", lambda: restart_calls.append(1) or (True, "ok"))

    state = probe.ProbeState()
    state.consecutive_failures = probe.FAIL_THRESHOLD - 1
    probe.probe_once(state)
    assert len(restart_calls) == 1


def test_probe_once_suppresses_restart_when_rate_limited(monkeypatch):
    monkeypatch.setattr(probe, "_read_url", lambda *_,**__: None)
    monkeypatch.setattr(probe, "_read_json_file", lambda p: None)
    monkeypatch.setattr(probe, "_append_log", lambda r: None)

    restart_calls = []
    monkeypatch.setattr(probe, "_restart_hub", lambda: restart_calls.append(1) or (True, "ok"))

    state = probe.ProbeState()
    now = _time_module.time()
    for _ in range(probe.MAX_RESTARTS_PER_HOUR):
        state.restart_history.append(now - 10)
    state.consecutive_failures = probe.FAIL_THRESHOLD

    probe.probe_once(state)
    assert len(restart_calls) == 0


# ── _restart_hub safety ────────────────────────────────────────────────────

def test_restart_hub_handles_missing_docker(monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *_,**__: (_ for _ in ()).throw(FileNotFoundError("docker")))
    ok, msg = probe._restart_hub()
    assert ok is False
    assert "docker" in msg.lower()


def test_restart_hub_success(monkeypatch):
    import subprocess

    class FakeProc:
        returncode = 0
        stdout = "restarted"
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *_,**__: FakeProc())
    ok, msg = probe._restart_hub()
    assert ok is True
