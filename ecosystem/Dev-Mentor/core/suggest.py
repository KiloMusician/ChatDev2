"""
core/suggest.py — Deterministic command suggestion engine.

Offline-first. No AI required for the base layer.
Optional LLM layer if configured.

Usage:
    from core.suggest import get_suggester
    s = get_suggester()
    suggestions = s.get_suggestions("ls", context=game_state_dict)
"""
from __future__ import annotations

import difflib
import random
from typing import Any, Dict, List, Optional, Set


# ─── Static command corpus ─────────────────────────────────────────────────────

GAME_COMMANDS: Set[str] = {
    # Core navigation
    "help", "ls", "cd", "cat", "pwd", "whoami", "man", "history",
    "head", "tail", "grep", "find", "stat", "file", "wc",
    "echo", "printf", "tee", "sort", "uniq", "cut", "awk", "sed",
    "mkdir", "touch", "rm", "mv", "cp", "chmod", "chown",
    "ps", "kill", "top", "df", "du", "free", "uname", "hostname", "uptime",
    # Network
    "ping", "curl", "wget", "nmap", "ssh", "nc", "netstat", "ss", "dig",
    "ifconfig", "ip", "traceroute",
    # Security
    "sudo", "john", "hashcat", "hydra", "gobuster", "sqlmap",
    "gdb", "strace", "binwalk", "base64", "xxd", "md5sum", "sha256sum",
    # Game-specific
    "status", "tutorial", "help", "hint", "wiki", "map", "agents",
    "talk", "msg", "ask", "trust", "faction", "quest", "quests",
    "lore", "chronicle", "arcs", "objectives",
    "skill", "skills", "xp", "achievements", "leaderboard",
    "hack", "exploit", "scan", "ascend", "root",
    "bank", "research", "colony", "hive", "cultivate", "bazaar",
    "meditate", "introspect", "haiku", "confess",
    "serena", "gordon", "skyclaw", "ada",
    "timer", "anchor", "remnant", "proficiency",
    "expose", "interrogate", "signal", "suspicion",
    "deck", "diary", "fates", "residual",
    "panel", "panels", "theme", "compress",
    "context", "plan", "surface", "environment",
    "tis100", "logic", "set", "sat", "sort", "fsm", "dp",
}


# ─── Context-aware suggestion rules ───────────────────────────────────────────

# Maps game state keys → list of (condition, suggested_commands, reason)
SUGGESTION_RULES: List[Dict] = [
    {
        "condition": lambda ctx: ctx.get("tutorial_step", 0) == 0,
        "commands": ["tutorial", "help", "ls"],
        "reason": "Good starting point",
    },
    {
        "condition": lambda ctx: ctx.get("level", 1) < 3 and not ctx.get("has_beat_ls"),
        "commands": ["ls", "pwd", "cat /etc/passwd"],
        "reason": "Explore your environment first",
    },
    {
        "condition": lambda ctx: not ctx.get("faction"),
        "commands": ["faction", "lore ada", "lore resistance"],
        "reason": "Choose your allegiance",
    },
    {
        "condition": lambda ctx: ctx.get("consciousness_level", 0) < 10,
        "commands": ["lore chimera", "meditate", "introspect", "haiku"],
        "reason": "Raise consciousness to unlock deeper systems",
    },
    {
        "condition": lambda ctx: ctx.get("consciousness_level", 0) >= 25 and not ctx.get("has_beat_reality"),
        "commands": ["reality", "cat /proc/.consciousness"],
        "reason": "You have enough awareness — pierce the veil",
    },
    {
        "condition": lambda ctx: ctx.get("xp", 0) > 500 and not ctx.get("has_beat_root_achieved"),
        "commands": ["sudo find /opt -name '*.key'", "exploit", "hack nexus-core"],
        "reason": "You're ready for privilege escalation",
    },
    {
        "condition": lambda ctx: len(ctx.get("mole_clues_found", [])) > 0
                     and not ctx.get("has_beat_mole_exposed"),
        "commands": ["expose", "ls /home/ghost/.investigation/", "cat suspect_list.txt"],
        "reason": "Follow the mole investigation",
    },
    {
        "condition": lambda ctx: ctx.get("runtime") == "docker",
        "commands": ["surface", "context", "plan"],
        "reason": "Check ecosystem status in Docker",
    },
    {
        "condition": lambda ctx: ctx.get("runtime") == "vscode",
        "commands": ["surface", "help", "tutorial"],
        "reason": "You're in VS Code — the workspace is your control panel",
    },
    {
        "condition": lambda ctx: ctx.get("commands_run", 0) > 100
                     and not ctx.get("has_beat_chimera_diff"),
        "commands": ["chimera", "lore chimera", "wiki CHIMERA"],
        "reason": "You've earned deeper CHIMERA access",
    },
]


class Suggester:
    """
    Deterministic + optional LLM suggestion engine.
    Offline-first: the deterministic layer always works.
    """

    def __init__(self, commands: Optional[Set[str]] = None, use_llm: bool = False):
        self.commands = commands or GAME_COMMANDS
        self.use_llm = use_llm
        self._llm_fn = None
        if use_llm:
            try:
                from services.inference import generate as llm_generate
                self._llm_fn = llm_generate
            except ImportError:
                pass

    # ── Fuzzy matching ────────────────────────────────────────────────────────

    def fuzzy_match(self, partial: str, cutoff: float = 0.55) -> List[str]:
        """Return close command matches using difflib."""
        return difflib.get_close_matches(partial, self.commands, n=3, cutoff=cutoff)

    # ── Deterministic rules ───────────────────────────────────────────────────

    def deterministic_suggestions(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Return suggestions based on game state, environment, and story progress."""
        out: List[Dict[str, str]] = []
        seen: Set[str] = set()
        for rule in SUGGESTION_RULES:
            try:
                if rule["condition"](context):
                    for cmd in rule["commands"]:
                        if cmd not in seen:
                            seen.add(cmd)
                            out.append({"command": cmd, "reason": rule["reason"]})
                    if len(out) >= 5:
                        break
            except Exception:
                continue
        return out[:5]

    # ── Combined API ──────────────────────────────────────────────────────────

    def get_suggestions(
        self,
        partial: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, str]]:
        """
        Return up to 5 suggestions as list of {"command": ..., "reason": ...}.
        Combines: fuzzy → deterministic → (optional LLM).
        Always works offline.
        """
        context = context or {}
        results: List[Dict[str, str]] = []
        seen: Set[str] = set()

        # 1. Fuzzy match on partial input
        if partial:
            for cmd in self.fuzzy_match(partial):
                if cmd not in seen:
                    seen.add(cmd)
                    results.append({"command": cmd, "reason": f"Did you mean `{cmd}`?"})

        # 2. Deterministic rules
        for s in self.deterministic_suggestions(context):
            if s["command"] not in seen:
                seen.add(s["command"])
                results.append(s)
            if len(results) >= 5:
                break

        # 3. LLM (optional, async not available here — skip in sync context)
        # Caller may call llm_suggestions() separately if async context available.

        return results[:5]

    def quick_chip(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Return a single `suggest` chip string (e.g. 'ls · pwd · status')."""
        sugs = self.get_suggestions(context=context)
        cmds = [s["command"].split()[0] for s in sugs[:3]]
        return " · ".join(cmds) if cmds else "help · status · tutorial"

    def random_tip(self) -> str:
        """Return a random command tip — works with zero context."""
        tips = [
            "Try `lore chimera` to deepen your consciousness.",
            "Type `msg ada hello` — Ada has information only she will share.",
            "Use `timer` to check the containment countdown.",
            "Run `proficiency matrix` to see which language abilities are unlocked.",
            "Type `faction rep` to see your standing with all factions.",
            "Try `meditate` when you're unsure what to do next.",
            "Use `map` to visualize the network topology.",
            "Type `signals` or `signal scan` to find hidden frequencies.",
            "`introspect` unlocks at consciousness level 30.",
            "The mole is in the Resistance. Find them with `expose <agent>`.",
        ]
        return random.choice(tips)


# ─── Singleton ─────────────────────────────────────────────────────────────────

_instance: Optional[Suggester] = None


def get_suggester(commands: Optional[Set[str]] = None, use_llm: bool = False) -> Suggester:
    global _instance
    if _instance is None:
        _instance = Suggester(commands=commands, use_llm=use_llm)
    return _instance
