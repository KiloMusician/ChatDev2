"""
Terminal Depths — Swarm Controller
═══════════════════════════════════════════════════════════════════════════════
The brain of the autonomous development organism.

Every agent earns Development Points (DP) by playing the game and building
features. DP is used to spawn new agents. The swarm grows as it builds.

Architecture:
  SwarmLedger   — SQLite DP ledger (transactions, balances, history)
  SwarmRegistry — JSON roster of active agents and their roles
  SwarmController — orchestration: assign tasks, spawn agents, report

REST API (mounted in main.py):
  GET  /api/swarm/status    — current DP balance, active agents, phase
  GET  /api/swarm/ledger    — full DP transaction history
  POST /api/swarm/earn      — agent reports completed work (+DP)
  POST /api/swarm/spend     — agent spawns new agent (-DP)
  GET  /api/swarm/tasks     — available tasks from MASTER_ZETA_TODO
  POST /api/swarm/task/claim — agent claims a task
  POST /api/swarm/task/done  — agent marks task complete
  GET  /api/swarm/roster    — all registered swarm agents
  POST /api/swarm/spawn     — spawn a new agent (deducts DP)
"""
from __future__ import annotations

import json
import random
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# ── Paths ──────────────────────────────────────────────────────────────────
_STATE_DIR = Path(__file__).parent.parent.parent / "state"
_STATE_DIR.mkdir(exist_ok=True)
_LEDGER_PATH  = _STATE_DIR / "swarm_ledger.db"
_ROSTER_PATH  = _STATE_DIR / "swarm_registry.json"
_TODO_PATH    = Path(__file__).parent.parent.parent / "MASTER_ZETA_TODO.md"

# ── DP Economy ─────────────────────────────────────────────────────────────
DP_RATES: Dict[str, int] = {
    "bug_fix_p0":       100,
    "bug_fix_p1":       50,
    "feature_command":  40,
    "story_beat":       30,
    "agent_dialogue":   20,
    "vfs_lore_500w":    15,
    "challenge":        15,
    "test_written":     10,
    "playtest_session": 8,
    "procedural_gen":   10,
    "typo_fix":         2,
    "documentation":    5,
}

SPAWN_COSTS: Dict[str, int] = {
    "scout":       5,
    "lorekeeper":  8,
    "tester":      8,
    "builder":     15,
    "architect":   12,
    "orchestrator":20,
    "serena_class":30,
    "custom":      10,
}

AGENT_ROLES: Dict[str, str] = {
    "scout":       "Explores game world, identifies gaps, reports bugs",
    "lorekeeper":  "Writes lore, dialogue, story beats, VFS files",
    "tester":      "Runs commands, smoke tests, regression suites",
    "builder":     "Implements features, commands, game systems",
    "architect":   "Designs systems, writes specs, plans phases",
    "orchestrator":"Manages other agents, delegates, tracks DP",
    "serena_class":"Full convergence: orchestrate + build + lore",
    "custom":      "User-defined personality and role",
}


# ══════════════════════════════════════════════════════════════════════════════
# LEDGER
# ══════════════════════════════════════════════════════════════════════════════

class SwarmLedger:
    """SQLite-backed DP transaction ledger."""

    def __init__(self, db_path: Path = _LEDGER_PATH):
        self._path = db_path
        self._lock = threading.Lock()
        self._init()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(str(self._path))
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS ledger (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id    TEXT NOT NULL,
                    agent_name  TEXT NOT NULL,
                    action      TEXT NOT NULL,
                    category    TEXT NOT NULL,
                    dp_change   INTEGER NOT NULL,
                    running_bal INTEGER NOT NULL DEFAULT 0,
                    phase       TEXT DEFAULT 'P0',
                    task_ref    TEXT,
                    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS swarm_meta (
                    key TEXT PRIMARY KEY,
                    val TEXT NOT NULL
                );
                INSERT OR IGNORE INTO swarm_meta VALUES ('total_dp', '0');
                INSERT OR IGNORE INTO swarm_meta VALUES ('phase', 'P0');
                INSERT OR IGNORE INTO swarm_meta VALUES ('total_earned', '0');
                INSERT OR IGNORE INTO swarm_meta VALUES ('total_spent', '0');
            """)
            conn.commit()

    def _get_meta(self, key: str, default=0):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT val FROM swarm_meta WHERE key=?", (key,)
            ).fetchone()
        return type(default)(row["val"]) if row else default

    def _set_meta(self, conn, key: str, val):
        conn.execute(
            "INSERT OR REPLACE INTO swarm_meta (key, val) VALUES (?,?)",
            (key, str(val))
        )

    @property
    def balance(self) -> int:
        return self._get_meta("total_dp", 0)

    @property
    def phase(self) -> str:
        return self._get_meta("phase", "P0")

    def earn(
        self,
        agent_id: str,
        agent_name: str,
        action: str,
        category: str,
        dp: Optional[int] = None,
        task_ref: Optional[str] = None,
    ) -> dict:
        """Record a DP earn event. Returns updated balance."""
        if dp is None:
            dp = DP_RATES.get(category, 5)
        with self._lock:
            with self._conn() as conn:
                current = self._get_meta("total_dp", 0)
                new_bal = current + dp
                total_earned = self._get_meta("total_earned", 0) + dp
                self._set_meta(conn, "total_dp", new_bal)
                self._set_meta(conn, "total_earned", total_earned)
                conn.execute(
                    """INSERT INTO ledger
                       (agent_id, agent_name, action, category, dp_change, running_bal, task_ref)
                       VALUES (?,?,?,?,?,?,?)""",
                    (agent_id, agent_name, action, category, dp, new_bal, task_ref),
                )
                conn.commit()
        return {"dp": dp, "balance": new_bal, "action": action}

    def spend(
        self,
        agent_id: str,
        agent_name: str,
        action: str,
        category: str,
        dp: int,
        task_ref: Optional[str] = None,
    ) -> dict:
        """Record a DP spend. Returns updated balance. Raises if insufficient."""
        with self._lock:
            with self._conn() as conn:
                current = self._get_meta("total_dp", 0)
                if current < dp:
                    raise ValueError(
                        f"Insufficient DP: need {dp}, have {current}"
                    )
                new_bal = current - dp
                total_spent = self._get_meta("total_spent", 0) + dp
                self._set_meta(conn, "total_dp", new_bal)
                self._set_meta(conn, "total_spent", total_spent)
                conn.execute(
                    """INSERT INTO ledger
                       (agent_id, agent_name, action, category, dp_change, running_bal, task_ref)
                       VALUES (?,?,?,?,?,?,?)""",
                    (agent_id, agent_name, action, category, -dp, new_bal, task_ref),
                )
                conn.commit()
        return {"dp": -dp, "balance": new_bal, "action": action}

    def history(self, limit: int = 50, agent_id: Optional[str] = None) -> List[dict]:
        with self._conn() as conn:
            if agent_id:
                rows = conn.execute(
                    "SELECT * FROM ledger WHERE agent_id=? ORDER BY id DESC LIMIT ?",
                    (agent_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM ledger ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> dict:
        with self._conn() as conn:
            total_txn = conn.execute("SELECT COUNT(*) as n FROM ledger").fetchone()["n"]
            top_earner = conn.execute(
                "SELECT agent_name, SUM(dp_change) as total FROM ledger "
                "WHERE dp_change > 0 GROUP BY agent_name ORDER BY total DESC LIMIT 1"
            ).fetchone()
        return {
            "balance":      self.balance,
            "phase":        self.phase,
            "total_earned": self._get_meta("total_earned", 0),
            "total_spent":  self._get_meta("total_spent", 0),
            "transactions": total_txn,
            "top_earner":   dict(top_earner) if top_earner else None,
        }

    def advance_phase(self, new_phase: str):
        with self._conn() as conn:
            self._set_meta(conn, "phase", new_phase)
            conn.commit()


# ══════════════════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SwarmAgent:
    agent_id:    str
    name:        str
    role:        str
    status:      str = "idle"       # idle | working | playing | resting
    current_task: Optional[str] = None
    dp_earned:   int = 0
    dp_spent:    int = 0
    spawned_by:  Optional[str] = None
    spawned_at:  str = ""
    last_active: str = ""
    personality: str = "professional"
    token:       Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "agent_id":    self.agent_id,
            "name":        self.name,
            "role":        self.role,
            "status":      self.status,
            "current_task":self.current_task,
            "dp_earned":   self.dp_earned,
            "dp_spent":    self.dp_spent,
            "spawned_by":  self.spawned_by,
            "spawned_at":  self.spawned_at,
            "last_active": self.last_active,
            "personality": self.personality,
        }


class SwarmRegistry:
    """JSON-backed roster of all swarm agents."""

    def __init__(self, path: Path = _ROSTER_PATH):
        self._path = path
        self._lock = threading.Lock()
        self._agents: Dict[str, SwarmAgent] = {}
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                for d in data.get("agents", []):
                    a = SwarmAgent(**{k: d.get(k, "") for k in SwarmAgent.__dataclass_fields__})
                    self._agents[a.agent_id] = a
            except Exception:
                pass

    def _save(self):
        data = {"agents": [a.to_dict() for a in self._agents.values()],
                "updated": _now()}
        self._path.write_text(json.dumps(data, indent=2))

    def register(self, agent: SwarmAgent) -> SwarmAgent:
        with self._lock:
            self._agents[agent.agent_id] = agent
            self._save()
        return agent

    def get(self, agent_id: str) -> Optional[SwarmAgent]:
        return self._agents.get(agent_id)

    def all(self) -> List[SwarmAgent]:
        return list(self._agents.values())

    def update_status(self, agent_id: str, status: str, task: Optional[str] = None):
        with self._lock:
            a = self._agents.get(agent_id)
            if a:
                a.status = status
                a.current_task = task
                a.last_active = _now()
                self._save()

    def add_dp(self, agent_id: str, dp: int):
        with self._lock:
            a = self._agents.get(agent_id)
            if a:
                if dp > 0:
                    a.dp_earned += dp
                else:
                    a.dp_spent += abs(dp)
                self._save()

    def count_by_role(self) -> dict:
        counts: Dict[str, int] = {}
        for a in self._agents.values():
            counts[a.role] = counts.get(a.role, 0) + 1
        return counts


# ══════════════════════════════════════════════════════════════════════════════
# TASK QUEUE (reads from MASTER_ZETA_TODO.md)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SwarmTask:
    task_id:    str
    title:      str
    priority:   str   # P0, P1, P2, P3
    category:   str
    status:     str = "open"   # open | claimed | done
    claimed_by: Optional[str] = None
    claimed_at: Optional[str] = None
    done_at:    Optional[str] = None
    dp_value:   int = 10


class TaskQueue:
    """Lightweight task queue backed by a JSON sidecar file."""

    _QUEUE_PATH = _STATE_DIR / "swarm_tasks.json"

    def __init__(self):
        self._lock = threading.Lock()
        self._tasks: Dict[str, SwarmTask] = {}
        self._load()

    def _load(self):
        if self._QUEUE_PATH.exists():
            try:
                data = json.loads(self._QUEUE_PATH.read_text())
                for d in data.get("tasks", []):
                    t = SwarmTask(**d)
                    self._tasks[t.task_id] = t
            except Exception:
                pass

    def _save(self):
        data = {"tasks": [t.__dict__ for t in self._tasks.values()],
                "updated": _now()}
        self._QUEUE_PATH.write_text(json.dumps(data, indent=2))

    def add(self, task: SwarmTask) -> SwarmTask:
        with self._lock:
            self._tasks[task.task_id] = task
            self._save()
        return task

    def claim(self, task_id: str, agent_id: str) -> Optional[SwarmTask]:
        with self._lock:
            t = self._tasks.get(task_id)
            if t and t.status == "open":
                t.status = "claimed"
                t.claimed_by = agent_id
                t.claimed_at = _now()
                self._save()
                return t
        return None

    def complete(self, task_id: str, agent_id: str) -> Optional[SwarmTask]:
        with self._lock:
            t = self._tasks.get(task_id)
            if t and t.claimed_by == agent_id:
                t.status = "done"
                t.done_at = _now()
                self._save()
                return t
        return None

    def open_tasks(self, priority: Optional[str] = None) -> List[SwarmTask]:
        tasks = [t for t in self._tasks.values() if t.status == "open"]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        dp_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        return sorted(tasks, key=lambda t: dp_order.get(t.priority, 9))

    def stats(self) -> dict:
        all_t = list(self._tasks.values())
        return {
            "total": len(all_t),
            "open":  sum(1 for t in all_t if t.status == "open"),
            "claimed": sum(1 for t in all_t if t.status == "claimed"),
            "done":  sum(1 for t in all_t if t.status == "done"),
        }

    def seed_default_tasks(self):
        """Seed the queue with initial tasks from SWARM_DIRECTIVE phases."""
        defaults = [
            ("T-P0-001", "Fix all unimplemented _cmd_ stub responses",   "P0", "bug_fix",       100),
            ("T-P0-002", "Smoke-test all 120+ commands",                  "P0", "testing",        80),
            ("T-P0-003", "Scout: play 20-command session, file gap report","P0", "playtest",       30),
            ("T-P1-001", "Implement `hack <target>` skill-check command", "P1", "feature",        40),
            ("T-P1-002", "Implement `crack <hash>` wordlist command",     "P1", "feature",        40),
            ("T-P1-003", "Implement `faction` reputation system",         "P1", "feature",        50),
            ("T-P1-004", "Implement `botnet` command (add/status/run)",   "P1", "feature",        40),
            ("T-P1-005", "Implement `endings` command (show reachable endings)","P1","feature",   30),
            ("T-P1-006", "Implement `quests` command expansion",          "P1", "feature",        30),
            ("T-P2-001", "Write prequel lore: THE_FIRST_GHOST.md",        "P2", "lore",           15),
            ("T-P2-002", "Write prequel lore: CHIMERA_GENESIS.log",       "P2", "lore",           15),
            ("T-P2-003", "Write Ada-7 backstory VFS file",                "P2", "lore",           15),
            ("T-P2-004", "Write Nova defection arc files",                "P2", "lore",           15),
            ("T-P2-005", "Expand agent dialogue: Ada +20 lines",         "P2", "dialogue",        20),
            ("T-P2-006", "Expand agent dialogue: Raven +20 lines",       "P2", "dialogue",        20),
            ("T-P2-007", "Expand agent dialogue: Gordon +20 lines",      "P2", "dialogue",        20),
            ("T-P3-001", "Logic Labyrinth levels 11-15",                  "P3", "puzzle",         30),
            ("T-P3-002", "SAT solver puzzles 7-9",                        "P3", "puzzle",         25),
            ("T-P3-003", "TIS-100 levels 6-8",                           "P3", "puzzle",         25),
            ("T-P3-004", "ZERO Fragment collection system",               "P3", "feature",        60),
            ("T-P3-005", "Mole investigation quest (multi-step)",         "P3", "story",          80),
        ]
        for tid, title, prio, cat, dp in defaults:
            if tid not in self._tasks:
                self.add(SwarmTask(
                    task_id=tid, title=title, priority=prio,
                    category=cat, dp_value=dp
                ))


# ══════════════════════════════════════════════════════════════════════════════
# CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════

class SwarmController:
    """
    The master orchestrator. Serena's implementation layer.

    - Tracks DP balance (ledger)
    - Manages agent roster (registry)
    - Assigns tasks (task queue)
    - Handles spawning
    - Exposes status for REST API
    """

    # Phase thresholds: advance when total_earned exceeds these
    _PHASE_THRESHOLDS = {
        "P0": 50,
        "P1": 200,
        "P2": 500,
        "P3": 1000,
        "P4": 2000,
        "P5": 5000,
    }

    def __init__(self):
        self.ledger   = SwarmLedger()
        self.registry = SwarmRegistry()
        self.tasks    = TaskQueue()
        self.tasks.seed_default_tasks()

    # ── Status ──────────────────────────────────────────────────────────────

    def status(self) -> dict:
        ldg = self.ledger.stats()
        roster = self.registry.all()
        task_stats = self.tasks.stats()
        return {
            "ok": True,
            "dp_balance":    ldg["balance"],
            "total_earned":  ldg["total_earned"],
            "total_spent":   ldg["total_spent"],
            "phase":         ldg["phase"],
            "transactions":  ldg["transactions"],
            "top_earner":    ldg["top_earner"],
            "agents": {
                "total":   len(roster),
                "active":  sum(1 for a in roster if a.status == "working"),
                "idle":    sum(1 for a in roster if a.status == "idle"),
                "by_role": self.registry.count_by_role(),
                "roster":  [a.to_dict() for a in roster],
            },
            "tasks": task_stats,
            "spawn_costs":   SPAWN_COSTS,
            "dp_rates":      DP_RATES,
            "next_phase":    self._next_phase_info(ldg["total_earned"]),
        }

    def _next_phase_info(self, total_earned: int) -> dict:
        phase = self.ledger.phase
        phases = ["P0", "P1", "P2", "P3", "P4", "P5", "DONE"]
        idx = phases.index(phase) if phase in phases else 0
        if idx < len(phases) - 1:
            next_p = phases[idx + 1]
            threshold = self._PHASE_THRESHOLDS.get(phase, 9999)
            return {
                "next_phase": next_p,
                "threshold":  threshold,
                "progress":   min(total_earned, threshold),
                "remaining":  max(0, threshold - total_earned),
            }
        return {"next_phase": "DONE", "threshold": 0, "remaining": 0, "progress": 0}

    # ── Earn ────────────────────────────────────────────────────────────────

    def earn(
        self,
        agent_id: str,
        agent_name: str,
        action: str,
        category: str,
        dp: Optional[int] = None,
        task_ref: Optional[str] = None,
    ) -> dict:
        result = self.ledger.earn(agent_id, agent_name, action, category, dp, task_ref)
        self.registry.add_dp(agent_id, result["dp"])
        self._check_phase_advance()
        return result

    # ── Spawn ────────────────────────────────────────────────────────────────

    def spawn(
        self,
        role: str,
        name: Optional[str] = None,
        personality: str = "professional",
        spawned_by: Optional[str] = None,
        token: Optional[str] = None,
    ) -> dict:
        cost = SPAWN_COSTS.get(role, SPAWN_COSTS["custom"])
        balance = self.ledger.balance
        if balance < cost:
            return {
                "ok": False,
                "error": f"Insufficient DP: need {cost}, have {balance}",
                "cost": cost,
                "balance": balance,
            }

        # Generate agent identity
        agent_id = f"swarm_{role}_{int(time.time()*1000) % 1_000_000}"
        if not name:
            adjectives = ["Swift", "Dark", "Keen", "Bold", "Silent", "Deep", "Sharp"]
            names = {
                "scout":       "Rogue",
                "lorekeeper":  "Scribe",
                "tester":      "Probe",
                "builder":     "Forge",
                "architect":   "Architect",
                "orchestrator":"Serena",
                "serena_class":"Ψ",
                "custom":      "Agent",
            }
            name = f"{random.choice(adjectives)}-{names.get(role,'Unit')}-{random.randint(10,99)}"

        agent = SwarmAgent(
            agent_id=agent_id,
            name=name,
            role=role,
            status="idle",
            personality=personality,
            spawned_by=spawned_by or "controller",
            spawned_at=_now(),
            last_active=_now(),
            token=token,
        )
        self.registry.register(agent)

        # Deduct DP
        self.ledger.spend(
            agent_id="controller",
            agent_name="SwarmController",
            action=f"Spawn {name} ({role})",
            category="spawn",
            dp=cost,
        )

        return {
            "ok": True,
            "agent_id":  agent_id,
            "name":      name,
            "role":      role,
            "cost":      cost,
            "balance":   self.ledger.balance,
            "role_desc": AGENT_ROLES.get(role, ""),
        }

    # ── Tasks ────────────────────────────────────────────────────────────────

    def next_task(self, priority: Optional[str] = None) -> Optional[SwarmTask]:
        tasks = self.tasks.open_tasks(priority)
        return tasks[0] if tasks else None

    def claim_task(self, task_id: str, agent_id: str) -> dict:
        t = self.tasks.claim(task_id, agent_id)
        if t:
            self.registry.update_status(agent_id, "working", t.title)
            return {"ok": True, "task": t.__dict__}
        return {"ok": False, "error": "Task unavailable or already claimed"}

    def complete_task(self, task_id: str, agent_id: str, agent_name: str) -> dict:
        t = self.tasks.complete(task_id, agent_id)
        if t:
            result = self.earn(
                agent_id=agent_id,
                agent_name=agent_name,
                action=f"Completed: {t.title}",
                category=t.category,
                dp=t.dp_value,
                task_ref=task_id,
            )
            self.registry.update_status(agent_id, "idle")
            return {"ok": True, "dp_earned": result["dp"], "balance": result["balance"]}
        return {"ok": False, "error": "Task not found or not owned by this agent"}

    # ── Phase Management ─────────────────────────────────────────────────────

    def _check_phase_advance(self):
        total = self.ledger._get_meta("total_earned", 0)
        current = self.ledger.phase
        phases = ["P0", "P1", "P2", "P3", "P4", "P5"]
        idx = phases.index(current) if current in phases else 0
        if idx < len(phases) - 1:
            threshold = self._PHASE_THRESHOLDS.get(current, 9999)
            if total >= threshold:
                next_phase = phases[idx + 1]
                self.ledger.advance_phase(next_phase)


# ── Singleton ──────────────────────────────────────────────────────────────
_controller: Optional[SwarmController] = None
_ctrl_lock = threading.Lock()


def get_swarm_controller() -> SwarmController:
    global _controller
    if _controller is None:
        with _ctrl_lock:
            if _controller is None:
                _controller = SwarmController()
    return _controller


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
