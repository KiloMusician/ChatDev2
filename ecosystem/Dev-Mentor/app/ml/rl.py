"""
app/ml/rl.py — Q-Table Reinforcement Learning Engine (Phase 2)
===============================================================
Offline Q-learning for Gordon's command policy.

State space  : (level_bucket, xp_bucket, beat_bucket, skill_tier)
Action space : 8 command categories — hacking, social, exploration, ml,
               lore, admin, narrative, stealth
Storage      : SQLite table `rl_q_table` in the memory DB
Policy       : epsilon-greedy (epsilon decays with episodes)

No external dependencies — pure Python + SQLite.
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Storage path ────────────────────────────────────────────────────────────
_DEFAULT_DB = Path(__file__).parent.parent.parent / "var" / "memory.db"

# ── Action space ────────────────────────────────────────────────────────────
ACTIONS: List[str] = [
    "hacking",
    "social",
    "exploration",
    "ml",
    "lore",
    "admin",
    "narrative",
    "stealth",
]

# Commands that belong to each action category
ACTION_CMDS: Dict[str, List[str]] = {
    "hacking":     ["exploit", "scan", "nmap", "crack", "inject", "breach", "payload"],
    "social":      ["talk", "ask", "trust", "praise", "diplomacy", "council"],
    "exploration": ["look", "examine", "cd", "ls", "cat", "scene", "map"],
    "ml":          ["ml", "train", "predict", "cluster", "generate"],
    "lore":        ["lore", "archive", "fragment", "codex", "echo", "flashback"],
    "admin":       ["syscheck", "gordon", "skyclaw", "serena", "status"],
    "narrative":   ["quest", "story", "mission", "arcs", "scene"],
    "stealth":     ["hide", "ghost", "cloak", "evade", "shadow"],
}

# ── Hyper-parameters ─────────────────────────────────────────────────────────
GAMMA       = 0.9    # discount factor
ALPHA       = 0.1    # learning rate
EPS_START   = 0.8    # initial exploration rate
EPS_MIN     = 0.05   # minimum exploration rate
EPS_DECAY   = 0.95   # per-episode epsilon decay


# ── State encoding ───────────────────────────────────────────────────────────

def encode_state(level: int, xp: int, beats: int, top_skill_xp: int) -> str:
    """Encode game state as a compact bucket string."""
    lv  = min(level // 5, 9)           # 0-9 (buckets of 5 levels)
    xb  = min(xp // 200, 9)            # 0-9 (buckets of 200 XP)
    bb  = min(beats // 3, 9)           # 0-9 (buckets of 3 story beats)
    sk  = min(top_skill_xp // 50, 9)   # 0-9 (buckets of 50 skill XP)
    return f"{lv}{xb}{bb}{sk}"


def _reward_from_xp_delta(xp_delta: int, beat_delta: int) -> float:
    """Convert XP gain + story beat gain into a reward scalar."""
    return float(xp_delta) * 0.1 + float(beat_delta) * 5.0


# ── Database helpers ─────────────────────────────────────────────────────────

def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rl_q_table (
            state   TEXT NOT NULL,
            action  TEXT NOT NULL,
            q_value REAL NOT NULL DEFAULT 0.0,
            visits  INTEGER NOT NULL DEFAULT 0,
            updated REAL NOT NULL DEFAULT 0.0,
            PRIMARY KEY (state, action)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rl_meta (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    conn.commit()


def _get_q(conn: sqlite3.Connection, state: str, action: str) -> float:
    row = conn.execute(
        "SELECT q_value FROM rl_q_table WHERE state=? AND action=?",
        (state, action),
    ).fetchone()
    return row[0] if row else 0.0


def _set_q(conn: sqlite3.Connection, state: str, action: str, q: float) -> None:
    conn.execute("""
        INSERT INTO rl_q_table (state, action, q_value, visits, updated)
        VALUES (?, ?, ?, 1, ?)
        ON CONFLICT(state, action) DO UPDATE SET
            q_value = excluded.q_value,
            visits  = visits + 1,
            updated = excluded.updated
    """, (state, action, q, time.time()))


def _get_meta(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    row = conn.execute("SELECT value FROM rl_meta WHERE key=?", (key,)).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row[0])
    except Exception:
        return row[0]


def _set_meta(conn: sqlite3.Connection, key: str, value: Any) -> None:
    conn.execute("""
        INSERT INTO rl_meta (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, json.dumps(value)))


# ── Public API ───────────────────────────────────────────────────────────────

class QTableAgent:
    """Epsilon-greedy Q-learning agent backed by SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or _DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        _ensure_table(self._conn)

    # ── Policy ────────────────────────────────────────────────────────────

    def get_epsilon(self) -> float:
        eps = _get_meta(self._conn, "epsilon", EPS_START)
        return max(EPS_MIN, float(eps))

    def choose_action(self, state: str) -> str:
        """Epsilon-greedy action selection."""
        eps = self.get_epsilon()
        if random.random() < eps:
            return random.choice(ACTIONS)
        return self.best_action(state)

    def best_action(self, state: str) -> str:
        """Return the greedy best action for this state."""
        q_vals = {a: _get_q(self._conn, state, a) for a in ACTIONS}
        return max(q_vals, key=lambda a: q_vals[a])

    def q_values(self, state: str) -> Dict[str, float]:
        return {a: _get_q(self._conn, state, a) for a in ACTIONS}

    # ── Learning ──────────────────────────────────────────────────────────

    def update(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str,
    ) -> float:
        """Single Q-learning update. Returns the new Q-value."""
        q_cur  = _get_q(self._conn, state, action)
        q_next = max(_get_q(self._conn, next_state, a) for a in ACTIONS)
        q_new  = q_cur + ALPHA * (reward + GAMMA * q_next - q_cur)
        _set_q(self._conn, state, action, q_new)
        self._conn.commit()
        return q_new

    def train_from_history(self, interactions: List[Dict]) -> Dict:
        """
        Offline Q-learning from interaction log rows.
        Each row: {cmd, xp_before, xp_after, beats_before, beats_after,
                   level, top_skill_xp}
        Returns training summary.
        """
        episodes = 0
        total_reward = 0.0
        updates = 0

        for i, row in enumerate(interactions[:-1]):
            nxt = interactions[i + 1]
            state      = encode_state(
                row.get("level", 1), row.get("xp_before", 0),
                row.get("beats_before", 0), row.get("top_skill_xp", 0),
            )
            next_state = encode_state(
                nxt.get("level", 1), nxt.get("xp_before", 0),
                nxt.get("beats_before", 0), nxt.get("top_skill_xp", 0),
            )
            cmd    = row.get("cmd", "")
            action = _categorise_cmd(cmd)
            reward = _reward_from_xp_delta(
                row.get("xp_after", 0) - row.get("xp_before", 0),
                row.get("beats_after", 0) - row.get("beats_before", 0),
            )
            self.update(state, action, reward, next_state)
            total_reward += reward
            updates += 1

        eps = self.get_epsilon()
        new_eps = max(EPS_MIN, eps * EPS_DECAY)
        _set_meta(self._conn, "epsilon", new_eps)
        _set_meta(self._conn, "last_train", time.time())
        _set_meta(self._conn, "total_updates",
                  int(_get_meta(self._conn, "total_updates", 0)) + updates)
        self._conn.commit()
        return {
            "episodes": episodes,
            "updates":  updates,
            "avg_reward": round(total_reward / max(updates, 1), 3),
            "epsilon":  round(new_eps, 4),
        }

    # ── Stats ─────────────────────────────────────────────────────────────

    def stats(self) -> Dict:
        total   = self._conn.execute("SELECT COUNT(*) FROM rl_q_table").fetchone()[0]
        max_q   = self._conn.execute("SELECT MAX(q_value) FROM rl_q_table").fetchone()[0] or 0.0
        avg_q   = self._conn.execute("SELECT AVG(q_value) FROM rl_q_table").fetchone()[0] or 0.0
        visits  = self._conn.execute("SELECT SUM(visits) FROM rl_q_table").fetchone()[0] or 0
        updates = int(_get_meta(self._conn, "total_updates", 0))
        last_ts = _get_meta(self._conn, "last_train", None)
        return {
            "q_table_entries":   total,
            "max_q_value":       round(float(max_q), 3),
            "avg_q_value":       round(float(avg_q), 3),
            "total_visits":      visits,
            "total_updates":     updates,
            "epsilon":           round(self.get_epsilon(), 4),
            "last_trained":      last_ts,
            "action_space":      len(ACTIONS),
            "state_space_size":  10 ** 4,
        }


def _categorise_cmd(cmd: str) -> str:
    """Map a raw command string to one of the 8 action categories."""
    base = cmd.split()[0].lower().rstrip("-_") if cmd else ""
    for action, cmds in ACTION_CMDS.items():
        if base in cmds:
            return action
    return "exploration"


def train_from_memory_db(db_path: Optional[Path] = None) -> Dict:
    """
    Read interaction log from memory.db and train the Q-table.
    Rebuilds synthetic (state, reward) pairs from XP timestamps.
    """
    db = db_path or _DEFAULT_DB
    if not db.exists():
        return {"error": "memory DB not found", "updates": 0}

    conn = sqlite3.connect(str(db))
    try:
        rows = conn.execute(
            "SELECT cmd, xp_gain, timestamp FROM interactions ORDER BY timestamp ASC LIMIT 500"
        ).fetchall()
    except Exception:
        rows = []
    conn.close()

    if not rows:
        return {"error": "no interaction history", "updates": 0}

    interactions = []
    cumxp = 0
    for i, (cmd, xp_gain, ts) in enumerate(rows):
        xp_gain = int(xp_gain or 0)
        interactions.append({
            "cmd":          cmd or "",
            "level":        max(1, cumxp // 100),
            "xp_before":    cumxp,
            "xp_after":     cumxp + xp_gain,
            "beats_before": i,
            "beats_after":  i + (1 if xp_gain > 20 else 0),
            "top_skill_xp": xp_gain * 3,
        })
        cumxp += xp_gain

    agent = QTableAgent(db)
    return agent.train_from_memory_db(interactions)


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "test.db"
        agent = QTableAgent(db)
        state = encode_state(5, 400, 6, 120)
        action = agent.choose_action(state)
        new_q  = agent.update(state, action, 10.0, encode_state(6, 450, 7, 140))
        print(f"State: {state}  Action: {action}  New Q: {new_q:.3f}")
        print(f"Stats: {agent.stats()}")
