"""Utility: Play the first few Terminal Depths commands and save output.

Usage:
  python scripts/terminal_depths_play.py --server http://127.0.0.1:5001 --out output.json

This is useful for automated validation and review of game responses.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError as e:
    raise SystemExit("Missing dependency: requests (pip install requests)") from e


def create_session(server: str) -> str:
    r = requests.post(f"{server}/api/game/session", json={})
    r.raise_for_status()
    data = r.json()
    return data["session_id"]


def run_command(server: str, session_id: str, command: str) -> dict[str, Any]:
    r = requests.post(
        f"{server}/api/game/command",
        json={"command": command, "session_id": session_id},
    )
    r.raise_for_status()
    return r.json()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a small set of Terminal Depths commands and save output."
    )
    parser.add_argument(
        "--server", default="http://127.0.0.1:5001", help="Game server URL"
    )
    parser.add_argument(
        "--out", default="terminal_depths_play_output.json", help="Output JSON path"
    )
    parser.add_argument(
        "--commands",
        nargs="*",
        default=["help", "tutorial", "skills", "ls", "talk ada"],
        help="Commands to run (default: first five starter commands)",
    )
    args = parser.parse_args(argv)

    session_id = create_session(args.server)

    results: list[dict[str, Any]] = []
    for cmd in args.commands:
        res = run_command(args.server, session_id, cmd)
        results.append({"command": cmd, "response": res})

    out = {
        "server": args.server,
        "session_id": session_id,
        "commands": results,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote output to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
