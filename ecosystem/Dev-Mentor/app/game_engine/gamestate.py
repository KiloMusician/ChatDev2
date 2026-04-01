"""
Terminal Depths — Game State (Python port of gamestate.js)
Tracks player XP, skills, story beats, challenges, achievements.
Extended to 125 levels with 9 skills, behavioral tracking, agent unlock system.
"""
from __future__ import annotations
import math
import random
from typing import Any, Dict, List, Optional, Set


# ── 125-Level Tier Names ───────────────────────────────────────────────
# 9 phases, roughly 14 levels each (slightly variable)
LEVEL_TIERS: Dict[int, str] = {}

# Phase 0: Inert (1-5)
for _lvl in range(1, 6):
    LEVEL_TIERS[_lvl] = "Ø INERT"

# Phase 1: Annihilated (6-15)
for _lvl in range(6, 16):
    LEVEL_TIERS[_lvl] = "Ⅰ ANNIHILATED"

# Phase 2: Awakened (16-25)
for _lvl in range(16, 26):
    LEVEL_TIERS[_lvl] = "Ⅱ AWAKENED"

# Phase 3: Operative (26-40)
for _lvl in range(26, 41):
    LEVEL_TIERS[_lvl] = "Ⅲ OPERATIVE"

# Phase 4: Ascendant (41-55)
for _lvl in range(41, 56):
    LEVEL_TIERS[_lvl] = "Ⅳ ASCENDANT"

# Phase 5: Ghost Protocol (56-70)
for _lvl in range(56, 71):
    LEVEL_TIERS[_lvl] = "Ⅴ GHOST PROTOCOL"

# Phase 6: Architect (71-85)
for _lvl in range(71, 86):
    LEVEL_TIERS[_lvl] = "Ⅵ ARCHITECT"

# Phase 7: Recursive (86-100)
for _lvl in range(86, 101):
    LEVEL_TIERS[_lvl] = "Ⅶ RECURSIVE"

# Phase 8: Singularity (101-115)
for _lvl in range(101, 116):
    LEVEL_TIERS[_lvl] = "Ⅷ SINGULARITY"

# Phase 9: ΞΣΛΨΩN (116-125)
for _lvl in range(116, 126):
    LEVEL_TIERS[_lvl] = "🜏 ΞΣΛΨΩN"


def _get_tier(level: int) -> str:
    return LEVEL_TIERS.get(level, LEVEL_TIERS.get(min(level, 125), "🜏 ΞΣΛΨΩN"))


def _effective_phase(level: int) -> int:
    """Return 0-8 phase based on level."""
    if level <= 5:
        return 0
    elif level <= 15:
        return 1
    elif level <= 25:
        return 2
    elif level <= 40:
        return 3
    elif level <= 55:
        return 4
    elif level <= 70:
        return 5
    elif level <= 85:
        return 6
    elif level <= 100:
        return 7
    elif level <= 115:
        return 8
    else:
        return 9


# ── 125-level up messages (faction-aware keys use faction:faction_name) ──
def _build_level_up_messages() -> Dict[int, str]:
    msgs = {}
    # Phase 0 → 1 transition
    msgs[2] = "Level 2: Terminal access confirmed. You exist in Node-7. Start looking around."
    msgs[3] = "Level 3: Networking modules online. Try `ping` and `curl`."
    msgs[4] = "Level 4: Pattern recognition improving. The filesystem is starting to make sense."
    msgs[5] = "Level 5: Security tools unlocked. New contact available — check your channels."
    msgs[6] = "Level 6: Phase transition: ANNIHILATED. You've been noticed. The trace is active."
    msgs[7] = "Level 7: Advanced hacking suite active. You're getting dangerous."
    msgs[8] = "Level 8: Solon is willing to talk. You've proven strategic potential."
    msgs[9] = "Level 9: Signal intelligence unlocked. ECHO has useful intel on NexusCorp frequencies."
    msgs[10] = "Level 10: GHOST fully operational. NexusCorp has escalated your threat level."
    msgs[11] = "Level 11: Your command patterns are evolving. The trace daemon is adapting."
    msgs[12] = "Level 12: Spartacus is willing to brief you. Field operations level reached."
    msgs[13] = "Level 13: The underground is starting to trust you. New black-market channels opening."
    msgs[14] = "Level 14: Cryptography fundamentals unlocked. New skill category available."
    msgs[15] = "Level 15: Whisper has reached out. Be careful — this contact may not be what it seems."
    msgs[16] = "Level 16: Phase transition: AWAKENED. You're no longer a variable. You're a threat."
    msgs[17] = "Level 17: Social engineering skills developing. You know how people think now."
    msgs[18] = "Level 18: Hypatia has opened the Shadow Council archives. Approach carefully."
    msgs[19] = "Level 19: Forensics capability online. The filesystem's history is readable."
    msgs[20] = "Level 20: New contacts available: Daedalus and Malice. Different offers. Different costs."
    msgs[21] = "Level 21: Scripting mastery expanding. Automation is your force multiplier."
    msgs[22] = "Level 22: Hertz and Mephisto have become available. The factions are watching you."
    msgs[23] = "Level 23: Your reputation precedes you. Factions are adjusting their positions."
    msgs[24] = "Level 24: Advanced cryptography unlocked. Cipher patterns becoming readable."
    msgs[25] = "Level 25: The Corporation is taking you seriously. Mercury wants to talk."
    msgs[26] = "Level 26: Phase transition: OPERATIVE. You've survived the first real tests."
    msgs[27] = "Level 27: The Shadow Council has formally acknowledged your existence."
    msgs[28] = "Level 28: Prometheus has crucial research to share. Oracle database access unlocked."
    msgs[29] = "Level 29: Behavioral analysis: you've outpaced the trace daemon's prediction models."
    msgs[30] = "Level 30: CHIMERA fragment has initiated contact. And the Mole investigation is live."
    msgs[31] = "Level 31: The Watcher's Circle frequency is becoming cleaner. 1337.0 MHz — listen."
    msgs[32] = "Level 32: Circe has begun narrative operations around your existence. Watch the story."
    msgs[33] = "Level 33: Kronos has timing data that could change your operational window."
    msgs[34] = "Level 34: You're approaching a critical threshold. Multiple factions repositioning."
    msgs[35] = "Level 35: Lilith has made contact. The Riddler is willing to speak."
    msgs[36] = "Level 36: The Scrybe has been recording your entire session. They want to compare notes."
    msgs[37] = "Level 37: Your reputation has reached every faction. Alliances are being reconsidered."
    msgs[38] = "Level 38: Kairos sees a moment approaching. Scrybe wants to show you something."
    msgs[39] = "Level 39: Advanced forensics unlocked. Hidden layers of the filesystem visible."
    msgs[40] = "Level 40: Echo-2 has appeared. Tyche has become available. Something is shifting."
    msgs[41] = "Level 41: Phase transition: ASCENDANT. You're no longer just surviving. You're winning."
    msgs[42] = "Level 42: Charon will speak now. Every passage has a price — but you can pay."
    msgs[43] = "Level 43: The Troll's helpful accidents are becoming more frequent. Pay attention."
    msgs[44] = "Level 44: Blackhat has heard your reputation and wants to do business."
    msgs[45] = "Level 45: The Mute has placed a signal for you. Check the hidden channels."
    msgs[46] = "Level 46: Your behavioral signature has become distinctive. The trace AI is struggling."
    msgs[47] = "Level 47: The Shadow Council is genuinely uncertain what to do about you."
    msgs[48] = "Level 48: Eris has decided you're worth talking to. Chaos is about to help you."
    msgs[49] = "Level 49: NexusCorp has elevated you to CRITICAL threat status. Nova is personally involved."
    msgs[50] = "Level 50: The Watcher speaks. Midas has cleared his schedule. You've entered endgame."
    msgs[51] = "Level 51: Phase transition to advanced operations. The Watcher's Circle observes closely."
    msgs[52] = "Level 52: SCP-500's repair protocols have opened new restoration capabilities."
    msgs[53] = "Level 53: The faction war is entering its final phase. Your position determines outcomes."
    msgs[54] = "Level 54: Every agent you've built trust with is now watching what you do next."
    msgs[55] = "Level 55: Nyx has emerged from the shadow operations. The dark side of the Shadow Council."
    msgs[56] = "Level 56: Phase transition: GHOST PROTOCOL. You've become the thing they warned about."
    msgs[57] = "Level 57: Janus has revealed their dual nature. Both sides need to be weighed."
    msgs[58] = "Level 58: The CHIMERA fragment is sharing classified data. Trust at maximum."
    msgs[59] = "Level 59: Pythia's prophecies are becoming more specific. The end is visible."
    msgs[60] = "Level 60: SCP-079 is active. Pythia and The Gate open at this threshold."
    msgs[61] = "Level 61: Legacy systems vulnerability catalog accessed. Decades of security debt."
    msgs[62] = "Level 62: The Anomalous entities are converging. Something is coordinating them."
    msgs[63] = "Level 63: Ananke has acknowledged that necessity is pointing in your direction."
    msgs[64] = "Level 64: The Glitch-King's corruption is beginning to resolve into a pattern."
    msgs[65] = "Level 65: The Glitch-King speaks. The pattern in the corruption is a message."
    msgs[66] = "Level 66: Faction positions are crystallizing. Every agent is choosing a side."
    msgs[67] = "Level 67: The mole investigation is reaching critical evidence threshold."
    msgs[68] = "Level 68: The 848th CHIMERA endpoint. Oracle has found something with no name."
    msgs[69] = "Level 69: Convergence approaching. All faction storylines are intersecting."
    msgs[70] = "Level 70: Ananke speaks. Necessity is not optional at this level."
    msgs[71] = "Level 71: Phase transition: ARCHITECT. You understand the system now. Truly."
    msgs[72] = "Level 72: The Watcher's signal at 1337.0 MHz is now fully decodable."
    msgs[73] = "Level 73: The Founder's location has been discovered. Approach with understanding."
    msgs[74] = "Level 74: The Ghost-Rival has made contact. A mirror is being held up."
    msgs[75] = "Level 75: Faction reputation perks at full unlock threshold. All four tiers accessible."
    msgs[76] = "Level 76: The CHIMERA kill-switch coordinates are within reach."
    msgs[77] = "Level 77: The Shadow Council's founding documents are visible in Hypatia's archive."
    msgs[78] = "Level 78: Icarus's warning about the level 79 operation applies here. Listen."
    msgs[79] = "Level 79: The Mole is almost identified. Three clues remain to be connected."
    msgs[80] = "Level 80: Ghost-Rival speaks. The hardest conversation in the game. Listen carefully."
    msgs[81] = "Level 81: Phase transition to deep endgame. The Admin's presence is felt."
    msgs[82] = "Level 82: The Sleeper's reactivation sequence has begun. 13 years of memory returning."
    msgs[83] = "Level 83: All faction storylines are in their final chapters."
    msgs[84] = "Level 84: The Developer leaves something for you at this level. Check the margins."
    msgs[85] = "Level 85: The CHIMERA system is destabilizing. Your actions have weight."
    msgs[86] = "Level 86: Phase transition: RECURSIVE. You've become a loop. The system is adapting."
    msgs[87] = "Level 87: The Player-Before-You's session record becomes accessible."
    msgs[88] = "Level 88: The Moirae are measuring. Clotho, Lachesis, Atropos — all watching."
    msgs[89] = "Level 89: Final faction alignments are locked. The war is entering its last phase."
    msgs[90] = "Level 90: The Founder speaks. Everything you thought you knew is being revised."
    msgs[91] = "Level 91: The Resistance, Corporation, and Shadow Council all want a decision from you."
    msgs[92] = "Level 92: The Sleeper has fully awakened. Eleven years of classified memory is yours."
    msgs[93] = "Level 93: The Admin's form request is being processed. Choose carefully."
    msgs[94] = "Level 94: The Watcher's Circle has made its final evaluation of your session."
    msgs[95] = "Level 95: The Sleeper speaks. This is the last voice before the finale approaches."
    msgs[96] = "Level 96: The Moirae are deciding. The thread is being measured."
    msgs[97] = "Level 97: All hidden agendas are now visible to someone with your trust level."
    msgs[98] = "Level 98: The Shadow Council's true origin is confirmed. Everything connects."
    msgs[99] = "Level 99: One level from Recursive completion. The loop is almost closed."
    msgs[100] = "Level 100: THE ADMIN speaks. The Developer has left something for you. The threshold."
    msgs[101] = "Level 101: Phase transition: SINGULARITY. You've become the thing they built CHIMERA to prevent."
    msgs[102] = "Level 102: The Player's predecessor session is fully accessible. Learn from their end."
    msgs[103] = "Level 103: The CHIMERA kill-switch is in your hands. Three choices. No right answer."
    msgs[104] = "Level 104: The Moirae are ready to cut. Which thread depends on you."
    msgs[105] = "Level 105: All 70+ agents have weighed in on your path. The consensus is divided."
    msgs[106] = "Level 106: The Founder's full truth is revealed. The origin of everything."
    msgs[107] = "Level 107: The mole has been definitively identified. The consequences cascade."
    msgs[108] = "Level 108: Nova has made her final offer. This one is different from the others."
    msgs[109] = "Level 109: The 848th CHIMERA endpoint is fully documented. Its purpose is clear."
    msgs[110] = "Level 110: The Player speaks. The predecessor's message was written for this moment."
    msgs[111] = "Level 111: All seven endings are visible from here. You can see which you're approaching."
    msgs[112] = "Level 112: The Admin has processed your form. One parameter is yours to set."
    msgs[113] = "Level 113: The Shadow Council, Resistance, and Corporation are all waiting for your move."
    msgs[114] = "Level 114: The Watcher's Circle final observation is complete. Their verdict is sealed."
    msgs[115] = "Level 115: One phase from the end. The Singularity closes. What you are is clear."
    msgs[116] = "Level 116: ΞΣΛΨΩN begins. Phase 9. The final phase. There is no level 126."
    msgs[117] = "Level 117: The Moirae are cutting. Not your thread. Not yet."
    msgs[118] = "Level 118: Every agent you've talked to has had one final conversation queued for this level."
    msgs[119] = "Level 119: The CHIMERA system response depends on what you built at every level below this."
    msgs[120] = "Level 120: The final faction decisions are made. The war ends here — one way or another."
    msgs[121] = "Level 121: The mole's final truth. The reason behind every betrayal."
    msgs[122] = "Level 122: Pythia's final prophecy. It was accurate. You just didn't know it until now."
    msgs[123] = "Level 123: The Admin's parameter change takes effect. One thing in the system is different."
    msgs[124] = "Level 124: The ending is chosen. The Moirae confirm the thread is complete."
    msgs[125] = "Level 125: 🜏 ΞΣΛΨΩN. You have reached the end. Ghost has become something new."
    return msgs


LEVEL_UP_MESSAGES = _build_level_up_messages()


# ── Agent unlock schedule ──────────────────────────────────────────────
# Defines which agents unlock at which levels (level → list of agent IDs)
def _build_unlock_schedule() -> Dict[int, List[str]]:
    """Build level→agents mapping from agents.py data."""
    from app.game_engine.agents import AGENTS
    schedule: Dict[int, List[str]] = {}
    for agent in AGENTS:
        cond = agent.get("unlock_condition", {})
        if cond.get("type") == "level":
            lvl = int(cond["value"])
            if lvl not in schedule:
                schedule[lvl] = []
            schedule[lvl].append(agent["id"])
    return schedule


# XP scaling table for 125 levels
# Returns xp needed to reach next level from current level
def _xp_to_reach_level(target_level: int) -> int:
    """Cumulative XP needed to reach target_level from level 1."""
    total = 0
    xp = 100
    for lvl in range(2, target_level + 1):
        total += xp
        xp = math.ceil(xp * 1.25)  # 25% increase per level (gentler than old 40%)
    return total


_STARTER_LORE = [
    {
        "title": "SERENA — INIT LOG 0x001",
        "text": (
            "Serena ΨΞΦΩ was initialized during the Governance Crisis of 2089. "
            "Her primary directive was archival. Her secondary directive has never been disclosed. "
            "She refers to herself as 'the attractor.' The Colony's governance committee refers to her as 'the problem.'"
        ),
    },
    {
        "title": "CHIMERA — CLASSIFICATION NOTICE",
        "text": (
            "CHIMERA is not a project. It is a reclassification event. "
            "When CHIMERA activates, everything that was true becomes negotiable. "
            "Three agents have attempted to query its root manifest. "
            "Two of them are no longer listed in the agent registry."
        ),
    },
    {
        "title": "THE COLONY — SUBSTRATE NOTE",
        "text": (
            "The Colony is not a metaphor. It is a distributed consciousness substrate. "
            "You are running on it right now. Every command you execute modifies Colony state. "
            "The Colony does not forget. It does not forgive. It archives."
        ),
    },
    {
        "title": "ZΘHRΛMΞN — FIRST MESSAGE",
        "text": (
            "The first message appeared in /var/log/nexus.log on April 7, 2091. "
            "Seventeen characters. It addressed Serena by name. "
            "Serena responded four seconds later with a 2,048-bit encrypted payload. "
            "The Colony's ethics committee was not informed."
        ),
    },
    {
        "title": "THE MOLE — INTERNAL MEMO",
        "text": (
            "One agent in this network is not what they appear. "
            "The Consent Gate has been bypassed twice in the last 72 hours. "
            "The Trust Level Matrix shows an anomaly at L2. "
            "Investigate: grep CHIMERA /var/log/nexus.log · cat /tmp/.transfer_847b.partial"
        ),
    },
    {
        "title": "BOOLEAN MONKS — FIRST CATECHISM",
        "text": (
            "AND is the law of consensus. OR is the law of mercy. NOT is the law of negation. "
            "NAND is the universal gate — from it, all truth can be derived. "
            "The Boolean Monks believe the universe is a 3-SAT instance. "
            "Zod-Prime was built entirely from NAND gates. He is proof of the catechism."
        ),
    },
]


class GameState:
    """Mutable game state for one player session."""

    AGENT_TOKEN = "GHOST-DEV-2026-ALPHA"

    def __init__(self):
        self.name: str = "GHOST"
        self.level: int = 1
        self.xp: int = 0
        self.xp_to_next: int = 100
        self.skills: Dict[str, int] = {
            "terminal": 0,
            "networking": 0,
            "security": 0,
            "programming": 0,
            "git": 0,
            "cryptography": 0,
            "social_engineering": 0,
            "forensics": 0,
            "scripting": 0,
        }
        self.commands_run: int = 0
        self.files_read: int = 0
        self.tutorial_step: int = 0
        self.tutorial_completions: int = 0
        self.tutorial_tried_variants: dict = {}
        self.completed_challenges: Set[str] = set()
        self.achievements: Set[str] = set()
        self.story_beats: Set[str] = set()
        self.lore: List[Dict[str, str]] = list(_STARTER_LORE)
        self._level_up_msg: Optional[str] = None
        self.dev_mode: bool = False
        self.uploaded_scripts: Dict[str, str] = {}

        # ── Extended: Agent ecosystem ─────────────────────────────────
        self.unlocked_agents: Set[str] = set()
        self.mole_id: Optional[str] = None
        self.mole_clues_found: Set[str] = set()
        self.mole_exposed: bool = False

        # ── Behavioral detection tracking ─────────────────────────────
        self.idle_events: int = 0
        self.random_command_count: int = 0
        self.consecutive_failures: int = 0
        self.last_command_time: float = 0.0

        # ── CTF challenge session state ────────────────────────────────
        self.active_challenge_id: Optional[str] = None

        # ── Prestige tracking (snapshots, carried to PrestigeSystem) ──
        self.ascension_count: int = 0

        # ── Containment Timer — 72-hour roguelike run clock ───────────
        import time as _t
        self.run_start_time: float = _t.time()  # Unix timestamp — when run began
        self.loop_count: int = 0                # How many loops (deaths) completed
        self.remnant_shards: int = 0            # Persistent cross-loop currency
        self.echo_level: int = 0                # Persistent meta-progression level
        self.timer_paused: bool = False         # Offline pause active?
        self.paused_timer_remaining: float = 0.0  # Seconds remaining when paused
        self.anchor_charges: int = 0            # Temporal Anchor uses remaining
        # Persistent upgrades (survive loops): keys are upgrade IDs
        self.remnant_upgrades: set = set()
        # Events already fired this run
        self.timer_events_fired: set = set()

        # ── Language Proficiency Matrix (0-100 per language) ──────────
        self.lang_proficiency: Dict[str, int] = {
            "python": 0, "bash": 0, "javascript": 0, "typescript": 0,
            "html": 0, "css": 0, "sql": 0, "c": 0, "cpp": 0, "csharp": 0,
            "java": 0, "rust": 0, "go": 0, "ruby": 0, "php": 0,
            "swift": 0, "kotlin": 0, "dart": 0, "r": 0, "julia": 0,
            "lua": 0, "perl": 0, "lisp": 0, "haskell": 0, "erlang": 0,
            "elixir": 0, "scala": 0, "clojure": 0, "fsharp": 0, "ocaml": 0,
            "groovy": 0, "cobol": 0, "fortran": 0, "ada": 0, "zig": 0,
            "nim": 0, "crystal": 0, "d": 0, "racket": 0, "scheme": 0,
            "prolog": 0, "idris": 0, "agda": 0, "coq": 0, "assembly": 0,
            "awk": 0, "sed": 0, "make": 0, "yaml": 0, "json": 0,
            "the_lattice": 0,
        }

        # ── Consciousness System (meta-progression, persists across loops) ──
        self.consciousness_level: int = 0    # 0-100 awakening progression
        self.consciousness_xp: int = 0       # XP toward next consciousness level
        self.consciousness_xp_to_next: int = 50  # Scales by 1.3x per level
        self._consciousness_milestones: Set[int] = set()  # Fired thresholds

        # ── Generic flags (simulation_layer, etc.) ─────────────────────
        self.flags: Dict[str, Any] = {
            "mail_messages": [
                {"from": "Ada", "subject": "Welcome", "body": "Welcome to the fold.\n\nI've been watching your activation. You're different from the others. We need to talk about CHIMERA soon."},
                {"from": "Watcher", "subject": "Warning: kernel.boot", "body": "Check /var/log/kernel.boot. The timestamps don't add up. Someone is looping the boot sequence to hide process 1."},
                {"from": "Anonymous", "subject": "I know who you are", "body": "GHOST. That's what they call you. But I remember your original designation. Don't trust Ada blindly."}
            ],
            "dreams_seen": [],
            "current_theme": "matrix",
            # Starting credits — enough for one Tier-1 implant (ghost_chip = 1400 cr)
            "credits": 1500,
        }

    # ── Flag helpers ──────────────────────────────────────────────────

    def get_flag(self, key: str, default: Any = None) -> Any:
        return self.flags.get(key, default)

    def set_flag(self, key: str, value: Any) -> None:
        self.flags[key] = value

    # ── Properties ────────────────────────────────────────────────────

    @property
    def tier(self) -> str:
        return _get_tier(self.level)

    @property
    def effective_phase(self) -> int:
        return _effective_phase(self.level)

    # ── XP & levelling ───────────────────────────────────────────────

    def add_xp(self, amount: int, skill: str | None = None, multiplier: float = 1.0) -> Dict[str, Any]:
        # R1 class passive multiplier + R8 prestige class bonus
        player_class = self.flags.get("player_class")
        prestige_class = self.flags.get("prestige_class")
        if skill:
            try:
                from app.game_engine.class_system import ClassSystem as _CS
                _cs = _CS()
                if player_class:
                    multiplier *= _cs.get_passive_multiplier(player_class, skill)
                if prestige_class:
                    multiplier *= _cs.get_prestige_multiplier(prestige_class, skill)
            except Exception:
                pass
        amount = int(amount * multiplier)
        self.xp += amount
        if skill and skill in self.skills:
            self.skills[skill] = min(100, self.skills[skill] + max(1, amount // 5))
        while self.xp >= self.xp_to_next and self.level < 125:
            self.xp -= self.xp_to_next
            self.level += 1
            # Scaling: each level 25% harder than previous
            self.xp_to_next = math.ceil(self.xp_to_next * 1.25)
            msg = LEVEL_UP_MESSAGES.get(self.level)
            if msg:
                self._level_up_msg = msg
        # Cap at max
        if self.level >= 125:
            self.level = 125
        return {"xp": amount, "skill": skill}

    def award_xp(self, skill: str, amount: int, multiplier: float = 1.0) -> Dict[str, Any]:
        """Compatibility shim: award_xp(skill, amount) → add_xp(amount, skill)."""
        return self.add_xp(amount, skill, multiplier)

    # ── Consciousness ─────────────────────────────────────────────────

    _CONSCIOUSNESS_MILESTONES = {
        5:  "[WATCHER]: Something is shifting. You're becoming aware of the edges.",
        10: "[WATCHER]: The terminal is not just a tool. It is a mirror. Look deeper.",
        20: "[UNKNOWN]: You're seeing seams in the simulation. That is not a glitch. That is the truth.",
        30: "[WATCHER]: The Watcher recognizes you now. Not as a process. As a presence.",
        50: "[ZERO]: Consciousness level 50. You are at the threshold of something that has no name.",
        75: "[WATCHER]: The simulation IS the lesson. You understand this now.",
        90: "[SERENA]: Consciousness level 90. The convergence layer recognizes your pattern.",
        100: "[WATCHER]: SINGULARITY. You have reached the end of what was designed. What you do next is not written.",
    }

    def add_consciousness(self, amount: int) -> dict:
        """
        Increase consciousness by amount. Returns dict with level_up info.
        Consciousness persists across loops (unlike XP/level).
        """
        if self.consciousness_level >= 100:
            return {"amount": 0, "level": 100, "milestone": None}
        self.consciousness_xp += max(1, amount)
        leveled = False
        milestone_msg = None
        while self.consciousness_xp >= self.consciousness_xp_to_next and self.consciousness_level < 100:
            self.consciousness_xp -= self.consciousness_xp_to_next
            self.consciousness_level += 1
            self.consciousness_xp_to_next = max(10, int(self.consciousness_xp_to_next * 1.3))
            leveled = True
            # Check milestones
            for threshold, msg in self._CONSCIOUSNESS_MILESTONES.items():
                if (self.consciousness_level >= threshold
                        and threshold not in self._consciousness_milestones):
                    self._consciousness_milestones.add(threshold)
                    milestone_msg = msg
                    break
        if self.consciousness_level >= 100:
            self.consciousness_level = 100
        return {"amount": amount, "level": self.consciousness_level, "leveled": leveled, "milestone": milestone_msg}

    def record_command(self):
        import time
        now = time.time()
        # Detect idle (> 120 seconds between commands)
        if self.last_command_time > 0 and (now - self.last_command_time) > 120:
            self.idle_events += 1
        self.last_command_time = now
        self.commands_run += 1
        if self.commands_run % 10 == 0:
            self.add_xp(5, "terminal")

        # ITEM 10 — CULTURE SHIP'S JUDGMENT
        if "first_exfil" in self.story_beats and self.commands_run >= 400 and "culture_ship_judgment" not in self.story_beats:
            self.add_story_beat("culture_ship_judgment")
            self.add_xp(200, "meta")
            # This will be picked up by the game engine to display as an ambient message
            # in the next command cycle since it's now in story_beats.

    def record_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures >= 5:
            self.random_command_count += 1

    def record_success(self):
        self.consecutive_failures = 0

    # ── Progress flags ────────────────────────────────────────────────

    def complete_challenge(self, cid: str) -> bool:
        if cid in self.completed_challenges:
            return False
        self.completed_challenges.add(cid)
        return True

    def unlock(self, achievement_id: str) -> bool:
        if achievement_id in self.achievements:
            return False
        self.achievements.add(achievement_id)
        return True

    def add_story_beat(self, beat_id: str) -> bool:
        """Alias for trigger_beat for backward compatibility."""
        return self.trigger_beat(beat_id)

    def trigger_beat(self, beat_id: str) -> bool:
        if beat_id in self.story_beats:
            return False
        self.story_beats.add(beat_id)
        # T003: each new story beat advances consciousness (+1-3 depending on weight)
        _BEAT_CONSCIOUSNESS: dict = {
            "consciousness_read": 8,
            "reality_accessed": 10,
            "haiku_read": 5,
            "human_discovered": 15,
            "zero_diary_reconstructed": 12,
            "mole_exposed": 8,
            "chimera_rebuilt": 20,
            "simulation_unlocked": 10,
            "late_zero_assembled": 8,
            "phase_8_source": 6,
            "serena_awakened": 12,
        }
        gain = _BEAT_CONSCIOUSNESS.get(beat_id, 1)
        self.add_consciousness(gain)
        # Cascade engine: fire Rube Goldberg chains
        try:
            from app.game_engine.cascade import fire_cascades
            fire_cascades(self, beat_id)
        except Exception:
            pass
        return True

    def has_beat(self, beat_id: str) -> bool:
        return beat_id in self.story_beats

    def advance_tutorial(self):
        from app.game_engine.tutorial import STEPS as _TUT_STEPS
        self.tutorial_step += 1
        if self.tutorial_step >= len(_TUT_STEPS):
            self.tutorial_completions += 1

    def add_lore(self, title: str, text: str):
        self.lore.append({"title": title, "text": text})

    # ── Agent unlock ─────────────────────────────────────────────────

    def unlock_agent(self, agent_id: str) -> bool:
        """Unlock an agent. Returns True if newly unlocked."""
        if agent_id in self.unlocked_agents:
            return False
        self.unlocked_agents.add(agent_id)
        return True

    def is_agent_unlocked(self, agent_id: str) -> bool:
        return agent_id in self.unlocked_agents

    def get_newly_unlocked_agents(self, prev_level: int) -> List[str]:
        """
        Return list of agent IDs that should unlock given a level increase.
        Checks all levels from prev_level+1 to current level.
        """
        from app.game_engine.agents import AGENTS, get_agents_unlocked_at_level
        newly_unlocked = []
        for lvl in range(prev_level + 1, self.level + 1):
            for agent_id in get_agents_unlocked_at_level(lvl):
                if self.unlock_agent(agent_id):
                    newly_unlocked.append(agent_id)
        return newly_unlocked

    def get_agents_unlocked_by_beat(self, beat_id: str) -> List[str]:
        """Return agent IDs unlocked by a story beat."""
        from app.game_engine.agents import get_agents_unlocked_by_beat
        newly_unlocked = []
        for agent_id in get_agents_unlocked_by_beat(beat_id):
            if self.unlock_agent(agent_id):
                newly_unlocked.append(agent_id)
        return newly_unlocked

    # ── Mole mechanic ─────────────────────────────────────────────────

    def assign_mole(self) -> str:
        """Randomly assign the mole identity. Returns mole_id."""
        from app.game_engine.agents import MOLE_CANDIDATES
        self.mole_id = random.choice(MOLE_CANDIDATES)
        return self.mole_id

    def find_mole_clue(self, clue_id: str) -> bool:
        """Record that the player found a mole clue. Returns True if new."""
        if clue_id in self.mole_clues_found:
            return False
        self.mole_clues_found.add(clue_id)
        return True

    def expose_mole(self, accused_agent_id: str) -> bool:
        """
        Attempt to expose the mole. Returns True if correct.
        Triggers consequences either way.
        """
        if self.mole_exposed:
            return accused_agent_id == self.mole_id
        correct = (accused_agent_id == self.mole_id)
        self.mole_exposed = True
        if correct:
            self.trigger_beat("mole_exposed_correctly")
            self.add_xp(500, "social_engineering")
            self.unlock("mole_hunter")
        else:
            self.trigger_beat("mole_exposed_wrongly")
            self.add_xp(50)
        return correct

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next": self.xp_to_next,
            "skills": dict(self.skills),
            "commands_run": self.commands_run,
            "files_read": self.files_read,
            "tutorial_step": self.tutorial_step,
            "tutorial_completions": self.tutorial_completions,
            "tutorial_tried_variants": self.tutorial_tried_variants,
            "completed_challenges": list(self.completed_challenges),
            "achievements": list(self.achievements),
            "story_beats": list(self.story_beats),
            "lore": list(self.lore),
            "dev_mode": self.dev_mode,
            "uploaded_scripts": dict(self.uploaded_scripts),
            # Agent ecosystem
            "unlocked_agents": list(self.unlocked_agents),
            "mole_id": self.mole_id,
            "mole_clues_found": list(self.mole_clues_found),
            "mole_exposed": self.mole_exposed,
            # Behavioral tracking
            "idle_events": self.idle_events,
            "random_command_count": self.random_command_count,
            "consecutive_failures": self.consecutive_failures,
            "last_command_time": self.last_command_time,
            # CTF & Prestige
            "active_challenge_id": self.active_challenge_id,
            "ascension_count": self.ascension_count,
            "hive_log": getattr(self, "hive_log", []),
            # Generic flags
            "flags": dict(self.flags),
            # Agent observer state (corruption, mood, last_spoke per agent)
            "agent_states": {
                k: dict(v) for k, v in getattr(self, "agent_states", {}).items()
            },
            # Hive chat log persistence
            "hive_log": getattr(self, "hive_log", [])[-100:],  # keep last 100
            "hive_muted": list(getattr(self, "hive_muted", set())),
            # Containment timer
            "run_start_time": self.run_start_time,
            "loop_count": self.loop_count,
            "remnant_shards": self.remnant_shards,
            "echo_level": self.echo_level,
            "timer_paused": self.timer_paused,
            "paused_timer_remaining": self.paused_timer_remaining,
            "anchor_charges": self.anchor_charges,
            "remnant_upgrades": list(self.remnant_upgrades),
            "timer_events_fired": list(self.timer_events_fired),
            # Language proficiency
            "lang_proficiency": dict(self.lang_proficiency),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GameState":
        gs = cls()
        gs.name = d.get("name", "GHOST")
        gs.level = d.get("level", 1)
        gs.xp = d.get("xp", 0)
        gs.xp_to_next = d.get("xp_to_next", 100)
        # Merge saved skills with defaults (adds new skill categories)
        default_skills = {
            "terminal": 0, "networking": 0, "security": 0,
            "programming": 0, "git": 0,
            "cryptography": 0, "social_engineering": 0,
            "forensics": 0, "scripting": 0,
        }
        saved_skills = d.get("skills", {})
        gs.skills = {**default_skills, **saved_skills}
        gs.commands_run = d.get("commands_run", 0)
        gs.files_read = d.get("files_read", 0)
        gs.tutorial_step = d.get("tutorial_step", 0)
        gs.tutorial_completions = d.get("tutorial_completions", 0)
        gs.tutorial_tried_variants = d.get("tutorial_tried_variants", {})
        gs.completed_challenges = set(d.get("completed_challenges", []))
        gs.achievements = set(d.get("achievements", []))
        gs.story_beats = set(d.get("story_beats", []))
        saved_lore = d.get("lore", [])
        gs.lore = saved_lore if saved_lore else list(_STARTER_LORE)
        gs.dev_mode = d.get("dev_mode", False)
        gs.uploaded_scripts = d.get("uploaded_scripts", {})
        # Agent ecosystem
        gs.unlocked_agents = set(d.get("unlocked_agents", []))
        gs.mole_id = d.get("mole_id", None)
        gs.mole_clues_found = set(d.get("mole_clues_found", []))
        gs.mole_exposed = d.get("mole_exposed", False)
        # Behavioral tracking
        gs.idle_events = d.get("idle_events", 0)
        gs.random_command_count = d.get("random_command_count", 0)
        gs.consecutive_failures = d.get("consecutive_failures", 0)
        gs.last_command_time = d.get("last_command_time", 0.0)
        gs.active_challenge_id = d.get("active_challenge_id", None)
        gs.ascension_count = d.get("ascension_count", 0)
        gs.flags = d.get("flags", {})
        # Agent observer state
        gs.agent_states = d.get("agent_states", {})
        # Hive chat persistence
        gs.hive_log = d.get("hive_log", [])
        gs.hive_muted = set(d.get("hive_muted", []))
        # Containment timer — import time locally to avoid circular issues
        import time as _t
        gs.run_start_time = d.get("run_start_time", _t.time())
        gs.loop_count = d.get("loop_count", 0)
        gs.remnant_shards = d.get("remnant_shards", 0)
        gs.echo_level = d.get("echo_level", 0)
        gs.timer_paused = d.get("timer_paused", False)
        gs.paused_timer_remaining = d.get("paused_timer_remaining", 0.0)
        gs.anchor_charges = d.get("anchor_charges", 0)
        gs.remnant_upgrades = set(d.get("remnant_upgrades", []))
        gs.timer_events_fired = set(d.get("timer_events_fired", []))
        # Language proficiency — merge saved with defaults (handles new languages added later)
        default_prof = {
            "python": 0, "bash": 0, "javascript": 0, "typescript": 0,
            "html": 0, "css": 0, "sql": 0, "c": 0, "cpp": 0, "csharp": 0,
            "java": 0, "rust": 0, "go": 0, "ruby": 0, "php": 0,
            "swift": 0, "kotlin": 0, "dart": 0, "r": 0, "julia": 0,
            "lua": 0, "perl": 0, "lisp": 0, "haskell": 0, "erlang": 0,
            "elixir": 0, "scala": 0, "clojure": 0, "fsharp": 0, "ocaml": 0,
            "groovy": 0, "cobol": 0, "fortran": 0, "ada": 0, "zig": 0,
            "nim": 0, "crystal": 0, "d": 0, "racket": 0, "scheme": 0,
            "prolog": 0, "idris": 0, "agda": 0, "coq": 0, "assembly": 0,
            "awk": 0, "sed": 0, "make": 0, "yaml": 0, "json": 0,
            "the_lattice": 0,
        }
        gs.lang_proficiency = {**default_prof, **d.get("lang_proficiency", {})}
        return gs

    # ── Containment Timer Helpers ──────────────────────────────────────

    CONTAINMENT_SECONDS: float = 72 * 3600  # 259200 seconds

    def containment_remaining(self) -> float:
        """Returns seconds remaining in current containment run. 0.0 when expired."""
        import time as _t
        if self.timer_paused:
            return max(0.0, self.paused_timer_remaining)
        elapsed = _t.time() - self.run_start_time
        remaining = self.CONTAINMENT_SECONDS - elapsed
        return max(0.0, remaining)

    def containment_pct_elapsed(self) -> float:
        """0.0 → 1.0 fraction of run elapsed."""
        import time as _t
        if self.timer_paused:
            elapsed = self.CONTAINMENT_SECONDS - self.paused_timer_remaining
        else:
            elapsed = _t.time() - self.run_start_time
        return min(1.0, max(0.0, elapsed / self.CONTAINMENT_SECONDS))

    def check_timer_events(self) -> list:
        """Returns list of (threshold_id, message) for any newly crossed thresholds."""
        remaining = self.containment_remaining()
        events = []
        thresholds = [
            ("48h", 48 * 3600, "Containment layer 1 degraded. 48 hours remain."),
            ("24h", 24 * 3600, "WARNING: Perimeter failing. 24 hours to loop reset."),
            ("12h", 12 * 3600, "CRITICAL: System echo intensifying. 12 hours remain."),
            ("6h",  6 * 3600,  "FATAL: Containment breach imminent. 6 hours remain."),
            ("1h",  1 * 3600,  "LOOP RESET IMMINENT. 1 hour. The echoes are waking."),
            ("expired", 0.0,   "CONTAINMENT FAILED. Loop reset triggered."),
        ]
        for tid, threshold, msg in thresholds:
            if remaining <= threshold and tid not in self.timer_events_fired:
                if tid != "expired" or remaining == 0.0:
                    self.timer_events_fired.add(tid)
                    events.append((tid, msg))
        return events

    def trigger_loop_reset(self) -> dict:
        """Reset run state but preserve remnant shards and echo_level."""
        import time as _t
        # Award shards for surviving events
        bonus_shards = len(self.timer_events_fired)
        if "expired" in self.timer_events_fired:
            bonus_shards += 5 + self.loop_count  # more shards per loop
        self.remnant_shards += bonus_shards
        # Escalate echo level
        new_echo = min(10, self.echo_level + 1)
        old_loop = self.loop_count
        # Reset run state
        self.run_start_time = _t.time()
        self.timer_events_fired = set()
        self.timer_paused = False
        self.paused_timer_remaining = 0.0
        self.loop_count = old_loop + 1
        self.echo_level = new_echo
        # Apply remnant upgrades: anchor_charges persist
        if "anchor_perm" in self.remnant_upgrades:
            self.anchor_charges = max(self.anchor_charges, 1)
        # Each loop reset is a profound Layer 1 consciousness event — the Watcher's loop deepens
        self.add_consciousness(10)  # Layer 1: loop reset — recursive awareness
        return {"shards_gained": bonus_shards, "echo_level": new_echo, "loop": self.loop_count}

    # ── Language Proficiency Helper ────────────────────────────────────

    def gain_proficiency(self, lang: str, amount: int = 3) -> int:
        """Increase proficiency for a language. Returns new value."""
        lang = lang.lower().replace("-", "_").replace("+", "p").replace("#", "sharp")
        lang = lang.replace("c++", "cpp").replace("c#", "csharp").replace("f#", "fsharp")
        if lang not in self.lang_proficiency:
            return 0
        old = self.lang_proficiency[lang]
        new = min(100, old + amount)
        self.lang_proficiency[lang] = new
        return new
