#!/usr/bin/env python3
"""Realtime NuSyQ-Hub Dashboard using DuckDB queries.

Replaces static report generation with live SQL queries.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.duckdb_integration.realtime_status import get_realtime_status


def print_section(title: str) -> None:
    """Print section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_quest_dashboard() -> None:
    """Display quest statistics dashboard."""
    print_section("📋 QUEST DASHBOARD")

    status = get_realtime_status()
    stats = status.get_quest_stats()

    print(f"\nTotal Quests: {stats['total']}")
    print(f"  🟢 Open:        {stats['open']}")
    print(f"  🔵 In Progress: {stats['in_progress']}")
    print(f"  ✅ Done:        {stats['done']}")
    print(f"  ⛔ Abandoned:   {stats['abandoned']}")

    # Active quests
    active = status.get_active_quests()
    if active:
        print(f"\n🎯 Active Quests ({len(active)}):")
        for quest in active[:10]:  # Show top 10
            priority_emoji = "🔴" if quest["priority"] >= 4 else "🟡" if quest["priority"] >= 2 else "🟢"
            print(f"  {priority_emoji} [{quest['status']}] {quest['title'][:50]}")


def print_event_timeline() -> None:
    """Display recent event timeline."""
    print_section("📊 EVENT TIMELINE (Last 20 Events)")

    status = get_realtime_status()
    events = status.get_recent_events(limit=20)

    for event in events:
        # Handle both string and datetime timestamps
        timestamp = event["timestamp"]
        if isinstance(timestamp, str):
            timestamp = timestamp[:19]  # Remove milliseconds
        else:
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        event_type = event["event"]

        # Format event type for display
        emoji = {
            "quest_added": "+",
            "quest_updated": "🔄",
            "quest_completed": "✅",
            "culture_ship_decision": "🚢",
            "task_submitted": "📤",
            "pu_started": "⚙️",
            "pu_completed": "✅",
            "pu_failed": "❌",
        }.get(event_type, "📌")

        print(f"  {timestamp} {emoji} {event_type}")


def print_event_counts() -> None:
    """Display event counts by type."""
    print_section("📈 EVENT ACTIVITY (Last 24 Hours)")

    status = get_realtime_status()
    counts = status.get_event_counts_by_type(hours=24)

    if counts:
        # Sort by count descending
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        for event_type, count in sorted_counts[:15]:  # Top 15
            bar = "█" * min(count, 40)  # Visual bar
            print(f"  {event_type:30s} {count:4d} {bar}")
    else:
        print("  No events in last 24 hours")


def print_agent_activity() -> None:
    """Display agent activity heatmap."""
    print_section("🤖 AGENT ACTIVITY")

    status = get_realtime_status()

    # Query agent assignments from active quests (future: display per-agent heatmap)
    active_quests = status.get_active_quests()
    for _quest in active_quests:
        # Placeholder: quests currently lack agent assignment metadata
        # This loop intentionally no-ops until data is available.
        pass

    # Query PU assignments
    pu_events = status.query_custom(
        """
        SELECT details->>'$.assigned_agents' as agents, COUNT(*) as count
        FROM events
        WHERE event = 'pu_started'
          AND timestamp >= current_timestamp - INTERVAL 24 HOUR
        GROUP BY agents
        ORDER BY count DESC
        LIMIT 10
        """
    )

    if pu_events:
        print("\n🎯 Most Active Agents (PU Executions - Last 24h):")
        for agents_json, count in pu_events:
            print(f"  {agents_json}: {count} tasks")
    else:
        print("\n  No agent activity in last 24 hours")


def print_system_health() -> None:
    """Display system health metrics."""
    print_section("💚 SYSTEM HEALTH")

    status = get_realtime_status()

    # Recent errors/failures
    error_count = status.query_custom(
        """
        SELECT COUNT(*)
        FROM events
        WHERE event IN ('pu_failed', 'quest_abandoned')
          AND timestamp >= current_timestamp - INTERVAL 24 HOUR
        """
    )

    # Success rate
    pu_total = status.query_custom(
        """
        SELECT COUNT(*)
        FROM events
        WHERE event IN ('pu_completed', 'pu_failed')
          AND timestamp >= current_timestamp - INTERVAL 24 HOUR
        """
    )

    pu_success = status.query_custom(
        """
        SELECT COUNT(*)
        FROM events
        WHERE event = 'pu_completed'
          AND timestamp >= current_timestamp - INTERVAL 24 HOUR
        """
    )

    errors = error_count[0][0] if error_count else 0
    total_pu = pu_total[0][0] if pu_total else 0
    success_pu = pu_success[0][0] if pu_success else 0

    print(f"\n❌ Errors/Failures (24h): {errors}")

    if total_pu > 0:
        success_rate = (success_pu / total_pu) * 100
        print(f"✅ PU Success Rate (24h): {success_rate:.1f}% ({success_pu}/{total_pu})")
    else:
        print("✅ PU Success Rate (24h): No PU executions")

    # Database size
    db_path = Path("data/state.duckdb")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"💾 Database Size: {size_mb:.2f} MB")


def main() -> None:
    """Display realtime dashboard."""
    print("\n" + "=" * 60)
    print("  🎯 NuSyQ-Hub Realtime Dashboard")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        print_quest_dashboard()
        print_event_timeline()
        print_event_counts()
        print_agent_activity()
        print_system_health()

        print("\n" + "=" * 60)
        print("  ✅ Dashboard Complete")
        print("  💡 Run 'python scripts/dashboard.py' anytime for live status")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Dashboard Error: {e}")
        print("   Ensure DuckDB is populated with events")


if __name__ == "__main__":
    main()
