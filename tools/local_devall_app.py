"""Bounded local DevAll app lifecycle helper."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
STATE_PATH = LOG_DIR / "local_devall_app.json"
STDOUT_LOG = LOG_DIR / "local_devall_app.stdout.log"
STDERR_LOG = LOG_DIR / "local_devall_app.stderr.log"
DEFAULT_PORT = int(os.environ.get("CHATDEV_LOCAL_RUN_PORT", "6400"))
DEFAULT_HOST = os.environ.get("CHATDEV_LOCAL_RUN_HOST", "127.0.0.1")


def _probe_health(base_url: str, timeout: float = 1.0) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        request = Request(f"{base_url.rstrip('/')}/health", headers={"User-Agent": "local-devall-app/1"})
        with urlopen(request, timeout=timeout) as response:
            body = response.read(1024).decode("utf-8", errors="replace")
            payload: dict[str, Any] = {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                "body_preview": body[:240],
            }
            try:
                payload["json"] = json.loads(body)
            except Exception:
                pass
            return payload
    except URLError as exc:
        return {
            "ok": False,
            "error": str(exc.reason if hasattr(exc, "reason") else exc)[:240],
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {str(exc)[:220]}",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }


def _load_state() -> dict[str, Any] | None:
    if not STATE_PATH.exists():
        return None
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_state(payload: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _clear_state() -> None:
    if STATE_PATH.exists():
        STATE_PATH.unlink()


def _is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        completed = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
        return str(pid) in completed.stdout
    except Exception:
        return False


def _python_command() -> list[str]:
    candidates = [
        ROOT / ".venv-gamedev313" / "Scripts" / "python.exe",
        ROOT / ".venv" / "Scripts" / "python.exe",
        Path(sys.executable),
    ]
    for candidate in candidates:
        if candidate.exists():
            return [str(candidate)]
    return ["python"]


def _base_url(host: str, port: int) -> str:
    return f"http://{host}:{port}"


def _wait_for_health(base_url: str, timeout: float) -> dict[str, Any]:
    deadline = time.perf_counter() + max(timeout, 1.0)
    last_probe: dict[str, Any] = {"ok": False, "error": "health_probe_not_run"}
    while time.perf_counter() < deadline:
        last_probe = _probe_health(base_url, timeout=min(1.0, timeout))
        if last_probe.get("ok") is True:
            return last_probe
        time.sleep(0.25)
    return last_probe


def local_status(*, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict[str, Any]:
    state = _load_state()
    base_url = _base_url(host, port)
    health = _probe_health(base_url)
    pid = int(state.get("pid", 0)) if state else 0
    return {
        "root": str(ROOT),
        "managed": state is not None,
        "pid": pid or None,
        "pid_alive": _is_pid_alive(pid) if pid else False,
        "base_url": base_url,
        "health": health,
        "state": state,
    }


def start_local_app(*, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 20.0) -> dict[str, Any]:
    status = local_status(host=host, port=port)
    if status["health"].get("ok") is True:
        return {
            "status": "already_running",
            **status,
        }

    if status["managed"] and not status["pid_alive"]:
        _clear_state()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stdout_handle = STDOUT_LOG.open("a", encoding="utf-8")
    stderr_handle = STDERR_LOG.open("a", encoding="utf-8")
    command = [
        *_python_command(),
        "server_main.py",
        "--host",
        host,
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        command,
        cwd=str(ROOT),
        stdout=stdout_handle,
        stderr=stderr_handle,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creationflags,
    )
    health = _wait_for_health(_base_url(host, port), timeout)
    if health.get("ok") is True:
        state = {
            "pid": process.pid,
            "host": host,
            "port": port,
            "base_url": _base_url(host, port),
            "stdout_log": str(STDOUT_LOG),
            "stderr_log": str(STDERR_LOG),
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "command": command,
        }
        _save_state(state)
        return {
            "status": "started",
            "pid": process.pid,
            "base_url": _base_url(host, port),
            "health": health,
            "state": state,
        }

    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except Exception:
            process.kill()
    return {
        "status": "failed_to_start",
        "pid": process.pid,
        "base_url": _base_url(host, port),
        "health": health,
        "stdout_log": str(STDOUT_LOG),
        "stderr_log": str(STDERR_LOG),
    }


def stop_local_app(*, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 10.0) -> dict[str, Any]:
    status = local_status(host=host, port=port)
    pid = status.get("pid")
    if not pid:
        return {
            "status": "not_managed",
            **status,
        }
    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except Exception as exc:
        return {
            "status": "stop_failed",
            "pid": pid,
            "error": f"{type(exc).__name__}: {exc}",
            **status,
        }

    deadline = time.perf_counter() + max(timeout, 1.0)
    while time.perf_counter() < deadline:
        if not _is_pid_alive(int(pid)):
            break
        time.sleep(0.25)

    _clear_state()
    return {
        "status": "stopped",
        "pid": pid,
        "base_url": _base_url(host, port),
        "health_after_stop": _probe_health(_base_url(host, port)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded local DevAll app lifecycle helper.")
    parser.add_argument("action", choices=["start", "stop", "status"])
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    if args.action == "start":
        payload = start_local_app(host=args.host, port=args.port, timeout=args.timeout)
    elif args.action == "stop":
        payload = stop_local_app(host=args.host, port=args.port, timeout=args.timeout)
    else:
        payload = local_status(host=args.host, port=args.port)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
