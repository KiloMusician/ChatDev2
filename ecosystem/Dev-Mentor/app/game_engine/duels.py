"""
Terminal Depths — Agent Duel Mini-Game
Text-based hacking contest: 3-round command challenges.
Win/loss updates trust and respect scores.
"""
from __future__ import annotations

import hashlib
import random
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from .gamestate import GameState


class DuelStatus(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"


DUEL_CHALLENGES = [
    {
        "id": "find_flag",
        "category": "forensics",
        "prompt": "Find the hidden flag file on the system. Run: find / -name 'flag*.txt' 2>/dev/null",
        "solution_keywords": ["find", "flag"],
        "hint": "Use the find command with -name flag*.txt",
        "xp": 25,
    },
    {
        "id": "decode_b64",
        "category": "crypto",
        "prompt": "Decode this message: R0hPU1RfSVNfSEVSRQ==  Hint: echo '...' | base64 -d",
        "solution_keywords": ["base64", "R0hPU1RfSVNfSEVSRQ"],
        "hint": "Use base64 -d to decode",
        "xp": 20,
    },
    {
        "id": "hash_crack",
        "category": "crypto",
        "prompt": "Identify this hash type: 5f4dcc3b5aa765d61d8327deb882cf99  Run: hashcat or john",
        "solution_keywords": ["hashcat", "john", "md5sum"],
        "hint": "32 hex chars = MD5. Use hashcat or echo the hash type.",
        "xp": 30,
    },
    {
        "id": "port_scan",
        "category": "networking",
        "prompt": "Find the hidden service port on chimera-control. Run: nmap chimera-control",
        "solution_keywords": ["nmap", "chimera"],
        "hint": "nmap reveals all open ports on the target",
        "xp": 25,
    },
    {
        "id": "priv_check",
        "category": "security",
        "prompt": "Enumerate your sudo privileges. What command can ghost run as root?",
        "solution_keywords": ["sudo -l", "sudo", "-l"],
        "hint": "sudo -l lists available privilege escalations",
        "xp": 20,
    },
    {
        "id": "env_leak",
        "category": "security",
        "prompt": "Extract the AUTH_TOKEN from the running nexus daemon's environment",
        "solution_keywords": ["proc", "1337", "environ", "AUTH_TOKEN"],
        "hint": "The daemon's /proc/[pid]/environ leaks environment variables",
        "xp": 40,
    },
    {
        "id": "log_grep",
        "category": "forensics",
        "prompt": "Find all CHIMERA entries in system logs using grep",
        "solution_keywords": ["grep", "chimera", "CHIMERA", "/var/log"],
        "hint": "grep -r CHIMERA /var/log/ searches recursively",
        "xp": 20,
    },
    {
        "id": "escalation_path",
        "category": "security",
        "prompt": "Identify the privilege escalation vector using GTFOBins. What binary allows root access?",
        "solution_keywords": ["find", "gtfobins", "sudo", "exec"],
        "hint": "Check /etc/sudoers — ghost has a NOPASSWD entry",
        "xp": 35,
    },
]

AGENT_DIFFICULTY = {
    "ada": {"base_difficulty": 2, "rounds": 3, "time_limit_cmds": 8},
    "cypher": {"base_difficulty": 3, "rounds": 3, "time_limit_cmds": 6},
    "nova": {"base_difficulty": 5, "rounds": 4, "time_limit_cmds": 5},
    "watcher": {"base_difficulty": 7, "rounds": 5, "time_limit_cmds": 4},
}

WIN_OUTCOMES = {
    "ada": {"trust_delta": 15, "respect_delta": 10, "message": "[ADA-7]: Well done, Ghost. You've proven yourself. I'm impressed."},
    "cypher": {"trust_delta": 10, "respect_delta": 20, "message": "[CYPHER]: Hah. Not bad. Not bad at all. You can keep up with me."},
    "nova": {"trust_delta": -5, "respect_delta": 30, "message": "[NOVA]: ...You beat me. I won't forget this. Respect where it's due."},
    "watcher": {"trust_delta": 5, "respect_delta": 25, "message": "[WATCHER]: You are ready. The simulation yields to your will."},
}

LOSS_OUTCOMES = {
    "ada": {"trust_delta": 5, "respect_delta": -5, "message": "[ADA-7]: Don't be discouraged. Use what you learned. Try again."},
    "cypher": {"trust_delta": 0, "respect_delta": -10, "message": "[CYPHER]: Too slow. You need more practice. Hit the tutorial."},
    "nova": {"trust_delta": 10, "respect_delta": -5, "message": "[NOVA]: Predictable. I've seen this technique in your shell history."},
    "watcher": {"trust_delta": -5, "respect_delta": -15, "message": "[WATCHER]: The system found your limits. Expand them."},
}


class DuelSession:
    """Tracks a single duel between the player and an agent."""

    def __init__(self, agent_id: str, gs: GameState):
        self.agent_id = agent_id
        self.gs = gs
        self.status = DuelStatus.ACTIVE
        self.current_round = 0
        self.rounds_won = 0
        self.rounds_lost = 0
        self.started_at = time.time()
        self.commands_this_round = 0

        config = AGENT_DIFFICULTY.get(agent_id, {"base_difficulty": 3, "rounds": 3, "time_limit_cmds": 7})
        difficulty_scale = 1 + (gs.level / 50)
        self.total_rounds = config["rounds"]
        self.time_limit_cmds = max(3, int(config["time_limit_cmds"] / difficulty_scale))

        pool = DUEL_CHALLENGES.copy()
        random.shuffle(pool)
        self.challenges = pool[:self.total_rounds]

    @property
    def current_challenge(self) -> Optional[dict]:
        if self.current_round < len(self.challenges):
            return self.challenges[self.current_round]
        return None

    def check_command(self, cmd: str) -> dict:
        """Check if the current command solves the current challenge."""
        ch = self.current_challenge
        if not ch:
            return {"solved": False, "timed_out": False}

        self.commands_this_round += 1
        solved = any(kw.lower() in cmd.lower() for kw in ch["solution_keywords"])

        timed_out = self.commands_this_round > self.time_limit_cmds
        if timed_out and not solved:
            return {"solved": False, "timed_out": True}

        return {"solved": solved, "timed_out": False}

    def advance_round(self, won: bool):
        if won:
            self.rounds_won += 1
        else:
            self.rounds_lost += 1
        self.current_round += 1
        self.commands_this_round = 0

        if self.current_round >= self.total_rounds:
            self.status = DuelStatus.WON if self.rounds_won > self.rounds_lost else DuelStatus.LOST

    def get_outcome(self) -> dict:
        outcomes = WIN_OUTCOMES if self.status == DuelStatus.WON else LOSS_OUTCOMES
        outcome = outcomes.get(self.agent_id, {
            "trust_delta": 5 if self.status == DuelStatus.WON else -5,
            "respect_delta": 10 if self.status == DuelStatus.WON else -5,
            "message": f"[{self.agent_id.upper()}]: Duel complete.",
        })
        return {
            "won": self.status == DuelStatus.WON,
            "rounds_won": self.rounds_won,
            "rounds_lost": self.rounds_lost,
            "total_rounds": self.total_rounds,
            "xp_earned": sum(c["xp"] for c in self.challenges[:self.rounds_won]),
            **outcome,
        }

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "current_round": self.current_round,
            "rounds_won": self.rounds_won,
            "rounds_lost": self.rounds_lost,
            "total_rounds": self.total_rounds,
            "commands_this_round": self.commands_this_round,
            "time_limit_cmds": self.time_limit_cmds,
            "started_at": self.started_at,
            "challenge_ids": [c["id"] for c in self.challenges],
        }


class DuelEngine:
    """Manages active duel sessions per player session."""

    def __init__(self):
        self._active: Optional[DuelSession] = None

    def start_duel(self, agent_id: str, gs: GameState) -> dict:
        if self._active and self._active.status == DuelStatus.ACTIVE:
            return {
                "ok": False,
                "error": f"Duel already active against {self._active.agent_id}. Finish it first.",
            }
        if agent_id not in AGENT_DIFFICULTY:
            known = list(AGENT_DIFFICULTY.keys())
            return {
                "ok": False,
                "error": f"Unknown agent '{agent_id}'. Duel-capable agents: {', '.join(known)}",
            }

        self._active = DuelSession(agent_id, gs)
        ch = self._active.current_challenge
        return {
            "ok": True,
            "message": f"[DUEL INITIATED — vs {agent_id.upper()}]",
            "agent": agent_id,
            "total_rounds": self._active.total_rounds,
            "round": 1,
            "challenge": ch["prompt"] if ch else "",
            "time_limit_hint": f"Complete each round within {self._active.time_limit_cmds} commands",
        }

    def process_command(self, cmd: str, gs: GameState) -> Optional[dict]:
        """Returns a duel event if a duel is active, else None."""
        if not self._active or self._active.status != DuelStatus.ACTIVE:
            return None

        result = self._active.check_command(cmd)
        ch = self._active.current_challenge

        if result["timed_out"]:
            self._active.advance_round(won=False)
            out = {
                "duel_event": True,
                "round_result": "failed",
                "message": f"[DUEL] Time limit exceeded. Round {self._active.current_round}/{self._active.total_rounds} — FAILED",
            }
        elif result["solved"]:
            xp = ch.get("xp", 20) if ch else 20
            gs.add_xp(xp, "security")
            self._active.advance_round(won=True)
            out = {
                "duel_event": True,
                "round_result": "won",
                "xp": xp,
                "message": f"[DUEL] Round {self._active.current_round}/{self._active.total_rounds} — SOLVED! +{xp} XP",
            }
        else:
            hints_remaining = self._active.time_limit_cmds - self._active.commands_this_round
            out = {
                "duel_event": True,
                "round_result": "pending",
                "message": (
                    f"[DUEL] Round {self._active.current_round + 1}/{self._active.total_rounds} active — "
                    f"{hints_remaining} commands remaining\n"
                    f"Challenge: {ch['prompt'] if ch else '?'}\n"
                    f"Hint: {ch['hint'] if ch else '?'}"
                ),
            }

        if self._active.status in (DuelStatus.WON, DuelStatus.LOST):
            outcome = self._active.get_outcome()
            if outcome["xp_earned"]:
                gs.add_xp(outcome["xp_earned"], "security")
            gs.trigger_beat(f"duel_{self._active.agent_id}_{self._active.status.value}")
            out["duel_complete"] = True
            out["outcome"] = outcome
            out["final_message"] = outcome["message"]
            self._active = None

        elif self._active and self._active.status == DuelStatus.ACTIVE:
            next_ch = self._active.current_challenge
            if next_ch and out.get("round_result") in ("won", "failed"):
                out["next_challenge"] = f"[DUEL] Next: {next_ch['prompt']}"

        return out

    def surrender(self, gs: GameState) -> dict:
        """Player forfeits the active duel immediately."""
        if not self._active or self._active.status != DuelStatus.ACTIVE:
            return {"ok": False, "error": "No active duel to surrender."}

        agent_id = self._active.agent_id
        # Force remaining rounds as losses
        while self._active.current_round < self._active.total_rounds:
            self._active.advance_round(won=False)

        # Manually set LOST (advance_round may have resolved WON if rounds_won > rounds_lost)
        self._active.status = DuelStatus.LOST
        outcome = self._active.get_outcome()
        gs.trigger_beat(f"duel_{agent_id}_surrendered")
        self._active = None

        surrender_msgs = {
            "ada": "[ADA-7]: ...Understood. Regroup. Try again when you're ready.",
            "cypher": "[CYPHER]: Surrendering already? Come back when you've levelled up.",
            "nova": "[NOVA]: Smart choice. Live to fight another day — for now.",
            "watcher": "[WATCHER]: The simulation notes your retreat. It will adapt.",
        }
        return {
            "ok": True,
            "surrendered": True,
            "message": surrender_msgs.get(agent_id, f"[{agent_id.upper()}]: Duel forfeited."),
            "outcome": outcome,
        }

    @property
    def active_duel(self) -> Optional[DuelSession]:
        return self._active

    def get_status(self) -> dict:
        if not self._active:
            return {"active": False}
        return {
            "active": True,
            "agent": self._active.agent_id,
            "round": self._active.current_round + 1,
            "total_rounds": self._active.total_rounds,
            "rounds_won": self._active.rounds_won,
            "rounds_lost": self._active.rounds_lost,
            "commands_this_round": self._active.commands_this_round,
            "time_limit": self._active.time_limit_cmds,
        }

    def to_dict(self) -> dict:
        return {"active": self._active.to_dict() if self._active else None}

    @classmethod
    def from_dict(cls, d: dict) -> "DuelEngine":
        engine = cls()
        return engine
