#!/usr/bin/env python3
"""Continuous Optimization Engine - Incremental Self-Improvement Pipeline.

Coordinates the ecosystem's continuous self-optimization using:
- Culture Ship strategic healing cycles
- Smart Search incremental index updates
- Real metrics collection and analysis
- Automated code quality improvements
- Quest-driven capability evolution

NO SIMULATED PROGRESS. Only actual, useful, measurable improvements.

OmniTag: [orchestration, optimization, culture_ship, real_improvement, zero_token]
MegaTag: [CONTINUOUS_IMPROVEMENT, ANTI_SIMULATION, TRUTH, HEALING]
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OptimizationCycle:
    """Record of a single optimization cycle."""

    timestamp: str
    duration_seconds: float

    # Smart Search
    search_files_updated: int = 0
    search_files_removed: int = 0

    # Metrics
    health_score_before: float = 0.0
    health_score_after: float = 0.0
    health_improvement: float = 0.0

    # Culture Ship healing
    healing_issues_identified: int = 0
    healing_fixes_applied: int = 0

    # Real improvements
    files_fixed: int = 0
    tests_passed: int = 0
    capabilities_added: int = 0


class ContinuousOptimizationEngine:
    """Orchestrate continuous ecosystem self-optimization."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize optimization engine.

        Args:
            repo_root: Repository root directory
        """
        if repo_root is None:
            repo_root = Path(__file__).resolve().parents[2]
        self.repo_root = repo_root
        self.state_dir = repo_root / "state"
        self.src_dir = repo_root / "src"

        # Optimization history
        self.history_file = self.state_dir / "optimization_history.jsonl"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def run_single_cycle(self) -> OptimizationCycle:
        """Run a single optimization cycle.

        Returns:
            Cycle results
        """
        logger.info("🔄 Starting optimization cycle")
        start_time = time.time()

        cycle = OptimizationCycle(timestamp=datetime.now().isoformat(), duration_seconds=0.0)

        # Step 1: Collect baseline metrics
        cycle.health_score_before = self._collect_health_score()
        logger.info(f"   📊 Baseline health: {cycle.health_score_before:.1f}%")

        # Step 2: Update Smart Search index
        search_stats = self._update_search_index()
        cycle.search_files_updated = search_stats.get("files_updated", 0)
        cycle.search_files_removed = search_stats.get("files_removed", 0)
        logger.info(
            f"   🔍 Search index: +{cycle.search_files_updated} ~{cycle.search_files_removed}"
        )

        # Step 3: Run Culture Ship healing
        healing_stats = self._run_culture_ship_healing()
        cycle.healing_issues_identified = healing_stats.get("issues_identified", 0)
        cycle.healing_fixes_applied = healing_stats.get("fixes_applied", 0)
        logger.info(
            f"   🚀 Culture Ship: {cycle.healing_issues_identified} issues, {cycle.healing_fixes_applied} fixes"
        )

        # Step 4: Collect post-optimization metrics
        cycle.health_score_after = self._collect_health_score()
        cycle.health_improvement = cycle.health_score_after - cycle.health_score_before
        logger.info(
            f"   📈 Health improvement: {cycle.health_improvement:+.2f}% ({cycle.health_score_after:.1f}%)"
        )

        # Step 5: Broadcast metrics
        self._broadcast_metrics()

        cycle.duration_seconds = time.time() - start_time
        logger.info(f"✅ Cycle complete in {cycle.duration_seconds:.1f}s")

        # Save cycle to history
        self._save_cycle(cycle)

        return cycle

    def _collect_health_score(self) -> float:
        """Collect current system health score.

        Returns:
            Health score percentage
        """
        try:
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "src.diagnostics.real_system_metrics",
                    "--quiet",
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

            if result.returncode == 0:
                # Parse metrics from output file
                metrics_files = list(self.state_dir.glob("real_system_metrics_*.json"))
                if metrics_files:
                    latest = max(metrics_files, key=lambda f: f.stat().st_mtime)
                    with latest.open() as f:
                        metrics = json.load(f)
                    return metrics.get("health_score", 0.0)
        except Exception as e:
            logger.warning(f"Failed to collect health score: {e}")

        return 0.0

    def _update_search_index(self) -> dict[str, Any]:
        """Update Smart Search index incrementally.

        Returns:
            Update statistics
        """
        try:
            result = subprocess.run(
                [
                    "python",
                    str(self.src_dir / "search" / "index_builder.py"),
                    "--incremental",
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=300,
            )

            if result.returncode == 0:
                stats = json.loads(result.stdout)
                return stats
        except Exception as e:
            logger.warning(f"Failed to update search index: {e}")

        return {}

    def _run_culture_ship_healing(self) -> dict[str, Any]:
        """Run Culture Ship strategic healing cycle.

        Returns:
            Healing statistics
        """
        try:
            # Import Culture Ship advisor
            import sys

            sys.path.insert(0, str(self.src_dir))

            from orchestration.culture_ship_strategic_advisor import \
                CultureShipStrategicAdvisor

            advisor = CultureShipStrategicAdvisor()
            results = advisor.run_full_strategic_cycle()

            return {
                "issues_identified": results.get("issues_identified", 0),
                "fixes_applied": len(results.get("implementations", [])),
            }
        except Exception as e:
            logger.warning(f"Failed to run Culture Ship healing: {e}")

        return {}

    def _broadcast_metrics(self) -> None:
        """Broadcast metrics to terminals."""
        try:
            subprocess.run(
                [
                    "python",
                    "-m",
                    "src.output.metrics_terminal_broadcaster",
                    "--once",
                ],
                cwd=self.repo_root,
                capture_output=True,
                check=False,
                timeout=30,
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast metrics: {e}")

    def _save_cycle(self, cycle: OptimizationCycle) -> None:
        """Save cycle to history.

        Args:
            cycle: Cycle to save
        """
        with self.history_file.open("a") as f:
            f.write(json.dumps(asdict(cycle)) + "\n")

    def run_continuous(self, interval_minutes: int = 30) -> None:
        """Run continuous optimization cycles.

        Args:
            interval_minutes: Minutes between cycles (default: 30)
        """
        logger.info(f"🔁 Starting continuous optimization (every {interval_minutes} minutes)")

        try:
            while True:
                try:
                    self.run_single_cycle()
                except Exception as e:
                    logger.error(f"Cycle failed: {e}")

                # Wait for next cycle
                wait_seconds = interval_minutes * 60
                logger.info(f"⏳ Next cycle in {interval_minutes} minutes")
                time.sleep(wait_seconds)
        except KeyboardInterrupt:
            logger.info("🛑 Continuous optimization stopped")

    def get_optimization_history(self, limit: int = 10) -> list[OptimizationCycle]:
        """Get recent optimization history.

        Args:
            limit: Maximum number of cycles to return

        Returns:
            List of recent cycles
        """
        cycles = []

        if not self.history_file.exists():
            return cycles

        with self.history_file.open() as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                cycle = OptimizationCycle(**data)
                cycles.append(cycle)

        # Return most recent first
        return list(reversed(cycles[-limit:]))

    def print_history_summary(self, limit: int = 10) -> None:
        """Print summary of recent optimization history.

        Args:
            limit: Maximum number of cycles to show
        """
        cycles = self.get_optimization_history(limit)

        if not cycles:
            logger.info("No optimization history found")
            return

        logger.info("")
        logger.info("=== OPTIMIZATION HISTORY (REAL IMPROVEMENTS ONLY) ===")
        logger.info("")

        for i, cycle in enumerate(cycles, 1):
            timestamp = datetime.fromisoformat(cycle.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Cycle {i} - {timestamp} ({cycle.duration_seconds:.1f}s):")
            logger.info(
                f"  Health: {cycle.health_score_before:.1f}% → {cycle.health_score_after:.1f}% ({cycle.health_improvement:+.2f}%)"
            )
            logger.info(f"  Search: +{cycle.search_files_updated} files indexed")
            logger.info(
                f"  Healing: {cycle.healing_issues_identified} issues, {cycle.healing_fixes_applied} fixes"
            )
            logger.info("")

        # Overall statistics
        total_improvement = sum(c.health_improvement for c in cycles)
        total_fixes = sum(c.healing_fixes_applied for c in cycles)
        total_files_indexed = sum(c.search_files_updated for c in cycles)

        logger.info("=== CUMULATIVE IMPROVEMENTS ===")
        logger.info(f"Health improvement: {total_improvement:+.2f}%")
        logger.info(f"Fixes applied: {total_fixes}")
        logger.info(f"Files indexed: {total_files_indexed}")
        logger.info("")


def main() -> None:
    """CLI entry point for optimization engine."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Continuous ecosystem self-optimization engine")
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=30,
        help="Interval between cycles in minutes (default: 30)",
    )
    parser.add_argument("--once", action="store_true", help="Run single cycle and exit")
    parser.add_argument("--history", action="store_true", help="Show optimization history")

    args = parser.parse_args()

    engine = ContinuousOptimizationEngine()

    if args.history:
        engine.print_history_summary()
    elif args.once:
        engine.run_single_cycle()
    else:
        engine.run_continuous(interval_minutes=args.interval)


if __name__ == "__main__":
    main()
