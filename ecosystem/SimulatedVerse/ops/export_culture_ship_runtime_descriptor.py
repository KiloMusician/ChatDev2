#!/usr/bin/env python3
"""Export the canonical SimulatedVerse Culture Ship runtime descriptor."""

from __future__ import annotations

import hashlib
import json
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "state" / "culture_ship_runtime_descriptor.json"
PACKAGE_JSON = ROOT / "package.json"
ENSURE_SURFACES = ROOT / "ops" / "ensure-local-surfaces.sh"
HEALTH_CHECKS = ROOT / "ops" / "health-checks.sh"
MINIMAL_SERVER = ROOT / "server" / "minimal_server.ts"
FULL_SERVER = ROOT / "server" / "full_server.ts"
CULTURE_MANIFEST = ROOT / "modules" / "culture_ship" / "manifest.yml"
SHIP_STATE_PATH = ROOT / "state" / "ship_state.json"
SHIP_MEMORY_PATH = ROOT / ".ship" / "memory.json"
CHATDEV_REGISTRY = ROOT / "packages" / "chatdev-adapter" / "registry.ts"
CHATDEV_SERVER = ROOT / "packages" / "chatdev-adapter" / "server.ts"
CHATDEV_HEALTH = ROOT / "ops" / "chatdev" / "health.ts"
GENERATOR_VERSION = "culture-ship-runtime-v1"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def sha256_path(path: Path) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    payload: dict[str, Any] = {}
    for raw in text.splitlines():
        if ":" not in raw or raw.lstrip().startswith("-"):
            continue
        key, value = raw.split(":", 1)
        payload[key.strip()] = value.strip() or True
    return payload


def read_package_scripts() -> dict[str, str]:
    payload = read_json(PACKAGE_JSON) or {}
    scripts = payload.get("scripts", {})
    return scripts if isinstance(scripts, dict) else {}


def read_chatdev_agents() -> list[str]:
    if not CHATDEV_REGISTRY.exists():
        return []
    agents: list[str] = []
    for raw in CHATDEV_REGISTRY.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped.endswith(":{") or stripped.endswith(": {"):
            agent = stripped.split(":", 1)[0].strip().strip('"').strip("'")
            if agent and agent not in {"export const ChatDevRegistry", "system", "id"}:
                agents.append(agent)
    return agents


def probe_json(url: str, timeout: float = 2.0) -> tuple[bool, dict[str, Any] | None, str]:
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            payload = json.loads(body) if body else {}
            return 200 <= response.status < 300, payload if isinstance(payload, dict) else {}, f"HTTP {response.status}"
    except (TimeoutError, URLError, ValueError, OSError) as exc:
        return False, None, str(exc)


def detect_runtime_mode(scripts: dict[str, str]) -> str:
    if "minimal_server.ts" in scripts.get("dev:minimal", ""):
        return "minimal"
    if scripts.get("dev:full"):
        return "full"
    return "unknown"


def host_resolves(host: str) -> bool:
    try:
        socket.getaddrinfo(host, None)
        return True
    except socket.gaierror:
        return False


def main() -> int:
    scripts = read_package_scripts()
    manifest = read_yaml(CULTURE_MANIFEST)
    ship_state = read_json(SHIP_STATE_PATH) or {}
    ship_memory = read_json(SHIP_MEMORY_PATH) or {}
    host = "127.0.0.1"
    port = 5002
    health_url = f"http://{host}:{port}/api/health"
    ready_url = f"http://{host}:{port}/readyz"
    chatdev_url = "http://127.0.0.1:4466/chatdev/agents"

    runtime_ok, runtime_payload, runtime_detail = probe_json(health_url)
    ready_ok, _ready_payload, ready_detail = probe_json(ready_url)
    chatdev_ok, chatdev_payload, chatdev_detail = probe_json(chatdev_url)
    agents = read_chatdev_agents()
    if isinstance(chatdev_payload, dict) and isinstance(chatdev_payload.get("agents"), list):
        live_agents = [
            item.get("id")
            for item in chatdev_payload["agents"]
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        agents = live_agents or agents

    descriptor = {
        "generated_at": iso_now(),
        "source_hashes": {
            normalize_path(PACKAGE_JSON): sha256_path(PACKAGE_JSON),
            normalize_path(ENSURE_SURFACES): sha256_path(ENSURE_SURFACES),
            normalize_path(HEALTH_CHECKS): sha256_path(HEALTH_CHECKS),
            normalize_path(MINIMAL_SERVER): sha256_path(MINIMAL_SERVER),
            normalize_path(FULL_SERVER): sha256_path(FULL_SERVER),
            normalize_path(CULTURE_MANIFEST): sha256_path(CULTURE_MANIFEST),
            normalize_path(SHIP_STATE_PATH): sha256_path(SHIP_STATE_PATH),
            normalize_path(SHIP_MEMORY_PATH): sha256_path(SHIP_MEMORY_PATH),
            normalize_path(CHATDEV_REGISTRY): sha256_path(CHATDEV_REGISTRY),
            normalize_path(CHATDEV_SERVER): sha256_path(CHATDEV_SERVER),
            normalize_path(CHATDEV_HEALTH): sha256_path(CHATDEV_HEALTH)
        },
        "source_paths": [
            normalize_path(PACKAGE_JSON),
            normalize_path(ENSURE_SURFACES),
            normalize_path(HEALTH_CHECKS),
            normalize_path(MINIMAL_SERVER),
            normalize_path(FULL_SERVER),
            normalize_path(CULTURE_MANIFEST),
            normalize_path(SHIP_STATE_PATH),
            normalize_path(SHIP_MEMORY_PATH),
            normalize_path(CHATDEV_REGISTRY),
            normalize_path(CHATDEV_SERVER),
            normalize_path(CHATDEV_HEALTH)
        ],
        "stale_after_seconds": 900,
        "generator_version": GENERATOR_VERSION,
        "runtime_owner": "simulatedverse",
        "control_owner": "nusyq_hub",
        "status": "ready" if runtime_ok and chatdev_ok else "degraded",
        "runtime_status": {
            "mode": detect_runtime_mode(scripts),
            "host": host,
            "host_resolves": host_resolves(host),
            "port": port,
            "health_url": health_url,
            "ready_url": ready_url,
            "ok": runtime_ok and ready_ok,
            "detail": runtime_detail if runtime_ok else runtime_detail or ready_detail,
            "reported_mode": runtime_payload.get("mode") if isinstance(runtime_payload, dict) else None
        },
        "chatdev": {
            "port": 4466,
            "agents_url": chatdev_url,
            "ok": chatdev_ok,
            "detail": chatdev_detail,
            "agents": agents
        },
        "culture_ship": {
            "manifest_version": manifest.get("version", "0.1.0"),
            "capabilities": manifest.get("capabilities", []),
            "policies": {
                "infrastructure_first": bool(manifest.get("infrastructure_first", True)),
                "local_first": bool(manifest.get("local_first", True)),
                "reversible": bool(manifest.get("reversible", True)),
                "token_default": (manifest.get("policies") or {}).get("token_default", "off")
                if isinstance(manifest.get("policies"), dict)
                else "off"
            },
            "last_tick": ship_state.get("lastTick"),
            "soft_lock_active": (ship_memory.get("softLock") or {}).get("active", False),
            "prefer_zero_token": (ship_memory.get("heuristics") or {}).get("preferZeroToken", True),
            "drivers": ship_memory.get("drivers", {}),
            "endpoints": [
                "/api/health",
                "/readyz",
                "/healthz",
                "/api/culture-ship/health-cycle",
                "/api/culture-ship/consciousness",
                "/api/consciousness/culture-ship/status"
            ],
            "commands": {
                key: scripts[key]
                for key in ("dev:minimal", "surfaces:ensure", "ops:health", "chatdev:health")
                if key in scripts
            }
        }
    }

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"descriptor": normalize_path(STATE_PATH), "status": descriptor["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
