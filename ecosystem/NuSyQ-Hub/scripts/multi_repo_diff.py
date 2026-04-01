#!/usr/bin/env python3
r"""Multi-Repo Diff Viewer

Shows uncommitted changes (git diff) across all 3 repositories:
- NuSyQ-Hub
- SimulatedVerse
- NuSyQ

Features:
- Per-repo git status and diff summary
- Optional --since-commit to show changes since a specific commit
- Receipt logging with change summaries
- File counts by change type (modified, added, deleted, renamed)
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def get_repo_root() -> Path:
    """Get NuSyQ-Hub root (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


REPOS = {
    "hub": {
        "path": get_repo_root(),
    },
    "simverse": {
        "path": get_repo_root().parent / "SimulatedVerse" / "SimulatedVerse",
    },
    "root": {
        "path": get_repo_root().parent.parent / "NuSyQ",
    },
}

RECEIPTS_DIR = get_repo_root() / "state" / "receipts" / "diff"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


def run_git_cmd(repo_path: Path, cmd: list[str]) -> tuple[int, str, str]:
    """Run git command in a specific repo."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(repo_path),
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return -1, "", "Git command timed out or git not found"


def get_repo_diff(repo_name: str, repo_path: Path, since_commit: str | None = None) -> dict[str, Any]:
    """Get diff information for a repository."""
    if not repo_path.exists():
        return {
            "repo": repo_name,
            "status": "missing",
            "path": str(repo_path),
        }

    # Check if it's a git repo
    is_git = (repo_path / ".git").exists()
    if not is_git:
        return {
            "repo": repo_name,
            "status": "not_git",
            "path": str(repo_path),
        }

    # Get status
    exit_code, status_out, _ = run_git_cmd(repo_path, ["git", "status", "--porcelain"])
    if exit_code != 0:
        return {
            "repo": repo_name,
            "status": "error",
            "error": "Failed to run git status",
        }

    # Parse status output
    staged_count = 0
    unstaged_count = 0
    for line in status_out.split("\n"):
        if not line:
            continue
        if line[0] in ["M", "A", "D", "R", "C"]:
            staged_count += 1
        if line[1] in ["M", "D"]:
            unstaged_count += 1

    # Get actual diff
    diff_args = ["git", "diff", "--stat"]
    if since_commit:
        diff_args.append(since_commit)

    exit_code, diff_out, _ = run_git_cmd(repo_path, diff_args)

    # Count files changed
    file_count = 0
    for line in diff_out.split("\n"):
        if " | " in line and ("insertion" in line or "deletion" in line):
            file_count += 1

    # Get current branch
    _, branch, _ = run_git_cmd(repo_path, ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    branch = branch.strip()

    return {
        "repo": repo_name,
        "path": str(repo_path),
        "status": "ok",
        "branch": branch,
        "staged_changes": staged_count,
        "unstaged_changes": unstaged_count,
        "files_changed": file_count,
        "diff_summary": diff_out[:500],  # First 500 chars
    }


def cmd_diff_viewer(since_commit: str | None = None) -> None:
    """Show diff information for all repos."""
    print("🔍 Multi-Repo Diff Viewer")
    print("=" * 60)

    all_diffs: list[dict[str, Any]] = []
    total_files_changed = 0

    for repo_name, repo_config in REPOS.items():
        repo_path = repo_config["path"]
        diff_info = get_repo_diff(repo_name, repo_path, since_commit)
        all_diffs.append(diff_info)

        print(f"\n📂 {repo_name.upper()}")
        print(f"   Path: {diff_info.get('path', 'N/A')}")

        if diff_info.get("status") == "ok":
            print(f"   Branch: {diff_info.get('branch', 'N/A')}")
            staged = diff_info.get("staged_changes", 0)
            unstaged = diff_info.get("unstaged_changes", 0)
            files = diff_info.get("files_changed", 0)
            print(f"   Staged: {staged}, Unstaged: {unstaged}, Files changed: {files}")
            total_files_changed += files
            if files > 0:
                print(f"   Diff:\n{diff_info.get('diff_summary', 'N/A')}")
        else:
            status = diff_info.get("status", "unknown")
            print(f"   Status: {status}")
            if "error" in diff_info:
                print(f"   Error: {diff_info['error']}")

    # Write receipt
    payload = {
        "timestamp": datetime.now().isoformat(),
        "since_commit": since_commit,
        "total_files_changed": total_files_changed,
        "repos": all_diffs,
    }

    receipt_path = RECEIPTS_DIR / f"diff_viewer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"\n✓ Diff receipt: {receipt_path}")
    print(f"  Total files changed: {total_files_changed}")


def main() -> None:
    """Main entry point."""
    import sys

    since_commit = None
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("--since-commit="):
            since_commit = sys.argv[1].split("=", 1)[1]

    cmd_diff_viewer(since_commit)


if __name__ == "__main__":
    main()
