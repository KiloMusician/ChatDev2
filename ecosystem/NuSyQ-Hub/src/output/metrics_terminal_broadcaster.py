#!/usr/bin/env python3
"""Metrics Terminal Broadcaster - Route Real System Metrics to Metrics Terminal.

Broadcasts real system metrics to the metrics terminal at regular intervals.
Replaces simulated metrics with actual data from the ecosystem.

OmniTag: [terminal_routing, metrics, real_data, zero_token]
MegaTag: [TRUTH, REALITY, ANTI_SIMULATION]
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from src.diagnostics.real_system_metrics import (RealSystemMetricsCollector,
                                                 SystemMetrics)
from src.output.terminal_integration import TerminalRouter

logger = logging.getLogger(__name__)


class MetricsTerminalBroadcaster:
    """Broadcast real system metrics to metrics terminal."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize broadcaster.

        Args:
            repo_root: Repository root directory
        """
        self.collector = RealSystemMetricsCollector(repo_root)
        self.router = TerminalRouter(repo_root)

    def format_metrics_for_terminal(self, metrics: SystemMetrics) -> str:
        """Format metrics for terminal display.

        Args:
            metrics: Metrics to format

        Returns:
            Formatted string for terminal
        """
        lines = [
            f"[{metrics.timestamp}] REAL SYSTEM METRICS (NO SIMULATION)",
            "",
            f"🏥 Health: {metrics.health_score:.1f}% ({metrics.working_files}/{metrics.total_files} working)",
            f"🎯 Quests: {metrics.quest_completion_rate:.1f}% complete ({metrics.completed_quests}/{metrics.total_quests}) | {metrics.total_xp_earned} XP",
            f"🔍 Search: {metrics.indexed_files:,} files indexed | <{metrics.search_performance_ms}ms queries",
            f"📊 Git: {metrics.commits_last_24h} commits (24h) | {metrics.commit_velocity_per_day:.1f}/day velocity",
            f"🚀 Culture Ship: {metrics.healing_cycles_run} healing cycles | {metrics.fixes_applied_total} fixes applied",
            f"⚡ PU Queue: {metrics.pu_success_rate:.1f}% success | {metrics.pu_tasks_completed} completed | {metrics.pu_tasks_pending} pending",
            f"🌱 Evolution: {metrics.new_capabilities_added} new capabilities (7d) | {metrics.integration_points_active} integrations | {metrics.zero_token_savings_percent:.0f}% token savings",
            "",
        ]
        return "\n".join(lines)

    def broadcast_once(self) -> SystemMetrics:
        """Collect and broadcast metrics once.

        Returns:
            Collected metrics
        """
        logger.info("📊 Broadcasting real system metrics...")

        # Collect metrics
        metrics = self.collector.collect_all()

        # Format for terminal
        message = self.format_metrics_for_terminal(metrics)

        # Route to metrics terminal
        self.router.write_to_terminal(message, terminal="metrics", level="INFO")

        logger.info("✅ Metrics broadcast complete")
        return metrics

    def broadcast_continuous(self, interval_seconds: int = 60) -> None:
        """Continuously broadcast metrics at regular intervals.

        Args:
            interval_seconds: Seconds between broadcasts (default: 60)
        """
        logger.info(f"📡 Starting continuous metrics broadcast (every {interval_seconds}s)")

        try:
            while True:
                try:
                    self.broadcast_once()
                except Exception as e:
                    logger.error(f"Failed to broadcast metrics: {e}")

                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("🛑 Metrics broadcast stopped")


def main() -> None:
    """CLI entry point for metrics broadcasting."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Broadcast real system metrics to metrics terminal"
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=60,
        help="Broadcast interval in seconds (default: 60)",
    )
    parser.add_argument("--once", action="store_true", help="Broadcast once and exit")

    args = parser.parse_args()

    broadcaster = MetricsTerminalBroadcaster()

    if args.once:
        broadcaster.broadcast_once()
    else:
        broadcaster.broadcast_continuous(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
