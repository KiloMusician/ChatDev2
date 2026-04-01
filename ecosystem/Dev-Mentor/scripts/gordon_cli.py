#!/usr/bin/env python3
"""Gordon CLI — The god-mode command-line interface for the Terminal Depths Lattice.

Usage:
    python scripts/gordon_cli.py <command> [options]
    (or symlink as 'gordon' on PATH)

Commands:
    gordon status [--watch]
    gordon cascade start | status | stop
    gordon workflow rimworld | chatdev | blueprint | hackathon
    gordon ask <agent> "<question>"
    gordon exec <agent> "<command>"
    gordon task add "<description>" --priority P0|P1|P2
    gordon task list [--filter incomplete|complete|p0|p1|p2]
    gordon logs [--follow] [--service <name>]
    gordon scale <service> <count>
    gordon seed-lattice
    gordon health
    gordon council vote "<proposal>"
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Optional

# ── optional deps ─────────────────────────────────────────────────────────────
try:
    import requests as _req

    REQUESTS_OK = True
except ImportError:
    _req = None
    REQUESTS_OK = False

try:
    import redis as _redis_lib

    _redis = _redis_lib.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
    )
    _redis.ping()
    REDIS_OK = True
except Exception:
    _redis = None
    REDIS_OK = False

try:
    import typer

    _typer_ok = True
except ImportError:
    typer = None  # type: ignore
    _typer_ok = False

# ── config ────────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent
STATE_DIR = BASE / "state"
LOG_DIR = BASE / "var"
TODO_FILE = BASE / "MASTER_ZETA_TODO.md"
_REPLIT_NATIVE = bool(os.getenv("REPLIT_DEV_DOMAIN")) and not os.getenv(
    "GORDON_DOCKER_HOST"
)
TD_URL = os.getenv("TERMINAL_DEPTHS_URL") or (
    "http://localhost:5000" if _REPLIT_NATIVE else "http://localhost:8008"
)
GORDON_SESSION = "gordon-cli-session"

LOG_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# ANSI colours
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

SERVICES = [
    {"name": "Terminal Depths", "url": f"{TD_URL}/api/health", "key": "td"},
    {"name": "Lattice API", "url": f"{TD_URL}/api/lattice/stats", "key": "lattice"},
    {"name": "NuSyQ Manifest", "url": f"{TD_URL}/api/nusyq/manifest", "key": "nusyq"},
    {"name": "MCP Server", "url": f"{TD_URL}/api/mcp/tools", "key": "mcp"},
]

WORKFLOWS = {
    "rimworld": "Start the RimWorld integration (VNC container + mod activation)",
    "blueprint": "Run genetic algorithm to evolve new base layouts",
    "chatdev": "Initiate a ChatDev multi-agent code generation session",
    "hackathon": "One-hour event: all agents collaborate on a chosen task",
    "chug": "Trigger a CHUG engine autonomous improvement cycle",
    "skyclaw": "Run a full SkyClaw filesystem + colony + crash scan",
}

AGENT_IDS = ["ada", "raven", "nova", "cypher", "watcher", "serena", "gordon", "zero"]

# ── helpers ───────────────────────────────────────────────────────────────────


def _get(path: str, timeout: int = 5) -> dict | None:
    if not REQUESTS_OK:
        return None
    try:
        r = _req.get(f"{TD_URL}{path}", timeout=timeout)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return None


def _post(path: str, body: dict, timeout: int = 10) -> dict | None:
    if not REQUESTS_OK:
        return None
    try:
        r = _req.post(f"{TD_URL}{path}", json=body, timeout=timeout)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return None


def _publish(channel: str, payload: dict):
    if REDIS_OK and _redis:
        try:
            _redis.publish(channel, json.dumps(payload))
        except Exception:
            pass


def _print_header(title: str):
    width = 56
    bar = "═" * width
    print(f"\n{BOLD}{CYAN}╔{bar}╗")
    print(f"║  {title:<{width-2}}║")
    print(f"╚{bar}╝{RESET}\n")


def _ok(msg: str):
    print(f"  {GREEN}✓{RESET}  {msg}")


def _warn(msg: str):
    print(f"  {YELLOW}⚠{RESET}  {msg}")


def _err(msg: str):
    print(f"  {RED}✗{RESET}  {msg}")


def _info(msg: str):
    print(f"  {CYAN}»{RESET}  {msg}")


def _dim(msg: str):
    print(f"  {DIM}{msg}{RESET}")


def _docker_available() -> bool:
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return False
    try:
        result = subprocess.run(
            [docker_bin, "info"],
            capture_output=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def _parse_todo() -> list[dict]:
    """Parse MASTER_ZETA_TODO.md into a list of task dicts."""
    if not TODO_FILE.exists():
        return []
    tasks = []
    current_priority = "P2"
    for line in TODO_FILE.read_text().splitlines():
        m = re.match(r"^##\s+P(\d)", line)
        if m:
            current_priority = f"P{m.group(1)}"
            continue
        m = re.match(r"^- \[([ x])\]\s+\*\*(\w+)\*\*:\s+(.+)", line)
        if m:
            done = m.group(1) == "x"
            task_id = m.group(2)
            description = m.group(3).split("—")[0].strip()
            tasks.append(
                {
                    "id": task_id,
                    "priority": current_priority,
                    "done": done,
                    "description": description,
                    "raw": line,
                }
            )
    return tasks


def _append_todo(description: str, priority: str, task_id: str):
    """Append a new task to MASTER_ZETA_TODO.md under the correct priority section."""
    if not TODO_FILE.exists():
        TODO_FILE.write_text(f"# MASTER ZETA TODO LIST\n\n## {priority} — ADDED\n\n")
    content = TODO_FILE.read_text()
    new_line = f"- [ ] **{task_id}**: {description}\n"
    # Find the right section header
    target = f"## {priority}"
    if target in content:
        idx = content.index(target)
        # Insert after the section header line
        line_end = content.index("\n", idx) + 1
        content = content[:line_end] + "\n" + new_line + content[line_end:]
    else:
        content += f"\n## {priority} — ADDED BY GORDON CLI\n\n{new_line}\n"
    TODO_FILE.write_text(content)


# ══════════════════════════════════════════════════════════════════════════════
# STATUS
# ══════════════════════════════════════════════════════════════════════════════


def cmd_status(watch: bool = False, interval: int = 5):
    """Show status of all services and agents."""

    def _once():
        _print_header("GORDON STATUS — LATTICE ECOSYSTEM")

        # API services
        print(f"  {BOLD}Services{RESET}")
        for svc in SERVICES:
            data = _get(svc["url"].replace(TD_URL, ""))
            if data is not None:
                extra = ""
                if svc["key"] == "td":
                    extra = f"  sessions={data.get('active_game_sessions', '?')}"
                elif svc["key"] == "lattice":
                    extra = f"  nodes={data.get('nodes','?')}  edges={data.get('edges','?')}"
                _ok(f"{svc['name']:<20}{DIM}{extra}{RESET}")
            else:
                _err(f"{svc['name']:<20}{DIM}unreachable{RESET}")

        # Redis
        print()
        print(f"  {BOLD}Message Bus{RESET}")
        if REDIS_OK:
            try:
                info = _redis.info("server")
                ver = info.get("redis_version", "?")
                _ok(f"Redis {ver:<20}{DIM}pub/sub ready{RESET}")
            except Exception:
                _warn("Redis  (connected but info failed)")
        else:
            _err("Redis  not reachable — inter-agent messaging disabled")

        # Docker
        print()
        print(f"  {BOLD}Docker Containers{RESET}")
        if _docker_available():
            try:
                result = subprocess.run(
                    ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                keywords = [
                    "lattice",
                    "kilocore",
                    "gordon",
                    "serena",
                    "culture",
                    "chatdev",
                    "skyclaw",
                    "rimworld",
                    "redis",
                    "ollama",
                    "model-router",
                    "dev-mentor",
                    "nusyq-hub",
                    "simulatedverse",
                ]
                lines = [
                    l
                    for l in result.stdout.strip().splitlines()
                    if any(k in l for k in keywords)
                ]
                if lines:
                    for l in lines:
                        parts = l.split("\t")
                        name = parts[0] if len(parts) > 0 else "?"
                        status = parts[1] if len(parts) > 1 else "?"
                        color = GREEN if "Up" in status else RED
                        print(f"  {color}●{RESET} {name:<30}{DIM}{status}{RESET}")
                else:
                    _dim("No Lattice containers found — run 'gordon cascade start'")
            except Exception as e:
                _warn(f"Docker query failed: {e}")
        else:
            _dim("Docker not available — container status skipped")

        # Task summary
        tasks = _parse_todo()
        total = len(tasks)
        done = sum(1 for t in tasks if t["done"])
        p0 = sum(1 for t in tasks if not t["done"] and t["priority"] == "P0")
        print()
        print(f"  {BOLD}Task Queue{RESET}")
        _info(
            f"MASTER ZETA TODO  {done}/{total} complete   {RED}{p0} P0 outstanding{RESET}"
        )

        print()

    if watch:
        try:
            while True:
                os.system("clear")
                _once()
                print(f"  {DIM}Refreshing every {interval}s — Ctrl+C to stop{RESET}")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nGordon status watch stopped.")
    else:
        _once()


# ══════════════════════════════════════════════════════════════════════════════
# CASCADE
# ══════════════════════════════════════════════════════════════════════════════


def cmd_cascade_start(dry_run: bool = False):
    """Scan MASTER_ZETA_TODO.md and dispatch all uncompleted tasks."""
    _print_header("GORDON CASCADE — INITIALIZING")

    tasks = _parse_todo()
    pending = [t for t in tasks if not t["done"]]
    p0 = [t for t in pending if t["priority"] == "P0"]
    p1 = [t for t in pending if t["priority"] == "P1"]
    p2 = [t for t in pending if t["priority"] == "P2"]

    _info(f"Scanned {TODO_FILE.name}: {len(tasks)} total, {len(pending)} pending")
    _info(f"  P0={len(p0)}  P1={len(p1)}  P2={len(p2)}")
    print()

    dispatched = 0
    for priority_group in [p0, p1, p2]:
        for task in priority_group:
            action = "DISPATCH" if not dry_run else "DRY-RUN"
            _dim(
                f"  [{action}] [{task['priority']}] {task['id']}: {task['description'][:60]}"
            )
            if not dry_run:
                _publish(
                    "lattice.task.created",
                    {
                        "task_id": task["id"],
                        "priority": task["priority"],
                        "description": task["description"],
                        "source": "gordon-cascade",
                        "ts": datetime.now(UTC).isoformat(),
                    },
                )
            dispatched += 1

    print()
    if dry_run:
        _info(f"Dry run complete: {dispatched} tasks would be dispatched")
    else:
        _ok(f"Cascade started: {dispatched} tasks published to Lattice bus")
        _info("Watch progress:  gordon logs --follow")
        _info("Monitor status:  gordon status --watch")

    # Publish cascade start event
    if not dry_run:
        _publish(
            "lattice.cascade.started",
            {
                "total_tasks": dispatched,
                "ts": datetime.now(UTC).isoformat(),
            },
        )


def cmd_cascade_status():
    """Show current cascade progress."""
    _print_header("CASCADE STATUS")
    tasks = _parse_todo()
    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    pct = int(done / total * 100) if total else 0
    bar_w = 40
    filled = int(bar_w * pct / 100)
    bar = "█" * filled + "░" * (bar_w - filled)
    print(f"  [{bar}] {pct}%")
    print(f"  {done}/{total} tasks complete\n")
    by_p = {}
    for t in tasks:
        by_p.setdefault(t["priority"], {"done": 0, "total": 0})
        by_p[t["priority"]]["total"] += 1
        if t["done"]:
            by_p[t["priority"]]["done"] += 1
    for p, counts in sorted(by_p.items()):
        c = GREEN if counts["done"] == counts["total"] else YELLOW
        print(f"  {c}{p}{RESET}  {counts['done']}/{counts['total']}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# WORKFLOW
# ══════════════════════════════════════════════════════════════════════════════


def cmd_workflow(name: str, task: str | None = None):
    """Trigger a named high-level workflow."""
    _print_header(f"GORDON WORKFLOW — {name.upper()}")

    if name not in WORKFLOWS:
        _err(f"Unknown workflow: '{name}'")
        _info("Available: " + ", ".join(WORKFLOWS.keys()))
        return

    _info(WORKFLOWS[name])
    print()

    if name == "rimworld":
        _info("Checking RimWorld VNC container…")
        if _docker_available():
            try:
                r = subprocess.run(
                    [
                        "docker",
                        "ps",
                        "--filter",
                        "name=rimworld-vnc",
                        "--format",
                        "{{.Status}}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                status = r.stdout.strip()
                if status:
                    _ok(f"RimWorld VNC: {status}")
                else:
                    _warn(
                        "RimWorld VNC not running — run: docker-compose --profile rimworld up -d"
                    )
            except Exception as e:
                _warn(f"Docker query failed: {e}")
        else:
            _warn("Docker not available — cannot launch RimWorld container")
        _publish(
            "lattice.workflow.started",
            {"workflow": "rimworld", "ts": datetime.now(UTC).isoformat()},
        )

    elif name == "chatdev":
        task_desc = task or "Implement next P0 task from MASTER_ZETA_TODO.md"
        _info(f"Task: {task_desc}")
        result = _post(
            "/api/swarm/task",
            {
                "task": task_desc,
                "source": "gordon-workflow-chatdev",
            },
        )
        if result:
            _ok(f"ChatDev task queued: {result}")
        else:
            _warn("Swarm API not responding — publishing to Redis instead")
            _publish(
                "lattice.task.created",
                {
                    "description": task_desc,
                    "source": "gordon-chatdev",
                    "priority": "P1",
                    "ts": datetime.now(UTC).isoformat(),
                },
            )
        _ok("ChatDev session initiated")

    elif name == "chug":
        _info("Triggering CHUG autonomous improvement cycle…")
        _publish(
            "lattice.chug.trigger",
            {"cycle": "auto", "ts": datetime.now(UTC).isoformat()},
        )
        _ok("CHUG engine cycle triggered — agents will run improvement loop")

    elif name == "skyclaw":
        _info("Dispatching SkyClaw full scan…")
        _publish(
            "lattice.skyclaw.scan_requested",
            {
                "targets": ["filesystem", "colony", "crash_logs", "processes"],
                "ts": datetime.now(UTC).isoformat(),
            },
        )
        _ok(
            "SkyClaw scan dispatched — results will appear on lattice.skyclaw.discovery"
        )

    elif name == "blueprint":
        _info("Requesting blueprint evolution cycle from Culture Ship…")
        _publish(
            "lattice.culture_ship.blueprint_request",
            {
                "generations": 5,
                "ts": datetime.now(UTC).isoformat(),
            },
        )
        _ok("Blueprint evolution requested")

    elif name == "hackathon":
        _info("Starting one-hour all-agents hackathon…")
        for agent in AGENT_IDS:
            _publish(
                f"lattice.agent.{agent}.task",
                {
                    "type": "hackathon",
                    "duration_s": 3600,
                    "ts": datetime.now(UTC).isoformat(),
                },
            )
        _ok(f"Hackathon event started — {len(AGENT_IDS)} agents notified")

    print()


# ══════════════════════════════════════════════════════════════════════════════
# ASK / EXEC
# ══════════════════════════════════════════════════════════════════════════════


def cmd_ask(agent: str, question: str):
    """Route a question to a specific agent via the Terminal Depths API."""
    _print_header(f"GORDON → {agent.upper()}")
    _info(f'Routing: "{question}"')
    print()

    command = f"talk {agent} {question}"
    result = _post(
        "/api/game/command",
        {
            "command": command,
            "session_id": GORDON_SESSION,
        },
    )

    if result:
        for line in result.get("output", []):
            if isinstance(line, dict):
                s = line.get("s", "")
                t = line.get("t", "")
                if t in ("npc", "lore", "story"):
                    print(f"  {CYAN}{s}{RESET}")
                elif t in ("dim",):
                    print(f"  {DIM}{s}{RESET}")
                elif t in ("error", "err"):
                    print(f"  {RED}{s}{RESET}")
                elif s.strip():
                    print(f"  {s}")
    else:
        _err("Terminal Depths API not responding")
        _info(
            f'Try: curl -X POST {TD_URL}/api/game/command -d \'{{"command":"talk {agent} {question}"}}\''
        )

    print()


def cmd_exec(agent: str, command: str):
    """Execute a game command scoped to an agent context."""
    _print_header(f"GORDON EXEC — [{agent.upper()}]")
    _info(f"Command: {command}")
    print()

    full_command = command if agent == "game" else f"{agent} {command}"
    result = _post(
        "/api/game/command",
        {
            "command": full_command,
            "session_id": GORDON_SESSION,
        },
    )

    if result:
        for line in result.get("output", []):
            if isinstance(line, dict):
                s = line.get("s", "")
                if s.strip():
                    print(f"  {s}")
    else:
        _err("Terminal Depths API not responding")

    print()


# ══════════════════════════════════════════════════════════════════════════════
# TASK
# ══════════════════════════════════════════════════════════════════════════════


def cmd_task_add(description: str, priority: str = "P1", skip_serena: bool = False):
    """Add a task to MASTER_ZETA_TODO.md, with optional Serena context analysis."""
    priority = priority.upper()
    if priority not in ("P0", "P1", "P2"):
        _err(f"Invalid priority: {priority}. Use P0, P1, or P2.")
        return

    tasks = _parse_todo()
    # Generate next ID in series
    prefix_map = {"P0": "C", "P1": "N", "P2": "Z"}
    prefix = prefix_map.get(priority, "G")
    nums = [
        int(re.sub(r"\D", "", t["id"]))
        for t in tasks
        if t["id"].startswith(prefix) and re.sub(r"\D", "", t["id"]).isdigit()
    ]
    next_num = max(nums, default=0) + 1
    task_id = f"{prefix}{next_num}"

    # ── Serena context (non-blocking: warn if unavailable) ──────────────────
    serena_context: list[str] = []
    if not skip_serena:
        try:
            s = _get_serena()
            _serena_ensure_indexed(s)
            # Ask Serena what's relevant to this task
            answer = s.ask(description, session_id=f"task-{task_id}", surface="cli")
            # Extract only the file references (first 3 results)
            lines = [l.strip() for l in answer.splitlines() if "@" in l and ":" in l][
                :3
            ]
            serena_context = lines
            # Also record the task as an observation in Serena's memory
            s.observe(
                subject=f"task:{task_id}",
                note=f"[{priority}] {description}",
                severity=(
                    "info"
                    if priority == "P2"
                    else "warn" if priority == "P1" else "critical"
                ),
            )
        except Exception:
            pass  # Serena is optional — task still gets created

    _append_todo(description, priority, task_id)
    _ok(f"Task added: [{priority}] {task_id}: {description}")

    if serena_context:
        _dim("  Serena identified related code:")
        for line in serena_context:
            _dim(f"    {line}")

    _publish(
        "lattice.task.created",
        {
            "task_id": task_id,
            "priority": priority,
            "description": description,
            "serena_context": serena_context,
            "source": "gordon-cli",
            "ts": datetime.now(UTC).isoformat(),
        },
    )


def cmd_task_list(filter_by: str = "incomplete", limit: int = 20):
    """List tasks from MASTER_ZETA_TODO.md."""
    _print_header("GORDON TASK LIST")
    tasks = _parse_todo()

    f = filter_by.lower()
    if f in ("incomplete", "pending", "open"):
        tasks = [t for t in tasks if not t["done"]]
    elif f in ("complete", "done"):
        tasks = [t for t in tasks if t["done"]]
    elif f in ("p0", "p1", "p2"):
        tasks = [t for t in tasks if t["priority"].lower() == f]
        tasks = [t for t in tasks if not t["done"]]

    tasks = tasks[:limit]

    if not tasks:
        _dim("No matching tasks found.")
        return

    for t in tasks:
        check = f"{GREEN}✓{RESET}" if t["done"] else f"{RED}○{RESET}"
        p_color = (
            RED if t["priority"] == "P0" else (YELLOW if t["priority"] == "P1" else DIM)
        )
        print(
            f"  {check} {p_color}{t['priority']}{RESET} [{t['id']}] {t['description'][:70]}"
        )

    remaining = len(_parse_todo()) - len(tasks)
    print()
    _dim(f"Showing {len(tasks)} tasks  (filter: {filter_by})")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# LOGS
# ══════════════════════════════════════════════════════════════════════════════


def cmd_logs(follow: bool = False, service: str = "all"):
    """Tail Lattice logs."""
    log_file = LOG_DIR / "gordon.log"
    if not log_file.exists():
        _warn(f"Log file not found: {log_file}")
        return

    if follow:
        _info(f"Following {log_file} — Ctrl+C to stop")
        try:
            subprocess.run(["tail", "-f", str(log_file)])
        except KeyboardInterrupt:
            print()
    else:
        try:
            result = subprocess.run(
                ["tail", "-n", "50", str(log_file)], capture_output=True, text=True
            )
            print(result.stdout)
        except Exception:
            content = log_file.read_text()
            lines = content.splitlines()[-50:]
            print("\n".join(lines))


# ══════════════════════════════════════════════════════════════════════════════
# SCALE
# ══════════════════════════════════════════════════════════════════════════════


def cmd_scale(service: str, count: int):
    """Scale a Docker Compose service."""
    _print_header(f"GORDON SCALE — {service} × {count}")
    if not _docker_available():
        _err("Docker not available")
        return

    compose_file = BASE / "docker-compose.yml"
    if not compose_file.exists():
        _err(f"docker-compose.yml not found at {compose_file}")
        return

    _info(f"Scaling {service} to {count} instances…")
    try:
        result = subprocess.run(
            [
                "docker-compose",
                "--file",
                str(compose_file),
                "up",
                "--scale",
                f"{service}={count}",
                "-d",
                service,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            _ok(f"{service} scaled to {count}")
        else:
            _err(f"Scale failed:\n{result.stderr}")
    except Exception as e:
        _err(f"Error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════════════════════


def cmd_health():
    """Deep health check of all Lattice endpoints."""
    _print_header("GORDON HEALTH CHECK")
    checks = [
        ("GET", "/api/health", None, "Core API"),
        ("GET", "/api/lattice/stats", None, "Lattice store"),
        (
            "POST",
            "/api/lattice/search",
            {"query": "serena", "top_k": 1},
            "Lattice search",
        ),
        ("GET", "/api/nusyq/manifest", None, "NuSyQ manifest"),
        ("GET", "/api/agent/leaderboard", None, "Agent leaderboard"),
        ("GET", "/api/swarm/status", None, "Swarm controller"),
        ("GET", "/api/mcp/tools", None, "MCP server"),
        ("GET", "/api/game/commands", None, "Game engine"),
    ]
    all_ok = True
    for method, path, payload, label in checks:
        data = _get(path) if method == "GET" else _post(path, payload or {})
        if data is not None:
            _ok(f"{label:<25}{DIM}OK{RESET}")
        else:
            _err(f"{label:<25}{DIM}unreachable{RESET}")
            all_ok = False

    print()
    if REDIS_OK:
        _ok("Redis pub/sub")
    else:
        _err("Redis pub/sub  — not reachable")
        all_ok = False

    print()
    if all_ok:
        _ok("All systems nominal. The Lattice is alive.")
    else:
        _warn("Some services unreachable — run 'gordon cascade start' to initialize.")


# ══════════════════════════════════════════════════════════════════════════════
# SEED LATTICE
# ══════════════════════════════════════════════════════════════════════════════


def cmd_seed_lattice():
    """Re-seed the Lattice knowledge graph from knowledge_graph.json."""
    _print_header("SEEDING LATTICE")
    result = _post("/api/lattice/seed", {})
    if result:
        seeded = result.get("seeded", "?")
        stats = result.get("stats", {})
        _ok(f"Seeded {seeded} entries")
        _info(f"Nodes: {stats.get('nodes', '?')}  Edges: {stats.get('edges', '?')}")
    else:
        _err("Lattice API not responding")


# ══════════════════════════════════════════════════════════════════════════════
# COUNCIL VOTE
# ══════════════════════════════════════════════════════════════════════════════


def cmd_council_vote(proposal: str):
    """Submit a proposal to the AI Council for a vote."""
    _print_header("AI COUNCIL VOTE")
    _info(f'Proposal: "{proposal}"')

    result = _post("/api/council/vote", {"proposal": proposal})
    if result:
        verdict = result.get("verdict", "unknown")
        votes = result.get("votes", {})
        print()
        color = GREEN if verdict == "approved" else RED
        print(f"  Verdict: {color}{verdict.upper()}{RESET}")
        if votes:
            for agent, vote in votes.items():
                v_color = GREEN if vote in ("yes", "approve") else RED
                print(f"  {v_color}●{RESET} {agent:<15} → {vote}")
    else:
        _warn("Council API not responding — publishing proposal to Redis")
        _publish(
            "lattice.council.proposal",
            {
                "proposal": proposal,
                "source": "gordon-cli",
                "ts": datetime.now(UTC).isoformat(),
            },
        )
        _ok("Proposal published to council channel")


# ══════════════════════════════════════════════════════════════════════════════
# SERENA — The Convergence Layer (direct Python integration)
# ══════════════════════════════════════════════════════════════════════════════


def _get_serena():
    """Instantiate SerenaAgent directly via Python import.
    Works even when the HTTP server is not running — Serena is always available.
    """
    sys.path.insert(0, str(BASE))
    from agents.serena import SerenaAgent

    return SerenaAgent(repo_root=BASE)


def _serena_ensure_indexed(s, fast: bool = True) -> int:
    """Walk if the index is empty or stale. Returns chunk count."""
    try:
        stats = s.memory.index_stats()
        if stats.get("total_chunks", 0) > 0:
            return stats["total_chunks"]
    except Exception:
        pass
    _info("Index empty — running fast walk first...")
    result = s.fast_walk() if fast else s.walk(mode="changed")
    return result.get("chunks_added", 0)


def _sev_color(sev: str) -> str:
    return {
        "critical": RED,
        "warn": YELLOW,
        "info": CYAN,
    }.get(sev, DIM)


def cmd_serena(
    sub: str,
    *positional,
    scope: str = "",
    mode: str = "scoped",
    severity: str = "",
    full_scan: bool = False,
    limit: int = 30,
):
    """Serena: The Convergence Layer — your always-on development partner."""
    try:
        s = _get_serena()
    except Exception as exc:
        _err(f"Serena init failed: {exc}")
        _dim("  Ensure agents/serena/ is intact and deps are installed.")
        return

    # ── status ──────────────────────────────────────────────────────────────
    if sub == "status":
        _print_header("SERENA Ψ — SYSTEM STATUS")
        try:
            st = s.get_status()
            mem = st.get("memory", {})
            idx = mem.get("index", {})
            _ok(f"Memory Palace     {CYAN}{mem.get('db_path', '?')}{RESET}")
            _ok(
                f"Indexed chunks     {BOLD}{idx.get('total_chunks', 0)}{RESET}  "
                f"(files: {idx.get('unique_files', 0)})"
            )
            _ok(f"Observations       {mem.get('observations', 0)}")
            _ok(f"Walk history       {mem.get('walks', 0)} walks")
            _ok(f"Policy trust       {st.get('trust_level', 'standard')}")
            print()
            # Quick alignment
            from agents.serena.drift import DriftDetector

            det = DriftDetector(BASE, s.memory._db_path)
            result = det.align_check()
            score = result.get("score", 0.0)
            a_color = (
                GREEN if result.get("aligned") else (YELLOW if score > 0.6 else RED)
            )
            print(
                f"  Alignment score  {a_color}{BOLD}{score:.0%}{RESET}  "
                f"({result['passed']}/{result['total']} checks)"
            )
            for c in result.get("checks", []):
                icon = f"{GREEN}✓{RESET}" if c["passed"] else f"{RED}✗{RESET}"
                print(f"    {icon}  {c['message']}")
        except Exception as exc:
            _err(f"Status error: {exc}")

    # ── walk ────────────────────────────────────────────────────────────────
    elif sub == "walk":
        _print_header(f"SERENA Ψ — WALK [{mode.upper()}]")
        try:
            t0 = time.time()
            if mode == "full":
                _info("Full walk — indexing entire repository...")
                result = s.walk(mode="full")
            else:
                _info("Scoped walk — indexing game engine, agents, scripts, cli...")
                result = s.fast_walk()
            elapsed = round(time.time() - t0, 1)
            _ok(f"Walk complete in {elapsed}s")
            _ok(f"Chunks indexed   {BOLD}{result.get('chunks_added', 0)}{RESET}")
            _ok(f"Files visited    {result.get('files_visited', 0)}")
            idx = result.get("index_stats", {})
            _dim(
                f"  Total in index: {idx.get('total_chunks', 0)} chunks "
                f"across {idx.get('indexed_files', 0)} files"
            )
        except Exception as exc:
            _err(f"Walk failed: {exc}")

    # ── ask ─────────────────────────────────────────────────────────────────
    elif sub == "ask":
        query = " ".join(positional)
        if not query:
            _err('Usage: gordon serena ask "<question about the codebase>"')
            return
        _print_header("SERENA Ξ — CODE INTELLIGENCE")
        try:
            _serena_ensure_indexed(s)
            if scope:
                from agents.serena.serena_agent import _format_answer

                results = s.memory.search_scoped(query, scope, limit=10)
                answer = _format_answer(query, results)
            else:
                answer = s.ask(query, session_id="gordon-cli", surface="cli")
            print()
            print(answer)
            print()
        except Exception as exc:
            _err(f"Ask failed: {exc}")

    # ── find ────────────────────────────────────────────────────────────────
    elif sub == "find":
        symbol = " ".join(positional)
        if not symbol:
            _err("Usage: gordon serena find <SymbolName> [--kind function|class]")
            return
        _print_header(f"SERENA Ξ — FIND: {symbol}")
        try:
            _serena_ensure_indexed(s)
            answer = s.find(symbol)
            print()
            print(answer)
            print()
        except Exception as exc:
            _err(f"Find failed: {exc}")

    # ── drift ───────────────────────────────────────────────────────────────
    elif sub == "drift":
        _print_header("SERENA Ω — DRIFT DETECTION")
        try:
            from agents.serena.drift import DriftDetector

            det = DriftDetector(BASE, s.memory._db_path)
            signals = det.detect_all(
                scope=scope or None,
                fast=not full_scan,
            )
            if not signals:
                _ok("No drift detected. The system is coherent.")
                return

            # Group by category
            from collections import Counter

            cats = Counter(sig.severity for sig in signals)
            crit = cats.get("critical", 0)
            warn = cats.get("warn", 0)
            info = cats.get("info", 0)
            crit_col = RED if crit else GREEN
            print(
                f"  Signals: {crit_col}{crit} critical{RESET}  "
                f"{YELLOW}{warn} warn{RESET}  {DIM}{info} info{RESET}"
            )
            print()

            shown = 0
            for sev in ("critical", "warn", "info"):
                for sig in [s2 for s2 in signals if s2.severity == sev]:
                    if shown >= limit:
                        remaining = len(signals) - shown
                        _dim(
                            f"  ... {remaining} more signals (use --limit N to see more)"
                        )
                        break
                    c = _sev_color(sev)
                    icon = {"critical": "✕", "warn": "⚠", "info": "◦"}.get(sev, "?")
                    fix = f"  {GREEN}[auto-fixable]{RESET}" if sig.auto_fix else ""
                    print(
                        f"  {c}{icon}{RESET}  {BOLD}{sig.category}{RESET}  "
                        f"{DIM}{sig.path}{RESET}"
                    )
                    print(f"     {sig.message}{fix}")
                    shown += 1
                if shown >= limit:
                    break
            print()
            if crit > 0:
                _warn(f"{crit} critical issue(s) need immediate attention")
        except Exception as exc:
            _err(f"Drift detection failed: {exc}")

    # ── align ───────────────────────────────────────────────────────────────
    elif sub == "align":
        _print_header("SERENA ⟁ — ALIGNMENT CHECK (Mladenc)")
        try:
            from agents.serena.drift import DriftDetector

            det = DriftDetector(BASE, s.memory._db_path)
            result = det.align_check()
            score = result.get("score", 0.0)
            aligned = result.get("aligned", False)
            a_color = GREEN if aligned else (YELLOW if score > 0.6 else RED)
            verdict = (
                "ALIGNED" if aligned else ("NOMINAL" if score > 0.6 else "DRIFTING")
            )
            print(f"\n  Score: {a_color}{BOLD}{score:.0%}  [{verdict}]{RESET}")
            print(f"  {DIM}{result.get('horizon', '')}{RESET}\n")
            for c in result.get("checks", []):
                icon = f"{GREEN}✓{RESET}" if c["passed"] else f"{RED}✗{RESET}"
                print(f"  {icon}  {c['name']:<25}  {c['message']}")
            print()
        except Exception as exc:
            _err(f"Align check failed: {exc}")

    # ── diff ────────────────────────────────────────────────────────────────
    elif sub == "diff":
        _print_header("SERENA Ψ — GIT DIFF")
        try:
            result = s.diff()
            print()
            print(result)
            print()
        except Exception as exc:
            _err(f"Diff failed: {exc}")

    # ── observe ─────────────────────────────────────────────────────────────
    elif sub == "observe":
        note = " ".join(positional)
        if not note:
            _err(
                'Usage: gordon serena observe "<observation>" [--severity info|warn|critical]'
            )
            return
        sev = severity or "info"
        try:
            result = s.observe(subject="gordon-cli", note=note, severity=sev)
            _ok(result)
            _publish(
                "lattice.serena.observation",
                {
                    "note": note,
                    "severity": sev,
                    "source": "gordon-cli",
                    "ts": datetime.now(UTC).isoformat(),
                },
            )
        except Exception as exc:
            _err(f"Observe failed: {exc}")

    # ── plan ────────────────────────────────────────────────────────────────
    elif sub == "plan":
        description = " ".join(positional)
        if not description:
            _err('Usage: gordon serena plan "<what you want to build>"')
            return
        _print_header("SERENA Φ — DEVELOPMENT PLAN")
        try:
            _serena_ensure_indexed(s)
            print()
            # 1. Semantic search for related code
            _info("Searching codebase for related context...")
            answer = s.ask(description, session_id="gordon-cli-plan", surface="cli")
            print(answer)
            print()
            # 2. Drift check — any existing issues in the area?
            _info("Checking for existing drift in related areas...")
            from agents.serena.drift import DriftDetector

            det = DriftDetector(BASE, s.memory._db_path)
            signals = det.detect_all(fast=True)
            critical = [sig for sig in signals if sig.severity == "critical"]
            warnings = [sig for sig in signals if sig.severity == "warn"]
            if critical:
                _warn(
                    f"{len(critical)} critical drift signal(s) exist — resolve before starting:"
                )
                for sig in critical[:5]:
                    print(f"    {RED}✕{RESET}  {sig.category}: {sig.path}")
                    print(f"       {sig.message}")
            elif warnings:
                _dim(
                    f"  {len(warnings)} warnings in drift (run 'gordon serena drift' to see)"
                )
            else:
                _ok("No critical drift. Safe to proceed.")
            print()
            # 3. Propose the plan
            proposal = s.propose(
                action="change_logic",
                description=f"Development plan: {description}",
                auto_only=False,
            )
            disp = proposal.get("disposition", "confirm")
            d_color = GREEN if disp == "automatic" else YELLOW
            print(
                f"  Consent gate: {d_color}{disp.upper()}{RESET}  "
                f"({proposal.get('reason', '')})"
            )
            print()
            _dim(
                '  To create a task from this plan: gordon task add "..." --priority P1'
            )
            _dim('  To record this observation:      gordon serena observe "..."')
        except Exception as exc:
            _err(f"Plan failed: {exc}")

    # ── audit ───────────────────────────────────────────────────────────────
    elif sub == "audit":
        _print_header("SERENA Ω — AUDIT TRAIL")
        try:
            obs = s.memory.recent_observations(limit=limit, severity=severity or None)
            if not obs:
                _dim("No observations recorded yet.")
                return
            for o in obs:
                sev = o.get("severity", "info")
                c = _sev_color(sev)
                icon = {"critical": "✕", "warn": "⚠", "info": "◦"}.get(sev, "?")
                ts = o.get("ts", "?")[:19]
                print(
                    f"  {c}{icon}{RESET}  {DIM}{ts}{RESET}  {BOLD}{o.get('subject','?')}{RESET}"
                )
                note = o.get("note", "")
                if note:
                    print(f"     {note[:120]}")
        except Exception as exc:
            _err(f"Audit failed: {exc}")

    # ── report ──────────────────────────────────────────────────────────────
    elif sub == "report":
        _print_header("SERENA — DEVELOPMENT SESSION REPORT")
        try:
            _serena_ensure_indexed(s)
            from agents.serena.drift import DriftDetector

            det = DriftDetector(BASE, s.memory._db_path)

            # Alignment
            align = det.align_check()
            score = align.get("score", 0.0)
            a_color = (
                GREEN if align.get("aligned") else (YELLOW if score > 0.6 else RED)
            )
            print(
                f"\n  {BOLD}Alignment{RESET}   {a_color}{score:.0%}{RESET}  "
                f"({align['passed']}/{align['total']} checks)"
            )

            # Drift summary
            signals = det.detect_all(fast=True)
            from collections import Counter

            cats = Counter(sig.category for sig in signals)
            sevs = Counter(sig.severity for sig in signals)
            print(
                f"  {BOLD}Drift{RESET}       "
                f"{RED}{sevs.get('critical',0)} critical{RESET}  "
                f"{YELLOW}{sevs.get('warn',0)} warn{RESET}  "
                f"{DIM}{sevs.get('info',0)} info{RESET}"
            )
            if cats:
                for cat, count in cats.most_common(5):
                    print(f"    {DIM}{count:>3}×{RESET}  {cat}")

            # Index stats
            idx = s.memory.index_stats()
            print(
                f"  {BOLD}Index{RESET}       "
                f"{idx.get('total_chunks',0)} chunks  "
                f"{idx.get('indexed_files',0)} files"
            )

            # Recent observations
            obs = s.memory.recent_observations(limit=5)
            if obs:
                print(f"\n  {BOLD}Recent Observations{RESET}")
                for o in obs:
                    sev = o.get("severity", "info")
                    c = _sev_color(sev)
                    ts = o.get("ts", "?")[:16]
                    print(f"    {c}◦{RESET}  {DIM}{ts}{RESET}  {o.get('subject','?')}")

            # Git diff
            print(f"\n  {BOLD}Changed Files{RESET}")
            diff_text = s.diff()
            for line in diff_text.splitlines()[1:8]:
                print(f"    {line}")

            # Save report
            report_path = STATE_DIR / "serena_dev_report.json"
            import json as _json

            report_data = {
                "ts": datetime.now(UTC).isoformat(),
                "alignment": align,
                "drift_summary": dict(cats),
                "severity_summary": dict(sevs),
                "index_stats": idx,
                "top_signals": [sig.to_dict() for sig in signals[:10]],
            }
            report_path.write_text(_json.dumps(report_data, indent=2))
            print()
            _ok(f"Full report saved → {report_path}")
            _publish("lattice.serena.dev_report", report_data)

        except Exception as exc:
            _err(f"Report failed: {exc}")

    # ── help / unknown ──────────────────────────────────────────────────────
    else:
        print(
            f"""
{BOLD}{CYAN}gordon serena — Serena: The Convergence Layer{RESET}
{DIM}Direct Python integration — works without the HTTP server.{RESET}

{BOLD}Subcommands:{RESET}
  gordon serena status                    — alignment score + index health
  gordon serena walk [--mode scoped|full] — index/re-index the repository
  gordon serena ask "<question>"          — semantic Q&A over the codebase
  gordon serena find <Symbol>             — find where a symbol is defined
  gordon serena drift [--scope <path>]    — detect drift signals
  gordon serena drift --full              — full scan (includes doc-debt AST)
  gordon serena align                     — Mladenc alignment check
  gordon serena diff                      — git-changed files
  gordon serena observe "<note>"          — log observation to Memory Palace
  gordon serena plan "<description>"      — propose + context for a new feature
  gordon serena audit [--severity warn]   — audit trail of observations
  gordon serena report                    — comprehensive dev session report

{BOLD}Examples:{RESET}
  gordon serena ask "where is faction rep modified?"
  gordon serena find InterAgentDirector
  gordon serena drift --scope app/game_engine
  gordon serena plan "add a persistence layer for player inventory"
  gordon serena report
"""
        )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN DISPATCHER
# ══════════════════════════════════════════════════════════════════════════════


def _usage():
    print(
        f"""
{BOLD}{CYAN}Gordon — Terminal Depths Lattice CLI{RESET}
{DIM}The god-mode orchestrator for the ecosystem.{RESET}

{BOLD}Usage:{RESET}
  gordon status [--watch] [--interval N]
  gordon cascade start [--dry-run]
  gordon cascade status
  gordon workflow <name> [--task "..."]
  gordon ask <agent> "<question>"
  gordon exec <agent> "<command>"
  gordon task add "<description>" [--priority P0|P1|P2]
  gordon task list [--filter incomplete|p0|p1|p2] [--limit N]
  gordon logs [--follow] [--service <name>]
  gordon scale <service> <count>
  gordon health
  gordon seed-lattice
  gordon council vote "<proposal>"
  gordon serena status | walk | ask | find | drift | align | diff | plan | report

{BOLD}Workflows:{RESET}"""
    )
    for k, v in WORKFLOWS.items():
        print(f"  {CYAN}{k:<12}{RESET} {DIM}{v}{RESET}")
    print(
        f"""
{BOLD}Agents:{RESET}
  {', '.join(AGENT_IDS)}

{BOLD}Examples:{RESET}
  gordon ask ada "What's the status of the colony?"
  gordon workflow chatdev --task "Implement geothermal power plant"
  gordon task add "Add multiplayer session support" --priority P1
  gordon status --watch --interval 10
  gordon cascade start
"""
    )


def main():
    args = sys.argv[1:]
    if not args:
        _usage()
        return

    cmd = args[0].lower()
    rest = args[1:]

    def _flag(flags: list[str]) -> bool:
        return any(f in rest for f in flags)

    def _flag_val(flag: str, default=None):
        for i, a in enumerate(rest):
            if a == flag and i + 1 < len(rest):
                return rest[i + 1]
        return default

    def _positional(n: int):
        positional = [a for a in rest if not a.startswith("--")]
        return positional[n] if n < len(positional) else None

    # ── status ────────────────────────────────────────────────────────────────
    if cmd == "status":
        watch = _flag(["--watch", "-w"])
        interval = int(_flag_val("--interval", 5))
        cmd_status(watch=watch, interval=interval)

    # ── cascade ───────────────────────────────────────────────────────────────
    elif cmd == "cascade":
        sub = _positional(0) or "status"
        if sub == "start":
            cmd_cascade_start(dry_run=_flag(["--dry-run"]))
        elif sub == "status":
            cmd_cascade_status()
        elif sub == "stop":
            _info("Stopping cascade — publishing halt signal to bus")
            _publish("lattice.cascade.stopped", {"ts": datetime.now(UTC).isoformat()})
            _ok("Halt signal sent")
        else:
            _err(f"Unknown cascade subcommand: {sub}")

    # ── workflow ──────────────────────────────────────────────────────────────
    elif cmd == "workflow":
        name = _positional(0) or ""
        task = _flag_val("--task")
        cmd_workflow(name, task=task)

    # ── ask ───────────────────────────────────────────────────────────────────
    elif cmd == "ask":
        agent = _positional(0) or "ada"
        question = _positional(1) or " ".join(
            [a for a in rest if not a.startswith("-")][1:]
        )
        if not question:
            _err('Usage: gordon ask <agent> "<question>"')
            return
        cmd_ask(agent, question)

    # ── exec ──────────────────────────────────────────────────────────────────
    elif cmd == "exec":
        agent = _positional(0) or "game"
        command = _positional(1) or " ".join(
            [a for a in rest if not a.startswith("-")][1:]
        )
        if not command:
            _err('Usage: gordon exec <agent> "<command>"')
            return
        cmd_exec(agent, command)

    # ── task ──────────────────────────────────────────────────────────────────
    elif cmd == "task":
        sub = _positional(0) or "list"
        if sub == "add":
            desc = _positional(1) or ""
            priority = _flag_val("--priority", "P1")
            if not desc:
                _err('Usage: gordon task add "<description>" [--priority P0|P1|P2]')
                return
            cmd_task_add(desc, priority)
        elif sub == "list":
            filter_by = _flag_val("--filter", "incomplete")
            limit = int(_flag_val("--limit", 20))
            cmd_task_list(filter_by, limit)
        else:
            _err(f"Unknown task subcommand: {sub}")

    # ── logs ──────────────────────────────────────────────────────────────────
    elif cmd == "logs":
        follow = _flag(["--follow", "-f"])
        service = _flag_val("--service", "all")
        cmd_logs(follow=follow, service=service)

    # ── scale ─────────────────────────────────────────────────────────────────
    elif cmd == "scale":
        service = _positional(0) or ""
        count = int(_positional(1) or 1)
        if not service:
            _err("Usage: gordon scale <service> <count>")
            return
        cmd_scale(service, count)

    # ── health ────────────────────────────────────────────────────────────────
    elif cmd == "health":
        cmd_health()

    # ── seed-lattice ──────────────────────────────────────────────────────────
    elif cmd == "seed-lattice":
        cmd_seed_lattice()

    # ── council ───────────────────────────────────────────────────────────────
    elif cmd == "council":
        sub = _positional(0) or ""
        if sub == "vote":
            proposal = _positional(1) or " ".join(
                [a for a in rest if not a.startswith("-")][1:]
            )
            if not proposal:
                _err('Usage: gordon council vote "<proposal>"')
                return
            cmd_council_vote(proposal)
        else:
            _err(f"Unknown council subcommand: {sub}")

    # ── serena ────────────────────────────────────────────────────────────────
    elif cmd == "serena":
        sub = _positional(0) or "help"
        # Collect all non-flag positional args after the subcommand
        positionals = [a for a in rest if not a.startswith("--")]
        pos_after_sub = tuple(positionals[1:])  # skip the sub itself
        scope = _flag_val("--scope", "")
        mode = _flag_val("--mode", "scoped")
        severity = _flag_val("--severity", "")
        limit = int(_flag_val("--limit", 30))
        full_scan = _flag(["--full"])
        cmd_serena(
            sub,
            *pos_after_sub,
            scope=scope,
            mode=mode,
            severity=severity,
            full_scan=full_scan,
            limit=limit,
        )

    else:
        _err(f"Unknown command: '{cmd}'")
        _usage()


if __name__ == "__main__":
    main()
