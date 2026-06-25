"""Bounded ChatDev2 colony truth probe.

This script intentionally separates live service truth from local checkout truth.
The colony service on :7338 can be healthy while the checked-out DevAll app has
routes that are not present in the running container image.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENDPOINTS = {
    "chatdev_colony": os.environ.get("CHATDEV_COLONY_URL", "http://localhost:7338"),
    "chatdev_local": os.environ.get("CHATDEV_LOCAL_URL", "http://localhost:6400"),
    "dev_mentor": os.environ.get("DEV_MENTOR_URL", os.environ.get("DEVMentor_URL", "http://localhost:7337")),
    "litellm": os.environ.get("LITELLM_URL", "http://localhost:4000"),
    "ollama": os.environ.get("OLLAMA_URL", "http://localhost:11434"),
}

PROBE_PATHS = {
    "chatdev_colony": ["/health", "/api/health", "/status", "/api/bridge/status", "/api/ecosystem/status"],
    "chatdev_local": ["/health", "/api/health", "/api/bridge/status", "/api/ecosystem/status"],
    "dev_mentor": ["/api/health", "/health"],
    "litellm": ["/v1/models"],
    "ollama": ["/api/tags"],
}


def _tcp_reachable(base_url: str, timeout: float) -> dict[str, Any]:
    parsed = urlparse(base_url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        return {"ok": False, "error": "missing host"}
    started = time.perf_counter()
    try:
        family = socket.AF_INET if host in {"localhost", "127.0.0.1"} else socket.AF_UNSPEC
        if family == socket.AF_INET:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(min(timeout, 0.4))
            try:
                sock.connect(("127.0.0.1", port))
            finally:
                sock.close()
        else:
            with socket.create_connection((host, port), timeout=min(timeout, 1.0)):
                pass
        return {
            "ok": True,
            "host": host,
            "port": port,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }
    except Exception as exc:
        return {
            "ok": False,
            "host": host,
            "port": port,
            "error": f"{type(exc).__name__}: {str(exc)[:160]}",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }


def _probe(url: str, timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        request = Request(url, headers={"User-Agent": "chatdev-colony-doctor/1"})
        with urlopen(request, timeout=timeout) as response:
            body = response.read(2048).decode("utf-8", errors="replace")
            payload = {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                "body_preview": body[:240],
            }
            try:
                decoded = json.loads(body)
            except Exception:
                decoded = None
            if isinstance(decoded, dict):
                payload["json"] = decoded
            return payload
    except URLError as exc:
        return {
            "ok": False,
            "error": str(exc.reason if hasattr(exc, "reason") else exc)[:240],
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {str(exc)[:220]}",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }


def _local_routes() -> dict[str, Any]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
            from server.app import app
    except Exception as exc:
        return {
            "loaded": False,
            "error": f"{type(exc).__name__}: {exc}",
            "import_output": (captured_stdout.getvalue() + captured_stderr.getvalue())[-2000:],
        }

    routes = []
    for route in _walk_routes(app.routes):
        path = getattr(route, "path", None)
        methods = sorted(getattr(route, "methods", []) or [])
        if path:
            routes.append({"path": path, "methods": methods})

    important = ["/health", "/api/health", "/api/bridge/status", "/api/ecosystem/status"]
    route_paths = {route["path"] for route in routes}
    return {
        "loaded": True,
        "count": len(routes),
        "important": {path: path in route_paths for path in important},
        "import_output": (captured_stdout.getvalue() + captured_stderr.getvalue())[-2000:],
        "routes": sorted(routes, key=lambda item: item["path"]),
    }


def _walk_routes(routes: Any) -> list[Any]:
    flattened = []
    for route in routes:
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            flattened.extend(_walk_routes(getattr(original_router, "routes", [])))
            continue

        nested_routes = getattr(route, "routes", None)
        if nested_routes:
            flattened.extend(_walk_routes(nested_routes))
            continue

        flattened.append(route)
    return flattened


def build_report(timeout: float = 2.0) -> dict[str, Any]:
    probes: dict[str, Any] = {}
    for name, base_url in DEFAULT_ENDPOINTS.items():
        tcp = _tcp_reachable(base_url, timeout)
        if not tcp["ok"]:
            probes[name] = {
                "base_url": base_url,
                "tcp": tcp,
                "paths": {
                    path: {"ok": False, "skipped": True, "reason": "tcp_unreachable"}
                    for path in PROBE_PATHS[name]
                },
            }
            continue
        probes[name] = {
            "base_url": base_url,
            "tcp": tcp,
            "paths": {
                path: _probe(f"{base_url.rstrip('/')}{path}", timeout)
                for path in PROBE_PATHS[name]
            },
        }

    local = _local_routes()
    colony_paths = probes["chatdev_colony"]["paths"]
    colony_status = colony_paths.get("/status", {}).get("json") or {}
    colony_surface = colony_status.get("surface") if isinstance(colony_status, dict) else {}
    if not isinstance(colony_surface, dict):
        colony_surface = {}
    live_surface_id = colony_surface.get("service_id")
    live_surface_kind = colony_surface.get("surface_kind")
    live_is_devmentor_worker = live_surface_id == "devmentor-chatdev-worker"
    drift = []
    surface_mismatches = []
    for path, present in local.get("important", {}).items():
        live = colony_paths.get(path)
        if present and live and not live.get("ok"):
            item = {
                "path": path,
                "local_route_present": True,
                "live_status": live.get("status"),
                "live_error": live.get("error"),
            }
            if live_is_devmentor_worker and path not in {"/health", "/api/health"}:
                item["reason"] = "live_service_is_devmentor_queue_worker"
                surface_mismatches.append(item)
            else:
                drift.append(item)

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": str(ROOT),
        "summary": {
            "chatdev_colony_health": probes["chatdev_colony"]["paths"]["/health"].get("ok") is True,
            "chatdev_local_health": probes["chatdev_local"]["paths"]["/health"].get("ok") is True,
            "local_app_loaded": local.get("loaded") is True,
            "live_surface_id": live_surface_id,
            "live_surface_kind": live_surface_kind,
            "surface_mismatch_count": len(surface_mismatches),
            "route_drift_count": len(drift),
        },
        "probes": probes,
        "local_routes": local,
        "drift": drift,
        "surface_mismatches": surface_mismatches,
        "notes": [
            "Use this instead of broad rg over ecosystem mirrors for first-pass ChatDev truth.",
            "A healthy :7338 service does not prove the local checkout routes are live in the container.",
            "If :7338 reports service_id=devmentor-chatdev-worker, ChatDev2 app-only routes are surface mismatches rather than route drift.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe ChatDev2 colony integration truth.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--timeout", type=float, default=2.0, help="Per-request timeout in seconds.")
    args = parser.parse_args()

    report = build_report(timeout=args.timeout)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print("ChatDev2 colony doctor")
        print(f"  root: {report['root']}")
        print(f"  colony health (:7338): {summary['chatdev_colony_health']}")
        print(f"  local health (:6400): {summary['chatdev_local_health']}")
        print(f"  local app loaded: {summary['local_app_loaded']}")
        print(f"  live surface: {summary.get('live_surface_id') or 'unknown'} ({summary.get('live_surface_kind') or 'unknown'})")
        if not summary["local_app_loaded"]:
            print(f"  local app error: {report['local_routes'].get('error')}")
        print(f"  surface mismatch count: {summary['surface_mismatch_count']}")
        for item in report["surface_mismatches"]:
            print(f"  mismatch: {item['path']} local=true live_surface={summary.get('live_surface_id')}")
        print(f"  route drift count: {summary['route_drift_count']}")
        for item in report["drift"]:
            print(f"  drift: {item['path']} local=true live={item.get('live_status') or item.get('live_error')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
