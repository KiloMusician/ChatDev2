"""Quest Query Interface - Agent-friendly quest log querying and continuation.

This module provides natural language commands for agents to:
- Query recent quests (what was I working on?)
- Continue from last session (where did I leave off?)
- View quest dependencies (what depends on what?)
- Check quest completion status (what's done?)

Usage:
    python scripts/start_nusyq.py quest_query --recent --limit=10
    python scripts/start_nusyq.py quest_continue
    python scripts/start_nusyq.py quest_graph --format mermaid
    python scripts/start_nusyq.py quest_status --incomplete
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# Quest log location
QUEST_LOG_PATH = Path(__file__).parent.parent / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"


def read_quest_log() -> list[dict[str, Any]]:
    """Read all quests from quest log."""
    if not QUEST_LOG_PATH.exists():
        return []

    quests: list[dict[str, Any]] = []
    with open(QUEST_LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    quest = json.loads(line)
                    quests.append(quest)
                except json.JSONDecodeError:
                    continue
    return quests


def query_recent_quests(limit: int = 10, quest_type: str | None = None) -> list[dict[str, Any]]:
    """Query recent quests with optional type filter.

    Args:
        limit: Maximum number of quests to return
        quest_type: Optional filter by quest type (council_loop, testing_chamber, etc.)

    Returns:
        List of recent quest dictionaries
    """
    quests = read_quest_log()

    if quest_type:
        quests = [q for q in quests if q.get("type") == quest_type]

    # Return most recent first
    return quests[-limit:][::-1]


def get_incomplete_quests() -> list[dict[str, Any]]:
    """Get all quests that are not completed."""
    quests = read_quest_log()
    return [q for q in quests if q.get("status") not in ("completed", "success", "graduated")]


def get_last_quest() -> dict[str, Any] | None:
    """Get the most recent quest."""
    quests = read_quest_log()
    return quests[-1] if quests else None


def get_quest_dependencies() -> dict[str, list[str]]:
    """Extract quest dependencies from quest log.

    Returns:
        Dict mapping quest IDs to list of dependency quest IDs
    """
    quests = read_quest_log()
    dependencies: dict[str, list[str]] = {}

    for quest in quests:
        quest_id = quest.get("quest_id") or quest.get("loop_id") or quest.get("prototype") or quest.get("timestamp")
        if quest_id:
            # Extract dependencies from quest (if present in metadata/context)
            deps = quest.get("dependencies", [])
            if isinstance(deps, list):
                dependencies[str(quest_id)] = [str(d) for d in deps]

    return dependencies


def generate_quest_graph(format: str = "text") -> str:
    """Generate visual quest dependency graph.

    Args:
        format: Output format ('text', 'mermaid', 'dot')

    Returns:
        Graph representation as string
    """
    quests = read_quest_log()
    dependencies = get_quest_dependencies()

    if format == "mermaid":
        lines = ["graph TD", ""]

        # Add nodes
        for quest in quests[-20:]:  # Last 20 quests
            quest_id = quest.get("quest_id") or quest.get("loop_id") or quest.get("prototype") or ""
            if quest_id:
                quest_type = quest.get("type", "unknown")
                status = quest.get("status", "unknown")
                node_id = str(quest_id).replace("-", "_")
                label = f"{quest_type}_{status}"

                # Color code by status
                if status in ("completed", "success", "graduated"):
                    lines.append(f'    {node_id}["{label}"]:::completed')
                elif status in ("failed", "abandoned"):
                    lines.append(f'    {node_id}["{label}"]:::failed')
                else:
                    lines.append(f'    {node_id}["{label}"]:::in_progress')

        # Add edges
        for quest_id, deps in dependencies.items():
            node_id = str(quest_id).replace("-", "_")
            for dep in deps:
                dep_id = str(dep).replace("-", "_")
                lines.append(f"    {dep_id} --> {node_id}")

        # Add styling
        lines.extend(
            [
                "",
                "    classDef completed fill:#90EE90",
                "    classDef failed fill:#FFB6C1",
                "    classDef in_progress fill:#87CEEB",
            ]
        )

        return "\n".join(lines)

    elif format == "dot":
        lines = ["digraph QuestGraph {", "    rankdir=LR;", ""]

        # Add nodes
        for quest in quests[-20:]:
            quest_id = quest.get("quest_id") or quest.get("loop_id") or quest.get("prototype") or ""
            if quest_id:
                quest_type = quest.get("type", "unknown")
                status = quest.get("status", "unknown")
                node_id = str(quest_id).replace("-", "_")

                # Color code by status
                color = (
                    "lightgreen"
                    if status in ("completed", "success", "graduated")
                    else "lightcoral"
                    if status in ("failed", "abandoned")
                    else "lightblue"
                )

                lines.append(f'    {node_id} [label="{quest_type}\\n{status}", style=filled, fillcolor={color}];')

        # Add edges
        for quest_id, deps in dependencies.items():
            node_id = str(quest_id).replace("-", "_")
            for dep in deps:
                dep_id = str(dep).replace("-", "_")
                lines.append(f"    {dep_id} -> {node_id};")

        lines.append("}")
        return "\n".join(lines)

    else:  # text format
        lines = ["Quest Dependency Graph (last 20 quests):", ""]

        for quest in quests[-20:]:
            quest_id = quest.get("quest_id") or quest.get("loop_id") or quest.get("prototype") or ""
            if quest_id:
                quest_type = quest.get("type", "unknown")
                status = quest.get("status", "unknown")

                status_symbol = (
                    "✅"
                    if status in ("completed", "success", "graduated")
                    else "❌"
                    if status in ("failed", "abandoned")
                    else "🔄"
                )

                deps = dependencies.get(str(quest_id), [])
                dep_str = f" (depends on: {', '.join(deps)})" if deps else ""

                lines.append(f"{status_symbol} {quest_type}: {quest_id}{dep_str}")

        return "\n".join(lines)


def continue_from_last_quest() -> dict[str, Any]:
    """Get context for continuing from last quest.

    Returns:
        Dictionary with last quest info and suggested next actions
    """
    last_quest = get_last_quest()

    if not last_quest:
        return {
            "status": "no_quests_found",
            "message": "No previous quests found in quest log.",
            "suggested_actions": [
                "Start a new quest with: python scripts/start_nusyq.py council_loop --demo",
                "Create a prototype with: python scripts/start_nusyq.py testing_chamber create <name>",
                "Check system health with: python scripts/start_nusyq.py doctor",
            ],
        }

    status = last_quest.get("status", "unknown")
    quest_id = last_quest.get("quest_id") or last_quest.get("loop_id") or last_quest.get("prototype")

    # Determine suggested actions based on last quest
    suggested_actions: list[str] = []

    if status in ("completed", "success", "graduated"):
        suggested_actions.extend(
            [
                f'Last quest "{quest_id}" completed successfully.',
                "Start next logical task:",
                '  - Run another closed loop: python scripts/start_nusyq.py council_loop "new task"',
                "  - Graduate a prototype: python scripts/start_nusyq.py testing_chamber graduate <name>",
                "  - Check for errors: python scripts/start_nusyq.py analyze_errors --prioritize",
            ]
        )
    elif status in ("failed", "abandoned"):
        suggested_actions.extend(
            [
                f'Last quest "{quest_id}" failed or was abandoned.',
                "Investigate or retry:",
                "  - Check error logs for details",
                '  - Retry with: python scripts/start_nusyq.py council_loop "same task description"',
                "  - Or start a different approach",
            ]
        )
    else:  # in progress or unknown
        suggested_actions.extend(
            [
                f'Last quest "{quest_id}" is in progress or status unknown.',
                "Continue or check status:",
                "  - View quest details in quest_log.jsonl",
                "  - Check if action is still running",
                "  - Or start a new quest if previous one is stuck",
            ]
        )

    return {"status": "found", "last_quest": last_quest, "suggested_actions": suggested_actions}


def main():
    """Command-line interface for quest querying."""
    parser = argparse.ArgumentParser(description="Quest Query Interface")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Query recent quests
    query_parser = subparsers.add_parser("query", help="Query recent quests")
    query_parser.add_argument("--limit", type=int, default=10, help="Max number of quests to show")
    query_parser.add_argument("--type", type=str, help="Filter by quest type")
    query_parser.add_argument("--incomplete", action="store_true", help="Show only incomplete quests")

    # Continue from last quest
    subparsers.add_parser("continue", help="Get context to continue from last quest")

    # Generate quest graph
    graph_parser = subparsers.add_parser("graph", help="Generate quest dependency graph")
    graph_parser.add_argument(
        "--format", choices=["text", "mermaid", "dot"], default="text", help="Graph output format"
    )
    graph_parser.add_argument("--output", type=str, help="Output file (default: stdout)")

    # Quest status
    subparsers.add_parser("status", help="Show quest status summary")

    args = parser.parse_args()

    if args.command == "query":
        if args.incomplete:
            quests = get_incomplete_quests()
            print(f"Incomplete Quests ({len(quests)}):")
            print("=" * 60)
        else:
            quests = query_recent_quests(limit=args.limit, quest_type=args.type)
            print(f"Recent Quests (last {len(quests)}):")
            print("=" * 60)

        for quest in quests:
            quest_type = quest.get("type", "unknown")
            status = quest.get("status", "unknown")
            quest_id = quest.get("quest_id") or quest.get("loop_id") or quest.get("prototype") or "unknown"
            timestamp = quest.get("timestamp", "unknown")

            print(f"\n[{timestamp}]")
            print(f"  Type: {quest_type}")
            print(f"  ID: {quest_id}")
            print(f"  Status: {status}")

            # Show additional details if available
            if "description" in quest:
                print(f"  Description: {quest['description']}")
            if "result" in quest:
                print(f"  Result: {quest['result']}")

    elif args.command == "continue":
        context = continue_from_last_quest()

        print("Continue from Last Quest")
        print("=" * 60)
        print(f"\nStatus: {context['status']}")

        if context["status"] == "found":
            last_quest = context["last_quest"]
            print("\nLast Quest:")
            print(f"  Type: {last_quest.get('type', 'unknown')}")
            print(f"  ID: {last_quest.get('quest_id') or last_quest.get('loop_id') or last_quest.get('prototype')}")
            print(f"  Status: {last_quest.get('status', 'unknown')}")
            print(f"  Timestamp: {last_quest.get('timestamp', 'unknown')}")

        print("\nSuggested Actions:")
        for action in context["suggested_actions"]:
            print(f"  {action}")

    elif args.command == "graph":
        graph = generate_quest_graph(format=args.format)

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(graph, encoding="utf-8")
            print(f"Quest graph written to: {output_path}")
        else:
            print(graph)

    elif args.command == "status":
        quests = read_quest_log()

        print("Quest System Status")
        print("=" * 60)
        print(f"\nTotal Quests: {len(quests)}")

        # Count by status
        status_counts: dict[str, int] = {}
        for quest in quests:
            status = quest.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        print("\nBy Status:")
        for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            status_symbol = (
                "✅"
                if status in ("completed", "success", "graduated")
                else "❌"
                if status in ("failed", "abandoned")
                else "🔄"
            )
            print(f"  {status_symbol} {status}: {count}")

        # Count by type
        type_counts: dict[str, int] = {}
        for quest in quests:
            quest_type = quest.get("type", "unknown")
            type_counts[quest_type] = type_counts.get(quest_type, 0) + 1

        print("\nBy Type:")
        for quest_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {quest_type}: {count}")

        # Show recent activity
        recent_quests = quests[-5:]
        print("\nRecent Activity:")
        for quest in recent_quests[::-1]:
            quest_type = quest.get("type", "unknown")
            status = quest.get("status", "unknown")
            timestamp = quest.get("timestamp", "unknown")
            status_symbol = (
                "✅"
                if status in ("completed", "success", "graduated")
                else "❌"
                if status in ("failed", "abandoned")
                else "🔄"
            )
            print(f"  {status_symbol} [{timestamp}] {quest_type} - {status}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
