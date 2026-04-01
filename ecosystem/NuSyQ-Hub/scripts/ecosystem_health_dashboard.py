#!/usr/bin/env python3
"""Three Before New Compliance Metrics Dashboard.

Tracks and reports on the effectiveness of the Three Before New protocol:
- New tool creation rate over time
- Discovery tool usage frequency
- Compliance rate (tools with proper justification in quest log)
- Top capabilities being searched
- Reuse vs greenfield ratio

Usage:
    python scripts/ecosystem_health_dashboard.py
    python scripts/ecosystem_health_dashboard.py --json
    python scripts/ecosystem_health_dashboard.py --days 30
"""

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def get_repo_root() -> Path:
    """Get repository root directory."""
    return Path(__file__).resolve().parent.parent


def count_new_tools_by_date(repo_root: Path, days: int = 30) -> dict[str, int]:
    """Count new files added in tool directories over time."""
    cutoff_date = datetime.now() - timedelta(days=days)

    # Git log for new files in tool directories
    result = subprocess.run(
        [
            "git",
            "log",
            "--since",
            cutoff_date.isoformat(),
            "--diff-filter=A",
            "--name-status",
            "--pretty=format:%ad",
            "--date=short",
            "--",
            "scripts/",
            "src/tools/",
            "src/utils/",
            "src/diagnostics/",
            "src/healing/",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    additions_by_date: dict[str, int] = defaultdict(int)
    current_date = None

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        if not line.startswith("A\t"):
            # Date line
            current_date = line
        else:
            # Addition line
            if current_date:
                additions_by_date[current_date] += 1

    return dict(sorted(additions_by_date.items()))


def parse_quest_log(repo_root: Path) -> list[dict[str, Any]]:
    """Parse quest log for Three Before New compliance entries."""
    quest_log_path = repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"

    if not quest_log_path.exists():
        return []

    entries = []
    with open(quest_log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("type") == "three_before_new":
                    entries.append(entry)
            except json.JSONDecodeError:
                continue

    return entries


def calculate_metrics(repo_root: Path, days: int = 30) -> dict[str, Any]:
    """Calculate Three Before New compliance metrics."""
    # Parse quest log entries
    tbn_entries = parse_quest_log(repo_root)

    # Count new tool additions from git
    additions_by_date = count_new_tools_by_date(repo_root, days)
    total_new_tools = sum(additions_by_date.values())

    # Count Three Before New compliant tools
    compliant_tools = len(tbn_entries)

    # Extract capability searches
    capabilities = [entry.get("capability", "unknown") for entry in tbn_entries]
    capability_counts = Counter(capabilities)

    # Calculate compliance rate
    compliance_rate = (compliant_tools / total_new_tools * 100) if total_new_tools > 0 else 0

    # Calculate average candidates found
    candidate_counts = [len(entry.get("candidates", [])) for entry in tbn_entries]
    avg_candidates = sum(candidate_counts) / len(candidate_counts) if candidate_counts else 0

    return {
        "period_days": days,
        "total_new_tools": total_new_tools,
        "compliant_tools": compliant_tools,
        "compliance_rate_pct": round(compliance_rate, 1),
        "avg_candidates_found": round(avg_candidates, 1),
        "top_capabilities": dict(capability_counts.most_common(10)),
        "additions_by_date": additions_by_date,
        "quest_log_entries": len(tbn_entries),
    }


def print_human_report(metrics: dict[str, Any]) -> None:
    """Print human-readable metrics report."""
    print("=" * 60)
    print("🏗️  THREE BEFORE NEW COMPLIANCE DASHBOARD")
    print("=" * 60)
    print(f"\n📅 Period: Last {metrics['period_days']} days\n")

    print("📊 SUMMARY METRICS")
    print("-" * 60)
    print(f"  Total new tools created:        {metrics['total_new_tools']}")
    print(f"  Tools with TBN compliance:      {metrics['compliant_tools']}")
    print(f"  Compliance rate:                {metrics['compliance_rate_pct']}%")
    print(f"  Avg candidates found per tool:  {metrics['avg_candidates_found']}")
    print(f"  Quest log entries:              {metrics['quest_log_entries']}")

    print("\n🔍 TOP CAPABILITIES SEARCHED")
    print("-" * 60)
    for capability, count in metrics["top_capabilities"].items():
        print(f"  {capability:30s} ({count}x)")

    if metrics["additions_by_date"]:
        print("\n📈 NEW TOOL CREATION TIMELINE")
        print("-" * 60)
        for date, count in list(metrics["additions_by_date"].items())[:10]:
            print(f"  {date}: {count} new tools")

    print("\n" + "=" * 60)

    # Health assessment
    compliance = metrics["compliance_rate_pct"]
    if compliance >= 70:
        status = "✅ EXCELLENT"
    elif compliance >= 40:
        status = "⚠️  NEEDS IMPROVEMENT"
    else:
        status = "🚨 CRITICAL - Brownfield pollution detected"

    print(f"Health Status: {status}")
    print("=" * 60)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Three Before New compliance metrics dashboard")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of human-readable report",
    )

    args = parser.parse_args()
    repo_root = get_repo_root()

    metrics = calculate_metrics(repo_root, days=args.days)

    if args.json:
        print(json.dumps(metrics, indent=2))
    else:
        print_human_report(metrics)


if __name__ == "__main__":
    main()
