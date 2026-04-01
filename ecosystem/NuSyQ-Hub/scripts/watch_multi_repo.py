#!/usr/bin/env python3
r"""Multi-Repo File Watcher

Monitors *.py, *.ts, *.md files across all 3 repositories:
- NuSyQ-Hub
- SimulatedVerse
- NuSyQ

Polling every 5 seconds; logs changes to state/receipts/watch/

Features:
- File modification detection (size/mtime)
- Max 10 changes per report (prevents spam)
- Receipt logging with ISO timestamp
- Per-repo change tracking
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# Repository configurations
REPOS = {
    "hub": {
        "path": Path(__file__).resolve().parent.parent,
        "extensions": [".py", ".md"],
    },
    "simverse": {
        "path": Path(__file__).resolve().parent.parent.parent / "SimulatedVerse" / "SimulatedVerse",
        "extensions": [".ts", ".js", ".py", ".md"],
    },
    "root": {
        "path": Path(__file__).resolve().parent.parent.parent.parent / "NuSyQ",
        "extensions": [".py", ".yaml", ".md"],
    },
}

WATCH_DIR = Path(__file__).resolve().parent.parent / "state" / "receipts" / "watch"
WATCH_DIR.mkdir(parents=True, exist_ok=True)

# State file to track file metadata
STATE_FILE = WATCH_DIR / "file_state.json"


def load_state() -> dict[str, dict[str, Any]]:
    """Load previous file state from disk."""
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            data: dict[str, dict[str, Any]] = json.load(f)
            return data
    return {}


def save_state(state: dict[str, dict[str, Any]]) -> None:
    """Save current file state to disk."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=str)


def get_file_signature(path: Path) -> dict[str, Any]:
    """Get file modification signature (size, mtime)."""
    try:
        stat = path.stat()
        return {
            "size": stat.st_size,
            "mtime": stat.st_mtime,
        }
    except (OSError, FileNotFoundError):
        return {}


def scan_repo(repo_name: str, repo_config: dict[str, Any]) -> list[dict[str, Any]]:
    """Scan repository for modified files."""
    changes: list[dict[str, Any]] = []
    repo_path = repo_config["path"]
    extensions = repo_config["extensions"]

    if not repo_path.exists():
        return []

    for ext in extensions:
        for file_path in repo_path.rglob(f"*{ext}"):
            # Skip hidden/system directories
            if "/.git" in str(file_path) or "\\.git" in str(file_path):
                continue
            if "/__pycache__" in str(file_path) or "\\__pycache__" in str(file_path):
                continue
            if "/node_modules" in str(file_path) or "\\node_modules" in str(file_path):
                continue
            if "/.venv" in str(file_path) or "\\.venv" in str(file_path):
                continue

            rel_path = file_path.relative_to(repo_path)

            current_sig = get_file_signature(file_path)
            if not current_sig:
                continue

            changes.append(
                {
                    "repo": repo_name,
                    "file": str(rel_path),
                    "size": current_sig["size"],
                    "mtime": current_sig["mtime"],
                }
            )

    return changes


def watch_cycle() -> None:
    """Single watch cycle: scan all repos, detect changes, write receipt."""
    state = load_state()
    all_changes: list[dict[str, Any]] = []
    by_repo: dict[str, int] = {}

    # Scan all repos
    for repo_name, repo_config in REPOS.items():
        changes = scan_repo(repo_name, repo_config)
        for change in changes:
            key = f"{repo_name}/{change['file']}"
            current_sig = {"size": change["size"], "mtime": change["mtime"]}

            # Check if file is new or modified
            if key not in state:
                all_changes.append({"type": "new", **change})
                by_repo[repo_name] = by_repo.get(repo_name, 0) + 1
            elif state[key] != current_sig:
                all_changes.append({"type": "modified", **change})
                by_repo[repo_name] = by_repo.get(repo_name, 0) + 1

            state[key] = current_sig

    # Save updated state
    save_state(state)

    # Write receipt if there are changes
    if all_changes:
        # Limit to 10 most recent changes
        all_changes = sorted(all_changes, key=lambda c: c["mtime"], reverse=True)[:10]

        receipt_path = WATCH_DIR / f"watch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        receipt = {
            "timestamp": datetime.now().isoformat(),
            "total_changes": len(all_changes),
            "by_repo": by_repo,
            "changes": all_changes,
        }

        with open(receipt_path, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2, default=str)

        print(f"📝 Watch receipt: {receipt_path}")
        print(f"   Total changes: {len(all_changes)}")
        for repo, count in by_repo.items():
            print(f"   {repo}: {count} files")


def list_receipts(limit: int = 10) -> None:
    """List recent watch receipts."""
    receipts = sorted(WATCH_DIR.glob("watch_*.json"), reverse=True)[:limit]
    if not receipts:
        print("No watch receipts found yet.")
        return

    print(f"📊 Recent Watch Receipts (last {len(receipts)}):")
    for receipt in receipts:
        with open(receipt, encoding="utf-8") as f:
            data = json.load(f)
        total = data.get("total_changes", 0)
        by_repo = data.get("by_repo", {})
        print(f"  {receipt.name}: {total} changes")
        for repo, count in by_repo.items():
            print(f"    └─ {repo}: {count}")


def main() -> None:
    """Main entry point."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        list_receipts(limit)
    else:
        print("🔍 Starting file watcher (single cycle)...")
        watch_cycle()
        print("✓ Watch cycle complete")


if __name__ == "__main__":
    main()
