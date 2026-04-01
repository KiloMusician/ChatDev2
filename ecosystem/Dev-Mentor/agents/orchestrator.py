#!/usr/bin/env python3
"""
agents/orchestrator.py — Terminal Depths Development Orchestrator

The main controller agent. Reads tasks from tasks/ directory,
delegates to sub-agents, tracks progress, and logs everything.

Usage:
    python3 agents/orchestrator.py             # run one cycle
    python3 agents/orchestrator.py --loop      # run continuously
    python3 agents/orchestrator.py --status    # show current state
    python3 agents/orchestrator.py --task <id> # run specific task
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent
TASKS_DIR = BASE_DIR / "tasks"
FILE_TASKS_DIR = TASKS_DIR / "legacy_runtime"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
AGENTS_DIR = BASE_DIR / "agents"
STATE_DIR = BASE_DIR / "state"
SIMULATEDVERSE_PORT = int(os.environ.get("SIMULATEDVERSE_PORT", "5002"))
SIMULATEDVERSE_HEALTH_URL = os.environ.get(
    "SIMULATEDVERSE_HEALTH_URL",
    f"http://127.0.0.1:{SIMULATEDVERSE_PORT}/api/health",
)
SIMULATEDVERSE_DAEMON = BASE_DIR / "scripts" / "simulatedverse_daemon.sh"

# Allowlist of agent scripts that may be launched via run_agent()
_ALLOWED_AGENTS = frozenset({
    "reflect.py", "analyze_errors.py", "llm_agent.py", "tester.py",
    "documenter.py", "content_generator.py", "implementer.py", "player.py",
    "lore_generator.py", "validator.py", "challenge_generator.py",
})
DEVLOG = BASE_DIR / "devlog.md"

TASKS_DIR.mkdir(exist_ok=True)
FILE_TASKS_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_DIR.mkdir(exist_ok=True)


def log(level: str, msg: str, **ctx):
    ts = time.strftime("%H:%M:%S")
    colors = {"INFO": "\033[36m", "OK": "\033[32m", "WARN": "\033[33m",
              "ERROR": "\033[31m", "TASK": "\033[35m"}
    c = colors.get(level, "\033[0m")
    r = "\033[0m"
    kv = "  ".join(f"{k}={v}" for k, v in ctx.items())
    print(f"{c}[{level}]{r} {ts} {msg}" + (f"  | {kv}" if kv else ""))


def write_devlog(entry: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(DEVLOG, "a") as f:
        f.write(f"\n## {ts}\n{entry}\n")


def list_pending_tasks() -> List[dict]:
    tasks = []
    for path in sorted(FILE_TASKS_DIR.glob("*.json")):
        try:
            with open(path) as f:
                task = json.load(f)
            if not isinstance(task, dict):
                continue
            if not any(task.get(key) for key in ("title", "details", "agent")):
                continue
            if task.get("status") in ("pending", None):
                tasks.append({**task, "_path": str(path)})
        except Exception:
            pass
    return tasks


def mark_task(path: str, status: str, result: str = ""):
    with open(path) as f:
        task = json.load(f)
    task["status"] = status
    task["result"] = result
    task["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(path, "w") as f:
        json.dump(task, f, indent=2)


def create_task(title: str, agent: str, details: str, priority: int = 5) -> str:
    tid = f"task_{int(time.time())}_{title[:20].replace(' ','_')}"
    path = FILE_TASKS_DIR / f"{tid}.json"
    with open(path, "w") as f:
        json.dump({
            "id": tid,
            "title": title,
            "agent": agent,
            "details": details,
            "priority": priority,
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }, f, indent=2)
    log("TASK", f"Created: {title}", agent=agent)
    return tid


_SAFE_ARG_RE = re.compile(r'^(?:--?[\w\-]+|[\w\-./]+)$')


def _validate_args(args: List[str]) -> List[str]:
    """Validate subprocess args are safe CLI tokens (flag or alphanumeric path).
    Rejects anything that could be used for shell injection. Only reaches here
    from internal callers — not from user HTTP input — but we validate anyway."""
    return [a for a in args if _SAFE_ARG_RE.match(str(a))]


def run_agent(agent_script: str, args: List[str] = []) -> dict:
    """Run a sub-agent script and capture output."""
    if agent_script not in _ALLOWED_AGENTS:
        return {"ok": False, "error": f"Unknown agent: {agent_script!r}"}
    script_path = AGENTS_DIR / agent_script
    if not script_path.exists():
        return {"ok": False, "error": f"Agent {agent_script} not found"}

    safe_args = _validate_args(args)
    try:
        # nosec B603 — shell=False (list form); script_path is from AGENTS_DIR
        # allowlist; args validated by _validate_args against safe token pattern.
        result = subprocess.run(  # nosec B603
            [sys.executable, str(script_path)] + safe_args,
            capture_output=True, text=True, timeout=240, cwd=str(BASE_DIR)
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Agent timed out"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run_playtest(quick: bool = False) -> dict:
    """Run the automated playtest suite."""
    args = ["--quick"] if quick else []
    result = subprocess.run(  # nosec B603
        [sys.executable, str(BASE_DIR / "playtest.py")] + args,
        capture_output=True, text=True, timeout=360, cwd=str(BASE_DIR)
    )
    lines = result.stdout.strip().split("\n")
    total_line = next((l for l in lines if "TOTAL:" in l), "unknown")
    return {
        "ok": result.returncode == 0,
        "summary": total_line.strip(),
        "output": result.stdout,
    }


def run_local_script(rel_path: str, args: List[str] | None = None, timeout: int = 360) -> dict:
    script = BASE_DIR / rel_path
    if not script.exists():
        return {"ok": False, "error": f"Missing script: {rel_path}"}
    cmd = [sys.executable, str(script)] + (args or [])
    try:
        result = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(BASE_DIR),
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_server() -> dict:
    """Check if the game server is running."""
    try:
        with urllib.request.urlopen("http://localhost:8008/api/health", timeout=6) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_url_json(url: str, timeout: int = 6) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return {
                "ok": True,
                "status": getattr(r, "status", 200),
                "body": json.loads(r.read()),
            }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ensure_simulatedverse() -> dict:
    health = check_url_json(SIMULATEDVERSE_HEALTH_URL)
    if health.get("ok"):
        return {"ok": True, "restarted": False}

    if not SIMULATEDVERSE_DAEMON.exists():
        return {"ok": False, "error": f"Missing daemon script: {SIMULATEDVERSE_DAEMON}"}

    try:
        subprocess.run(  # nosec B603
            ["bash", str(SIMULATEDVERSE_DAEMON)],
            capture_output=True,
            text=True,
            timeout=40,
            cwd=str(BASE_DIR),
            check=False,
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}

    for _ in range(30):
        time.sleep(1)
        health = check_url_json(SIMULATEDVERSE_HEALTH_URL)
        if health.get("ok"):
            return {"ok": True, "restarted": True}
    return {"ok": False, "error": "SimulatedVerse did not become healthy after daemon launch"}


def _hub_health_probe_log() -> Path:
    return STATE_DIR / "runtime" / "hub_health_probe.jsonl"


def read_latest_hub_health_probe() -> dict | None:
    """Return the newest probe record if the health listener has produced one."""
    probe_log = _hub_health_probe_log()
    if not probe_log.exists():
        return None

    try:
        lines = [line.strip() for line in probe_log.read_text(encoding="utf-8").splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            return None
        return json.loads(lines[-1])
    except Exception:
        return None


def generate_status_report() -> dict:
    """Generate a status report from knowledge base."""
    report = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "status": {}}

    # Check last playtest
    pt_file = KNOWLEDGE_DIR / "last_playtest.json"
    if pt_file.exists():
        with open(pt_file) as f:
            report["last_playtest"] = json.load(f)

    # Count pending tasks
    pending = list_pending_tasks()
    report["pending_tasks"] = len(pending)
    report["tasks"] = [{"title": t.get("title"), "agent": t.get("agent")} for t in pending[:5]]

    # Server status
    server = check_server()
    report["server"] = server

    return report


def cycle(verbose: bool = False):
    """Run one orchestration cycle."""
    log("INFO", "=== Orchestrator Cycle Start ===")

    # 1. Check server health
    health = check_server()
    if not health.get("ok"):
        log("WARN", "Server not running", error=health.get("error", ""))
        write_devlog("⚠ Server down during orchestration cycle")
        return

    log("OK", "Server healthy", sessions=health.get("active_game_sessions", 0))

    simverse = ensure_simulatedverse()
    if simverse.get("ok"):
        if simverse.get("restarted"):
            log("OK", "SimulatedVerse recovered via daemon launcher", port=SIMULATEDVERSE_PORT)
        else:
            log("OK", "SimulatedVerse healthy", port=SIMULATEDVERSE_PORT)
    else:
        log("WARN", "SimulatedVerse unavailable", error=simverse.get("error", "unknown"))

    # 2. Run quick playtest
    log("INFO", "Running quick playtest...")
    pt = run_playtest(quick=True)
    log("OK" if pt["ok"] else "WARN", f"Playtest: {pt['summary']}")

    # 2b. Serena cycle — keep the convergence layer current
    serena_mode = "full" if not (STATE_DIR / "serena_status.json").exists() else "scoped"
    serena = run_local_script("scripts/serena_cycle.py", ["--mode", serena_mode], timeout=600)
    if serena["ok"]:
        log("OK", "Serena cycle complete", mode=serena_mode)
        try:
            serena_status = json.loads(serena["stdout"].strip())
            align_score = float(serena_status.get("align", {}).get("score", 0.0))
            if align_score < 0.85:
                create_task(
                    title="Heal Serena alignment drift",
                    agent="implementer.py",
                    details=f"Alignment dropped to {align_score:.2f}. Review state/serena_status.json and resolve drift.",
                    priority=1,
                )
                log("WARN", "Serena alignment below threshold", score=align_score)
        except Exception:
            pass
    else:
        log("WARN", "Serena cycle failed", error=serena.get("error") or serena.get("stderr", "")[:120])

    # 3. Process pending tasks
    tasks = list_pending_tasks()
    hub_critical = False
    hub_reason = "healthy"
    hub_drift_flags: list[str] = []
    hub_listener = run_local_script("scripts/health_listener.py", ["--once"], timeout=60)
    if hub_listener["ok"]:
        try:
            hub_status = json.loads(hub_listener["stdout"].strip())
            if hub_status.get("ok") is False:
                hub_reason = str(hub_status.get("reason") or "unknown")
                log("WARN", "Hub health listener unavailable or stale", reason=hub_reason)
            else:
                hub_critical = bool(hub_status.get("critical"))
                hub_reason = str(hub_status.get("reason") or "healthy")
                hub_drift_flags = list(hub_status.get("drift_flags") or [])
                if hub_critical:
                    log("WARN", "Hub health listener marked Hub critical", reason=hub_reason)
                else:
                    log("OK", "Hub health listener clear", reason=hub_reason)
        except Exception:
            log("WARN", "Hub health listener returned invalid payload")
    else:
        hub_probe = read_latest_hub_health_probe()
        hub_critical = bool(hub_probe and hub_probe.get("healthy") is False)
        hub_drift_flags = list((hub_probe or {}).get("drift_flags", []))
        if hub_critical:
            log("WARN", "Hub health probe fallback marked Hub unhealthy", drift_flags=hub_drift_flags)

    if tasks and not hub_critical:
        log("TASK", f"Processing {len(tasks)} pending tasks...")
        for task in tasks[:3]:  # Process up to 3 per cycle
            log("TASK", f"→ {task['title']}", agent=task.get("agent", "?"))
            task_type = task.get("type", "")
            if task_type == "spawn_agent":
                # Route spawn_agent tasks through dispatch_task.py
                result = run_local_script(
                    "scripts/dispatch_task.py",
                    ["--task", task["id"]],
                    timeout=60,
                )
            else:
                agent = task.get("agent", "tester.py")
                result = run_agent(agent, ["--task", task["id"]])
            status = "done" if result["ok"] else "failed"
            mark_task(task["_path"], status, result.get("stdout", "")[:200])
            log("OK" if result["ok"] else "ERROR", f"Task {status}: {task['title']}")
    elif tasks:
        log(
            "WARN",
            "Hub health listener reports critical drift; skipping pending task execution",
            drift_flags=hub_drift_flags,
        )
    else:
        log("INFO", "No pending tasks")

    # 3b. Fold agent outputs back into state + queue
    watcher = run_local_script("scripts/agent_output_watcher.py", ["--once"], timeout=120)
    if watcher["ok"]:
        log("OK", "Agent output watcher synced state")
    else:
        log("WARN", "Agent output watcher failed", error=watcher.get("error") or watcher.get("stderr", "")[:120])

    # 4. Run content agent for variety
    content_result = run_agent("content_generator.py", ["--batch", "3"])
    if content_result["ok"]:
        log("OK", "Content generator ran", lines=content_result.get("stdout", "").count("\n"))

    # 5. Update devlog
    report = generate_status_report()
    entry = (
        f"**Cycle complete**\n"
        f"- Server: {'✓ up' if health.get('ok') else '✗ down'}\n"
        f"- Playtest: {pt['summary']}\n"
        f"- Tasks pending: {len(tasks)}\n"
    )
    write_devlog(entry)

    log("INFO", "=== Orchestrator Cycle Complete ===")


def show_status():
    """Print current orchestrator status."""
    print("\n=== ORCHESTRATOR STATUS ===")
    server = check_server()
    print(f"Server: {'✓ UP' if server.get('ok') else '✗ DOWN'}")
    if server.get("ok"):
        print(f"  sessions: {server.get('active_game_sessions', 0)}")
        print(f"  uptime:   {server.get('uptime_s', 0)}s")

    tasks = list_pending_tasks()
    print(f"\nPending tasks: {len(tasks)}")
    for t in tasks[:5]:
        print(f"  [{t.get('priority', 5)}] {t.get('title', '?')} ({t.get('agent', '?')})")

    pt_file = KNOWLEDGE_DIR / "last_playtest.json"
    if pt_file.exists():
        with open(pt_file) as f:
            pt = json.load(f)
        print(f"\nLast playtest: {pt.get('timestamp', '?')}")
        print(f"  {pt.get('total_pass', 0)}/{pt.get('total_pass', 0)+pt.get('total_fail', 0)} passed")
    print()


def main():
    parser = argparse.ArgumentParser(description="Terminal Depths Orchestrator Agent")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--task", help="Run specific task ID")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--interval", type=int, default=300, help="Loop interval seconds")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.task:
        # Directly dispatch a single task by ID (used by tests and CI)
        tasks = list_pending_tasks()
        task = next((t for t in tasks if t.get("id") == args.task), None)
        if not task:
            log("ERROR", f"Task not found: {args.task}")
            return
        task_type = task.get("type", "")
        if task_type == "spawn_agent":
            result = run_local_script("scripts/dispatch_task.py", ["--task", args.task], timeout=60)
        else:
            agent = task.get("agent", "tester.py")
            result = run_agent(agent, ["--task", args.task])
        status = "done" if result["ok"] else "failed"
        mark_task(task["_path"], status, result.get("stdout", "")[:200])
        log("OK" if result["ok"] else "ERROR", f"Task {status}: {task['title']}")
        return

    if args.loop:
        log("INFO", f"Starting orchestration loop (interval={args.interval}s)")
        while True:
            try:
                cycle(verbose=args.verbose)
            except KeyboardInterrupt:
                log("INFO", "Loop interrupted by user")
                break
            except Exception as e:
                log("ERROR", f"Cycle failed: {e}")
            time.sleep(args.interval)
    else:
        cycle(verbose=args.verbose)


if __name__ == "__main__":
    main()
