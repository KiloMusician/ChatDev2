#!/usr/bin/env python3
"""
Gordon Agent — Autonomous Terminal Depths Player with Serena Integration

The Gordon Node: A self-aware, self-improving player that inhabits the Terminal Depths
universe and learns through direct play, memory accumulation, and multi-agent orchestration.

Features:
- Persistent memory (SQLite + JSONL chronicle)
- Model routing (select best LLM for each decision)
- Serena REST API integration (ask, drift, align)
- Strategic phase planner (ORIENTATION → EXPLORATION → SKILL-BUILD → FACTION → ARG → PRESTIGE → IDLE)
- Auto‑session creation and state tracking
- Learning from past actions (strategy success rates)

Usage:
  # Against Replit dev server (auto‑discovers URL)
  python gordon_player.py

  # Against a custom deployment
  python gordon_player.py --url https://your-repl.replit.dev --session my-gordon

  # Debug mode with limited steps
  python gordon_player.py --mode debug --steps 20

  # Orchestrate (future expansion)
  python gordon_player.py --mode orchestrate

Environment variables (optional):
  GORDON_GAME_API    – override game API URL
  GORDON_MODEL_ROUTER – override model router URL
  WORKSPACE_ROOT     – where state/ is located
  GORDON_MODE        – default mode
  GORDON_MEMORY      – memory type (only sqlite supported currently)
"""

import argparse
import asyncio
import json
import logging
import os
import random
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import httpx
except ImportError:
    raise SystemExit(
        "gordon_player.py requires 'httpx'. Install with: pip install httpx"
    )

# ============================================================
# Configuration
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("gordon")

REPLIT_DEV_DOMAIN = os.getenv("REPLIT_DEV_DOMAIN", "")
_GORDON_API_ENV = os.getenv("GORDON_GAME_API", "")  # set by server at startup
_DOCKER_GATEWAY = os.getenv("GORDON_DOCKER_HOST", "")  # e.g. host.docker.internal

# URL resolution strategy:
#
#  Running in Docker container → use GORDON_DOCKER_HOST gateway or GORDON_GAME_API
#  Running natively in Replit  → always connect to localhost:5000 directly.
#      Replit maps port 5000 → port 80 for the browser preview.
#      GORDON_GAME_API is often set to the HTTPS public domain by the server;
#      using that URL from inside the same Repl causes SSL cert failure.
#      Bypassing via localhost avoids the proxy and TLS entirely.
#  Anywhere else               → GORDON_GAME_API → localhost:7337
_in_replit = bool(REPLIT_DEV_DOMAIN) and not _DOCKER_GATEWAY

DEFAULT_URL = (
    f"http://{_DOCKER_GATEWAY}:7337" if _DOCKER_GATEWAY else
    "http://localhost:5000" if _in_replit else
    _GORDON_API_ENV if _GORDON_API_ENV else
    "http://localhost:7337"
)

GORDON_VERSION = "1.0.0"          # merged version
PHASE_NAMES = [
    "ORIENTATION",
    "EXPLORATION",
    "SKILL-BUILD",
    "FACTION",
    "ARG",
    "PRESTIGE",
    "IDLE",
]

# ============================================================
# Data Models
# ============================================================

@dataclass
class GameState:
    """Current game state snapshot, enriched with phase tracking."""
    session_id: str
    player_level: int
    current_location: str
    inventory: List[str]
    current_health: int
    max_health: int
    available_commands: List[str]
    npcs_present: List[str]
    memory_snapshot: Dict
    # Gordon‑specific fields
    xp: Dict[str, int] = field(default_factory=dict)
    flags: Dict[str, Any] = field(default_factory=dict)
    beats: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    cwd: str = "/home/ghost"
    commands_run: int = 0
    tutorial_step: int = 0
    is_root: bool = False
    last_output: List[dict] = field(default_factory=list)
    tick: int = 0
    phase_idx: int = 0

    @property
    def phase(self) -> str:
        return PHASE_NAMES[min(self.phase_idx, len(PHASE_NAMES) - 1)]

    def total_xp(self) -> int:
        return sum(self.xp.values())

    def has_beat(self, beat: str) -> bool:
        return beat in self.beats


class ActionDecision:
    """Represents a decision made by Gordon."""
    def __init__(
        self,
        command: str,
        reasoning: str,
        model_used: str,
        confidence: float,
        timestamp: str
    ):
        self.command = command
        self.reasoning = reasoning
        self.model_used = model_used
        self.confidence = confidence
        self.timestamp = timestamp


# ============================================================
# Memory System
# ============================================================

class GordonMemory:
    """Persistent memory system for Gordon's experiences."""

    def __init__(self, memory_type: str = "sqlite", workspace: str = "/workspace"):
        self.memory_type = memory_type
        self.workspace = Path(workspace)
        self.db_path = self.workspace / "state" / "gordon_memory.db"
        self.chronicle_path = self.workspace / "state" / "gordon_chronicle.jsonl"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database and run schema migrations."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    session_id TEXT,
                    state_hash TEXT,
                    action TEXT,
                    result TEXT,
                    outcome TEXT,
                    learning TEXT,
                    model_used TEXT
                )
            """)

            # Full strategies schema — matches update_strategy() exactly
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY,
                    pattern TEXT UNIQUE,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    total_uses INTEGER DEFAULT 0,
                    last_used TEXT,
                    success_rate REAL DEFAULT 0.0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS npc_interactions (
                    id INTEGER PRIMARY KEY,
                    npc_name TEXT,
                    last_seen TEXT,
                    dialog_snippets TEXT,
                    relationship_score REAL
                )
            """)

            conn.commit()

        # Migrate any pre-existing strategies table that uses old column names
        self._migrate_strategies()

    def _migrate_strategies(self):
        """Add missing columns to strategies table if they don't exist (safe migration)."""
        needed = {
            "success_count": "INTEGER DEFAULT 0",
            "failure_count": "INTEGER DEFAULT 0",
            "total_uses":    "INTEGER DEFAULT 0",
            "last_used":     "TEXT",
            "success_rate":  "REAL DEFAULT 0.0",
        }
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(strategies)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            for col, col_def in needed.items():
                if col not in existing_cols:
                    cursor.execute(
                        f"ALTER TABLE strategies ADD COLUMN {col} {col_def}"
                    )
            conn.commit()

    def store_experience(
        self,
        session_id: str,
        state: GameState,
        action: str,
        result: str,
        outcome: str,
        model_used: str,
        learning: str
    ):
        """Store a complete experience."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "state_hash": hash(json.dumps(state.__dict__, default=str)),
            "action": action,
            "result": result,
            "outcome": outcome,
            "model_used": model_used,
            "learning": learning
        }

        with open(self.chronicle_path, "a") as f:
            f.write(json.dumps(record) + "\n")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories
                (timestamp, session_id, state_hash, action, result, outcome, model_used, learning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["timestamp"],
                session_id,
                record["state_hash"],
                action,
                result,
                outcome,
                model_used,
                learning
            ))
            conn.commit()

    def get_strategies(self) -> Dict[str, float]:
        """Retrieve learned strategies with success rates."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pattern, success_rate FROM strategies
                WHERE success_rate > 0.5
                ORDER BY success_rate DESC
            """)
            return {row[0]: row[1] for row in cursor.fetchall()}

    def update_strategy(self, pattern: str, succeeded: bool):
        """Update strategy success rate, keeping success_rate in sync."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            inc = 1 if succeeded else 0
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO strategies
                    (pattern, success_count, failure_count, total_uses, last_used, success_rate)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(pattern) DO UPDATE SET
                    success_count = success_count + ?,
                    failure_count = failure_count + ?,
                    total_uses    = total_uses + 1,
                    last_used     = ?,
                    success_rate  = CAST(success_count + ? AS REAL) / (total_uses + 1)
            """, (
                pattern,
                inc, 1 - inc, now, float(inc),   # INSERT values
                inc, 1 - inc, now, inc             # UPDATE values
            ))
            conn.commit()

    def recall_past_actions(self, pattern: str, limit: int = 5) -> List[Dict]:
        """Recall past actions matching a pattern."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, action, result, outcome FROM memories
                WHERE action LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{pattern}%", limit))
            return [
                {
                    "timestamp": row[0],
                    "action": row[1],
                    "result": row[2],
                    "outcome": row[3]
                }
                for row in cursor.fetchall()
            ]


# ============================================================
# Model Router
# ============================================================

class ModelRouter:
    """Interface to the model router service."""

    def __init__(self, router_url: str):
        self.router_url = router_url

    async def select_model(
        self, task_type: str, required_capabilities: List[str]
    ) -> Optional[Dict]:
        """Ask router for best model for task."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.router_url}/api/route",
                    json={
                        "task_type": task_type,
                        "required_capabilities": required_capabilities
                    },
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Router error: {e}")
        return None

    async def get_models(self) -> List[Dict]:
        """Get all available models."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.router_url}/api/models",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Failed to get models: {e}")
        return []


# ============================================================
# Game API Client
# ============================================================

class GameAPI:
    """Thin async client for the Terminal Depths REST API."""

    def __init__(self, base_url: str, session_id: Optional[str] = None, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id
        self.timeout = timeout
        self._http = httpx.AsyncClient(timeout=timeout)
        self._http.headers.update({
            "Content-Type": "application/json",
            "X-Gordon-Agent": f"Gordon/{GORDON_VERSION}",
        })

    async def close(self):
        await self._http.aclose()

    async def create_session(self) -> Optional[str]:
        """Create a new game session."""
        try:
            response = await self._http.post(
                f"{self.base_url}/api/game/session",
                json={"player_name": "Gordon"}
            )
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                logger.info(f"✓ Session created: {self.session_id}")
                return self.session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
        return None

    async def command(self, cmd: str) -> List[dict]:
        """Send a terminal command, return list of output line dicts."""
        if not self.session_id:
            logger.warning("No session ID, cannot send command")
            return []
        url = f"{self.base_url}/api/game/command"
        try:
            response = await self._http.post(
                url,
                json={"session_id": self.session_id, "command": cmd}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("output", [])
        except httpx.TimeoutException:
            logger.warning(f"command timed out: {cmd}")
            return []
        except Exception as exc:
            logger.error(f"API error on command {cmd!r}: {exc}")
            return []

    async def game_state(self) -> Optional[dict]:
        """Fetch current game state."""
        if not self.session_id:
            return None
        url = f"{self.base_url}/api/game/state"
        try:
            response = await self._http.get(url, params={"session_id": self.session_id})
            if response.status_code == 200:
                return response.json()
        except Exception as exc:
            logger.debug(f"game_state fetch failed: {exc}")
        return None

    # ── Serena REST API — meta‑intelligence for Gordon ──────────────────

    async def serena_ask(self, query: str, scope: str = "") -> Optional[dict]:
        """Ask Serena's Ξ-search. Returns indexed code intelligence."""
        url = f"{self.base_url}/api/serena/ask"
        try:
            response = await self._http.post(
                url,
                json={"query": query, "scope": scope or None, "limit": 3}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as exc:
            logger.debug(f"serena_ask failed: {exc}")
        return None

    async def serena_drift(self) -> Optional[dict]:
        """Check for coherence drift via Serena's Drift Detection Engine."""
        url = f"{self.base_url}/api/serena/drift"
        try:
            response = await self._http.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception as exc:
            logger.debug(f"serena_drift failed: {exc}")
        return None

    async def serena_align(self) -> Optional[dict]:
        """Check Mladenc alignment score via Serena."""
        url = f"{self.base_url}/api/serena/align"
        try:
            response = await self._http.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception as exc:
            logger.debug(f"serena_align failed: {exc}")
        return None


# ============================================================
# Strategy Planner (Serena‑aware)
# ============================================================

class Planner:
    """
    Stateless strategy engine.
    Given Gordon's current mental GameState, returns the next command(s) to execute.
    """

    # Orientation commands — run once at startup, includes Serena consultation
    ORIENTATION_SEQUENCE = [
        "whoami",
        "status",
        "help | head -20",
        "ls",
        "cat /home/ghost/.profile",
        "agents",
        "arcs",
        "faction --list",
        # Serena consultation — Gordon aligns with the convergence layer
        "serena status",
        "serena walk",
        "serena align",
        "serena drift",
    ]

    # Exploration sweep
    EXPLORATION_DIRS = [
        "/sys", "/data", "/net", "/corp", "/logs",
        "/home/ghost/projects", "/home/ghost/scripts",
    ]

    # ARG investigation chain
    ARG_CHAIN = [
        "signal analyze 0",
        "myth palimpsest",
        "myth zohramien",
        "talk lexicon palimpsest",
        "manifest cathedral",
    ]

    # High‑value skill‑build commands
    SKILL_TARGETS = [
        "challenge list",
        "challenge next",
        "tutorial list",
        "tutorial next",
    ]

    def __init__(self, workspace: str, personality: str = "explorer"):
        self.workspace = Path(workspace)
        self.personality = personality
        self._orientation_idx = 0
        self._exploration_idx = 0
        self._arg_idx = 0
        self.playbook_path = self.workspace / "state" / "playbook.json"
        self.playbook = self._load_playbook()
        self.sequence_steps = self._load_personality_sequence()

    def _load_playbook(self) -> Dict[str, Any]:
        if not self.playbook_path.exists():
            return {}
        try:
            return json.loads(self.playbook_path.read_text())
        except Exception as exc:
            logger.warning("Failed to load playbook data: %s", exc)
            return {}

    def _load_personality_sequence(self) -> List[Dict[str, Any]]:
        arcs = self.playbook.get("arcs", {})
        arc_id = self.playbook.get("default_arc", "")
        arc = arcs.get(arc_id, {})
        persona = arc.get("personas", {}).get(self.personality, {})
        sequence = persona.get("sequence", [])
        return [step for step in sequence if step.get("command")]

    def next_commands(self, gs: GameState) -> List[str]:
        """Return 1‑3 commands Gordon should execute this tick."""
        if gs.phase == "ORIENTATION":
            if self._orientation_idx < len(self.sequence_steps):
                cmd = self.sequence_steps[self._orientation_idx]["command"]
                self._orientation_idx += 1
                return [cmd]
            if self._orientation_idx < len(self.ORIENTATION_SEQUENCE):
                cmd = self.ORIENTATION_SEQUENCE[self._orientation_idx]
                self._orientation_idx += 1
                return [cmd]
            else:
                gs.phase_idx += 1
                return []

        if gs.phase == "EXPLORATION":
            if self._exploration_idx < len(self.EXPLORATION_DIRS):
                d = self.EXPLORATION_DIRS[self._exploration_idx]
                self._exploration_idx += 1
                return [f"ls {d}", f"cat {d}/README 2>/dev/null || echo (empty)"]
            else:
                gs.phase_idx += 1
                return []

        if gs.phase == "SKILL-BUILD":
            cmds = ["status"]
            cmds.append(random.choice(self.SKILL_TARGETS))
            if gs.total_xp() > 500:
                gs.phase_idx += 1   # advance to FACTION
            return cmds

        if gs.phase == "FACTION":
            cmds = ["faction --list", "trust --matrix"]
            if gs.total_xp() > 1000 and not gs.has_beat("faction_joined"):
                cmds.append("faction join PHANTOM_CIRCUIT")
            if gs.has_beat("faction_joined"):
                gs.phase_idx += 1
            return cmds

        if gs.phase == "ARG":
            if self._arg_idx < len(self.ARG_CHAIN):
                cmd = self.ARG_CHAIN[self._arg_idx]
                self._arg_idx += 1
                return [cmd]
            gs.phase_idx += 1
            return []

        if gs.phase == "PRESTIGE":
            cmds = ["augment list", "augment buy OVERCLOCK_v2"]
            if gs.total_xp() > 5000:
                cmds.append("prestige check")
            if gs.has_beat("prestige_complete"):
                gs.phase_idx += 1
            return cmds

        # IDLE — heartbeat
        idle_cmds = ["status", "watcher", "signal analyze 1337"]
        return [random.choice(idle_cmds)]


# ============================================================
# Gordon Agent
# ============================================================

class GordonAgent:
    """The player‑god that inhabits Terminal Depths."""

    def __init__(
        self,
        game_api: str,
        model_router: str,
        workspace: str,
        personality: str = "explorer",
        session_id: Optional[str] = None,
        tick_delay: float = 2.0,
        verbose: bool = True
    ):
        self.api = GameAPI(game_api, session_id=session_id)
        self.router = ModelRouter(model_router)
        self.memory = GordonMemory(workspace=workspace)
        self.personality = personality
        self.planner = Planner(workspace=workspace, personality=personality)
        self.tick_delay = tick_delay
        self.verbose = verbose
        self.step_count = 0
        self.start_time = time.time()
        self.gs = GameState(
            session_id=session_id or "",
            player_level=0,
            current_location="terminal",
            inventory=[],
            current_health=100,
            max_health=100,
            available_commands=[],
            npcs_present=[],
            memory_snapshot={}
        )
        self._log_path = f"gordon_session_{int(time.time())}.jsonl"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.api.close()

    # ------------------------------------------------------------------
    # Serena meta‑intelligence
    # ------------------------------------------------------------------

    async def _serena_briefing(self) -> None:
        """
        Pull meta‑intelligence from Serena's REST API.
        Called at startup and every 20 ticks.
        Non‑fatal — if Serena is unavailable, Gordon continues without her.
        """
        # Alignment check
        align = await self.api.serena_align()
        if align and align.get("ok"):
            score = align.get("score", 0.0)
            aligned = align.get("aligned", False)
            icon = "✅" if aligned else "⚠"
            print(
                f"  [Serena→Gordon] {icon} Alignment: {score:.0%} "
                f"({'aligned' if aligned else 'drifting'})"
            )
            if not aligned:
                for chk in align.get("checks", []):
                    if not chk.get("passed"):
                        print(f"    ✕ {chk['name']}: {chk['message']}")

        # Drift check — Gordon logs critical signals
        drift = await self.api.serena_drift()
        if drift and drift.get("ok") and not drift.get("clean"):
            crit = drift.get("critical", 0)
            warn = drift.get("warnings", 0)
            print(f"  [Serena→Gordon] ⟁ Drift: {crit} critical, {warn} warn signals")
            for cat, signals in drift.get("signals", {}).items():
                if signals:
                    first = signals[0]
                    print(
                        f"    [{cat}] {first.get('path','?')}: "
                        f"{first.get('message','?')[:60]}"
                    )
            logger.info("Gordon drift briefing: %d critical, %d warn", crit, warn)

    # ------------------------------------------------------------------
    # State synchronisation
    # ------------------------------------------------------------------

    async def _sync_state(self) -> None:
        """Pull state from API and update our mental model."""
        raw = await self.api.game_state()
        if raw:
            state = raw.get("state", raw)
            self.gs.player_level = state.get("level", self.gs.player_level)
            self.gs.current_location = state.get("current_layer", self.gs.current_location)
            self.gs.available_commands = raw.get("commands", self.gs.available_commands)
            self.gs.xp = state.get("skills", self.gs.xp)
            self.gs.flags = state.get("flags", self.gs.flags)
            self.gs.beats = state.get("story_beats", raw.get("beats", self.gs.beats))
            self.gs.achievements = state.get("achievements", self.gs.achievements)
            self.gs.cwd = raw.get("cwd", self.gs.cwd)
            self.gs.commands_run = state.get("commands_run", self.gs.commands_run)
            self.gs.tutorial_step = state.get("tutorial_step", self.gs.tutorial_step)
            self.gs.is_root = raw.get("is_root", self.gs.is_root)

    # ------------------------------------------------------------------
    # Action planning (model router + fallback to planner)
    # ------------------------------------------------------------------

    async def _plan_action(self) -> ActionDecision:
        """
        Decide next action, first consulting the model router.
        If router unavailable, fall back to the heuristic planner.
        """
        # Build prompt for router
        state_desc = (
            f"Level {self.gs.player_level} | Location {self.gs.current_location} | "
            f"Health {self.gs.current_health}/{self.gs.max_health} | "
            f"XP {self.gs.total_xp()} | Phase {self.gs.phase}"
        )
        task_type = f"gameplay_{self.gs.phase.lower()}"
        model_info = await self.router.select_model(
            task_type=task_type,
            required_capabilities=["reasoning", "tools"]
        )
        model_used = model_info["model_id"] if model_info else "heuristic"

        # In a full implementation, we would call an LLM here.
        # For now, use the heuristic planner.
        commands = self.planner.next_commands(self.gs)
        if not commands:
            # Shouldn't happen; fallback
            command = "status"
        else:
            command = commands[0]  # planner may return multiple; we take first for now

        decision = ActionDecision(
            command=command,
            reasoning=f"Heuristic planner (phase {self.gs.phase})",
            model_used=model_used,
            confidence=0.7,
            timestamp=datetime.now().isoformat()
        )
        return decision

    # ------------------------------------------------------------------
    # Command execution and logging
    # ------------------------------------------------------------------

    async def _execute_step(self) -> bool:
        """Execute one step of gameplay."""
        # 1. Sync state (every 5 ticks)
        if self.gs.tick % 5 == 1:
            await self._sync_state()

        # 2. Serena briefing every 20 ticks
        if self.gs.tick % 20 == 0 and self.gs.tick > 0:
            await self._serena_briefing()

        # 3. Plan next action
        decision = await self._plan_action()
        cmd = decision.command

        # 4. Execute command
        output = await self.api.command(cmd)
        self.gs.last_output = output

        # 5. Determine outcome (heuristic: non‑error lines = success)
        has_error = any(line.get("t") == "error" for line in output)
        outcome = "failure" if has_error else "success"

        # 6. Store in memory
        output_snippet = json.dumps(output[:5]) if len(output) > 5 else json.dumps(output)
        self.memory.store_experience(
            session_id=self.api.session_id or "unknown",
            state=self.gs,
            action=cmd,
            result=output_snippet,
            outcome=outcome,
            model_used=decision.model_used,
            learning=decision.reasoning
        )

        # 7. Update strategy pattern
        pattern = cmd.split()[0]  # first word
        self.memory.update_strategy(pattern, outcome == "success")

        self.step_count += 1
        self.gs.tick += 1

        if self.verbose:
            self._print_output(cmd, output)

        return True

    # ------------------------------------------------------------------
    # Output formatting
    # ------------------------------------------------------------------

    def _print_output(self, cmd: str, output: List[dict]) -> None:
        """Pretty‑print command output."""
        print(f"\n  [{self.gs.phase}] $ {cmd}")
        for line in output[:20]:   # cap display at 20 lines
            t = line.get("t", "info")
            s = line.get("s", "")
            prefix = {
                "error":   "✗",
                "success": "✔",
                "system":  "⊕",
                "warn":    "⚠",
                "story":   "◈",
                "xp":      "★",
            }.get(t, " ")
            print(f"    {prefix} {s}")
        if len(output) > 20:
            print(f"    … ({len(output)-20} more lines)")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(self, max_steps: Optional[int] = None) -> None:
        """Run autonomous game loop."""

        # Create session if not provided
        if not self.api.session_id:
            if not await self.api.create_session():
                logger.error("Failed to create game session")
                return
        else:
            logger.info(f"Using existing session: {self.api.session_id}")

        print(f"\n{'═'*58}")
        print(f"  GORDON v{GORDON_VERSION} — Autonomous Terminal Depths Agent")
        print(f"  Target : {self.api.base_url}")
        print(f"  Session: {self.api.session_id}")
        print(f"  Persona: {self.personality}")
        print(f"  Serena : active (ΨΞΦΩ meta‑intelligence)")
        print(f"{'═'*58}\n")

        # Initial Serena briefing — align before first move
        await self._serena_briefing()

        try:
            while True:
                if max_steps and self.step_count >= max_steps:
                    print(f"\n  [Gordon] max steps ({max_steps}) reached — exiting.")
                    break

                success = await self._execute_step()
                if not success:
                    await asyncio.sleep(2)
                    continue

                await asyncio.sleep(self.tick_delay)

        except KeyboardInterrupt:
            print("\n\n  [Gordon] Interrupted. Session log saved to:", self._log_path)
        except Exception as exc:
            logger.exception(f"Gordon crashed: {exc}")
            raise
        finally:
            self._print_summary()

    def _print_summary(self):
        """Print session summary."""
        elapsed = time.time() - self.start_time
        logger.info("")
        logger.info("╔════════════════════════════════════════════════════╗")
        logger.info("║ Gordon Gameplay Summary                            ║")
        logger.info("╠════════════════════════════════════════════════════╣")
        logger.info(f"║ Steps Executed:        {self.step_count:<30} ║")
        logger.info(f"║ Time Elapsed:          {elapsed:.1f}s{' '*20} ║")
        logger.info(f"║ Learning Records:      {self.memory.chronicle_path}{' '*8} ║")
        logger.info("╚════════════════════════════════════════════════════╝")
        logger.info("")


# ============================================================
# CLI Entry Point
# ============================================================

async def main():
    parser = argparse.ArgumentParser(
        description="Gordon: Autonomous Terminal Depths Player Agent with Serena Integration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Game API base URL")
    parser.add_argument(
        "--session",
        default=f"gordon-{uuid.uuid4().hex[:8]}",
        help="Session ID (will be created if doesn't exist)"
    )
    parser.add_argument(
        "--mode",
        choices=["autonomous", "debug", "orchestrate"],
        default=os.getenv("GORDON_MODE", "autonomous"),
        help="Mode of operation"
    )
    parser.add_argument("--steps", type=int, default=None, help="Max steps (debug mode)")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between ticks")
    parser.add_argument("--quiet", action="store_true", help="Suppress per‑command output")
    parser.add_argument("--game-api", default=None, help="Override game API URL")
    parser.add_argument("--model-router", default=None, help="Override model router URL")
    parser.add_argument("--workspace", default=None, help="Workspace root")
    parser.add_argument(
        "--personality",
        choices=["explorer", "completionist"],
        default="explorer",
        help="Planning personality for the run"
    )

    args = parser.parse_args()

    # Determine URLs from env or args
    game_api = args.game_api or args.url or os.getenv("GORDON_GAME_API", DEFAULT_URL)
    model_router = args.model_router or os.getenv("GORDON_MODEL_ROUTER", "http://localhost:9001")
    # Resolve workspace: explicit arg > env var > directory containing this script
    _script_dir = str(Path(__file__).parent.resolve())
    workspace = args.workspace or os.getenv("WORKSPACE_ROOT") or _script_dir

    # Create agent
    async with GordonAgent(
        game_api=game_api,
        model_router=model_router,
        workspace=workspace,
        personality=args.personality,
        session_id=args.session,
        tick_delay=args.delay,
        verbose=not args.quiet
    ) as gordon:
        if args.mode == "autonomous":
            logger.info("🚀 Gordon entering autonomous mode...")
            await gordon.run(max_steps=None)
        elif args.mode == "debug":
            logger.info(f"🐛 Debug mode: {args.steps or 'unlimited'} steps")
            await gordon.run(max_steps=args.steps or 10)
        elif args.mode == "orchestrate":
            logger.info("🎼 Orchestrate mode (not yet implemented)")
            # Future: delegate tasks to Continue, Roo, SimulatedVerse


if __name__ == "__main__":
    asyncio.run(main())
