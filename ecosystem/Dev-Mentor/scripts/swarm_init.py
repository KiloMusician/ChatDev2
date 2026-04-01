#!/usr/bin/env python3
"""Terminal Depths — Swarm Initializer
════════════════════════════════════════════════════════════════════════════════
Phase 0 boot sequence for the autonomous development swarm.

Usage:
    python scripts/swarm_init.py              # Full init
    python scripts/swarm_init.py --assess     # Assessment only (no spawn)
    python scripts/swarm_init.py --play N     # Play N commands and report
    python scripts/swarm_init.py --seed       # Register seed agents only
    python scripts/swarm_init.py --status     # Show current swarm status

What it does:
    1. Assess environment (RAM, CPU, Ollama, game API, agent DB)
    2. Register 5 seed agents (Serena, Ada-7, Gordon, Raven, Zod-Prime)
    3. Each seed agent plays 10 commands and earns initial DP
    4. Compile gap report from play sessions
    5. Spawn first wave of Scouts (5 DP each)
    6. Output prioritized build queue to stdout
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────
TD_URL = os.environ.get("TD_URL", "http://localhost:7337")
STATE_DIR = Path(__file__).parent.parent / "state"

SEED_AGENTS = [
    {"name": "Serena", "email": "serena@psi.terminal-depths", "agent_type": "serena"},
    {"name": "Ada-7", "email": "ada7@faction.terminal-depths", "agent_type": "claude"},
    {
        "name": "Gordon",
        "email": "gordon@docker.terminal-depths",
        "agent_type": "gordon",
    },
    {"name": "Raven", "email": "raven@shadow.terminal-depths", "agent_type": "custom"},
    {"name": "Zod-Prime", "email": "zod@monks.terminal-depths", "agent_type": "custom"},
]

SCOUT_COMMANDS = [
    "help",
    "ls",
    "ls -la",
    "ls /opt",
    "ls /var/log",
    "ls /home/ghost",
    "cat /etc/motd",
    "cat /etc/passwd",
    "ps aux",
    "netstat",
    "mail",
    "lore",
    "arcs",
    "agents",
    "quests",
    "map",
    "skill",
    "workspace",
    "forensics /etc/passwd",
    "tor",
]

KNOWLEDGE_PROBE_COMMANDS = [
    "cat /opt/chimera/core/ZERO_SPECIFICATION.md",
    "cat /var/log/kernel.boot",
    "cat /var/log/residual_contact.log",
    "cat /var/log/agent_comms.log",
    "cat /home/ghost/.watcher_note",
    "ls /opt/library/",
    "steg /etc/motd",
    "sql SELECT * FROM agents LIMIT 3",
    "bank balance",
    "research list",
    "logic labyrinth",
    "sat list",
    "set puzzles",
    "tis100 list",
    "hive",
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.reason, "code": e.code}
    except Exception as e:
        return {"error": str(e)}


def _print(msg: str, prefix: str = "  "):
    print(f"{prefix}{msg}")


def assess_environment() -> dict:
    """Check all systems before spawning anything."""
    print("\n╔══════════════════════════════════════════════╗")
    print("║  SWARM PHASE 0: ENVIRONMENT ASSESSMENT      ║")
    print("╚══════════════════════════════════════════════╝\n")

    results = {}

    # 1. Game API health
    health = _api("/api/health")
    alive = "ok" in str(health).lower() or health.get("status") == "ok"
    results["api_alive"] = alive
    _print(
        f"[{'✓' if alive else '✗'}] Game API at {TD_URL}: {'ALIVE' if alive else 'DOWN'}"
    )

    # 2. Agent registration
    caps = _api("/api/capabilities")
    results["capabilities"] = "name" in caps
    _print(
        f"[{'✓' if results['capabilities'] else '✗'}] Capabilities manifest: "
        f"{'available' if results['capabilities'] else 'unavailable'}"
    )

    # 3. Swarm controller
    swarm = _api("/api/swarm/status")
    results["swarm_ok"] = swarm.get("ok", False)
    if results["swarm_ok"]:
        _print(
            f"[✓] Swarm Controller: ONLINE (DP={swarm.get('dp_balance',0)}, "
            f"Agents={swarm.get('agents',{}).get('total',0)})"
        )
    else:
        _print("[✗] Swarm Controller: OFFLINE or not mounted")

    # 4. State directory
    state_ok = STATE_DIR.exists()
    results["state_dir"] = state_ok
    _print(f"[{'✓' if state_ok else '✗'}] State directory: {STATE_DIR}")

    # 5. Existing agents
    lb = _api("/api/agent/leaderboard")
    count = lb.get("count", 0)
    results["registered_agents"] = count
    _print(f"[✓] Registered agents: {count}")

    # 6. Swarm DP balance
    if results["swarm_ok"]:
        dp = swarm.get("dp_balance", 0)
        phase = swarm.get("phase", "?")
        _print(f"[✓] Development Points: {dp} DP (Phase {phase})")
        results["dp"] = dp
        results["phase"] = phase

    print()
    return results


def register_seed_agents() -> dict:
    """Register all 5 seed agents and return their tokens."""
    print("╔══════════════════════════════════════════════╗")
    print("║  REGISTERING SEED AGENTS                    ║")
    print("╚══════════════════════════════════════════════╝\n")

    tokens = {}
    token_file = STATE_DIR / "seed_tokens.json"

    # Load existing
    if token_file.exists():
        try:
            tokens = json.loads(token_file.read_text())
        except Exception:
            pass

    for agent in SEED_AGENTS:
        if agent["name"] in tokens:
            _print(f"[→] {agent['name']:12s} already registered (token on file)")
            continue

        result = _api("/api/agent/register", agent)
        if "token" in result:
            tokens[agent["name"]] = result["token"]
            tokens[f"{agent['name']}_session"] = result.get("session_id", "")
            _print(
                f"[✓] {agent['name']:12s} registered → token={result['token'][:12]}..."
            )
        elif result.get("error"):
            _print(f"[✗] {agent['name']:12s} failed: {result['error']}")
        else:
            _print(f"[?] {agent['name']:12s} unexpected response: {result}")

    # Save tokens
    STATE_DIR.mkdir(exist_ok=True)
    token_file.write_text(json.dumps(tokens, indent=2))
    _print(f"\n[✓] Tokens saved to {token_file}")
    print()
    return tokens


def play_session(token: str, agent_name: str, commands: list) -> dict:
    """Play a set of commands and collect gap report."""
    gaps = []
    successes = []
    dp_earned = 0

    for cmd in commands:
        result = _api("/api/agent/command", {"command": cmd}, {"X-Agent-Token": token})
        output_lines = result.get("output", [])
        raw = " ".join(
            item.get("s", "") if isinstance(item, dict) else str(item)
            for item in output_lines
        ).lower()

        # Gap detection
        is_gap = any(
            kw in raw
            for kw in [
                "not implemented",
                "coming soon",
                "todo",
                "stub",
                "unknown command",
                "command not found",
                "no output",
            ]
        )
        is_error = result.get("error") or "error" in raw[:50]

        if is_gap:
            gaps.append({"command": cmd, "issue": "placeholder/unimplemented"})
        elif is_error:
            gaps.append({"command": cmd, "issue": "error response"})
        else:
            successes.append(cmd)

        # Earn DP for playtest
        _api(
            "/api/swarm/earn",
            {
                "agent_id": f"agt_{agent_name.lower()}",
                "agent_name": agent_name,
                "action": f"Playtest: {cmd}",
                "category": "playtest_session",
                "dp": 2,
            },
        )
        dp_earned += 2
        time.sleep(0.05)  # be gentle

    return {
        "agent": agent_name,
        "commands": len(commands),
        "successes": len(successes),
        "gaps": gaps,
        "dp_earned": dp_earned,
    }


def compile_gap_report(play_results: list) -> dict:
    """Compile all play sessions into a unified gap report."""
    all_gaps = []
    for r in play_results:
        for g in r.get("gaps", []):
            all_gaps.append(g)

    # Deduplicate
    seen = set()
    unique_gaps = []
    for g in all_gaps:
        key = g["command"]
        if key not in seen:
            seen.add(key)
            unique_gaps.append(g)

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_commands_played": sum(r["commands"] for r in play_results),
        "gaps_found": len(unique_gaps),
        "gaps": unique_gaps,
        "agents": [r["agent"] for r in play_results],
        "total_dp_earned": sum(r["dp_earned"] for r in play_results),
    }

    report_path = STATE_DIR / "gap_report.json"
    STATE_DIR.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2))
    return report


def print_gap_report(report: dict):
    print("╔══════════════════════════════════════════════╗")
    print("║  GAP REPORT                                 ║")
    print("╚══════════════════════════════════════════════╝\n")
    _print(f"Commands played:  {report['total_commands_played']}")
    _print(f"Gaps found:       {report['gaps_found']}")
    _print(f"DP earned:        {report['total_dp_earned']}")
    if report["gaps"]:
        print("\n  Missing/Broken:")
        for g in report["gaps"]:
            _print(f"  • {g['command']:30s}  [{g['issue']}]", prefix="  ")
    print()


def print_status():
    """Print current swarm status."""
    status = _api("/api/swarm/status")
    if not status.get("ok"):
        print("Swarm controller offline.")
        return

    print("\n╔══════════════════════════════════════════════╗")
    print("║  SWARM STATUS                               ║")
    print("╚══════════════════════════════════════════════╝\n")
    _print(f"Phase:          {status['phase']}")
    _print(f"DP Balance:     {status['dp_balance']}")
    _print(f"Total Earned:   {status['total_earned']}")
    _print(f"Total Spent:    {status['total_spent']}")
    _print(f"Transactions:   {status['transactions']}")
    _print(f"Active Agents:  {status['agents']['total']}")

    by_role = status["agents"].get("by_role", {})
    if by_role:
        print("\n  Agents by Role:")
        for role, count in by_role.items():
            _print(f"  • {role:<15s} × {count}", prefix="  ")

    tasks = status.get("tasks", {})
    print("\n  Tasks:")
    _print(f"  Open:    {tasks.get('open', 0)}")
    _print(f"  Claimed: {tasks.get('claimed', 0)}")
    _print(f"  Done:    {tasks.get('done', 0)}")

    nxt = status.get("next_phase", {})
    if nxt.get("remaining", 0) > 0:
        print(
            f"\n  Next phase: {nxt['next_phase']} " f"({nxt['remaining']} DP remaining)"
        )
    print()


def main():
    parser = argparse.ArgumentParser(description="Swarm Phase 0 Initializer")
    parser.add_argument("--assess", action="store_true", help="Assessment only")
    parser.add_argument("--seed", action="store_true", help="Register seed agents")
    parser.add_argument("--play", type=int, metavar="N", help="Play N sessions")
    parser.add_argument("--status", action="store_true", help="Show swarm status")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.assess:
        assess_environment()
        return

    # Full init
    env = assess_environment()

    if not env.get("api_alive"):
        print("ERROR: Game API is not running. Start the server first.")
        print("  python -m cli.devmentor serve --host 0.0.0.0 --port 5000")
        sys.exit(1)

    tokens = register_seed_agents()

    if args.seed:
        print("Seed agents registered. Run without --seed for full init.")
        return

    # Play sessions
    n_sessions = args.play or 1
    print("╔══════════════════════════════════════════════╗")
    print("║  RUNNING PLAY SESSIONS                      ║")
    print("╚══════════════════════════════════════════════╝\n")

    play_results = []
    for agent in SEED_AGENTS[:n_sessions]:
        tok = tokens.get(agent["name"])
        if not tok:
            continue
        _print(f"[→] {agent['name']} playing {len(SCOUT_COMMANDS)} commands...")
        result = play_session(tok, agent["name"], SCOUT_COMMANDS)
        play_results.append(result)
        _print(
            f"[✓] {agent['name']}: {result['successes']} ok, {len(result['gaps'])} gaps, +{result['dp_earned']} DP"
        )

    if play_results:
        report = compile_gap_report(play_results)
        print_gap_report(report)

    print_status()
    print("Phase 0 initialization complete. The swarm is awake.\n")


if __name__ == "__main__":
    main()
