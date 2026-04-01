"""
core/port_resolver.py — Ecosystem-wide port and URL resolution shim.

Single source of truth for service URLs across all NuSyQ ecosystem members:
  Dev-Mentor / Terminal Depths (this repo)
  SimulatedVerse
  Gordon orchestrator
  Serena, SkyClaw, Culture Ship
  NuSyQ-Hub, NuSyQ-Ultimate

RESOLUTION ORDER (for Terminal Depths URL):
  1. TERMINAL_DEPTHS_URL env var (explicit override — highest priority)
  2. TD_URL env var (short alias)
  3. config.runtime.SELF_PORT auto-detect (Replit→5000, Docker/VS Code→7337)
  4. Port probing (try 7337, then 5000, then 5000 as final fallback)

WHY THIS EXISTS:
  mcp/server.py had 30 scattered `_base = os.environ.get("TERMINAL_DEPTHS_URL",
  "http://localhost:5000")` inline variables, all hardcoded to 5000 as default.
  This was wrong in Docker/VS Code contexts (correct port is 7337) and made
  the ecosystem ignore the canonical SELF_PORT detection in config/runtime.py.
  This shim centralises resolution so all callers import once.

USAGE:
  from core.port_resolver import td_url, svc_url

  base = td_url()                        # auto-detected URL for this environment
  gordon = svc_url("gordon")             # Gordon orchestrator URL from port_map.json
  rimapi = svc_url("rimapi")             # RimAPI bridge URL

ENVIRONMENT VARIABLES (can be set in shell / .env / docker-compose.yml):
  TERMINAL_DEPTHS_URL  — full URL override, e.g. http://localhost:7337
  TD_URL               — short alias for TERMINAL_DEPTHS_URL
  PORT                 — port override (used by config.runtime.SELF_PORT)
  REPL_ID              — set by Replit; triggers port 5000 default
  REPLIT_DEPLOYMENT    — set by Replit deployments; triggers port 5000 default
  VSCODE_PID           — set by VS Code; triggers port 7337 default
"""

from __future__ import annotations

import json
import os
import socket
import pathlib
from typing import Optional

# ── Resolve project root ────────────────────────────────────────────────────
_HERE = pathlib.Path(__file__).parent        # core/
ROOT  = _HERE.parent                         # repo root

# ── Try to import config.runtime (may not be available in all contexts) ─────
try:
    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from config.runtime import SELF_PORT as _SELF_PORT, RUNTIME_ENV as _RUNTIME_ENV
except Exception:
    # Fallback: replicate the detection inline
    _is_replit = bool(
        os.environ.get("REPL_ID")
        or os.environ.get("REPLIT_MODE")
        or os.environ.get("REPLIT_DEPLOYMENT")
    )
    _SELF_PORT = int(os.environ.get("PORT", "5000" if _is_replit else "7337"))
    _RUNTIME_ENV = "replit" if _is_replit else "unknown"

# ── Load port_map.json ───────────────────────────────────────────────────────
_PORT_MAP: dict = {}
try:
    _PORT_MAP = json.loads((ROOT / "config" / "port_map.json").read_text())
except Exception:
    pass

_PORTS: dict[str, dict] = _PORT_MAP.get("ports", {})
_ENV_OVERRIDES: dict[str, dict] = _PORT_MAP.get("env_overrides", {})


# ── Core resolution functions ─────────────────────────────────────────────────

def td_url(default: Optional[str] = None) -> str:
    """
    Resolve the canonical URL for the Terminal Depths / DevMentor API.

    Resolution order:
      1. TERMINAL_DEPTHS_URL env var
      2. TD_URL env var
      3. config.runtime.SELF_PORT auto-detect
      4. `default` argument (if provided)
      5. http://localhost:5000 (hard fallback, never reached in practice)
    """
    explicit = (
        os.environ.get("TERMINAL_DEPTHS_URL")
        or os.environ.get("TD_URL")
    )
    if explicit:
        return explicit.rstrip("/")

    if default is not None:
        return default.rstrip("/")

    return f"http://localhost:{_SELF_PORT}"


def svc_url(service_name: str, fallback: str = "") -> str:
    """
    Resolve the URL for any named service from port_map.json.

    Args:
        service_name: The 'service' field value in port_map.json,
                      e.g. "gordon", "serena", "rimapi", "simulatedverse"
        fallback:     Returned if service is not found in port_map.json

    Examples:
        svc_url("gordon")       → "http://localhost:3000"
        svc_url("simulatedverse") → "http://localhost:5100"
    """
    # Check env overrides first (e.g., Docker service names instead of localhost)
    env_override_key = f"{service_name.upper()}_URL"
    env_val = os.environ.get(env_override_key)
    if env_val:
        return env_val.rstrip("/")

    # Look up in port_map.json by service name
    for port_key, cfg in _PORTS.items():
        svc = cfg.get("service", "")
        if svc == service_name:
            host = os.environ.get("SERVICE_HOST", "localhost")
            return f"http://{host}:{port_key}"

    return fallback


def probe_td_url(timeout: float = 1.0) -> str:
    """
    Actively probe for the running Terminal Depths server.
    Tries SELF_PORT first, then the other port, returns whichever responds.

    This is the fallback for when the env var is not set and you need certainty.
    Most callers should use td_url() instead.
    """
    candidates = [
        f"http://localhost:{_SELF_PORT}",
        f"http://localhost:{5000 if _SELF_PORT == 7337 else 7337}",
    ]
    # Check TERMINAL_DEPTHS_URL first
    explicit = os.environ.get("TERMINAL_DEPTHS_URL") or os.environ.get("TD_URL")
    if explicit:
        candidates = [explicit.rstrip("/"), *candidates]

    for url in candidates:
        try:
            host = url.replace("http://", "").split(":")[0]
            port = int(url.rsplit(":", 1)[-1].rstrip("/"))
            with socket.create_connection((host, port), timeout=timeout):
                return url
        except Exception:
            continue

    # Nothing responded — return the auto-detected URL anyway
    return f"http://localhost:{_SELF_PORT}"


def runtime_info() -> dict:
    """
    Return a summary of the current runtime environment and resolved URLs.
    Useful for health checks and debugging.
    """
    return {
        "runtime_env": _RUNTIME_ENV,
        "self_port": _SELF_PORT,
        "td_url": td_url(),
        "td_url_source": (
            "TERMINAL_DEPTHS_URL" if os.environ.get("TERMINAL_DEPTHS_URL")
            else "TD_URL" if os.environ.get("TD_URL")
            else f"config.runtime.SELF_PORT ({_RUNTIME_ENV})"
        ),
        "gordon_url": svc_url("gordon"),
        "simulatedverse_url": svc_url("simulatedverse"),
        "env_vars": {
            "TERMINAL_DEPTHS_URL": os.environ.get("TERMINAL_DEPTHS_URL", ""),
            "TD_URL": os.environ.get("TD_URL", ""),
            "PORT": os.environ.get("PORT", ""),
            "REPL_ID": bool(os.environ.get("REPL_ID")),
            "VSCODE_PID": bool(os.environ.get("VSCODE_PID")),
            "DOCKER_CONTAINER": bool(os.environ.get("DOCKER_CONTAINER")),
        },
    }


# ── Module-level convenience constants ───────────────────────────────────────
#
# Import these directly instead of calling td_url() repeatedly:
#
#   from core.port_resolver import TD_BASE
#   url = f"{TD_BASE}/api/game/command"
#
TD_BASE: str = td_url()
SELF_PORT: int = _SELF_PORT
RUNTIME_ENV: str = _RUNTIME_ENV
