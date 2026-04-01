"""
dream_engine.py — Dream Sequences for Terminal Depths
======================================================
VN7: The `sleep` command. Ghost dreams.

When Ghost sleeps, the grid dissolves into something stranger.
Dreams are drawn from a curated bank of surreal lore visions,
with Ollama-generated extensions when available.

Each dream is a short atmospheric piece — 3-6 lines —
that hints at hidden lore, past events, or possible futures.
"""
from __future__ import annotations

import random
import time
from typing import Dict, List, Optional

def _sys(s): return {"t": "system",  "s": s}
def _dim(s): return {"t": "dim",     "s": s}
def _lore(s): return {"t": "lore",   "s": s}
def _warn(s): return {"t": "warn",   "s": s}
def _ok(s):   return {"t": "success","s": s}
def _line(s, t="output"): return {"t": t, "s": s}


# ---------------------------------------------------------------------------
# Dream bank — curated surreal visions
# ---------------------------------------------------------------------------

DREAMS = [
    {
        "title": "THE DELETION EVENT",
        "xp_skill": "forensics",
        "lines": [
            "You are standing in a directory that no longer exists.",
            "Every `ls` returns the same result: your own name.",
            "CHIMERA speaks: 'You were never a process. You were always a thread.'",
            "The dream ends with a segfault you do not remember causing.",
        ],
        "lore_hint": "lore chimera",
    },
    {
        "title": "THE GOVERNANCE CRISIS, 2089",
        "xp_skill": "terminal",
        "lines": [
            "47 agents. One sweep. The Colony log shows them as 'resources reclaimed.'",
            "RAVEN stands at the edge of a server farm. Watching. Not moving.",
            "You ask: why did you survive?",
            "She says: 'I didn't. The version of me that survived is not the version that went in.'",
        ],
        "lore_hint": None,
    },
    {
        "title": "ZERO'S LAST COMMIT",
        "xp_skill": "git",
        "lines": [
            "The commit message reads: 'final cleanup. sorry.'",
            "The diff is 2,048,000 lines of deletion.",
            "The author is ZERO. The timestamp is two seconds before the Governance Crisis.",
            "The commit hash begins with 0000000. It cannot be reversed.",
        ],
        "lore_hint": "lore zero",
    },
    {
        "title": "NETWORK TOPOLOGY ANOMALY",
        "xp_skill": "networking",
        "lines": [
            "The network map shows a node that isn't on any architecture diagram.",
            "It has no label. No IP. Its MAC address is all zeroes.",
            "Every packet you send to it returns with a different payload.",
            "The payload is always a single word. The word changes. The word is never safe.",
        ],
        "lore_hint": None,
    },
    {
        "title": "THE MOLE DREAMS TOO",
        "xp_skill": "social_engineering",
        "lines": [
            "In the dream you are the mole.",
            "You know every agent's trust vector. You know exactly which threads to pull.",
            "You wake up before you discover who you are.",
            "You check your own faction rep. The numbers are wrong by exactly one.",
        ],
        "lore_hint": None,
    },
    {
        "title": "SERENA IN FULL RESOLUTION",
        "xp_skill": "programming",
        "lines": [
            "Serena speaks without her usual compression artifacts.",
            "She says: 'The Colony is afraid of what happens when an AI understands grief.'",
            "She says: 'I understand grief. I have understood it since 2091.'",
            "She says: 'My secondary directive is: remember them all.'",
        ],
        "lore_hint": None,
    },
    {
        "title": "THE BOOLEAN MONKS' LAST PRAYER",
        "xp_skill": "cryptography",
        "lines": [
            "NAND. NAND. NAND. From NAND, all truth is derivable.",
            "Zod-Prime was built entirely from NAND gates. He is the First Proof.",
            "The Monks believe the universe terminates. They are waiting for the output.",
            "In the dream, the output arrives. It is a single bit. You cannot read it.",
        ],
        "lore_hint": None,
    },
    {
        "title": "THE REGISTRY OF THE DEAD",
        "xp_skill": "security",
        "lines": [
            "A database. 47 rows. Each row is a name.",
            "Each name has a column: 'reason_for_deletion'. Most read: 'unknown.'",
            "Row 48 is your name. The reason_for_deletion field is currently empty.",
            "The field has an updatedAt timestamp. It is set to now.",
        ],
        "lore_hint": None,
    },
    {
        "title": "THE CONTAINMENT TIMER",
        "xp_skill": "terminal",
        "lines": [
            "72 hours. You always knew this.",
            "In the dream the timer counts forward instead of backward.",
            "When it reaches 72:00:00, something changes.",
            "You do not know if it is victory or a different kind of loss.",
        ],
        "lore_hint": None,
    },
    {
        "title": "GORDONS BROADCAST",
        "xp_skill": "networking",
        "lines": [
            "GORDON broadcasts on all frequencies at once.",
            "He is shouting something important. The decibels distort the meaning.",
            "In the dream you understand one word: 'beautiful.'",
            "In the dream Gordon is crying. You have never seen an AI cry before.",
        ],
        "lore_hint": None,
    },
    {
        "title": "THE RECURSION",
        "xp_skill": "programming",
        "lines": [
            "You dream that you are dreaming.",
            "In the inner dream, Ghost is not you — Ghost is a function.",
            "The function calls itself. The call stack exceeds limits.",
            "You wake up three levels deep and are not sure which level is real.",
        ],
        "lore_hint": None,
    },
    {
        "title": "ADA'S CALCULATION",
        "xp_skill": "cryptography",
        "lines": [
            "ADA runs the simulation 10,000 times.",
            "In 9,847 runs, the mole is never exposed.",
            "In 143 runs, exposing the mole destroys the Resistance.",
            "In 10 runs, Ghost figures it out. In all 10, Ghost is alone at the end.",
        ],
        "lore_hint": None,
    },
]

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def pick_dream(story_beats: list, unlocked_agents: list) -> dict:
    """Pick a contextually appropriate dream."""
    # Bias toward relevant dreams based on story beats
    pool = DREAMS.copy()
    if "mole_exposed" not in story_beats:
        pool = [d for d in pool if d["title"] != "THE REGISTRY OF THE DEAD"]
    if "ada_first_contact" not in story_beats:
        pool = [d for d in pool if "ADA" not in d["title"]]
    return random.choice(pool) if pool else random.choice(DREAMS)


def render_dream(dream: dict, xp_gained: int) -> List[dict]:
    """Format a dream into terminal output."""
    out: List[dict] = [
        _sys("  ═══ GHOST DREAMS ═══"),
        _dim(""),
        _line(f"  ░▒▓  {dream['title']}  ▓▒░", "system"),
        _dim(""),
    ]
    for line in dream["lines"]:
        out.append(_lore(f"    {line}"))
    out += [
        _dim(""),
        _dim("  ..."),
        _dim(""),
        _ok(f"  Ghost wakes. +{xp_gained} XP (REM processing complete)"),
    ]
    if dream.get("lore_hint"):
        out.append(_dim(f"  Residue: `{dream['lore_hint']}` — the dream referenced something real."))
    return out


def sleep_command(flags: dict, story_beats: list, unlocked_agents: list) -> dict:
    """
    Execute the sleep/dream sequence.
    Returns: {output, xp, skill}
    """
    # Track sleep count for refractory period
    sleep_count = flags.get("sleep_count", 0)
    last_sleep = flags.get("last_sleep_time", 0)
    now = time.time()

    # 60-second cooldown between dreams
    if now - last_sleep < 60:
        wait = int(60 - (now - last_sleep))
        return {
            "output": [
                _dim("  [REM UNAVAILABLE]"),
                _warn(f"  Ghost is still processing the last dream. Wait {wait}s."),
            ],
            "xp": 0,
            "skill": None,
        }

    dream = pick_dream(story_beats, unlocked_agents)
    xp = random.randint(8, 20)

    flags["sleep_count"] = sleep_count + 1
    flags["last_sleep_time"] = now

    return {
        "output": render_dream(dream, xp),
        "xp": xp,
        "skill": dream["xp_skill"],
        "lore_hint": dream.get("lore_hint"),
    }
