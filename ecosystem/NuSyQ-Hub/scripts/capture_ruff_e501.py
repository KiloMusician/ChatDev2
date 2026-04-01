#!/usr/bin/env python3
"""Run ruff (E501 selection) and write output to `ruff_e501.txt` as UTF-8.

PowerShell's redirection (`>`) writes UTF-16 by default which can confuse
downstream parsers. This helper ensures consistent UTF-8 output.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def find_ruff_cmd() -> list[str]:
    # Prefer module invocation via the same Python interpreter
    return [sys.executable, "-m", "ruff", "check", ".", "--select", "E501"]


def main() -> int:
    out_path = Path("ruff_e501.txt")
    cmd = find_ruff_cmd()
    print("Running:", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except Exception as exc:
        print("Failed to run ruff:", exc)
        return 2

    combined = "".join([proc.stdout or "", proc.stderr or ""]) or ""
    try:
        out_path.write_text(combined, encoding="utf-8")
        print(f"Wrote ruff output to {out_path} (UTF-8)")
    except Exception as exc:
        print("Failed to write ruff output:", exc)
        return 3

    if proc.returncode != 0:
        print("Ruff returned non-zero exit code:", proc.returncode)
    else:
        print("Ruff completed OK (exit 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
