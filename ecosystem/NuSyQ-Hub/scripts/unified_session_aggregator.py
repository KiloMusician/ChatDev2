#!/usr/bin/env python3
"""Unified session aggregator — consolidate session logs across 3 repos.

Discovers and summarizes session log files from:
- NuSyQ-Hub: docs/Agent-Sessions/*.md
- SimulatedVerse: docs/Agent-Sessions/*.md (if exists)
- NuSyQ: docs/Agent-Sessions/*.md (if exists)

Categorizes by type (SPRINT, SESSION, PHASE, COMPLETION) and emits
consolidated receipt with progress timeline.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
RECEIPTS_DIR = REPO_ROOT / "state" / "receipts" / "cli"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

REPOS = {
    "hub": Path(__file__).resolve().parent.parent,
    "simverse": Path(__file__).resolve().parent.parent.parent / "SimulatedVerse" / "SimulatedVerse",
    "root": Path(__file__).resolve().parent.parent.parent.parent / "NuSyQ",
}


def infer_session_type(filename: str) -> str:
    """Infer session type from filename."""
    filename_lower = filename.lower()
    if "sprint" in filename_lower:
        return "SPRINT"
    elif "completion" in filename_lower or "complete" in filename_lower:
        return "COMPLETION"
    elif "phase" in filename_lower:
        return "PHASE"
    else:
        return "SESSION"


def extract_timestamp(filepath: Path) -> str:
    """Extract or derive timestamp from file."""
    # Try to parse from filename patterns like SPRINT_1_COMPLETION_20260110.md
    match = re.search(r"20\d{6}", filepath.name)
    if match:
        date_str = match.group()
        # Parse YYYYMMDD into ISO format
        try:
            dt = datetime.strptime(date_str, "%Y%m%d")
            return dt.isoformat()
        except ValueError:
            pass
    # Fall back to file modification time
    return datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()


def aggregate_sessions(repos_dict: dict[str, Path]) -> dict[str, Any]:
    """Aggregate sessions from all repos."""
    all_sessions: list[dict[str, Any]] = []
    repo_stats = {}

    for repo_name, repo_path in repos_dict.items():
        session_dir = repo_path / "docs" / "Agent-Sessions"
        if not session_dir.exists():
            repo_stats[repo_name] = {"found": False, "count": 0}
            continue

        repo_sessions: list[dict[str, Any]] = []
        for md_file in sorted(session_dir.glob("*.md"), reverse=True):
            session_type = infer_session_type(md_file.name)
            timestamp = extract_timestamp(md_file)
            repo_sessions.append(
                {
                    "name": md_file.name,
                    "type": session_type,
                    "repo": repo_name,
                    "timestamp": timestamp,
                    "size_bytes": md_file.stat().st_size,
                }
            )

        all_sessions.extend(repo_sessions)
        repo_stats[repo_name] = {
            "found": True,
            "count": len(repo_sessions),
            "types": {},
        }
        for sess in repo_sessions:
            t = sess["type"]
            repo_stats[repo_name]["types"][t] = repo_stats[repo_name]["types"].get(t, 0) + 1

    # Sort by timestamp descending
    all_sessions.sort(key=lambda s: s["timestamp"], reverse=True)

    # Type counts
    type_counts = {}
    for sess in all_sessions:
        t = sess["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "total_sessions": len(all_sessions),
        "by_type": type_counts,
        "recent": all_sessions[:10],
        "by_repo": repo_stats,
    }


def main() -> None:
    """Main entry point."""
    payload = aggregate_sessions(REPOS)

    # Save receipt
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    receipt_path = RECEIPTS_DIR / f"session_aggregator_{ts}.json"
    payload["timestamp"] = datetime.now().isoformat()
    payload["command"] = "session_aggregator"

    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"✓ Session aggregator receipt: {receipt_path}")
    print(f"\nTotal sessions: {payload['total_sessions']}")
    print(f"By type: {payload['by_type']}")
    print("\nBy repo:")
    for repo_name, stats in payload["by_repo"].items():
        if stats.get("found"):
            print(f"  {repo_name}: {stats['count']} sessions")
            for t, cnt in stats.get("types", {}).items():
                print(f"    - {t}: {cnt}")
        else:
            print(f"  {repo_name}: (not found)")

    print("\nRecent sessions (top 5):")
    for sess in payload["recent"][:5]:
        print(f"  [{sess['type']}] {sess['name']} ({sess['repo']})")


if __name__ == "__main__":
    main()
