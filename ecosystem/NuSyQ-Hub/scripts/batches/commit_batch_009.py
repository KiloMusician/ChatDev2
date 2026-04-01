#!/usr/bin/env python3
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
branch = "feature/batch-009"
files = [
    "scripts/surgical_type_fix.py",
    "scripts/sync_ollama_to_lmstudio.py",
    "scripts/test_cascades.py",
    "scripts/test_culture_ship_cycle.py",
    "scripts/test_ecosystem_activation.py",
    "scripts/test_integration_wiring.py",
    "scripts/test_oldest_house_fix.py",
    "scripts/test_zeta05_quantum_escalation.py",
    "scripts/three_before_new_precommit_hook.py",
    "scripts/update_rosetta.py",
    "scripts/validate_devcontainer.py",
    "scripts/agent_adapter_example.py",
    "scripts/commit_batch1.py",
    "scripts/generate_commit_batches.py",
    "scripts/git_create_branch_and_push.py",
    "scripts/init_db.py",
    "scripts/migrate_models_and_artifacts.py",
    "scripts/migrate_quest_log.py",
    "scripts/nusyq_task.py",
    "scripts/query_tasks.py",
]


def run(cmd):
    print("RUN:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(repo))
    if res.returncode != 0:
        raise SystemExit(res.returncode)


run(["git", "-C", str(repo), "checkout", "-b", branch])
for f in files:
    run(["git", "-C", str(repo), "add", f])
run(["git", "-C", str(repo), "commit", "-m", "batched(commit): add 20 files from batch 009"])
run(["git", "-C", str(repo), "push", "-u", "origin", branch])
print("Batch", branch, "pushed")
