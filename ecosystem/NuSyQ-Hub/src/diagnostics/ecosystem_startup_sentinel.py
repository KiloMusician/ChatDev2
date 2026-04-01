#!/usr/bin/env python3
"""🏥 NuSyQ Ecosystem Startup Health Check & Auto-Activation System.

Ensures all autonomous systems are running when VS Code starts or computer restarts.

OmniTag: {
    "purpose": "startup_health_sentinel",
    "tags": ["Python", "autonomous", "health_monitoring", "startup_automation"],
    "category": "system_activation",
    "evolution_stage": "v1.0_production"
}
"""

from __future__ import annotations

import codecs
import io
import json
import logging
import os
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    pass

# Centralized service configuration using factory pattern
from src.utils.config_factory import get_service_config

try:
    from src.utils import config_helper
except ImportError:
    config_helper = None  # type: ignore[assignment]

# Fix Windows console UTF-8 encoding for emojis
if sys.platform == "win32":
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")
    except (AttributeError, io.UnsupportedOperation):
        logging.getLogger(__name__).debug("Suppressed AttributeError/io", exc_info=True)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EcosystemStartupSentinel:
    """Monitors and activates autonomous systems on startup."""

    class AutonomousSystemConfig(TypedDict, total=False):
        """Defines AutonomousSystemConfig data."""

        name: str
        path: str | None
        required: bool
        auto_start: bool
        health_check: Callable[[], bool]
        activator: Callable[[], bool] | None
        description: str

    class SystemStatus(TypedDict):
        """Defines SystemStatus data."""

        active: bool
        dormant: bool
        error: bool
        state: str
        details: str

    class StartupReport(TypedDict):
        """Defines StartupReport data."""

        timestamp: str
        systems_checked: int
        systems_active: int
        systems_dormant: int
        systems_activated: int
        warnings: list[str]
        errors: list[str]
        status: dict[str, EcosystemStartupSentinel.SystemStatus]
        overall_health: float
        required_health: float

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize StartupReport with repo_root."""
        self.repo_root = repo_root or Path(__file__).resolve().parents[2]
        self.config_file = self.repo_root / "config" / "autonomous_systems_config.json"
        self.status_file = self.repo_root / "data" / "ecosystem_startup_status.json"

        # Define autonomous systems that should auto-start
        self.autonomous_systems: dict[str, EcosystemStartupSentinel.AutonomousSystemConfig] = {
            "culture_ship": {
                "name": "Culture Ship Strategic Oversight",
                "path": "scripts/launch_culture_ship.py",
                "required": False,
                "auto_start": False,  # Launch manually for now
                "activator": self._launch_culture_ship,
                "description": "Strategic oversight dashboard with Culture Mind decision support",
            },
            "wizard_navigator": {
                "name": "Wizard Navigator Repository Explorer",
                "path": "src/tools/wizard_navigator_consolidated.py",
                "required": False,
                "auto_start": False,  # Interactive tool
                "activator": None,
                "description": "Interactive repository navigation with AI assistance",
            },
            "ollama_service": {
                "name": "Ollama Local LLM Service",
                "path": None,  # External service
                "required": False,  # Optional but helpful for local AI
                "auto_start": True,
                "health_check": self._check_ollama_service,
                "activator": self._start_ollama_service,
            },
            "performance_monitor": {
                "name": "Performance Monitor",
                "path": "src/core/performance_monitor.py",
                "required": True,
                "auto_start": True,
                "health_check": self._check_performance_monitor,
                "activator": self._start_performance_monitor,
            },
            "architecture_watcher": {
                "name": "Architecture Watcher",
                "path": "src/core/ArchitectureWatcher.py",
                "required": True,
                "auto_start": True,
                "health_check": self._check_architecture_watcher,
                "activator": self._start_architecture_watcher,
            },
            "real_time_context_monitor": {
                "name": "Real-Time Context Monitor",
                "path": "src/real_time_context_monitor.py",
                "required": True,
                "auto_start": True,
                "health_check": self._check_context_monitor,
                "activator": self._start_context_monitor,
            },
            "multi_ai_orchestrator": {
                "name": "Multi-AI Orchestrator",
                "path": "src/orchestration/multi_ai_orchestrator.py",
                "required": False,
                "auto_start": False,  # On-demand only
                "health_check": self._check_orchestrator,
                "activator": None,
            },
            "quantum_workflow_automator": {
                "name": "Quantum Workflow Automator",
                "path": "src/orchestration/quantum_workflow_automation.py",
                "required": False,
                "auto_start": False,
                "health_check": self._check_quantum_workflows,
                "activator": None,
            },
            "rpg_inventory_system": {
                "name": "RPG Inventory System",
                "path": "src/system/rpg_inventory.py",
                "required": False,
                "auto_start": True,
                "health_check": self._check_rpg_system,
                "activator": self._start_rpg_system,
            },
        }

        self.startup_report: EcosystemStartupSentinel.StartupReport = {
            "timestamp": datetime.now().isoformat(),
            "systems_checked": 0,
            "systems_active": 0,
            "systems_dormant": 0,
            "systems_activated": 0,
            "warnings": [],
            "errors": [],
            "status": {},
            "overall_health": 0.0,
            "required_health": 0.0,
        }

    def run_startup_check(self) -> EcosystemStartupSentinel.StartupReport:
        """Run comprehensive startup health check."""
        # Check each autonomous system
        for system_id, system_config in self.autonomous_systems.items():
            self.startup_report["systems_checked"] += 1
            status = self._check_system(system_id, system_config)
            self.startup_report["status"][system_id] = status

            # Display status
            if status["active"]:
                logger.info("✅ %s is active", system_config.get("name", system_id))
            elif status["dormant"]:
                logger.info("⚠️ %s is dormant", system_config.get("name", system_id))
            else:
                logger.info("❌ %s is not available", system_config.get("name", system_id))

            # Auto-activate if configured
            if status["dormant"] and system_config.get("auto_start", False):
                activator = system_config.get("activator")
                if activator:
                    activated = activator()
                    if activated:
                        self.startup_report["systems_activated"] += 1
                        status["active"] = True
                        status["state"] = "ACTIVATED"
                    else:
                        self.startup_report["errors"].append(
                            f"Failed to activate {system_config.get('name', 'unknown')}",
                        )
                else:
                    self.startup_report["warnings"].append(
                        f"{system_config.get('name', 'unknown')} is dormant but has no activator",
                    )

        # Count active/dormant
        for status in self.startup_report["status"].values():
            if status["active"]:
                self.startup_report["systems_active"] += 1
            elif status["dormant"]:
                self.startup_report["systems_dormant"] += 1

        # Display summary

        if self.startup_report["warnings"]:
            for _warning in self.startup_report["warnings"]:
                logger.warning("Startup warning: %s", _warning)

        if self.startup_report["errors"]:
            for _error in self.startup_report["errors"]:
                logger.error("Startup error: %s", _error)

        # Save status report
        self._save_status_report()

        # Compute health focusing on required systems (optional systems are on-demand)
        required_total = sum(1 for cfg in self.autonomous_systems.values() if cfg.get("required"))
        required_active = 0
        for sys_id, status in self.startup_report["status"].items():
            if self.autonomous_systems.get(sys_id, {}).get("required") and status.get("active"):
                required_active += 1

        overall_health = (
            self.startup_report["systems_active"] / max(self.startup_report["systems_checked"], 1)
        ) * 100

        required_health = (
            (required_active / required_total) * 100 if required_total else overall_health
        )

        # Prefer required-system health for determining exit behavior
        # Decision is applied in main(); no action needed here beyond computing metrics.

        # Add computed health metrics to report
        self.startup_report["overall_health"] = overall_health
        self.startup_report["required_health"] = required_health

        return self.startup_report

    def _check_system(
        self, system_id: str, config: EcosystemStartupSentinel.AutonomousSystemConfig
    ) -> EcosystemStartupSentinel.SystemStatus:
        """Check status of an individual system."""
        status: EcosystemStartupSentinel.SystemStatus = {
            "active": False,
            "dormant": False,
            "error": False,
            "state": "UNKNOWN",
            "details": "",
        }

        try:
            # Check if file exists (skip for external services)
            path_value = config.get("path")
            if path_value:
                # Paths may be stored as strings or Path objects; normalize to Path
                system_path = self.repo_root / str(path_value)
                if not system_path.exists():
                    status["error"] = True
                    status["state"] = "NOT_FOUND"
                    status["details"] = f"File not found: {path_value}"
                    return status

            # Run health check if available
            health_check = config.get("health_check")
            if health_check and callable(health_check):
                try:
                    is_active = health_check()
                    if is_active:
                        status["active"] = True
                        status["state"] = "ACTIVE"
                    else:
                        status["dormant"] = True
                        status["state"] = "DORMANT"
                except Exception as e:
                    status["error"] = True
                    status["state"] = "HEALTH_CHECK_FAILED"
                    status["details"] = str(e)
            else:
                # No health check - assume dormant
                status["dormant"] = True
                status["state"] = "NO_HEALTH_CHECK"

        except Exception as e:
            status["error"] = True
            status["state"] = "ERROR"
            status["details"] = str(e)
            logger.exception("Error checking %s: %s", system_id, e)

        return status

    # Health check methods for specific systems
    def _check_ollama_service(self) -> bool:
        """Check if Ollama service is running."""
        try:
            import requests
        except ImportError:
            logger.debug("requests library not available")
            return False

        try:
            # Resolve Ollama base URL via centralized config factory
            config = get_service_config()
            if (
                config
                and hasattr(config, "_config")
                and config._config is not None
                and hasattr(config._config, "get_ollama_url")
            ):
                base_url = config._config.get_ollama_url()
            elif config_helper is not None:
                base_url = config_helper.get_ollama_host()
            else:
                # Conservative fallback if config unavailable
                host = os.environ.get("OLLAMA_BASE_URL") or os.environ.get(
                    "OLLAMA_HOST", "http://127.0.0.1"
                )
                port = os.environ.get("OLLAMA_PORT", "11434")
                base_url = f"{host.rstrip('/')}:{port}"

            response = requests.get(f"{base_url}/api/tags", timeout=3)
            status_code = int(getattr(response, "status_code", 0))
            return status_code == 200
        except requests.RequestException as e:
            logger.debug("Ollama health check request failed: %s", e)
            return False
        except Exception as e:
            logger.exception("Unexpected error during Ollama health check: %s", e)
            return False

    def _check_performance_monitor(self) -> bool:
        """Check if performance monitor is active."""
        status_file = self.repo_root / "data" / "performance" / "current_session.json"
        if status_file.exists():
            try:
                with open(status_file, encoding="utf-8") as f:
                    session_data = json.load(f)
                # Check if session is recent (within last hour)
                session_time = datetime.fromisoformat(session_data.get("start_time", ""))
                age = (datetime.now() - session_time).total_seconds()
                return age < 3600  # Active if less than 1 hour old
            except (OSError, json.JSONDecodeError, ValueError) as e:
                logger.exception("Error reading performance monitor session file: %s", e)
        return False

    def _check_architecture_watcher(self) -> bool:
        """Check if architecture watcher is running."""
        # Look for watcher process or recent architecture updates
        arch_file = self.repo_root / "data" / "KILO-FOOLISH_Master_Architecture.md"
        if arch_file.exists():
            # Check if recently updated (within last 24 hours)
            age = time.time() - arch_file.stat().st_mtime
            return age < 86400
        return False

    def _check_context_monitor(self) -> bool:
        """Check if real-time context monitor is active."""
        context_file = self.repo_root / "context.json"
        if context_file.exists():
            age = time.time() - context_file.stat().st_mtime
            return age < 3600  # Active if updated in last hour
        return False

    def _check_orchestrator(self) -> bool:
        """Check if multi-AI orchestrator is running."""
        # Check for orchestrator status file
        return False  # On-demand only

    def _check_quantum_workflows(self) -> bool:
        """Check if quantum workflow automator is active."""
        return False  # On-demand only

    def _check_rpg_system(self) -> bool:
        """Check if RPG inventory system is active."""
        rpg_status = self.repo_root / "data" / "rpg_inventory_state.json"
        if rpg_status.exists():
            age = time.time() - rpg_status.stat().st_mtime
            return age < 3600
        return False

    # Activation methods for specific systems
    def _start_ollama_service(self) -> bool:
        """Start Ollama service in background."""
        try:
            # Check if ollama is in PATH
            result = subprocess.run(
                ["ollama", "--version"], check=False, capture_output=True, timeout=5
            )

            if result.returncode != 0:
                logger.warning("Ollama not found in PATH - skipping auto-start")
                return False

            # Start Ollama service in background
            if sys.platform == "win32":
                subprocess.Popen(
                    ["ollama", "serve"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            # Wait briefly for service to start
            logger.info("Ollama service starting... (waiting 5s)")
            time.sleep(5)

            # Verify it started
            if self._check_ollama_service():
                logger.info("✅ Ollama service started successfully")
                return True
            logger.warning("⚠️ Ollama service started but not yet responding")
            return False

        except subprocess.TimeoutExpired:
            logger.exception("Ollama version check timed out")
            return False
        except FileNotFoundError:
            logger.warning("Ollama executable not found - install from ollama.ai")
            return False
        except Exception as e:
            logger.exception("Failed to start Ollama service: %s", e)
            return False

    def _start_performance_monitor(self) -> bool:
        """Start performance monitor system."""
        try:
            # Import and start in background - ensure proper path
            if str(self.repo_root) not in sys.path:
                sys.path.insert(0, str(self.repo_root))

            from src.core.performance_monitor import PerformanceMonitor

            monitor = PerformanceMonitor(self.repo_root)
            session_id = monitor.start_session("startup_auto_session")
            monitor.start_background_monitoring()

            logger.info("Started performance monitor: %s", session_id)
            return True
        except Exception as e:
            logger.exception("Failed to start performance monitor: %s", e)
            return False

    def _start_architecture_watcher(self) -> bool:
        """Start architecture watcher system."""
        try:
            # Start watcher in background process
            watcher_path = self.repo_root / "src" / "healing" / "ArchitectureWatcher.py"
            if not watcher_path.exists():
                return False

            # Run initial scan instead of continuous watching (less invasive)
            scanner_path = (
                self.repo_root / "src" / "core" / "ArchitectureScanner.py"
            )  # FIX: Correct path
            if scanner_path.exists():
                subprocess.Popen(
                    [sys.executable, str(scanner_path)],
                    cwd=str(self.repo_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info("Triggered architecture scan")
                return True
            return False
        except Exception as e:
            logger.exception("Failed to start architecture watcher: %s", e)
            return False

    def _start_context_monitor(self) -> bool:
        """Start real-time context monitor."""
        try:
            import asyncio
            import threading

            if str(self.repo_root) not in sys.path:
                sys.path.insert(0, str(self.repo_root))

            from src.real_time_context_monitor import RealTimeContextMonitor

            # Create new event loop for context monitor
            loop = asyncio.new_event_loop()

            def run_monitor() -> None:
                asyncio.set_event_loop(loop)
                monitor = RealTimeContextMonitor()
                monitor.start_monitoring()
                loop.run_forever()

            # Start in background thread
            monitor_thread = threading.Thread(target=run_monitor, daemon=True)
            monitor_thread.start()

            logger.info("Started real-time context monitor with async event loop")
            return True
        except Exception as e:
            logger.exception("Failed to start context monitor: %s", e)
            return False

    def _start_rpg_system(self) -> bool:
        """Start RPG inventory system."""
        try:
            if str(self.repo_root) not in sys.path:
                sys.path.insert(0, str(self.repo_root))

            from src.system.rpg_inventory import RPGInventorySystem

            rpg = RPGInventorySystem()
            # Update state without starting full monitoring via public API
            rpg.update_resource_metrics()

            logger.info("Started RPG inventory system")
            return True
        except Exception as e:
            logger.exception("Failed to start RPG system: %s", e)
            return False

    def _save_status_report(self) -> None:
        """Save status report to file."""
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.status_file, "w", encoding="utf-8") as f:
            json.dump(self.startup_report, f, indent=2)

    def _launch_culture_ship(self) -> bool:
        """Launch Culture Ship strategic oversight GUI."""
        try:
            culture_ship_script = self.repo_root / "scripts" / "launch_culture_ship.py"
            if culture_ship_script.exists():
                # Launch in background with Zen validation (non-blocking)
                from src.utils.safe_subprocess import safe_subprocess

                safe_subprocess.Popen(
                    [sys.executable, str(culture_ship_script)],
                    cwd=str(self.repo_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info("🚀 Culture Ship launched successfully (Zen-validated)")
                return True
            return False
        except Exception as e:
            logger.exception("Failed to launch Culture Ship: %s", e)
            return False


def main() -> None:
    """Main entry point for startup health check."""
    sentinel = EcosystemStartupSentinel()
    report = sentinel.run_startup_check()

    # Exit with error code if required-system health is poor (optional systems may remain dormant)
    required_health = report.get("required_health")
    if required_health is None:
        # Fallback to previous overall calculation
        health_score = (report["systems_active"] / report["systems_checked"]) * 100
        if health_score < 70:
            sys.exit(1)
        sys.exit(0)

    # Use stricter threshold for required systems
    if required_health < 90:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
