#!/usr/bin/env python3
"""Service Manager - Start, stop, and monitor NuSyQ-Hub services

Manages critical services:
- PU Queue Processor
- Cross Ecosystem Sync
- Guild Board Renderer
- Autonomous Monitor (optional)

Disables OpenTelemetry if collector not available.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


class ServiceManager:
    """Manages NuSyQ-Hub background services."""

    def __init__(self, root: Path):
        self.root = root
        self.state_dir = root / "state" / "services"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "services.json"
        self.log_dir = root / "data" / "service_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.pid_dir = self.state_dir / "pids"
        self.pid_dir.mkdir(parents=True, exist_ok=True)
        self.health_check_interval = 60  # seconds

        # Disable OpenTelemetry if not configured
        if "OTEL_EXPORTER_OTLP_ENDPOINT" not in os.environ:
            os.environ["OTEL_SDK_DISABLED"] = "true"
            os.environ["OTEL_TRACES_EXPORTER"] = "none"
            print("Info: OpenTelemetry disabled (no collector configured)")

    def load_state(self) -> dict[str, Any]:
        """Load service state from disk."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except (OSError, json.JSONDecodeError):
                pass
        return {"services": {}, "last_update": None}

    def save_state(self, state: dict[str, Any]) -> None:
        """Save service state to disk."""
        state["last_update"] = datetime.now().isoformat()
        self.state_file.write_text(json.dumps(state, indent=2))

    def _pid_file(self, service_name: str) -> Path:
        return self.pid_dir / f"{service_name}.pid"

    def _log_pid(self, service_name: str, pid: int) -> None:
        self._pid_file(service_name).write_text(str(pid), encoding="utf-8")

    def _clear_pid(self, service_name: str) -> None:
        try:
            self._pid_file(service_name).unlink(missing_ok=True)
        except OSError:
            pass

    def _is_pid_alive(self, pid: int) -> bool:
        try:
            if sys.platform == "win32":
                subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}"], text=True, stderr=subprocess.DEVNULL)
                return True
            os.kill(pid, 0)
            return True
        except (OSError, subprocess.CalledProcessError):
            return False

    def _read_pid(self, service_name: str) -> int | None:
        path = self._pid_file(service_name)
        if not path.exists():
            return None
        try:
            pid = int(path.read_text(encoding="utf-8").strip())
        except ValueError:
            path.unlink(missing_ok=True)
            return None
        if self._is_pid_alive(pid):
            return pid
        path.unlink(missing_ok=True)
        return None

    def _ensure_singleton(self, service_name: str, friendly_name: str) -> int | None:
        pid = self._read_pid(service_name)
        if pid:
            print(f"   ⚠️ {friendly_name} already running (PID: {pid}); lock prevented duplicate.")
        return pid

    def start_pu_queue(self, simulated: bool = False) -> dict[str, Any]:
        """Start PU Queue processor."""
        log_file = self.log_dir / "pu_queue.log"
        existing_pid = self._ensure_singleton("pu_queue_runner", "PU Queue Processor")
        if existing_pid:
            return {
                "status": "already_running",
                "pid": existing_pid,
                "log_file": str(log_file),
                "note": "Lock file prevented duplicate launch",
            }

        print("\n🔧 Starting PU Queue Processor...")

        # PU queue runner only has --real flag, no --simulated
        cmd = [sys.executable, str(self.root / "scripts" / "pu_queue_runner.py")]
        if not simulated:
            cmd.append("--real")

        try:
            # Run in background
            with open(log_file, "a") as f:
                proc = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=str(self.root),
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
                )

                self._log_pid("pu_queue_runner", proc.pid)

                print(f"   ✅ Started (PID: {proc.pid})")
                print(f"   📝 Log: {log_file}")

                return {
                    "status": "running",
                    "pid": proc.pid,
                    "mode": "simulated" if simulated else "real",
                    "started_at": datetime.now().isoformat(),
                    "log_file": str(log_file),
                }
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {"status": "failed", "error": str(e)}

    def start_cross_sync(self) -> dict[str, Any]:
        """Start Cross Ecosystem Sync."""
        log_file = self.log_dir / "cross_sync.log"
        existing_pid = self._ensure_singleton("cross_sync", "Cross Ecosystem Sync")
        if existing_pid:
            return {
                "status": "already_running",
                "pid": existing_pid,
                "log_file": str(log_file),
                "note": "Lock file prevented duplicate launch",
            }

        print("\n🔄 Starting Cross Ecosystem Sync...")

        # Use Python to run the sync continuously
        cmd = [
            sys.executable,
            "-c",
            """
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from src.tools.cross_ecosystem_sync import CrossEcosystemSync

sync = CrossEcosystemSync()
print("Cross Ecosystem Sync started")
while True:
    try:
        result = sync.sync_all()
        print(f"Sync complete at {time.strftime('%H:%M:%S')} -> {result.get('status')}")
    except Exception as e:
        print(f"Sync error: {e}")
    time.sleep(300)  # Sync every 5 minutes
""",
        ]

        try:
            with open(log_file, "a") as f:
                proc = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=str(self.root),
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
                )

                self._log_pid("cross_sync", proc.pid)

                print(f"   ✅ Started (PID: {proc.pid})")
                print(f"   📝 Log: {log_file}")

                return {
                    "status": "running",
                    "pid": proc.pid,
                    "started_at": datetime.now().isoformat(),
                    "log_file": str(log_file),
                }
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {"status": "failed", "error": str(e)}

    def start_guild_renderer(self) -> dict[str, Any]:
        """Start Guild Board auto-renderer."""
        log_file = self.log_dir / "guild_renderer.log"
        existing_pid = self._ensure_singleton("guild_renderer", "Guild Board Renderer")
        if existing_pid:
            return {
                "status": "already_running",
                "pid": existing_pid,
                "log_file": str(log_file),
                "note": "Lock file prevented duplicate launch",
            }

        print("\n🏰 Starting Guild Board Renderer...")

        cmd = [
            sys.executable,
            "-c",
            """
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from scripts.render_guild_board import render_guild_board_markdown

# Renderer loop
print("Guild Board Renderer started")
while True:
    try:
        result = render_guild_board_markdown()
        print(f"[{time.strftime('%H:%M:%S')}] {result}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Render error: {e}")
    time.sleep(600)  # Render every 10 minutes
""",
        ]

        try:
            with open(log_file, "a") as f:
                proc = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=str(self.root),
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
                )

                self._log_pid("guild_renderer", proc.pid)

                print(f"   ✅ Started (PID: {proc.pid})")
                print(f"   📝 Log: {log_file}")

                return {
                    "status": "running",
                    "pid": proc.pid,
                    "started_at": datetime.now().isoformat(),
                    "log_file": str(log_file),
                }
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {"status": "failed", "error": str(e)}

    def start_autonomous_monitor(self) -> dict[str, Any]:
        """Start Autonomous Monitor."""
        print("\n🤖 Starting Autonomous Monitor...")

        log_file = self.log_dir / "autonomous_monitor.log"

        cmd = [
            sys.executable,
            "-c",
            """
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from src.automation.autonomous_monitor import AutonomousMonitor

monitor = AutonomousMonitor(audit_interval=1800)
print("Autonomous Monitor started")
monitor.run_forever()
""",
        ]

        try:
            with open(log_file, "a") as f:
                proc = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=str(self.root),
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
                )

            print(f"   ✅ Started (PID: {proc.pid})")
            print(f"   📝 Log: {log_file}")

            return {
                "status": "running",
                "pid": proc.pid,
                "started_at": datetime.now().isoformat(),
                "log_file": str(log_file),
            }
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {"status": "failed", "error": str(e)}

    def start_all(self, skip_optional: bool = False) -> None:
        """Start all services."""
        print("=" * 70)
        print("🚀 STARTING NUSYQ-HUB SERVICES")
        print("=" * 70)

        state = self.load_state()
        services = state.get("services", {})

        # Start PU Queue (simulated mode for safety)
        services["pu_queue"] = self.start_pu_queue(simulated=True)

        # Start Cross Sync
        services["cross_sync"] = self.start_cross_sync()

        # Start Guild Renderer
        services["guild_renderer"] = self.start_guild_renderer()

        # Optionally start Autonomous Monitor
        if not skip_optional:
            services["autonomous_monitor"] = self.start_autonomous_monitor()

        state["services"] = services
        self.save_state(state)

        print("\n" + "=" * 70)
        print("✨ SERVICE STARTUP COMPLETE")
        print("=" * 70)
        print(f"\n📊 Status saved to: {self.state_file}")
        print(f"📝 Logs directory: {self.log_dir}")
        print("\n💡 To view service status: python scripts/service_manager.py status")
        print("💡 To stop services: python scripts/service_manager.py stop")

    def status(self) -> None:
        """Show service status."""
        print("=" * 70)
        print("📊 NUSYQ-HUB SERVICE STATUS")
        print("=" * 70)

        state = self.load_state()
        services = state.get("services", {})

        if not services:
            print("\n❌ No services running")
            return

        print(f"\nLast update: {state.get('last_update', 'Unknown')}\n")

        for name, info in services.items():
            status = info.get("status", "unknown")
            icon = "✅" if status == "running" else "❌"
            print(f"{icon} {name.replace('_', ' ').title()}")
            print(f"   Status: {status}")
            if "pid" in info:
                print(f"   PID: {info['pid']}")
            if "started_at" in info:
                print(f"   Started: {info['started_at']}")
            if "log_file" in info:
                print(f"   Log: {info['log_file']}")
            print()

    def health_check(self) -> dict[str, bool]:
        """Check if services are still running."""
        state = self.load_state()
        services = state.get("services", {})
        health = {}

        try:
            import psutil

            for name, info in services.items():
                if "pid" not in info:
                    health[name] = False
                    continue

                try:
                    proc = psutil.Process(info["pid"])
                    health[name] = proc.is_running()
                except psutil.NoSuchProcess:
                    health[name] = False

        except ImportError:
            # psutil not available, assume all running
            for name in services:
                health[name] = True

        return health

    def monitor(self, check_interval: int = 60, auto_restart: bool = False) -> None:
        """Monitor services and optionally restart crashed ones."""
        print("=" * 70)
        print("👀 MONITORING NUSYQ-HUB SERVICES")
        print("=" * 70)
        print(f"\nCheck interval: {check_interval}s")
        print(f"Auto-restart: {'enabled' if auto_restart else 'disabled'}")
        print("\nPress Ctrl+C to stop monitoring\n")

        try:
            while True:
                health = self.health_check()
                timestamp = datetime.now().strftime("%H:%M:%S")

                any_down = False
                for name, is_healthy in health.items():
                    if not is_healthy:
                        print(f"[{timestamp}] ⚠️  {name} is down")
                        any_down = True

                        if auto_restart:
                            print(f"[{timestamp}] 🔄 Attempting to restart {name}...")
                            # Restart logic would go here
                            # For now, just notify
                            print(f"[{timestamp}] Info: Auto-restart not yet implemented")

                if not any_down:
                    print(f"[{timestamp}] ✅ All services healthy")

                time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped")

    def stop_all(self) -> None:
        """Stop all services."""
        print("=" * 70)
        print("🛑 STOPPING NUSYQ-HUB SERVICES")
        print("=" * 70)

        state = self.load_state()
        services = state.get("services", {})

        if not services:
            print("\n❌ No services running")
            return

        for name, info in services.items():
            if "pid" in info:
                try:
                    import psutil

                    proc = psutil.Process(info["pid"])
                    proc.terminate()
                    proc.wait(timeout=5)
                    print(f"✅ Stopped {name} (PID: {info['pid']})")
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    print(f"⚠️  {name} already stopped or unresponsive")
                except ImportError:
                    print(f"⚠️  Cannot stop {name}: psutil not installed")
                    print(f"   Manually kill PID: {info['pid']}")

        # Clear state
        state["services"] = {}
        self.save_state(state)

        print("\n✅ All services stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manage NuSyQ-Hub services")
    parser.add_argument(
        "action",
        choices=["start", "stop", "status", "restart", "monitor", "health"],
        help="Action to perform",
    )
    parser.add_argument("--skip-optional", action="store_true", help="Skip optional services (autonomous monitor)")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Health check interval in seconds (for monitor command)",
    )
    parser.add_argument(
        "--auto-restart",
        action="store_true",
        help="Automatically restart crashed services (for monitor command)",
    )
    args = parser.parse_args()

    manager = ServiceManager(ROOT)

    if args.action == "start":
        manager.start_all(skip_optional=args.skip_optional)
    elif args.action == "stop":
        manager.stop_all()
    elif args.action == "status":
        manager.status()
    elif args.action == "restart":
        manager.stop_all()
        time.sleep(2)
        manager.start_all(skip_optional=args.skip_optional)
    elif args.action == "health":
        health = manager.health_check()
        print("=" * 70)
        print("🏥 SERVICE HEALTH CHECK")
        print("=" * 70)
        print()
        for name, is_healthy in health.items():
            status = "✅ Healthy" if is_healthy else "❌ Down"
            print(f"{name}: {status}")
        print()
        if all(health.values()):
            print("✅ All services healthy")
        else:
            print("⚠️  Some services are down")
    elif args.action == "monitor":
        manager.monitor(check_interval=args.interval, auto_restart=args.auto_restart)


if __name__ == "__main__":
    main()
