"""Commit a small batch of files (task-runtime + Phase2 docs) and push to origin.

Usage: python scripts/commit_batch1.py
"""

import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
branch = "feature/task-runtime-batch1"
files = [
    "docs/PHASE_2_TASK_ENFORCEMENT.md",
    "src/task_runtime/__init__.py",
    "src/task_runtime/db.py",
    "src/task_runtime/models.py",
    "src/task_runtime/manager.py",
    "src/task_runtime/agent_wrapper.py",
    "src/task_runtime/README.md",
    "scripts/nusyq_task.py",
    "scripts/init_db.py",
    "scripts/migrate_quest_log.py",
    "scripts/migrate_models_and_artifacts.py",
    "scripts/agent_adapter_example.py",
    "scripts/query_tasks.py",
    "scripts/git_create_branch_and_push.py",
]


def run(cmd):
    print("RUN:", cmd)
    res = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        raise SystemExit(res.returncode)


def main():
    run(["git", "checkout", "-b", branch])
    for f in files:
        run(["git", "add", f])
    run(
        [
            "git",
            "commit",
            "-m",
            "chore(task-runtime): add DB runtime, agent wrapper, migrations (batch1)",
        ]
    )
    run(["git", "push", "-u", "origin", branch])


if __name__ == "__main__":
    main()
