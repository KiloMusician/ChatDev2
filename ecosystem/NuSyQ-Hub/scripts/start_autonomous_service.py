#!/usr/bin/env python3
"""Start autonomous monitor as a background service.
[ROUTE AGENTS] 🤖

This script:
1. Starts the autonomous monitor in continuous mode
2. Detaches the process to run in background
3. Saves PID for management
4. Logs output to file
5. Registers with guild board

Usage:
    python scripts/start_autonomous_service.py           # Start service
    python scripts/start_autonomous_service.py --stop    # Stop service
    python scripts/start_autonomous_service.py --status  # Check status
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
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


class AutonomousMonitorService:
    """Manages autonomous monitor as a background service."""

    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.state_dir = self.root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.state_dir / "autonomous_monitor.log"
        self.pid_file = self.state_dir / "autonomous_monitor.pid"
        self.script = self.root / "scripts" / "autonomous_monitor.py"

    @staticmethod
    def _parse_iso_timestamp(raw: object) -> datetime | None:
        """Parse ISO timestamp safely into timezone-aware datetime."""
        if not isinstance(raw, str) or not raw.strip():
            return None
        value = raw.strip()
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    def start(
        self,
        interval: int = 300,
        auto_cycle: str = "on-pending",
        auto_cycle_timeout: int = 240,
        max_pus: int = 2,
        cycle_sleep: int = 1,
        vantage_sweep: bool = True,
        vantage_timeout: int = 180,
        greenfield_generate_every: int = 0,
    ) -> None:
        """Start the autonomous monitor service."""
        # Check if already running
        if self.is_running():
            print("⚠️  Autonomous monitor is already running")
            pid = self._read_pid()
            print(f"   PID: {pid}")
            return

        print("🚀 Starting Autonomous Monitor Service")
        print(f"   Script: {self.script}")
        print(f"   Log file: {self.log_file}")
        print(f"   Interval: {interval}s")
        print(f"   Auto-cycle: {auto_cycle}")
        print(f"   Auto-cycle timeout: {auto_cycle_timeout}s")
        print(f"   Auto-cycle max PUs: {max_pus}")
        print(f"   Auto-cycle internal sleep: {cycle_sleep}s")
        print(f"   Vantage sweep: {'on' if vantage_sweep else 'off'}")
        print(f"   Vantage timeout: {vantage_timeout}s")
        print(f"   Greenfield generate every: {greenfield_generate_every}")

        # Build command
        cmd = [
            sys.executable,
            "-u",
            str(self.script),
            "continuous",
            "--auto-cycle",
            auto_cycle,
            "--max-pus",
            str(max(1, max_pus)),
            "--sleep",
            str(max(0, cycle_sleep)),
            "--auto-cycle-timeout",
            str(auto_cycle_timeout),
            "--vantage-timeout",
            str(vantage_timeout),
            "--greenfield-generate-every",
            str(max(0, greenfield_generate_every)),
            "--real-pus",
            "--interval",
            str(interval),
        ]
        if not vantage_sweep:
            cmd.append("--no-vantage-sweep")

        # Start detached process
        try:
            # Open log file
            log_handle = open(self.log_file, "a", encoding="utf-8")

            # Start process in background
            env = os.environ.copy()
            env.setdefault("PYTHONUNBUFFERED", "1")
            if sys.platform == "win32":
                # Windows: use CREATE_NEW_PROCESS_GROUP
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                process = subprocess.Popen(
                    cmd,
                    cwd=self.root,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    env=env,
                    creationflags=creation_flags,
                )
            else:
                # Unix: use start_new_session
                process = subprocess.Popen(
                    cmd,
                    cwd=self.root,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    env=env,
                    start_new_session=True,
                )

            # Save PID
            self.pid_file.write_text(str(process.pid), encoding="utf-8")

            # Wait a moment to ensure it started
            time.sleep(2)

            if self.is_running():
                print("✅ Autonomous monitor started successfully")
                print(f"   PID: {process.pid}")
                print(f"   View logs: tail -f {self.log_file}")

                # Register with guild board
                if GUILD_AVAILABLE:
                    try:
                        asyncio.run(
                            agent_heartbeat(
                                agent_id="autonomous",
                                status="working",
                                current_quest="continuous_monitoring",
                            )
                        )
                        asyncio.run(
                            agent_post(
                                agent_id="autonomous",
                                message=f"Autonomous monitor service started (PID: {process.pid}, interval: {interval}s)",
                                quest_id=None,
                                post_type="maintenance",
                            )
                        )
                        print("   Registered with guild board ✅")
                    except Exception as e:
                        print(f"   Warning: Failed to register with guild board: {e}")
            else:
                print("❌ Failed to start autonomous monitor")
                if self.log_file.exists():
                    print("\nRecent log output:")
                    print(self.log_file.read_text(encoding="utf-8")[-1000:])

        except Exception as e:
            print(f"❌ Error starting service: {e}")
            raise

    def stop(self) -> None:
        """Stop the autonomous monitor service."""
        if not self.is_running():
            print("⚠️  Autonomous monitor is not running")
            return

        pid = self._read_pid()
        print(f"🛑 Stopping autonomous monitor (PID: {pid})")

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
                            agent_id="autonomous",
                            status="offline",
                            current_quest=None,
                        )
                    )
                    asyncio.run(
                        agent_post(
                            agent_id="autonomous",
                            message="Autonomous monitor service stopped",
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
        print("📊 Autonomous Monitor Service Status")
        print()
        latest_trace_time: datetime | None = None

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

        # Show latest cycle proof from trace artifact.
        reports_dir = self.root / "state" / "reports"
        traces = sorted(reports_dir.glob("autonomous_monitor_trace_*.json"))
        if traces:
            latest = traces[-1]
            print()
            print(f"   Latest trace: {latest.name}")
            latest_trace_time = datetime.fromtimestamp(latest.stat().st_mtime, tz=UTC)
            try:
                trace = json.loads(latest.read_text(encoding="utf-8"))
                trace_generated_at = self._parse_iso_timestamp(trace.get("generated_at"))
                if trace_generated_at is not None:
                    latest_trace_time = trace_generated_at
                steps = trace.get("steps", [])
                step_payload = {s.get("step"): s.get("payload", {}) for s in steps}

                pu_check = step_payload.get("pu_queue_check", {})
                auto_cycle = step_payload.get("auto_cycle", {})
                vantage_system = step_payload.get("vantage_system_doctor", {})
                vantage_existing = step_payload.get("vantage_existing_project_fix_dry_run", {})
                vantage_greenfield = step_payload.get("vantage_greenfield_health", {})

                if pu_check:
                    print(
                        "   Queue check: "
                        f"pending={pu_check.get('pending')} total={pu_check.get('total')} "
                        f"seeded={pu_check.get('seeded_from_gaps', 0)} "
                        f"auto_cycle_ran={pu_check.get('auto_cycle_ran')}"
                    )
                if auto_cycle:
                    print(
                        "   Auto-cycle: "
                        f"return_code={auto_cycle.get('return_code')} "
                        f"cmd={' '.join(auto_cycle.get('command', []))}"
                    )
                if vantage_system or vantage_existing or vantage_greenfield:
                    print(
                        "   Vantage RCs: "
                        f"system={vantage_system.get('return_code')} "
                        f"existing={vantage_existing.get('return_code')} "
                        f"greenfield={vantage_greenfield.get('return_code')}"
                    )
            except Exception as exc:
                print(f"   Warning: Could not parse latest trace: {exc}")

        # Show current queue distribution.
        queue_path = self.root / "data" / "unified_pu_queue.json"
        if queue_path.exists():
            try:
                queue_data = json.loads(queue_path.read_text(encoding="utf-8"))
                status_counts: dict[str, int] = {}
                for item in queue_data:
                    status = str(item.get("status", "unknown"))
                    status_counts[status] = status_counts.get(status, 0) + 1

                print()
                print(f"   PU queue totals: {len(queue_data)}")
                for status, count in sorted(status_counts.items(), key=lambda kv: (-kv[1], kv[0])):
                    print(f"      {status}: {count}")
            except Exception as exc:
                print(f"   Warning: Could not read PU queue stats: {exc}")

        # Show aggregate execution counters.
        metrics_path = self.root / "data" / "execution_metrics.json"
        if metrics_path.exists():
            try:
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                print()
                print("   Execution metrics:")
                print(f"      total_cycles: {metrics.get('total_cycles')}")
                print(f"      total_tasks_processed: {metrics.get('total_tasks_processed')}")
                print(f"      successful_executions: {metrics.get('successful_executions')}")
                print(f"      failed_executions: {metrics.get('failed_executions')}")
                print(f"      skipped_executions: {metrics.get('skipped_executions')}")
                metrics_updated_raw = metrics.get("updated_at")
                print(f"      updated_at: {metrics_updated_raw}")
                metrics_updated_at = self._parse_iso_timestamp(metrics_updated_raw)
                if metrics_updated_at and latest_trace_time:
                    staleness_seconds = int((latest_trace_time - metrics_updated_at).total_seconds())
                    if staleness_seconds > 600:
                        staleness_minutes = staleness_seconds // 60
                        print(
                            "      ⚠ stale: "
                            f"{staleness_minutes}m behind latest trace "
                            "(queue + trace output are fresher)"
                        )
            except Exception as exc:
                print(f"   Warning: Could not read execution metrics: {exc}")

    def is_running(self) -> bool:
        """Check if service is running."""
        if not self.pid_file.exists():
            return False

        pid = self._read_pid()
        if pid is None:
            return False

        if PSUTIL_AVAILABLE:
            if not psutil.pid_exists(pid):
                return False
            try:
                proc = psutil.Process(pid)
                cmdline = " ".join(proc.cmdline()).lower()
                script_hint = str(self.script).lower()
                return bool(cmdline) and script_hint in cmdline
            except Exception:
                return False

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
    parser = argparse.ArgumentParser(description="Manage autonomous monitor background service")

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
        default=300,
        help="Monitoring interval in seconds (default: 300)",
    )
    parser.add_argument(
        "--auto-cycle",
        choices=["always", "on-pending", "off"],
        default="on-pending",
        help="Auto-cycle mode (default: on-pending)",
    )
    parser.add_argument(
        "--auto-cycle-timeout",
        type=int,
        default=240,
        help="Timeout (seconds) for each auto_cycle subprocess (default: 240)",
    )
    parser.add_argument(
        "--max-pus",
        type=int,
        default=2,
        help="Max PUs per auto-cycle run (default: 2)",
    )
    parser.add_argument(
        "--cycle-sleep",
        type=int,
        default=1,
        help="Sleep seconds inside each auto-cycle run (default: 1)",
    )
    parser.add_argument(
        "--vantage-sweep",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable three-vantage sweep each cycle (default: enabled)",
    )
    parser.add_argument(
        "--vantage-timeout",
        type=int,
        default=180,
        help="Timeout (seconds) for each vantage sweep command (default: 180)",
    )
    parser.add_argument(
        "--greenfield-generate-every",
        type=int,
        default=0,
        help="If >0, run greenfield smoke generation every N monitor cycles",
    )

    args = parser.parse_args()

    service = AutonomousMonitorService()

    if args.stop:
        service.stop()
    elif args.status:
        service.status()
    elif args.restart:
        service.stop()
        time.sleep(2)
        service.start(
            interval=args.interval,
            auto_cycle=args.auto_cycle,
            auto_cycle_timeout=args.auto_cycle_timeout,
            max_pus=max(1, args.max_pus),
            cycle_sleep=max(0, args.cycle_sleep),
            vantage_sweep=args.vantage_sweep,
            vantage_timeout=args.vantage_timeout,
            greenfield_generate_every=max(0, args.greenfield_generate_every),
        )
    else:
        # Default: start
        service.start(
            interval=args.interval,
            auto_cycle=args.auto_cycle,
            auto_cycle_timeout=args.auto_cycle_timeout,
            max_pus=max(1, args.max_pus),
            cycle_sleep=max(0, args.cycle_sleep),
            vantage_sweep=args.vantage_sweep,
            vantage_timeout=args.vantage_timeout,
            greenfield_generate_every=max(0, args.greenfield_generate_every),
        )


if __name__ == "__main__":
    main()
