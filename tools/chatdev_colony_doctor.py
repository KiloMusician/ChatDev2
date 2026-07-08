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
import subprocess
import socket
import sys
import tempfile
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

STARTUP_ROUTE_TIMEOUTS = {
    "/health": 1.0,
    "/api/health": 1.0,
    "/api/bridge/status": 6.0,
    "/api/ecosystem/status": 6.0,
}


def _python_capability_probe(command: list[str], timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [
                *command,
                "-c",
                "import sys, importlib.util, platform; "
                "print(sys.executable); "
                "print(importlib.util.find_spec('pygame') is not None); "
                "print(platform.python_version())",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        return {
            "ok": completed.returncode == 0 and len(lines) >= 3,
            "command": command,
            "returncode": completed.returncode,
            "executable": lines[0] if len(lines) >= 1 else None,
            "pygame": lines[1] == "True" if len(lines) >= 2 else None,
            "python_version": lines[2] if len(lines) >= 3 else None,
            "stderr_tail": completed.stderr[-300:],
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }
    except Exception as exc:
        return {
            "ok": False,
            "command": command,
            "error": f"{type(exc).__name__}: {str(exc)[:200]}",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }


def _gamedev_python_candidates() -> list[dict[str, Any]]:
    workspace_root = ROOT.parent.parent
    sandbox_python = workspace_root / "_sandboxes" / "chatdev-factory-prototype-smoke" / ".venv" / "Scripts" / "python.exe"
    repo_python = ROOT / ".venv" / "Scripts" / "python.exe"
    repo_gamedev_python = ROOT / ".venv-gamedev313" / "Scripts" / "python.exe"
    candidates: list[dict[str, Any]] = [
        {"label": "system_python", "command": ["python"]},
        {"label": "py_launcher_3", "command": ["py", "-3"]},
    ]
    if sandbox_python.exists():
        candidates.append({"label": "sandbox_venv", "command": [str(sandbox_python)]})
    if repo_python.exists():
        candidates.append({"label": "repo_venv", "command": [str(repo_python)]})
    if repo_gamedev_python.exists():
        candidates.append({"label": "repo_gamedev_venv", "command": [str(repo_gamedev_python)]})
    return candidates


def _gamedev_env_probe(timeout: float) -> list[dict[str, Any]]:
    results = []
    for candidate in _gamedev_python_candidates():
        result = _python_capability_probe(candidate["command"], timeout)
        result["label"] = candidate["label"]
        results.append(result)
    return results


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


def _startup_probe_port() -> int:
    configured = os.environ.get("CHATDEV_LOCAL_STARTUP_PORT")
    if configured:
        return int(configured)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


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


def _local_app_startup_probe(timeout: float) -> dict[str, Any]:
    startup_port = _startup_probe_port()
    startup_paths = ["/health", "/api/health", "/api/bridge/status", "/api/ecosystem/status"]
    startup_retry_paths = {"/api/bridge/status", "/api/ecosystem/status"}
    process: subprocess.Popen[str] | None = None
    log_handle: Any | None = None
    captured_output = ""
    started = time.perf_counter()
    try:
        env = os.environ.copy()
        env.setdefault("PYTHONUNBUFFERED", "1")
        log_dir = Path(tempfile.gettempdir()) / "chatdev-local-startup-smoke"
        log_dir.mkdir(parents=True, exist_ok=True)
        startup_log_path = log_dir / f"startup-{startup_port}.log"
        log_handle = startup_log_path.open("w+", encoding="utf-8", errors="replace")
        process = subprocess.Popen(
            [
                sys.executable,
                "server_main.py",
                "--host",
                "127.0.0.1",
                "--port",
                str(startup_port),
                "--log-level",
                "warning",
            ],
            cwd=str(ROOT),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

        health_url = f"http://127.0.0.1:{startup_port}/health"
        deadline = time.perf_counter() + max(timeout, 5.0)

        def _probe_startup_path(path: str) -> dict[str, Any]:
            route_timeout = max(timeout, STARTUP_ROUTE_TIMEOUTS.get(path, 1.0))
            attempts = 2 if path in startup_retry_paths else 1
            last_result: dict[str, Any] = {"ok": False, "error": "startup_probe_not_run"}
            for attempt in range(attempts):
                last_result = _probe(f"http://127.0.0.1:{startup_port}{path}", route_timeout)
                if last_result.get("ok") is True:
                    return last_result
                if attempt + 1 < attempts:
                    time.sleep(0.2)
            return last_result

        while time.perf_counter() < deadline:
            if process.poll() is not None:
                break
            try:
                probe = _probe(health_url, min(1.0, timeout))
                if probe.get("ok") is True:
                    path_results = {
                        path: _probe_startup_path(path)
                        for path in startup_paths
                    }
                    return {
                        "ok": True,
                        "port": startup_port,
                        "health_url": health_url,
                        "paths": path_results,
                        "log_path": str(startup_log_path),
                        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                        "output_tail": "",
                    }
            except Exception:
                pass
            time.sleep(0.2)

        timed_out = process.poll() is None
        if timed_out and process.poll() is None:
            with contextlib.suppress(Exception):
                process.terminate()
            with contextlib.suppress(Exception):
                process.wait(timeout=5)
            if process.poll() is None:
                with contextlib.suppress(Exception):
                    process.kill()
        if log_handle is not None:
            try:
                log_handle.flush()
                captured_output = startup_log_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                captured_output = ""
        return {
            "ok": False,
            "port": startup_port,
            "health_url": health_url,
            "error": "startup_timeout" if timed_out else f"startup_exit_{process.returncode}",
            "paths": {
                path: {"ok": False, "skipped": True, "reason": "startup_failed"}
                for path in startup_paths
            },
            "log_path": str(startup_log_path),
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "output_tail": captured_output[-1000:],
        }
    except Exception as exc:
        return {
            "ok": False,
            "port": startup_port,
            "error": f"{type(exc).__name__}: {str(exc)[:200]}",
            "paths": {
                path: {"ok": False, "skipped": True, "reason": "startup_exception"}
                for path in startup_paths
            },
            "log_path": str(startup_log_path) if 'startup_log_path' in locals() else None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "output_tail": captured_output[-1000:],
        }
    finally:
        if log_handle is not None:
            with contextlib.suppress(Exception):
                log_handle.close()
        if process is not None and process.poll() is None:
            with contextlib.suppress(Exception):
                process.terminate()
            with contextlib.suppress(Exception):
                process.wait(timeout=5)
            if process.poll() is None:
                with contextlib.suppress(Exception):
                    process.kill()


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
    local_startup_probe = (
        _local_app_startup_probe(timeout)
        if probes["chatdev_local"]["paths"]["/health"].get("ok") is not True and local.get("loaded") is True
        else {
            "ok": probes["chatdev_local"]["paths"]["/health"].get("ok") is True,
            "skipped": probes["chatdev_local"]["paths"]["/health"].get("ok") is True,
            "reason": "already_live" if probes["chatdev_local"]["paths"]["/health"].get("ok") is True else "local_app_not_loaded",
            "paths": {
                path: probes["chatdev_local"]["paths"].get(path, {"ok": False, "skipped": True, "reason": "missing_probe"})
                for path in PROBE_PATHS["chatdev_local"]
            },
        }
    )
    startup_paths = local_startup_probe.get("paths", {})
    local_core_routes_ready = all(
        startup_paths.get(path, {}).get("ok") is True
        for path in ("/health", "/api/health")
    )
    local_extended_routes_ready = all(
        startup_paths.get(path, {}).get("ok") is True
        for path in ("/api/bridge/status", "/api/ecosystem/status")
    )
    gamedev_env = _gamedev_env_probe(timeout)
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
            "local_app_bootable": local_startup_probe.get("ok") is True,
            "local_app_core_routes_ready": local_core_routes_ready,
            "local_app_extended_routes_ready": local_extended_routes_ready,
            "live_surface_id": live_surface_id,
            "live_surface_kind": live_surface_kind,
            "surface_mismatch_count": len(surface_mismatches),
            "route_drift_count": len(drift),
            "gamedev_python_with_pygame": [item["label"] for item in gamedev_env if item.get("pygame") is True],
        },
        "probes": probes,
        "local_routes": local,
        "local_startup_probe": local_startup_probe,
        "gamedev_env": gamedev_env,
        "drift": drift,
        "surface_mismatches": surface_mismatches,
        "notes": [
            "Use this instead of broad rg over ecosystem mirrors for first-pass ChatDev truth.",
            "A healthy :7338 service does not prove the local checkout routes are live in the container.",
            "If :7338 reports service_id=devmentor-chatdev-worker, ChatDev2 app-only routes are surface mismatches rather than route drift.",
            "GameDev pygame smoke truth depends on the selected Python lane; inspect gamedev_env before assuming the active venv is valid.",
        ],
    }


def build_local_proof(timeout: float = 2.0) -> dict[str, Any]:
    report = build_report(timeout=timeout)
    summary = report.get("summary", {})
    startup_probe = report.get("local_startup_probe", {})
    return {
        "generated_at": report.get("generated_at"),
        "root": report.get("root"),
        "summary": {
            "chatdev_local_health": summary.get("chatdev_local_health") is True,
            "local_app_loaded": summary.get("local_app_loaded") is True,
            "local_app_bootable": summary.get("local_app_bootable") is True,
            "local_app_core_routes_ready": summary.get("local_app_core_routes_ready") is True,
            "local_app_extended_routes_ready": summary.get("local_app_extended_routes_ready") is True,
        },
        "local_startup_probe": startup_probe,
        "next_action": (
            "start_local_devall_app"
            if summary.get("chatdev_local_health") is not True
            else "none"
        ),
        "notes": [
            "Use this bounded proof to distinguish a currently running :6400 app from a checkout that can boot and answer key routes locally.",
            "local_app_extended_routes_ready reflects /api/bridge/status plus /api/ecosystem/status during the temporary startup probe.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe ChatDev2 colony integration truth.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--local-proof", action="store_true", help="Return only the bounded local DevAll app proof payload.")
    parser.add_argument("--timeout", type=float, default=2.0, help="Per-request timeout in seconds.")
    args = parser.parse_args()

    report = build_local_proof(timeout=args.timeout) if args.local_proof else build_report(timeout=args.timeout)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        if args.local_proof:
            print("ChatDev2 local DevAll proof")
            print(f"  root: {report['root']}")
            print(f"  local health (:6400): {summary['chatdev_local_health']}")
            print(f"  local app loaded: {summary['local_app_loaded']}")
            print(f"  local app bootable: {summary['local_app_bootable']}")
            print(f"  local core routes ready: {summary['local_app_core_routes_ready']}")
            print(f"  local extended routes ready: {summary['local_app_extended_routes_ready']}")
            print(f"  next action: {report['next_action']}")
        else:
            print("ChatDev2 colony doctor")
            print(f"  root: {report['root']}")
            print(f"  colony health (:7338): {summary['chatdev_colony_health']}")
            print(f"  local health (:6400): {summary['chatdev_local_health']}")
            print(f"  local app loaded: {summary['local_app_loaded']}")
            print(f"  local app bootable: {summary['local_app_bootable']}")
            print(f"  live surface: {summary.get('live_surface_id') or 'unknown'} ({summary.get('live_surface_kind') or 'unknown'})")
            if not summary["local_app_loaded"]:
                print(f"  local app error: {report['local_routes'].get('error')}")
            print(f"  gamedev python lanes with pygame: {', '.join(summary['gamedev_python_with_pygame']) or 'none'}")
            print(f"  surface mismatch count: {summary['surface_mismatch_count']}")
            for item in report["surface_mismatches"]:
                print(f"  mismatch: {item['path']} local=true live_surface={summary.get('live_surface_id')}")
            print(f"  route drift count: {summary['route_drift_count']}")
            for item in report["drift"]:
                print(f"  drift: {item['path']} local=true live={item.get('live_status') or item.get('live_error')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
