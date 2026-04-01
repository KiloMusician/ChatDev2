#!/usr/bin/env python3
"""Hang Detection and Diagnostics Tool

Monitors ruff/quality tool processes and detects when they're stuck.

Shows:
- Which file is currently being processed
- How long it's been processing
- When timeout should be triggered
- Recommendations for handling stuck processes
"""

import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

PROJECT_ROOT = Path(__file__).parent.parent


class HangDetector:
    """Detects and diagnoses hanging processes."""

    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds
        self.process_start_time: datetime | None = None
        self.current_file: str | None = None
        self.stuck_files: list[str] = []

    def _log(self, message: str) -> None:
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def _get_ruff_processes(self) -> list[psutil.Process]:
        """Get all running ruff processes."""
        try:
            processes = []
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if "ruff" in proc.name() or (proc.cmdline() and "ruff" in " ".join(proc.cmdline())):
                        processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return processes
        except Exception as e:
            self._log(f"⚠️  Error getting processes: {e}")
            return []

    def _extract_file_from_cmdline(self, cmdline: list[str]) -> str | None:
        """Extract file being processed from ruff command line."""
        for _i, arg in enumerate(cmdline):
            if arg.endswith(".py") and Path(arg).exists():
                return arg
        return None

    def monitor(self) -> None:
        """Monitor ruff processes for hangs."""
        self._log("🔍 Ruff Hang Monitor Started")
        self._log(f"⏱️  Timeout threshold: {self.timeout_seconds}s")
        self._log("")

        process_tracking: dict[int, dict] = {}  # pid -> {file, start_time}

        try:
            while True:
                processes = self._get_ruff_processes()

                if not processes:
                    self._log("ℹ️  No ruff processes found")
                    time.sleep(5)
                    continue

                # Check each process
                for proc in processes:
                    try:
                        pid = proc.pid
                        cmdline = proc.cmdline() or []

                        # First time seeing this process
                        if pid not in process_tracking:
                            file_path = self._extract_file_from_cmdline(cmdline)
                            process_tracking[pid] = {
                                "file": file_path or "unknown",
                                "start_time": datetime.now(),
                                "warned": False,
                            }
                            self._log(f"▶️  Process {pid} started: {cmdline[-1] if cmdline else 'unknown'}")

                        # Check for timeout
                        tracking = process_tracking[pid]
                        elapsed = datetime.now() - tracking["start_time"]

                        if elapsed.total_seconds() > self.timeout_seconds:
                            if not tracking["warned"]:
                                self._log(
                                    f"⚠️  HANG DETECTED (PID {pid}):\n"
                                    f"     File: {tracking['file']}\n"
                                    f"     Elapsed: {int(elapsed.total_seconds())}s "
                                    f"(threshold: {self.timeout_seconds}s)\n"
                                    f"     → Consider killing process and updating checkpoint"
                                )
                                tracking["warned"] = True
                                self.stuck_files.append(tracking["file"])
                        else:
                            # Still running normally
                            status = f"Processing: {tracking['file']} ({int(elapsed.total_seconds())}s)"
                            if not tracking["warned"]:
                                self._log(status)

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process ended
                        if pid in process_tracking:
                            elapsed = datetime.now() - process_tracking[pid]["start_time"]
                            self._log(f"✅ Process {pid} completed in {int(elapsed.total_seconds())}s")
                            del process_tracking[pid]

                # Clean up dead processes from tracking
                dead_pids = [pid for pid in process_tracking if not any(p.pid == pid for p in processes)]
                for pid in dead_pids:
                    del process_tracking[pid]

                time.sleep(5)

        except KeyboardInterrupt:
            self._log("\n⏸️  Monitoring stopped")
            self._print_summary()

    def _print_summary(self) -> None:
        """Print summary of detected hangs."""
        if not self.stuck_files:
            self._log("✅ No hangs detected")
            return

        self._log("\n" + "=" * 70)
        self._log("🔴 STUCK FILES DETECTED")
        self._log("=" * 70)

        for file_path in self.stuck_files:
            self._log(f"  - {file_path}")

        self._log("\n💡 RECOMMENDATIONS:")
        self._log("  1. Kill the hanging process (Ctrl+C)")
        self._log("  2. Add these files to skip list in batch checkpoint")
        self._log("  3. Or increase timeout and batch size to 1 (process separately)")
        self._log("\n  To clean checkpoint and restart:")
        self._log("     rm state/quality_*_checkpoint.json")
        self._log("     python scripts/quality_orchestrator.py")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Ruff hang detector")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout threshold in seconds (default: 60)")

    args = parser.parse_args()

    detector = HangDetector(timeout_seconds=args.timeout)
    detector.monitor()


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("❌ psutil not installed. Install with:")
        print("     pip install psutil")
        sys.exit(1)
