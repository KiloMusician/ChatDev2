#!/usr/bin/env python3
"""Copilot Hang Monitor - Detects and kills hanging Copilot/subprocess processes.
[ROUTE METRICS] 📊

This monitor:
1. Detects processes that have been running too long
2. Kills hanging processes gracefully (SIGTERM) or forcefully (SIGKILL)
3. Reports to guild board for coordination
4. Logs all actions for debugging

Usage:
    python scripts/copilot_hang_monitor.py --check         # Check once, report only
    python scripts/copilot_hang_monitor.py --kill-now      # Kill hanging processes now
    python scripts/copilot_hang_monitor.py --daemon        # Run continuously
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Ensure we can import from src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import psutil
except ImportError:
    print("❌ ERROR: psutil not installed")
    print("   Install with: pip install psutil")
    sys.exit(1)

# Try to import guild protocols for reporting
try:
    from src.guild.agent_guild_protocols import agent_heartbeat, agent_post

    GUILD_AVAILABLE = True
except ImportError:
    GUILD_AVAILABLE = False


@dataclass
class HangingProcess:
    """Information about a potentially hanging process."""

    pid: int
    name: str
    cmdline: str
    runtime_seconds: float
    create_time: datetime
    cpu_percent: float
    memory_mb: float


class CopilotHangMonitor:
    """Monitors and kills hanging Copilot and related processes."""

    # Patterns to detect suspicious processes
    SUSPICIOUS_PATTERNS = [
        "copilot",
        "github-copilot",
        "node.*copilot",
        "pytest.*--",
        "ruff.*check",
        "mypy.*--",
        "python.*test",
    ]

    # Timeout thresholds (in minutes)
    DEFAULT_TIMEOUT_MINUTES = 10
    PYTEST_TIMEOUT_MINUTES = 15
    RUFF_TIMEOUT_MINUTES = 5
    MYPY_TIMEOUT_MINUTES = 10

    def __init__(
        self,
        timeout_minutes: int = DEFAULT_TIMEOUT_MINUTES,
        dry_run: bool = False,
        report_to_guild: bool = True,
    ):
        self.timeout = timedelta(minutes=timeout_minutes)
        self.dry_run = dry_run
        self.report_to_guild = report_to_guild and GUILD_AVAILABLE
        self.logger = logging.getLogger(__name__)
        self.root = Path(__file__).resolve().parents[1]

    def _get_timeout_for_process(self, cmdline: str) -> timedelta:
        """Get appropriate timeout based on process type."""
        cmdline_lower = cmdline.lower()

        if "pytest" in cmdline_lower:
            return timedelta(minutes=self.PYTEST_TIMEOUT_MINUTES)
        elif "ruff" in cmdline_lower:
            return timedelta(minutes=self.RUFF_TIMEOUT_MINUTES)
        elif "mypy" in cmdline_lower:
            return timedelta(minutes=self.MYPY_TIMEOUT_MINUTES)
        else:
            return self.timeout

    def _is_suspicious_process(self, cmdline: str) -> bool:
        """Check if process matches suspicious patterns."""
        cmdline_lower = cmdline.lower()
        return any(
            pattern.replace(".*", " ") in cmdline_lower or pattern.split(".*")[0] in cmdline_lower
            for pattern in self.SUSPICIOUS_PATTERNS
        )

    def find_hanging_processes(self) -> list[HangingProcess]:
        """Find processes that have been running too long."""
        hanging = []

        for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time", "cpu_percent", "memory_info"]):
            try:
                if not proc.info["cmdline"]:
                    continue

                cmd_str = " ".join(proc.info["cmdline"])

                # Check if it's a suspicious process
                if not self._is_suspicious_process(cmd_str):
                    continue

                # Check runtime
                create_time = datetime.fromtimestamp(proc.info["create_time"])
                runtime = datetime.now() - create_time
                timeout = self._get_timeout_for_process(cmd_str)

                if runtime > timeout:
                    # Get resource usage
                    cpu_percent = proc.info.get("cpu_percent", 0) or 0
                    memory_info = proc.info.get("memory_info")
                    memory_mb = memory_info.rss / 1024 / 1024 if memory_info else 0

                    hanging.append(
                        HangingProcess(
                            pid=proc.info["pid"],
                            name=proc.info["name"],
                            cmdline=cmd_str[:200],  # Truncate long commands
                            runtime_seconds=runtime.total_seconds(),
                            create_time=create_time,
                            cpu_percent=cpu_percent,
                            memory_mb=memory_mb,
                        )
                    )

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return hanging

    def kill_process(self, proc: HangingProcess) -> dict[str, Any]:
        """Kill a single hanging process."""
        result = {
            "pid": proc.pid,
            "name": proc.name,
            "success": False,
            "method": None,
            "error": None,
        }

        if self.dry_run:
            result["success"] = True
            result["method"] = "dry_run"
            return result

        try:
            # Try graceful termination first
            os.kill(proc.pid, signal.SIGTERM)
            time.sleep(2)

            # Check if still alive
            if psutil.pid_exists(proc.pid):
                try:
                    # Still alive, force kill
                    os.kill(proc.pid, signal.SIGKILL)
                    result["method"] = "SIGKILL"
                    result["success"] = True
                except ProcessLookupError:
                    result["method"] = "already_dead"
                    result["success"] = True
            else:
                result["method"] = "SIGTERM"
                result["success"] = True

        except ProcessLookupError:
            result["method"] = "already_dead"
            result["success"] = True
        except PermissionError as e:
            result["error"] = f"Permission denied: {e}"
        except Exception as e:
            result["error"] = str(e)

        return result

    def kill_hanging_processes(self) -> list[dict[str, Any]]:
        """Find and kill all hanging processes."""
        hanging = self.find_hanging_processes()

        if not hanging:
            self.logger.info("✅ No hanging processes found")
            return []

        self.logger.info(f"🔍 Found {len(hanging)} hanging processes")

        results = []
        for proc in hanging:
            runtime_str = str(timedelta(seconds=int(proc.runtime_seconds)))

            self.logger.info(
                f"   PID {proc.pid}: {proc.name} (runtime: {runtime_str}, "
                f"CPU: {proc.cpu_percent:.1f}%, MEM: {proc.memory_mb:.1f}MB)"
            )
            self.logger.info(f"      Cmd: {proc.cmdline}")

            kill_result = self.kill_process(proc)
            results.append(
                {
                    "process": proc,
                    "kill_result": kill_result,
                }
            )

            if kill_result["success"]:
                method = kill_result["method"]
                if method == "dry_run":
                    self.logger.info("      🔍 DRY RUN - would kill")
                else:
                    self.logger.info(f"      ✅ Killed ({method})")
            else:
                error = kill_result.get("error", "Unknown error")
                self.logger.error(f"      ❌ Failed to kill: {error}")

        # Report to guild board if available
        if self.report_to_guild and results:
            self._report_to_guild(results)

        return results

    def _report_to_guild(self, results: list[dict[str, Any]]) -> None:
        """Report hanging process actions to guild board."""
        try:
            killed_count = sum(1 for r in results if r["kill_result"]["success"])
            failed_count = len(results) - killed_count

            # Post summary to guild
            message = f"Hang monitor: Killed {killed_count}/{len(results)} hanging processes"
            if failed_count > 0:
                message += f" ({failed_count} failed)"

            agent_post(
                agent_id="hang_monitor",
                message=message,
                quest_id=None,
                post_type="maintenance",
            )

            # If we killed Copilot specifically, update its heartbeat
            copilot_killed = any("copilot" in r["process"].name.lower() for r in results if r["kill_result"]["success"])

            if copilot_killed:
                agent_heartbeat(
                    agent_id="copilot",
                    status="offline",
                    current_quest=None,
                )

        except Exception as e:
            self.logger.warning(f"Failed to report to guild: {e}")

    def run_monitoring_loop(self, interval_seconds: int = 60) -> None:
        """Run continuous monitoring loop."""
        self.logger.info("🚀 Starting Copilot hang monitor")
        self.logger.info(f"   Timeout threshold: {self.timeout}")
        self.logger.info(f"   Check interval: {interval_seconds}s")
        self.logger.info(f"   Dry run: {self.dry_run}")
        self.logger.info(f"   Guild reporting: {self.report_to_guild}")
        self.logger.info("")

        cycle_count = 0

        while True:
            try:
                cycle_count += 1
                self.logger.info(f"📊 Monitor cycle {cycle_count} - {datetime.now().isoformat()}")

                results = self.kill_hanging_processes()

                if results:
                    killed = sum(1 for r in results if r["kill_result"]["success"])
                    self.logger.info(f"🔄 Killed {killed}/{len(results)} processes, continuing...")
                else:
                    self.logger.info("✅ All clear")

                self.logger.info(f"⏸️  Sleeping for {interval_seconds}s...\n")
                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                self.logger.info("\n🛑 Stopping monitor (KeyboardInterrupt)")
                break
            except Exception as exc:
                self.logger.error(f"❌ Monitor error: {exc}")
                time.sleep(interval_seconds)


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Monitor and kill hanging Copilot/subprocess processes")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        help="Check for hanging processes and report (no kill)",
    )
    group.add_argument(
        "--kill-now",
        action="store_true",
        help="Kill hanging processes immediately and exit",
    )
    group.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously as daemon",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=CopilotHangMonitor.DEFAULT_TIMEOUT_MINUTES,
        help=f"Timeout in minutes (default: {CopilotHangMonitor.DEFAULT_TIMEOUT_MINUTES})",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds for daemon mode (default: 60)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be killed without actually killing",
    )
    parser.add_argument(
        "--no-guild",
        action="store_true",
        help="Don't report to guild board",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    return parser.parse_args()


def main() -> None:
    """Entry point for hang monitor."""
    args = _parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    # Create monitor
    monitor = CopilotHangMonitor(
        timeout_minutes=args.timeout,
        dry_run=args.dry_run,
        report_to_guild=not args.no_guild,
    )

    # Run appropriate mode
    if args.check:
        # Check only mode
        hanging = monitor.find_hanging_processes()
        if hanging:
            print(f"⚠️  Found {len(hanging)} hanging processes:")
            for proc in hanging:
                runtime_str = str(timedelta(seconds=int(proc.runtime_seconds)))
                print(f"   • PID {proc.pid}: {proc.name} (runtime: {runtime_str})")
                print(f"     {proc.cmdline[:100]}...")
        else:
            print("✅ No hanging processes found")

    elif args.kill_now:
        # Kill once and exit
        results = monitor.kill_hanging_processes()
        if results:
            killed = sum(1 for r in results if r["kill_result"]["success"])
            print(f"✅ Killed {killed}/{len(results)} hanging processes")
        else:
            print("✅ No hanging processes to kill")

    elif args.daemon:
        # Continuous monitoring
        monitor.run_monitoring_loop(interval_seconds=args.interval)

    else:
        # Default: check and report
        print("No mode specified. Use --check, --kill-now, or --daemon")
        print("Run with --help for usage information")


if __name__ == "__main__":
    main()
