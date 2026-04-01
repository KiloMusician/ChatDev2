"""Agent availability registry for MJOLNIR Protocol.

Probes each agent to determine real-time availability before dispatch.
Uses lightweight health checks: HTTP pings, CLI lookups, import checks.
"""

from __future__ import annotations

import asyncio  # required for monkeypatch.setattr(agent_registry.asyncio, ...) in tests
import importlib
import importlib.util
import json
import logging
import os
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent availability states."""

    ONLINE = "online"  # Responding and ready
    OFFLINE = "offline"  # Not reachable
    DEGRADED = "degraded"  # Reachable but not fully functional
    UNKNOWN = "unknown"  # Probe skipped or not yet run

    def __str__(self) -> str:
        """Return string representation."""
        return self.value


@dataclass
class AgentProbeResult:
    """Result of probing a single agent's availability."""

    agent: str
    status: AgentStatus
    latency_ms: float | None = None
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON output."""
        d: dict[str, Any] = {
            "agent": self.agent,
            "status": str(self.status),
        }
        if self.latency_ms is not None:
            d["latency_ms"] = round(self.latency_ms, 1)
        if self.detail:
            d["detail"] = self.detail
        if self.metadata:
            d["metadata"] = self.metadata
        return d


# ── Agent probe definitions ──────────────────────────────────────────────────


def _probe_http(url: str, timeout: float = 3.0) -> tuple[AgentStatus, str, dict[str, Any]]:
    """Probe an HTTP endpoint. Returns (status, detail, metadata)."""
    start = time.monotonic()
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=timeout) as resp:
            elapsed = (time.monotonic() - start) * 1000
            body = resp.read(4096).decode("utf-8", errors="replace")
            meta: dict[str, Any] = {"url": url, "http_status": resp.status}
            try:
                meta["response"] = json.loads(body)
            except (ValueError, json.JSONDecodeError):
                meta["response_text"] = body[:200]
            return AgentStatus.ONLINE, f"HTTP {resp.status} in {elapsed:.0f}ms", meta
    except (URLError, OSError, TimeoutError) as exc:
        return AgentStatus.OFFLINE, str(exc)[:120], {"url": url}


def _probe_cli(command: str) -> tuple[AgentStatus, str, dict[str, Any]]:
    """Check if a CLI tool is available via shutil.which."""
    path = shutil.which(command)
    if path:
        return AgentStatus.ONLINE, f"Found at {path}", {"path": path}
    return AgentStatus.OFFLINE, f"{command} not found in PATH", {}


def _probe_env_var(var_name: str) -> tuple[AgentStatus, str, dict[str, Any]]:
    """Check if an environment variable is set (non-empty)."""
    val = os.environ.get(var_name, "")
    if val:
        return AgentStatus.ONLINE, f"{var_name} is set", {"env_var": var_name}
    return AgentStatus.OFFLINE, f"{var_name} not set", {"env_var": var_name}


def _run_probe_command(command: list[str], timeout: float = 5.0) -> tuple[int, str]:
    """Execute a small CLI probe command and return (exit_code, combined_output)."""
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        combined = "\n".join(
            part for part in [getattr(exc, "stdout", None), getattr(exc, "stderr", None)] if part
        ).strip()
        return 124, combined or "probe timeout"
    except OSError as exc:
        return 127, str(exc)

    combined_output = "\n".join(
        part for part in [completed.stdout, completed.stderr] if part
    ).strip()
    return completed.returncode, combined_output


_CLAUDE_AUTH_FAILURE_MARKERS = (
    "oauth token has expired",
    "not logged in",
    "please run /login",
    "invalid api key",
    "failed to authenticate",
)

_CLAUDE_PLACEHOLDER_KEYS = {
    "<your_key_here>",
    "your_key_here",
    "your-claude-key-here",
    "sk-ant-your-anthropic-key-here",
}


def _probe_claude_cli() -> tuple[AgentStatus, str, dict[str, Any]]:
    """Probe Claude CLI availability and basic auth health.

    Uses a lightweight probe by default to avoid blocking startup flows.
    Set ``NUSYQ_STRICT_CLAUDE_AUTH_PROBE=1`` to force auth-status checks.
    """
    custom_cmd = os.getenv("NUSYQ_CLAUDE_CLI_COMMAND", "").strip()
    strict_auth_probe = os.getenv("NUSYQ_STRICT_CLAUDE_AUTH_PROBE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    candidate_commands: list[str] = []
    if custom_cmd:
        parsed = shlex.split(custom_cmd)
        if parsed:
            candidate_commands.append(parsed[0])
    candidate_commands.extend(["claude.cmd", "claude"])

    # Check VS Code Claude Code extension paths (cross-platform)
    vscode_ext_dir = Path.home() / ".vscode" / "extensions"
    if vscode_ext_dir.exists():
        # Find anthropic.claude-code-* directories, sort descending to get latest version first
        claude_ext_dirs = sorted(
            vscode_ext_dir.glob("anthropic.claude-code-*"),
            key=lambda p: p.name,
            reverse=True,
        )
        for ext_dir in claude_ext_dirs:
            native_binary = ext_dir / "resources" / "native-binary" / "claude.exe"
            if native_binary.exists():
                candidate_commands.append(str(native_binary))
                break  # Use latest version only

    placeholder_key = (
        str(os.getenv("ANTHROPIC_API_KEY", "")).strip().lower() in _CLAUDE_PLACEHOLDER_KEYS
    )
    seen_commands: set[str] = set()
    last_detail = "Claude CLI probe did not find a runnable command"
    last_metadata: dict[str, Any] = {}

    for command_name in candidate_commands:
        normalized = command_name.strip()
        if not normalized or normalized in seen_commands:
            continue
        seen_commands.add(normalized)

        resolved_path = shutil.which(normalized)
        if not resolved_path and not Path(normalized).exists():
            continue

        metadata: dict[str, Any] = {
            "command": normalized,
            "path": resolved_path or normalized,
        }

        if not strict_auth_probe:
            if placeholder_key:
                return (
                    AgentStatus.DEGRADED,
                    "Claude CLI found but ANTHROPIC_API_KEY looks like a placeholder value",
                    metadata,
                )
            return AgentStatus.ONLINE, "Claude CLI command detected (light probe)", metadata

        if normalized.lower().endswith(".cmd"):
            cmd_exe = shutil.which("cmd.exe")
            if not cmd_exe:
                return (
                    AgentStatus.DEGRADED,
                    "Claude CLI command found but cmd.exe is unavailable for .cmd execution",
                    metadata,
                )
            probe_cmd = (
                [cmd_exe, "/d", "/s", "/c", f"{normalized} auth status"]
                if strict_auth_probe
                else [cmd_exe, "/d", "/s", "/c", f"{normalized} --version"]
            )
        else:
            executable = resolved_path or normalized
            probe_cmd = (
                [executable, "auth", "status"] if strict_auth_probe else [executable, "--version"]
            )

        exit_code, output = _run_probe_command(probe_cmd, timeout=4.0)
        lower_output = output.lower()
        metadata["auth_exit_code"] = exit_code
        if output:
            metadata["auth_output_tail"] = output[-200:]

        if exit_code == 0:
            if strict_auth_probe:
                return AgentStatus.ONLINE, "Claude CLI is authenticated and available", metadata
            return AgentStatus.ONLINE, "Claude CLI is available", metadata

        if any(marker in lower_output for marker in _CLAUDE_AUTH_FAILURE_MARKERS):
            return (
                AgentStatus.DEGRADED,
                "Claude CLI command is available but authentication is invalid or expired",
                metadata,
            )

        if "unknown command" in lower_output or "unrecognized" in lower_output:
            if placeholder_key:
                return (
                    AgentStatus.DEGRADED,
                    "Claude CLI found but ANTHROPIC_API_KEY looks like a placeholder value",
                    metadata,
                )
            return AgentStatus.ONLINE, "Claude CLI found (probe command unsupported)", metadata

        if placeholder_key:
            return (
                AgentStatus.DEGRADED,
                "Claude CLI found but ANTHROPIC_API_KEY looks like a placeholder value",
                metadata,
            )

        last_detail = "Claude CLI found but probe was inconclusive"
        last_metadata = metadata

    if custom_cmd:
        return (
            AgentStatus.OFFLINE,
            "Claude CLI command not found or not runnable (check NUSYQ_CLAUDE_CLI_COMMAND)",
            {"custom_command": custom_cmd, **last_metadata},
        )
    return AgentStatus.OFFLINE, last_detail, last_metadata


def _probe_import(module_path: str) -> tuple[AgentStatus, str, dict[str, Any]]:
    """Check if a Python module can be resolved without importing side effects."""
    try:
        spec = importlib.util.find_spec(module_path)
    except (ImportError, ModuleNotFoundError, ValueError) as exc:
        return AgentStatus.OFFLINE, f"Spec lookup failed: {exc}", {"module": module_path}
    if spec is None:
        return AgentStatus.OFFLINE, f"Module not found: {module_path}", {"module": module_path}
    meta: dict[str, Any] = {
        "module": module_path,
        "origin": str(spec.origin) if spec.origin else None,
    }
    return AgentStatus.ONLINE, f"Module resolvable: {module_path}", meta


def _probe_metaclaw() -> tuple[AgentStatus, str, dict[str, Any]]:
    """Probe local MetaClaw (Node.js observability/trace agent).

    Checks for the agent directory in state/runtime/external/metaclaw-agent/
    and whether Node.js + npm are available with node_modules installed.
    """
    runtime_dir = (
        Path(__file__).resolve().parents[2] / "state" / "runtime" / "external" / "metaclaw-agent"
    )
    if not runtime_dir.exists():
        return AgentStatus.OFFLINE, "MetaClaw runtime not found", {"path": str(runtime_dir)}

    node_ok = bool(shutil.which("node"))
    npm_ok = bool(shutil.which("npm"))
    node_modules_ok = (runtime_dir / "node_modules").exists()
    env_ok = (runtime_dir / ".env").exists()

    meta: dict[str, Any] = {
        "path": str(runtime_dir),
        "node_available": node_ok,
        "npm_available": npm_ok,
        "node_modules_ready": node_modules_ok,
        "env_configured": env_ok,
    }

    if node_ok and node_modules_ok:
        return AgentStatus.ONLINE, "MetaClaw ready", meta
    if runtime_dir.exists():
        return AgentStatus.DEGRADED, "MetaClaw present (run npm install in metaclaw-agent/)", meta
    return AgentStatus.OFFLINE, "MetaClaw not installed", meta


def _probe_hermes_agent() -> tuple[AgentStatus, str, dict[str, Any]]:
    """Probe local Hermes-Agent (OpenRouter-based autonomous Python CLI agent).

    Checks for cli.py in state/runtime/external/hermes-agent/ and verifies the
    Python interpreter can find it.  No network required for probe.
    """
    runtime_dir = (
        Path(__file__).resolve().parents[2] / "state" / "runtime" / "external" / "hermes-agent"
    )
    cli_path = runtime_dir / "cli.py"
    if not cli_path.exists():
        return AgentStatus.OFFLINE, "Hermes-Agent not installed", {"path": str(runtime_dir)}

    # Verify pyproject.toml / requirements exist so we can report install completeness
    meta: dict[str, Any] = {"path": str(cli_path)}
    has_reqs = (runtime_dir / "requirements.txt").exists()
    has_pyproj = (runtime_dir / "pyproject.toml").exists()
    meta["has_requirements"] = has_reqs or has_pyproj

    # Quick sanity-check: look for OPENROUTER_API_KEY in env or hermes home .env
    hermes_home = Path(os.getenv("HERMES_HOME", str(Path.home() / ".hermes")))
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("HERMES_API_KEY")
    env_file_present = (hermes_home / ".env").exists() or (runtime_dir / ".env").exists()
    meta["api_key_configured"] = bool(api_key) or env_file_present

    status = (
        AgentStatus.ONLINE
        if (meta["has_requirements"] and meta["api_key_configured"])
        else AgentStatus.DEGRADED
    )
    detail = (
        "Hermes-Agent ready"
        if status == AgentStatus.ONLINE
        else "Hermes-Agent present (check API key / requirements)"
    )
    return status, detail, meta


def _probe_skyclaw_binary() -> tuple[AgentStatus, str, dict[str, Any]]:
    """Probe local SkyClaw (Rust) sidecar runtime.

    Checks for SkyClaw binary in state/runtime/skyclaw/target/debug/.
    Supports both Windows (.exe) and Linux (via WSL) binaries.
    """
    import shutil
    import subprocess

    runtime_dir = Path(__file__).resolve().parents[2] / "state" / "runtime" / "skyclaw"
    if not runtime_dir.exists():
        return AgentStatus.OFFLINE, "SkyClaw runtime not installed", {"path": str(runtime_dir)}

    # Find binary - Windows prefers .exe, falls back to WSL for Linux binary
    binary_path: Path | None = None
    use_wsl = False

    if os.name == "nt":
        exe_path = runtime_dir / "target" / "debug" / "skyclaw.exe"
        linux_path = runtime_dir / "target" / "debug" / "skyclaw"
        if exe_path.exists():
            binary_path = exe_path
        elif linux_path.exists():
            binary_path = linux_path
            use_wsl = True
    else:
        binary_path = runtime_dir / "target" / "debug" / "skyclaw"

    if binary_path is None or not binary_path.exists():
        return AgentStatus.OFFLINE, "SkyClaw binary not found", {"path": str(runtime_dir)}

    # WSL-mode: Linux ELF binary on Windows — skip execution probe (WSL cold-start >5s).
    # Instead verify WSL is installed (instant) and report binary-present status.
    if use_wsl:
        wsl_exe = shutil.which("wsl")
        if wsl_exe is None:
            return (
                AgentStatus.DEGRADED,
                "SkyClaw binary found (Linux ELF) but WSL is not installed",
                {"path": str(binary_path), "wsl_mode": True},
            )
        return (
            AgentStatus.ONLINE,
            "SkyClaw binary present (Linux ELF via WSL)",
            {
                "path": str(binary_path),
                "wsl_mode": True,
                "note": "WSL execution not probed at startup",
            },
        )

    # Native binary: run --version check directly
    cmd = [str(binary_path), "--version"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0] if result.stdout else "unknown"
            return (
                AgentStatus.ONLINE,
                f"SkyClaw ready ({version})",
                {
                    "path": str(binary_path),
                    "version": version,
                    "wsl_mode": False,
                },
            )
        return (
            AgentStatus.DEGRADED,
            f"SkyClaw binary found but version check failed (rc={result.returncode})",
            {
                "path": str(binary_path),
                "wsl_mode": False,
            },
        )
    except subprocess.TimeoutExpired:
        return AgentStatus.DEGRADED, "SkyClaw version check timed out", {"path": str(binary_path)}
    except Exception as exc:
        return AgentStatus.DEGRADED, f"SkyClaw probe error: {exc}", {"path": str(binary_path)}


def _probe_chatdev_local() -> tuple[AgentStatus, str, dict[str, Any]]:
    """Detect local ChatDev launcher capability when MCP HTTP health is offline."""
    run_files = ("run.py", "run_ollama.py")
    candidates: list[Path] = []

    env_path = os.getenv("CHATDEV_PATH")
    if env_path:
        candidates.append(Path(env_path).expanduser())

    settings_path = Path(__file__).resolve().parents[1] / "integration" / "settings.json"
    if settings_path.exists():
        try:
            settings_data = json.loads(settings_path.read_text(encoding="utf-8"))
            configured = settings_data.get("chatdev_path")
            if isinstance(configured, str) and configured.strip():
                candidates.append(Path(configured.strip()).expanduser())
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)

    # Known NuSyQ workspace fallbacks
    candidates.extend(
        [
            Path("C:/Users/keath/NuSyQ/ChatDev"),
            Path("/mnt/c/Users/keath/NuSyQ/ChatDev"),
            Path.home() / "NuSyQ" / "ChatDev",
            Path("C:/Users/keath/Desktop/Legacy/ChatDev_CORE/ChatDev-main"),
        ]
    )

    seen: set[str] = set()
    for candidate in candidates:
        normalized = str(candidate.resolve()) if candidate.exists() else str(candidate)
        if normalized in seen:
            continue
        seen.add(normalized)
        if any((candidate / run_file).exists() for run_file in run_files):
            return (
                AgentStatus.ONLINE,
                "Local ChatDev installation detected (launcher-capable)",
                {"chatdev_path": str(candidate)},
            )

    return AgentStatus.OFFLINE, "ChatDev local installation not detected", {}


def _probe_devtool() -> tuple[AgentStatus, str, dict[str, Any]]:
    """Probe DevTool+ availability.

    DevTool+ provides 25+ Chrome DevTools MCP tools for browser automation,
    debugging, and testing. Chrome is preferred; Edge can be surfaced as a
    degraded fallback in Windows/WSL environments.

    Returns:
        (status, detail, metadata) tuple
    """
    try:
        from src.integrations.devtool_bridge import \
            probe_devtool as _bridge_probe

        status_str, detail, meta = _bridge_probe()
        # Convert string status to AgentStatus enum
        status_map = {
            "ONLINE": AgentStatus.ONLINE,
            "DEGRADED": AgentStatus.DEGRADED,
            "OFFLINE": AgentStatus.OFFLINE,
        }
        return status_map.get(status_str, AgentStatus.UNKNOWN), detail, meta
    except ImportError as e:
        return (
            AgentStatus.OFFLINE,
            f"DevTool+ bridge import failed: {e}",
            {"error": str(e)},
        )
    except Exception as e:
        return (
            AgentStatus.UNKNOWN,
            f"DevTool+ probe error: {e}",
            {"error": str(e)},
        )


def _probe_gitkraken() -> tuple[AgentStatus, str, dict[str, Any]]:
    """Probe GitKraken MCP availability (requires Git).

    GitKraken provides 24 MCP tools for multi-platform git operations,
    cross-provider issue/PR management, and GitLens features.

    Returns:
        (status, detail, metadata) tuple
    """
    try:
        from src.integrations.gitkraken_bridge import \
            probe_gitkraken as _bridge_probe

        result = _bridge_probe()
        status_str = result.get("status", "offline").upper()
        detail = result.get("detail", "GitKraken probe failed")

        status_map = {
            "ONLINE": AgentStatus.ONLINE,
            "DEGRADED": AgentStatus.DEGRADED,
            "OFFLINE": AgentStatus.OFFLINE,
        }
        return status_map.get(status_str, AgentStatus.UNKNOWN), detail, {}
    except ImportError as e:
        return (
            AgentStatus.OFFLINE,
            f"GitKraken bridge import failed: {e}",
            {"error": str(e)},
        )
    except Exception as e:
        return (
            AgentStatus.UNKNOWN,
            f"GitKraken probe error: {e}",
            {"error": str(e)},
        )


def _probe_huggingface() -> tuple[AgentStatus, str, dict[str, Any]]:
    """Probe HuggingFace MCP availability.

    HuggingFace Hub provides 10 MCP tools for searching models, datasets,
    papers, and Spaces. Supports authenticated access.

    Returns:
        (status, detail, metadata) tuple
    """
    try:
        from src.integrations.huggingface_bridge import \
            probe_huggingface as _bridge_probe

        result = _bridge_probe()
        status_str = result.get("status", "offline").upper()
        detail = result.get("detail", "HuggingFace probe completed")
        meta = {
            "tools": result.get("tools", 10),
            "authenticated": result.get("authenticated", False),
            "username": result.get("username"),
        }

        status_map = {
            "ONLINE": AgentStatus.ONLINE,
            "DEGRADED": AgentStatus.DEGRADED,
            "OFFLINE": AgentStatus.OFFLINE,
        }
        return status_map.get(status_str, AgentStatus.UNKNOWN), detail, meta
    except ImportError as e:
        return (
            AgentStatus.OFFLINE,
            f"HuggingFace bridge import failed: {e}",
            {"error": str(e)},
        )
    except Exception as e:
        return (
            AgentStatus.UNKNOWN,
            f"HuggingFace probe error: {e}",
            {"error": str(e)},
        )


def _probe_dbclient() -> tuple[AgentStatus, str, dict[str, Any]]:
    """Probe DBClient MCP availability.

    DBClient provides 3 MCP tools for SQL database operations:
    get-databases, get-tables, execute-query.

    Returns:
        (status, detail, metadata) tuple
    """
    try:
        from src.integrations.dbclient_bridge import \
            probe_dbclient as _bridge_probe

        result = _bridge_probe()
        status_str = result.get("status", "offline").upper()
        detail = result.get("detail", "DBClient probe completed")
        meta = {
            "tools": result.get("tools", 3),
            "state_db_available": result.get("state_db_available", False),
            "databases": result.get("databases", []),
        }

        status_map = {
            "ONLINE": AgentStatus.ONLINE,
            "DEGRADED": AgentStatus.DEGRADED,
            "OFFLINE": AgentStatus.OFFLINE,
        }
        return status_map.get(status_str, AgentStatus.UNKNOWN), detail, meta
    except ImportError as e:
        return (
            AgentStatus.OFFLINE,
            f"DBClient bridge import failed: {e}",
            {"error": str(e)},
        )
    except Exception as e:
        return (
            AgentStatus.UNKNOWN,
            f"DBClient probe error: {e}",
            {"error": str(e)},
        )


# ── Registry ─────────────────────────────────────────────────────────────────

# Maps agent name → list of (probe_fn, *args) to try in order
# First successful probe wins; all fail → OFFLINE
AGENT_PROBES: dict[str, list[tuple]] = {
    "ollama": [
        (_probe_http, "http://127.0.0.1:11434/api/tags"),
    ],
    "lmstudio": [
        # Check env override first (e.g. LMSTUDIO_BASE_URL=http://10.0.0.172:1234)
        (_probe_http, os.environ.get("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234") + "/v1/models"),
        # Fallback: network IP common for LM Studio on LAN
        (_probe_http, "http://10.0.0.172:1234/v1/models"),
    ],
    "chatdev": [
        (_probe_http, "http://127.0.0.1:8081/health"),
        (_probe_chatdev_local,),
    ],
    "codex": [
        (_probe_cli, "codex"),
    ],
    "claude_cli": [
        (_probe_claude_cli,),
    ],
    "copilot": [
        (_probe_env_var, "NUSYQ_COPILOT_BRIDGE_MODE"),
        # Copilot runs inside VS Code — env var is set by the extension
    ],
    "consciousness": [
        (_probe_import, "src.consciousness"),
    ],
    "quantum_resolver": [
        (_probe_import, "src.healing.quantum_problem_resolver"),
    ],
    "factory": [
        (_probe_import, "src.factories.project_factory"),
    ],
    "openclaw": [
        (_probe_http, "http://127.0.0.1:18789/"),  # Gateway serves HTTP on 18789 (dashboard)
    ],
    "skyclaw": [
        (_probe_skyclaw_binary,),  # Local Rust sidecar runtime
    ],
    "intermediary": [
        (_probe_import, "src.ai.ai_intermediary"),
    ],
    "devtool": [
        (_probe_devtool,),  # Chrome DevTools MCP (via DevTool+ extension)
    ],
    "gitkraken": [
        (_probe_gitkraken,),  # GitKraken MCP (git, issues, PRs across providers)
    ],
    "huggingface": [
        (_probe_huggingface,),  # HuggingFace Hub MCP (models, datasets, papers)
    ],
    "dbclient": [
        (_probe_dbclient,),  # DBClient MCP (SQL databases)
    ],
    "neural_ml": [
        (
            _probe_import,
            "src.ml",
        ),  # Consciousness-enhanced ML + NeuralQuantumBridge (offline-capable)
    ],
    "hermes": [
        (_probe_hermes_agent,),  # OpenRouter-based autonomous Python agent (web+terminal toolsets)
    ],
    "optimizer": [
        (
            _probe_import,
            "src.orchestration.continuous_optimization_engine",
        ),  # ContinuousOptimizationEngine (offline, culture-ship healing cycles)
    ],
    "metaclaw": [
        (_probe_metaclaw,),  # MetaClaw Node.js observability + trace agent
    ],
}

# Human-friendly display names
AGENT_DISPLAY_NAMES: dict[str, str] = {
    "ollama": "Ollama (local LLMs)",
    "lmstudio": "LM Studio",
    "chatdev": "ChatDev MCP",
    "codex": "Codex CLI",
    "claude_cli": "Claude CLI",
    "copilot": "VS Code Copilot",
    "consciousness": "Consciousness Temple",
    "quantum_resolver": "Quantum Resolver",
    "factory": "Project Factory",
    "openclaw": "OpenClaw Gateway (TypeScript)",
    "skyclaw": "SkyClaw Sidecar (Rust)",
    "intermediary": "AI Intermediary (Cognitive Bridge)",
    "devtool": "DevTool+ (Chrome DevTools MCP)",
    "gitkraken": "GitKraken MCP (Git + Issues/PRs)",
    "huggingface": "HuggingFace Hub MCP (ML Models/Datasets)",
    "dbclient": "DBClient MCP (SQL Database Operations)",
    "neural_ml": "Neural ML System (ConsciousnessEnhancedML + NeuralQuantumBridge)",
    "hermes": "Hermes-Agent (OpenRouter autonomous CLI — web+terminal toolsets)",
    "optimizer": "Continuous Optimization Engine (culture-ship healing cycles, offline)",
    "metaclaw": "MetaClaw (autonomous Web3 bounty hunting agent — Base chain, USDC rewards)",
}


class AgentAvailabilityRegistry:
    """Probes agents and reports availability.

    Usage:
        registry = AgentAvailabilityRegistry()
        results = await registry.probe_all()
        for name, result in results.items():
            print(f"{name}: {result.status}")
    """

    def __init__(self, timeout: float = 3.0) -> None:
        """Initialize AgentAvailabilityRegistry with timeout."""
        self.timeout = timeout

    async def probe_one(self, agent: str) -> AgentProbeResult:
        """Probe a single agent's availability.

        Args:
            agent: Agent name (must be in AGENT_PROBES)

        Returns:
            AgentProbeResult with status and details
        """
        probes = AGENT_PROBES.get(agent)
        if not probes:
            return AgentProbeResult(
                agent=agent,
                status=AgentStatus.UNKNOWN,
                detail=f"No probe defined for '{agent}'",
            )

        # Run probes in order; first success wins.
        # Keep probe execution synchronous to avoid platform-specific
        # threadpool deadlocks observed under WSL/Windows subprocess + socket probes.
        detail = "All probes failed"
        metadata: dict[str, Any] = {}
        degraded_result: AgentProbeResult | None = None

        for probe_def in probes:
            probe_fn = probe_def[0]
            probe_args = probe_def[1:]

            start = time.monotonic()
            try:
                # HTTP probes accept a timeout kwarg.
                if probe_fn is _probe_http:
                    status, detail, meta = probe_fn(*probe_args, timeout=self.timeout)
                else:
                    status, detail, meta = probe_fn(*probe_args)

                latency = (time.monotonic() - start) * 1000

                if status == AgentStatus.ONLINE:
                    return AgentProbeResult(
                        agent=agent,
                        status=status,
                        latency_ms=latency,
                        detail=detail,
                        metadata=meta,
                    )
                if status == AgentStatus.DEGRADED and degraded_result is None:
                    degraded_result = AgentProbeResult(
                        agent=agent,
                        status=status,
                        latency_ms=latency,
                        detail=detail,
                        metadata=meta,
                    )
                detail = detail or "Probe did not report availability"
                metadata = meta
            except Exception as exc:
                detail = f"Probe error: {exc}"
                metadata = {}

        if degraded_result is not None:
            return degraded_result

        # All probes failed hard-offline
        return AgentProbeResult(
            agent=agent,
            status=AgentStatus.OFFLINE,
            detail=detail,
            metadata=metadata,
        )

    async def probe_with_recovery(self, agent: str, auto_recover: bool = True) -> AgentProbeResult:
        """Probe an agent with optional auto-recovery for known agents.

        Currently supports auto-recovery for:
        - ollama: Uses OllamaServiceManager with WSL awareness

        Args:
            agent: Agent name
            auto_recover: If True and agent is offline, attempt recovery

        Returns:
            AgentProbeResult (may be ONLINE after successful recovery)
        """
        result = await self.probe_one(agent)

        if result.status == AgentStatus.ONLINE or not auto_recover:
            return result

        # ── Auto-recovery logic ──────────────────────────────────────────────
        if agent == "ollama":
            try:
                from src.services.ollama_service_manager import \
                    OllamaServiceManager

                logger.info("Ollama offline — attempting auto-recovery...")

                mgr = OllamaServiceManager()
                if mgr.ensure_running():
                    # Re-probe after recovery
                    return await self.probe_one(agent)
                else:
                    result.detail = f"{result.detail} (auto-recovery failed)"
            except ImportError:
                pass  # OllamaServiceManager not available

        return result

    # Agents that support auto-recovery via probe_with_recovery()
    RECOVERABLE_AGENTS: frozenset[str] = frozenset({"ollama"})

    async def probe_all(
        self,
        agents: list[str] | None = None,
        *,
        auto_recover: bool = True,
    ) -> dict[str, AgentProbeResult]:
        """Probe all (or specified) agents concurrently.

        Args:
            agents: Specific agents to probe (defaults to all registered)
            auto_recover: If True (default), use probe_with_recovery() for agents
                          that support it (currently: ollama). This means an offline
                          Ollama will be started automatically before reporting status.

        Returns:
            Dict mapping agent name to probe result
        """
        targets = agents or list(AGENT_PROBES.keys())

        # Lazy import to avoid circular imports — best-effort; silently skipped if unavailable.
        try:
            from src.system.agent_awareness import emit as _emit
        except Exception:
            _emit = None

        output: dict[str, AgentProbeResult] = {}
        for agent in targets:
            try:
                if auto_recover and agent in self.RECOVERABLE_AGENTS:
                    output[agent] = await self.probe_with_recovery(agent, auto_recover=True)
                else:
                    output[agent] = await self.probe_one(agent)
            except Exception as exc:
                output[agent] = AgentProbeResult(
                    agent=agent,
                    status=AgentStatus.UNKNOWN,
                    detail=f"Probe exception: {exc}",
                )

            # Broadcast availability to the 'agents' terminal log (best-effort).
            if _emit is not None:
                result = output[agent]
                try:
                    if result.status == AgentStatus.ONLINE:
                        latency_str = (
                            f"latency={result.latency_ms:.0f}ms"
                            if result.latency_ms is not None
                            else ""
                        )
                        _emit.agent_online(agent, latency_str)
                    elif result.status == AgentStatus.DEGRADED:
                        _emit(
                            agent,
                            f"DEGRADED: {result.detail}",
                            level="WARNING",
                            source="mjolnir",
                        )
                        _emit(
                            "agents",
                            f"[agent_degraded] {agent}: {result.detail}",
                            level="WARNING",
                            source="mjolnir",
                        )
                    else:
                        # OFFLINE or UNKNOWN
                        _emit(
                            agent,
                            f"OFFLINE: {result.detail}",
                            level="WARNING",
                            source="mjolnir",
                        )
                        _emit(
                            "agents",
                            f"[agent_offline] {agent}: {result.detail}",
                            level="WARNING",
                            source="mjolnir",
                        )
                except Exception:
                    pass  # Never let emit failures break the probe loop

        return output

    def get_display_name(self, agent: str) -> str:
        """Get human-friendly name for an agent."""
        return AGENT_DISPLAY_NAMES.get(agent, agent)
