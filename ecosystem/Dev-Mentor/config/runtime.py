"""
config/runtime.py — Single source of truth for service ports, state paths,
and environment detection.

POLICY
  - Port numbers come from config/port_map.json.  Never hard-code port literals.
  - State file paths come from PATHS below.  Never scatter "state/foo.db" strings.
  - Environment detection is explicit and auditable.
  - All callers use:
        from config.runtime import svc, port, probe, PATHS, RUNTIME_ENV

This module has ZERO imports from the game engine.  Import it anywhere safely.
"""

from __future__ import annotations

import json
import os
import socket
import pathlib

# ── Resolve project root ────────────────────────────────────────────────────
_HERE  = pathlib.Path(__file__).parent          # config/
ROOT   = _HERE.parent                           # repo root

# ── Load port_map.json once ─────────────────────────────────────────────────
_PORT_MAP_PATH = _HERE / "port_map.json"
_PORT_MAP: dict = {}
try:
    _PORT_MAP = json.loads(_PORT_MAP_PATH.read_text())
except Exception:
    pass

_PORTS_BY_KEY: dict[str, dict] = _PORT_MAP.get("ports", {})

# Build a name→config lookup in addition to the port-keyed one
_PORTS_BY_NAME: dict[str, dict] = {}
for _k, _v in _PORTS_BY_KEY.items():
    _svc_name = _v.get("service") or _v.get("name", "").lower().replace(" ", "_")
    _PORTS_BY_NAME[_svc_name] = dict(_v, port_key=_k)

# ── Environment detection ────────────────────────────────────────────────────
def _detect_env() -> str:
    """Return 'replit' | 'docker' | 'vscode' | 'unknown'."""
    if os.environ.get("REPLIT_DEPLOYMENT") or os.environ.get("REPL_ID"):
        return "replit"
    if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER"):
        return "docker"
    if os.environ.get("VSCODE_PID") or os.environ.get("TERM_PROGRAM") == "vscode":
        return "vscode"
    return "unknown"

RUNTIME_ENV: str = _detect_env()

# ── Main port for *this* process (Replit=5000, local/docker=7337) ────────────
# Default is 7337 (local/Docker/VS Code). Only use 5000 when explicitly on Replit.
_is_replit = bool(os.environ.get("REPL_ID") or os.environ.get("REPLIT_MODE") or os.environ.get("REPLIT_DEPLOYMENT"))
_default_port = "5000" if _is_replit else "7337"
SELF_PORT: int = int(os.environ.get("PORT", _default_port))

# ── Service accessors ────────────────────────────────────────────────────────

def svc(name: str) -> dict:
    """Return the port_map entry for a service name, or {} if unknown.

    Accepts either the port key ("3000") or the service slug ("gordon").
    Always includes a resolved 'port' int.
    """
    # Try slug lookup
    entry = _PORTS_BY_NAME.get(name, {})
    if entry:
        return entry
    # Try port-key lookup ("3000")
    entry = _PORTS_BY_KEY.get(str(name), {})
    if entry:
        return dict(entry, port_key=str(name))
    return {}


def port(name: str, fallback: int | None = None) -> int:
    """Return the local port number for a named service.

    Checks env vars first (e.g. PORT, MODEL_ROUTER_PORT, SERENA_HEALTH_PORT)
    so overrides always win.
    """
    _env_overrides: dict[str, str] = {
        "devmentor":     "PORT",
        "terminal_depths": "PORT",
        "model_router":  "MODEL_ROUTER_PORT",
        "serena":        "SERENA_HEALTH_PORT",
        "serena_analytics": "SERENA_HEALTH_PORT",
        "nusyq":         "NUSYQ_PORT",
    }
    env_key = _env_overrides.get(name)
    if env_key:
        override = os.environ.get(env_key)
        if override:
            return int(override)
    entry = svc(name)
    if entry:
        return int(entry.get("local_port") or entry.get("port_key", fallback or 0))
    if fallback is not None:
        return fallback
    raise KeyError(f"runtime: unknown service '{name}' and no fallback provided")


def probe(name_or_port: str | int, host: str = "127.0.0.1", timeout: float = 0.35) -> bool:
    """TCP-probe a service by name or raw port number. Returns True = reachable."""
    if isinstance(name_or_port, str) and not name_or_port.isdigit():
        p = port(name_or_port, fallback=0)
        if p == 0:
            return False
    else:
        p = int(name_or_port)
    if p == 0:
        return False
    try:
        with socket.create_connection((host, p), timeout=timeout):
            return True
    except Exception:
        return False


# ── Canonical state file paths ───────────────────────────────────────────────
# Defined once here.  Everywhere else: from config.runtime import PATHS
PATHS: dict[str, pathlib.Path] = {
    # databases
    "db_devmentor":    ROOT / "state" / "devmentor.db",
    "db_agents":       ROOT / "state" / "agents.db",
    "db_economy":      ROOT / "state" / "economy.db",
    "db_lattice":      ROOT / "state" / "lattice.db",
    "db_serena":       ROOT / "state" / "serena_memory.db",
    "db_gordon":       ROOT / "state" / "gordon_memory.db",
    "db_memory":       ROOT / "state" / "memory.db",
    "db_ml":           ROOT / "state" / "model_registry.db",
    "db_rl":           ROOT / "state" / "rl_state.db",
    # state files
    "quest_log":       ROOT / "state" / "quest_log.jsonl",
    "agent_manifest":  ROOT / "state" / "agent_manifest.json",
    "nusyq_state":     ROOT / "state" / "nusyq_service_state.json",
    "port_status":     ROOT / "state" / "port_status.json",
    "gordon_status":   ROOT / "state" / "gordon_status.json",
    "memory_snapshot": ROOT / "state" / "memory_snapshot.json",
    "knowledge_graph": ROOT / "state" / "knowledge_graph.json",
    "dependency_check":ROOT / "state" / "dependency_check.json",
    # config files
    "port_map":        _PORT_MAP_PATH,
    "models_config":   _HERE / "models.yaml",
    "ecosystem_state": _HERE / "ecosystem_state.yaml",
    # sessions dir
    "sessions_dir":    ROOT / "sessions",
}


# ── Service table for boot / health consumers ────────────────────────────────
# Ordered list used by _cmd_boot and /api/system/boot.
# Each entry: (service_name, display_name, tag, critical)
# Port is resolved at call-time via port(service_name) so env vars win.

BOOT_SERVICES_FULL: list[tuple[str, str, str, bool]] = [
    ("devmentor",       "Terminal Depths API",    "REPLIT", True),
    ("devmentor_local", "DevMentor (local)",      "",       False),
    ("gordon",          "Gordon Orchestrator",    "",       False),
    ("serena",          "Serena Analytics",       "",       False),
    ("skyclaw",         "SkyClaw Scanner",        "",       False),
    ("culture_ship",    "Culture Ship",           "",       False),
    ("redis",           "Redis pub/sub",          "",       False),
    ("model_router",    "Model Router",           "",       False),
    ("ollama",          "Ollama (local LLM)",     "",       False),
    ("lattice_api",     "Lattice API",            "",       False),
    ("mcp_server",      "MCP Server",             "",       False),
    ("openwebui",       "OpenWebUI",              "",       False),
    ("vscode_bridge",   "VS Code Bridge",         "",       False),
]

BOOT_SERVICES_QUICK: list[tuple[str, str, str, bool]] = [
    ("devmentor",       "Terminal Depths API",    "REPLIT", True),
    ("serena",          "Serena Analytics",       "",       False),
    ("model_router",    "Model Router",           "",       False),
    ("ollama",          "Ollama (local LLM)",     "",       False),
    ("redis",           "Redis pub/sub",          "",       False),
]

# Extra port fallbacks for services not in port_map (added here, never in call sites)
_EXTRA_PORTS: dict[str, int] = {
    "devmentor_local": 7337,
    "redis":           int(os.environ.get("REDIS_PORT", "6379")),
    "ollama":          11434,
    "mcp_server":      8008,
    "lattice_api":     8091,
}


def resolve_port(service_name: str) -> int:
    """Like port() but also checks _EXTRA_PORTS for services not in port_map."""
    try:
        return port(service_name)
    except KeyError:
        return _EXTRA_PORTS.get(service_name, 0)


def build_service_status(quick: bool = False) -> dict[str, dict]:
    """Build the services dict used by /api/system/boot.

    Returns:
        {service_name: {port, up, critical}}
    """
    src = BOOT_SERVICES_QUICK if quick else BOOT_SERVICES_FULL
    result: dict[str, dict] = {}
    for svc_name, display, tag, critical in src:
        p = resolve_port(svc_name)
        if svc_name == "devmentor":
            p = SELF_PORT
        result[svc_name] = {
            "display":  display,
            "port":     p,
            "up":       probe(p),
            "critical": critical,
            "tag":      tag,
        }
    return result


# ── Input sanitization ───────────────────────────────────────────────────────
_MAX_CMD_LEN   = 512
_MAX_ARG_LEN   = 256
_MAX_ARG_COUNT = 32


class CommandSanitizer:
    """Validate and sanitize raw input before it reaches command handlers.

    Design:
      - Reject, never silently mutate.  Callers receive a structured error or
        a clean (cmd, args) tuple.
      - All limits are defined here.  No magic numbers in handlers.
    """

    BLOCKED_SEQUENCES: tuple[str, ...] = (
        "\x00", "\r\n", "\n\n",           # null bytes, double newlines
        "../", "..\\",                     # path traversal
        "${", "$(", "`",                   # shell injection seeds
        "\x1b[",                           # raw ANSI injection
    )

    @classmethod
    def sanitize(cls, raw: str) -> tuple[str, list[str]] | tuple[None, str]:
        """Parse and sanitize a raw command string.

        Returns:
            (cmd: str, args: list[str])  on success
            (None, error_message: str)   on rejection
        """
        if not isinstance(raw, str):
            return None, "input must be a string"
        if len(raw) > _MAX_CMD_LEN:
            return None, f"command too long ({len(raw)} > {_MAX_CMD_LEN} chars)"

        # Block dangerous sequences before any splitting
        raw_lower = raw.lower()
        for seq in cls.BLOCKED_SEQUENCES:
            if seq.lower() in raw_lower:
                return None, f"blocked sequence in input: {seq!r}"

        # Normalise and split
        stripped = raw.strip()
        if not stripped:
            return None, "empty command"

        parts = stripped.split()
        cmd   = parts[0].lower()
        args  = parts[1:]

        # Per-field limits
        if len(cmd) > 64:
            return None, "command token too long"
        if len(args) > _MAX_ARG_COUNT:
            return None, f"too many arguments ({len(args)} > {_MAX_ARG_COUNT})"
        for arg in args:
            if len(arg) > _MAX_ARG_LEN:
                return None, f"argument too long: {arg[:32]!r}..."

        # Allow only printable ASCII + common unicode range
        for ch in stripped:
            if ord(ch) < 0x20 and ch not in ('\t',):
                return None, f"non-printable character in input: {ord(ch):#04x}"

        return cmd, args


# ── Summary helper ────────────────────────────────────────────────────────────

def runtime_summary() -> dict:
    """Return a lightweight dict describing the current runtime configuration.

    Used by /api/system/boot and validate_all.py.
    """
    return {
        "env":       RUNTIME_ENV,
        "self_port": SELF_PORT,
        "port_map":  str(_PORT_MAP_PATH),
        "services":  len(_PORTS_BY_KEY),
        "paths_ok":  {k: v.exists() for k, v in PATHS.items()},
        "version":   _PORT_MAP.get("_version", "unknown"),
    }
