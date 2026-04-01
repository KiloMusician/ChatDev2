"""Lightweight health check for NuSyQ ecosystem.

Checks (best-effort):
- key files exist (quest log, start_nusyq.py, core modules)
- attempt to import MCP server (NuSyQ/mcp_server)
- attempt HTTP GET to MCP_SERVER_URL (env or default http://localhost:8000)

Usage:
    python scripts/health_check.py

Outputs JSON summary and exits with 0 if core checks pass, otherwise 1.
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from importlib import import_module
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_MCP_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8080")

checks: dict[str, dict[str, Any]] = {
    "files": {},
    "imports": {},
    "http": {},
    "processes": {},
}

# File checks
files_to_check = [
    ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl",
    ROOT / "scripts" / "start_nusyq.py",
    ROOT / "src" / "tools" / "agent_task_router.py",
    ROOT / "src" / "system" / "dictionary" / "consciousness_bridge.py",
]

for p in files_to_check:
    checks["files"][str(p.relative_to(ROOT))] = p.exists()


def _check_mcp_imports() -> None:
    """Best-effort MCP server import checks across modern and legacy layouts."""
    # try importing by adding likely NuSyQ root if not already on sys.path
    potential = Path("C:/Users/keath/NuSyQ").resolve()
    if str(potential) not in sys.path:
        sys.path.insert(0, str(potential))

    import_targets = [
        "src.integration.mcp_server",  # current in-repo module
        "src.mcp_server",  # compatibility shim
        "mcp_server.main",  # legacy NuSyQ root layout
    ]

    checks["imports"]["mcp_server_available"] = False
    checks["imports"]["mcp_import_targets"] = import_targets
    errors: dict[str, str] = {}

    for target in import_targets:
        try:
            module = import_module(target)
            checks["imports"][target] = True
            checks["imports"]["mcp_server_available"] = True
            checks["imports"]["mcp_server_symbol"] = bool(
                hasattr(module, "MCPServer") or hasattr(module, "NuSyQMCPServer") or hasattr(module, "main")
            )
            checks["imports"]["mcp_import_target"] = target
            return
        except ImportError as exc:  # pragma: no cover - best-effort
            checks["imports"][target] = False
            errors[target] = str(exc)

    checks["imports"]["mcp_server_symbol"] = False
    checks["imports"]["mcp_import_errors"] = errors


_check_mcp_imports()


def _try_health(url: str) -> tuple[bool, dict[str, object]]:
    detail: dict[str, object] = {"url": url}
    try:
        req = urllib.request.Request(url.rstrip("/") + "/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            is_healthy = resp.status == 200
            detail["status"] = resp.status
            try:
                body = resp.read().decode("utf-8")
                detail["body"] = json.loads(body)
            except ValueError:
                detail["body"] = None
            return is_healthy, detail
    except urllib.error.HTTPError as err:  # pragma: no cover - best-effort
        detail["status"] = getattr(err, "code", None)
        detail["error"] = str(err)
        return False, detail
    except OSError as exc:  # pragma: no cover - best-effort
        detail["error"] = str(exc)
        return False, detail


# Try a small set of MCP endpoints (env override first, then common ports)
mcp_candidates = [
    DEFAULT_MCP_URL,
    "http://127.0.0.1:8080",
    "http://localhost:8081",
]
for candidate in mcp_candidates:
    ok, info = _try_health(candidate)
    checks["http"]["mcp_health"] = ok
    checks["http"]["mcp_health_body"] = info.get("body")
    checks["http"]["mcp_health_status"] = info.get("status")
    checks["http"]["mcp_health_url"] = candidate
    if ok:
        break
else:
    checks["http"]["mcp_health_error"] = info.get("error")


# Process checks
def _process_running(keyword: str) -> bool:
    """Lightweight ps scan for a keyword."""
    try:
        out = subprocess.check_output(["ps", "-ef"], text=True)
        return keyword in out
    except (subprocess.CalledProcessError, OSError):
        return False


def _state_flag(name: str) -> bool:
    """Look at critical_services.json to avoid brittle ps matching."""
    state_file = ROOT / "state" / "services" / "critical_services.json"
    if not state_file.exists():
        return False
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        services = data.get("services") or data.get("states") or {}
        entry = services.get(name) if isinstance(services, dict) else None
        if isinstance(entry, dict):
            status = entry.get("status") or entry.get("state")
            return str(status).lower() == "running"
    except (OSError, ValueError):
        return False
    return False


# Prefer state file; fall back to ps keyword
checks["processes"]["orchestrator"] = _state_flag("orchestrator") or _process_running("start_multi_ai_orchestrator.py")
# The PU queue runner is spawned via python -c so the command line often lacks
# the script name; consult state file first.
checks["processes"]["pu_queue"] = _state_flag("pu_queue") or _process_running("pu_queue_runner")
# Trace service runs as HTTP endpoint, not standalone process - check via HTTP
trace_ok, trace_info = _try_health("http://localhost:4318")
checks["processes"]["trace_service"] = trace_ok

# Final verdict: core is OK if quest log exists and either the import or HTTP health check passes
quest_log_key = str((ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl").relative_to(ROOT))
core_ok = checks["files"].get(quest_log_key, False) and (
    checks["imports"].get("mcp_server_available", False) or checks["http"].get("mcp_health", False)
)

result = {
    "root": str(ROOT),
    "mcp_server_url": DEFAULT_MCP_URL,
    "core_ok": core_ok,
    "checks": checks,
}

print(json.dumps(result, indent=2))

if not core_ok:
    sys.exit(1)

sys.exit(0)
