#!/usr/bin/env python3
"""agent_status.py — Zero-token instant orient for the AI agent.
Run this at the start of every session. Takes 1 second. Saves minutes.
Usage: python3 scripts/agent_status.py
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
HEALTH_URL = os.getenv("TERMINAL_DEPTHS_HEALTH_URL", "http://localhost:8008/api/manifest")


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT)
    return r.stdout.strip()


def main():
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║     AGENT INSTANT ORIENT — ZERO TOKEN EDITION       ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    # Git state
    head = sh("git log --oneline -3")
    branch = sh("git branch --show-current")
    dirty = sh("git status --short | head -5")
    print(f"  Git branch:  {branch}")
    print("  Recent commits:\n" + "\n".join(f"    {l}" for l in head.splitlines()))
    if dirty:
        print("  Dirty files:\n" + "\n".join(f"    {l}" for l in dirty.splitlines()))
    else:
        print("  Working tree: clean")

    # commands.py stats
    cmd_file = ROOT / "app/game_engine/commands.py"
    if cmd_file.exists():
        lines = cmd_file.read_text().count("\n")
        handlers = sh("grep -c 'def _cmd_' app/game_engine/commands.py")
        to_dict_line = sh(
            "grep -n 'def to_dict' app/game_engine/commands.py | tail -1 | cut -d: -f1"
        )
        print(
            f"\n  commands.py:  {lines} lines  |  {handlers} handlers  |  to_dict @ line {to_dict_line}"
        )

    # TODO stats
    todo_file = ROOT / "MASTER_ZETA_TODO.md"
    if todo_file.exists():
        done = sh("grep -c '^- \\[x\\]' MASTER_ZETA_TODO.md")
        remaining = sh("grep -c '^- \\[ \\]' MASTER_ZETA_TODO.md")
        print(f"  MASTER TODO:  {done} done  |  {remaining} remaining")

        # Next 5 items
        next_items = sh("grep '^- \\[ \\]' MASTER_ZETA_TODO.md | head -5")
        print("\n  NEXT 5 TODO:")
        for item in next_items.splitlines():
            print(f"    {item[:80]}")

    # Server health
    try:
        r = urllib.request.urlopen(HEALTH_URL, timeout=2)
        data = json.loads(r.read())
        print(
            f"\n  Server:  UP  | ok={data.get('ok', data.get('status'))}  "
            f"session_count={data.get('session_count', data.get('active_game_sessions', '?'))}"
        )
    except Exception:
        print("\n  Server:  DOWN or not started")

    # Size audit
    size_file = ROOT / "state/size_audit.json"
    if size_file.exists():
        audit = json.loads(size_file.read_text())
        print(
            f"  Repo size:   {audit['working_mb']:.0f} MB working + {audit['git_mb']:.0f} MB git = {audit['working_mb']+audit['git_mb']:.0f} MB total"
        )
        print(f"  Stage:       {audit['stage']}")
    else:
        print("  Size audit:  not run yet — run: python3 scripts/size_audit.py")

    # Winning pattern reminder
    print(
        """
  ─────────────────────────────────────────────────────
  WINNING PATTERN:
  1. grep "^- \\[ \\]" MASTER_ZETA_TODO.md | head -20
  2. grep -n "def to_dict" app/game_engine/commands.py
  3. Batch edit: all new _cmd_* before to_dict anchor
  4. restart_workflow → sleep 12 → one test pass → commit
  ─────────────────────────────────────────────────────
"""
    )


if __name__ == "__main__":
    main()
