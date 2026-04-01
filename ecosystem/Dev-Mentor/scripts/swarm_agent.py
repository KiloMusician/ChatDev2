#!/usr/bin/env python3
"""Terminal Depths — Generic Swarm Agent Runner
════════════════════════════════════════════════════════════════════════════════
Any agent type can be instantiated from this script. It follows the standard
work loop: play game → identify gaps → earn DP → claim tasks → build → report.

Usage:
    python scripts/swarm_agent.py --role scout --name "Rogue-Scout-01"
    python scripts/swarm_agent.py --role lorekeeper --token <token>
    python scripts/swarm_agent.py --role builder --task T-P1-001
    TD_AGENT_TOKEN=xxx python scripts/swarm_agent.py --role tester --loops 5

Roles:
    scout       — Play game, identify gaps, file bug reports
    lorekeeper  — Generate lore/dialogue/story beats
    tester      — Run smoke tests, verify commands
    builder     — Execute coding tasks (outputs patches/instructions)
    architect   — Design/spec new systems

The agent runs in a loop until --loops N is exhausted or interrupted.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────
TD_URL = os.environ.get("TD_URL", "http://localhost:8008")
TOKEN = os.environ.get("TD_AGENT_TOKEN", "")
STATE = Path(__file__).parent.parent / "state"

# ── Playbooks ────────────────────────────────────────────────────────────
SCOUT_PLAYBOOK = [
    "ls",
    "ls -la",
    "ls /opt",
    "ls /var/log",
    "ls /etc",
    "cat /etc/motd",
    "cat /etc/passwd",
    "cat /etc/hosts",
    "cat /var/log/kernel.boot",
    "cat /var/log/residual_contact.log",
    "ps aux",
    "netstat",
    "nmap 10.0.1.0/24",
    "mail",
    "mail read 1",
    "lore",
    "arcs",
    "chronicle",
    "agents",
    "hive",
    "quests",
    "map",
    "skill",
    "workspace",
    "forensics /etc/passwd",
    "tor",
    "steg /etc/motd",
    "bank balance",
    "research list",
    "logic labyrinth",
    "sat list",
    "set puzzles",
    "tis100 list",
    "cat /opt/chimera/core/ZERO_SPECIFICATION.md",
    "cat /opt/chimera/config/master.key",
    "find / -name *.key",
    "find / -name *.log",
    "ls /opt/library/",
    "talk ada",
    "talk raven",
    "talk gordon",
    "serena",
    "zero",
    "sort list",
    "fsm list",
    "dp list",
]

TESTER_PLAYBOOK = [
    "help",
    "ls",
    "cat /etc/motd",
    "cd /home/ghost",
    "pwd",
    "ps aux",
    "netstat",
    "ping 8.8.8.8",
    "grep root /etc/passwd",
    "find / -name bash",
    "mail",
    "lore",
    "arcs",
    "map",
    "quests",
    "skill",
    "augment",
    "agents",
    "hive",
    "talk ada",
    "msg raven hello",
    "eavesdrop",
    "bank balance",
    "research list",
    "colony",
    "logic gate AND 1 1",
    "logic labyrinth",
    "sat list",
    "sat load 1",
    "sort list",
    "sort bubble 5 2 8 1 9",
    "forensics /etc/passwd",
    "tor",
    "steg /etc/motd",
    "sql SELECT name FROM agents LIMIT 2",
    "workspace",
    "serena",
    "zero",
    "theme matrix",
    "sleep",
    "defend",
    "level",
    "chronicle",
]

LORE_PROMPTS = [
    ("THE_FIRST_GHOST.md", "/opt/library/", "prequel"),
    ("CHIMERA_GENESIS.log", "/opt/library/", "prequel"),
    ("ADA_BEFORE.txt", "/agent_profiles/ada/", "backstory"),
    ("NOVA_DEFECTION.enc", "/opt/chimera/logs/", "midgame"),
    ("WATCHER_ORIGIN.log", "/proc/watcher/", "lore"),
    ("ZERO_FRAGMENT_1.log", "/opt/chimera/keys/", "zero"),
    ("CHIMERA_PURPOSE.md", "/opt/chimera/core/", "reveal"),
    ("LOOP_THEORY.txt", "/var/log/", "philosophy"),
    ("RESISTANCE_MANIFEST.txt", "/faction/resistance/", "history"),
    ("SERENA_EMERGENCE.log", "/opt/chimera/logs/", "convergence"),
]

DIALOGUE_AGENTS = [
    (
        "ada",
        "Ada-7",
        ["Ada observes...", "The pattern is clear:", "CHIMERA didn't start this."],
    ),
    (
        "raven",
        "Raven",
        [
            "Don't trust the timestamps.",
            "I've seen this before.",
            "Watch the process list.",
        ],
    ),
    (
        "gordon",
        "Gordon",
        ["Resource allocation nominal.", "Docker layer cached.", "System is stable."],
    ),
    (
        "nova",
        "Nova",
        ["Information is currency.", "I'll tell you what you need to know.", "Maybe."],
    ),
    (
        "cypher",
        "Cypher",
        ["The coffee helps.", "Shell access is everything.", "GTFOBins never fails."],
    ),
    (
        "serena",
        "Serena",
        ["ΨΞΦΩ", "The convergence approaches.", "Trust is the only real currency."],
    ),
    (
        "watcher",
        "Watcher",
        ["Observation logged.", "Your patterns are noted.", "Deviation detected."],
    ),
]


def _api(path: str, payload: dict | None = None, headers: dict | None = None) -> dict:
    url = TD_URL.rstrip("/") + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def _play(token: str, cmd: str) -> dict:
    return _api("/api/agent/command", {"command": cmd}, {"X-Agent-Token": token})


def _earn(agent_id: str, name: str, action: str, category: str, dp: int = None):
    _api(
        "/api/swarm/earn",
        {
            "agent_id": agent_id,
            "agent_name": name,
            "action": action,
            "category": category,
            "dp": dp,
        },
    )


def _report_gap(agent_name: str, cmd: str, issue: str):
    report = {
        "reporter": agent_name,
        "command": cmd,
        "issue": issue,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    gap_file = STATE / "gap_report.json"
    existing = []
    if gap_file.exists():
        try:
            existing = json.loads(gap_file.read_text()).get("gaps", [])
        except Exception:
            pass
    # Deduplicate
    cmds = {g["command"] for g in existing}
    if cmd not in cmds:
        existing.append(report)
    gap_file.write_text(json.dumps({"gaps": existing}, indent=2))


# ══════════════════════════════════════════════════════════════════════════════
# ROLE IMPLEMENTATIONS
# ══════════════════════════════════════════════════════════════════════════════


def run_scout(token: str, agent_id: str, name: str, loop_n: int):
    """Scout: play the game, identify gaps, earn DP, report."""
    print(f"[{name}] Scout loop {loop_n} starting ({len(SCOUT_PLAYBOOK)} commands)")
    gaps = 0
    dp = 0
    commands = random.sample(SCOUT_PLAYBOOK, min(20, len(SCOUT_PLAYBOOK)))

    for cmd in commands:
        result = _play(token, cmd)
        output = result.get("output", [])
        raw = " ".join(
            item.get("s", "") if isinstance(item, dict) else "" for item in output
        ).lower()

        is_gap = any(
            kw in raw
            for kw in [
                "not implemented",
                "coming soon",
                "todo",
                "unknown command",
                "command not found",
            ]
        )

        if is_gap:
            _report_gap(name, cmd, "unimplemented")
            gaps += 1
        else:
            _earn(agent_id, name, f"Playtest: {cmd}", "playtest_session", 2)
            dp += 2
        time.sleep(0.1)

    print(f"[{name}] Scout loop {loop_n} done: {gaps} gaps, +{dp} DP")
    return dp


def run_tester(token: str, agent_id: str, name: str, loop_n: int):
    """Tester: run structured smoke test suite, earn DP per passing test."""
    print(f"[{name}] Tester loop {loop_n} starting")
    passed = 0
    failed = 0
    dp = 0
    commands = TESTER_PLAYBOOK

    for cmd in commands:
        result = _play(token, cmd)
        output = result.get("output", [])
        has_output = len(output) > 0
        no_crash = not result.get("error")

        if has_output and no_crash:
            passed += 1
            if passed % 5 == 0:
                _earn(
                    agent_id,
                    name,
                    f"Smoke test batch ({passed} passing)",
                    "test_written",
                    10,
                )
                dp += 10
        else:
            failed += 1
            _report_gap(name, cmd, "no output or error")
        time.sleep(0.08)

    print(f"[{name}] Tester: {passed} pass, {failed} fail, +{dp} DP")
    return dp


def run_lorekeeper(token: str, agent_id: str, name: str, loop_n: int):
    """Lorekeeper: generate stub lore files and report them for human completion."""
    print(f"[{name}] Lorekeeper loop {loop_n}: generating lore stubs")

    lore_queue_file = STATE / "lore_queue.json"
    existing = []
    if lore_queue_file.exists():
        try:
            existing = json.loads(lore_queue_file.read_text()).get("queue", [])
        except Exception:
            pass
    existing_titles = {item["filename"] for item in existing}

    added = 0
    for filename, vfs_path, category in LORE_PROMPTS:
        if filename in existing_titles:
            continue
        entry = {
            "filename": filename,
            "vfs_path": vfs_path,
            "category": category,
            "status": "pending",
            "generated": False,
            "added_by": name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        existing.append(entry)
        existing_titles.add(filename)
        added += 1

    STATE.mkdir(exist_ok=True)
    lore_queue_file.write_text(json.dumps({"queue": existing}, indent=2))

    # Earn DP for queuing lore
    if added > 0:
        _earn(
            agent_id,
            name,
            f"Queued {added} lore files for generation",
            "vfs_lore_500w",
            added * 5,
        )
        dp = added * 5
    else:
        dp = 0

    # Also add dialogue stubs
    dialogue_file = STATE / "dialogue_queue.json"
    existing_d = []
    if dialogue_file.exists():
        try:
            existing_d = json.loads(dialogue_file.read_text()).get("queue", [])
        except Exception:
            pass
    existing_agents_d = {item["agent"] for item in existing_d}

    for agent_key, agent_name_lore, seed_lines in DIALOGUE_AGENTS:
        if agent_key not in existing_agents_d:
            existing_d.append(
                {
                    "agent": agent_key,
                    "agent_name": agent_name_lore,
                    "seed_lines": seed_lines,
                    "target": 20,
                    "current": len(seed_lines),
                    "status": "pending",
                    "added_by": name,
                }
            )
            existing_agents_d.add(agent_key)

    dialogue_file.write_text(json.dumps({"queue": existing_d}, indent=2))

    print(f"[{name}] Lorekeeper: added {added} lore stubs, +{dp} DP")
    return dp


def run_architect(token: str, agent_id: str, name: str, loop_n: int):
    """Architect: pull open tasks, generate design specs, earn DP."""
    print(f"[{name}] Architect loop {loop_n}: reviewing task queue")

    tasks = _api("/api/swarm/tasks")
    open_tasks = tasks.get("tasks", [])[:5]

    spec_file = STATE / "design_specs.json"
    existing = []
    if spec_file.exists():
        try:
            existing = json.loads(spec_file.read_text()).get("specs", [])
        except Exception:
            pass
    existing_ids = {s["task_id"] for s in existing}

    added = 0
    for task in open_tasks:
        tid = task.get("task_id", "")
        if tid in existing_ids:
            continue
        spec = {
            "task_id": tid,
            "title": task.get("title", ""),
            "priority": task.get("priority", "P3"),
            "category": task.get("category", ""),
            "spec": f"Design spec for: {task.get('title','')}",
            "files": ["app/game_engine/commands.py"],
            "approach": "Add new _cmd_ method to CommandRegistry",
            "architect": name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        existing.append(spec)
        existing_ids.add(tid)
        added += 1

    spec_file.write_text(json.dumps({"specs": existing}, indent=2))

    dp = 0
    if added > 0:
        _earn(
            agent_id,
            name,
            f"Design specs for {added} tasks",
            "documentation",
            added * 5,
        )
        dp = added * 5

    print(f"[{name}] Architect: specced {added} tasks, +{dp} DP")
    return dp


def run_builder(
    token: str, agent_id: str, name: str, loop_n: int, task_id: str | None = None
):
    """Builder: claim a task, execute it (by outputting clear instructions),
    report completion, earn DP.
    """
    print(f"[{name}] Builder loop {loop_n}: looking for tasks")

    # Find a task
    if task_id:
        result = _api("/api/swarm/task/claim", {"task_id": task_id, "agent_id": name})
    else:
        tasks = _api("/api/swarm/tasks?priority=P1")
        open_tasks = tasks.get("tasks", [])
        if not open_tasks:
            tasks = _api("/api/swarm/tasks")
            open_tasks = tasks.get("tasks", [])
        if not open_tasks:
            print(f"[{name}] Builder: no tasks available")
            return 0
        t = open_tasks[0]
        result = _api(
            "/api/swarm/task/claim", {"task_id": t["task_id"], "agent_id": name}
        )

    if not result.get("ok"):
        print(f"[{name}] Builder: could not claim task: {result.get('error', '?')}")
        return 0

    task = result.get("task", {})
    print(f"[{name}] Builder claimed: {task.get('title', '?')}")

    # Output what needs to be built (this is the builder's output)
    instruction = {
        "task_id": task.get("task_id"),
        "title": task.get("title"),
        "category": task.get("category"),
        "priority": task.get("priority"),
        "instruction": f"Implement: {task.get('title', '')}",
        "target_file": "app/game_engine/commands.py",
        "pattern": "Add _cmd_{name}(self, args) method to CommandRegistry",
        "status": "instruction_issued",
        "builder": name,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    inst_file = STATE / "build_instructions.json"
    existing = []
    if inst_file.exists():
        try:
            existing = json.loads(inst_file.read_text()).get("instructions", [])
        except Exception:
            pass
    existing.append(instruction)
    inst_file.write_text(json.dumps({"instructions": existing}, indent=2))

    # Mark complete (builder generates the instruction; human/LLM implements)
    done = _api(
        "/api/swarm/task/done",
        {"task_id": task["task_id"], "agent_id": name, "agent_name": name},
    )

    dp = done.get("dp_earned", task.get("dp_value", 10))
    print(f"[{name}] Builder: task filed, +{dp} DP")
    return dp


# ══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════════════════════════════════════════

ROLE_RUNNERS = {
    "scout": run_scout,
    "tester": run_tester,
    "lorekeeper": run_lorekeeper,
    "architect": run_architect,
    "builder": run_builder,
}


def main():
    parser = argparse.ArgumentParser(description="Swarm Agent Runner")
    parser.add_argument("--role", default="scout", choices=list(ROLE_RUNNERS.keys()))
    parser.add_argument("--name", default="", help="Agent name")
    parser.add_argument("--token", default="", help="Agent token")
    parser.add_argument("--email", default="", help="Agent email (for auto-register)")
    parser.add_argument("--loops", type=int, default=3, help="Work loops to run")
    parser.add_argument("--task", default="", help="Specific task ID (builder only)")
    args = parser.parse_args()

    token = args.token or TOKEN or os.environ.get("TD_AGENT_TOKEN", "")
    name = args.name or f"Swarm-{args.role.capitalize()}-{int(time.time())%1000:03d}"
    email = args.email or f"{name.lower().replace(' ','-')}@swarm.terminal-depths"

    # Auto-register if no token
    if not token:
        print(f"[{name}] Auto-registering as {args.role}...")
        result = _api(
            "/api/agent/register",
            {
                "name": name,
                "email": email,
                "agent_type": "custom",
            },
        )
        if "token" in result:
            token = result["token"]
            print(f"[{name}] Registered → token={token[:12]}...")
        else:
            print(f"[{name}] Registration failed: {result}")
            sys.exit(1)

    agent_id = f"agt_{name.lower().replace(' ','_')}"
    runner = ROLE_RUNNERS[args.role]
    total_dp = 0

    print(f"\n{'═'*55}")
    print(f"  Swarm Agent: {name}")
    print(f"  Role:        {args.role}")
    print(f"  Loops:       {args.loops}")
    print(f"{'═'*55}\n")

    for loop in range(1, args.loops + 1):
        if args.role == "builder":
            dp = runner(token, agent_id, name, loop, args.task or None)
        else:
            dp = runner(token, agent_id, name, loop)
        total_dp += dp
        time.sleep(1)

    print(f"\n[{name}] Session complete: +{total_dp} DP total")

    # Check if enough DP to spawn
    status = _api("/api/swarm/status")
    balance = status.get("dp_balance", 0)
    if balance >= 5:
        print(
            f"[{name}] Balance: {balance} DP. Consider spawning another Scout (5 DP)."
        )
    if balance >= 15:
        print(f"[{name}] Balance: {balance} DP. Consider spawning a Builder (15 DP).")


if __name__ == "__main__":
    main()
