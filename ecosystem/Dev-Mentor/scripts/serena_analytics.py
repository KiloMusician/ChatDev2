"""Serena Analytics — data science and ML agent.

Serena subscribes to Lattice events, analyses colony data,
embeds knowledge into the Lattice, and publishes insights.

In a full deployment this would wrap Ollama for embedding + analysis.
The stub here provides deterministic analytics useful immediately.

Usage:
    python scripts/serena_analytics.py --daemon
    python scripts/serena_analytics.py --analyse          # one-shot colony analysis
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import sys
import time
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


SERENA_HEALTH_PORT = int(os.getenv("SERENA_HEALTH_PORT", "3001"))

BASE = Path(__file__).parent.parent
STATE_DIR = BASE / "state"
LOG_DIR = BASE / "var"
LOG_DIR.mkdir(parents=True, exist_ok=True)

SERENA_DB = os.getenv("SERENA_DB", str(STATE_DIR / "serena_memory.db"))

# Use localhost:5000 when running natively in Replit (REPLIT_DEV_DOMAIN is set
# by the platform). The external HTTPS domain causes SSL errors from inside the
# same Repl; localhost bypasses the proxy entirely.
_REPLIT_NATIVE = bool(os.getenv("REPLIT_DEV_DOMAIN")) and not os.getenv(
    "GORDON_DOCKER_HOST"
)
TD_URL = os.getenv("TERMINAL_DEPTHS_URL") or (
    "http://localhost:5000" if _REPLIT_NATIVE else "http://localhost:8008"
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] SERENA %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "serena.log"),
    ],
)
log = logging.getLogger("serena")

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


# ─── Lattice DB (extends existing serena_memory.db) ──────────────────────────


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(SERENA_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lattice_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            channel   TEXT NOT NULL,
            data      TEXT NOT NULL,
            ts        TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lattice_insights (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            topic     TEXT NOT NULL,
            insight   TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            ts        TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS colony_states (
            agent_id  TEXT NOT NULL,
            data      TEXT NOT NULL,
            ts        TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (agent_id, ts)
        )
    """
    )
    conn.commit()
    return conn


def embed_event(channel: str, data: dict) -> None:
    """Store an event in the Lattice memory DB."""
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO lattice_events (channel, data, ts) VALUES (?,?,?)",
                (channel, json.dumps(data), _now()),
            )
    except Exception as e:
        log.debug(f"Embed failed: {e}")


def store_insight(topic: str, insight: str, confidence: float = 1.0) -> None:
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO lattice_insights (topic, insight, confidence, ts) "
                "VALUES (?,?,?,?)",
                (topic, insight, confidence, _now()),
            )
        publish("lattice.serena.insight", {"topic": topic, "insight": insight})
    except Exception as e:
        log.debug(f"Insight store failed: {e}")


# ─── Colony analytics ─────────────────────────────────────────────────────────


def analyse_colony() -> dict[str, Any]:
    """Pull colony state from Terminal Depths and generate analytics."""
    if not REQUESTS_OK:
        return {"error": "requests unavailable"}

    _passkey = os.getenv("NUSYQ_PASSKEY", "")
    _auth_headers = {"X-NuSyQ-Passkey": _passkey} if _passkey else {}

    try:
        r = requests.get(
            f"{TD_URL}/api/nusyq/colonist_state", timeout=8, headers=_auth_headers
        )
        if r.status_code != 200:
            return {"error": f"API returned {r.status_code}"}
        data = r.json()
        ids = data.get("agents", [])
    except Exception as e:
        return {"error": str(e)}

    states: list[dict] = []
    for aid in ids:
        try:
            ar = requests.get(
                f"{TD_URL}/api/nusyq/colonist_state/{aid}",
                timeout=5,
                headers=_auth_headers,
            )
            if ar.status_code == 200:
                states.append(ar.json())
        except Exception:
            pass

    if not states:
        return {"error": "no colonist states available"}

    avg_mood = sum(s.get("mood", 0.5) for s in states) / len(states)
    avg_health = sum(s.get("health", 1.0) for s in states) / len(states)
    downed = [s["name"] for s in states if s.get("is_downed")]
    mental = [s["name"] for s in states if s.get("is_mental_state")]

    # Generate recommendations
    recs: list[str] = []
    if avg_mood < 0.4:
        recs.append("Colony mood is critically low — schedule recreation or feast.")
    if downed:
        recs.append(f"Downed colonists require medical priority: {', '.join(downed)}.")
    if mental:
        recs.append(
            f"Mental break risk: {', '.join(mental)}. Relieve stress immediately."
        )
    if avg_health < 0.7:
        recs.append(
            "Average health below 70% — check for untreated injuries or illness."
        )
    if not recs:
        recs.append("Colony is stable. No immediate interventions required.")

    # Drift score (0.0 = stable, 1.0 = critical)
    drift = (1 - avg_mood) * 0.5 + (1 - avg_health) * 0.3 + len(downed) * 0.1
    drift = min(drift, 1.0)

    report = {
        "timestamp": _now(),
        "colonist_count": len(states),
        "avg_mood": round(avg_mood, 3),
        "avg_health": round(avg_health, 3),
        "drift_score": round(drift, 3),
        "downed": downed,
        "mental_break": mental,
        "recommendations": recs,
        "serena_verdict": (
            "critical" if drift > 0.7 else "warning" if drift > 0.4 else "nominal"
        ),
    }

    # Embed into Lattice
    store_insight("colony_analytics", json.dumps(report), confidence=0.9)
    publish("lattice.serena.colony_analytics", report)

    log.info(
        f"Colony analysis: drift={drift:.2f} mood={avg_mood:.2f} "
        f"colonists={len(states)} verdict={report['serena_verdict']}"
    )
    return report


# ─── Event subscriptions ──────────────────────────────────────────────────────


def subscribe_and_embed() -> None:
    """Listen for all lattice events and embed them in memory."""
    if not REDIS_OK or _r is None:
        log.warning("Redis unavailable — event embedding disabled")
        return

    pubsub = _r.pubsub()
    pubsub.psubscribe("lattice.*")
    log.info("Serena subscribed to lattice.*")

    for message in pubsub.listen():
        if message["type"] not in ("message", "pmessage"):
            continue
        channel = message.get("channel", "")
        try:
            data = json.loads(message.get("data", "{}"))
            embed_event(channel, data)

            # Analyse on crash events
            if "crash" in channel:
                log.info("Crash event received — embedding and queuing analysis")
                store_insight(
                    "crash_analysis",
                    f"Crash detected at {_now()}. Full analysis pending.",
                    confidence=0.5,
                )
        except Exception as e:
            log.debug(f"Subscription handler error: {e}")


# ─── Entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--daemon", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    args = ap.parse_args()

    log.info("Serena Analytics online. The Lattice grows.")
    get_conn()  # ensure tables exist

    if args.analyse:
        report = analyse_colony()
        print(json.dumps(report, indent=2))
        return

    if args.daemon:
        import threading

        start_health_server(
            SERENA_HEALTH_PORT,
            agent="Serena",
            version="1.0.0",
            extra={"role": "convergence_layer", "redis_ok": False},
        )
        t = threading.Thread(target=subscribe_and_embed, daemon=True)
        t.start()

        cycle = 0
        while True:
            cycle += 1
            if cycle % 4 == 0:  # every ~2 min
                try:
                    report = analyse_colony()
                    _hs_set(
                        {
                            "cycles": cycle,
                            "status": "ok",
                            "last_analysis": report.get("timestamp", ""),
                        }
                    )
                except Exception as e:
                    log.error(f"Analysis error: {e}")
                    _hs_set({"status": "degraded", "last_error": str(e)})
            else:
                _hs_set({"cycles": cycle})
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                break
    else:
        report = analyse_colony()
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
