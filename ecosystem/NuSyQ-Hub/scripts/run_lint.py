#!/usr/bin/env python3
"""Lightweight lint runner for NuSyQ-Hub.

Reads JSON config from stdin (optional) and runs ruff on the repo.
Falls back to a no-op with guidance if ruff is not installed.
"""

import json
import subprocess
import sys
from pathlib import Path


def main():
    try:
        cfg = json.load(sys.stdin)
    except Exception:
        cfg = {}

    root = Path(cfg.get("root", ".")).resolve()
    ruff_cmd = ["ruff", "check", "."]

    try:
        proc = subprocess.run(
            ruff_cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("ruff not installed; install with: pip install ruff", file=sys.stderr)
        return 1

    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
