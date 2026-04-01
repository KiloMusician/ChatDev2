"""
Feature Store — SQLite time-series of game / agent events.

Records player actions, XP gains, story beats, quest completions, and
system events. Used by the Player Model and Culture Ship for inference.

Msg⛛ protocol: [ML⛛{feature}]

Tables:
  feature_events  — raw event stream
  player_profiles — aggregated player stats per session
  session_summary — per-session final state

API:
  record(session_id, event_type, features)
  get_session_features(session_id, limit)
  get_player_profile(session_id)
  predict_next_action(session_id)  — heuristic, no heavy ML needed
"""
from __future__ import annotations

import json
import math
import sqlite3
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _ROOT / "state" / "feature_store.db"

_DDL = """
CREATE TABLE IF NOT EXISTS feature_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    features    TEXT,       -- JSON dict
    ts          REAL
);
CREATE INDEX IF NOT EXISTS idx_fe_session ON feature_events(session_id, ts);

CREATE TABLE IF NOT EXISTS player_profiles (
    session_id      TEXT PRIMARY KEY,
    commands_run    INTEGER DEFAULT 0,
    xp_total        INTEGER DEFAULT 0,
    beats_triggered INTEGER DEFAULT 0,
    quests_done     INTEGER DEFAULT 0,
    playtime_s      REAL DEFAULT 0,
    top_commands    TEXT,   -- JSON list
    last_updated    REAL
);

CREATE TABLE IF NOT EXISTS session_summary (
    session_id  TEXT PRIMARY KEY,
    level       INTEGER,
    final_xp    INTEGER,
    story_pct   REAL,
    completed   INTEGER DEFAULT 0,
    ts          REAL
);
"""

_INTERESTING_EVENTS = {
    "command", "beat_triggered", "xp_gain", "quest_complete",
    "level_up", "npc_talk", "faction_join", "achievement",
    "loop_reset", "fragment_collect",
}


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def _init_db() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        c.executescript(_DDL)


# ── Write ─────────────────────────────────────────────────────────────────────

def record(session_id: str, event_type: str, features: Dict[str, Any]) -> None:
    if event_type not in _INTERESTING_EVENTS:
        return
    with _conn() as c:
        c.execute(
            "INSERT INTO feature_events (session_id, event_type, features, ts) VALUES (?,?,?,?)",
            (session_id, event_type, json.dumps(features), time.time()),
        )
        c.commit()
    _update_profile(session_id, event_type, features)


def _update_profile(session_id: str, event_type: str, features: Dict) -> None:
    with _conn() as c:
        existing = c.execute(
            "SELECT * FROM player_profiles WHERE session_id=?", (session_id,)
        ).fetchone()
        now = time.time()
        if not existing:
            c.execute(
                """INSERT INTO player_profiles
                   (session_id, commands_run, xp_total, beats_triggered,
                    quests_done, top_commands, last_updated)
                   VALUES (?,0,0,0,0,?,?)""",
                (session_id, json.dumps([]), now),
            )
            c.commit()
            existing = c.execute(
                "SELECT * FROM player_profiles WHERE session_id=?", (session_id,)
            ).fetchone()

        cmds = existing["commands_run"]
        xp = existing["xp_total"]
        beats = existing["beats_triggered"]
        quests = existing["quests_done"]
        top_raw = json.loads(existing["top_commands"] or "[]")
        top = Counter({v[0]: v[1] for v in top_raw})

        if event_type == "command":
            cmds += 1
            cmd_name = features.get("cmd", "unknown")
            top[cmd_name] = top.get(cmd_name, 0) + 1
        elif event_type == "xp_gain":
            xp += int(features.get("amount", 0))
        elif event_type == "beat_triggered":
            beats += 1
        elif event_type == "quest_complete":
            quests += 1

        top_list = [[k, v] for k, v in top.most_common(10)]
        c.execute(
            """UPDATE player_profiles SET
               commands_run=?, xp_total=?, beats_triggered=?,
               quests_done=?, top_commands=?, last_updated=?
               WHERE session_id=?""",
            (cmds, xp, beats, quests, json.dumps(top_list), now, session_id),
        )
        c.commit()


# ── Read ──────────────────────────────────────────────────────────────────────

def get_session_features(session_id: str, limit: int = 50) -> List[Dict]:
    with _conn() as c:
        rows = c.execute(
            """SELECT event_type, features, ts FROM feature_events
               WHERE session_id=? ORDER BY ts DESC LIMIT ?""",
            (session_id, limit),
        ).fetchall()
    result = []
    for r in rows:
        feat = json.loads(r["features"] or "{}")
        result.append({"type": r["event_type"], "ts": r["ts"], **feat})
    return result


def get_player_profile(session_id: str) -> Optional[Dict]:
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM player_profiles WHERE session_id=?", (session_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["top_commands"] = json.loads(d.get("top_commands") or "[]")
    return d


def global_stats() -> Dict:
    with _conn() as c:
        total_events = c.execute("SELECT COUNT(*) FROM feature_events").fetchone()[0]
        sessions = c.execute(
            "SELECT COUNT(DISTINCT session_id) FROM feature_events"
        ).fetchone()[0]
        top_event_types = c.execute(
            """SELECT event_type, COUNT(*) as n FROM feature_events
               GROUP BY event_type ORDER BY n DESC LIMIT 5"""
        ).fetchall()
    return {
        "total_events": total_events,
        "unique_sessions": sessions,
        "top_event_types": [{"type": r["event_type"], "count": r["n"]}
                            for r in top_event_types],
    }


def store_stats() -> Dict:
    """Backward-compatible alias used by the backend bootstrap report."""
    return global_stats()


# ── Heuristic Player Model ────────────────────────────────────────────────────

_EXPLORER_CMDS = {"ls", "cat", "help", "man", "info", "lore", "status", "map"}
_FIGHTER_CMDS = {"attack", "duel", "hack", "exploit", "exfil", "breach"}
_SOCIAL_CMDS = {"talk", "trust", "msg", "bribe", "join", "party"}
_BUILDER_CMDS = {"augment", "upgrade", "research", "colony", "build"}


def predict_player_archetype(session_id: str) -> Dict:
    """
    Heuristic player model: no ML library needed.
    Returns archetype (explorer/fighter/social/builder/balanced)
    and recommended next actions.
    """
    profile = get_player_profile(session_id)
    if not profile:
        return {"archetype": "newcomer", "confidence": 0.0,
                "suggestions": ["help", "status", "ls"]}

    top = {cmd: count for cmd, count in profile.get("top_commands", [])}
    total = sum(top.values()) or 1

    scores = {
        "explorer": sum(top.get(c, 0) for c in _EXPLORER_CMDS) / total,
        "fighter":  sum(top.get(c, 0) for c in _FIGHTER_CMDS) / total,
        "social":   sum(top.get(c, 0) for c in _SOCIAL_CMDS) / total,
        "builder":  sum(top.get(c, 0) for c in _BUILDER_CMDS) / total,
    }
    max_score = max(scores.values()) if scores else 0
    if max_score < 0.1:
        archetype = "balanced"
    else:
        archetype = max(scores, key=scores.get)

    suggestions = {
        "explorer":  ["lore", "map", "fragments", "diary"],
        "fighter":   ["duel", "hack", "augment", "rank"],
        "social":    ["trust", "party", "faction join", "talk"],
        "builder":   ["colony", "research", "upgrade", "swarm"],
        "balanced":  ["consciousness", "story", "missions", "serena ask"],
        "newcomer":  ["help", "status", "tutorial", "lore intro"],
    }.get(archetype, ["help"])

    return {
        "archetype": archetype,
        "confidence": round(max_score, 3),
        "scores": {k: round(v, 3) for k, v in scores.items()},
        "suggestions": suggestions,
        "commands_run": profile.get("commands_run", 0),
        "xp_total": profile.get("xp_total", 0),
    }


def predict_next_action(session_id: str) -> Optional[str]:
    """
    Markov-chain next-command prediction — zero-token, offline-first.
    Builds a bigram model from the session's command history and
    returns the most likely next command, or None if insufficient data.
    """
    try:
        with _conn() as c:
            rows = c.execute(
                """SELECT features FROM feature_events
                   WHERE session_id=? AND event_type='command'
                   ORDER BY ts ASC LIMIT 200""",
                (session_id,),
            ).fetchall()
        cmds = []
        for r in rows:
            feat = json.loads(r["features"] or "{}")
            cmd = feat.get("cmd", "").strip()
            if cmd:
                cmds.append(cmd)
        if len(cmds) < 3:
            return None
        # Build bigram transition counts
        transitions: Dict[str, Dict[str, int]] = {}
        for i in range(len(cmds) - 1):
            cur, nxt = cmds[i], cmds[i + 1]
            transitions.setdefault(cur, {})
            transitions[cur][nxt] = transitions[cur].get(nxt, 0) + 1
        last = cmds[-1]
        if last not in transitions:
            return None
        nexts = transitions[last]
        best = max(nexts, key=nexts.get)
        # Only return if confidence is reasonable (appeared > once or unique)
        if nexts[best] < 1:
            return None
        return best
    except Exception:
        return None


def initialise() -> Dict:
    _init_db()
    stats = global_stats()
    return {"status": "ready", **stats}
