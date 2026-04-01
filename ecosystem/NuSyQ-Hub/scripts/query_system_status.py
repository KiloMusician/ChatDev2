#!/usr/bin/env python3
"""Query-based system status replacement for static reports.

Instead of generating thousands of unused report files, query the database
when status is needed.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.duckdb_integration.realtime_status import get_realtime_status


def query_github_validation() -> None:
    """Query GitHub commit/validation events instead of generating reports."""
    print("\n📊 GitHub Validation Status (Last 7 Days)")
    print("=" * 60)

    status = get_realtime_status()

    # Query commit-related events
    results = status.query_custom(
        """
        SELECT
            DATE(timestamp) as date,
            COUNT(*) as events,
            SUM(CASE WHEN details LIKE '%success%' THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN details LIKE '%fail%' THEN 1 ELSE 0 END) as failed
        FROM events
        WHERE timestamp >= current_timestamp - INTERVAL 7 DAY
          AND (event LIKE '%commit%' OR event LIKE '%validation%' OR event LIKE '%github%')
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        """
    )

    if results:
        print("\nDate         | Events | Success | Failed")
        print("-" * 60)
        for row in results:
            date, events, successful, failed = row
            print(f"{date} | {events:6d} | {successful:7d} | {failed:6d}")
    else:
        print("\n⚠️  No GitHub validation events in last 7 days")
        print("💡 This replaces generating 2,151+ static report files")


def query_multi_repo_insights() -> None:
    """Query multi-repo activity instead of generating static reports."""
    print("\n🔍 Multi-Repo Insights")
    print("=" * 60)

    status = get_realtime_status()

    # Query by repo/component
    results = status.query_custom(
        """
        SELECT
            details->>'$.component' as component,
            COUNT(*) as events,
            MAX(timestamp) as last_activity
        FROM events
        WHERE timestamp >= current_timestamp - INTERVAL 7 DAY
          AND details LIKE '%component%'
        GROUP BY component
        ORDER BY events DESC
        LIMIT 15
        """
    )

    if results:
        print("\nComponent/Repo          | Events | Last Activity")
        print("-" * 60)
        for row in results:
            component, events, last_activity = row
            if component:
                # Format timestamp
                if isinstance(last_activity, str):
                    last_str = last_activity[:19]
                else:
                    last_str = last_activity.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{component:23s} | {events:6d} | {last_str}")
    else:
        print("\n⚠️  No multi-repo events tracked")
        print("💡 Add component tracking to events for better insights")


def query_system_health_metrics() -> None:
    """Query live system health metrics instead of static reports."""
    print("\n💚 System Health Metrics (Live)")
    print("=" * 60)

    status = get_realtime_status()

    # Event velocity (events per hour)
    velocity = status.query_custom(
        """
        SELECT COUNT(*) / 24.0 as events_per_hour
        FROM events
        WHERE timestamp >= current_timestamp - INTERVAL 24 HOUR
        """
    )

    # Most active event types
    top_events = status.query_custom(
        """
        SELECT event, COUNT(*) as count
        FROM events
        WHERE timestamp >= current_timestamp - INTERVAL 24 HOUR
        GROUP BY event
        ORDER BY count DESC
        LIMIT 5
        """
    )

    # Error rate
    errors = status.query_custom(
        """
        SELECT
            COUNT(*) as total_errors,
            COUNT(DISTINCT event) as error_types
        FROM events
        WHERE timestamp >= current_timestamp - INTERVAL 24 HOUR
          AND (event LIKE '%fail%' OR event LIKE '%error%' OR details LIKE '%error%')
        """
    )

    # Display metrics
    if velocity:
        events_per_hour = velocity[0][0] or 0
        print(f"\n📈 Event Velocity: {events_per_hour:.2f} events/hour")

    if errors:
        total_errors, error_types = errors[0]
        print(f"❌ Errors (24h): {total_errors} ({error_types} types)")

    if top_events:
        print("\n🔥 Top Event Types (24h):")
        for event, count in top_events:
            print(f"  {event:30s}: {count:4d}")

    # Database health
    db_path = Path("data/state.duckdb")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        total_events = status.query_custom("SELECT COUNT(*) FROM events")[0][0]
        print(f"\n💾 Database: {size_mb:.2f} MB, {total_events:,} events")


def query_token_efficiency() -> None:
    """Query token usage efficiency metrics."""
    print("\n🎯 Token Efficiency Metrics")
    print("=" * 60)

    status = get_realtime_status()

    # Query for token-related events
    token_events = status.query_custom(
        """
        SELECT
            COUNT(*) as optimized_operations,
            SUM(CASE WHEN details LIKE '%sns%' THEN 1 ELSE 0 END) as sns_usage,
            SUM(CASE WHEN details LIKE '%zero_token%' THEN 1 ELSE 0 END) as zero_token_usage
        FROM events
        WHERE timestamp >= current_timestamp - INTERVAL 7 DAY
          AND (details LIKE '%token%' OR details LIKE '%optimize%')
        """
    )

    if token_events and token_events[0][0] > 0:
        optimized, sns, zero_token = token_events[0]
        print(f"\n✅ Optimized Operations (7d): {optimized}")
        print(f"🔧 SNS-Core Usage: {sns}")
        print(f"⚡ Zero-Token Operations: {zero_token}")
    else:
        print("\n⚠️  No token efficiency events tracked")
        print("💡 Add token usage tracking to operations")


def main() -> None:
    """Run all status queries."""
    print("\n" + "=" * 60)
    print("  🎯 NuSyQ-Hub Status Queries (Replaces Static Reports)")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        query_github_validation()
        query_multi_repo_insights()
        query_system_health_metrics()
        query_token_efficiency()

        print("\n" + "=" * 60)
        print("  ✅ All Queries Complete")
        print("  💡 These queries replace thousands of static report files")
        print("  📊 Run anytime for up-to-date status")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Query Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
