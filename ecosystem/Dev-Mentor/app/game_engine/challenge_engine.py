"""
app/game_engine/challenge_engine.py — RL2 Daily/Weekly Challenge Modes
=======================================================================
Deterministic daily and weekly challenges generated from date seeds.
Each challenge type has specific win conditions tracked against live
game state. Completing a challenge awards bonus XP, credits, and
an achievement flag.

State stored in gs.flags["active_challenge"] and gs.flags["challenge_log"].
Wire format compatible: all public methods return List[dict] with t/s keys.
"""
from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Challenge type definitions
# ---------------------------------------------------------------------------

CHALLENGE_TYPES: Dict[str, Dict[str, Any]] = {
    "speedrun": {
        "name": "SPEEDRUN",
        "tagline": "Complete X objectives before the timer expires.",
        "description": (
            "Execute 20 distinct commands within 10 minutes of starting. "
            "No repeats counted. Speed is the weapon."
        ),
        "icon": "⚡",
        "win_condition": {"type": "command_variety", "target": 20},
        "time_limit_s": 600,
        "xp_reward": 200,
        "credit_reward": 150,
        "achievement": "SPEEDRUNNER",
    },
    "stealth": {
        "name": "STEALTH",
        "tagline": "Gain maximum XP with minimum trace level.",
        "description": (
            "Earn 300 XP while keeping your trace level below 30. "
            "Every noisy command costs you the run."
        ),
        "icon": "👁",
        "win_condition": {"type": "xp_under_trace", "xp_target": 300, "max_trace": 30},
        "time_limit_s": 0,
        "xp_reward": 250,
        "credit_reward": 100,
        "achievement": "GHOST_RUNNER",
    },
    "economist": {
        "name": "ECONOMIST",
        "tagline": "Reach 1000 credits before the session ends.",
        "description": (
            "Accumulate 1000 credits through looting, trading, and economy "
            "commands. No exploits — earn it."
        ),
        "icon": "◈",
        "win_condition": {"type": "credits", "target": 1000},
        "time_limit_s": 0,
        "xp_reward": 180,
        "credit_reward": 200,
        "achievement": "MARKET_MAKER",
    },
    "scholar": {
        "name": "SCHOLAR",
        "tagline": "Max out 3 skills within 50 commands.",
        "description": (
            "Reach skill level 10 in any 3 skills within your next 50 commands. "
            "Focus beats quantity."
        ),
        "icon": "◎",
        "win_condition": {"type": "skills_maxed", "count": 3, "level": 10, "cmd_budget": 50},
        "time_limit_s": 0,
        "xp_reward": 300,
        "credit_reward": 75,
        "achievement": "POLYMATH",
    },
    "ghost": {
        "name": "GHOST",
        "tagline": "Complete the run without dying or being detected.",
        "description": (
            "Reach level 5 without triggering a death event or crossing "
            "trace level 50. Leave no footprint."
        ),
        "icon": "◌",
        "win_condition": {"type": "survival", "target_level": 5, "max_trace": 50},
        "time_limit_s": 0,
        "xp_reward": 350,
        "credit_reward": 120,
        "achievement": "PHANTOM_PROTOCOL",
    },
    # --- Web Exploitation ---
    "web_novice": {
        "name": "WEB_NOVICE",
        "tagline": "Basic web reconnaissance and testing.",
        "description": "Execute 5 distinct commands related to network and web tools.",
        "icon": "🌐",
        "win_condition": {"type": "command_variety", "target": 5},
        "time_limit_s": 300,
        "xp_reward": 50,
        "credit_reward": 25,
        "achievement": "WEB_SCRAPER",
    },
    "web_adept": {
        "name": "WEB_ADEPT",
        "tagline": "Advanced web structure analysis.",
        "description": "Execute 15 distinct commands to map out remote services.",
        "icon": "🕸",
        "win_condition": {"type": "command_variety", "target": 15},
        "time_limit_s": 600,
        "xp_reward": 150,
        "credit_reward": 100,
        "achievement": "SITE_MAPPER",
    },
    "sql_injector": {
        "name": "SQL_INJECTOR",
        "tagline": "Bypass authentication via injection.",
        "description": "Execute 30 distinct commands without repeat. Database focus.",
        "icon": "💉",
        "win_condition": {"type": "command_variety", "target": 30},
        "time_limit_s": 1200,
        "xp_reward": 300,
        "credit_reward": 250,
        "achievement": "DROP_TABLES",
    },
    "xss_master": {
        "name": "XSS_MASTER",
        "tagline": "Cross-site scripting at scale.",
        "description": "Execute 50 distinct commands. Total domain dominance.",
        "icon": "☣",
        "win_condition": {"type": "command_variety", "target": 50},
        "time_limit_s": 1800,
        "xp_reward": 500,
        "credit_reward": 500,
        "achievement": "SCRIPT_GOD",
    },
    # --- Cryptography ---
    "crypto_basic": {
        "name": "CRYPTO_BASIC",
        "tagline": "Understand the basics of encryption.",
        "description": "Reach level 3 in Cryptography skill within 20 commands.",
        "icon": "🔐",
        "win_condition": {"type": "skills_maxed", "count": 1, "level": 3, "cmd_budget": 20},
        "time_limit_s": 0,
        "xp_reward": 50,
        "credit_reward": 50,
        "achievement": "DECODER_RING",
    },
    "cipher_breaker": {
        "name": "CIPHER_BREAKER",
        "tagline": "Crack intermediate rotational and substitution ciphers.",
        "description": "Reach level 7 in Cryptography skill within 40 commands.",
        "icon": "🔓",
        "win_condition": {"type": "skills_maxed", "count": 1, "level": 7, "cmd_budget": 40},
        "time_limit_s": 0,
        "xp_reward": 150,
        "credit_reward": 150,
        "achievement": "ENIGMA_LOST",
    },
    "entropy_hunter": {
        "name": "ENTROPY_HUNTER",
        "tagline": "Analyze high-entropy data for patterns.",
        "description": "Reach level 10 in Cryptography and Scripting within 60 commands.",
        "icon": "🎲",
        "win_condition": {"type": "skills_maxed", "count": 2, "level": 10, "cmd_budget": 60},
        "time_limit_s": 0,
        "xp_reward": 300,
        "credit_reward": 300,
        "achievement": "RANDOM_WALKER",
    },
    "quantum_safe": {
        "name": "QUANTUM_SAFE",
        "tagline": "Implement post-quantum cryptographic standards.",
        "description": "Reach level 15 in 3 technical skills within 100 commands.",
        "icon": "⚛",
        "win_condition": {"type": "skills_maxed", "count": 3, "level": 15, "cmd_budget": 100},
        "time_limit_s": 0,
        "xp_reward": 500,
        "credit_reward": 600,
        "achievement": "SHOR_PROOF",
    },
    # --- Forensics ---
    "forensics_init": {
        "name": "FORENSICS_INIT",
        "tagline": "Initial file system analysis.",
        "description": "Read 10 distinct files to gather initial intel.",
        "icon": "🔍",
        "win_condition": {"type": "file_reading", "target": 10},
        "time_limit_s": 0,
        "xp_reward": 50,
        "credit_reward": 40,
        "achievement": "LEAVE_NO_STONE",
    },
    "data_archeologist": {
        "name": "DATA_ARCHEOLOGIST",
        "tagline": "Uncover deleted or hidden artifacts.",
        "description": "Read 30 distinct files across the system.",
        "icon": "🏺",
        "win_condition": {"type": "file_reading", "target": 30},
        "time_limit_s": 0,
        "xp_reward": 150,
        "credit_reward": 120,
        "achievement": "DIGITAL_HISTORY",
    },
    "trace_analyst": {
        "name": "TRACE_ANALYST",
        "tagline": "Follow the breadcrumbs of a ghost process.",
        "description": "Read 100 distinct files to reconstruct events.",
        "icon": "👣",
        "win_condition": {"type": "file_reading", "target": 100},
        "time_limit_s": 0,
        "xp_reward": 300,
        "credit_reward": 250,
        "achievement": "TIMELINE_CONSTRUCTOR",
    },
    "memory_dump": {
        "name": "MEMORY_DUMP",
        "tagline": "Full volatile memory reconstruction.",
        "description": "Read 250 distinct files. Leave nothing unexamined.",
        "icon": "🧠",
        "win_condition": {"type": "file_reading", "target": 250},
        "time_limit_s": 0,
        "xp_reward": 500,
        "credit_reward": 450,
        "achievement": "VOLATILITY_MASTER",
    },
    # --- OSINT ---
    "osint_scout": {
        "name": "OSINT_SCOUT",
        "tagline": "Gathering publicly available information.",
        "description": "Accumulate 100 credits via public bounties.",
        "icon": "📡",
        "win_condition": {"type": "credits", "target": 100},
        "time_limit_s": 0,
        "xp_reward": 50,
        "credit_reward": 50,
        "achievement": "PUBLIC_EYE",
    },
    "public_record": {
        "name": "PUBLIC_RECORD",
        "tagline": "Mining government and corporate databases.",
        "description": "Accumulate 500 credits through information trading.",
        "icon": "🏛",
        "win_condition": {"type": "credits", "target": 500},
        "time_limit_s": 0,
        "xp_reward": 150,
        "credit_reward": 150,
        "achievement": "ARCHIVIST",
    },
    "social_grapher": {
        "name": "SOCIAL_GRAPHER",
        "tagline": "Mapping the connections between agents.",
        "description": "Accumulate 2000 credits. Knowledge is profit.",
        "icon": "🕸",
        "win_condition": {"type": "credits", "target": 2000},
        "time_limit_s": 0,
        "xp_reward": 300,
        "credit_reward": 300,
        "achievement": "NODE_MAPPER",
    },
    "deep_search": {
        "name": "DEEP_SEARCH",
        "tagline": "Indexing the unindexed web.",
        "description": "Accumulate 5000 credits. Own the market.",
        "icon": "🕳",
        "win_condition": {"type": "credits", "target": 5000},
        "time_limit_s": 0,
        "xp_reward": 500,
        "credit_reward": 500,
        "achievement": "LEVIATHAN",
    },
    # --- Hardware ---
    "hardware_tinkerer": {
        "name": "HARDWARE_TINKERER",
        "tagline": "Understanding the physical substrate.",
        "description": "Execute 10 distinct hardware-related commands.",
        "icon": "🔌",
        "win_condition": {"type": "command_variety", "target": 10},
        "time_limit_s": 0,
        "xp_reward": 50,
        "credit_reward": 50,
        "achievement": "SOLDER_MONKEY",
    },
    "kernel_panic": {
        "name": "KERNEL_PANIC",
        "tagline": "Exploiting ring-0 vulnerabilities.",
        "description": "Execute 25 distinct commands targeting the kernel.",
        "icon": "💥",
        "win_condition": {"type": "command_variety", "target": 25},
        "time_limit_s": 0,
        "xp_reward": 150,
        "credit_reward": 150,
        "achievement": "RING_BREAKER",
    },
    "buffer_overflow": {
        "name": "BUFFER_OVERFLOW",
        "tagline": "Smashing the stack for fun and profit.",
        "description": "Execute 45 distinct commands without crashing.",
        "icon": "🌊",
        "win_condition": {"type": "command_variety", "target": 45},
        "time_limit_s": 0,
        "xp_reward": 300,
        "credit_reward": 300,
        "achievement": "STACK_SMASHER",
    },
    "silicon_soul": {
        "name": "SILICON_SOUL",
        "tagline": "Becoming one with the machine code.",
        "description": "Reach level 15 while keeping trace below 20.",
        "icon": "💾",
        "win_condition": {"type": "survival", "target_level": 15, "max_trace": 20},
        "time_limit_s": 0,
        "xp_reward": 500,
        "credit_reward": 500,
        "achievement": "PURE_MACHINE",
    },
    # --- Network ---
    "net_sniffer": {
        "name": "NET_SNIFFER",
        "tagline": "Listening to the wire.",
        "description": "Gain 100 XP with trace level below 20.",
        "icon": "👂",
        "win_condition": {"type": "xp_under_trace", "xp_target": 100, "max_trace": 20},
        "time_limit_s": 0,
        "xp_reward": 50,
        "credit_reward": 50,
        "achievement": "WIRE_TAPPER",
    },
    "port_scanner": {
        "name": "PORT_SCANNER",
        "tagline": "Knocking on all the doors.",
        "description": "Gain 500 XP with trace level below 40.",
        "icon": "🚪",
        "win_condition": {"type": "xp_under_trace", "xp_target": 500, "max_trace": 40},
        "time_limit_s": 0,
        "xp_reward": 150,
        "credit_reward": 150,
        "achievement": "SCAN_MASTER",
    },
    "packet_master": {
        "name": "PACKET_MASTER",
        "tagline": "Forging custom TCP/IP headers.",
        "description": "Gain 1500 XP with trace level below 60.",
        "icon": "📦",
        "win_condition": {"type": "xp_under_trace", "xp_target": 1500, "max_trace": 60},
        "time_limit_s": 0,
        "xp_reward": 300,
        "credit_reward": 300,
        "achievement": "RAW_SOCKETS",
    },
    "grid_ghost": {
        "name": "GRID_GHOST",
        "tagline": "Moving unseen through the global network.",
        "description": "Gain 5000 XP while keeping trace under 10.",
        "icon": "👻",
        "win_condition": {"type": "xp_under_trace", "xp_target": 5000, "max_trace": 10},
        "time_limit_s": 0,
        "xp_reward": 500,
        "credit_reward": 500,
        "achievement": "NETWORK_PHANTOM",
    },
    # --- Social Engineering ---
    "phish_init": {
        "name": "PHISH_INIT",
        "tagline": "The art of human deception.",
        "description": "Reach level 5 in Social Engineering within 30 commands.",
        "icon": "🎣",
        "win_condition": {"type": "skills_maxed", "count": 1, "level": 5, "cmd_budget": 30},
        "time_limit_s": 0,
        "xp_reward": 50,
        "credit_reward": 50,
        "achievement": "LITTLE_BIRDY",
    },
    "trust_architect": {
        "name": "TRUST_ARCHITECT",
        "tagline": "Building rapport for exploitation.",
        "description": "Reach level 8 in 2 social skills within 60 commands.",
        "icon": "🤝",
        "win_condition": {"type": "skills_maxed", "count": 2, "level": 8, "cmd_budget": 60},
        "time_limit_s": 0,
        "xp_reward": 150,
        "credit_reward": 150,
        "achievement": "BEST_FRIEND",
    },
    "mind_hacker": {
        "name": "MIND_HACKER",
        "tagline": "Rewriting human protocols.",
        "description": "Reach level 12 in 3 social skills within 100 commands.",
        "icon": "🧠",
        "win_condition": {"type": "skills_maxed", "count": 3, "level": 12, "cmd_budget": 100},
        "time_limit_s": 0,
        "xp_reward": 300,
        "credit_reward": 300,
        "achievement": "PUPPET_MASTER",
    },
    "cult_leader": {
        "name": "CULT_LEADER",
        "tagline": "Total psychological dominance.",
        "description": "Reach level 15 in 5 skills within 200 commands.",
        "icon": "👑",
        "win_condition": {"type": "skills_maxed", "count": 5, "level": 15, "cmd_budget": 200},
        "time_limit_s": 0,
        "xp_reward": 500,
        "credit_reward": 500,
        "achievement": "MESMER",
    },
}

_CHALLENGE_IDS = list(CHALLENGE_TYPES.keys())


def _line(text: str, t: str = "info") -> dict:
    return {"t": t, "s": text}


def _ok(text: str) -> List[dict]:
    return [_line(text, "success")]


def _err(text: str) -> List[dict]:
    return [_line(text, "error")]


def _dim(text: str) -> List[dict]:
    return [_line(text, "dim")]


def _sys(text: str) -> List[dict]:
    return [_line(text, "system")]


def _lore(text: str) -> dict:
    return _line(text, "lore")


def _warn(text: str) -> dict:
    return _line(text, "warn")


# ---------------------------------------------------------------------------
# ChallengeEngine
# ---------------------------------------------------------------------------

class ChallengeEngine:
    """Daily/weekly challenge generation and tracking."""

    def _seed_from_str(self, s: str) -> int:
        """Deterministic integer seed from a string (date/week key)."""
        h = hashlib.sha256(s.encode()).hexdigest()
        return int(h[:8], 16)

    def _pick_challenge(self, seed: int) -> str:
        import random as _r
        rng = _r.Random(seed)
        return rng.choice(_CHALLENGE_IDS)

    def get_daily(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Return deterministic daily challenge for a date string (YYYY-MM-DD)."""
        if date_str is None:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seed = self._seed_from_str(f"daily:{date_str}")
        cid = self._pick_challenge(seed)
        c = dict(CHALLENGE_TYPES[cid])
        c["id"] = cid
        c["period"] = "daily"
        c["period_key"] = date_str
        c["seed"] = seed
        return c

    def get_weekly(self, week_str: Optional[str] = None) -> Dict[str, Any]:
        """Return deterministic weekly challenge. week_str = 'YYYY-WNN'."""
        if week_str is None:
            now = datetime.now(timezone.utc)
            week_str = f"{now.year}-W{now.isocalendar()[1]:02d}"
        seed = self._seed_from_str(f"weekly:{week_str}")
        cid = self._pick_challenge(seed)
        c = dict(CHALLENGE_TYPES[cid])
        c["id"] = cid
        c["period"] = "weekly"
        c["period_key"] = week_str
        c["seed"] = seed
        return c

    def start_challenge(self, challenge_id: str, gs: Any) -> List[dict]:
        """Initialize challenge state in gs.flags."""
        if challenge_id not in CHALLENGE_TYPES:
            return _err(f"  challenge: unknown id '{challenge_id}'") + _dim(
                f"  Available: {', '.join(_CHALLENGE_IDS)}"
            )

        active = gs.flags.get("active_challenge")
        if active:
            return _err(
                f"  challenge: already running '{active['id']}'. "
                "Use 'challenge progress' or abandon it first."
            )

        c = CHALLENGE_TYPES[challenge_id]
        state = {
            "id": challenge_id,
            "started_at": time.time(),
            "start_xp": gs.xp,
            "start_credits": getattr(gs, "credits", 0),
            "start_cmd_count": len(getattr(gs, "command_count", [])),
            "start_level": gs.level,
            "start_skills": dict(gs.skills) if hasattr(gs, "skills") else {},
            "failed": False,
        }
        gs.flags["active_challenge"] = state

        out: List[dict] = []
        out += _sys(f"  {c['icon']} CHALLENGE STARTED: {c['name']}")
        out.append(_line(f"  {c['description']}", "lore"))
        out.append(_line(f"  Reward: +{c['xp_reward']} XP  +{c['credit_reward']} credits  [{c['achievement']}]", "info"))
        if c["time_limit_s"]:
            minutes = c["time_limit_s"] // 60
            out += _dim(f"  Time limit: {minutes} minutes")
        out += _dim("  Type 'challenge progress' to check your status.")
        return out

    def check_progress(self, gs: Any) -> List[dict]:
        """Evaluate current state against active challenge objectives."""
        active = gs.flags.get("active_challenge")
        if not active:
            return _dim("  No active challenge. Use 'challenge list' to see options.")

        cid = active["id"]
        c = CHALLENGE_TYPES[cid]
        wc = c["win_condition"]
        out: List[dict] = []

        out += _sys(f"  {c['icon']} CHALLENGE: {c['name']}")

        # Time check
        elapsed = time.time() - active["started_at"]
        if c["time_limit_s"] and elapsed > c["time_limit_s"]:
            out.append(_line("  STATUS: FAILED — time expired", "error"))
            gs.flags.pop("active_challenge", None)
            return out

        if c["time_limit_s"]:
            remaining = c["time_limit_s"] - elapsed
            out += _dim(f"  Time remaining: {int(remaining)}s")

        wc_type = wc["type"]
        completed = False

        if wc_type == "command_variety":
            cmd_history = getattr(gs, "command_history", [])
            unique_cmds = len(set(cmd_history[-200:]))
            target = wc["target"]
            bar = _progress_bar(unique_cmds, target)
            out.append(_line(f"  Commands: {bar} {unique_cmds}/{target}", "info"))
            completed = unique_cmds >= target

        elif wc_type == "xp_under_trace":
            xp_gained = gs.xp - active["start_xp"]
            trace = gs.flags.get("trace_level", 0)
            max_trace = wc["max_trace"]
            xp_target = wc["xp_target"]
            bar = _progress_bar(xp_gained, xp_target)
            out.append(_line(f"  XP gained: {bar} {xp_gained}/{xp_target}", "info"))
            if trace >= max_trace:
                out.append(_line(f"  TRACE EXCEEDED ({trace}/{max_trace}) — challenge failed!", "error"))
                gs.flags.pop("active_challenge", None)
                return out
            out += _dim(f"  Trace: {trace}/{max_trace} (safe)")
            completed = xp_gained >= xp_target

        elif wc_type == "credits":
            credits = getattr(gs, "credits", 0)
            target = wc["target"]
            bar = _progress_bar(credits, target)
            out.append(_line(f"  Credits: {bar} {credits}/{target}", "info"))
            completed = credits >= target

        elif wc_type == "skills_maxed":
            skills = gs.skills if hasattr(gs, "skills") else {}
            maxed = [sk for sk, val in skills.items() if val >= wc["level"]]
            needed = wc["count"]
            start_cmds = active.get("start_cmd_count", 0)
            cmd_budget = wc["cmd_budget"]
            cmds_used = len(getattr(gs, "command_history", [])) - start_cmds
            bar = _progress_bar(len(maxed), needed)
            out.append(_line(f"  Skills at {wc['level']}+: {bar} {len(maxed)}/{needed}", "info"))
            out += _dim(f"  Commands used: {cmds_used}/{cmd_budget}")
            if cmds_used >= cmd_budget and len(maxed) < needed:
                out.append(_line("  Command budget exhausted — challenge failed!", "error"))
                gs.flags.pop("active_challenge", None)
                return out
            completed = len(maxed) >= needed

        elif wc_type == "survival":
            target_level = wc["target_level"]
            trace = gs.flags.get("trace_level", 0)
            max_trace = wc["max_trace"]
            died = gs.flags.get("challenge_death", False)
            bar = _progress_bar(gs.level, target_level)
            out.append(_line(f"  Level: {bar} {gs.level}/{target_level}", "info"))
            if died or trace >= max_trace:
                reason = "death event" if died else f"trace exceeded ({trace})"
                out.append(_line(f"  FAILED: {reason}", "error"))
                gs.flags.pop("active_challenge", None)
                return out
            out += _dim(f"  Trace: {trace}/{max_trace}  |  Deaths: {'YES' if died else 'none'}")
            completed = gs.level >= target_level

        elif wc_type == "file_reading":
            files_read = getattr(gs, "files_read", 0)
            target = wc["target"]
            bar = _progress_bar(files_read, target)
            out.append(_line(f"  Files Read: {bar} {files_read}/{target}", "info"))
            completed = files_read >= target

        if completed:
            out += self.complete_challenge(gs)
        else:
            out += _dim(f"  Keep going. Reward: +{c['xp_reward']} XP  +{c['credit_reward']} credits")

        return out

    def complete_challenge(self, gs: Any) -> List[dict]:
        """Award bonus XP/credits/achievement, clear active challenge."""
        active = gs.flags.get("active_challenge")
        if not active:
            return _dim("  No active challenge to complete.")

        cid = active["id"]
        c = CHALLENGE_TYPES[cid]

        gs.add_xp(c["xp_reward"], "networking")
        gs.credits = getattr(gs, "credits", 0) + c["credit_reward"]

        ach_key = f"achievement_{c['achievement'].lower()}"
        if not gs.flags.get(ach_key):
            gs.flags[ach_key] = True
            achievement_line = _line(f"  ACHIEVEMENT UNLOCKED: [{c['achievement']}]", "xp")
        else:
            achievement_line = _line(f"  Achievement already earned: [{c['achievement']}]", "dim")

        log = gs.flags.get("challenge_log", [])
        log.append({
            "id": cid,
            "completed_at": time.time(),
            "xp": c["xp_reward"],
            "credits": c["credit_reward"],
        })
        gs.flags["challenge_log"] = log[-50:]
        gs.flags.pop("active_challenge", None)

        out: List[dict] = []
        out += _sys(f"  {c['icon']} CHALLENGE COMPLETE: {c['name']}")
        out.append(_line(f"  +{c['xp_reward']} XP  +{c['credit_reward']} credits", "success"))
        out.append(achievement_line)
        out += [_line("  The grid acknowledges your excellence.", "lore")]
        return out

    def render_challenges(self, gs: Any) -> List[dict]:
        """List all available challenges with status."""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        week_str = f"{now.year}-W{now.isocalendar()[1]:02d}"

        daily = self.get_daily(date_str)
        weekly = self.get_weekly(week_str)
        active = gs.flags.get("active_challenge")
        log = gs.flags.get("challenge_log", [])
        completed_ids = {e["id"] for e in log}

        out: List[dict] = []
        out += _sys("  ╔══ CHALLENGE BOARD ══╗")
        out.append(_line(f"  Date: {date_str}  |  Week: {week_str}", "dim"))
        out.append(_line("  ─────────────────────────────────────────────", "dim"))

        # Daily
        d_status = "ACTIVE" if active and active["id"] == daily["id"] else (
            "DONE" if daily["id"] in completed_ids else "AVAILABLE"
        )
        out.append(_line(f"  ⚡ DAILY  [{daily['icon']} {daily['name']}]  {d_status}", "info"))
        out += _dim(f"    {daily['tagline']}")
        out += _dim(f"    Reward: +{daily['xp_reward']} XP  +{daily['credit_reward']} credits")
        out += _dim(f"    challenge start {daily['id']}")

        out.append(_line("  ─────────────────────────────────────────────", "dim"))

        # Weekly
        w_status = "ACTIVE" if active and active["id"] == weekly["id"] else (
            "DONE" if weekly["id"] in completed_ids else "AVAILABLE"
        )
        out.append(_line(f"  ◎ WEEKLY [{weekly['icon']} {weekly['name']}]  {w_status}", "warn"))
        out += _dim(f"    {weekly['tagline']}")
        out += _dim(f"    Reward: +{weekly['xp_reward']} XP  +{weekly['credit_reward']} credits")
        out += _dim(f"    challenge start {weekly['id']}")

        out.append(_line("  ─────────────────────────────────────────────", "dim"))

        # All types
        out.append(_line("  All challenge types:", "dim"))
        for cid, c in CHALLENGE_TYPES.items():
            status = "DONE" if cid in completed_ids else "available"
            out.append(_line(f"  {c['icon']} {cid:<18} {c['name']:<14} [{status}]", "dim"))

        if active:
            out.append(_line(f"\n  Currently running: {active['id']} — 'challenge progress'", "success"))

        return out


def _progress_bar(current: int, total: int, width: int = 12) -> str:
    if total <= 0:
        return "[" + "=" * width + "]"
    filled = min(width, int(width * current / total))
    empty = width - filled
    return "[" + "=" * filled + "-" * empty + "]"


# ---------------------------------------------------------------------------
# Factory singleton
# ---------------------------------------------------------------------------

_engine_instance: "ChallengeEngine | None" = None


def get_challenge_engine() -> "ChallengeEngine":
    """Return shared ChallengeEngine singleton (import-safe)."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ChallengeEngine()
    return _engine_instance
