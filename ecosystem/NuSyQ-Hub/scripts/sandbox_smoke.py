#!/usr/bin/env python3
"""Smoke test for SandboxRunner (Phase 3)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.integration.sandbox_runner import get_sandbox_runner


def main() -> None:
    runner = get_sandbox_runner()
    result = runner.run(
        ["python", "-c", "print('hello from sandbox')"],
        env={"OPENAI_API_KEY": "dummy"},
        readonly_mount=Path(".").resolve(),
    )
    print("success:", result.success, "rc:", result.returncode)
    print("stdout:", result.stdout.strip())
    print("stderr:", result.stderr.strip())
    print("workdir:", result.workdir)


if __name__ == "__main__":
    main()
