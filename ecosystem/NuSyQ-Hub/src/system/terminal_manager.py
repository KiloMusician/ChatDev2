#!/usr/bin/env python3
"""🖥️ Terminal Manager - Robust Terminal Output Access System.

Enhanced terminal interaction with fallback methods and session tracking.

🏷️ OmniTag: terminal_manager|system_integration|output_access|session_tracking
🏷️ MegaTag: terminal_output_reliability|command_execution|debugging_support
🏷️ RSHTS: recursive_terminal_access|self_healing_output|quantum_session_management
"""

import json
import logging
import os
import signal
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TerminalSession:
    """Terminal session tracking with enhanced metadata."""

    session_id: str
    start_time: datetime
    last_activity: datetime
    command_count: int
    status: str  # active, idle, closed
    working_directory: str
    environment: dict[str, str]
    command_history: list[dict[str, Any]]

    def to_dict(self) -> None:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "command_count": self.command_count,
            "status": self.status,
            "working_directory": self.working_directory,
            "environment": self.environment,
            "command_history": self.command_history,
        }


class EnhancedTerminalManager:
    """🧠 KILO-FOOLISH Terminal Management System.

    Provides robust terminal output access with multiple fallback methods,
    session tracking, and quantum-consciousness integration.
    """

    def __init__(self, workspace_root: Path | None = None) -> None:
        """Initialize EnhancedTerminalManager with workspace_root."""
        root_env = os.getenv("NU_SYQ_HUB_ROOT", str(Path(__file__).resolve().parents[2]))
        self.workspace_root = workspace_root or Path(root_env).expanduser()
        self.sessions_file = self.workspace_root / "data" / "terminal_sessions.json"
        self.output_cache = self.workspace_root / "data" / "terminal_output_cache"
        self.active_sessions: dict[str, TerminalSession] = {}

        # Ensure directories exist
        self.sessions_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_cache.mkdir(parents=True, exist_ok=True)

        # Initialize consciousness and tracking
        self.consciousness_data: dict[str, Any] = {}
        self.consciousness_track: Any = None

        # Load existing sessions
        self._load_sessions()

        # Register quantum-consciousness hooks
        self._register_consciousness_hooks()

    def _load_sessions(self) -> None:
        """Load existing terminal sessions from persistence."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for session_data in data.get("sessions", []):
                        session = TerminalSession(
                            session_id=session_data["session_id"],
                            start_time=datetime.fromisoformat(session_data["start_time"]),
                            last_activity=datetime.fromisoformat(session_data["last_activity"]),
                            command_count=session_data["command_count"],
                            status=session_data["status"],
                            working_directory=session_data["working_directory"],
                            environment=session_data.get("environment", {}),
                            command_history=session_data.get("command_history", []),
                        )
                        self.active_sessions[session.session_id] = session
            except (KeyError, ValueError, json.JSONDecodeError):
                logger.debug("Suppressed KeyError/ValueError/json", exc_info=True)

    def _save_sessions(self) -> None:
        """Persist terminal sessions to storage."""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "sessions": [session.to_dict() for session in self.active_sessions.values()],
            }
            with open(self.sessions_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            logger.debug("Suppressed FileNotFoundError/OSError/json", exc_info=True)

    def _register_consciousness_hooks(self) -> None:
        """Register with the KILO-FOOLISH consciousness system."""
        try:
            # Enhanced consciousness integration with fallback implementation
            self.consciousness_hooks = {
                "terminal_activity": True,
                "command_tracking": True,
                "output_analysis": True,
                "session_awareness": True,
                "context_memory": True,
            }

            # Try to import and register with consciousness system
            try:
                from src.consciousness.consciousness_core import \
                    ConsciousnessCore

                consciousness = ConsciousnessCore()
                consciousness.register_terminal_manager(self)
                self.consciousness_hooks["active_integration"] = True
            except ImportError:
                # Fallback consciousness simulation
                self._simulate_consciousness_integration()
                self.consciousness_hooks["active_integration"] = False

        except (ImportError, AttributeError, RuntimeError):
            # Minimal hooks for basic functionality
            self.consciousness_hooks = {
                "terminal_activity": False,
                "command_tracking": False,
                "output_analysis": False,
            }

    def _simulate_consciousness_integration(self) -> None:
        """Simulate consciousness integration when actual system unavailable."""
        # Create consciousness simulation data
        self.consciousness_data = {
            "session_memories": {},
            "command_patterns": {},
            "user_preferences": {},
            "context_awareness": True,
        }

        # Simulate consciousness awareness of terminal activity
        def track_consciousness_event(event_type, event_data) -> None:
            if event_type not in self.consciousness_data:
                self.consciousness_data[event_type] = []
            self.consciousness_data[event_type].append(
                {
                    "timestamp": time.time(),
                    "data": event_data,
                }
            )

        self.consciousness_track = track_consciousness_event

    def create_session(self, working_dir: str | None = None) -> str:
        """Create a new terminal session with tracking."""
        session_id = str(uuid.uuid4())
        working_dir = working_dir or str(self.workspace_root)

        session = TerminalSession(
            session_id=session_id,
            start_time=datetime.now(),
            last_activity=datetime.now(),
            command_count=0,
            status="active",
            working_directory=working_dir,
            environment={},
            command_history=[],
        )

        self.active_sessions[session_id] = session
        self._save_sessions()

        return session_id

    def execute_command(
        self,
        command: str,
        session_id: str | None = None,
        capture_output: bool = True,
        timeout: int = 30,
        is_background: bool | None = None,
    ) -> dict[str, Any]:
        """Execute command with robust output capture and session tracking.

        Args:
            command: Command to execute
            session_id: Optional session ID for tracking
            capture_output: Whether to capture and return output
            timeout: Command timeout in seconds (can be overridden by
                TERMINAL_COMMAND_TIMEOUT environment variable)
            is_background: If True, disables output capture for background tasks.

        Returns:
            Dictionary with execution results, output, and metadata. On
            timeout a standardized ``error_payload`` is included for
            Copilot surface.

        """
        if is_background is True:
            capture_output = False
        elif is_background is False:
            capture_output = True

        if not session_id:
            session_id = self.create_session()

        session = self.active_sessions.get(session_id)
        if not session:
            session_id = self.create_session()
            session = self.active_sessions[session_id]

        # Prepare command execution
        start_time = datetime.now()
        execution_data: dict[str, Any] = {
            "command": command,
            "session_id": session_id,
            "start_time": start_time.isoformat(),
            "working_directory": session.working_directory,
            "status": "executing",
            "is_background": not capture_output,
        }

        # Allow environment override
        timeout = int(os.getenv("TERMINAL_COMMAND_TIMEOUT", timeout))

        try:
            # Update session
            session.last_activity = start_time
            session.command_count += 1
            session.command_history.append(execution_data)

            if capture_output:
                # Manual process control for timeout handling
                process: subprocess.Popen[str] = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=session.working_directory,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                    execution_data.update(
                        {
                            "status": "completed",
                            "return_code": process.returncode,
                            "stdout": stdout,
                            "stderr": stderr,
                            "duration": (datetime.now() - start_time).total_seconds(),
                        }
                    )

                    # Cache output for retrieval
                    self._cache_output(session_id, execution_data)

                except subprocess.TimeoutExpired:
                    # Send termination signal and log diagnostics
                    process.send_signal(signal.SIGTERM)
                    logger.warning(f"⏰ Command timeout after {timeout}s: {command}")
                    try:
                        stdout, stderr = process.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        stdout, stderr = process.communicate()
                    except OSError:
                        stdout, stderr = "", ""
                    execution_data.update(
                        {
                            "status": "timeout",
                            "error": f"Command timed out after {timeout} seconds",
                            "stdout": stdout,
                            "stderr": stderr,
                            "duration": (datetime.now() - start_time).total_seconds(),
                            "error_payload": {
                                "type": "timeout",
                                "message": f"Command timed out after {timeout} seconds",
                                "command": command,
                                "timeout": timeout,
                                "stdout": stdout,
                                "stderr": stderr,
                            },
                        }
                    )

                    session.command_history[-1] = execution_data
                    self._save_sessions()
                    return execution_data

            else:
                # Execute without capture (background/daemon)
                process_bg: subprocess.Popen[bytes] = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=session.working_directory,
                )
                execution_data.update(
                    {
                        "status": "background",
                        "process_id": process_bg.pid,
                        "duration": (datetime.now() - start_time).total_seconds(),
                    }
                )

            # Update session history
            session.command_history[-1] = execution_data
            self._save_sessions()

            return execution_data

        except (OSError, subprocess.SubprocessError, TimeoutError) as e:
            execution_data.update(
                {
                    "status": "error",
                    "error": str(e),
                    "duration": (datetime.now() - start_time).total_seconds(),
                    "error_payload": {
                        "type": "exception",
                        "message": str(e),
                        "command": command,
                    },
                }
            )
            session.command_history[-1] = execution_data
            self._save_sessions()
            return execution_data

    def _cache_output(self, session_id: str, execution_data: dict[str, Any]) -> None:
        """Cache command output for later retrieval."""
        try:
            cache_file = self.output_cache / f"{session_id}_{int(time.time())}.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(execution_data, f, indent=2, ensure_ascii=False)
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            logger.debug("Suppressed FileNotFoundError/OSError/json", exc_info=True)

    def get_session_output(self, session_id: str, command_index: int = -1) -> dict[str, Any] | None:
        """Get output from a specific command in a session."""
        session = self.active_sessions.get(session_id)
        if not session or not session.command_history:
            return None

        try:
            return session.command_history[command_index]
        except IndexError:
            return None

    def get_latest_output(self, max_commands: int = 5) -> list[dict[str, Any]]:
        """Get the latest command outputs across all sessions."""
        all_commands: list[Any] = []
        for session in self.active_sessions.values():
            for cmd in session.command_history[-max_commands:]:
                cmd["session_info"] = {
                    "session_id": session.session_id[:8] + "...",
                    "working_directory": session.working_directory,
                }
                all_commands.append(cmd)

        # Sort by execution time
        all_commands.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        return all_commands[:max_commands]

    def get_session_summary(self) -> dict[str, Any]:
        """Get summary of all terminal sessions."""
        now = datetime.now()

        summary: dict[str, Any] = {
            "total_sessions": len(self.active_sessions),
            "active_sessions": len(
                [s for s in self.active_sessions.values() if s.status == "active"]
            ),
            "total_commands": sum(s.command_count for s in self.active_sessions.values()),
            "last_activity": (
                max([s.last_activity for s in self.active_sessions.values()])
                if self.active_sessions
                else None
            ),
            "sessions": [],
        }

        for session in self.active_sessions.values():
            session_info = {
                "session_id": session.session_id[:8] + "...",
                "status": session.status,
                "command_count": session.command_count,
                "working_directory": session.working_directory,
                "last_activity": session.last_activity.isoformat(),
                "duration_minutes": (now - session.start_time).total_seconds() / 60,
            }
            summary["sessions"].append(session_info)

        return summary

    def cleanup_old_sessions(self, hours_old: int = 24) -> None:
        """Clean up old inactive sessions."""
        cutoff = datetime.now() - timedelta(hours=hours_old)
        old_sessions = [
            sid
            for sid, session in self.active_sessions.items()
            if session.last_activity < cutoff and session.status != "active"
        ]

        for session_id in old_sessions:
            del self.active_sessions[session_id]

        if old_sessions:
            self._save_sessions()

        return len(old_sessions)


def create_enhanced_terminal_manager():
    """Factory function for creating enhanced terminal manager."""
    return EnhancedTerminalManager()


# Backwards-compatible public API: some modules/tests import `TerminalManager`
# so expose the expected name as an alias to the implemented class.
TerminalManager = EnhancedTerminalManager


# Quantum-consciousness integration hook
def register_with_ai_coordinator() -> bool | None:
    """Register terminal manager with AI Coordinator for system-wide integration."""
    try:
        # Enhanced AI Coordinator integration with comprehensive fallback

        # Try to import and connect with actual AI Coordinator
        try:
            from src.core.ai_coordinator import AICoordinator

            coordinator = AICoordinator()

            # Register terminal manager as a service
            registration_data = {
                "service_name": "terminal_manager",
                "capabilities": [
                    "command_execution",
                    "session_management",
                    "output_caching",
                    "consciousness_hooks",
                    "quantum_integration",
                ],
                "status": "active",
                "priority": "high",
            }

            success = coordinator.register_service("terminal_manager", registration_data)
            return bool(success)

        except ImportError:
            # Fallback AI coordination simulation

            # Create AI coordination simulation
            ai_coordination_data = {
                "registration_status": "simulated",
                "coordination_level": "basic",
                "available_functions": [
                    "execute_command",
                    "get_session_info",
                    "cache_output",
                    "track_performance",
                ],
                "integration_features": {
                    "command_routing": True,
                    "result_caching": True,
                    "performance_monitoring": True,
                    "consciousness_bridge": True,
                },
            }

            # Store coordination data globally for other systems to access
            globals()["_terminal_ai_coordination"] = ai_coordination_data

            return True

    except (ImportError, RuntimeError, AttributeError):
        return False


if __name__ == "__main__":
    # Test the enhanced terminal manager

    manager = create_enhanced_terminal_manager()

    # Test session creation
    demo_session_id = manager.create_session()

    # Test command execution
    demo_result = manager.execute_command(
        "echo 'Hello KILO-FOOLISH Terminal Manager!'", demo_session_id
    )

    # Test output retrieval
    latest_output = manager.get_latest_output(1)

    # Test session summary
    demo_summary = manager.get_session_summary()
