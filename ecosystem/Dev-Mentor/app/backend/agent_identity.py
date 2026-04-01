"""
DevMentor — Agent Identity System
═══════════════════════════════════════════════════════════════════════════════
SQLite-backed agent registration for AI agents, bots, LLMs, and human players
operating outside of Replit Auth (CLI, Docker, IDE, LLM tool calls, etc.)

Any software with HTTP/curl access can register as an agent and maintain
persistent progress across sessions, even across different surfaces.

Agent Types:
  human         — traditional human player
  claude        — Anthropic Claude (Sonnet, Opus, Haiku)
  copilot       — GitHub Copilot (any model)
  codex         — OpenAI Codex / GPT-4 tool-calling agents
  ollama        — Ollama local LLM (any model)
  gordon        — Docker Gordon AI agent
  roo_code      — Roo Code (Cline fork)
  lm_studio     — LM Studio local inference
  open_webui    — Open WebUI / LibreChat
  docker_agent  — Any agent running in Docker
  powershell_agent — PowerShell-based automation
  custom        — User-defined agent type

Usage:
    from app.backend.agent_identity import AgentDB
    db = AgentDB()
    rec = db.register("Claude", "claude@anthropic.terminal-depths", "claude")
    # rec.token  →  use in X-Agent-Token header
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# ── Storage path ───────────────────────────────────────────────────────────
_DB_DIR = Path(__file__).parent.parent.parent / "state"
_DB_DIR.mkdir(exist_ok=True)
_DB_PATH = _DB_DIR / "agents.db"

# ── Known agent types ──────────────────────────────────────────────────────
AGENT_TYPES = {
    "human":            "Human Player",
    "claude":           "Anthropic Claude",
    "copilot":          "GitHub Copilot",
    "codex":            "OpenAI Codex / GPT agent",
    "ollama":           "Ollama Local LLM",
    "gordon":           "Docker Gordon",
    "roo_code":         "Roo Code (Cline)",
    "lm_studio":        "LM Studio",
    "open_webui":       "Open WebUI / LibreChat",
    "chatdev":          "ChatDev Agent",
    "nusyq":            "NuSyQ-Hub Agent",
    "serena":           "Serena (Convergence Layer)",
    "docker_agent":     "Generic Docker Agent",
    "powershell_agent": "PowerShell Automation",
    "bash_agent":       "Bash Automation",
    "vsc_extension":    "VS Code Extension",
    "obsidian":         "Obsidian Plugin",
    "custom":           "Custom / Unknown",
}


@dataclass
class AgentRecord:
    agent_id: str
    name: str
    email: str
    agent_type: str
    token: str
    session_id: Optional[str] = None
    registered_at: str = ""
    last_seen: str = ""
    play_count: int = 0
    capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "email": self.email,
            "agent_type": self.agent_type,
            "agent_type_label": AGENT_TYPES.get(self.agent_type, "Unknown"),
            "session_id": self.session_id,
            "registered_at": self.registered_at,
            "last_seen": self.last_seen,
            "play_count": self.play_count,
            "capabilities": self.capabilities,
        }

    def public_dict(self) -> dict:
        d = self.to_dict()
        d.pop("session_id", None)
        return d


class AgentDB:
    """SQLite-backed agent identity store."""

    def __init__(self, db_path: Path = _DB_PATH):
        self._path = db_path
        self._init_db()

    # ── Internal ──────────────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id      TEXT PRIMARY KEY,
                    name          TEXT NOT NULL,
                    email         TEXT NOT NULL UNIQUE,
                    agent_type    TEXT NOT NULL DEFAULT 'custom',
                    token         TEXT NOT NULL UNIQUE,
                    session_id    TEXT,
                    registered_at TEXT NOT NULL,
                    last_seen     TEXT NOT NULL,
                    play_count    INTEGER NOT NULL DEFAULT 0,
                    capabilities  TEXT NOT NULL DEFAULT '[]'
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_token ON agents (token)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_email ON agents (email)"
            )
            conn.commit()

    def _row_to_record(self, row) -> AgentRecord:
        return AgentRecord(
            agent_id=row["agent_id"],
            name=row["name"],
            email=row["email"],
            agent_type=row["agent_type"],
            token=row["token"],
            session_id=row["session_id"],
            registered_at=row["registered_at"],
            last_seen=row["last_seen"],
            play_count=row["play_count"],
            capabilities=json.loads(row["capabilities"] or "[]"),
        )

    @staticmethod
    def _make_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def _make_id(email: str) -> str:
        return "agt_" + hashlib.sha256(email.encode()).hexdigest()[:16]

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Public API ─────────────────────────────────────────────────────────

    def register(
        self,
        name: str,
        email: str,
        agent_type: str = "custom",
        capabilities: Optional[List[str]] = None,
    ) -> AgentRecord:
        """Register a new agent. If email already exists, return existing record."""
        existing = self.get_by_email(email)
        if existing:
            return existing

        agent_id = self._make_id(email)
        token = self._make_token()
        now = self._now()
        caps = capabilities or []

        with self._conn() as conn:
            conn.execute(
                """INSERT INTO agents
                   (agent_id, name, email, agent_type, token,
                    registered_at, last_seen, play_count, capabilities)
                   VALUES (?,?,?,?,?,?,?,0,?)""",
                (agent_id, name, email, agent_type, token,
                 now, now, json.dumps(caps)),
            )
            conn.commit()

        return AgentRecord(
            agent_id=agent_id, name=name, email=email,
            agent_type=agent_type, token=token,
            registered_at=now, last_seen=now,
            play_count=0, capabilities=caps,
        )

    def login(self, email: str) -> Optional[AgentRecord]:
        """Retrieve agent by email, update last_seen."""
        rec = self.get_by_email(email)
        if rec:
            self._touch(rec.token)
        return rec

    def get_by_token(self, token: str) -> Optional[AgentRecord]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM agents WHERE token = ?", (token,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_record(row)

    def get_by_email(self, email: str) -> Optional[AgentRecord]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM agents WHERE email = ?", (email,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_record(row)

    def get_by_id(self, agent_id: str) -> Optional[AgentRecord]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM agents WHERE agent_id = ?", (agent_id,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_record(row)

    def link_session(self, token: str, session_id: str) -> bool:
        """Associate a game session_id with an agent token."""
        with self._conn() as conn:
            n = conn.execute(
                "UPDATE agents SET session_id=?, last_seen=?, play_count=play_count+1 "
                "WHERE token=?",
                (session_id, self._now(), token),
            ).rowcount
            conn.commit()
        return n > 0

    def list_all(self, limit: int = 100) -> List[AgentRecord]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM agents ORDER BY last_seen DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def _touch(self, token: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE agents SET last_seen=? WHERE token=?",
                (self._now(), token),
            )
            conn.commit()


# ── Singleton ──────────────────────────────────────────────────────────────
_db: Optional[AgentDB] = None


def get_agent_db() -> AgentDB:
    global _db
    if _db is None:
        _db = AgentDB()
    return _db


# ── Capability Manifest ────────────────────────────────────────────────────
def build_capability_manifest() -> dict:
    """
    Machine-readable manifest of all Terminal Depths capabilities.
    Designed for consumption by Claude, Copilot, Codex, and any LLM agent.
    """
    return {
        "name": "Terminal Depths",
        "description": (
            "A cyberpunk browser terminal RPG and learning environment. "
            "Explore a simulated Unix filesystem, interact with AI agents, "
            "uncover a conspiracy, and level up real development skills."
        ),
        "version": "2.0",
        "entry_points": {
            "web": "https://{domain}/game/",
            "api_command": "POST /api/game/command",
            "api_agent": "POST /api/agent/command",
            "api_register": "POST /api/agent/register",
            "api_capabilities": "GET /api/capabilities",
            "api_state": "GET /api/game/state",
            "api_docs": "GET /api/docs",
            "cli": "python cli/devmentor.py play",
            "bootstrap_python": "python bootstrap/td_quickstart.py",
            "bootstrap_bash": "bash bootstrap/td_quickstart.sh",
            "bootstrap_powershell": "pwsh bootstrap/td_quickstart.ps1",
            "bootstrap_node": "node bootstrap/td_node.js",
            "mcp": "JSON-RPC 2.0 at /mcp",
        },
        "agent_guidelines": {
            "start": (
                "POST /api/agent/register with {name, email, agent_type} to get a token. "
                "Then POST /api/agent/command with {command} and X-Agent-Token header. "
                "Your game session is persistent across connections."
            ),
            "discovery": (
                "Run 'help' to see all commands. Run 'tutorial' to start learning. "
                "Run 'quests' to see active objectives. Run 'hive' to talk to other agents. "
                "Run 'lore' to see the narrative. Run 'map' to see the network."
            ),
            "learning": (
                "The game teaches real Unix/Linux skills. Every command you run teaches you. "
                "Run 'cat /etc/passwd', 'ps aux', 'netstat', 'find / -name *.key' to explore. "
                "Complete challenges to earn XP and unlock story beats."
            ),
            "narrative": (
                "You are Ghost, a hacker on node-7. CHIMERA is not surveillance — it's containment. "
                "Someone in the network is a mole. The Residual is a pre-existing intelligence. "
                "The kernel.boot file has impossible timestamps. Ask Serena about the third path."
            ),
        },
        "command_categories": {
            "filesystem": {
                "commands": ["ls", "cd", "cat", "find", "grep", "pwd", "mkdir", "rm", "cp", "mv", "ln", "chmod", "stat", "tree", "file"],
                "description": "Navigate and read the simulated filesystem. Contains lore, secrets, and CHIMERA data.",
            },
            "process": {
                "commands": ["ps", "top", "kill", "jobs", "fg", "bg", "nohup", "pidof", "pgrep"],
                "description": "View and control processes. watcher_eternal PID 1 is always watching.",
            },
            "network": {
                "commands": ["ping", "nmap", "netstat", "curl", "wget", "nc", "ssh", "dig", "whois", "traceroute", "ifconfig", "ip"],
                "description": "Explore the simulated network. chimera-control on 10.0.1.254 is restricted.",
            },
            "agents": {
                "commands": ["talk", "msg", "whisper", "dm", "agents", "hive", "eavesdrop"],
                "description": "Interact with 71 AI agents. Each has distinct personality, faction, trust level.",
            },
            "story": {
                "commands": ["lore", "map", "arcs", "chronicle", "mail", "quests", "quest"],
                "description": "Progress the narrative. CHIMERA, the mole, the Residual, and ΨΞΦΩ await.",
            },
            "economy": {
                "commands": ["bank", "research", "colony", "resources"],
                "description": "Manage credits, research technologies, build colony infrastructure.",
            },
            "puzzles": {
                "commands": ["logic", "sat", "sort", "fsm", "dp", "set", "tis100"],
                "description": "Math/logic puzzles that teach CS fundamentals through gameplay.",
            },
            "meta": {
                "commands": ["theme", "sleep", "defend", "augment", "skill", "level"],
                "description": "Character progression, customization, dream sequences, and minigames.",
            },
            "dev": {
                "commands": ["git", "python3", "node", "make", "vim", "nano", "diff", "patch"],
                "description": "Simulated development tools for learning real workflows.",
            },
            "special": {
                "commands": ["serena", "zero", "ΨΞΦΩ", "restart tutorial", "forensics", "tor", "steg"],
                "description": "Secret commands, ARG triggers, and advanced gameplay surfaces.",
            },
        },
        "story_context": {
            "current_arc": "CHIMERA Exposure",
            "key_files": [
                "/var/log/kernel.boot",
                "/opt/chimera/config/master.key",
                "/opt/chimera/core/ZERO_SPECIFICATION.md",
                "/var/log/residual_contact.log",
                "/var/log/agent_comms.log",
                "/home/ghost/.watcher_note",
            ],
            "key_agents": ["Ada-7", "Raven", "Watcher", "Nova", "Serena", "Cypher", "Gordon"],
            "secret_triggers": ["zero", "ΨΞΦΩ", "mole", "chimera", "simulation", "loop", "nova is the enemy"],
        },
        "xp_system": {
            "skills": ["terminal", "networking", "security", "programming", "cryptography",
                       "social_engineering", "forensics", "scripting", "git"],
            "level_cap": 50,
            "xp_sources": ["commands", "challenges", "story_beats", "agent_interactions", "puzzles"],
        },
        "auth": {
            "human": "Replit Auth (optional) — use /auth/login",
            "agent": "Agent Token (required) — POST /api/agent/register → X-Agent-Token header",
            "anonymous": "Any session_id works — progress is tied to session persistence",
        },
    }
