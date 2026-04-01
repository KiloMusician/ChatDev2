"""SkyClaw Scanner — autonomous threat and resource detection agent.

SkyClaw watches:
  - Network endpoints (service health)
  - File system changes (new saves, crash logs)
  - Redis streams (for anomalous event patterns)
  - Colony API (for unusual colonist states)

Publishes findings to:
  - Redis: lattice.skyclaw.discovery, lattice.skyclaw.alert

Usage:
    python scripts/skyclaw_scanner.py --daemon
    python scripts/skyclaw_scanner.py --scan once
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import UTC, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.backend import service_registry

from core.process_discovery import scan_processes as discover_processes
from core.process_discovery import sync_processes_to_registry

# ─── Health server (stdlib-only, works offline) ───────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
try:
    from health_server import set_status as _hs_set
    from health_server import start_health_server
except ImportError:

    def start_health_server(*a, **kw):
        pass  # type: ignore

    def _hs_set(*a, **kw):
        pass  # type: ignore


SKYCLAW_HEALTH_PORT = int(os.getenv("SKYCLAW_HEALTH_PORT", "3002"))

BASE = ROOT
STATE_DIR = BASE / "state"
LOG_DIR = BASE / "var"
LOG_DIR.mkdir(parents=True, exist_ok=True)

SCAN_INTERVAL = int(os.getenv("SKYCLAW_SCAN_INTERVAL", "300"))
PROCESS_STALE_SECONDS = int(os.getenv("SKYCLAW_PROCESS_STALE_SECONDS", "300"))
TD_URL = os.getenv("TERMINAL_DEPTHS_URL", "http://localhost:7337")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] SKYCLAW %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "skyclaw.log"),
    ],
)
log = logging.getLogger("skyclaw")

# ─── Redis ────────────────────────────────────────────────────────────────────
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

try:
    import requests

    REQUESTS_OK = True
except Exception:
    requests = None
    REQUESTS_OK = False


def publish(channel: str, data: dict) -> None:
    if not REDIS_OK or _r is None:
        return
    try:
        _r.publish(channel, json.dumps({**data, "_ts": _now()}))
    except Exception:
        pass


def _now() -> str:
    return datetime.now(UTC).isoformat()


# ─── File system scanner ──────────────────────────────────────────────────────

_file_hashes: dict[str, str] = {}


def scan_filesystem() -> list[dict]:
    findings = []
    watch_paths = [
        BASE / "state",
        BASE / "var",
        Path("/rimworld/saves") if Path("/rimworld").exists() else None,
    ]

    for base_path in watch_paths:
        if base_path is None or not base_path.exists():
            continue
        for p in base_path.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix in (".pyc", ".log") and p.stat().st_size == 0:
                continue
            try:
                sig = f"{p.stat().st_mtime}:{p.stat().st_size}"
                prev = _file_hashes.get(str(p))
                if prev != sig:
                    _file_hashes[str(p)] = sig
                    if prev is not None:
                        findings.append(
                            {
                                "type": "file_changed",
                                "path": str(p),
                                "size": p.stat().st_size,
                            }
                        )
            except Exception:
                pass

    return findings


# ─── Colony state anomaly detection ──────────────────────────────────────────

_prev_colony: dict = {}


def scan_colony_state() -> list[dict]:
    if not REQUESTS_OK:
        return []
    findings = []
    try:
        resp = requests.get(f"{TD_URL}/api/nusyq/colonist_state", timeout=5)
        if resp.status_code != 200:
            return []
        data = resp.json()
        agents = data.get("agents", [])

        for agent_id in agents:
            try:
                ar = requests.get(
                    f"{TD_URL}/api/nusyq/colonist_state/{agent_id}", timeout=5
                )
                if ar.status_code != 200:
                    continue
                state = ar.json()
                prev = _prev_colony.get(agent_id, {})

                # Detect mood crash
                mood = state.get("mood", 1.0)
                if mood < 0.2 and prev.get("mood", 1.0) >= 0.2:
                    findings.append(
                        {
                            "type": "colonist_mood_crash",
                            "agent": agent_id,
                            "mood": mood,
                        }
                    )

                # Detect downed colonist
                if state.get("is_downed") and not prev.get("is_downed"):
                    findings.append(
                        {
                            "type": "colonist_downed",
                            "agent": agent_id,
                        }
                    )

                _prev_colony[agent_id] = state
            except Exception:
                pass

    except Exception as e:
        log.debug(f"Colony scan failed: {e}")

    return findings


# ─── Crash log watcher ────────────────────────────────────────────────────────

CRASH_KEYWORDS = [
    "Fatal",
    "NullReferenceException",
    "OutOfMemoryException",
    "UnityException",
    "StackOverflow",
    "Access violation",
]


def scan_crash_logs() -> list[dict]:
    findings = []
    crash_dir = BASE / "var"
    for log_path in crash_dir.glob("*.log"):
        try:
            lines = log_path.read_text(errors="replace").splitlines()[-50:]
            for line in lines:
                for kw in CRASH_KEYWORDS:
                    if kw in line:
                        findings.append(
                            {
                                "type": "crash_keyword_detected",
                                "source": log_path.name,
                                "keyword": kw,
                                "line": line[:200],
                            }
                        )
                        break
        except Exception:
            pass
    return findings


# ─── Main scan cycle ──────────────────────────────────────────────────────────


def run_scan(process_stale_seconds: int = PROCESS_STALE_SECONDS) -> dict:
    log.info("Running scan cycle...")
    all_findings: list[dict] = []
    process_sync = {"status": "skipped", "seen": 0, "ecosystem": 0, "pruned": 0}

    all_findings += scan_filesystem()
    all_findings += scan_colony_state()
    all_findings += scan_crash_logs()

    try:
        service_registry.initialise()
        processes = discover_processes()
        sync_summary = sync_processes_to_registry(
            processes,
            stale_seconds=process_stale_seconds,
        )
        process_sync = {"status": "ok", **sync_summary}
        publish("lattice.skyclaw.discovery", {"type": "process_sync", **process_sync})
        log.info(
            "Process sync complete: seen=%s ecosystem=%s pruned=%s",
            process_sync["seen"],
            process_sync["ecosystem"],
            process_sync["pruned"],
        )
    except Exception as exc:
        process_sync = {
            "status": "error",
            "error": str(exc),
            "seen": 0,
            "ecosystem": 0,
            "pruned": 0,
        }
        publish(
            "lattice.skyclaw.alert", {"type": "process_sync_failed", "error": str(exc)}
        )
        log.warning("Process sync failed: %s", exc)

    for f in all_findings:
        severity = (
            "alert"
            if f["type"] in ("crash_keyword_detected", "colonist_downed")
            else "discovery"
        )
        channel = f"lattice.skyclaw.{severity}"
        publish(channel, f)
        log.info(f"[{severity.upper()}] {f['type']}: {json.dumps(f)[:100]}")

    # Save map
    scan_result = {
        "timestamp": _now(),
        "findings": len(all_findings),
        "process_sync": process_sync,
        "detail": all_findings[:20],
    }
    (STATE_DIR / "skyclaw_scan.json").write_text(json.dumps(scan_result, indent=2))
    return scan_result


# ─── Entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--daemon", action="store_true")
    ap.add_argument("--scan", choices=["once"])
    ap.add_argument("--process-scan-interval", type=int, default=None)
    ap.add_argument("--process-stale-seconds", type=int, default=PROCESS_STALE_SECONDS)
    args = ap.parse_args()
    scan_interval = args.process_scan_interval or SCAN_INTERVAL

    if args.daemon:
        log.info("SkyClaw daemon starting. The eye is open.")
        start_health_server(
            SKYCLAW_HEALTH_PORT,
            agent="SkyClaw",
            version="1.0.0",
            extra={"role": "anomaly_scanner", "redis_ok": REDIS_OK},
        )
        scan_count = 0
        while True:
            try:
                result = run_scan(process_stale_seconds=args.process_stale_seconds)
                scan_count += 1
                _hs_set(
                    {
                        "cycles": scan_count,
                        "status": "ok",
                        "redis_ok": REDIS_OK,
                        "last_scan": result.get("timestamp", ""),
                        "anomalies": result.get("anomaly_count", 0),
                        "process_sync": result.get("process_sync", {}).get(
                            "status", "unknown"
                        ),
                    }
                )
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"Scan error: {e}")
                _hs_set({"status": "degraded", "last_error": str(e)})
            time.sleep(scan_interval)
    else:
        result = run_scan(process_stale_seconds=args.process_stale_seconds)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
