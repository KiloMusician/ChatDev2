#!/usr/bin/env python3
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
branch = "feature/batch-004"
files = [
    "data/ecosystem/quest_assignments.json",
    "data/state.duckdb",
    "data/temple_of_knowledge/floor_1_foundation/agent_registry.json",
    "data/temple_of_knowledge/floor_1_foundation/knowledge_base.json",
    "data/temple_of_knowledge/floor_1_foundation/omnitag_archive.json",
    "data/unified_pu_queue.json",
]


def run(cmd):
    print("RUN:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(repo))
    if res.returncode != 0:
        raise SystemExit(res.returncode)


run(["git", "-C", str(repo), "checkout", "-b", branch])
for f in files:
    run(["git", "-C", str(repo), "add", f])
run(["git", "-C", str(repo), "commit", "-m", "batched(commit): add 6 files from batch 004"])
run(["git", "-C", str(repo), "push", "-u", "origin", branch])
print("Batch", branch, "pushed")
