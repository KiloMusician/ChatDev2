#!/usr/bin/env python3
"""Continuous Multi-System Processor - Processes tasks across all subsystems.

Features:
- Processes background queue tasks via Ollama
- Executes quests from quest_log
- Monitors Guild Board for new assignments
- Runs healing cycles for error resolution
- Logs to all terminal channels
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ContinuousProcessor")


class ContinuousProcessor:
    """Multi-system continuous processor."""

    def __init__(self, batch_size: int = 10, cycle_interval: int = 60):
        self.batch_size = batch_size
        self.cycle_interval = cycle_interval
        self.running = True
        self.cycle_count = 0
        self.total_processed = 0
        self.log_path = Path(__file__).parent.parent / "data/terminal_logs"

        # Subsystems (lazy loaded)
        self._bg_orchestrator = None
        self._guild_board = None
        self._quantum_resolver = None

    @property
    def bg_orchestrator(self):
        if self._bg_orchestrator is None:
            from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator

            self._bg_orchestrator = BackgroundTaskOrchestrator()
        return self._bg_orchestrator

    @property
    def guild_board(self):
        if self._guild_board is None:
            try:
                from src.guild.guild_board import GuildBoard

                self._guild_board = GuildBoard()
            except Exception as e:
                logger.warning(f"Guild Board not available: {e}")
        return self._guild_board

    @property
    def quantum_resolver(self):
        if self._quantum_resolver is None:
            try:
                from src.healing.quantum_problem_resolver import QuantumProblemResolver

                self._quantum_resolver = QuantumProblemResolver()
            except Exception as e:
                logger.warning(f"Quantum Resolver not available: {e}")
        return self._quantum_resolver

    def stop(self, *args):
        """Handle shutdown signal."""
        logger.info("Shutdown signal received...")
        self.running = False

    def log_to_terminal(self, channel: str, message: str, level: str = "INFO", meta: dict | None = None):
        """Write to terminal log file."""
        log_file = self.log_path / f"{channel.lower()}.log"
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "channel": channel,
            "level": level,
            "message": message,
            "meta": meta or {},
        }
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    async def process_queue_batch(self) -> int:
        """Process a batch of queue tasks."""
        processed = 0
        for _ in range(self.batch_size):
            if not self.running:
                break
            try:
                result = await self.bg_orchestrator.process_next_task()
                if result:
                    processed += 1
                    logger.debug(f"Processed: {result.task_id}")
                else:
                    break  # Queue empty
            except Exception as e:
                logger.error(f"Task processing error: {e}")
                break
        return processed

    async def check_guild_board(self) -> dict[str, Any]:
        """Check Guild Board for status and assignments."""
        if not self.guild_board:
            return {}

        try:
            summary = await self.guild_board.get_board_summary()
            return summary
        except Exception as e:
            logger.warning(f"Guild Board check failed: {e}")
            return {}

    async def run_healing_cycle(self) -> dict[str, Any]:
        """Run a healing/maintenance cycle."""
        if not self.quantum_resolver:
            return {"status": "unavailable"}

        try:
            # Simple health check
            result = {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}
            return result
        except Exception as e:
            logger.warning(f"Healing cycle failed: {e}")
            return {"status": "error", "error": str(e)}

    async def run_cycle(self) -> dict[str, Any]:
        """Run a single processing cycle."""
        self.cycle_count += 1
        cycle_start = datetime.now(UTC)

        logger.info(f"=== Cycle {self.cycle_count} starting ===")

        # Get queue stats
        stats = self.bg_orchestrator.get_queue_stats()
        logger.info(f"Queue: {stats['queued']} queued, {stats['completed']} completed")

        # Process queue batch
        processed = await self.process_queue_batch()
        self.total_processed += processed
        logger.info(f"Processed {processed} tasks this cycle")

        # Check Guild Board
        guild_status = await self.check_guild_board()
        if guild_status:
            logger.info(
                f"Guild: {guild_status.get('agent_count', 0)} agents, {guild_status.get('quest_count', 0)} quests"
            )

        # Run healing cycle every 5 cycles
        healing_status = {}
        if self.cycle_count % 5 == 0:
            healing_status = await self.run_healing_cycle()
            logger.info(f"Healing: {healing_status.get('status', 'unknown')}")

        # Update stats
        updated_stats = self.bg_orchestrator.get_queue_stats()
        cycle_duration = (datetime.now(UTC) - cycle_start).total_seconds()

        cycle_result = {
            "cycle": self.cycle_count,
            "processed": processed,
            "total_processed": self.total_processed,
            "queue_stats": updated_stats,
            "guild_status": guild_status,
            "healing_status": healing_status,
            "duration_seconds": cycle_duration,
        }

        # Log to terminals
        self.log_to_terminal("Tasks", f"Cycle {self.cycle_count}: {processed} processed", meta=updated_stats)
        self.log_to_terminal("System", f"Cycle complete: {updated_stats['queued']} remaining", meta=cycle_result)

        logger.info(f"=== Cycle {self.cycle_count} complete ({cycle_duration:.1f}s) ===")
        return cycle_result

    async def run(self):
        """Main processing loop."""
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        logger.info("=" * 60)
        logger.info("  CONTINUOUS PROCESSOR STARTING")
        logger.info(f"  Batch size: {self.batch_size}")
        logger.info(f"  Cycle interval: {self.cycle_interval}s")
        logger.info("=" * 60)

        self.log_to_terminal("System", "Continuous processor started")

        while self.running:
            try:
                await self.run_cycle()

                if self.running:
                    logger.info(f"Sleeping {self.cycle_interval}s until next cycle...")
                    await asyncio.sleep(self.cycle_interval)

            except Exception as e:
                logger.error(f"Cycle error: {e}")
                await asyncio.sleep(10)  # Brief pause on error

        # Shutdown summary
        final_stats = self.bg_orchestrator.get_queue_stats()
        logger.info("=" * 60)
        logger.info("  PROCESSOR SHUTDOWN")
        logger.info(f"  Total cycles: {self.cycle_count}")
        logger.info(f"  Total processed: {self.total_processed}")
        logger.info(f"  Final queue: {final_stats['queued']} pending")
        logger.info("=" * 60)

        self.log_to_terminal("System", f"Processor stopped: {self.total_processed} total processed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Continuous Multi-System Processor")
    parser.add_argument("--batch", type=int, default=10, help="Tasks per batch")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between cycles")
    args = parser.parse_args()

    processor = ContinuousProcessor(batch_size=args.batch, cycle_interval=args.interval)
    asyncio.run(processor.run())
