"""
app/game_engine/signal_harvester.py — Gameplay Signal Harvester

Every command a player executes feeds this module. It accumulates structured
signals that the CHUG engine reads to decide what to build, fix, and improve.

Design principle: Playing the game IS contributing to building it.
  - Command patterns reveal what UX needs attention
  - Errors reveal what needs hardening
  - Fragment discoveries reveal narrative engagement
  - Milestone events trigger autonomous improvement cycles
  - Signal density (via `signal` command) feeds [Msg⛛{X}] lore

Usage:
    from app.game_engine.signal_harvester import harvest, get_cultivation_report
    harvest(cmd="ls", gs=session.gs, output=result)    # after each command
    report = get_cultivation_report()                   # CHUG reads this
"""
from __future__ import annotations

import json
import threading
import time
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent.parent
SIGNALS_FILE = ROOT / ".devmentor" / "gameplay_signals.json"
CULTIVATION_FILE = ROOT / ".devmentor" / "cultivation_report.json"

_lock = threading.Lock()

# ── Rolling in-memory buffer (most recent 500 signals) ────────────────
_recent: deque[Dict[str, Any]] = deque(maxlen=500)

# ── Counters (persist-on-flush) ───────────────────────────────────────
_cmd_counter: Counter = Counter()
_error_counter: Counter = Counter()
_beat_counter: Counter = Counter()
_milestone_log: List[Dict[str, Any]] = []

_FLUSH_INTERVAL = 60  # seconds between disk writes
_last_flush: float = 0.0

# ── Milestone thresholds that trigger a CHUG cycle ───────────────────
_CHUG_MILESTONES = {
    "cmds_50": 50,
    "cmds_100": 100,
    "cmds_250": 250,
    "cmds_500": 500,
    "cmds_1000": 1000,
}
_triggered_milestones: set[str] = set()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_state() -> None:
    """Load persisted counters from disk (called once at module init)."""
    global _triggered_milestones
    if not SIGNALS_FILE.exists():
        return
    try:
        data = json.loads(SIGNALS_FILE.read_text())
        _cmd_counter.update(data.get("cmd_counts", {}))
        _error_counter.update(data.get("error_counts", {}))
        _beat_counter.update(data.get("beat_counts", {}))
        _triggered_milestones = set(data.get("triggered_milestones", []))
        for item in data.get("milestone_log", []):
            _milestone_log.append(item)
    except Exception:
        pass


def _flush_to_disk() -> None:
    """Write current counters to disk."""
    global _last_flush
    SIGNALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated": _utc_now(),
        "cmd_counts": dict(_cmd_counter.most_common(100)),
        "error_counts": dict(_error_counter.most_common(50)),
        "beat_counts": dict(_beat_counter),
        "triggered_milestones": sorted(_triggered_milestones),
        "milestone_log": _milestone_log[-50:],
        "recent_count": len(_recent),
    }
    SIGNALS_FILE.write_text(json.dumps(payload, indent=2))
    _last_flush = time.time()


def _maybe_flush() -> None:
    global _last_flush
    if time.time() - _last_flush > _FLUSH_INTERVAL:
        _flush_to_disk()


def _check_milestones(total_cmds: int) -> List[str]:
    """Return list of newly triggered milestone IDs."""
    newly_triggered = []
    for mid, threshold in _CHUG_MILESTONES.items():
        if mid not in _triggered_milestones and total_cmds >= threshold:
            _triggered_milestones.add(mid)
            _milestone_log.append({
                "id": mid,
                "threshold": threshold,
                "actual": total_cmds,
                "ts": _utc_now(),
            })
            newly_triggered.append(mid)
    return newly_triggered


def harvest(cmd: str, gs: Any, output: Any) -> List[str]:
    """
    Record a gameplay signal. Called after every game command.

    Args:
        cmd:    The raw command string (e.g. "ls", "signal pulse", "map")
        gs:     GameState instance for this session
        output: Command result dict (from session.execute)

    Returns:
        List of milestone IDs that were just crossed (empty if none).
        Callers can use this to trigger a background CHUG cycle.
    """
    verb = cmd.strip().split()[0].lower() if cmd.strip() else "?"

    # Track XP and output richness as signal quality indicators
    has_error = any(
        s.get("t") == "err" for s in (output.get("output", []) if isinstance(output, dict) else [])
    )
    has_lore = any(
        s.get("t") in ("lore", "sys") for s in (output.get("output", []) if isinstance(output, dict) else [])
    )

    signal = {
        "ts": _utc_now(),
        "cmd": verb,
        "full": cmd[:80],
        "err": has_error,
        "lore": has_lore,
        "cmds": getattr(gs, "commands_run", 0),
        "lvl": getattr(gs, "level", 0),
        "xp": getattr(gs, "xp", 0),
    }

    with _lock:
        _recent.append(signal)
        _cmd_counter[verb] += 1
        if has_error:
            _error_counter[verb] += 1

        total_cmds = getattr(gs, "commands_run", 0)
        newly_triggered = _check_milestones(total_cmds)
        _maybe_flush()

    return newly_triggered


def record_story_beat(beat_id: str, gs: Any) -> None:
    """Call when a story beat fires. Tracks narrative engagement."""
    with _lock:
        _beat_counter[beat_id] += 1
        _milestone_log.append({
            "id": f"beat:{beat_id}",
            "ts": _utc_now(),
            "player_level": getattr(gs, "level", 0),
        })
        _maybe_flush()


def record_fragment(fragment_id: str, gs: Any) -> None:
    """Call when a [Msg⛛{X}] fragment is discovered."""
    with _lock:
        key = f"fragment:{fragment_id}"
        _milestone_log.append({
            "id": key,
            "ts": _utc_now(),
            "player_level": getattr(gs, "level", 0),
            "cmds": getattr(gs, "commands_run", 0),
        })
        _milestone_log.append({"id": "fragment_discovery", "ts": _utc_now()})
        _maybe_flush()


def get_cultivation_report() -> Dict[str, Any]:
    """
    Generate a cultivation report that the CHUG engine reads during ASSESS.
    Returns a dict summarizing player behavior and system health signals.
    """
    with _lock:
        total_signals = sum(_cmd_counter.values())
        top_commands = _cmd_counter.most_common(15)
        error_prone = _error_counter.most_common(10)
        beats_fired = len(_beat_counter)
        fragments_found = sum(1 for m in _milestone_log if m.get("id", "").startswith("fragment:"))
        milestones = sorted(_triggered_milestones)

        # Commands that have errors > 20% of the time are UX debt
        ux_debt = [
            {"cmd": cmd, "errors": cnt, "total": _cmd_counter.get(cmd, 0)}
            for cmd, cnt in error_prone
            if _cmd_counter.get(cmd, 0) > 0
            and cnt / _cmd_counter.get(cmd, 0) > 0.2
        ]

        # Commands used ≥ 10× are "core engagement loops"
        core_loops = [cmd for cmd, cnt in top_commands if cnt >= 10]

        # Commands never used (from a known set) are undiscovered features
        _KNOWN_COMMANDS = {
            "map", "ls", "cat", "signal", "omni", "vantage", "delegate",
            "converge", "reflect", "psiflow", "status", "inventory", "help",
            "scan", "hack", "decrypt", "diary", "fates", "residual", "deck",
            "rehabilitate", "timer", "anchor", "remnant", "proficiency",
            "polyglot", "chug", "msg-x",
        }
        never_used = sorted(_KNOWN_COMMANDS - set(_cmd_counter.keys()))

        report = {
            "generated": _utc_now(),
            "total_signals": total_signals,
            "unique_commands_used": len(_cmd_counter),
            "top_commands": [{"cmd": c, "count": n} for c, n in top_commands],
            "error_prone_commands": [{"cmd": c, "errors": n} for c, n in error_prone],
            "ux_debt": ux_debt,
            "core_engagement_loops": core_loops,
            "undiscovered_features": never_used,
            "story_beats_fired": beats_fired,
            "fragments_found": fragments_found,
            "milestones_reached": milestones,
            "recent_errors": [
                s for s in list(_recent)[-50:] if s.get("err")
            ],
            "chug_suggestions": _derive_chug_suggestions(
                ux_debt, never_used, error_prone, core_loops
            ),
        }

    CULTIVATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    CULTIVATION_FILE.write_text(json.dumps(report, indent=2))
    return report


def _derive_chug_suggestions(
    ux_debt: list,
    never_used: list,
    error_prone: list,
    core_loops: list,
) -> List[str]:
    """Translate player behavior patterns into CHUG improvement bullets."""
    suggestions = []

    if ux_debt:
        cmds = ", ".join(d["cmd"] for d in ux_debt[:3])
        suggestions.append(
            f"FIX: High error rate on commands [{cmds}] — improve help text or validation"
        )

    if len(never_used) > 8:
        sample = ", ".join(never_used[:5])
        suggestions.append(
            f"DISCOVER: {len(never_used)} commands never used by players — add tutorial hooks for [{sample}]"
        )

    if len(core_loops) >= 3:
        loops = ", ".join(core_loops[:3])
        suggestions.append(
            f"DEEPEN: Core engagement loops [{loops}] — add depth layers or rewards"
        )

    if not suggestions:
        suggestions.append("MAINTAIN: System healthy — run verification and document improvements")

    return suggestions[:7]


def flush() -> None:
    """Force immediate disk write."""
    with _lock:
        _flush_to_disk()


def get_stats() -> Dict[str, Any]:
    """Quick stats for the `chug` in-game command display."""
    with _lock:
        return {
            "total_signals": sum(_cmd_counter.values()),
            "unique_cmds": len(_cmd_counter),
            "error_prone": len(_error_counter),
            "beats": len(_beat_counter),
            "milestones": sorted(_triggered_milestones),
            "serena_observations": _read_serena_observations(limit=3),
            "gordon_learnings": _read_gordon_learnings(limit=3),
        }


# ── Serena MemoryPalace integration ───────────────────────────────────

def _read_serena_observations(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Read recent observations from Serena's SQLite MemoryPalace.
    Returns a list of observation dicts (zero-dependency — reads raw SQLite).
    """
    import sqlite3
    db = ROOT / "state" / "serena_memory.db"
    if not db.exists():
        return []
    try:
        with sqlite3.connect(str(db), timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                """
                SELECT content, severity, created_at, tags
                FROM observations
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return [
                {
                    "content": r["content"],
                    "severity": r["severity"],
                    "ts": r["created_at"],
                    "tags": r["tags"],
                    "source": "serena",
                }
                for r in rows
            ]
    except Exception:
        return []


# ── Gordon Chronicle integration ──────────────────────────────────────

def _read_gordon_learnings(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Read recent learnings from Gordon's chronicle JSONL file.
    Returns a list of {action, outcome, learning, ts} dicts.
    """
    chronicle = ROOT / "state" / "gordon_chronicle.jsonl"
    if not chronicle.exists():
        return []
    try:
        lines = chronicle.read_text().splitlines()
        results = []
        for line in lines[-limit:]:
            try:
                entry = json.loads(line)
                results.append({
                    "action": entry.get("action", ""),
                    "outcome": entry.get("outcome", ""),
                    "learning": entry.get("learning", ""),
                    "ts": entry.get("timestamp", ""),
                    "source": "gordon",
                })
            except Exception:
                pass
        return results
    except Exception:
        return []


def get_full_context() -> Dict[str, Any]:
    """
    Assemble the full cultivation context — gameplay signals + Serena + Gordon.
    This is what the LLM Cultivator receives for analysis.
    """
    report = get_cultivation_report()
    serena_obs = _read_serena_observations(limit=10)
    gordon_learnings = _read_gordon_learnings(limit=10)
    return {
        **report,
        "serena_observations": serena_obs,
        "gordon_learnings": gordon_learnings,
        "context_sources": ["signal_harvester", "serena_memory_palace", "gordon_chronicle"],
        "nusyq_wired": True,
    }


# ── Module initialization ─────────────────────────────────────────────
_load_state()
