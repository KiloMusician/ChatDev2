#!/usr/bin/env python3
"""Start All Critical Services - Unified startup for NuSyQ-Hub ecosystem

This script starts all critical services in the correct order with health monitoring:

1. MCP Server (Model Context Protocol) - AI integration
2. Multi-AI Orchestrator - Core coordination
3. PU Queue Processor - Task execution
4. Guild Board Renderer - Quest tracking
5. Cross Ecosystem Sync - Quest log sync
6. Autonomous Monitor - Repository watching

All services run in background with auto-restart on failure.
"""

import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Setup path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Disable OpenTelemetry if not configured
if "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT" not in os.environ:
    base = "http://127.0.0.1:4318"
    os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{base}/v1/traces"
    os.environ.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_TRACES_PROTOCOL", "http/protobuf")


class CriticalServiceManager:
    """Manages critical NuSyQ services with health monitoring and auto-restart."""

    def __init__(self):
        self.root = ROOT
        self.state_dir = ROOT / "state" / "services"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "critical_services.json"
        self.log_dir = ROOT / "data" / "service_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.services = {}
        self.monitoring = False

    @staticmethod
    def _port_in_use(host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.25)
            try:
                return s.connect_ex((host, port)) == 0
            except OSError:
                return False

    def start_mcp_server(self) -> dict:
        """Start MCP Server in background thread."""
        print("\n🔌 Starting MCP Server...")

        try:
            import threading

            from src.integration.mcp_server import MCPServer, ServiceConfig

            # Resolve host/port and avoid clashes
            cfg_host, cfg_port = ServiceConfig.get_mcp_server_address()
            host = os.environ.get("MCP_SERVER_HOST", cfg_host)
            port = int(os.environ.get("MCP_SERVER_PORT", cfg_port))
            if self._port_in_use(host, port):
                url = f"http://{host}:{port}"
                print(f"   ⚠️  Port {port} already in use; assuming MCP is running at {url}")
                return {
                    "status": "running",
                    "type": "external",
                    "host": host,
                    "port": port,
                    "url": url,
                    "started_at": datetime.now().isoformat(),
                    "reason": "port_in_use",
                }

            # Create server instance
            server = MCPServer(host=host, port=port)

            # Start in background thread
            def run_server():
                print(f"   🌐 MCP Server starting on {server.host}:{server.port}")
                server.run(debug=False)

            server_thread = threading.Thread(target=run_server, daemon=True, name="MCP-Server")
            server_thread.start()

            # Wait for server to be ready
            time.sleep(1.0)

            # Health check
            import requests

            health_url = f"http://{server.host}:{server.port}/health"
            try:
                response = requests.get(health_url, timeout=3)
                if response.status_code != 200:
                    raise RuntimeError(f"Health check failed: {response.status_code}")
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"MCP Server not responding: {e}") from e

            print(f"   ✅ MCP Server running at http://{server.host}:{server.port}")
            print(
                "   🛠️  Available tools: 6 (analyze_repository, get_context, orchestrate_task, generate_code, generate_tests, check_system_health)"
            )

            return {
                "status": "running",
                "type": "thread",
                "thread_id": server_thread.ident,
                "thread": server_thread,
                "url": f"http://{server.host}:{server.port}",
                "started_at": datetime.now().isoformat(),
                "health_check": health_url,
            }
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {"status": "failed", "error": str(e)}

    def start_multi_ai_orchestrator(self) -> dict:
        """Start Multi-AI Orchestrator."""
        print("\n🎯 Starting Multi-AI Orchestrator...")

        log_file = self.log_dir / "orchestrator.log"
        cmd = [sys.executable, str(self.root / "scripts" / "start_multi_ai_orchestrator.py")]

        try:
            with open(log_file, "a") as f:
                proc = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=str(self.root),
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
                )

            time.sleep(0.5)  # Give it time to start

            print(f"   ✅ Started (PID: {proc.pid})")
            print(f"   📝 Log: {log_file}")

            return {
                "status": "running",
                "type": "process",
                "pid": proc.pid,
                "process": proc,
                "started_at": datetime.now().isoformat(),
                "log_file": str(log_file),
            }
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {"status": "failed", "error": str(e)}

    def start_pu_queue(self) -> dict:
        """Start PU Queue Processor."""
        print("\n⚙️  Starting PU Queue Processor...")

        log_file = self.log_dir / "pu_queue.log"
        cmd = [
            sys.executable,
            "-c",
            """
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from scripts.pu_queue_runner import main

print("PU Queue Processor started (continuous mode)")

# Run continuously with 5-minute intervals
while True:
    try:
        main()  # Process queue
        print(f"Queue processed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(300)  # Wait 5 minutes between runs
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error in queue processing: {e}")
        time.sleep(60)  # Wait 1 minute on error
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
                "type": "process",
                "pid": proc.pid,
                "process": proc,
                "mode": "real",
                "started_at": datetime.now().isoformat(),
                "log_file": str(log_file),
            }
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {"status": "failed", "error": str(e)}

    def start_guild_renderer(self) -> dict:
        """Start Guild Board Renderer."""
        print("\n⚔️  Starting Guild Board Renderer...")

        log_file = self.log_dir / "guild_renderer.log"
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
    render_guild_board_markdown()
    time.sleep(60)  # Re-render every 60 seconds
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
                "type": "process",
                "pid": proc.pid,
                "process": proc,
                "started_at": datetime.now().isoformat(),
                "log_file": str(log_file),
            }
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {"status": "failed", "error": str(e)}

    def start_cross_sync(self) -> dict:
        """Start Cross Ecosystem Sync."""
        print("\n🔄 Starting Cross Ecosystem Sync...")

        log_file = self.log_dir / "cross_sync.log"
        cmd = [
            sys.executable,
            "-c",
            """
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

print("Cross Ecosystem Sync started")

# Simplified sync using file copying instead of async
while True:
    try:
        import shutil
        from datetime import datetime

        repo_root = Path.cwd()
        hub_quest_log = repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"

        # Find SimulatedVerse
        simverse_root = None
        for possible_path in [
            repo_root.parent / "SimulatedVerse" / "SimulatedVerse",
            Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse",
            Path("/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"),
        ]:
            if possible_path.exists():
                simverse_root = possible_path
                break

        if simverse_root and hub_quest_log.exists():
            sv_shared = simverse_root / "shared_cultivation"
            sv_shared.mkdir(parents=True, exist_ok=True)
            sv_quest_log = sv_shared / "quest_log.jsonl"

            shutil.copy2(hub_quest_log, sv_quest_log)
            print(f"✅ Synced quest log at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("⚠️  SimulatedVerse not found or quest log missing")

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

            print(f"   ✅ Started (PID: {proc.pid})")
            print(f"   📝 Log: {log_file}")

            return {
                "status": "running",
                "type": "process",
                "pid": proc.pid,
                "process": proc,
                "started_at": datetime.now().isoformat(),
                "log_file": str(log_file),
            }
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {"status": "failed", "error": str(e)}

    def start_autonomous_monitor(self) -> dict:
        """Start Autonomous Monitor."""
        print("\n🤖 Starting Autonomous Monitor...")

        log_file = self.log_dir / "autonomous_monitor.log"
        cmd = [
            sys.executable,
            "-c",
            """
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from src.automation.autonomous_monitor import AutonomousMonitor

monitor = AutonomousMonitor(audit_interval=1800)
print("Autonomous Monitor started")

# Run audit loop using correct method name
import time
while True:
    try:
        monitor.run_single_audit()
        print(f"Audit completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(1800)  # Wait 30 minutes between audits
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error in audit: {e}")
        time.sleep(60)  # Wait 1 minute on error
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
                "type": "process",
                "pid": proc.pid,
                "process": proc,
                "started_at": datetime.now().isoformat(),
                "log_file": str(log_file),
            }
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {"status": "failed", "error": str(e)}

    def save_state(self):
        """Save current service state to disk."""
        state = {
            "services": {},
            "last_update": datetime.now().isoformat(),
        }

        for name, info in self.services.items():
            # Don't serialize process/thread objects
            serializable = {k: v for k, v in info.items() if k not in ["process", "thread"]}
            state["services"][name] = serializable

        self.state_file.write_text(json.dumps(state, indent=2))

    def health_check(self) -> dict[str, bool]:
        """Check if services are still alive."""
        health = {}

        try:
            import psutil
        except ImportError:
            # If psutil not available, assume all running
            return dict.fromkeys(self.services, True)

        for name, info in self.services.items():
            if info.get("status") != "running":
                health[name] = False
                continue

            service_type = info.get("type")

            if service_type == "process":
                # Check process PID
                pid = info.get("pid")
                if pid:
                    try:
                        proc = psutil.Process(pid)
                        health[name] = proc.is_running()
                    except psutil.NoSuchProcess:
                        health[name] = False
                else:
                    health[name] = False

            elif service_type == "external":
                url = info.get("url")
                host = info.get("host", "localhost")
                port = info.get("port")
                ok = False
                if url:
                    try:
                        import urllib.request

                        req = urllib.request.Request(str(url).rstrip("/") + "/health")
                        with urllib.request.urlopen(req, timeout=3) as resp:
                            ok = resp.status < 500
                    except Exception:
                        ok = False
                elif port:
                    try:
                        import socket as _s

                        with _s.socket(_s.AF_INET, _s.SOCK_STREAM) as s:
                            s.settimeout(0.5)
                            ok = s.connect_ex((host, int(port))) == 0
                    except Exception:
                        ok = False
                health[name] = ok

            elif service_type == "thread":
                # Check thread
                thread = info.get("thread")
                health[name] = thread is not None and thread.is_alive()

            else:
                health[name] = False

        return health

    def restart_service(self, name: str):
        """Restart a specific service."""
        print(f"\n🔄 Restarting {name}...")

        # Map service names to start methods
        start_methods = {
            "mcp_server": self.start_mcp_server,
            "orchestrator": self.start_multi_ai_orchestrator,
            "pu_queue": self.start_pu_queue,
            "guild_renderer": self.start_guild_renderer,
            "cross_sync": self.start_cross_sync,
            "autonomous_monitor": self.start_autonomous_monitor,
        }

        if name in start_methods:
            self.services[name] = start_methods[name]()
            self.save_state()
        else:
            print(f"   ⚠️  Unknown service: {name}")

    def monitor_and_restart(self, check_interval: int = 60):
        """Continuously monitor and auto-restart crashed services."""
        print("\n" + "=" * 70)
        print("👀 MONITORING SERVICES (Auto-restart enabled)")
        print("=" * 70)
        print(f"\nCheck interval: {check_interval}s")
        print("Press Ctrl+C to stop monitoring\n")

        self.monitoring = True

        try:
            while self.monitoring:
                health = self.health_check()
                timestamp = datetime.now().strftime("%H:%M:%S")

                for name, is_healthy in health.items():
                    if not is_healthy:
                        print(f"[{timestamp}] ⚠️  {name} is DOWN - restarting...")
                        self.restart_service(name)
                    else:
                        print(f"[{timestamp}] ✅ {name} is healthy")

                time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped")
            self.monitoring = False

    def start_all(self, with_monitoring: bool = True):
        """Start all critical services."""
        print("=" * 70)
        print("🚀 STARTING ALL CRITICAL SERVICES")
        print("=" * 70)

        # Start services in dependency order
        self.services["mcp_server"] = self.start_mcp_server()
        time.sleep(0.5)

        self.services["orchestrator"] = self.start_multi_ai_orchestrator()
        time.sleep(0.5)

        self.services["pu_queue"] = self.start_pu_queue()
        time.sleep(0.5)

        self.services["guild_renderer"] = self.start_guild_renderer()
        time.sleep(0.5)

        self.services["cross_sync"] = self.start_cross_sync()
        time.sleep(0.5)

        self.services["autonomous_monitor"] = self.start_autonomous_monitor()

        # Save state
        self.save_state()

        print("\n" + "=" * 70)
        print("✨ ALL CRITICAL SERVICES STARTED")
        print("=" * 70)
        print(f"\n📊 State saved to: {self.state_file}")
        print(f"📝 Logs directory: {self.log_dir}")

        # Show status
        health = self.health_check()
        running_count = sum(1 for h in health.values() if h)
        print(f"\n🎯 Status: {running_count}/{len(health)} services running")

        for name, is_healthy in health.items():
            icon = "✅" if is_healthy else "❌"
            print(f"   {icon} {name}")

        # Start monitoring if requested
        if with_monitoring:
            self.monitor_and_restart(check_interval=60)
        else:
            print("\n💡 Run with --monitor to enable auto-restart")

    def status(self):
        """Show current service status."""
        print("=" * 70)
        print("📊 CRITICAL SERVICES STATUS")
        print("=" * 70)

        if not self.services:
            # Try to load from state file
            if self.state_file.exists():
                state = json.loads(self.state_file.read_text())
                self.services = state.get("services", {})

        if not self.services:
            print("\n❌ No services found")
            print("💡 Run 'python scripts/start_all_critical_services.py start' to launch services")
            return

        health = self.health_check()

        print(f"\nLast update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        for name, info in self.services.items():
            is_healthy = health.get(name, False)
            icon = "✅" if is_healthy else "❌"
            status = "RUNNING" if is_healthy else "DOWN"

            print(f"{icon} {name.replace('_', ' ').title()} - {status}")
            print(f"   Type: {info.get('type', 'unknown')}")

            if "pid" in info:
                print(f"   PID: {info['pid']}")
            if "url" in info:
                print(f"   URL: {info['url']}")
            if "started_at" in info:
                print(f"   Started: {info['started_at']}")
            if "log_file" in info:
                print(f"   Log: {info['log_file']}")
            print()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage critical NuSyQ services")
    parser.add_argument(
        "action",
        choices=["start", "status", "monitor"],
        help="Action to perform",
    )
    parser.add_argument(
        "--no-monitor",
        action="store_true",
        help="Start services without monitoring loop",
    )

    args = parser.parse_args()

    manager = CriticalServiceManager()

    if args.action == "start":
        manager.start_all(with_monitoring=not args.no_monitor)
    elif args.action == "status":
        manager.status()
    elif args.action == "monitor":
        # Load existing services and start monitoring
        if manager.state_file.exists():
            state = json.loads(manager.state_file.read_text())
            manager.services = state.get("services", {})
        manager.monitor_and_restart(check_interval=60)


if __name__ == "__main__":
    main()
