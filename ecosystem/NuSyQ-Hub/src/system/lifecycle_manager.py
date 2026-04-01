#!/usr/bin/env python3
"""ΞNuSyQ Lifecycle Manager.

========================
Single source of truth for system startup and shutdown sequences.

Responsibilities:
- Start services in correct order (Docker → Ollama → MCP → etc.)
- Verify each service before proceeding
- Clean shutdown (prevent orphan processes)
- State persistence (know what's running)
- Idempotent (safe to run multiple times)

Usage:
    python -m src.system.lifecycle_manager start   # Start all services
    python -m src.system.lifecycle_manager stop    # Stop all services
    python -m src.system.lifecycle_manager status  # Check what's running
    python -m src.system.lifecycle_manager restart # Full cycle
"""

import argparse
import json
import logging
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ServiceState(Enum):
    """Service states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class Service:
    """Service definition."""

    name: str
    check_fn: Callable[[], bool]
    start_fn: Callable[[], bool] | None = None
    stop_fn: Callable[[], bool] | None = None
    required: bool = True
    depends_on: list[str] = field(default_factory=list)
    state: ServiceState = ServiceState.UNKNOWN


class LifecycleManager:
    """Manages system lifecycle with deterministic start/stop sequences."""

    def __init__(self, repo_root: Path):
        """Initialize LifecycleManager with repo_root."""
        self.repo_root = repo_root
        self.state_file = repo_root / "data" / "lifecycle_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Define services in dependency order
        self.services: dict[str, Service] = {
            "docker": Service(
                name="Docker Daemon",
                check_fn=self._check_docker,
                start_fn=self._start_docker,
                required=False,  # Optional but recommended
                depends_on=[],
            ),
            "ollama": Service(
                name="Ollama LLM",
                check_fn=self._check_ollama,
                start_fn=self._start_ollama,
                stop_fn=self._stop_ollama,
                required=True,  # Core dependency
                depends_on=[],
            ),
            "vscode": Service(
                name="VS Code Workspace",
                check_fn=self._check_vscode,
                required=False,
                depends_on=[],
            ),
            "terminals": Service(
                name="Agent Terminals",
                check_fn=self._check_terminals,
                start_fn=self._start_terminals,
                required=False,
                depends_on=["vscode"],
            ),
            "quest_system": Service(
                name="Quest System",
                check_fn=self._check_quest_system,
                required=True,
                depends_on=[],
            ),
        }

    # =========================================================================
    # CHECK FUNCTIONS (Verify service state)
    # =========================================================================

    def _check_port(self, host: str, port: int, timeout: int = 2) -> bool:
        """Check if a port is listening."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (TimeoutError, ConnectionRefusedError, OSError):
            return False

    def _check_docker(self) -> bool:
        """Check if Docker daemon is running."""
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_docker_compose(self) -> bool:
        """Check if Docker Compose is available."""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_docker_context(self) -> str:
        """Get current Docker context (desktop-linux, etc)."""
        try:
            result = subprocess.run(
                ["docker", "context", "show"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return "unknown"

    def _check_ollama(self) -> bool:
        """Check if Ollama is running."""
        return self._check_port("localhost", 11434, timeout=2)

    def _check_vscode(self) -> bool:
        """Check if VS Code workspace is open."""
        # Check for .vscode directory
        return (self.repo_root / ".vscode").exists()

    def _check_terminals(self) -> bool:
        """Check if agent terminals are set up."""
        # For now, assume terminals exist if terminal config exists
        terminal_config = self.repo_root / "data" / "terminal_config.json"
        return terminal_config.exists()

    def _check_quest_system(self) -> bool:
        """Check if quest system is operational."""
        quest_log = self.repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        return quest_log.exists()

    # =========================================================================
    # START FUNCTIONS (Launch services)
    # =========================================================================

    def _is_wsl(self) -> bool:
        """Detect when the manager is running inside WSL."""
        return bool(os.environ.get("WSL_DISTRO_NAME") or Path("/run/WSL").exists())

    def _start_docker(self) -> bool:
        """Start Docker Desktop."""
        system = platform.system()
        try:
            if system == "Windows":
                # Try to start Docker Desktop
                subprocess.Popen(
                    ["C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info("  Launched Docker Desktop (waiting 15s for daemon...)")
                time.sleep(15)
                return self._check_docker()
            elif system == "Darwin":  # macOS
                subprocess.Popen(
                    ["open", "-a", "Docker"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(15)
                return self._check_docker()
            elif system == "Linux":
                if self._is_wsl():
                    logger.info("  Running inside WSL; start Docker Desktop on the Windows host.")
                    logger.info("  Run scripts/wait_for_docker.py after Docker Desktop boots.")
                    return False

                systemctl_path = shutil.which("systemctl")
                if systemctl_path:
                    try:
                        subprocess.run([systemctl_path, "start", "docker"], check=True)
                        time.sleep(5)
                        return self._check_docker()
                    except subprocess.CalledProcessError as err:
                        logger.error(f"  systemctl start docker failed: {err}")

                dockerd_path = shutil.which("dockerd")
                if dockerd_path:
                    logger.info("  Launching dockerd directly (no systemctl detected).")
                    subprocess.Popen(
                        [dockerd_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    time.sleep(5)
                    return self._check_docker()

                logger.info(
                    "  Docker daemon binary not found; install Docker Engine or start Docker Desktop."
                )
                return False
        except Exception as e:
            logger.error(f"  Failed to start Docker: {e}")
            return False

        return False

    def _start_ollama(self) -> bool:
        """Start Ollama server."""
        try:
            # Start Ollama in background
            if platform.system() == "Windows":
                subprocess.Popen(
                    ["ollama", "serve"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            logger.info("  Started Ollama (waiting 10s for models...)")
            time.sleep(10)
            return self._check_ollama()
        except Exception as e:
            logger.error(f"  Failed to start Ollama: {e}")
            return False

    def _start_terminals(self) -> bool:
        """Initialize agent terminals."""
        # This would integrate with terminal management layer (FIX 3)
        logger.info("  Terminal management not yet implemented")
        return True

    # =========================================================================
    # STOP FUNCTIONS (Shutdown services)
    # =========================================================================

    def _stop_ollama(self) -> bool:
        """Stop Ollama server."""
        try:
            # Find and kill Ollama process
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], check=False)
            else:
                subprocess.run(["pkill", "-f", "ollama serve"], check=False)

            time.sleep(2)
            return not self._check_ollama()
        except Exception as e:
            logger.error(f"  Failed to stop Ollama: {e}")
            return False

    # =========================================================================
    # LIFECYCLE ORCHESTRATION
    # =========================================================================

    def check_all_services(self) -> dict[str, ServiceState]:
        """Check status of all services."""
        status = {}
        for key, svc in self.services.items():
            try:
                is_running = svc.check_fn()
                svc.state = ServiceState.RUNNING if is_running else ServiceState.STOPPED
            except Exception as e:
                logger.error(f"  Error checking {svc.name}: {e}")
                svc.state = ServiceState.UNKNOWN
            status[key] = svc.state

        return status

    def start_all_services(self, force: bool = False) -> bool:
        """Start all services in dependency order."""
        logger.info("\n🚀 Starting ΞNuSyQ Ecosystem Services...")
        logger.info("=" * 60)

        # Check current state first
        self.check_all_services()

        success = True
        for _key, svc in self.services.items():
            # Check dependencies
            for dep in svc.depends_on:
                if self.services[dep].state != ServiceState.RUNNING:
                    logger.warning(
                        f"⚠️  {svc.name} depends on {self.services[dep].name} (not running)"
                    )
                    if svc.required:
                        success = False
                        continue

            # Skip if already running (unless force)
            if svc.state == ServiceState.RUNNING and not force:
                logger.info(f"✅ {svc.name:30s} [already running]")
                continue

            # Try to start
            if svc.start_fn:
                logger.info(f"⏳ {svc.name:30s} [starting...]")
                svc.state = ServiceState.STARTING
                try:
                    if svc.start_fn():
                        svc.state = ServiceState.RUNNING
                        logger.info(f"✅ {svc.name:30s} [started successfully]")
                    else:
                        svc.state = ServiceState.FAILED
                        logger.error(f"❌ {svc.name:30s} [failed to start]")
                        if svc.required:
                            success = False
                except Exception as e:
                    svc.state = ServiceState.FAILED
                    logger.error(f"❌ {svc.name:30s} [error: {e}]")
                    if svc.required:
                        success = False
            else:
                # No start function - check if it's running
                if svc.check_fn():
                    svc.state = ServiceState.RUNNING
                    logger.info(f"✅ {svc.name:30s} [available]")
                else:
                    svc.state = ServiceState.STOPPED
                    status_text = "required but not running" if svc.required else "optional"
                    logger.warning(f"⚠️  {svc.name:30s} [{status_text}]")
                    if svc.required:
                        success = False

        self._save_state()
        logger.info("\n" + "=" * 60)
        if success:
            logger.info("✅ ΞNuSyQ Ecosystem Ready")
        else:
            logger.error("⚠️  Some required services failed to start")

        return success

    def stop_all_services(self) -> bool:
        """Stop all services in reverse dependency order."""
        logger.info("\n🛑 Stopping ΞNuSyQ Ecosystem Services...")
        logger.info("=" * 60)

        # Stop in reverse order
        for key in reversed(list(self.services.keys())):
            svc = self.services[key]
            if svc.state != ServiceState.RUNNING:
                logger.info(f"⏭️  {svc.name:30s} [not running, skipped]")
                continue

            if svc.stop_fn:
                logger.info(f"⏳ {svc.name:30s} [stopping...]")
                try:
                    if svc.stop_fn():
                        svc.state = ServiceState.STOPPED
                        logger.info(f"✅ {svc.name:30s} [stopped]")
                    else:
                        logger.error(f"⚠️  {svc.name:30s} [failed to stop cleanly]")
                except Exception as e:
                    logger.error(f"❌ {svc.name:30s} [error: {e}]")
            else:
                logger.info(f"Info: {svc.name:30s} [no stop function]")

        self._save_state()
        logger.info("\n" + "=" * 60)
        logger.info("✅ ΞNuSyQ Ecosystem Stopped")
        return True

    def print_status(self) -> None:
        """Print current service status."""
        status = self.check_all_services()
        logger.info("\n📊 ΞNuSyQ Ecosystem Status")
        logger.info("=" * 60)

        for key, svc in self.services.items():
            state = status[key]
            emoji = {
                ServiceState.RUNNING: "✅",
                ServiceState.STOPPED: "❌",
                ServiceState.STARTING: "⏳",
                ServiceState.FAILED: "💥",
                ServiceState.UNKNOWN: "❓",
            }[state]

            required_text = "(required)" if svc.required else "(optional)"
            logger.info(f"{emoji} {svc.name:30s} {state.value:10s} {required_text}")

        running_count = sum(1 for s in status.values() if s == ServiceState.RUNNING)
        total_required = sum(1 for s in self.services.values() if s.required)
        logger.info(f"\n📈 {running_count}/{len(self.services)} services running")
        logger.info(f"📌 {total_required} required services defined")

    def _save_state(self) -> None:
        """Save current state to disk."""
        state_data = {
            "timestamp": datetime.now().isoformat(),
            "services": {
                key: {"state": svc.state.value, "name": svc.name}
                for key, svc in self.services.items()
            },
        }
        self.state_file.write_text(json.dumps(state_data, indent=2), encoding="utf-8")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="ΞNuSyQ Lifecycle Manager")
    parser.add_argument(
        "action",
        choices=["start", "stop", "restart", "status"],
        help="Lifecycle action to perform",
    )
    parser.add_argument("--force", action="store_true", help="Force restart even if running")

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    manager = LifecycleManager(repo_root)

    if args.action == "start":
        success = manager.start_all_services(force=args.force)
        return 0 if success else 1

    elif args.action == "stop":
        manager.stop_all_services()
        return 0

    elif args.action == "restart":
        manager.stop_all_services()
        time.sleep(2)
        success = manager.start_all_services(force=True)
        return 0 if success else 1

    elif args.action == "status":
        manager.print_status()
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
