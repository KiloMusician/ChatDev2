#!/usr/bin/env python3
"""🔄 KILO-FOOLISH Process & Terminal Management System.

Tracks all running processes, manages terminal sessions, and provides administrative access.

OmniTag: {
    "purpose": "process_management_system",
    "type": "system_administration",
    "evolution_stage": "v4.0_enhanced"
}
MegaTag: {
    "scope": "terminal_management",
    "integration_points": ["subprocess_tracking", "administrative_access", "copilot_sessions"],
    "quantum_context": "process_consciousness_tracking"
}
RSHTS: ΞΨΩ∞⟨PROCESS_MGMT⟩→ΦΣΣ
"""

import json
import logging
import os
import shlex
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

from src.utils.graceful_shutdown import GracefulShutdownMixin, ShutdownConfig

logger = logging.getLogger(__name__)


class ProcessManager(GracefulShutdownMixin):
    """Comprehensive process and terminal management for Copilot sessions with graceful shutdown."""

    def __init__(self, shutdown_config: ShutdownConfig | None = None) -> None:
        """Initialize ProcessManager with shutdown_config."""
        super().__init__(shutdown_config)
        self.repo_root = Path.cwd()
        self.process_log = self.repo_root / "data" / "logs" / "process_management.json"
        self.terminal_sessions: dict[str, Any] = {}
        self.background_processes: dict[str, Any] = {}
        self.admin_terminals: dict[str, Any] = {}
        self.process_history: list[dict[str, Any]] = []

        # Ensure directories exist
        self.process_log.parent.mkdir(parents=True, exist_ok=True)

        # Register cleanup and state saving
        self.register_cleanup_task(self._cleanup_background_processes)
        self.register_state_saver(self._save_final_state)

        # Load existing process state
        self.load_process_state()

    def scan_existing_processes(self) -> dict[str, Any]:
        """Scan for existing processes related to our repository."""
        current_processes: dict[str, list[Any]] = {
            "copilot_related": [],
            "vscode_related": [],
            "powershell_sessions": [],
            "python_processes": [],
            "system_processes": [],
            "background_jobs": [],
        }

        try:
            # Get current process info
            current_pid = os.getpid()
            psutil.Process(current_pid)

            # Scan all processes
            for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time", "status"]):
                try:
                    proc_info = proc.info
                    proc_name = proc_info["name"].lower()
                    cmdline = " ".join(proc_info["cmdline"] or []).lower()

                    # Categorize processes
                    if "copilot" in proc_name or "copilot" in cmdline:
                        current_processes["copilot_related"].append(
                            {
                                "pid": proc_info["pid"],
                                "name": proc_info["name"],
                                "cmdline": proc_info["cmdline"],
                                "status": proc_info["status"],
                                "create_time": datetime.fromtimestamp(
                                    proc_info["create_time"]
                                ).isoformat(),
                            }
                        )

                    elif "code" in proc_name or "vscode" in proc_name:
                        current_processes["vscode_related"].append(
                            {
                                "pid": proc_info["pid"],
                                "name": proc_info["name"],
                                "status": proc_info["status"],
                                "create_time": datetime.fromtimestamp(
                                    proc_info["create_time"]
                                ).isoformat(),
                            }
                        )

                    elif "powershell" in proc_name or "pwsh" in proc_name:
                        current_processes["powershell_sessions"].append(
                            {
                                "pid": proc_info["pid"],
                                "name": proc_info["name"],
                                "cmdline": proc_info["cmdline"],
                                "status": proc_info["status"],
                                "create_time": datetime.fromtimestamp(
                                    proc_info["create_time"]
                                ).isoformat(),
                            }
                        )

                    elif "python" in proc_name and any(
                        self.repo_root.name in arg for arg in (proc_info["cmdline"] or [])
                    ):
                        current_processes["python_processes"].append(
                            {
                                "pid": proc_info["pid"],
                                "name": proc_info["name"],
                                "cmdline": proc_info["cmdline"],
                                "status": proc_info["status"],
                                "create_time": datetime.fromtimestamp(
                                    proc_info["create_time"]
                                ).isoformat(),
                            }
                        )

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    # Process disappeared or access denied
                    continue

        except (OSError, AttributeError, ValueError):
            logger.debug("Suppressed AttributeError/OSError/ValueError", exc_info=True)

        return current_processes

    def create_admin_terminal(self, session_name: str | None = None) -> dict[str, Any]:
        """Create a new administrative PowerShell terminal session."""
        if not session_name:
            session_name = f"admin_session_{int(time.time())}"

        try:
            # Create PowerShell script for elevated session
            script_content = f"""
# KILO-FOOLISH Administrative Terminal Session
$Host.UI.RawUI.WindowTitle = "KILO-FOOLISH Admin: {session_name}"
Write-Host "🎮 KILO-FOOLISH Administrative Terminal" -ForegroundColor Cyan
Write-Host "Session: {session_name}" -ForegroundColor Yellow
Write-Host "PID: $PID" -ForegroundColor Green
Write-Host "Admin: $(([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator'))" -ForegroundColor Magenta
Write-Host "Working Directory: $(Get-Location)" -ForegroundColor Blue
Write-Host "==============================================" -ForegroundColor Cyan

# set execution policy
set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Change to repository directory
Set-Location "{self.repo_root}"

# Create session tracking file
$sessionInfo = @{{
    session_name = "{session_name}"
    pid = $PID
    created = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    admin_status = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')
    working_directory = "$(Get-Location)"
}}

$sessionInfo | ConvertTo-Json | Out-File -FilePath "logs/storage/terminal_session_{session_name}.json" -Encoding UTF8

Write-Host "✅ Administrative session ready!" -ForegroundColor Green
Write-Host "📝 Session logged to: logs/storage/terminal_session_{session_name}.json" -ForegroundColor Yellow
"""

            # Save script to temporary file
            temp_script = self.repo_root / "temp" / f"admin_session_{session_name}.ps1"
            temp_script.parent.mkdir(parents=True, exist_ok=True)

            with open(temp_script, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Try to start elevated PowerShell process
            try:
                # Method 1: Use subprocess with shell execution
                process = subprocess.Popen(
                    [
                        "powershell.exe",
                        "-ExecutionPolicy",
                        "RemoteSigned",
                        "-NoExit",
                        "-File",
                        str(temp_script),
                    ],
                    creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
                    cwd=str(self.repo_root),
                )

                session_info = {
                    "session_name": session_name,
                    "pid": process.pid,
                    "created": datetime.now().isoformat(),
                    "script_path": str(temp_script),
                    "status": "created",
                    "method": "subprocess_create_new_console",
                }

                self.admin_terminals[session_name] = session_info
                return session_info

            except Exception as subprocess_error:
                # Method 2: Try using os.system
                try:
                    command = f'start powershell -ExecutionPolicy RemoteSigned -NoExit -File "{temp_script}"'
                    os.system(command)

                    session_info = {
                        "session_name": session_name,
                        "created": datetime.now().isoformat(),
                        "script_path": str(temp_script),
                        "status": "created_via_os_system",
                        "method": "os_system_start",
                    }

                    self.admin_terminals[session_name] = session_info
                    return session_info

                except Exception as os_error:
                    return {"error": f"Failed to create terminal: {subprocess_error}, {os_error}"}

        except Exception as e:
            return {"error": str(e)}

    def create_background_process(
        self,
        command: str,
        name: str | None = None,
        max_runtime_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Create a background process with tracking."""
        if not name:
            name = f"bg_process_{int(time.time())}"

        try:
            command_list = shlex.split(command)
            # Start background process
            process = subprocess.Popen(
                command_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.repo_root),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )

            process_info = {
                "name": name,
                "pid": process.pid,
                "command": command,
                "created": datetime.now().isoformat(),
                "status": "running",
                "is_background": True,
                "max_runtime_seconds": max_runtime_seconds,
                "stdout_file": f"logs/storage/bg_process_{name}_stdout.log",
                "stderr_file": f"logs/storage/bg_process_{name}_stderr.log",
            }

            self.background_processes[name] = {
                "info": process_info,
                "process": process,
            }

            if max_runtime_seconds and max_runtime_seconds > 0:
                timer = threading.Timer(
                    max_runtime_seconds,
                    self._terminate_background_process,
                    args=(name, process, "max_runtime"),
                )
                timer.daemon = True
                timer.start()

            # Start output monitoring thread
            threading.Thread(
                target=self._monitor_background_process,
                args=(name, process),
                daemon=True,
            ).start()

            return process_info

        except Exception as e:
            return {"error": str(e)}

    def _terminate_background_process(
        self, name: str, process: subprocess.Popen, reason: str
    ) -> None:
        """Terminate a tracked background process."""
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        except (OSError, subprocess.SubprocessError):
            logger.debug("Suppressed OSError/subprocess", exc_info=True)
        finally:
            info = self.background_processes.get(name, {}).get("info", {})
            if info:
                info["status"] = "terminated"
                info["terminated_reason"] = reason
                info["terminated_at"] = datetime.now().isoformat()

    def _monitor_background_process(self, name: str, process: subprocess.Popen) -> None:
        """Monitor background process output."""
        stdout_file = self.repo_root / "data" / "logs" / f"bg_process_{name}_stdout.log"
        stderr_file = self.repo_root / "data" / "logs" / f"bg_process_{name}_stderr.log"

        stdout_file.parent.mkdir(parents=True, exist_ok=True)
        stderr_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Monitor stdout
            if process.stdout:
                with open(stdout_file, "w", encoding="utf-8") as f:
                    for line in iter(process.stdout.readline, b""):
                        if line:
                            f.write(line.decode("utf-8", errors="ignore"))
                            f.flush()

            # Monitor stderr
            if process.stderr:
                with open(stderr_file, "w", encoding="utf-8") as f:
                    for line in iter(process.stderr.readline, b""):
                        if line:
                            f.write(line.decode("utf-8", errors="ignore"))
                            f.flush()

        except (OSError, UnicodeDecodeError):
            logger.debug("Suppressed OSError/UnicodeDecodeError", exc_info=True)

    def get_terminal_status(self) -> dict[str, Any]:
        """Get status of all terminal sessions and processes."""
        terminal_state_path = self.repo_root / "data" / "intelligent_terminal_state.json"
        terminal_state: dict[str, Any] = {}
        if terminal_state_path.exists():
            try:
                terminal_state = json.loads(terminal_state_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                terminal_state = {}

        status = {
            "timestamp": datetime.now().isoformat(),
            "admin_terminals": {},
            "background_processes": {},
            "system_processes": self.scan_existing_processes(),
            "total_terminals": len(self.admin_terminals),
            "total_background": len(self.background_processes),
            "intelligent_terminal_state": terminal_state,
            "intelligent_terminal_count": terminal_state.get("total_terminals", 0),
        }

        # Check admin terminal status
        for session_name, session_info in self.admin_terminals.items():
            # Check if session log file exists (indicates terminal is active)
            session_log = self.repo_root / "data" / "logs" / f"terminal_session_{session_name}.json"
            status["admin_terminals"][session_name] = {
                **session_info,
                "active": session_log.exists(),
                "log_file": str(session_log),
            }

        # Check background process status
        for name, bg_info in self.background_processes.items():
            process = bg_info["process"]
            try:
                poll_result = process.poll()
                is_running = poll_result is None
                status["background_processes"][name] = {
                    **bg_info["info"],
                    "running": is_running,
                    "return_code": poll_result,
                    "cpu_percent": (psutil.Process(process.pid).cpu_percent() if is_running else 0),
                }
            except (psutil.NoSuchProcess, AttributeError):
                status["background_processes"][name] = {
                    **bg_info["info"],
                    "running": False,
                    "status": "terminated",
                }

        return status

    def save_process_state(self) -> None:
        """Save current process state to file."""
        state = {
            "timestamp": datetime.now().isoformat(),
            "admin_terminals": self.admin_terminals,
            "background_processes": {
                name: info["info"] for name, info in self.background_processes.items()
            },
            "process_history": self.process_history[-100:],  # Keep last 100 entries
        }

        with open(self.process_log, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)

    def load_process_state(self) -> None:
        """Load process state from file."""
        try:
            if self.process_log.exists():
                with open(self.process_log, encoding="utf-8") as f:
                    state = json.load(f)

                self.admin_terminals = state.get("admin_terminals", {})
                self.process_history = state.get("process_history", [])
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            logger.debug("Suppressed FileNotFoundError/OSError/json", exc_info=True)

    def cleanup_terminated_processes(self) -> None:
        """Clean up terminated processes and sessions."""
        # Clean up background processes
        terminated: list[Any] = []
        for name, bg_info in self.background_processes.items():
            try:
                if bg_info["process"].poll() is not None:
                    terminated.append(name)
            except (AttributeError, OSError):
                terminated.append(name)

        for name in terminated:
            del self.background_processes[name]

        # Clean up admin terminals (check if session logs are stale)
        stale_terminals: list[Any] = []
        for session_name in self.admin_terminals:
            session_log = self.repo_root / "data" / "logs" / f"terminal_session_{session_name}.json"
            if session_log.exists():
                try:
                    # Check if log is older than 1 hour with no recent updates
                    stat = session_log.stat()
                    age = time.time() - stat.st_mtime
                    if age > 3600:  # 1 hour
                        stale_terminals.append(session_name)
                except (OSError, AttributeError):
                    stale_terminals.append(session_name)

        for session_name in stale_terminals:
            del self.admin_terminals[session_name]

    def generate_report(self) -> str:
        """Generate comprehensive process management report."""
        status = self.get_terminal_status()

        report = f"""
# 🔄 KILO-FOOLISH Process Management Report

## 📊 Current Status
*Generated: {status["timestamp"]}*

### 🖥️ Administrative Terminals
Total Active: {status["total_terminals"]}
Intelligent Groups: {status.get("intelligent_terminal_count", 0)}

"""

        if status["admin_terminals"]:
            for session_name, terminal_info in status["admin_terminals"].items():
                active_status = "🟢 ACTIVE" if terminal_info["active"] else "🔴 INACTIVE"
                report += f"""
**{session_name}**
- Status: {active_status}
- Created: {terminal_info.get("created", "Unknown")}
- Method: {terminal_info.get("method", "Unknown")}
- Log: {terminal_info.get("log_file", "None")}
"""
        else:
            report += "No administrative terminals currently active.\n"

        terminal_groups = status.get("intelligent_terminal_state", {}).get("terminals", {})
        if terminal_groups:
            report += "\n### 🧭 Intelligent Terminal Groups\n"
            for term_id, term in terminal_groups.items():
                name = term.get("name", term_id)
                report += f"- {name} ({term_id})\n"

        report += f"""
### 🔄 Background Processes
Total Running: {status["total_background"]}

"""

        if status["background_processes"]:
            for process_name, process_info in status["background_processes"].items():
                running_status = "🟢 RUNNING" if process_info["running"] else "🔴 STOPPED"
                report += f"""
**{process_name}**
- Status: {running_status}
- PID: {process_info.get("pid", "Unknown")}
- Command: {process_info.get("command", "Unknown")[:50]}...
- CPU: {process_info.get("cpu_percent", 0):.1f}%
"""
        else:
            report += "No background processes currently running.\n"

        report += f"""
### 🔍 System Process Summary

**VS Code Related:** {len(status["system_processes"]["vscode_related"])} processes
**PowerShell Sessions:** {len(status["system_processes"]["powershell_sessions"])} sessions
**Python Processes:** {len(status["system_processes"]["python_processes"])} processes
**Copilot Related:** {len(status["system_processes"]["copilot_related"])} processes

### 🎯 Recommendations

"""

        if status["total_terminals"] == 0:
            report += "- **Create Administrative Terminal**: Run `create_admin_terminal()` for elevated access\n"

        if len(status["system_processes"]["powershell_sessions"]) > 5:
            report += "- **Consider Cleanup**: Many PowerShell sessions detected - consider consolidation\n"

        report += """
### 🛠️ Available Actions

1. **Create Admin Terminal**: `process_manager.create_admin_terminal("session_name")`
2. **Start Background Process**: `process_manager.create_background_process("command", "name")`
3. **Check Status**: `process_manager.get_terminal_status()`
4. **Cleanup**: `process_manager.cleanup_terminated_processes()`

---
*Process management is key to maintaining clean Copilot workflows*
"""

        return report

    def _graceful_shutdown_impl(self) -> None:
        """Implementation-specific graceful shutdown logic."""
        logger.info("🛑 ProcessManager: Beginning graceful shutdown")

        # Stop any monitoring loops
        self.monitoring_active = False

        # Wait a moment for background operations to complete
        time.sleep(1)

        logger.info("✅ ProcessManager: Graceful shutdown implementation complete")

    def _cleanup_background_processes(self) -> None:
        """Cleanup background processes during shutdown."""
        logger.info("🧹 ProcessManager: Cleaning up background processes")

        for name, process_info in list(self.background_processes.items()):
            try:
                process = process_info.get("process")
                if process and process.poll() is None:  # Still running
                    logger.info(f"🛑 Terminating background process: {name}")
                    process.terminate()

                    # Give it a moment to terminate gracefully
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"⚠️ Force killing background process: {name}")
                        process.kill()

            except Exception as e:
                logger.exception(f"❌ Error cleaning up process {name}: {e}")

        self.background_processes.clear()

    def _save_final_state(self) -> None:
        """Save final state during shutdown."""
        logger.info("💾 ProcessManager: Saving final state")
        try:
            self.save_process_state()
        except Exception as e:
            logger.exception(f"❌ Error saving final state: {e}")


def main():
    """Main function for testing and demonstration with graceful shutdown."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Create manager with graceful shutdown
    shutdown_config = ShutdownConfig(graceful_timeout=15.0, log_progress=True)
    manager = ProcessManager(shutdown_config)

    try:
        # Scan existing processes
        manager.scan_existing_processes()

        # Create administrative terminal
        admin_result = manager.create_admin_terminal("test_admin_session")
        if "error" not in admin_result:
            pass
        else:
            pass

        # Get status
        manager.get_terminal_status()

        # Generate and save report
        report = manager.generate_report()

        # Simulate running state
        while not manager.is_shutdown_requested():
            time.sleep(1)

    except KeyboardInterrupt:
        manager.request_shutdown("User interrupt")

    finally:
        # Execute graceful shutdown
        manager.execute_graceful_shutdown()
    report_path = manager.repo_root / "docs" / "reports" / "process_management_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # Save state
    manager.save_process_state()

    return manager


if __name__ == "__main__":
    manager = main()
