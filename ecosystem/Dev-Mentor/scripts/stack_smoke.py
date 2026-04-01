#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[1]
PORT_MAP_PATH = BASE / "config" / "port_map.json"
DEFAULT_SERVICES = (
    "devmentor",
    "nusyq_hub",
    "nusyq_bridge",
    "model_router",
    "simulatedverse",
)

import os as _os

# In Replit the gateway runs on 5000, not the Docker port (7337).
# Downstream Docker services keep their port_map ports — they're just unreachable.
_IS_REPLIT = bool(
    _os.getenv("REPL_ID")
    or _os.getenv("REPLIT_DEV_DOMAIN")
    or _os.getenv("REPLIT_CLUSTER")
)
_REPLIT_PORT_OVERRIDES: dict[str, int] = {"devmentor": 5000} if _IS_REPLIT else {}


def load_port_map(path: Path = PORT_MAP_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_targets(
    selected_services: tuple[str, ...] = DEFAULT_SERVICES,
    path: Path = PORT_MAP_PATH,
) -> list[dict[str, Any]]:
    ports = load_port_map(path).get("ports", {})
    wanted = set(selected_services)
    targets: list[dict[str, Any]] = []
    for port, meta in ports.items():
        service = str(meta.get("service", "")).strip()
        if service not in wanted:
            continue
        health = str(meta.get("health", "/health"))
        external = int(_REPLIT_PORT_OVERRIDES.get(service, meta.get("external", port)))
        url = f"http://127.0.0.1:{external}{health}"
        targets.append(
            {
                "service": service,
                "name": meta.get("name", service),
                "url": url,
                "critical": bool(meta.get("critical", False)),
            }
        )
    targets.sort(key=lambda item: selected_services.index(item["service"]))
    return targets


def probe_target(target: dict[str, Any], timeout: float = 5.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(target["url"], timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            ok = 200 <= getattr(response, "status", 200) < 300
            parsed: dict[str, Any] | None = None
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = None
            if parsed is not None:
                status = str(parsed.get("status", "")).lower()
                if status and status not in {"ok", "healthy"}:
                    ok = False
                if "ready" in parsed and parsed.get("ready") is False:
                    ok = False
            return {
                **target,
                "ok": ok,
                "status": getattr(response, "status", 200),
                "body_preview": body[:200],
            }
    except urllib.error.HTTPError as exc:
        return {
            **target,
            "ok": False,
            "status": exc.code,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            **target,
            "ok": False,
            "status": None,
            "error": str(exc),
        }


def run_smoke(selected_services: tuple[str, ...], timeout: float) -> dict[str, Any]:
    targets = load_targets(selected_services)
    results = [probe_target(target, timeout=timeout) for target in targets]
    failed = [result for result in results if not result.get("ok")]
    return {
        "ok": not failed,
        "checked": len(results),
        "failed": len(failed),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check the live ecosystem stack")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument(
        "--services",
        default=",".join(DEFAULT_SERVICES),
        help="Comma-separated service ids from config/port_map.json",
    )
    parser.add_argument(
        "--timeout", type=float, default=5.0, help="Per-endpoint timeout in seconds"
    )
    args = parser.parse_args()

    selected_services = tuple(s.strip() for s in args.services.split(",") if s.strip())
    report = run_smoke(selected_services, timeout=args.timeout)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Stack smoke: {report['checked']} checked, {report['failed']} failed")
        for result in report["results"]:
            marker = "OK " if result.get("ok") else "FAIL"
            suffix = (
                f"status={result.get('status')}"
                if result.get("ok")
                else result.get("error", "unknown error")
            )
            print(f"  [{marker}] {result['service']:<14} {result['url']}  {suffix}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
