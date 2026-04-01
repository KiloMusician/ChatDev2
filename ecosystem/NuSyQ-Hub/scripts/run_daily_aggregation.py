"""Daily Aggregation Runner

Runs single-repo aggregation, multi-repo aggregation, and captures deltas.
Intended for scheduling via GitHub Actions or local Task Scheduler.

Usage:
    python scripts/run_daily_aggregation.py --commit

If --commit passed and git available with clean working tree except aggregation
changes, will stage and commit updated artifacts.
"""

from __future__ import annotations

import subprocess
import sys

AGGREGATOR_SINGLE = [sys.executable, "src/tools/report_aggregator.py", "--markdown", "--json"]
AGGREGATOR_MULTI = [sys.executable, "src/tools/multi_repo_aggregator.py", "--markdown", "--json"]


def run_cmd(cmd: list[str]) -> int:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}\nSTDERR:\n{proc.stderr}")
    else:
        if proc.stdout:
            print(proc.stdout)
    return proc.returncode


def artifacts_changed() -> bool:
    """Check if docs/Reports aggregation artifacts have modifications."""
    try:
        res = subprocess.run(["git", "status", "--porcelain", "docs/Reports"], capture_output=True, text=True)
        if res.returncode != 0:
            return False
        return bool(res.stdout.strip())
    except FileNotFoundError:
        return False


def commit_changes() -> None:
    if not artifacts_changed():
        print("No aggregation artifact changes detected; skipping commit.")
        return
    subprocess.run(["git", "add", "docs/Reports"], check=False)
    subprocess.run(["git", "commit", "-m", "chore: daily aggregated insights update"], check=False)
    print("Committed aggregated insights artifacts.")


def main(argv: list[str]) -> int:
    commit_flag = "--commit" in argv
    print("Running single-repo aggregation...")
    if run_cmd(AGGREGATOR_SINGLE) != 0:
        print("Single-repo aggregation failed; aborting.")
        return 1
    print("Running multi-repo aggregation...")
    if run_cmd(AGGREGATOR_MULTI) != 0:
        print("Multi-repo aggregation failed; aborting.")
        return 2
    if commit_flag:
        commit_changes()
    print("Daily aggregation complete.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
