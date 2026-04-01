#!/usr/bin/env python3
"""Emit terminal banners with simple dedup to avoid spam.

Usage:
  python scripts/terminal_banner.py --name "Claude" --line "=== Claude Agent Terminal ==="
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Terminal banner with dedup.")
    parser.add_argument("--name", required=True, help="Unique terminal key")
    parser.add_argument(
        "--line",
        action="append",
        default=[],
        help="Banner line to print (repeatable)",
    )
    parser.add_argument(
        "--window-seconds",
        type=float,
        default=None,
        help="Minimum seconds between prints for this terminal",
    )
    args = parser.parse_args()

    window_default = float(os.getenv("NUSYG_TERMINAL_BANNER_WINDOW_SECONDS", "600"))
    window = args.window_seconds if args.window_seconds is not None else window_default
    force = os.getenv("NUSYG_TERMINAL_BANNER_FORCE", "0").lower() in ("1", "true", "yes")

    state_path = Path("state/terminal_banners.json")
    state = _load_state(state_path)
    now = time.time()

    last = None
    record = state.get(args.name, {})
    if isinstance(record, dict):
        last = record.get("last_printed")

    should_print = force or (last is None) or (now - float(last) >= window)
    if should_print:
        for line in args.line:
            print(line)
        state[args.name] = {"last_printed": now}
        _save_state(state_path, state)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
