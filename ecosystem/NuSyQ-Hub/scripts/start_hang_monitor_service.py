#!/usr/bin/env python3
"""Start Copilot hang monitor as a background service.
[ROUTE METRICS] 📊

This script:
1. Starts the hang monitor in daemon mode
2. Detaches the process to run in background
3. Saves PID for management
4. Logs output to file
5. Registers with guild board

Usage:
    python scripts/start_hang_monitor_service.py           # Start service
    python scripts/start_hang_monitor_service.py --stop    # Stop service
    python scripts/start_hang_monitor_service.py --status  # Check status
"""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Ensure we can import from src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from src.guild.agent_guild_protocols import agent_heartbeat, agent_post

    GUILD_AVAILABLE = True
except ImportError:
    GUILD_AVAILABLE = False

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class HangMonitorService:
    """Manages Copilot hang monitor as a background service."""

    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.state_dir = self.root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.state_dir / "copilot_hang_monitor.log"
        self.pid_file = self.state_dir / "copilot_hang_monitor.pid"
        self.script = self.root / "scripts" / "copilot_hang_monitor.py"

    def start(
        self,
        interval: int = 60,
        timeout: int = 15,
        dry_run: bool = False,
    ) -> None:
        """Start the hang monitor service."""
        # Check if already running
        if self.is_running():
            print("⚠️  Hang monitor is already running")
            pid = self._read_pid()
            print(f"   PID: {pid}")
            return

        print("🚀 Starting Copilot Hang Monitor Service")
        print(f"   Script: {self.script}")
        print(f"   Log file: {self.log_file}")
        print(f"   Interval: {interval}s")
        print(f"   Timeout: {timeout} minutes")
        print(f"   Dry run: {dry_run}")

        # Build command
        cmd = [
            sys.executable,
            str(self.script),
            "--daemon",
            "--interval",
            str(interval),
            "--timeout",
            str(timeout),
        ]

        if dry_run:
            cmd.append("--dry-run")

        # Start detached process
        try:
            # Open log file
            log_handle = open(self.log_file, "a", encoding="utf-8")

            # Start process in background
            if sys.platform == "win32":
                # Windows: use CREATE_NEW_PROCESS_GROUP
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                process = subprocess.Popen(
                    cmd,
                    cwd=self.root,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    creationflags=creation_flags,
                )
            else:
                # Unix: use start_new_session
                process = subprocess.Popen(
                    cmd,
                    cwd=self.root,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )

            # Save PID
            self.pid_file.write_text(str(process.pid), encoding="utf-8")

            # Wait a moment to ensure it started
            time.sleep(2)

            if self.is_running():
                print("✅ Hang monitor started successfully")
                print(f"   PID: {process.pid}")
                print(f"   View logs: tail -f {self.log_file}")

                # Register with guild board
                if GUILD_AVAILABLE:
                    try:
                        asyncio.run(
                            agent_heartbeat(
                                agent_id="hang_monitor",
                                status="working",
                                current_quest="copilot_monitoring",
                            )
                        )
                        asyncio.run(
                            agent_post(
                                agent_id="hang_monitor",
                                message=f"Hang monitor service started (PID: {process.pid}, interval: {interval}s, timeout: {timeout}m)",
                                quest_id=None,
                                post_type="maintenance",
                            )
                        )
                        print("   Registered with guild board ✅")
                    except Exception as e:
                        print(f"   Warning: Failed to register with guild board: {e}")
            else:
                print("❌ Failed to start hang monitor")
                if self.log_file.exists():
                    print("\nRecent log output:")
                    print(self.log_file.read_text(encoding="utf-8")[-1000:])

        except Exception as e:
            print(f"❌ Error starting service: {e}")
            raise

    def stop(self) -> None:
        """Stop the hang monitor service."""
        if not self.is_running():
            print("⚠️  Hang monitor is not running")
            return

        pid = self._read_pid()
        print(f"🛑 Stopping hang monitor (PID: {pid})")

        try:
            if PSUTIL_AVAILABLE:
                # Use psutil for graceful shutdown
                proc = psutil.Process(pid)
                proc.terminate()

                # Wait up to 10 seconds for graceful shutdown
                try:
                    proc.wait(timeout=10)
                    print("   Stopped gracefully ✅")
                except psutil.TimeoutExpired:
                    print("   Graceful shutdown timed out, forcing...")
                    proc.kill()
                    print("   Killed forcefully ✅")
            else:
                # Fallback to os.kill
                if sys.platform == "win32":
                    os.kill(pid, signal.SIGTERM)
                else:
                    os.kill(pid, signal.SIGTERM)

                # Wait and verify
                time.sleep(2)
                if self.is_running():
                    os.kill(pid, signal.SIGKILL)
                    print("   Killed forcefully ✅")
                else:
                    print("   Stopped gracefully ✅")

            # Remove PID file
            if self.pid_file.exists():
                self.pid_file.unlink()

            # Update guild board
            if GUILD_AVAILABLE:
                try:
                    asyncio.run(
                        agent_heartbeat(
                            agent_id="hang_monitor",
                            status="offline",
                            current_quest=None,
                        )
                    )
                    asyncio.run(
                        agent_post(
                            agent_id="hang_monitor",
                            message="Hang monitor service stopped",
                            quest_id=None,
                            post_type="maintenance",
                        )
                    )
                except Exception:
                    pass

        except ProcessLookupError:
            print("   Process already terminated")
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception as e:
            print(f"❌ Error stopping service: {e}")
            raise

    def status(self) -> None:
        """Check service status."""
        print("📊 Copilot Hang Monitor Service Status")
        print()

        if not self.is_running():
            print("   Status: ❌ Not running")
            if self.pid_file.exists():
                print(f"   Stale PID file found: {self.pid_file}")
            return

        pid = self._read_pid()
        print("   Status: ✅ Running")
        print(f"   PID: {pid}")

        if PSUTIL_AVAILABLE:
            try:
                proc = psutil.Process(pid)
                create_time = time.ctime(proc.create_time())
                cpu_percent = proc.cpu_percent(interval=1)
                memory_mb = proc.memory_info().rss / 1024 / 1024

                print(f"   Started: {create_time}")
                print(f"   CPU: {cpu_percent:.1f}%")
                print(f"   Memory: {memory_mb:.1f} MB")
            except Exception as e:
                print(f"   Warning: Could not get process details: {e}")

        # Show recent log lines
        if self.log_file.exists():
            print()
            print("   Recent log output (last 10 lines):")
            lines = self.log_file.read_text(encoding="utf-8").strip().split("\n")
            for line in lines[-10:]:
                print(f"      {line}")

    def is_running(self) -> bool:
        """Check if service is running."""
        if not self.pid_file.exists():
            return False

        pid = self._read_pid()
        if pid is None:
            return False

        if PSUTIL_AVAILABLE:
            return psutil.pid_exists(pid)
        else:
            # Fallback: try to send signal 0
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                return False

    def _read_pid(self) -> int | None:
        """Read PID from file."""
        if not self.pid_file.exists():
            return None

        try:
            return int(self.pid_file.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            return None


def main() -> None:
    """Entry point for service management."""
    parser = argparse.ArgumentParser(description="Manage Copilot hang monitor background service")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--stop",
        action="store_true",
        help="Stop the service",
    )
    group.add_argument(
        "--status",
        action="store_true",
        help="Check service status",
    )
    group.add_argument(
        "--restart",
        action="store_true",
        help="Restart the service",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Process timeout in minutes (default: 15)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (report only, don't kill)",
    )

    args = parser.parse_args()

    service = HangMonitorService()

    if args.stop:
        service.stop()
    elif args.status:
        service.status()
    elif args.restart:
        service.stop()
        time.sleep(2)
        service.start(interval=args.interval, timeout=args.timeout, dry_run=args.dry_run)
    else:
        # Default: start
        service.start(interval=args.interval, timeout=args.timeout, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
