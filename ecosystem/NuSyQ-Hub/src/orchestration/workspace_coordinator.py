"""Unified Workspace Coordinator - Tri-Partite System Orchestration.

Modernized architecture for coordinating NuSyQ-Hub, SimulatedVerse, and NuSyQ
repositories in a VS Code multi-root workspace. Designed to work WITH Copilot's
capabilities rather than against them.

Architecture Principles:
1. File-based state (no in-memory assumptions)
2. Health-first design (observable, measurable, actionable)
3. Event-driven coordination (repos communicate via standard events)
4. Self-healing where possible
5. VS Code task integration
"""

import asyncio
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)


class RepoStatus(Enum):
    """Repository health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class ServiceType(Enum):
    """Service types in the ecosystem."""

    MCP_SERVER = "mcp_server"  # NuSyQ MCP server
    SIMVERSE_DEV = "simverse_dev"  # SimulatedVerse dev server
    OLLAMA = "ollama"  # Ollama model service
    CHATDEV = "chatdev"  # ChatDev multi-agent


@dataclass
class RepoHealth:
    """Health snapshot for a repository."""

    name: str
    path: Path
    status: RepoStatus
    timestamp: datetime
    errors: int
    warnings: int
    services: dict[str, bool]  # service_name -> is_running
    last_check: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Implement __post_init__."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WorkspaceState:
    """Complete workspace state snapshot."""

    timestamp: datetime
    repos: dict[str, RepoHealth]
    overall_status: RepoStatus
    active_services: list[str]
    recent_errors: list[str]
    coordinator_version: str = "1.0.0"


class WorkspaceCoordinator:
    """Coordinates the tri-partite workspace ecosystem.

    Design Philosophy:
    - Each repo is autonomous (can function independently)
    - Coordination is optional enhancement (not requirement)
    - State is file-based and observable
    - Health checks are lightweight and fast
    - Recovery is automated where safe
    """

    def __init__(
        self,
        hub_root: Path,
        simverse_root: Path | None = None,
        nusyq_root: Path | None = None,
    ):
        """Initialize WorkspaceCoordinator with hub_root, simverse_root, nusyq_root."""
        self.hub_root = Path(hub_root)
        self.service_config = self._load_service_config()

        self.simverse_root = Path(simverse_root) if simverse_root else self._find_simverse()
        self.nusyq_root = Path(nusyq_root) if nusyq_root else self._find_nusyq()

        self.state_file = self.hub_root / "state" / "workspace_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Simple task registry for scheduled and ad-hoc actions
        self.tasks: dict[str, dict[str, Any]] = {}
        self._setup_culture_ship_tasks()

    def run_task(self, name: str) -> dict[str, Any]:
        """Run a registered task by name.

        Evaluates optional condition, executes the command and returns a result dict.
        """
        task = self.tasks.get(name)
        if not task:
            return {"success": False, "status": "error", "error": f"task '{name}' not found"}

        # Condition gate
        cond = task.get("condition")
        try:
            if callable(cond) and not cond():
                return {"success": False, "status": "skipped", "reason": "condition_false"}
        except Exception as exc:
            # If condition evaluation fails, default to run to avoid silent misses
            logger.warning("Condition for task %s failed: %s", name, exc)

        # Build command
        cmd: list[str] = []
        cmd_str = task.get("command")
        if isinstance(cmd_str, str):
            # Execute via repository Python to ensure correct environment
            py = sys.executable if hasattr(sys, "executable") else "python"
            cmd = [py, str(self.hub_root / "scripts" / "start_nusyq.py")]
            cmd.extend(cmd_str.split())

        # Fallback to explicit args array if provided
        if not cmd and isinstance(task.get("args"), list):
            cmd = task["args"]

        # Execute
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.hub_root),
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            result = {
                "success": proc.returncode == 0,
                "status": "success" if proc.returncode == 0 else "failed",
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }

            # Write receipt if configured
            out_tpl = task.get("output")
            if out_tpl:
                try:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    rel = out_tpl.replace("{timestamp}", ts)
                    path = self.hub_root / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    payload = {
                        "task": name,
                        "command": cmd_str,
                        "timestamp": datetime.now().isoformat(),
                        "result": {k: v for k, v in result.items() if k != "stdout"},
                    }
                    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                except Exception as exc:
                    logger.warning("Failed to write task receipt for %s: %s", name, exc)

            return result
        except Exception as exc:
            return {"success": False, "status": "error", "error": str(exc)}

    def _has_culture_ship_fixes(self) -> bool:
        """Check the latest audit receipt for fixable issues."""
        receipts_dir = self.hub_root / "state" / "receipts" / "culture-ship"
        if not receipts_dir.exists():
            return False

        candidates = sorted(receipts_dir.glob("audit_*.json"))
        if not candidates:
            return False

        try:
            latest = json.loads(candidates[-1].read_text(encoding="utf-8"))
            return (latest.get("analysis", {}).get("fixable_issues", 0) or 0) > 0
        except Exception:
            return False

    def _repo_has_changes(self, rel_path: str, since: str = "6h") -> bool:
        """Return True if repository has changes in rel_path within the timeframe."""
        try:
            proc = subprocess.run(
                [
                    "git",
                    "log",
                    f"--since={since}",
                    "--oneline",
                    "--",
                    rel_path,
                ],
                cwd=str(self.hub_root),
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return bool(proc.stdout.strip())
        except Exception:
            # If git is unavailable, do not block automation
            return True

    def _setup_culture_ship_tasks(self) -> None:
        """Register Culture Ship recurring tasks in the coordinator."""
        self.tasks.update(
            {
                "culture_ship_health_audit": {
                    "schedule": "*/30 * * * *",  # Every 30 minutes
                    "args": [
                        "python",
                        str(self.hub_root / "src" / "culture_ship" / "health_probe.py"),
                    ],
                    "condition": getattr(self, "_is_work_hours", lambda: True),
                    "output": "state/receipts/culture-ship/health_{timestamp}.json",
                    "notify_on": ["failure", "degraded"],
                },
                "culture_ship_dry_run_audit": {
                    "schedule": "0 */3 * * *",  # Every 3 hours
                    "args": [
                        "python",
                        str(self.hub_root / "src" / "culture_ship_real_action.py"),
                        "--dry-run",
                        "--targets",
                        "src/",
                    ],
                    "condition": lambda: self._repo_has_changes("src/", "6h"),
                    "output": "state/receipts/culture-ship/audit_{timestamp}.json",
                    "notify_on": ["fixes_available"],
                },
                "culture_ship_apply_fixes": {
                    "schedule": "0 2 * * *",  # Daily at 2 AM
                    "args": [
                        "python",
                        str(self.hub_root / "src" / "culture_ship_real_action.py"),
                        "--apply",
                        "--targets",
                        "src/",
                    ],
                    "condition": self._has_culture_ship_fixes,
                    "requires": ["culture_ship_dry_run_audit"],
                    "output": "state/receipts/culture-ship/fixes_{timestamp}.json",
                    "notify_on": ["success", "failure"],
                },
            }
        )

    def _find_simverse(self) -> Path | None:
        """Auto-discover SimulatedVerse repository."""
        cfg_path = self.service_config.get("paths", {}).get("simulatedverse")
        candidates = [
            Path(cfg_path) if cfg_path else None,
            Path("C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"),
            self.hub_root.parent / "SimulatedVerse" / "SimulatedVerse",
        ]
        for path in candidates:
            if path and path.exists() and (path / "package.json").exists():
                return path
        return None

    def _find_nusyq(self) -> Path | None:
        """Auto-discover NuSyQ repository."""
        cfg_path = self.service_config.get("paths", {}).get("nusyq")
        candidates = [
            Path(cfg_path) if cfg_path else None,
            Path("C:/Users/keath/NuSyQ"),
            self.hub_root.parent / "NuSyQ",
        ]
        for path in candidates:
            if path and path.exists() and (path / "mcp_server").exists():
                return path
        return None

    def _load_service_config(self) -> dict[str, Any]:
        """Load shared service configuration if present."""
        cfg_path = self.hub_root / "config" / "service_config.json"
        if cfg_path.exists():
            try:
                with open(cfg_path, encoding="utf-8") as handle:
                    return cast(dict[str, Any], json.load(handle))
            except (json.JSONDecodeError, ValueError, OSError) as exc:
                logger.warning("Failed to load service_config.json: %s", exc)
        return {}

    async def check_repo_health(self, repo_name: str, repo_path: Path) -> RepoHealth:
        """Check health of a single repository.

        Fast, non-invasive checks:
        - Directory exists
        - Key files present
        - Recent error logs
        - Service processes (if applicable)
        """
        if not repo_path or not repo_path.exists():
            return RepoHealth(
                name=repo_name,
                path=repo_path,
                status=RepoStatus.OFFLINE,
                timestamp=datetime.now(),
                errors=0,
                warnings=0,
                services={},
                metadata={"reason": "path_not_found"},
            )

        services = {}
        errors = 0
        warnings = 0
        metadata = {}

        # Repository-specific checks
        if repo_name == "NuSyQ-Hub":
            # Check Python environment
            src_dir = repo_path / "src"
            metadata["has_src"] = src_dir.exists()

            # Quick error scan (just count, don't read all)
            try:
                result = subprocess.run(
                    [
                        "python",
                        "-m",
                        "ruff",
                        "check",
                        "src",
                        "--select",
                        "E9,F63,F7,F82",
                        "--quiet",
                    ],
                    cwd=repo_path,
                    capture_output=True,
                    timeout=5,
                )
                errors = result.stdout.decode().count("\n") if result.stdout else 0
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)

        elif repo_name == "SimulatedVerse":
            # Check Node.js project
            package_json = repo_path / "package.json"
            metadata["has_package_json"] = package_json.exists()

            # Check if dev server is running (port 5002)
            dev_cfg = self.service_config.get("services", {}).get("simverse_dev", {})
            services["dev_server"] = await self._check_port(
                dev_cfg.get("port", 5002), dev_cfg.get("host", "localhost")
            )

        elif repo_name == "NuSyQ":
            # Check MCP server
            mcp_cfg = self.service_config.get("services", {}).get("mcp_server", {})
            services["mcp_server"] = await self._check_port(
                mcp_cfg.get("port", 3000), mcp_cfg.get("host", "localhost")
            )

            # Check Ollama
            ollama_cfg = self.service_config.get("services", {}).get("ollama", {})
            services["ollama"] = await self._check_port(
                ollama_cfg.get("port", 11434), ollama_cfg.get("host", "localhost")
            )

            # Check for Ollama models
            try:
                result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    timeout=3,
                )
                metadata["ollama_models"] = result.returncode == 0
            except Exception:
                metadata["ollama_models"] = False

        # Determine overall status
        if errors > 10:
            status = RepoStatus.DEGRADED
        elif any(services.values()) or metadata.get("has_src") or metadata.get("has_package_json"):
            status = RepoStatus.HEALTHY
        else:
            status = RepoStatus.UNKNOWN

        return RepoHealth(
            name=repo_name,
            path=repo_path,
            status=status,
            timestamp=datetime.now(),
            errors=errors,
            warnings=warnings,
            services=services,
            metadata=metadata,
        )

    async def _check_port(self, port: int, host: str = "localhost") -> bool:
        """Quick port check without full HTTP request."""
        try:
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=1.0
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def snapshot(self) -> WorkspaceState:
        """Capture current workspace state across all repos."""
        repos = {}

        # Check each repository
        if self.hub_root:
            repos["NuSyQ-Hub"] = await self.check_repo_health("NuSyQ-Hub", self.hub_root)

        if self.simverse_root:
            repos["SimulatedVerse"] = await self.check_repo_health(
                "SimulatedVerse", self.simverse_root
            )

        if self.nusyq_root:
            repos["NuSyQ"] = await self.check_repo_health("NuSyQ", self.nusyq_root)

        # Determine overall status
        statuses = [r.status for r in repos.values()]
        if RepoStatus.OFFLINE in statuses or RepoStatus.DEGRADED in statuses:
            overall = RepoStatus.DEGRADED
        elif RepoStatus.HEALTHY in statuses:
            overall = RepoStatus.HEALTHY
        else:
            overall = RepoStatus.UNKNOWN

        # Collect active services
        active_services = []
        for repo in repos.values():
            for service, running in repo.services.items():
                if running:
                    active_services.append(f"{repo.name}:{service}")

        # Collect recent errors
        recent_errors = []
        for repo in repos.values():
            if repo.errors > 0:
                recent_errors.append(f"{repo.name}: {repo.errors} errors")

        state = WorkspaceState(
            timestamp=datetime.now(),
            repos=repos,
            overall_status=overall,
            active_services=active_services,
            recent_errors=recent_errors,
        )

        # Persist to file
        self._save_state(state)

        try:
            from src.system.agent_awareness import emit as _emit

            _level = "WARNING" if overall == RepoStatus.DEGRADED else "INFO"
            _emit(
                "system",
                f"Workspace snapshot: {overall.value} | repos={len(repos)}"
                f" services={len(active_services)} errors={len(recent_errors)}",
                level=_level,
                source="workspace_coordinator",
            )
        except Exception:
            pass

        return state

    def _save_state(self, state: WorkspaceState) -> None:
        """Save state to disk for Copilot visibility."""
        state_dict = {
            "timestamp": state.timestamp.isoformat(),
            "overall_status": state.overall_status.value,
            "active_services": state.active_services,
            "recent_errors": state.recent_errors,
            "coordinator_version": state.coordinator_version,
            "repos": {
                name: {
                    "name": repo.name,
                    "path": str(repo.path),
                    "status": repo.status.value,
                    "timestamp": repo.timestamp.isoformat(),
                    "errors": repo.errors,
                    "warnings": repo.warnings,
                    "services": repo.services,
                    "metadata": repo.metadata,
                }
                for name, repo in state.repos.items()
            },
        }

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)

    def load_state(self) -> WorkspaceState | None:
        """Load last known state from disk."""
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file, encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct state (simplified - full deserialization would be more complex)
            return cast("WorkspaceState | None", data)
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.warning(f"Failed to load workspace state: {e}")
            return None

    async def diagnose_mcp_failure(self) -> dict[str, Any]:
        """Diagnose why MCP server is failing.

        Common issues:
        1. Port already in use
        2. Python environment issues
        3. Missing dependencies
        4. Configuration errors
        """
        diagnostics: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "issues": [],
            "recommendations": [],
        }

        if not self.nusyq_root:
            diagnostics["issues"].append("NuSyQ repository not found")
            return diagnostics

        mcp_main = self.nusyq_root / "mcp_server" / "main.py"
        if not mcp_main.exists():
            diagnostics["issues"].append(f"MCP server main.py not found at {mcp_main}")
            return diagnostics

        # Check port 3000
        port_in_use = await self._check_port(3000)
        if port_in_use:
            diagnostics["issues"].append("Port 3000 already in use")
            diagnostics["recommendations"].append("Kill process on port 3000 or change MCP port")

        # Check Python environment
        venv_python = self.nusyq_root / ".venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            diagnostics["issues"].append("Virtual environment not found")
            diagnostics["recommendations"].append("Create virtual environment in NuSyQ/.venv")

        # Check for error logs
        log_file = self.nusyq_root / "mcp_server_runtime.err"
        if log_file.exists():
            try:
                with open(log_file, encoding="utf-8") as f:
                    last_errors = f.readlines()[-10:]  # Last 10 lines
                diagnostics["last_errors"] = [line.strip() for line in last_errors]
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)

        return diagnostics

    async def auto_heal(self) -> dict[str, Any]:
        """Attempt automatic healing of known issues.

        Safe, non-destructive recovery actions:
        1. Restart failed services
        2. Clear port locks
        3. Rebuild configuration
        """
        actions: list[dict[str, Any]] = []

        # Check MCP server
        if self.nusyq_root:
            mcp_running = await self._check_port(3000)
            if not mcp_running:
                diagnostics = await self.diagnose_mcp_failure()
                if "Port 3000 already in use" in diagnostics.get("issues", []):
                    # Don't auto-restart if port occupied by something else
                    actions.append(
                        {
                            "service": "mcp_server",
                            "action": "skip",
                            "reason": "port_occupied",
                        }
                    )
                else:
                    # Could auto-restart here, but safer to report
                    actions.append(
                        {
                            "service": "mcp_server",
                            "action": "diagnose_only",
                            "diagnostics": diagnostics,
                        }
                    )

        return {"actions": actions}

    def generate_copilot_summary(self, state: WorkspaceState) -> str:
        """Generate human-readable summary for Copilot context."""
        lines = [
            "# Workspace State Snapshot",
            f"**Timestamp:** {state.timestamp.isoformat()}",
            f"**Overall Status:** {state.overall_status.value.upper()}",
            "",
            "## Repositories",
        ]

        for name, repo in state.repos.items():
            lines.append(f"### {name}")
            lines.append(f"- **Status:** {repo.status.value}")
            lines.append(f"- **Path:** {repo.path}")
            lines.append(f"- **Errors:** {repo.errors}")

            if repo.services:
                lines.append("- **Services:**")
                for svc, running in repo.services.items():
                    status_icon = "✅" if running else "❌"
                    lines.append(f"  - {status_icon} {svc}")

            if repo.metadata:
                lines.append("- **Metadata:**")
                for key, val in repo.metadata.items():
                    lines.append(f"  - {key}: {val}")
            lines.append("")

        if state.active_services:
            lines.append("## Active Services")
            for svc in state.active_services:
                lines.append(f"- {svc}")
            lines.append("")

        if state.recent_errors:
            lines.append("## Recent Errors")
            for err in state.recent_errors:
                lines.append(f"- {err}")
            lines.append("")

        return "\n".join(lines)


async def main():
    """CLI entry point for workspace coordination."""
    import sys

    coordinator = WorkspaceCoordinator(hub_root=Path(__file__).resolve().parents[2])

    if len(sys.argv) > 1 and sys.argv[1] == "diagnose-mcp":
        diagnostics = await coordinator.diagnose_mcp_failure()
        logger.info(json.dumps(diagnostics, indent=2))
        return

    if len(sys.argv) > 1 and sys.argv[1] == "heal":
        result = await coordinator.auto_heal()
        logger.info(json.dumps(result, indent=2))
        return

    # Default: snapshot
    state = await coordinator.snapshot()
    summary = coordinator.generate_copilot_summary(state)
    logger.info(summary)


if __name__ == "__main__":
    asyncio.run(main())
