"""
procgen/quests.py — Procedural quest generation for Terminal Depths.

Generates coherent, randomised quest objects using seeded templates.
Quests are stateless to generate but stateful once accepted (stored in gs.flags).
"""
from __future__ import annotations
import random
import hashlib
import time
from typing import Optional

# ── Quest templates ────────────────────────────────────────────────────────────
_VERBS = [
    "Infiltrate", "Extract", "Decrypt", "Neutralise", "Trace",
    "Clone", "Intercept", "Purge", "Secure", "Expose",
    "Recover", "Relay", "Monitor", "Map", "Override",
]

_OBJECTS = [
    "the nexus auth log", "CHIMERA's supply manifest", "a darknet relay key",
    "the watcher's secondary feed", "a ghost process signature",
    "Ada's memory fragment", "the NexusCorp payroll chain",
    "a corrupted sentry loop", "the convergence seed",
    "Raven's extraction route", "the lattice heartbeat signal",
    "a synthetic agent profile", "the containment wall hash",
    "an encrypted faction manifesto", "the colony uplink token",
]

_CONDITIONS = [
    "before the CHIMERA sweep timer expires",
    "without triggering the trace alarm",
    "using only stealth commands",
    "while maintaining zero detected intrusions",
    "before the nexus gateway rotates",
    "under root access conditions",
    "across exactly three node hops",
    "with agent trust above 60",
    "while the colony supply is positive",
    "before the Watcher notices",
]

_REWARDS = [
    ("networking", 40, 120),
    ("stealth",    35, 100),
    ("crypto",     45, 130),
    ("archaeology",30,  90),
    ("social",     25,  80),
    ("terminal",   20,  70),
    ("missions",   50, 150),
]

_HINT_CMDS = [
    "exploit", "trace", "scan", "map", "ssh ghost@node-7",
    "decompile chimera-core", "botnet status", "coop join",
    "osint ada", "serena query chimera", "flashback all",
    "fragments", "consciousness", "diary",
]

_FACTIONS = [
    "Special Circumstances", "The Resistance", "NexusCorp",
    "The Watcher's Order", "Ghost Collective", "Nexus Syndicate",
]

_DIFFICULTIES = ["ROUTINE", "ELEVATED", "CRITICAL", "CLASSIFIED"]


def _seed_from(session_id: str, nonce: int) -> int:
    raw = f"pq_{session_id}_{nonce}_{int(time.time() // 3600)}"
    return int(hashlib.sha256(raw.encode()).hexdigest()[:16], 16)


def generate_quest(session_id: str = "default", nonce: int = 0) -> dict:
    """
    Generate a single procedural quest dict.

    Returns:
        {
            "id":           str  — stable identifier (deterministic for same session+nonce+hour),
            "title":        str,
            "objective":    str,
            "faction":      str,
            "difficulty":   str,
            "xp_skill":     str,
            "xp_min":       int,
            "xp_max":       int,
            "command_hint": str  — in-game command to trigger completion,
            "expires_in":   int  — seconds (3600 for hourly rotation),
        }
    """
    rng = random.Random(_seed_from(session_id, nonce))

    verb       = rng.choice(_VERBS)
    obj        = rng.choice(_OBJECTS)
    condition  = rng.choice(_CONDITIONS)
    skill, lo, hi = rng.choice(_REWARDS)
    hint       = rng.choice(_HINT_CMDS)
    faction    = rng.choice(_FACTIONS)
    difficulty = rng.choice(_DIFFICULTIES)

    title = f"{verb} {obj}"
    objective = f"{verb} {obj} — {condition}."

    uid = hashlib.md5(f"{session_id}_{nonce}_{title}".encode()).hexdigest()[:8]

    return {
        "id":           f"pq_{uid}",
        "title":        title,
        "objective":    objective,
        "faction":      faction,
        "difficulty":   difficulty,
        "xp_skill":     skill,
        "xp_min":       lo,
        "xp_max":       hi,
        "command_hint": hint,
        "expires_in":   3600,
    }


def generate_batch(
    session_id: str = "default",
    count: int = 5,
    seed_offset: int = 0,
) -> list[dict]:
    """Generate `count` distinct procedural quests for a session."""
    seen_titles: set[str] = set()
    quests: list[dict] = []
    attempt = seed_offset
    while len(quests) < count and attempt < seed_offset + count * 3:
        q = generate_quest(session_id, attempt)
        if q["title"] not in seen_titles:
            seen_titles.add(q["title"])
            quests.append(q)
        attempt += 1
    return quests


def accept_quest(quest: dict, gs_flags: dict) -> None:
    """Mark a quest as accepted in gamestate flags."""
    qid = quest["id"]
    active = gs_flags.setdefault("procgen_quests", [])
    if not any(q.get("id") == qid for q in active):
        active.append(quest)


def complete_quest(quest_id: str, gs_flags: dict) -> Optional[dict]:
    """Mark a quest complete, return the quest dict if found."""
    active = gs_flags.get("procgen_quests", [])
    match = next((q for q in active if q.get("id") == quest_id), None)
    if match:
        done = gs_flags.setdefault("procgen_quests_done", [])
        if quest_id not in done:
            done.append(quest_id)
    return match


def active_quests(gs_flags: dict) -> list[dict]:
    """Return list of accepted but incomplete procgen quests."""
    active = gs_flags.get("procgen_quests", [])
    done   = set(gs_flags.get("procgen_quests_done", []))
    return [q for q in active if q.get("id") not in done]


def render_quest(q: dict, done: bool = False) -> list[str]:
    """Return formatted lines for displaying a single quest."""
    icon = "✓" if done else "○"
    lines = [
        f"  {icon} [{q['difficulty']}] {q['title']}",
        f"    Faction: {q['faction']}  |  Skill: {q['xp_skill']}  |  XP: {q['xp_min']}–{q['xp_max']}",
        f"    {q['objective']}",
        f"    Hint: try '{q['command_hint']}'",
    ]
    return lines
