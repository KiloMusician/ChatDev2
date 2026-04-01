"""Port Allocator — Dynamic port assignment for the ΔΨΣ service mesh.

The Telephone Operator pattern: when a new service starts, it calls
allocate_port_for_service() to claim a free port, then registers with
the ServiceRegistry. The gateway can then route to it immediately.

Usage:
  from scripts.port_allocator import find_free_port, allocate_port_for_service

  port = allocate_port_for_service("my-agent")
  # → 8213 (or whatever was free)

CLI:
  python scripts/port_allocator.py scan         # list all free ports 8000-9000
  python scripts/port_allocator.py alloc <name> # allocate and print a port
"""

from __future__ import annotations

import json
import random
import socket
import sys
from pathlib import Path
from typing import Dict, List, Optional

_ROOT = Path(__file__).resolve().parent.parent
_ASSIGNMENTS_PATH = _ROOT / "state" / "port_assignments.json"

# ── Port ranges (matching config/port_map.json philosophy) ───────────────────

_RESERVED_PORTS = {
    5000,  # devmentor main API (Replit external)
    7337,  # devmentor docker
    3000,
    3001,
    3002,
    3003,  # health servers
    6379,  # Redis
    8080,  # model router
    8765,  # rimapi bridge
    11434,  # Ollama
    1234,  # LM Studio
}

_AGENT_RANGE = (8100, 8200)  # agent HTTP services
_SERVICE_RANGE = (8200, 8500)  # general services
_ML_RANGE = (8500, 8600)  # ML services


def is_port_free(port: int, host: str = "localhost") -> bool:
    """Return True if no process is listening on port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) != 0


def find_free_port(
    start: int = 8000,
    end: int = 9000,
    exclude: set | None = None,
    max_attempts: int = 100,
) -> int:
    """Return a free port in [start, end], not in exclude set."""
    excluded = _RESERVED_PORTS | (exclude or set())
    candidates = [p for p in range(start, end + 1) if p not in excluded]
    random.shuffle(candidates)
    for port in candidates[:max_attempts]:
        if is_port_free(port):
            return port
    raise RuntimeError(f"No free port found in range {start}-{end}")


def scan_free_ports(start: int = 8000, end: int = 9000) -> list[int]:
    """Return all free ports in range (slow for large ranges)."""
    return [p for p in range(start, end + 1) if is_port_free(p)]


# ── Persistent assignments ────────────────────────────────────────────────────


def _load_assignments() -> dict[str, int]:
    if _ASSIGNMENTS_PATH.exists():
        try:
            return json.loads(_ASSIGNMENTS_PATH.read_text())
        except Exception:
            pass
    return {}


def _save_assignments(data: dict[str, int]) -> None:
    _ASSIGNMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _ASSIGNMENTS_PATH.write_text(json.dumps(data, indent=2))


def allocate_port_for_service(
    service_name: str,
    port_range: str = "service",
    force_new: bool = False,
) -> int:
    """Allocate and persist a port for a named service.
    If the service already has an allocation and that port is free, reuse it.
    """
    assignments = _load_assignments()
    existing = assignments.get(service_name)

    if existing and not force_new and is_port_free(existing):
        return existing

    ranges = {
        "agent": _AGENT_RANGE,
        "service": _SERVICE_RANGE,
        "ml": _ML_RANGE,
    }
    start, end = ranges.get(port_range, _SERVICE_RANGE)
    already_used = set(assignments.values())
    port = find_free_port(start, end, exclude=already_used)

    assignments[service_name] = port
    _save_assignments(assignments)
    return port


def release_port(service_name: str) -> int | None:
    """Remove a service's port assignment."""
    assignments = _load_assignments()
    port = assignments.pop(service_name, None)
    if port is not None:
        _save_assignments(assignments)
    return port


def all_assignments() -> dict[str, int]:
    return _load_assignments()


def summary() -> dict:
    assignments = _load_assignments()
    result = {}
    for name, port in sorted(assignments.items()):
        result[name] = {
            "port": port,
            "free": is_port_free(port),
            "status": "available" if is_port_free(port) else "in_use",
        }
    return result


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if cmd == "scan":
        start = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        end = int(sys.argv[3]) if len(sys.argv) > 3 else 8100
        free = scan_free_ports(start, end)
        print(f"Free ports {start}-{end}: {free}")

    elif cmd == "alloc":
        name = sys.argv[2] if len(sys.argv) > 2 else "unnamed"
        port = allocate_port_for_service(name)
        print(f"Allocated port {port} for '{name}'")

    elif cmd == "release":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        port = release_port(name)
        print(
            f"Released port {port} for '{name}'"
            if port
            else f"No assignment for '{name}'"
        )

    elif cmd == "summary":
        s = summary()
        for name, info in s.items():
            flag = "●" if not info["free"] else "○"
            print(f"  {flag} {name:<30} port {info['port']} ({info['status']})")

    else:
        print(f"Usage: {sys.argv[0]} [scan|alloc <name>|release <name>|summary]")
