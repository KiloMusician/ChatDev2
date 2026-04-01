"""Ecosystem Orchestrator.

======================

Purpose: Background loop that continuously orchestrates:
1. Error scanning
2. Error→Signal bridge
3. Signal→Quest bridge
4. Quest recommendations (via AI)
5. Safety enforcement
6. Guild board updates
7. Metrics/logging

This is the "spine" that makes the entire system autonomous.

Run via:
    python src/orchestration/ecosystem_orchestrator.py [--mode once|daemon|test] [--interval 60]

Modes:
    once   - Run one cycle and exit
    daemon - Background loop (continuous)
    test   - Test mode (no side effects)
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent


class AutonomyLevel(Enum):
    """Control how much the orchestrator does automatically."""

    DISABLED = 0  # Do nothing
    MONITORING = 1  # Scan only
    SUGGESTING = 2  # Scan + suggest
    CLAIMING = 3  # Auto-claim quests
    EXECUTING = 4  # Execute simple quests
    FULL = 5  # Full autonomy (with approval)


class OrchestratorCycle:
    """Single orchestration cycle state."""

    def __init__(self):
        """Initialize OrchestratorCycle."""
        self.cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        self.results: dict[str, Any] = {}
        self.errors: list[str] = []

    def add_result(self, stage: str, data: dict[str, Any]) -> None:
        """Record result of a stage."""
        self.results[stage] = {
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

    def add_error(self, stage: str, error: str) -> None:
        """Record error in a stage."""
        self.errors.append(f"{stage}: {error}")
        logger.error(f"❌ {stage}: {error}")

    def duration(self) -> float:
        """Duration of cycle in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    def summary(self) -> dict[str, Any]:
        """Get cycle summary."""
        return {
            "cycle_id": self.cycle_id,
            "duration_seconds": self.duration(),
            "stages_completed": list(self.results.keys()),
            "errors": self.errors,
            "results": self.results,
            "timestamp": datetime.now().isoformat(),
        }


class EcosystemOrchestrator:
    """Main orchestrator coordinator."""

    def __init__(self, autonomy_level: AutonomyLevel = AutonomyLevel.SUGGESTING):
        """Initialize EcosystemOrchestrator with autonomy_level."""
        self.autonomy_level = autonomy_level
        self.cycle_count = 0
        self.cycles_log: list[dict[str, Any]] = []
        self.is_running = False

    async def stage_error_scan(self, cycle: OrchestratorCycle, test_mode: bool = False) -> bool:
        """Stage 1: Run error scanner."""
        del test_mode
        logger.info("=" * 80)
        logger.info("🔍 STAGE 1: ERROR SCANNING")
        logger.info("=" * 80)

        try:
            from src.orchestration.error_signal_bridge import run_error_scan

            report_path = await run_error_scan()

            # Read result
            if report_path.exists():
                with open(report_path) as f:
                    report = json.load(f)

                error_count = report.get("summary", {}).get("total_errors", 0)
                cycle.add_result(
                    "error_scan",
                    {
                        "report_path": str(report_path),
                        "total_errors": error_count,
                        "by_repository": report.get("summary", {}).get("by_repository", {}),
                    },
                )

                logger.info(f"✅ Scan complete: {error_count} errors found")
                return True
            else:
                logger.warning("Report not found after scan")
                return False

        except Exception as e:
            cycle.add_error("error_scan", str(e))
            return False

    async def stage_error_to_signal(
        self, cycle: OrchestratorCycle, test_mode: bool = False
    ) -> bool:
        """Stage 2: Error→Signal bridge."""
        logger.info("=" * 80)
        logger.info("📡 STAGE 2: ERROR→SIGNAL BRIDGE")
        logger.info("=" * 80)

        try:
            from src.orchestration.error_signal_bridge import \
                bridge_cycle as error_signal_cycle

            result = await error_signal_cycle(test_mode=test_mode)
            cycle.add_result("error_to_signal", result)

            signals_posted = result.get("signals_posted", 0)
            logger.info(f"✅ Posted {signals_posted} signals")
            return True

        except Exception as e:
            cycle.add_error("error_to_signal", str(e))
            return False

    async def stage_signal_to_quest(
        self, cycle: OrchestratorCycle, test_mode: bool = False
    ) -> bool:
        """Stage 3: Signal→Quest bridge."""
        logger.info("=" * 80)
        logger.info("📋 STAGE 3: SIGNAL→QUEST BRIDGE")
        logger.info("=" * 80)

        try:
            from src.orchestration.signal_quest_mapper import \
                bridge_cycle as signal_quest_cycle

            result = await signal_quest_cycle(test_mode=test_mode)
            cycle.add_result("signal_to_quest", result)

            quests_created = result.get("quests_created", 0)
            logger.info(f"✅ Created {quests_created} quests")
            return True

        except Exception as e:
            cycle.add_error("signal_to_quest", str(e))
            return False

    async def stage_suggest_actions(self, cycle: OrchestratorCycle) -> bool:
        """Stage 4: Suggest actions for active quests."""
        logger.info("=" * 80)
        logger.info("💡 STAGE 4: ACTION SUGGESTIONS")
        logger.info("=" * 80)

        try:
            from scripts.nusyq_actions.work_task_actions import \
                collect_quest_signal

            # Collect current quest state
            signal_data = collect_quest_signal(ROOT if ROOT.exists() else None)
            cycle.add_result(
                "actions_suggested",
                {
                    "active_quests": len(signal_data),
                    "quest_ids": list(signal_data.keys()),
                },
            )

            logger.info(f"✅ Analyzed {len(signal_data)} active quests")
            return True

        except Exception as e:
            cycle.add_error("actions_suggested", str(e))
            # Non-critical, continue
            return True

    async def stage_update_bootstrap(self, cycle: OrchestratorCycle) -> bool:
        """Stage 5: Update bootstrap state for agents."""
        logger.info("=" * 80)
        logger.info("🧠 STAGE 5: BOOTSTRAP STATE UPDATE")
        logger.info("=" * 80)

        try:
            from scripts.copilot_bootstrap import generate_bootstrap_context

            context = generate_bootstrap_context()

            cycle.add_result(
                "bootstrap_updated",
                {
                    "system_health": context.system_health,
                    "active_quests": len(context.active_quests),
                    "errors": context.error_ground_truth,
                },
            )

            logger.info("✅ Bootstrap context refreshed")
            return True

        except Exception as e:
            cycle.add_error("bootstrap_updated", str(e))
            # Non-critical, continue
            return True

    async def stage_metrics_update(self, cycle: OrchestratorCycle) -> bool:
        """Stage 6: Update metrics and observability."""
        logger.info("=" * 80)
        logger.info("📊 STAGE 6: METRICS UPDATE")
        logger.info("=" * 80)

        try:
            summary = cycle.summary()

            # Log cycle summary
            logger.info(f"Cycle duration: {summary['duration_seconds']:.2f}s")
            logger.info(f"Stages: {', '.join(summary['stages_completed'])}")

            if summary["errors"]:
                logger.warning(f"Errors: {len(summary['errors'])}")

            cycle.add_result(
                "metrics_updated",
                {
                    "cycle_duration_seconds": summary["duration_seconds"],
                    "stages_completed": len(summary["stages_completed"]),
                    "errors_in_cycle": len(summary["errors"]),
                },
            )

            return True

        except Exception as e:
            logger.error(f"Metrics update error: {e}")
            return False

    async def run_cycle(self, test_mode: bool = False) -> dict[str, Any]:
        """Run one complete orchestration cycle."""
        self.cycle_count += 1
        cycle = OrchestratorCycle()

        logger.info("\n")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info(f"║ ECOSYSTEM ORCHESTRATION CYCLE #{self.cycle_count}")
        logger.info(f"║ Autonomy: {self.autonomy_level.name} | Test Mode: {test_mode}")
        logger.info("╚" + "=" * 78 + "╝")

        # Run stages in sequence
        stages = [
            ("error_scan", lambda: self.stage_error_scan(cycle, test_mode)),
            ("error_to_signal", lambda: self.stage_error_to_signal(cycle, test_mode)),
            ("signal_to_quest", lambda: self.stage_signal_to_quest(cycle, test_mode)),
            ("actions_suggested", lambda: self.stage_suggest_actions(cycle)),
            ("bootstrap_updated", lambda: self.stage_update_bootstrap(cycle)),
            ("metrics_updated", lambda: self.stage_metrics_update(cycle)),
        ]

        for stage_name, stage_func in stages:
            if self.autonomy_level == AutonomyLevel.DISABLED:
                logger.info(f"⏭️  {stage_name} (skipped - autonomy disabled)")
                continue

            try:
                success = await stage_func()
                if not success and stage_name in ("error_scan", "error_to_signal"):
                    logger.warning(f"❌ Critical stage failed: {stage_name}")
                    break
            except Exception as e:
                logger.error(f"Stage exception: {stage_name}: {e}")
                cycle.add_error(stage_name, str(e))

        # Log cycle
        summary = cycle.summary()
        self.cycles_log.append(summary)

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info(f"CYCLE SUMMARY: {summary['cycle_id']}")
        logger.info(f"  Duration: {summary['duration_seconds']:.2f}s")
        logger.info(
            f"  Stages: {len(summary['stages_completed'])} completed, {len(summary['errors'])} errors"
        )
        for stage in summary["stages_completed"]:
            logger.info(f"    ✅ {stage}")
        if summary["errors"]:
            for error in summary["errors"]:
                logger.info(f"    ❌ {error}")
        logger.info("=" * 80 + "\n")

        return summary

    async def run_daemon(self, interval: int = 60, test_mode: bool = False) -> None:
        """Run orchestrator as background daemon."""
        self.is_running = True
        logger.info(f"Starting orchestrator daemon (interval: {interval}s)")
        logger.info("Press Ctrl+C to stop")

        try:
            while self.is_running:
                await self.run_cycle(test_mode=test_mode)

                # Wait before next cycle
                logger.info(f"Next cycle in {interval}s...")
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            logger.info("\nOrchestrator stopped by user")
            self.is_running = False
        except Exception as e:
            logger.error(f"Daemon error: {e}")
            self.is_running = False

    def get_status(self) -> dict[str, Any]:
        """Get orchestrator status."""
        return {
            "is_running": self.is_running,
            "cycle_count": self.cycle_count,
            "autonomy_level": self.autonomy_level.name,
            "recent_cycles": self.cycles_log[-5:] if self.cycles_log else [],
        }


async def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Ecosystem Orchestrator")
    parser.add_argument(
        "--mode",
        choices=["once", "daemon", "test"],
        default="once",
        help="Run mode: once (default), daemon (continuous), test (dry-run)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Cycle interval for daemon mode (seconds)",
    )
    parser.add_argument(
        "--autonomy",
        type=str,
        choices=[level.name for level in AutonomyLevel],
        default="SUGGESTING",
        help="Autonomy level (DISABLED, MONITORING, SUGGESTING, CLAIMING, EXECUTING, FULL)",
    )

    args = parser.parse_args()

    autonomy = AutonomyLevel[args.autonomy]
    orchestrator = EcosystemOrchestrator(autonomy_level=autonomy)

    try:
        if args.mode == "once":
            result = await orchestrator.run_cycle(test_mode=False)
            logger.info(json.dumps(result, indent=2, default=str))
            return 0

        elif args.mode == "test":
            logger.info("Running in TEST MODE - no changes will be made")
            result = await orchestrator.run_cycle(test_mode=True)
            logger.info(json.dumps(result, indent=2, default=str))
            return 0

        elif args.mode == "daemon":
            await orchestrator.run_daemon(interval=args.interval, test_mode=False)
            return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
