#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

BASE = Path("/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub")
COMPOSE_FILE = BASE / "deploy" / "docker-compose.dev.yml"
STATUS_FILE = BASE / "state" / "system_status.json"
LOG_FILE = Path("/mnt/c/Users/keath/Dev-Mentor/state/runtime/hub_health_probe.jsonl")
HEALTH_URL = "http://localhost:8000/api/health"
STATUS_URL = "http://localhost:8000/api/status"
FAIL_THRESHOLD = 3
RESTART_COOLDOWN_SECONDS = 300
MAX_RESTARTS_PER_HOUR = 1
READ_RETRIES = 3
READ_RETRY_BACKOFF_SECONDS = 0.5
_STOP_EVENT = threading.Event()


def _now() -> datetime:
    return datetime.now(UTC)


def _ts() -> str:
    return _now().isoformat()


def _read_json_file(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_url(url: str, timeout: int = 10, attempts: int = READ_RETRIES) -> dict | None:
    for attempt in range(max(1, attempts)):
        try:
            with urlopen(url, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            if attempt >= max(1, attempts) - 1:
                return None
            time.sleep(READ_RETRY_BACKOFF_SECONDS * (attempt + 1))
    return None


def _heartbeat_stale(status_payload: dict | None, max_age_seconds: int = 120) -> bool:
    if not status_payload:
        return True
    details = status_payload.get("details") or {}
    stamp = details.get("last_heartbeat")
    if not stamp:
        return True
    try:
        dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except Exception:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return (_now() - dt).total_seconds() > max_age_seconds


def _append_log(record: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")


@dataclass
class ProbeState:
    consecutive_failures: int = 0
    restart_history: list[float] | None = None
    last_restart_at: float | None = None

    def __post_init__(self) -> None:
        if self.restart_history is None:
            self.restart_history = []

    def can_restart(self, now: float) -> bool:
        self.restart_history = [t for t in self.restart_history if now - t <= 3600]
        if (
            self.last_restart_at
            and now - self.last_restart_at < RESTART_COOLDOWN_SECONDS
        ):
            return False
        return len(self.restart_history) < MAX_RESTARTS_PER_HOUR

    def mark_restart(self, now: float) -> None:
        self.last_restart_at = now
        self.restart_history.append(now)


def _restart_hub() -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "restart", "nusyq-hub"],
            cwd=str(BASE),
            capture_output=True,
            text=True,
            timeout=240,
            check=False,
        )
    except Exception as exc:
        return False, str(exc)
    output = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, output


def probe_once(state: ProbeState) -> int:
    now = time.time()
    api_health = _read_url(HEALTH_URL)
    api_status = _read_url(STATUS_URL)
    file_status = _read_json_file(STATUS_FILE)

    drift_flags: list[str] = []
    overall_status = (api_health or {}).get("overall_status")
    api_system = (api_health or {}).get("system") or {}
    api_status_value = api_system.get("status")
    file_status_value = (file_status or {}).get("status")

    if api_health is None:
        drift_flags.append("api_health_unreachable")
    if api_status is None:
        drift_flags.append("api_status_unreachable")
    if file_status is None:
        drift_flags.append("status_file_missing")
    if overall_status in {None, "unknown"}:
        drift_flags.append("overall_status_unknown")
    if api_status_value and file_status_value and api_status_value != file_status_value:
        drift_flags.append("status_mismatch")
    if _heartbeat_stale(api_status):
        drift_flags.append("heartbeat_stale")

    healthy = len(drift_flags) == 0
    if healthy:
        state.consecutive_failures = 0
    else:
        state.consecutive_failures += 1

    record = {
        "ts": _ts(),
        "healthy": healthy,
        "consecutive_failures": state.consecutive_failures,
        "drift_flags": drift_flags,
        "api_health": api_health,
        "api_status": api_status,
        "file_status": file_status,
    }

    if state.consecutive_failures >= FAIL_THRESHOLD:
        if state.can_restart(now):
            ok, output = _restart_hub()
            state.mark_restart(now)
            record["restart_attempted"] = True
            record["restart_ok"] = ok
            record["restart_output"] = output
            time.sleep(10)
            record["post_restart_health"] = _read_url(HEALTH_URL)
            if record["post_restart_health"] is None:
                record["manual_intervention_required"] = True
        else:
            record["restart_suppressed"] = True
            record["manual_intervention_required"] = True

    _append_log(record)
    return 0 if healthy else 1


def _install_signal_handlers() -> None:
    def _handle_signal(signum, frame):
        _STOP_EVENT.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handle_signal)
        except Exception:
            continue


def run_daemon(interval: int, state: ProbeState) -> int:
    _STOP_EVENT.clear()
    _install_signal_handlers()
    while not _STOP_EVENT.is_set():
        probe_once(state)
        if _STOP_EVENT.wait(interval):
            break
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Probe NuSyQ-Hub health and restart conservatively on sustained drift."
    )
    parser.add_argument(
        "--interval", type=int, default=30, help="Loop interval in seconds"
    )
    parser.add_argument(
        "--once", action="store_true", help="Run a single probe and exit"
    )
    parser.add_argument(
        "--daemon", action="store_true", help="Run continuously until signalled"
    )
    args = parser.parse_args(argv)

    state = ProbeState()
    if args.once:
        return probe_once(state)

    return run_daemon(args.interval, state)


if __name__ == "__main__":
    raise SystemExit(main())
