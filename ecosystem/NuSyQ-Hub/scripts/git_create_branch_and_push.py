"""Create a branch, commit staged changes, and push to origin.

This script runs git commands via subprocess to avoid shell escaping issues.

Usage:
  python scripts/git_create_branch_and_push.py <branch-name> "commit message"
"""

import subprocess
import sys
from pathlib import Path


def run(cmd, cwd):
    print("RUN:", cmd)
    res = subprocess.run(cmd, cwd=cwd, shell=False, capture_output=True, text=True, check=False)
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        raise SystemExit(res.returncode)


def main():
    if len(sys.argv) < 3:
        print("Usage: git_create_branch_and_push.py <branch> <commit-message>")
        return
    branch = sys.argv[1]
    msg = sys.argv[2]
    repo = Path(__file__).resolve().parents[1]

    run(["git", "checkout", "-b", branch], cwd=str(repo))
    run(["git", "add", "-A"], cwd=str(repo))
    run(["git", "commit", "-m", msg], cwd=str(repo))
    run(["git", "push", "-u", "origin", branch], cwd=str(repo))


if __name__ == "__main__":
    main()
