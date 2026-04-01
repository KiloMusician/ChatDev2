"""Gordon Orchestrator — the god-mode conductor of the Terminal Keeper Lattice.

Gordon monitors all services, detects failures (including RimWorld crashes),
delegates tasks to specialized agents, runs the CHUG engine, and
publishes events to the Redis pub/sub bus.

Usage:
    python scripts/gordon_orchestrator.py --mode daemon   # continuous
    python scripts/gordon_orchestrator.py --mode once     # single cycle
    python scripts/gordon_orchestrator.py --mode status   # print status and exit
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

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


GORDON_HEALTH_PORT = int(os.getenv("GORDON_HEALTH_PORT", "3000"))

# ─── Optional: Redis pub/sub ──────────────────────────────────────────────────
try:
    import redis as _redis_lib

    _redis = _redis_lib.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"),
        decode_responses=True,
    )
    _redis.ping()
    REDIS_OK = True
except Exception:
    _redis = None  # type: ignore
    REDIS_OK = False

# ─── Optional: requests ───────────────────────────────────────────────────────
try:
    import requests as _req

    REQUESTS_OK = True
except Exception:
    _req = None  # type: ignore
    REQUESTS_OK = False

# ─── Config ───────────────────────────────────────────────────────────────────

BASE = Path(__file__).parent.parent
STATE_DIR = BASE / "state"
LOG_DIR = BASE / "var"
LOG_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Replit runs on 5000; Docker runs on 7337 — detect automatically
_is_replit = bool(
    os.getenv("REPL_ID")
    or os.getenv("REPLIT_DEV_DOMAIN")
    or os.getenv("REPLIT_CLUSTER")
)
_td_default_port = 5000 if _is_replit else 7337
TD_URL = os.getenv("TERMINAL_DEPTHS_URL", f"http://localhost:{_td_default_port}")
_mr_host = "localhost" if _is_replit else "kilocore-model-router"
MODEL_ROUTER_URL = os.getenv("MODEL_ROUTER_URL", f"http://{_mr_host}:9001")
# KiloCore compose uses kilocore-* container names on kilocore-net.
# Replit falls back to localhost.
_h = "localhost" if _is_replit else "kilocore-{}"
_SERENA_URL = f"http://{_h.format('serena')}:3001/health"
_SERENA_BASE = _SERENA_URL.removesuffix("/health")  # base for /ask, /drift, etc.
_SKYCLAW_URL = f"http://{_h.format('skyclaw')}:3002/health"
_SHIP_URL = f"http://{_h.format('culture-ship')}:3003/health"
_NUSYQ_URL = f"http://{_h.format('nusyq-hub')}:8000"
# internal port 5000, mapped to host 5100
_SIMVERSE_URL = f"http://{_h.format('simulatedverse')}:5000"
_CHATDEV_URL = f"http://{_h.format('chatdev')}:7338"  # container-only
_OLLAMA_URL = f"http://{_h.format('ollama')}:11434"
CHECK_INT = int(os.getenv("GORDON_CHECK_INTERVAL", "30"))  # seconds
SNAPSHOT_INT = int(os.getenv("GORDON_SNAPSHOT_INTERVAL", "5"))  # N cycles

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] GORDON %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "gordon.log"),
    ],
)
log = logging.getLogger("gordon")


# ─── Service Registry ─────────────────────────────────────────────────────────


@dataclass
class ServiceDef:
    name: str
    url: str
    container: str | None = None
    critical: bool = False
    status: str = "unknown"
    last_check: str = ""
    fail_count: int = 0


SERVICES: list[ServiceDef] = [
    # ── Core infrastructure ───────────────────────────────────────────────────
    ServiceDef(
        "Terminal Depths", f"{TD_URL}/api/health", "kilocore-dev-mentor", critical=True
    ),
    ServiceDef("Ollama", f"{_OLLAMA_URL}/api/tags", "kilocore-ollama", critical=True),
    ServiceDef("Redis", "", "kilocore-redis", critical=True),
    ServiceDef("Postgres", "", "kilocore-postgres", critical=True),  # container-only
    # ── Orchestration & simulation ────────────────────────────────────────────
    ServiceDef("NuSyQ-Hub", f"{_NUSYQ_URL}/api/health", "kilocore-nusyq-hub"),
    ServiceDef("SimulatedVerse", f"{_SIMVERSE_URL}/health", "kilocore-simulatedverse"),
    ServiceDef("ChatDev", f"{_CHATDEV_URL}/health", "kilocore-chatdev"),
    ServiceDef(
        "Model Router",
        f"{MODEL_ROUTER_URL.rstrip('/')}/health",
        "kilocore-model-router",
    ),
    # ── Agent sidecars ────────────────────────────────────────────────────────
    ServiceDef("Serena", _SERENA_URL, "kilocore-serena"),
    ServiceDef("SkyClaw", _SKYCLAW_URL, "kilocore-skyclaw"),
    ServiceDef("Culture Ship", _SHIP_URL, "kilocore-culture-ship"),
    # ── Optional heavy services ───────────────────────────────────────────────
    ServiceDef("RimWorld API", "http://rimapi:8765/health", "terminal-depths-rimworld"),
]


# ─── Redis pub/sub helpers ────────────────────────────────────────────────────


def publish(channel: str, data: dict) -> None:
    """Publish a JSON event to Redis. No-op if Redis unavailable."""
    if not REDIS_OK or _redis is None:
        return
    try:
        _redis.publish(channel, json.dumps({**data, "_ts": _now()}))
    except Exception as e:
        log.debug(f"Redis publish failed: {e}")


def _now() -> str:
    return datetime.now(UTC).isoformat()


# ─── Service health checks ────────────────────────────────────────────────────


def check_http(url: str, timeout: int = 5) -> bool:
    if not REQUESTS_OK or not url:
        return True  # skip unconfigured
    try:
        r = _req.get(url, timeout=timeout)
        return r.status_code < 500
    except Exception:
        return False


def check_redis() -> bool:
    if not REDIS_OK or _redis is None:
        return False
    try:
        _redis.ping()
        return True
    except Exception:
        return False


def check_docker_container(name: str) -> str:
    """Returns 'running' | 'stopped' | 'not_found' | 'error'."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", name],
            capture_output=True,
            text=True,
            timeout=5,
        )
        status = result.stdout.strip()
        return status if status else "not_found"
    except FileNotFoundError:
        return "error"  # docker not available
    except Exception:
        return "error"


def health_cycle() -> dict[str, str]:
    """Run one full health check across all services."""
    results: dict[str, str] = {}

    for svc in SERVICES:
        svc.last_check = _now()

        if svc.name == "Redis":
            ok = check_redis()
        elif svc.url:
            ok = check_http(svc.url)
        elif svc.container:
            ok = check_docker_container(svc.container) == "running"
        else:
            ok = True  # unknown, assume ok

        prev = svc.status
        svc.status = "ok" if ok else "down"
        svc.fail_count = 0 if ok else svc.fail_count + 1

        results[svc.name] = svc.status

        if not ok and prev != "down":
            _on_service_down(svc)
        elif ok and prev == "down":
            log.info(f"✓ {svc.name} recovered")
            publish("lattice.service.recovered", {"service": svc.name})

    return results


def _on_service_down(svc: ServiceDef) -> None:
    log.warning(f"✗ {svc.name} is DOWN (fails={svc.fail_count})")
    publish("lattice.service.down", {"service": svc.name, "critical": svc.critical})

    if svc.container and svc.fail_count >= 3:
        _restart_container(svc)


def _restart_container(svc: ServiceDef) -> None:
    log.info(f"→ Restarting container {svc.container}")
    try:
        subprocess.run(
            ["docker", "restart", svc.container],
            timeout=30,
            check=True,
            capture_output=True,
        )
        svc.fail_count = 0
        publish("lattice.container.restarted", {"container": svc.container})
    except Exception as e:
        log.error(f"Failed to restart {svc.container}: {e}")


# ─── Federated snapshot ───────────────────────────────────────────────────────
# Pulls real state from all live surfaces into one dict, written to
# state/gordon_federated.json and published to lattice.gordon.snapshot.


def _get_json(url: str, timeout: int = 5) -> dict | None:
    """GET url, return parsed JSON or None on any error."""
    if not REQUESTS_OK:
        return None
    try:
        r = _req.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _post_json(url: str, body: dict, timeout: int = 5) -> dict | None:
    if not REQUESTS_OK:
        return None
    try:
        r = _req.post(url, json=body, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def federated_snapshot() -> dict:
    """Pull current state from all live surfaces in parallel. Returns unified dict."""
    snap: dict[str, Any] = {"timestamp": _now(), "surfaces": {}}
    _mr_base = MODEL_ROUTER_URL.rstrip("/")

    def _td():
        return "terminal_depths", (
            _get_json(f"{TD_URL}/api/game/state") or _get_json(f"{TD_URL}/api/health")
        )

    def _nusyq():
        return "nusyq_hub", {
            "health": _get_json(f"{_NUSYQ_URL}/api/health"),
            "agents": _get_json(f"{_NUSYQ_URL}/api/agents"),
        }

    def _simverse():
        return "simulatedverse", (
            _get_json(f"{_SIMVERSE_URL}/api/state")
            or _get_json(f"{_SIMVERSE_URL}/health")
        )

    def _serena():
        return "serena", {
            "drift": _get_json(f"{_SERENA_BASE}/drift"),
            "memory": _post_json(
                f"{_SERENA_BASE}/ask",
                {"query": "what are the most recent events?", "limit": 5},
            ),
        }

    def _model_router():
        return "model_router", (
            _get_json(f"{_mr_base}/api/models") or _get_json(f"{_mr_base}/health")
        )

    def _ollama():
        return "ollama", _get_json(f"{_OLLAMA_URL}/api/tags")

    def _lattice():
        return "lattice", (
            _get_json("http://localhost:9101/api/lattice/stats")
            or _get_json("http://localhost:9101/health")
        )

    def _keeper():
        keeper_root = os.getenv("KEEPER_ROOT", r"C:\CONCEPT")
        bridge = Path(keeper_root) / "tools" / "keeper-bridge.ps1"
        if not bridge.exists():
            return "keeper", {"note": "keeper-bridge.ps1 not found"}
        try:
            r = subprocess.run(
                [
                    "pwsh",
                    "-NoLogo",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(bridge),
                    "snapshot",
                ],
                capture_output=True,
                text=True,
                timeout=12,
            )
            if r.returncode == 0 and r.stdout.strip():
                return "keeper", json.loads(r.stdout.strip())
            return "keeper", {"error": f"rc={r.returncode}"}
        except Exception as e:
            return "keeper", {"error": str(e)}

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [
            pool.submit(fn)
            for fn in (
                _td,
                _nusyq,
                _simverse,
                _serena,
                _model_router,
                _ollama,
                _lattice,
                _keeper,
            )
        ]
        for fut in futures:
            try:
                key, val = fut.result(timeout=20)
                snap["surfaces"][key] = val
            except Exception as e:
                log.debug(f"Surface fetch failed: {e}")

    snap_path = STATE_DIR / "gordon_federated.json"
    try:
        snap_path.write_text(json.dumps(snap, indent=2, default=str))
    except Exception as e:
        log.debug(f"Could not write federated snapshot: {e}")

    publish(
        "lattice.gordon.snapshot",
        {
            "surfaces": list(snap["surfaces"].keys()),
            "ts": snap["timestamp"],
        },
    )
    surfaces = ", ".join(snap["surfaces"].keys())
    log.info(f"Federated snapshot written — surfaces: {surfaces}")
    return snap


# ─── RimWorld crash detection ─────────────────────────────────────────────────

_RIMWORLD_LAST_STATUS: str = "unknown"

CRASH_NARRATIVE: list[str] = [
    "[WATCHER]: A fracture has occurred in colony simulation. The fabric shudders.",
    "[ADA-7]: Gordon, I'm reading an abnormal termination in the colony layer. Investigating.",
    "[CYPHER]: Even simulations have bad days. Let's see what broke.",
    "[SERENA]: Indexing crash event into the Lattice. Root cause analysis starting.",
]


def check_rimworld() -> None:
    global _RIMWORLD_LAST_STATUS
    status = check_docker_container("terminal-depths-rimworld")

    if status == "not_found":
        return  # RimWorld not running, skip

    if status != "running" and _RIMWORLD_LAST_STATUS == "running":
        log.warning("RimWorld container exited unexpectedly — crash detected!")
        _on_rimworld_crash()

    _RIMWORLD_LAST_STATUS = status


def _on_rimworld_crash() -> None:
    log.info("Triggering RimWorld crash narrative pipeline...")

    # Fetch crash log from container if available
    crash_log = _get_rimworld_crash_log()

    event_data = {
        "type": "colony_crash",
        "timestamp": _now(),
        "crash_log": crash_log[:2000] if crash_log else None,
        "narrative": CRASH_NARRATIVE,
    }

    publish("lattice.rimworld.crash", event_data)

    # Notify Terminal Depths so it can inject a quest / message to the player
    if REQUESTS_OK:
        try:
            _req.post(
                f"{TD_URL}/api/game/command",
                json={"command": "crash_event", "source": "gordon", **event_data},
                timeout=5,
            )
        except Exception:
            pass

    # Ask ChatDev / Serena to analyse and propose a fix
    publish(
        "lattice.task.created",
        {
            "task": "Analyse RimWorld crash and propose fix",
            "priority": "P0",
            "assignee": "chatdev",
            "context": crash_log[:500] if crash_log else "no log available",
        },
    )


def _get_rimworld_crash_log() -> str:
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", "100", "terminal-depths-rimworld"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (result.stdout + result.stderr).strip()
    except Exception:
        return ""


# ─── Task delegation ──────────────────────────────────────────────────────────


def delegate_task(
    task: str, assignee: str, priority: str = "P1", context: str = ""
) -> None:
    """Publish a task to the Lattice task queue."""
    log.info(f"→ Delegating [{priority}] '{task}' to {assignee}")
    publish(
        "lattice.task.created",
        {
            "task": task,
            "assignee": assignee,
            "priority": priority,
            "context": context,
        },
    )


# ─── CHUG engine hook ─────────────────────────────────────────────────────────


def run_chug_cycle() -> None:
    """Signal the CHUG engine to run an improvement cycle."""
    if REQUESTS_OK:
        try:
            _req.post(
                f"{TD_URL}/api/chug/cycle",
                json={"trigger": "gordon_orchestrator"},
                timeout=5,
            )
            log.info("CHUG cycle triggered")
        except Exception as e:
            log.debug(f"CHUG cycle skipped: {e}")


# ─── Status report ────────────────────────────────────────────────────────────


def print_status(results: dict[str, str]) -> None:
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║           GORDON ORCHESTRATOR — STATUS               ║")
    print("╠══════════════════════════════════════════════════════╣")
    for name, status in results.items():
        icon = "✓" if status == "ok" else "✗"
        color_on = "\033[32m" if status == "ok" else "\033[31m"
        color_off = "\033[0m"
        print(
            f"║  {color_on}{icon}{color_off} {name:<38} {color_on}{status:<6}{color_off}  ║"
        )
    redis_label = "Redis pub/sub" + (" (connected)" if REDIS_OK else " (unavailable)")
    print(f"║  {'·'} {redis_label:<46}║")
    print("╚══════════════════════════════════════════════════════╝\n")


# ─── Main loop ────────────────────────────────────────────────────────────────


def daemon_loop() -> None:
    log.info("Gordon orchestrator starting — The grid awakens.")
    start_health_server(
        GORDON_HEALTH_PORT,
        agent="Gordon",
        version="1.0.0",
        extra={"redis_ok": REDIS_OK, "role": "orchestrator"},
    )
    publish("lattice.gordon.online", {"status": "starting"})

    cycle = 0
    while True:
        try:
            cycle += 1
            log.info(f"--- Cycle {cycle} ---")

            results = health_cycle()
            check_rimworld()

            # Every SNAPSHOT_INT cycles: pull full federated state from all surfaces
            federated: dict = {}
            if cycle % SNAPSHOT_INT == 0:
                federated = federated_snapshot()

            # Every 10 cycles: trigger CHUG + delegate low-priority work
            if cycle % 10 == 0:
                run_chug_cycle()
                delegate_task("Prune stale Lattice nodes", "serena", "P2")

            # Save status to state file for Control Hub
            status_path = STATE_DIR / "gordon_status.json"
            payload = {
                "cycle": cycle,
                "timestamp": _now(),
                "services": results,
                "redis_ok": REDIS_OK,
                "federated": {
                    k: (
                        "ok"
                        if (v and "error" not in v and "note" not in v)
                        else "unavailable"
                    )
                    for k, v in federated.get("surfaces", {}).items()
                },
            }
            status_path.write_text(json.dumps(payload, indent=2))

            # Update health endpoint with live data
            _hs_set(
                {
                    "cycles": cycle,
                    "redis_ok": REDIS_OK,
                    "services": results,
                    "status": "ok",
                    "federated_surfaces": list(federated.get("surfaces", {}).keys()),
                }
            )

        except KeyboardInterrupt:
            log.info("Gordon shutting down.")
            publish("lattice.gordon.offline", {})
            break
        except Exception as e:
            log.error(f"Cycle error: {e}")

        time.sleep(CHECK_INT)


# ─── Entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser(description="Gordon Orchestrator")
    ap.add_argument("--mode", choices=["daemon", "once", "status"], default="once")
    args = ap.parse_args()

    if args.mode == "status":
        results = health_cycle()
        print_status(results)
    elif args.mode == "once":
        results = health_cycle()
        check_rimworld()
        snap = federated_snapshot()
        print_status(results)
        log.info(
            f"Single cycle complete. Federated surfaces: {', '.join(snap['surfaces'].keys())}"
        )
    else:
        daemon_loop()


if __name__ == "__main__":
    main()
