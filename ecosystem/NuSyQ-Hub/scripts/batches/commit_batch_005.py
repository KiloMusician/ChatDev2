#!/usr/bin/env python3
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
branch = "feature/batch-005"
files = [
    "docs/Auto/SUMMARY_PRUNE_PLAN.json",
    "docs/GUILD_BOARD.md",
    "docs/PHASE_2_TASK_ENFORCEMENT.md",
]


def run(cmd):
    print("RUN:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(repo))
    if res.returncode != 0:
        raise SystemExit(res.returncode)


run(["git", "-C", str(repo), "checkout", "-b", branch])
for f in files:
    run(["git", "-C", str(repo), "add", f])
run(["git", "-C", str(repo), "commit", "-m", "batched(commit): add 3 files from batch 005"])
run(["git", "-C", str(repo), "push", "-u", "origin", branch])
print("Batch", branch, "pushed")
