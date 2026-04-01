#!/usr/bin/env python3
"""Background queue processor - runs continuously processing tasks."""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class QueueProcessor:
    def __init__(
        self,
        batch_size: int = 5,
        sleep_interval: int = 30,
        pid_file: Path | None = None,
        heartbeat_file: Path | None = None,
    ):
        self.batch_size = batch_size
        self.sleep_interval = sleep_interval
        self.running = True
        self.orchestrator = None
        state_dir = Path(__file__).parent.parent / "state/background_tasks"
        state_dir.mkdir(parents=True, exist_ok=True)
        self.pid_file = pid_file or (state_dir / "queue_processor.pid")
        self.heartbeat_file = heartbeat_file or (state_dir / "queue_processor_heartbeat.json")
        self._pid_acquired = False

    def stop(self, *args):
        logger.info("Shutdown signal received, stopping gracefully...")
        self.running = False

    @staticmethod
    def _is_pid_running(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _acquire_singleton(self) -> bool:
        """Ensure exactly one queue processor instance is active."""
        if self.pid_file.exists():
            raw = self.pid_file.read_text(encoding="utf-8").strip()
            existing_pid = int(raw) if raw.isdigit() else -1
            if self._is_pid_running(existing_pid):
                logger.error(
                    "Queue processor already running with PID %s (%s)",
                    existing_pid,
                    self.pid_file,
                )
                return False
            logger.warning("Removing stale pid file: %s", self.pid_file)
            self.pid_file.unlink(missing_ok=True)

        self.pid_file.write_text(str(os.getpid()), encoding="utf-8")
        self._pid_acquired = True
        return True

    def _release_singleton(self):
        if self._pid_acquired:
            self.pid_file.unlink(missing_ok=True)
            self._pid_acquired = False

    def _write_heartbeat(
        self,
        stats: dict | None = None,
        processed: int = 0,
        state: str = "running",
        note: str = "",
    ):
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "pid": os.getpid(),
            "state": state,
            "processed_last_batch": processed,
            "stats": stats or {},
            "batch_size": self.batch_size,
            "sleep_interval": self.sleep_interval,
            "note": note,
        }
        self.heartbeat_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    async def process_batch(self):
        """Process a batch of tasks."""
        processed = 0
        for _ in range(self.batch_size):
            if not self.running:
                break
            task_future = asyncio.create_task(self.orchestrator.process_next_task())
            while not task_future.done():
                done, _ = await asyncio.wait({task_future}, timeout=10)
                if done:
                    break
                stats = self.orchestrator.get_queue_stats()
                self._write_heartbeat(
                    stats=stats,
                    processed=processed,
                    state="running",
                    note="processing_task",
                )
            result = await task_future
            if result:
                processed += 1
                logger.info(f"Processed: {result.task_id} -> {result.status.name}")
            else:
                break
        return processed

    async def run(self):
        """Main processing loop."""
        if not self._acquire_singleton():
            self._write_heartbeat(state="blocked", note="Another queue_processor instance is active")
            return

        self.orchestrator = BackgroundTaskOrchestrator()
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        logger.info("Queue processor started (pid=%s)", os.getpid())

        try:
            while self.running:
                stats = self.orchestrator.get_queue_stats()
                logger.info(f"Queue: {stats['queued']} queued, {stats['completed']} completed")
                self._write_heartbeat(stats=stats, processed=0, state="running", note="loop_start")

                processed = 0
                if stats["queued"] > 0:
                    processed = await self.process_batch()
                    if processed > 0:
                        # Log to terminal
                        log_path = Path(__file__).parent.parent / "data/terminal_logs/tasks.log"
                        with open(log_path, "a", encoding="utf-8") as f:
                            f.write(
                                json.dumps(
                                    {
                                        "ts": datetime.now(UTC).isoformat(),
                                        "channel": "Tasks",
                                        "level": "INFO",
                                        "message": f"Batch processed: {processed} tasks",
                                        "meta": stats,
                                    }
                                )
                                + "\n"
                            )
                else:
                    logger.info("Queue empty, waiting...")

                self._write_heartbeat(stats=stats, processed=processed, state="running")
                await asyncio.sleep(self.sleep_interval)
        finally:
            self._write_heartbeat(
                stats=(self.orchestrator.get_queue_stats() if self.orchestrator else {}),
                state="stopped",
                note="Queue processor exited",
            )
            self._release_singleton()
            logger.info("Queue processor stopped")

    @staticmethod
    def monitor(pid_file: Path, heartbeat_file: Path) -> int:
        if not pid_file.exists():
            print(f"status=stopped pid_file={pid_file}")
            return 1

        raw = pid_file.read_text(encoding="utf-8").strip()
        pid = int(raw) if raw.isdigit() else -1
        alive = QueueProcessor._is_pid_running(pid)

        heartbeat = {}
        if heartbeat_file.exists():
            try:
                heartbeat = json.loads(heartbeat_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                heartbeat = {"error": "invalid heartbeat json"}

        heartbeat_age_seconds = None
        heartbeat_state = None
        if isinstance(heartbeat, dict):
            heartbeat_state = heartbeat.get("state")
            raw_ts = heartbeat.get("ts")
            if raw_ts:
                try:
                    hb_ts = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
                    heartbeat_age_seconds = (datetime.now(UTC) - hb_ts).total_seconds()
                except Exception:
                    heartbeat_age_seconds = None

        status = "running" if alive else "stale_pid"
        if alive and heartbeat_age_seconds is not None:
            sleep_interval = 30
            if isinstance(heartbeat, dict):
                try:
                    sleep_interval = int(heartbeat.get("sleep_interval", sleep_interval))
                except Exception:
                    sleep_interval = 30
            if heartbeat_age_seconds > max(90, sleep_interval * 4):
                status = "running_stale_heartbeat"

        print(
            json.dumps(
                {
                    "status": status,
                    "pid": pid,
                    "pid_file": str(pid_file),
                    "heartbeat_file": str(heartbeat_file),
                    "heartbeat_age_seconds": heartbeat_age_seconds,
                    "heartbeat_state": heartbeat_state,
                    "heartbeat": heartbeat,
                },
                indent=2,
            )
        )
        return 0 if status == "running" else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Managed background queue processor")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--sleep-interval", type=int, default=30)
    parser.add_argument(
        "--pid-file",
        default="state/background_tasks/queue_processor.pid",
        help="Path to singleton pid file",
    )
    parser.add_argument(
        "--heartbeat-file",
        default="state/background_tasks/queue_processor_heartbeat.json",
        help="Path to heartbeat status file",
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Print processor status/heartbeat and exit",
    )
    args = parser.parse_args()

    pid_file = Path(args.pid_file)
    heartbeat_file = Path(args.heartbeat_file)

    if args.monitor:
        raise SystemExit(QueueProcessor.monitor(pid_file=pid_file, heartbeat_file=heartbeat_file))

    processor = QueueProcessor(
        batch_size=args.batch_size,
        sleep_interval=args.sleep_interval,
        pid_file=pid_file,
        heartbeat_file=heartbeat_file,
    )
    asyncio.run(processor.run())
