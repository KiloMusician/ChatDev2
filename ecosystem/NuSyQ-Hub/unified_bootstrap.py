#!/usr/bin/env python3
"""unified_bootstrap.py — Modernized Unified Bootstrap for NuSyQ Ecosystem

This script provides a single entry point to bootstrap and manage all three repositories:
- NuSyQ-Hub (Python orchestration)
- SimulatedVerse (Node.js HTTP server)
- NuSyQ (PowerShell orchestrator + MCP server)

Features:
- Dynamic path detection and configuration
- Service health checks and status reporting
- Graceful startup with dependency management
- Cross-platform compatibility (Windows/Linux/Mac)
- Error recovery and rollback
- Logging and monitoring integration

Usage:
    python unified_bootstrap.py [command]

Commands:
    start       Start all services
    stop        Stop all services
    status      Show service status
    health      Run health checks
    restart     Restart all services
    bootstrap   Full bootstrap (setup + start)
"""

import argparse
import logging
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Terminal integration (best-effort)
try:
    from src.system.enhanced_terminal_ecosystem import TerminalManager
except Exception:
    TerminalManager = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("bootstrap.log", mode="a")],
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for a service."""

    name: str
    repo_name: str
    path: Path | None = None
    port: int | None = None
    startup_command: list[str] | None = None
    health_check_url: str | None = None
    process_name: str | None = None
    status: str = "unknown"
    pid: int | None = None


@dataclass
class EcosystemConfig:
    """Configuration for the entire ecosystem."""

    hub: ServiceConfig
    simulatedverse: ServiceConfig
    nusyq: ServiceConfig
    base_paths: dict[str, Path] = field(default_factory=dict)


class UnifiedBootstrap:
    """Unified bootstrap manager for the NuSyQ ecosystem."""

    def __init__(self):
        self.config = self._load_config()
        self.system = platform.system().lower()
        # Terminal manager (optional) + terminal logging
        try:
            self.tm = TerminalManager.get_instance() if TerminalManager else None
        except Exception:
            self.tm = None
        # Initialize terminal logging adapter so standard logs forward into channels
        try:
            from src.system.init_terminal import init_terminal_logging

            init_terminal_logging(channel="Main")
        except Exception:
            pass

    def _load_config(self) -> EcosystemConfig:
        """Load ecosystem configuration with dynamic path detection."""
        # Detect base paths
        base_paths = self._detect_base_paths()

        # Configure services
        hub_config = ServiceConfig(
            name="NuSyQ-Hub",
            repo_name="NuSyQ-Hub",
            path=base_paths.get("hub"),
            startup_command=["python", "scripts/start_nusyq.py", "activate_ecosystem"],
            health_check_url=None,  # No web server, just infrastructure activation
            process_name="python" if base_paths.get("hub") else None,
        )

        simverse_config = ServiceConfig(
            name="SimulatedVerse",
            repo_name="SimulatedVerse",
            path=base_paths.get("simulatedverse"),
            port=5000,
            startup_command=["npm", "run", "dev"],
            health_check_url="http://localhost:5000/healthz",
            process_name="node" if base_paths.get("simulatedverse") else None,
        )

        nusyq_config = ServiceConfig(
            name="NuSyQ",
            repo_name="NuSyQ",
            path=base_paths.get("nusyq"),
            port=3000,
            startup_command=["python", "mcp_server/main.py"],
            health_check_url="http://localhost:3000/health" if base_paths.get("nusyq") else None,
            process_name="python" if base_paths.get("nusyq") else None,
        )

        return EcosystemConfig(
            hub=hub_config,
            simulatedverse=simverse_config,
            nusyq=nusyq_config,
            base_paths=base_paths,
        )

    def _detect_base_paths(self) -> dict[str, Path]:
        """Dynamically detect repository paths."""
        paths = {}

        # Start from current directory and search upwards/adjacent
        current = Path.cwd()

        # Check if we're in one of the repos
        if (current / "scripts" / "start_nusyq.py").exists():
            paths["hub"] = current
        elif (current / "package.json").exists() and "SimulatedVerse" in str(current):
            paths["simulatedverse"] = current
        elif (current / "NuSyQ.Orchestrator.ps1").exists():
            paths["nusyq"] = current

        # Search adjacent directories
        parent = current.parent
        for subdir in parent.iterdir():
            if subdir.is_dir():
                if "NuSyQ-Hub" in subdir.name and (subdir / "scripts" / "start_nusyq.py").exists():
                    paths["hub"] = subdir
                elif "SimulatedVerse" in subdir.name and (subdir / "package.json").exists():
                    paths["simulatedverse"] = subdir
                elif subdir.name == "NuSyQ" and (subdir / "NuSyQ.Orchestrator.ps1").exists():
                    paths["nusyq"] = subdir

        # Check known locations
        known_locations = {
            "hub": [
                Path.home() / "Desktop" / "Legacy" / "NuSyQ-Hub",
                Path.home() / "Desktop" / "NuSyQ-Hub",
            ],
            "simulatedverse": [
                Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse",
                Path.home() / "Desktop" / "SimulatedVerse",
            ],
            "nusyq": [
                Path.home() / "NuSyQ",
                Path.home() / "Desktop" / "NuSyQ",
            ],
        }

        for repo_name, locations in known_locations.items():
            if repo_name not in paths:
                for location in locations:
                    if location.exists():
                        # Verify it's the right repo
                        if (
                            repo_name == "hub"
                            and (location / "scripts" / "start_nusyq.py").exists()
                        ):
                            paths[repo_name] = location
                            break
                        elif repo_name == "simulatedverse" and (location / "package.json").exists():
                            paths[repo_name] = location
                            break
                        elif (
                            repo_name == "nusyq" and (location / "NuSyQ.Orchestrator.ps1").exists()
                        ):
                            paths[repo_name] = location
                            break

        # Check environment variables as fallback
        env_vars = {
            "hub": "NUSYQ_HUB_PATH",
            "simulatedverse": "SIMULATEDVERSE_PATH",
            "nusyq": "NUSYQ_ROOT_PATH",
        }

        for repo_name, env_var in env_vars.items():
            if repo_name not in paths:
                env_path = os.environ.get(env_var)
                if env_path and Path(env_path).exists():
                    paths[repo_name] = Path(env_path)

        return paths

    def check_service_health(self, service: ServiceConfig) -> tuple[bool, str]:
        """Check if a service is healthy."""
        if not service.health_check_url:
            return False, "No health check URL configured"

        # For SimulatedVerse, use a simpler check since it can be slow
        if service.name == "SimulatedVerse":
            return self._basic_health_check(service)

        try:
            import requests

            response = requests.get(service.health_check_url, timeout=10)
            if response.status_code == 200:
                return True, "Healthy"
            else:
                return False, f"HTTP {response.status_code}"
        except ImportError:
            # Fallback to basic connectivity check
            return self._basic_health_check(service)
        except Exception as e:
            return False, str(e)

    def _basic_health_check(self, service: ServiceConfig) -> tuple[bool, str]:
        """Basic health check without requests library."""
        if not service.port:
            return False, "No port configured"

        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(("localhost", service.port))
            sock.close()
            return result == 0, "Port open" if result == 0 else "Port closed"
        except Exception as e:
            return False, str(e)

    def start_service(self, service: ServiceConfig) -> bool:
        """Start a service."""
        if not service.path or not service.startup_command:
            logger.error(f"Cannot start {service.name}: missing path or command")
            return False

        try:
            logger.info(f"Starting {service.name}...")
            os.chdir(service.path)

            if self.system == "windows":
                # Use subprocess with shell=True for Windows
                process = subprocess.Popen(
                    service.startup_command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            else:
                process = subprocess.Popen(
                    service.startup_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

            service.pid = process.pid
            service.status = "starting"

            # Wait a bit for startup
            time.sleep(5)

            # Check if process is still running
            if process.poll() is None:
                service.status = "running"
                logger.info(f"{service.name} started successfully (PID: {service.pid})")
                if getattr(self, "tm", None):
                    self.tm.send(
                        service.name,
                        "info",
                        "started",
                        meta={"pid": service.pid, "path": str(service.path)},
                    )
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"{service.name} failed to start: {stderr.decode()}")
                if getattr(self, "tm", None):
                    self.tm.send(
                        "Errors",
                        "error",
                        f"{service.name} failed to start",
                        meta={"stderr": stderr.decode()},
                    )
                return False

        except Exception as e:
            logger.error(f"Error starting {service.name}: {e}")
            return False

    def stop_service(self, service: ServiceConfig) -> bool:
        """Stop a service."""
        if not service.pid:
            logger.warning(f"No PID for {service.name}, cannot stop")
            return False

        try:
            if self.system == "windows":
                subprocess.run(["taskkill", "/PID", str(service.pid), "/F"], check=True)
            else:
                os.kill(service.pid, 15)  # SIGTERM
                time.sleep(2)
                if self._process_exists(service.pid):
                    os.kill(service.pid, 9)  # SIGKILL

            service.status = "stopped"
            service.pid = None
            logger.info(f"{service.name} stopped")
            if getattr(self, "tm", None):
                self.tm.send(service.name, "info", "stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping {service.name}: {e}")
            return False

    def _process_exists(self, pid: int) -> bool:
        """Check if process exists."""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _find_process_by_name(self, name: str) -> bool:
        """Check if a process with the given name is running."""
        try:
            import psutil

            for proc in psutil.process_iter(["pid", "name"]):
                if name.lower() in proc.info["name"].lower():
                    return True
            return False
        except ImportError:
            # Fallback: use tasklist on Windows
            if self.system == "windows":
                try:
                    result = subprocess.run(
                        ["tasklist", "/FI", f"IMAGENAME eq {name}.exe"],
                        capture_output=True,
                        text=True,
                    )
                    return name.lower() in result.stdout.lower()
                except Exception:
                    pass
            return False

    def get_service_status(self, service: ServiceConfig) -> str:
        """Get detailed status of a service."""
        if not service.path:
            return "not_configured"

        # First check if we have a PID and it's still running
        if service.pid and self._process_exists(service.pid):
            # If it has a port, check health
            if service.port:
                healthy, _ = self.check_service_health(service)
                return "healthy" if healthy else "running_unhealthy"
            return "running"

        # If no PID but has a port, check if port is open (service might be running independently)
        if service.port:
            healthy, _ = self._basic_health_check(service)
            if healthy:
                return "running"

        # Check if process name is running (for services that might restart themselves)
        if service.process_name and self._find_process_by_name(service.process_name):
            return "running"

        return "stopped"

    def bootstrap_ecosystem(self) -> bool:
        """Full bootstrap: setup dependencies and start services."""
        logger.info("Starting full ecosystem bootstrap...")
        if getattr(self, "tm", None):
            self.tm.send("Tasks", "info", "bootstrap_started")

        # Setup dependencies
        if not self._setup_dependencies():
            if getattr(self, "tm", None):
                self.tm.send("Errors", "error", "dependency_setup_failed")
            return False

        # Start services in dependency order
        services = [self.config.simulatedverse, self.config.nusyq, self.config.hub]

        for service in services:
            if service.path:
                if not self.start_service(service):
                    logger.error(f"Bootstrap failed at {service.name}")
                    if getattr(self, "tm", None):
                        self.tm.send("Errors", "error", f"bootstrap_failed_at_{service.name}")
                    return False
            else:
                logger.warning(f"Skipping {service.name}: path not found")
                if getattr(self, "tm", None):
                    self.tm.send("Suggestions", "warning", f"skip_{service.name}_missing_path")

        # Final health check
        ok = self.run_health_checks()
        if getattr(self, "tm", None):
            self.tm.send(
                "Tasks",
                "info",
                "bootstrap_completed" if ok else "bootstrap_completed_with_errors",
                meta={"ok": ok},
            )
        return ok

    def _setup_dependencies(self) -> bool:
        """Setup dependencies for all services."""
        logger.info("Setting up dependencies...")

        # NuSyQ-Hub: Python venv
        if self.config.hub.path:
            venv_path = self.config.hub.path / ".venv"
            if not venv_path.exists():
                logger.info("Setting up Python virtual environment...")
                try:
                    os.chdir(self.config.hub.path)
                    subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
                    # Install requirements
                    pip = (
                        str(venv_path / "Scripts" / "pip")
                        if self.system == "windows"
                        else str(venv_path / "bin" / "pip")
                    )
                    subprocess.run([pip, "install", "-r", "requirements.txt"], check=True)
                except Exception as e:
                    logger.error(f"Failed to setup Python venv: {e}")
                    if getattr(self, "tm", None):
                        self.tm.send(
                            "Errors", "error", "Failed to setup Python venv", meta={"error": str(e)}
                        )
                    return False

        # SimulatedVerse: npm install
        if self.config.simulatedverse.path:
            package_json = self.config.simulatedverse.path / "package.json"
            node_modules = self.config.simulatedverse.path / "node_modules"
            if package_json.exists() and not node_modules.exists():
                logger.info("Installing Node.js dependencies...")
                try:
                    os.chdir(self.config.simulatedverse.path)
                    subprocess.run(["npm", "install"], check=True)
                except Exception as e:
                    logger.error(f"Failed to install npm dependencies: {e}")
                    if getattr(self, "tm", None):
                        self.tm.send(
                            "Errors",
                            "error",
                            "Failed to install npm dependencies",
                            meta={"error": str(e)},
                        )
                    return False

        # NuSyQ: PowerShell modules
        if self.config.nusyq.path and self.system == "windows":
            logger.info("Ensuring PowerShell modules...")
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "Install-Module PowerShell-Yaml -Scope CurrentUser -Force -AllowClobber",
                    ],
                    check=True,
                )
            except Exception as e:
                logger.warning(f"PowerShell module setup failed: {e}")
                if getattr(self, "tm", None):
                    self.tm.send(
                        "Warnings",
                        "warning",
                        "PowerShell module setup failed",
                        meta={"error": str(e)},
                    )

        return True

    def run_health_checks(self) -> bool:
        """Run health checks on all services."""
        logger.info("Running health checks...")

        all_healthy = True
        for service in [self.config.hub, self.config.simulatedverse, self.config.nusyq]:
            if service.path:
                status = self.get_service_status(service)
                service.status = status

                healthy, health_msg = self.check_service_health(service)

                # For services without health checks, consider them healthy if they're running
                if not service.health_check_url:
                    if status in ["running", "healthy"]:
                        healthy = True
                        health_msg = "Running (no health check)"
                    else:
                        healthy = False
                        health_msg = "Not running"

                if healthy:
                    logger.info(f"✅ {service.name}: {status} - {health_msg}")
                    if getattr(self, "tm", None):
                        self.tm.send(
                            "Metrics",
                            "info",
                            f"health {service.name}",
                            meta={"status": status, "detail": health_msg},
                        )
                else:
                    logger.warning(f"⚠️  {service.name}: {status} - {health_msg}")
                    if getattr(self, "tm", None):
                        self.tm.send(
                            "Errors",
                            "warning",
                            f"health {service.name}",
                            meta={"status": status, "detail": health_msg},
                        )
                    all_healthy = False
            else:
                logger.error(f"❌ {service.name}: path not configured")
                if getattr(self, "tm", None):
                    self.tm.send("Errors", "error", f"{service.name}: path not configured")
                all_healthy = False

        return all_healthy

    def show_status(self):
        """Show status of all services."""
        print("\n🔍 NuSyQ Ecosystem Status")
        print("=" * 50)

        for service in [self.config.hub, self.config.simulatedverse, self.config.nusyq]:
            status = self.get_service_status(service)
            path_str = str(service.path) if service.path else "Not found"
            port_str = f" (port {service.port})" if service.port else ""

            status_icon = {
                "healthy": "✅",
                "running": "🟢",
                "running_unhealthy": "🟡",
                "stopped": "🔴",
                "not_configured": "❓",
            }.get(status, "❓")

            print(f"{status_icon} {service.name}: {status}")
            print(f"   Path: {path_str}{port_str}")
            if service.pid:
                print(f"   PID: {service.pid}")
            print()

    def start_all(self) -> bool:
        """Start all services."""
        logger.info("Starting all services...")
        success = True

        for service in [self.config.simulatedverse, self.config.nusyq, self.config.hub]:
            if service.path and self.get_service_status(service) == "stopped":
                if not self.start_service(service):
                    success = False

        return success

    def stop_all(self) -> bool:
        """Stop all services."""
        logger.info("Stopping all services...")
        success = True

        for service in [self.config.hub, self.config.nusyq, self.config.simulatedverse]:
            if service.pid:
                if not self.stop_service(service):
                    success = False

        return success

    def restart_all(self) -> bool:
        """Restart all services."""
        logger.info("Restarting all services...")
        self.stop_all()
        time.sleep(2)
        return self.start_all()


def main():
    parser = argparse.ArgumentParser(description="Unified Bootstrap for NuSyQ Ecosystem")
    parser.add_argument(
        "command",
        choices=["start", "stop", "status", "health", "restart", "bootstrap"],
        help="Command to execute",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    bootstrap = UnifiedBootstrap()

    print("🚀 NuSyQ Unified Bootstrap")
    print("=" * 30)

    # Detect paths
    print("📍 Detected paths:")
    for name, path in bootstrap.config.base_paths.items():
        print(f"   {name}: {path}")
    print()

    success = True

    if args.command == "start":
        success = bootstrap.start_all()
    elif args.command == "stop":
        success = bootstrap.stop_all()
    elif args.command == "status":
        bootstrap.show_status()
    elif args.command == "health":
        success = bootstrap.run_health_checks()
    elif args.command == "restart":
        success = bootstrap.restart_all()
    elif args.command == "bootstrap":
        success = bootstrap.bootstrap_ecosystem()

    if success:
        print("✅ Operation completed successfully")
    else:
        print("❌ Operation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
