#!/usr/bin/env python3
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
branch = "feature/batch-003"
files = [
    "archive/launchers/copilot_agent_launcher_v1.py",
    "archive/obsolete/launchers/kilo_foolish_master_launcher.py",
    "archive/quantum_problem_resolver_evolution/quantum_problem_resolver_transcendent.py",
    "archive/quantum_problem_resolver_evolution/quantum_problem_resolver_unified.py",
    "archive/quantum_problem_resolver_evolution/quantum_problem_resolver_v4.2.0_ARCHIVE.py",
]


def run(cmd):
    print("RUN:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(repo))
    if res.returncode != 0:
        raise SystemExit(res.returncode)


run(["git", "-C", str(repo), "checkout", "-b", branch])
for f in files:
    run(["git", "-C", str(repo), "add", f])
run(["git", "-C", str(repo), "commit", "-m", "batched(commit): add 5 files from batch 003"])
run(["git", "-C", str(repo), "push", "-u", "origin", branch])
print("Batch", branch, "pushed")
