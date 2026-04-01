#!/usr/bin/env python3
"""Unified stack bring-up for NuSyQ-Hub.

Starts (mostly in background):
1) Terminal API (uvicorn) so category terminals are reachable.
2) Intelligent terminal presets/registry (init_terminal.py) – foreground, quick.
3) Critical services bundle (start_all_critical_services.py) – orchestrator, PU queue, guild board renderer, quest sync, trace, etc.
4) Developer workflow orchestrator in watch mode (lint/test/build triggers).

Outputs PID + log locations so agents and humans can tail them.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "data" / "service_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def spawn(name: str, cmd: list[str], log_name: str) -> int:
    """Start a background process with stdout/err to a log file, skipping if already running from prior log."""
    log_path = LOG_DIR / log_name
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Soft duplicate guard: if log has a pid line, check it.
    if log_path.exists():
        for line in log_path.read_text().splitlines()[:5]:
            if "pid=" in line:
                try:
                    existing = int(line.split("pid=")[1].split()[0])
                    if pid_running(existing):
                        print(f"[SKIP] {name:<24} already running pid={existing}")
                        return existing
                except Exception:
                    pass

    with open(log_path, "a", buffering=1) as f:
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=f,
            stderr=subprocess.STDOUT,
        )
    print(f"[STARTED] {name:<24} pid={proc.pid} log={log_path}")
    return proc.pid


def run_fg(name: str, cmd: list[str]) -> int:
    """Run a quick foreground step (non-daemon)."""
    print(f"[RUN] {name} ...")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode == 0:
        print(f"[OK] {name}")
    else:
        print(f"[FAIL] {name} rc={result.returncode}")
    return result.returncode


def status_only() -> None:
    print("Service status (best-effort from logs):")
    for name, log_name in [
        ("terminal_api", "terminal_api.log"),
        ("critical_services", "critical_services.log"),
        ("dev_workflow_orchestrator", "dev_workflow_orchestrator.log"),
        ("trace_service", "trace_service.log"),
    ]:
        log_path = LOG_DIR / log_name
        pid = None
        if log_path.exists():
            for line in log_path.read_text().splitlines():
                if "pid=" in line:
                    try:
                        pid = int(line.split("pid=")[1].split()[0])
                        break
                    except Exception:
                        pass
        if pid is None:
            print(f" - {name}: no pid recorded (log: {log_path})")
        else:
            alive = pid_running(pid)
            print(f" - {name}: pid={pid} alive={alive} log={log_path}")


def _kill_pid(pid: int, label: str) -> None:
    try:
        os.kill(pid, 9)
        print(f"[KILLED] {label:<24} pid={pid}")
    except Exception as exc:
        print(f"[WARN] could not kill {label} pid={pid}: {exc}")


def clean() -> None:
    """Terminate known background services to avoid duplicate pile-ups."""
    print("Cleaning background services (pid + pattern based)...")

    # First, kill PIDs recorded in logs
    for name, log_name in [
        ("terminal_api", "terminal_api.log"),
        ("critical_services", "critical_services.log"),
        ("dev_workflow_orchestrator", "dev_workflow_orchestrator.log"),
        ("trace_service", "trace_service.log"),
    ]:
        log_path = LOG_DIR / log_name
        if not log_path.exists():
            continue
        for line in log_path.read_text().splitlines():
            if "pid=" in line:
                try:
                    pid = int(line.split("pid=")[1].split()[0])
                    if pid_running(pid):
                        _kill_pid(pid, name)
                except Exception:
                    continue

    # Fallback: kill by common process name patterns to catch leftovers
    patterns = [
        "start_multi_ai_orchestrator.py",
        "pu_queue_runner.py",
        "dev_workflow_orchestrator.py",
        "trace_service.py",
    ]
    try:
        out = subprocess.check_output(["ps", "-ef"], text=True)
    except Exception:
        out = ""
    for line in out.splitlines():
        if any(pat in line for pat in patterns) and "grep" not in line:
            parts = line.split()
            if parts:
                try:
                    pid = int(parts[1])
                    _kill_pid(pid, "process_match")
                except Exception:
                    continue


def main() -> None:
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in {"status", "--status", "-s"}:
            status_only()
            return
        if arg in {"clean", "reset"}:
            clean()
            return
        if arg in {"relaunch", "restart"}:
            clean()
            # Fall through to normal launch

    # Force OTLP HTTP env for spawned services
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://127.0.0.1:4318/v1/traces"
    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "http://127.0.0.1:4318/v1/traces"
    os.environ["OTEL_EXPORTER_OTLP_PROTOCOL"] = "http/protobuf"
    os.environ["OTEL_EXPORTER_OTLP_TRACES_PROTOCOL"] = "http/protobuf"

    py = sys.executable

    # 1) Terminal API (keeps intelligent terminals reachable)
    spawn(
        "terminal_api",
        [py, "scripts/start_nusyq.py", "terminal_api"],
        "terminal_api.log",
    )

    # 2) Initialize terminal registry/presets (fast, blocking)
    run_fg("init_terminal_presets", [py, "src/system/init_terminal.py"])

    # 3) Critical services bundle (orchestrator, pu_queue, guild renderer, trace, etc.)
    spawn(
        "critical_services",
        [py, "scripts/start_all_critical_services.py", "start"],
        "critical_services.log",
    )

    # 3b) Trace service placeholder (until real collector wired)
    spawn(
        "trace_service",
        [py, "scripts/trace_service.py"],
        "trace_service.log",
    )

    # 4) Dev workflow orchestrator in watch mode (polling or watchdog)
    spawn(
        "dev_workflow_orchestrator",
        [
            py,
            "scripts/dev_workflow_orchestrator.py",
            "--config",
            "config/dev_orchestrator.json",
            "--watch",
        ],
        "dev_workflow_orchestrator.log",
    )

    print("\nDone. Tail logs in data/service_logs/. Use `ps -p <pid>` to confirm health.")


if __name__ == "__main__":
    main()
