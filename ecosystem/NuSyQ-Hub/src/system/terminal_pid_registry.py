"""Terminal PID Registry — maps live VS Code terminal PIDs to agent roles.

Each live terminal is a PowerShell watcher process. This registry:
  - Discovers all live pwsh.exe PIDs via psutil
  - Assigns each to a terminal role (claude, copilot, errors, tasks, ...)
  - Persists the mapping to state/terminal_pid_registry.json
  - Provides broadcast helpers that write NDJSON to the correct log file
    so the PowerShell watcher in that terminal displays it live in color

Agents call: get_registry().write(agent_name, message, level="INFO")
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REGISTRY_PATH = _REPO_ROOT / "state" / "terminal_pid_registry.json"
_LOG_DIR = _REPO_ROOT / "data" / "terminal_logs"
_WATCHER_DIR = _REPO_ROOT / "data" / "terminal_watchers"


def _normalize_runtime_path(raw_path: str | Path) -> Path:
    """Normalize persisted Windows paths when accessed from WSL/POSIX runtimes."""
    path_str = str(raw_path)
    if os.name != "nt" and len(path_str) >= 3 and path_str[1:3] == ":\\":
        drive = path_str[0].lower()
        suffix = path_str[3:].replace("\\", "/")
        return Path(f"/mnt/{drive}/{suffix}")
    return Path(path_str)


# Ordered list of terminal roles.  The i-th PID (sorted by creation time)
# is assigned to the i-th role when auto-assigning.
TERMINAL_ROLES: list[str] = [
    "claude",
    "copilot",
    "codex",
    "chatdev",
    "ollama",
    "lmstudio",
    "ai_council",
    "intermediary",
    "culture_ship",
    "errors",
    "tasks",
    "tests",
    "metrics",
    "suggestions",
    "anomalies",
    "future",
    "agents",
    "zeta",
    "main",
    "simulatedverse",
    "system",
    "moderator",
    "chatgpt_bridge",
]

# Map agent / system names to their primary terminal role
AGENT_TO_ROLE: dict[str, str] = {
    # Core agents
    "claude": "claude",
    "claude_cli": "claude",
    "copilot": "copilot",
    "codex": "codex",
    "chatdev": "chatdev",
    "ollama": "ollama",
    "lmstudio": "lmstudio",
    "lm_studio": "lmstudio",
    "ai_council": "ai_council",
    "council": "ai_council",
    "intermediary": "intermediary",
    "culture_ship": "culture_ship",
    "consciousness": "simulatedverse",
    "simulatedverse": "simulatedverse",
    "quantum_resolver": "agents",
    "neural_ml": "agents",
    "factory": "agents",
    "openclaw": "agents",
    "skyclaw": "agents",
    "metaclaw": "agents",
    "hermes": "agents",
    "hermes_agent": "agents",
    "huggingface": "agents",
    "dbclient": "agents",
    "devtool": "agents",
    "gitkraken": "agents",
    "shepherd": "simulatedverse",
    # System channels
    "errors": "errors",
    "tasks": "tasks",
    "tests": "tests",
    "metrics": "metrics",
    "suggestions": "suggestions",
    "anomalies": "anomalies",
    "future": "future",
    "zeta": "zeta",
    "main": "main",
    "system": "system",
}


@dataclass
class TerminalEntry:
    """A single registered terminal."""

    pid: int
    role: str
    label: str
    log_file: str
    watcher_script: str
    status: str = "active"  # active | dead | unassigned
    assigned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_write: str | None = None
    write_count: int = 0

    def log_path(self) -> Path:
        return _normalize_runtime_path(self.log_file)

    def watcher_path(self) -> Path:
        return _normalize_runtime_path(self.watcher_script)

    def startup_command(self) -> str:
        """PowerShell command to start watching this terminal's log file."""
        script = self.watcher_path()
        if script.exists():
            return f"& '{script}'"
        # Fallback: simple tail
        return f"Get-Content -Wait -Tail 20 '{self.log_path()}'"


class TerminalPIDRegistry:
    """Live registry of VS Code terminal PIDs and their agent roles.

    Usage::

        reg = get_registry()
        reg.write("claude", "Analyzing codebase...", level="INFO")
        reg.broadcast("Task queue: 42 pending", level="INFO")
        print(reg.status_table())
    """

    def __init__(self, registry_path: Path = _REGISTRY_PATH) -> None:
        self._path = registry_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.entries: dict[str, TerminalEntry] = {}  # role → entry
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            for role, raw in data.get("entries", {}).items():
                self.entries[role] = TerminalEntry(**raw)
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

    def _save(self) -> None:
        payload = {
            "updated": datetime.now().isoformat(),
            "entries": {role: asdict(e) for role, e in self.entries.items()},
        }
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover_live_pids(self) -> list[tuple[int, str]]:
        """Return [(pid, name)] for all live pwsh.exe processes, sorted by create_time."""
        try:
            import psutil
        except ImportError:
            logger.warning("psutil not installed — cannot auto-discover terminal PIDs")
            return []

        results: list[tuple[int, float, str]] = []
        for proc in psutil.process_iter(["pid", "name", "create_time"]):
            try:
                if proc.info["name"] and "pwsh" in proc.info["name"].lower():
                    results.append((proc.info["pid"], proc.info["create_time"], proc.info["name"]))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        results.sort(key=lambda x: x[1])  # oldest first
        return [(pid, name) for pid, _, name in results]

    def auto_assign(self, pids: list[int] | None = None) -> dict[str, TerminalEntry]:
        """Assign terminal roles to live PIDs.

        If *pids* is given, use that list (in order); otherwise auto-discover.
        Roles are assigned positionally from TERMINAL_ROLES.
        Returns the updated entries dict.
        """
        if pids is None:
            live = self.discover_live_pids()
            pids = [p for p, _ in live]

        for i, pid in enumerate(pids):
            role = TERMINAL_ROLES[i] if i < len(TERMINAL_ROLES) else f"terminal_{i}"
            log_file = str(_LOG_DIR / f"{role}.log")
            watcher_script = str(_WATCHER_DIR / f"watch_{role}_terminal.ps1")
            entry = TerminalEntry(
                pid=pid,
                role=role,
                label=f"{role.replace('_', ' ').title()} Terminal",
                log_file=log_file,
                watcher_script=watcher_script,
            )
            self.entries[role] = entry

        # Check which PIDs are still alive
        self._refresh_status()
        self._save()
        return self.entries

    def assign_pid(self, pid: int, role: str) -> TerminalEntry:
        """Manually assign a specific PID to a role."""
        log_file = str(_LOG_DIR / f"{role}.log")
        watcher_script = str(_WATCHER_DIR / f"watch_{role}_terminal.ps1")
        entry = TerminalEntry(
            pid=pid,
            role=role,
            label=f"{role.replace('_', ' ').title()} Terminal",
            log_file=log_file,
            watcher_script=watcher_script,
        )
        self.entries[role] = entry
        self._save()
        return entry

    def _refresh_status(self) -> None:
        """Mark dead PIDs as such."""
        try:
            import psutil

            for entry in self.entries.values():
                try:
                    proc = psutil.Process(entry.pid)
                    entry.status = "active" if proc.is_running() else "dead"
                except psutil.NoSuchProcess:
                    entry.status = "dead"
        except ImportError:
            pass

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def write(
        self,
        agent_or_role: str,
        message: str,
        level: str = "INFO",
        source: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        """Write a message to the log file watched by *agent_or_role*'s terminal.

        The message is written as NDJSON so the PowerShell watcher displays
        it in color.  Returns True if a matching entry was found and written.
        """
        role = AGENT_TO_ROLE.get(agent_or_role.lower(), agent_or_role.lower())
        entry = self.entries.get(role)
        if entry is None:
            # Fall through to main if unmapped
            entry = self.entries.get("main")
        if entry is None:
            # Write directly to log dir without a registered terminal
            self._write_to_log(
                _LOG_DIR / f"{role}.log", message, level, source or agent_or_role, extra
            )
            return False

        self._write_to_log(entry.log_path(), message, level, source or agent_or_role, extra)
        entry.last_write = datetime.now().isoformat()
        entry.write_count += 1
        return True

    @staticmethod
    def _write_to_log(
        log_path: Path,
        message: str,
        level: str,
        source: str,
        extra: dict[str, Any] | None,
    ) -> None:
        """Append a single NDJSON line to *log_path*."""
        log_path.parent.mkdir(parents=True, exist_ok=True)
        record: dict[str, Any] = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "level": level.upper(),
            "source": source,
            "message": message,
        }
        if extra:
            record.update(extra)
        try:
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except OSError as exc:
            logger.debug("terminal_pid_registry write failed: %s", exc)

    def broadcast(
        self,
        message: str,
        level: str = "INFO",
        source: str = "system",
        roles: list[str] | None = None,
    ) -> int:
        """Write *message* to multiple terminals.  Returns count written."""
        targets = roles or ["main", "agents", "system"]
        written = 0
        for role in targets:
            entry = self.entries.get(role)
            if entry:
                self._write_to_log(entry.log_path(), message, level, source, None)
                written += 1
            else:
                self._write_to_log(_LOG_DIR / f"{role}.log", message, level, source, None)
                written += 1
        return written

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_entry(self, agent_or_role: str) -> TerminalEntry | None:
        role = AGENT_TO_ROLE.get(agent_or_role.lower(), agent_or_role.lower())
        return self.entries.get(role)

    def get_channel_map(self) -> dict[str, dict[str, Any]]:
        """Return agent → {pid, log_file, status} for all known agents."""
        result: dict[str, dict[str, Any]] = {}
        for agent, role in AGENT_TO_ROLE.items():
            entry = self.entries.get(role)
            result[agent] = {
                "role": role,
                "pid": entry.pid if entry else None,
                "log_file": str(_LOG_DIR / f"{role}.log"),
                "status": entry.status if entry else "unregistered",
                "write_count": entry.write_count if entry else 0,
            }
        return result

    def status_table(self) -> str:
        """Pretty-print table of all registered terminals."""
        self._refresh_status()
        lines = [
            f"{'ROLE':<22} {'PID':>7}  {'STATUS':<12} {'WRITES':>7}  LOG FILE",
            "-" * 80,
        ]
        for role in TERMINAL_ROLES:
            entry = self.entries.get(role)
            if entry:
                log = Path(entry.log_file).name
                lines.append(
                    f"{role:<22} {entry.pid:>7}  {entry.status:<12} {entry.write_count:>7}  {log}"
                )
            else:
                lines.append(f"{role:<22} {'—':>7}  {'unassigned':<12} {'—':>7}")
        return "\n".join(lines)

    def get_startup_commands(self) -> dict[str, str]:
        """Return {role: powershell_command} for launching each watcher."""
        return {role: entry.startup_command() for role, entry in self.entries.items()}

    def emit_awareness_event(self) -> None:
        """Broadcast the current terminal map to the guild board (fire-and-forget)."""
        try:
            import asyncio

            from src.guild.guild_board import get_board  # type: ignore[import]

            async def _emit() -> None:
                board = await get_board()
                await board._emit_event(  # type: ignore[attr-defined]
                    "terminal_registry_updated",
                    {
                        "active_terminals": sum(
                            1 for e in self.entries.values() if e.status == "active"
                        ),
                        "roles": list(self.entries.keys()),
                    },
                )

            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = loop.create_task(_emit())
                task.add_done_callback(lambda _: None)
            else:
                loop.run_until_complete(_emit())
        except Exception:
            pass  # Awareness emission is best-effort


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_registry: TerminalPIDRegistry | None = None


def get_registry() -> TerminalPIDRegistry:
    """Get (or create) the global terminal PID registry."""
    global _registry
    if _registry is None:
        _registry = TerminalPIDRegistry()
    return _registry
