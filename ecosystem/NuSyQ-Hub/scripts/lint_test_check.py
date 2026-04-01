#!/usr/bin/env python3
"""Run linting, tests, and type checks for the NuSyQ-Hub repository."""

import argparse
import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    """Run a command and return the CompletedProcess.

    If capture is True, captures stdout/stderr for inspection without spamming output.
    """
    logger.info("$ %s", " ".join(cmd))
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return subprocess.run(cmd, timeout=300)


def _ruff_command_for_mode(mode: str) -> list[str]:
    """Return the appropriate Ruff command for the requested mode.

    Diagnostic/fast mode defaults to a critical-only gate to keep doctor
    actionable while large style debt remains in brownfield code.
    Set `NUSYQ_LINT_DIAGNOSTIC_STRICT=1` to force full Ruff in diagnostic mode.
    """
    strict_diag = os.getenv("NUSYQ_LINT_DIAGNOSTIC_STRICT", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if mode in {"diagnostic", "fast"} and not strict_diag:
        # Syntax/import/runtime-blocking categories only.
        return [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--select",
            "E9,F63,F7,F82",
            "src",
            "tests",
        ]
    return [sys.executable, "-m", "ruff", "check", "src", "tests"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run linting, tests, and type checks.")
    parser.add_argument(
        "--mode",
        default="full",
        choices=["full", "diagnostic", "fast"],
        help="Run full checks or a lightweight diagnostic pass.",
    )
    args = parser.parse_args()

    # 1) Black (check-only) — align with workspace line length
    # Use the same line length as the formatting task to avoid perpetual diffs
    result = run([sys.executable, "-m", "black", "--check", "--line-length=100", "src", "tests"])
    if result.returncode != 0:
        logger.error("Command failed: %s -m black --check src tests", sys.executable)
        sys.exit(result.returncode)

    # 2) Ruff (critical-only in diagnostic mode unless strict env override).
    # Try modern CLI first, fallback to legacy invocation when needed.
    ruff_cmd_modern = _ruff_command_for_mode(args.mode)
    ruff_modern = run(ruff_cmd_modern, capture=True)
    if ruff_modern.returncode == 0:
        # Print trimmed output if any (ruff is usually quiet on success)
        if ruff_modern.stdout:
            print(ruff_modern.stdout)
    else:
        # If the error looks like an unknown subcommand, fallback to legacy invocation
        err_txt = (ruff_modern.stderr or "") + (ruff_modern.stdout or "")
        if "unrecognized subcommand" in err_txt.lower() or "no such command" in err_txt.lower():
            ruff_cmd_legacy = [sys.executable, "-m", "ruff", "src", "tests"]
            ruff_legacy = run(ruff_cmd_legacy, capture=True)
            if ruff_legacy.returncode != 0:
                if ruff_legacy.stdout:
                    logger.error(ruff_legacy.stdout)
                if ruff_legacy.stderr:
                    logger.error(ruff_legacy.stderr)
                logger.error("Command failed: %s", " ".join(ruff_cmd_legacy))
                sys.exit(ruff_legacy.returncode)
        else:
            # Real lint failures or other errors – surface output and fail
            if ruff_modern.stdout:
                print(ruff_modern.stdout)
            if ruff_modern.stderr:
                print(ruff_modern.stderr)
            print(f"Command failed: {' '.join(ruff_cmd_modern)}")
            sys.exit(ruff_modern.returncode)

    if args.mode in {"diagnostic", "fast"}:
        if "E9,F63,F7,F82" in " ".join(ruff_cmd_modern):
            print("Diagnostic mode: Ruff critical gate active (E9,F63,F7,F82).")
            print("Set NUSYQ_LINT_DIAGNOSTIC_STRICT=1 to run full Ruff in diagnostic mode.")
        print("Diagnostic mode: skipped full pytest suite.")
        print("\nAll checks passed!")
        return

    # 3) Tests with coverage summary (pytest.ini may add more flags)
    result = run([sys.executable, "-m", "pytest", "--cov=src", "--cov-report=term-missing"])
    if result.returncode != 0:
        print(f"Command failed: {sys.executable} -m pytest --cov=src --cov-report=term-missing")
        sys.exit(result.returncode)

    print("\nAll checks passed!")


if __name__ == "__main__":
    main()
