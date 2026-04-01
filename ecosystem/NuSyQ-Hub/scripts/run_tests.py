#!/usr/bin/env python3
"""Thin pytest wrapper for NuSyQ-Hub.

Reads JSON config from stdin (optional) and runs pytest with provided args
or defaults to -q for brevity. Falls back gracefully if pytest is missing.
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
    args = cfg.get("pytest_args", ["-q"])

    cmd = ["pytest", *args]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        print("pytest not installed; install with: pip install pytest", file=sys.stderr)
        return 1

    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
