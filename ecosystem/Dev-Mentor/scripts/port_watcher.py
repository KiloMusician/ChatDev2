"""port_watcher.py — Deterministic port-health watchdog.

Reads config/port_map.json, probes every declared local port with a TCP
connect (stdlib only — no requests, no psutil, no AI), and:

  1. Writes a live status snapshot to state/port_status.json
  2. Appends unresolved gaps to MASTER_ZETA_TODO.md (if it exists)
  3. Publishes lattice.ports.status events to Redis (if Redis is reachable)
  4. Logs startup-command hints for any port that is dark

This script is intentionally AI-free.  It is the floor, not the ceiling.

Usage:
    python scripts/port_watcher.py              # single scan, print report
    python scripts/port_watcher.py --daemon     # continuous loop (60s interval)
    python scripts/port_watcher.py --fix        # print start-commands for dark ports
    python scripts/port_watcher.py --todo       # append gaps to MASTER_ZETA_TODO.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import socket
import sys
import time
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

BASE = Path(__file__).parent.parent
STATE_DIR = BASE / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = BASE / "var"
LOG_DIR.mkdir(parents=True, exist_ok=True)
CFG_PATH = BASE / "config" / "port_map.json"

WATCH_INTERVAL = int(os.getenv("PORT_WATCH_INTERVAL", "60"))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] PORTWATCHER %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "port_watcher.log"),
    ],
)
log = logging.getLogger("port_watcher")

# ─── Optional Redis ───────────────────────────────────────────────────────────
try:
    import redis as _redis_lib

    _r = _redis_lib.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
    )
    _r.ping()
    REDIS_OK = True
except Exception:
    _r = None
    REDIS_OK = False


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _load_port_map() -> dict[str, Any]:
    try:
        with open(CFG_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        log.error(f"Port map not found: {CFG_PATH}")
        return {}
    except json.JSONDecodeError as e:
        log.error(f"Port map JSON error: {e}")
        return {}


def _probe(host: str, port: int, timeout: float = 1.5) -> bool:
    """Pure stdlib TCP connect probe — works offline, no deps."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError, TimeoutError):
        return False


def scan_all() -> dict[str, Any]:
    """Probe every port in port_map.json, return structured report."""
    pm = _load_port_map()
    ports_cfg = pm.get("ports", {})
    offline_core = set(pm.get("offline_core", []))
    ai_amplifiers = set(pm.get("ai_amplifiers", []))

    results: dict[str, Any] = {}
    alive_count = 0
    dark_count = 0
    critical_dark: list[str] = []

    for ext_port, info in ports_cfg.items():
        local_port = info.get("local_port", int(ext_port))
        name = info.get("name", ext_port)
        critical = info.get("critical", False)
        ai_req = info.get("ai_required", False)
        script = info.get("script")
        health_ep = info.get("health", "/health")
        note = info.get("note", "")

        alive = _probe("localhost", local_port)

        tier = (
            "offline_core"
            if ext_port in offline_core
            else "ai_amplifier" if ext_port in ai_amplifiers else "optional"
        )

        entry = {
            "name": name,
            "local_port": local_port,
            "ext_port": int(ext_port),
            "alive": alive,
            "critical": critical,
            "ai_required": ai_req,
            "tier": tier,
            "health_ep": health_ep,
            "start_cmd": script,
            "note": note,
            "checked_at": _now(),
        }
        results[ext_port] = entry

        if alive:
            alive_count += 1
        else:
            dark_count += 1
            if critical:
                critical_dark.append(name)
            log.warning(f"DARK  port {local_port:5d}  [{tier:12s}]  {name}")

    log.info(
        f"Scan complete — {alive_count} alive, {dark_count} dark, "
        f"{len(critical_dark)} critical dark"
    )

    return {
        "timestamp": _now(),
        "alive": alive_count,
        "dark": dark_count,
        "critical_dark": critical_dark,
        "ports": results,
    }


def save_status(report: dict) -> None:
    out = STATE_DIR / "port_status.json"
    out.write_text(json.dumps(report, indent=2))
    log.info(f"Status saved → {out}")
    # Write port_gaps.json — dark port list for Serena/Gordon consumption
    _save_gaps(report)


def _save_gaps(report: dict) -> None:
    """Write state/port_gaps.json with only the dark ports for agent consumption."""
    dark_ports = {
        k: v for k, v in report.get("ports", {}).items() if not v.get("alive")
    }
    gaps = {
        "timestamp": report.get("timestamp"),
        "dark_count": len(dark_ports),
        "critical_dark": report.get("critical_dark", []),
        "gaps": [
            {
                "name": v["name"],
                "port": v["local_port"],
                "tier": v["tier"],
                "start_cmd": v.get("start_cmd"),
            }
            for v in dark_ports.values()
        ],
    }
    _gap_path = STATE_DIR / "port_gaps.json"
    _gap_path.write_text(json.dumps(gaps, indent=2))
    log.debug(f"Gaps saved → {_gap_path}  ({len(dark_ports)} dark)")


def publish_to_redis(report: dict) -> None:
    if not REDIS_OK or _r is None:
        return
    try:
        summary = {
            "timestamp": report["timestamp"],
            "alive": report["alive"],
            "dark": report["dark"],
            "critical_dark": report["critical_dark"],
        }
        _r.publish("lattice.ports.status", json.dumps(summary))
        _r.set("lattice:ports:last_scan", json.dumps(summary), ex=300)
    except Exception as e:
        log.debug(f"Redis publish failed: {e}")


def print_report(report: dict) -> None:
    ports = report["ports"]
    print(f"\n{'═'*70}")
    print(f"  PORT WATCHER — {report['timestamp']}")
    print(
        f"  Alive: {report['alive']}  Dark: {report['dark']}  "
        f"Critical dark: {len(report['critical_dark'])}"
    )
    print(f"{'═'*70}")
    for ext, info in sorted(ports.items(), key=lambda x: int(x[0])):
        icon = "✓" if info["alive"] else "✗"
        tier = info["tier"][:6].upper()
        lp = info["local_port"]
        name = info["name"][:45]
        status = "ALIVE" if info["alive"] else "DARK "
        print(f"  {icon} :{lp:<5}  [{tier:6s}]  {status}  {name}")
    print(f"{'═'*70}\n")


def print_fix_hints(report: dict) -> None:
    dark = [(e, i) for e, i in report["ports"].items() if not i["alive"]]
    if not dark:
        print("All ports alive. Nothing to fix.")
        return
    print(f"\n{'─'*60}")
    print("  DARK PORTS — start commands:")
    print(f"{'─'*60}")
    for ext, info in sorted(dark, key=lambda x: int(x[0])):
        cmd = info.get("start_cmd") or "# no start command defined"
        print(f"\n  [{info['name']}]  :{info['local_port']}")
        print(f"  $ {cmd}")
    print(f"\n{'─'*60}\n")


def append_todo(report: dict) -> None:
    """Append unresolved dark ports to MASTER_ZETA_TODO.md."""
    todo_paths = [
        BASE / "MASTER_ZETA_TODO.md",
        BASE / "todo.md",
    ]
    dark = [
        (e, i)
        for e, i in report["ports"].items()
        if not i["alive"] and not i.get("ai_required", False)
    ]
    if not dark:
        log.info("No deterministic dark ports to add to TODO.")
        return

    block = [
        f"\n### Port Watcher — {report['timestamp']}",
        "<!-- auto-generated by scripts/port_watcher.py -->",
        "",
    ]
    for ext, info in sorted(dark, key=lambda x: int(x[0])):
        tier = info["tier"]
        block.append(
            f"- [ ] **{info['name']}** (:{info['local_port']}) "
            f"[{tier}] — start: `{info.get('start_cmd') or 'TBD'}`"
        )
    block.append("")

    block_text = "\n".join(block)

    for path in todo_paths:
        if path.exists():
            with open(path, "a") as f:
                f.write(block_text)
            log.info(f"Appended {len(dark)} dark-port tasks → {path}")
            return

    # Neither file exists — create todo.md
    (BASE / "todo.md").write_text(f"# Port Watcher TODO\n{block_text}")
    log.info(f"Created todo.md with {len(dark)} dark-port tasks")


def daemon_loop() -> None:
    # ── Import health server to expose watcher status itself ─────────────────
    try:
        from health_server import set_status as _hs_set
        from health_server import start_health_server
    except ImportError:

        def start_health_server(*a, **kw):
            pass  # type: ignore

        def _hs_set(*a, **kw):
            pass  # type: ignore

    watcher_port = int(os.getenv("PORT_WATCHER_HEALTH_PORT", "0"))  # 0 = disabled
    if watcher_port:
        start_health_server(watcher_port, agent="PortWatcher", version="1.0.0")

    log.info(f"Port Watcher daemon starting — scanning every {WATCH_INTERVAL}s")
    scan_n = 0
    while True:
        try:
            report = scan_all()
            save_status(report)
            publish_to_redis(report)
            scan_n += 1
            if watcher_port:
                _hs_set(
                    {
                        "cycles": scan_n,
                        "alive": report["alive"],
                        "dark": report["dark"],
                        "critical_dark": report["critical_dark"],
                    }
                )
        except KeyboardInterrupt:
            log.info("Port Watcher shutting down.")
            break
        except Exception as e:
            log.error(f"Watcher cycle error: {e}")
        try:
            time.sleep(WATCH_INTERVAL)
        except KeyboardInterrupt:
            break


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Port Watcher — deterministic port scanner"
    )
    ap.add_argument("--daemon", action="store_true", help="Run continuously")
    ap.add_argument(
        "--fix", action="store_true", help="Print start commands for dark ports"
    )
    ap.add_argument(
        "--todo", action="store_true", help="Append dark ports to MASTER_ZETA_TODO.md"
    )
    ap.add_argument("--json", action="store_true", help="Output raw JSON report")
    args = ap.parse_args()

    if args.daemon:
        daemon_loop()
        return

    report = scan_all()
    save_status(report)
    publish_to_redis(report)

    if args.json:
        print(json.dumps(report, indent=2))
    elif args.fix:
        print_fix_hints(report)
    elif args.todo:
        append_todo(report)
    else:
        print_report(report)


if __name__ == "__main__":
    main()
