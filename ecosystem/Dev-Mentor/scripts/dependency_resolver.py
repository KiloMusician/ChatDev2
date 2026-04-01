"""Dependency Resolver — Harmony's spine.

Reads config/dependencies.yaml and determines which services are running,
which are missing, and what would need to start to satisfy the dependency graph.

In the Telephone Operator metaphor: this is the operator consulting the
switchboard and calling each extension to confirm the line is live.

Offline-first: uses only socket probes and HTTP checks. No heavy deps.

CLI:
  python scripts/dependency_resolver.py check          # report all services
  python scripts/dependency_resolver.py check redis    # check single service
  python scripts/dependency_resolver.py graph          # print dependency graph
  python scripts/dependency_resolver.py start <name>   # start a missing service
  python scripts/dependency_resolver.py bootstrap      # check + start all critical

Programmatic:
  from scripts.dependency_resolver import check_all, resolve_start_order, bootstrap
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Try PyYAML; fall back to a minimal YAML parser for simple keys
try:
    import yaml as _yaml

    def _load_yaml(text: str) -> dict:
        return _yaml.safe_load(text)

except ImportError:

    def _load_yaml(text: str) -> dict:  # type: ignore[misc]
        """Minimal YAML loader: handles top-level key: value and key:\n  sub: value."""
        result: dict = {}
        current_key = None
        for line in text.splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            if ":" in stripped:
                k, _, v = stripped.partition(":")
                k = k.strip()
                v = v.strip()
                if indent == 0:
                    current_key = k
                    result[k] = {} if not v else v
                elif current_key and isinstance(result.get(current_key), dict):
                    result[current_key][k] = v if v else {}
        return result


_ROOT = Path(__file__).resolve().parent.parent
_DEPS_PATH = _ROOT / "config" / "dependencies.yaml"
_RESULTS_PATH = _ROOT / "state" / "dependency_check.json"

_CHECK_TIMEOUT = 1.5  # seconds per probe
_START_WAIT = 8.0  # seconds to wait after spawning a service


# ── Probes ────────────────────────────────────────────────────────────────────


def _port_open(host: str, port: int, timeout: float = _CHECK_TIMEOUT) -> bool:
    """Return True if something is accepting TCP connections on host:port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (TimeoutError, OSError):
        return False


def _http_healthy(
    host: str, port: int, path: str, timeout: float = _CHECK_TIMEOUT
) -> tuple[bool, str]:
    """Return (ok, status_code_or_error). Does NOT require requests library."""
    import urllib.error
    import urllib.request

    url = f"http://{host}:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status < 400, str(resp.status)
    except urllib.error.HTTPError as e:
        return e.code < 500, str(e.code)
    except Exception as ex:
        return False, str(ex)


# ── YAML loading ──────────────────────────────────────────────────────────────


def _load_deps() -> dict:
    """Load config/dependencies.yaml. Return {} if not found."""
    if not _DEPS_PATH.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(_DEPS_PATH.read_text()) or {}
    except ImportError:
        return _load_yaml(_DEPS_PATH.read_text())
    except Exception:
        return {}


def _service_specs(deps: dict) -> dict[str, dict]:
    """Return only the service entries (skip top-level non-dict values and gateway_routes)."""
    skip = {"gateway_routes", "_comment", "_version"}
    return {k: v for k, v in deps.items() if k not in skip and isinstance(v, dict)}


# ── Core checks ───────────────────────────────────────────────────────────────


def check_service(name: str, spec: dict) -> dict:
    """Probe a single service. Returns:
    {name, port, status, healthy, probe_ms, requires, can_start}
    """
    port = spec.get("default_port", 0)
    health_path = spec.get("health_endpoint", "/health")
    host = "localhost"
    t0 = time.monotonic()

    if not port:
        return {
            "name": name,
            "port": None,
            "status": "no_port",
            "healthy": False,
            "probe_ms": 0,
            "requires": spec.get("requires", []),
            "can_start": bool(spec.get("start_command")),
        }

    port_live = _port_open(host, port)
    if port_live and health_path and health_path != "/":
        ok, code = _http_healthy(host, port, health_path)
        status = "healthy" if ok else f"http_{code}"
    elif port_live:
        ok = True
        status = "port_open"
    else:
        ok = False
        status = "unreachable"

    elapsed_ms = round((time.monotonic() - t0) * 1000, 1)
    return {
        "name": name,
        "port": port,
        "status": status,
        "healthy": ok,
        "probe_ms": elapsed_ms,
        "requires": spec.get("requires", []),
        "can_start": bool(spec.get("start_command")),
        "tags": spec.get("tags", []),
        "description": spec.get("description", ""),
        "start_command": spec.get("start_command", ""),
    }


def check_all(verbose: bool = False) -> dict:
    """Probe all services in dependencies.yaml.
    Returns {services: [...], summary: {...}}
    """
    deps = _load_deps()
    specs = _service_specs(deps)
    if not specs:
        return {
            "services": [],
            "summary": {"total": 0, "healthy": 0, "missing": 0},
            "error": f"No specs found in {_DEPS_PATH}",
        }

    results = []
    for name, spec in specs.items():
        r = check_service(name, spec)
        if verbose:
            icon = "✓" if r["healthy"] else "✗"
            print(
                f"  {icon} {name:<28} :{r['port']}  {r['status']}  ({r['probe_ms']}ms)"
            )
        results.append(r)

    healthy = sum(1 for r in results if r["healthy"])
    critical_down = [
        r for r in results if not r["healthy"] and "critical" in r.get("tags", [])
    ]
    optional_down = [
        r for r in results if not r["healthy"] and "critical" not in r.get("tags", [])
    ]

    summary = {
        "total": len(results),
        "healthy": healthy,
        "critical_down": len(critical_down),
        "optional_down": len(optional_down),
        "critical_names": [r["name"] for r in critical_down],
        "optional_names": [r["name"] for r in optional_down],
    }

    output = {"services": results, "summary": summary, "ts": time.time()}
    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(json.dumps(output, indent=2))
    return output


# ── Topological sort for start order ──────────────────────────────────────────


def resolve_start_order(specs: dict[str, dict]) -> list[str]:
    """Topological sort of services by their requires graph."""
    graph: dict[str, list[str]] = {
        name: spec.get("requires", []) for name, spec in specs.items()
    }
    visited: set = set()
    result: list[str] = []

    def visit(node: str, path: set = set()):
        if node in visited:
            return
        if node in path:
            result.append(node)  # cycle: just include it
            return
        path = path | {node}
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep, path)
        visited.add(node)
        result.append(node)

    for name in list(graph.keys()):
        visit(name)
    return result


# ── Bootstrap ─────────────────────────────────────────────────────────────────


def start_service(name: str, spec: dict) -> subprocess.Popen | None:
    """Attempt to start a service using its start_command from dependencies.yaml.
    Substitutes {port} with the default_port.
    Returns the Popen handle or None on failure.
    """
    cmd_template = spec.get("start_command", "")
    port = spec.get("default_port", 0)
    if not cmd_template or not port:
        return None

    cmd = cmd_template.format(port=port)
    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return proc
    except Exception as e:
        print(f"  [RESOLVER] Failed to start {name}: {e}", file=sys.stderr)
        return None


def bootstrap(dry_run: bool = True) -> dict:
    """Check all services. For any that are down and have a start_command,
    attempt to start them (unless dry_run=True, which only reports intent).

    In the Telephone Operator metaphor: the operator calls every extension,
    and if a line is dead, plugs in a new cable.
    """
    check = check_all()
    deps = _load_deps()
    specs = _service_specs(deps)
    order = resolve_start_order(specs)

    started = []
    skipped = []
    failed = []

    status_map = {r["name"]: r for r in check["services"]}

    for name in order:
        r = status_map.get(name)
        if not r:
            continue
        if r["healthy"]:
            continue  # already up
        if not r["can_start"]:
            skipped.append(name)
            continue

        spec = specs.get(name, {})
        if dry_run:
            started.append(f"[DRY] would start: {name} on :{spec.get('default_port')}")
            continue

        print(f"  [RESOLVER] Starting {name} on port {spec.get('default_port')}…")
        proc = start_service(name, spec)
        if proc:
            time.sleep(_START_WAIT)
            # Re-probe
            result = check_service(name, spec)
            if result["healthy"]:
                started.append(name)
            else:
                failed.append(name)
        else:
            failed.append(name)

    return {
        "already_healthy": check["summary"]["healthy"],
        "started": started,
        "skipped_no_cmd": skipped,
        "failed": failed,
        "dry_run": dry_run,
        "summary": check["summary"],
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    target = sys.argv[2] if len(sys.argv) > 2 else None

    if cmd == "check":
        deps = _load_deps()
        specs = _service_specs(deps)
        if target:
            if target not in specs:
                print(f"Unknown service: {target}")
                sys.exit(1)
            r = check_service(target, specs[target])
            print(json.dumps(r, indent=2))
        else:
            result = check_all(verbose=True)
            s = result["summary"]
            print(
                f"\n  {s['healthy']}/{s['total']} healthy | "
                f"{s['critical_down']} critical down | "
                f"{s['optional_down']} optional down"
            )
            if s["critical_names"]:
                print(f"  Critical down: {', '.join(s['critical_names'])}")

    elif cmd == "graph":
        deps = _load_deps()
        specs = _service_specs(deps)
        order = resolve_start_order(specs)
        print("Start order (dependency-sorted):")
        for i, name in enumerate(order, 1):
            spec = specs.get(name, {})
            reqs = spec.get("requires", [])
            req_str = f" (requires: {', '.join(reqs)})" if reqs else ""
            print(f"  {i:2}. {name}{req_str}")

    elif cmd == "start":
        if not target:
            print("Usage: dependency_resolver.py start <service-name>")
            sys.exit(1)
        deps = _load_deps()
        specs = _service_specs(deps)
        if target not in specs:
            print(f"Unknown service: {target}")
            sys.exit(1)
        result = bootstrap(dry_run=False)
        print(json.dumps(result, indent=2))

    elif cmd == "bootstrap":
        dry = "--live" not in sys.argv
        if dry:
            print("  (dry-run — pass --live to actually start services)")
        result = bootstrap(dry_run=dry)
        print(json.dumps(result, indent=2))

    else:
        print(
            f"Usage: {sys.argv[0]} [check [<name>]|graph|start <name>|bootstrap [--live]]"
        )
