"""
daily_quests.py — Daily & Weekly Quest System for Terminal Depths

Quests reset based on real-world UTC date (daily) or week number (weekly).
Quest definitions are static pools; active quests are drawn based on date seed
so all players on the same day get the same quests (simulated "shared world").

State stored in gs.flags as:
  "daily_quest_date"    : "2026-03-18"
  "daily_quests_active" : [quest_id, ...]
  "daily_quest_progress": {quest_id: int}
  "daily_quest_claimed" : {quest_id: bool}
  "weekly_quest_wn"     : 11   (ISO week number)
  "weekly_quest_active" : quest_id
  "weekly_quest_progress": int
  "weekly_quest_claimed" : bool
"""

from __future__ import annotations
import random
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .gamestate import GameState

# ─────────────────────────────────────────────────────────────────────────────
# Quest definitions
# ─────────────────────────────────────────────────────────────────────────────

DAILY_QUESTS: List[Dict[str, Any]] = [
    # Terminal fundamentals
    {
        "id": "dq_pwd_3",
        "title": "Orient Yourself",
        "desc": "Run `pwd` 3 times. The path is always worth confirming.",
        "cmd_match": r"^pwd$",
        "target": 3,
        "xp": 15,
        "credits": 10,
        "skill": "terminal",
        "tags": ["basic", "orientation"],
    },
    {
        "id": "dq_ls_5",
        "title": "What Lies Beneath",
        "desc": "Use `ls` in 5 different directories. Reconnaissance first.",
        "cmd_match": r"^ls\b",
        "target": 5,
        "xp": 20,
        "credits": 15,
        "skill": "terminal",
        "tags": ["basic", "recon"],
    },
    {
        "id": "dq_cat_lore",
        "title": "The Reader",
        "desc": "Read 3 files with `cat`. The answers are in the files.",
        "cmd_match": r"^cat\b",
        "target": 3,
        "xp": 25,
        "credits": 20,
        "skill": "terminal",
        "tags": ["lore", "reading"],
    },
    # Agent interactions
    {
        "id": "dq_talk_2",
        "title": "Social Protocol",
        "desc": "Talk to 2 different agents. Relationships matter.",
        "cmd_match": r"^(talk|ask|msg|dm|whisper)\b",
        "target": 2,
        "xp": 30,
        "credits": 25,
        "skill": "social_engineering",
        "tags": ["social", "agents"],
    },
    {
        "id": "dq_msg_ada",
        "title": "Reach Out",
        "desc": "Send a private message to Ada. She's been waiting.",
        "cmd_match": r"^msg\s+ada\b",
        "target": 1,
        "xp": 40,
        "credits": 30,
        "skill": "social_engineering",
        "tags": ["social", "ada", "story"],
        "hint": "Try: msg ada hello",
    },
    {
        "id": "dq_hive_check",
        "title": "Community Service",
        "desc": "Check the Hive chat. Stay connected to the colony.",
        "cmd_match": r"^hive\b",
        "target": 1,
        "xp": 20,
        "credits": 15,
        "skill": "social_engineering",
        "tags": ["social", "hive"],
    },
    # Security / hacking
    {
        "id": "dq_scan_network",
        "title": "Daily Sweep",
        "desc": "Run a network scan. See what changed overnight.",
        "cmd_match": r"^(nmap|scan|netstat|ss|ifconfig|ip)\b",
        "target": 2,
        "xp": 35,
        "credits": 30,
        "skill": "networking",
        "tags": ["security", "recon"],
    },
    {
        "id": "dq_check_logs",
        "title": "Audit Trail",
        "desc": "Read system logs 2 times. The evidence is in the logs.",
        "cmd_match": r"^(journalctl|dmesg|tail|cat\s+/var/log)\b",
        "target": 2,
        "xp": 30,
        "credits": 25,
        "skill": "security",
        "tags": ["security", "forensics"],
    },
    {
        "id": "dq_exploit_attempt",
        "title": "Penetration Test",
        "desc": "Attempt a privilege escalation. Even failure teaches.",
        "cmd_match": r"^(exploit|sudo|gtfobins|suid)\b",
        "target": 1,
        "xp": 50,
        "credits": 40,
        "skill": "security",
        "tags": ["security", "exploit"],
        "hint": "Try: exploit --list",
    },
    # Puzzle systems
    {
        "id": "dq_logic_gate",
        "title": "Boolean Meditation",
        "desc": "Run a logic gate simulation. The Boolean Monks approve.",
        "cmd_match": r"^logic\b",
        "target": 1,
        "xp": 40,
        "credits": 35,
        "skill": "programming",
        "tags": ["puzzle", "logic", "boolean_monks"],
    },
    {
        "id": "dq_sat_run",
        "title": "Satisfiability",
        "desc": "Engage the SAT solver. Find satisfaction in constraint.",
        "cmd_match": r"^sat\b",
        "target": 1,
        "xp": 40,
        "credits": 35,
        "skill": "programming",
        "tags": ["puzzle", "sat", "algorithmic_guild"],
    },
    {
        "id": "dq_tis100_run",
        "title": "Assembly Practice",
        "desc": "Work on a TIS-100 puzzle. The machine thinks in registers.",
        "cmd_match": r"^tis100\b",
        "target": 1,
        "xp": 45,
        "credits": 40,
        "skill": "programming",
        "tags": ["puzzle", "tis100"],
    },
    {
        "id": "dq_sort_challenge",
        "title": "Algorithmic Efficiency",
        "desc": "Run a sorting challenge. Measure yourself against optimal.",
        "cmd_match": r"^sort\b",
        "target": 1,
        "xp": 35,
        "credits": 30,
        "skill": "programming",
        "tags": ["puzzle", "sort", "algorithmic_guild"],
    },
    # Economy
    {
        "id": "dq_bank_check",
        "title": "Financial Oversight",
        "desc": "Check your bank balance. Know your resources.",
        "cmd_match": r"^bank\b",
        "target": 1,
        "xp": 10,
        "credits": 50,  # cash reward for checking
        "skill": "terminal",
        "tags": ["economy"],
    },
    {
        "id": "dq_research_view",
        "title": "Technology Survey",
        "desc": "View the research tree. Know what you can unlock.",
        "cmd_match": r"^research\b",
        "target": 1,
        "xp": 15,
        "credits": 20,
        "skill": "programming",
        "tags": ["economy", "research"],
    },
    # Lore / exploration
    {
        "id": "dq_anomaly_check",
        "title": "SCP Compliance",
        "desc": "Check the anomaly registry. Containment is everyone's job.",
        "cmd_match": r"^anomaly\b",
        "target": 1,
        "xp": 25,
        "credits": 20,
        "skill": "terminal",
        "tags": ["lore", "scp"],
    },
    {
        "id": "dq_read_chimera",
        "title": "Know Your Enemy",
        "desc": "Read a file from /opt/chimera/. Know what you're fighting.",
        "cmd_match": r"^cat\s+/opt/chimera/",
        "target": 1,
        "xp": 50,
        "credits": 45,
        "skill": "security",
        "tags": ["lore", "chimera", "story"],
        "hint": "Try: cat /opt/chimera/config/master.conf",
    },
    {
        "id": "dq_wiki_query",
        "title": "Knowledge Synthesis",
        "desc": "Look up a topic in the knowledge base.",
        "cmd_match": r"^(wiki|hint)\b",
        "target": 1,
        "xp": 20,
        "credits": 15,
        "skill": "terminal",
        "tags": ["learning", "wiki"],
    },
    # Meta / fun
    {
        "id": "dq_fortune",
        "title": "Seek Wisdom",
        "desc": "Read your fortune. It may be more accurate than you expect.",
        "cmd_match": r"^fortune\b",
        "target": 1,
        "xp": 10,
        "credits": 5,
        "skill": "terminal",
        "tags": ["fun"],
    },
    {
        "id": "dq_news_read",
        "title": "Stay Informed",
        "desc": "Read the colony news. Situational awareness.",
        "cmd_match": r"^news\b",
        "target": 1,
        "xp": 15,
        "credits": 10,
        "skill": "terminal",
        "tags": ["lore", "colony"],
    },
    {
        "id": "dq_git_status",
        "title": "Version Control",
        "desc": "Check git status. Know where the codebase stands.",
        "cmd_match": r"^git\s+(status|log|diff)\b",
        "target": 1,
        "xp": 20,
        "credits": 15,
        "skill": "git",
        "tags": ["git", "dev"],
    },
    {
        "id": "dq_commit_something",
        "title": "Leave a Mark",
        "desc": "Make a git commit. Contribution matters.",
        "cmd_match": r"^git\s+commit\b",
        "target": 1,
        "xp": 40,
        "credits": 35,
        "skill": "git",
        "tags": ["git", "dev"],
    },
    {
        "id": "dq_ps_check",
        "title": "Process Watch",
        "desc": "Check running processes with `ps aux`. What's watcher_eternal doing?",
        "cmd_match": r"^ps\b",
        "target": 1,
        "xp": 20,
        "credits": 15,
        "skill": "security",
        "tags": ["security", "forensics", "scp"],
        "hint": "Try: ps aux | grep watcher",
    },
    {
        "id": "dq_help_read",
        "title": "RTFM",
        "desc": "Read a man page or help entry. The documentation knows.",
        "cmd_match": r"^(man|help)\b",
        "target": 2,
        "xp": 15,
        "credits": 10,
        "skill": "terminal",
        "tags": ["learning"],
    },
]

WEEKLY_QUESTS: List[Dict[str, Any]] = [
    {
        "id": "wq_chimera_deep_dive",
        "title": "Operation: Open Eyes",
        "desc": (
            "The full CHIMERA picture. This week: read the master config, "
            "examine the source code, check the keys directory, and send a message to Nova. "
            "Four steps. Four discoveries."
        ),
        "steps": [
            {"cmd_match": r"^cat\s+/opt/chimera/config/master\.conf", "label": "Read master.conf"},
            {"cmd_match": r"^cat\s+/opt/chimera/src/chimera\.py", "label": "Read chimera.py"},
            {"cmd_match": r"^ls\s+/opt/chimera/(keys|core)", "label": "Check keys/core"},
            {"cmd_match": r"^msg\s+nova\b", "label": "Contact Nova"},
        ],
        "xp": 200,
        "credits": 150,
        "skill": "security",
        "unlock": "nova_deep_dialogue",
    },
    {
        "id": "wq_agent_network",
        "title": "Colony Relationship Map",
        "desc": (
            "Build your network. This week: private message 4 different agents, "
            "read the AI Council charter, check the hive 3 times, and view agent states."
        ),
        "steps": [
            {"cmd_match": r"^msg\s+(ada|raven|cypher|gordon|watcher|serena|nova|echo)\b",
             "label": "Message 4 agents", "target": 4},
            {"cmd_match": r"^cat\s+/opt/ai_council/CHARTER\.md", "label": "Read AI Council Charter"},
            {"cmd_match": r"^hive\b", "label": "Check Hive 3 times", "target": 3},
            {"cmd_match": r"^(agents|colony)\b", "label": "Check colony dashboard"},
        ],
        "xp": 200,
        "credits": 150,
        "skill": "social_engineering",
        "unlock": "colony_diplomat",
    },
    {
        "id": "wq_puzzle_gauntlet",
        "title": "Mathematical Ascension",
        "desc": (
            "Face all four puzzle systems. Logic gate → SAT solver → DP puzzle → Sorting arena. "
            "The Boolean Monks, Algorithmic Guild, and Serialists are watching."
        ),
        "steps": [
            {"cmd_match": r"^logic\b", "label": "Complete a Logic puzzle"},
            {"cmd_match": r"^sat\b", "label": "Run the SAT solver"},
            {"cmd_match": r"^dp\b", "label": "Attempt a DP challenge"},
            {"cmd_match": r"^sort\b", "label": "Run the Sorting arena"},
        ],
        "xp": 250,
        "credits": 200,
        "skill": "programming",
        "unlock": "cross_faction_respect",
    },
    {
        "id": "wq_deep_recon",
        "title": "Ghost Protocol: Reconnaissance",
        "desc": (
            "Full network survey. Map every accessible directory, "
            "read the anomaly registry, check all faction areas, "
            "and examine the process list."
        ),
        "steps": [
            {"cmd_match": r"^ls\b", "label": "Survey 10 directories", "target": 10},
            {"cmd_match": r"^anomaly\b", "label": "Read anomaly registry"},
            {"cmd_match": r"^faction\b", "label": "Check faction status"},
            {"cmd_match": r"^ps\b", "label": "Examine running processes"},
        ],
        "xp": 180,
        "credits": 140,
        "skill": "networking",
        "unlock": "recon_expert",
    },
    {
        "id": "wq_zero_hunt",
        "title": "Find Zero",
        "desc": (
            "Follow the trail. Read the Zero Specification, "
            "examine BLACK_NOVEMBER.log, check the kernel boot log, "
            "and message Ada about what you found."
        ),
        "steps": [
            {"cmd_match": r"^cat\s+/opt/chimera/core/ZERO_SPECIFICATION\.md", "label": "Read Zero Specification"},
            {"cmd_match": r"^cat\s+/opt/chimera/core/BLACK_NOVEMBER\.log", "label": "Read BLACK_NOVEMBER.log"},
            {"cmd_match": r"^cat\s+/var/log/kernel\.boot", "label": "Check kernel.boot timestamps"},
            {"cmd_match": r"^msg\s+ada\b", "label": "Report findings to Ada"},
        ],
        "xp": 300,
        "credits": 250,
        "skill": "security",
        "unlock": "zero_hunter",
        "story_beat": "zero_trail_followed",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────────────────────

class DailyQuestEngine:

    NUM_DAILY = 3   # quests shown per day

    def __init__(self, gs: "GameState"):
        self.gs = gs

    def _today(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _this_week(self) -> int:
        return datetime.now(timezone.utc).isocalendar()[1]

    def _seed_for_date(self, date_str: str) -> int:
        return int(hashlib.md5(date_str.encode()).hexdigest(), 16) % (2**31)

    def _refresh_daily(self):
        today = self._today()
        if self.gs.flags.get("daily_quest_date") == today:
            return  # already current
        seed = self._seed_for_date(today)
        rng = random.Random(seed)
        pool = list(DAILY_QUESTS)
        rng.shuffle(pool)
        selected = pool[:self.NUM_DAILY]
        self.gs.flags["daily_quest_date"] = today
        self.gs.flags["daily_quests_active"] = [q["id"] for q in selected]
        self.gs.flags["daily_quest_progress"] = {q["id"]: 0 for q in selected}
        self.gs.flags["daily_quest_claimed"] = {}

    def _refresh_weekly(self):
        wn = self._this_week()
        if self.gs.flags.get("weekly_quest_wn") == wn:
            return
        seed = self._seed_for_date(f"week-{wn}")
        rng = random.Random(seed)
        quest = rng.choice(WEEKLY_QUESTS)
        self.gs.flags["weekly_quest_wn"] = wn
        self.gs.flags["weekly_quest_active"] = quest["id"]
        self.gs.flags["weekly_quest_step"] = 0
        self.gs.flags["weekly_quest_claimed"] = False
        # Per-step targets
        self.gs.flags["weekly_quest_step_counts"] = {
            str(i): 0 for i in range(len(quest.get("steps", [])))
        }

    def get_daily_quests(self) -> List[Dict]:
        self._refresh_daily()
        ids = self.gs.flags.get("daily_quests_active", [])
        by_id = {q["id"]: q for q in DAILY_QUESTS}
        return [by_id[i] for i in ids if i in by_id]

    def get_weekly_quest(self) -> Optional[Dict]:
        self._refresh_weekly()
        wid = self.gs.flags.get("weekly_quest_active")
        by_id = {q["id"]: q for q in WEEKLY_QUESTS}
        return by_id.get(wid)

    def on_command(self, cmd_raw: str) -> List[dict]:
        """Called after every command. Updates quest progress. Returns reward lines."""
        import re
        self._refresh_daily()
        self._refresh_weekly()
        out = []

        # ── Daily quests ─────────────────────────────────────────────────────
        ids = self.gs.flags.get("daily_quests_active", [])
        progress = self.gs.flags.get("daily_quest_progress", {})
        claimed = self.gs.flags.get("daily_quest_claimed", {})
        by_id = {q["id"]: q for q in DAILY_QUESTS}

        for qid in ids:
            if claimed.get(qid):
                continue
            q = by_id.get(qid)
            if not q:
                continue
            if re.search(q["cmd_match"], cmd_raw.strip(), re.IGNORECASE):
                progress[qid] = progress.get(qid, 0) + 1
                self.gs.flags["daily_quest_progress"] = progress
                if progress[qid] >= q["target"]:
                    # Quest complete!
                    claimed[qid] = True
                    self.gs.flags["daily_quest_claimed"] = claimed
                    xp = q.get("xp", 20)
                    cr = q.get("credits", 0)
                    self.gs.add_xp(xp, q.get("skill", "terminal"))
                    # Award credits via economy if available
                    try:
                        from .economy import Economy
                        econ = Economy()
                        econ.deposit("player", cr, f"Daily Quest: {q['title']}")
                    except Exception:
                        pass
                    out += [
                        {"t": "system", "s": ""},
                        {"t": "system", "s": f"  ✓ DAILY QUEST COMPLETE: {q['title']}"},
                        {"t": "xp",    "s": f"  +{xp} XP · +{cr} credits"},
                        {"t": "dim",   "s": "  Type `quests` to see your progress."},
                        {"t": "system", "s": ""},
                    ]

        # ── Weekly quest ──────────────────────────────────────────────────────
        if not self.gs.flags.get("weekly_quest_claimed"):
            wquest = self.get_weekly_quest()
            if wquest:
                steps = wquest.get("steps", [])
                step_idx = self.gs.flags.get("weekly_quest_step", 0)
                step_counts = self.gs.flags.get("weekly_quest_step_counts", {})
                if step_idx < len(steps):
                    step = steps[step_idx]
                    step_target = step.get("target", 1)
                    cur = step_counts.get(str(step_idx), 0)
                    if re.search(step["cmd_match"], cmd_raw.strip(), re.IGNORECASE):
                        cur += 1
                        step_counts[str(step_idx)] = cur
                        self.gs.flags["weekly_quest_step_counts"] = step_counts
                        if cur >= step_target:
                            step_idx += 1
                            self.gs.flags["weekly_quest_step"] = step_idx
                            if step_idx >= len(steps):
                                # Weekly complete!
                                self.gs.flags["weekly_quest_claimed"] = True
                                xp = wquest.get("xp", 200)
                                cr = wquest.get("credits", 150)
                                self.gs.add_xp(xp, wquest.get("skill", "terminal"))
                                unlock = wquest.get("unlock")
                                if unlock:
                                    self.gs.flags[f"unlock_{unlock}"] = True
                                beat = wquest.get("story_beat")
                                if beat:
                                    self.gs.add_story_beat(beat)
                                try:
                                    from .economy import Economy
                                    econ = Economy()
                                    econ.deposit("player", cr, f"Weekly Quest: {wquest['title']}")
                                except Exception:
                                    pass
                                out += [
                                    {"t": "system", "s": ""},
                                    {"t": "system", "s": "  ╔═══════════════════════════════════════╗"},
                                    {"t": "system", "s": f"  ║  WEEKLY QUEST COMPLETE!               ║"},
                                    {"t": "system", "s": f"  ║  {wquest['title']:<37}║"},
                                    {"t": "system", "s": "  ╚═══════════════════════════════════════╝"},
                                    {"t": "xp",    "s": f"  +{xp} XP · +{cr} credits"},
                                    {"t": "system", "s": ""},
                                ]
                            else:
                                # Step complete
                                label = step.get("label", f"Step {step_idx}")
                                next_label = steps[step_idx].get("label", f"Step {step_idx+1}") if step_idx < len(steps) else ""
                                out += [
                                    {"t": "dim", "s": f"  [Weekly Quest] ✓ {label}"},
                                    {"t": "dim", "s": f"  [Weekly Quest] → Next: {next_label}"},
                                ]
        return out

    def display(self) -> List[dict]:
        """Full quests display for the `quests` command."""
        self._refresh_daily()
        self._refresh_weekly()
        today = self._today()
        out = [
            {"t": "system", "s": ""},
            {"t": "system", "s": "  ╔════════════════════════════════════════════════╗"},
            {"t": "system", "s": "  ║              ACTIVE QUESTS                     ║"},
            {"t": "system", "s": f"  ║  Date: {today}                      ║"},
            {"t": "system", "s": "  ╚════════════════════════════════════════════════╝"},
            {"t": "system", "s": ""},
            {"t": "system", "s": "  ── DAILY QUESTS ─────────────────────────────────"},
            {"t": "system", "s": ""},
        ]
        daily = self.get_daily_quests()
        progress = self.gs.flags.get("daily_quest_progress", {})
        claimed = self.gs.flags.get("daily_quest_claimed", {})
        for q in daily:
            qid = q["id"]
            done = claimed.get(qid, False)
            prog = progress.get(qid, 0)
            tgt = q["target"]
            status = "✓" if done else f"{prog}/{tgt}"
            color = "success" if done else "info"
            out += [
                {"t": color, "s": f"  [{status}] {q['title']}"},
                {"t": "dim",   "s": f"       {q['desc']}"},
                {"t": "dim",   "s": f"       Reward: +{q['xp']} XP · +{q['credits']} credits"},
            ]
            if not done and q.get("hint"):
                out.append({"t": "dim", "s": f"       Hint: {q['hint']}"})
            out.append({"t": "dim", "s": ""})

        out += [
            {"t": "system", "s": "  ── WEEKLY QUEST ──────────────────────────────────"},
            {"t": "system", "s": ""},
        ]
        wq = self.get_weekly_quest()
        if wq:
            wclaimed = self.gs.flags.get("weekly_quest_claimed", False)
            step_idx = self.gs.flags.get("weekly_quest_step", 0)
            steps = wq.get("steps", [])
            out += [
                {"t": "success" if wclaimed else "info", "s": f"  {'[✓]' if wclaimed else '[~]'} {wq['title']}"},
                {"t": "dim",   "s": f"       {wq['desc']}"},
                {"t": "dim",   "s": f"       Reward: +{wq['xp']} XP · +{wq['credits']} credits"},
                {"t": "dim",   "s": ""},
            ]
            for i, step in enumerate(steps):
                if wclaimed or i < step_idx:
                    mark = "✓"
                    col = "success"
                elif i == step_idx:
                    mark = "→"
                    col = "warn"
                else:
                    mark = "○"
                    col = "dim"
                out.append({"t": col, "s": f"       {mark} {step['label']}"})
        else:
            out.append({"t": "dim", "s": "  No weekly quest active."})

        # T9.2 — Procgen missions section
        procgen = self.gs.flags.get("procgen_quests", [])
        if procgen:
            out += [
                {"t": "system", "s": ""},
                {"t": "system", "s": "  ── GENERATED MISSIONS ────────────────────────────"},
                {"t": "system", "s": ""},
            ]
            _badges = {"recon": "🔍", "heist": "💀", "social": "🤝",
                       "puzzle": "🧩", "faction": "⚔", "story": "📖"}
            for q in procgen:
                badge = _badges.get(q.get("type", ""), "•")
                out += [
                    {"t": "info", "s": f"  {badge} [{q.get('type','?').upper()}] {q.get('title','?')}"},
                    {"t": "dim",  "s": f"       {q.get('objective', '')}"},
                    {"t": "dim",  "s": f"       → {q.get('command_hint', '')}  (+{q.get('xp_reward', 0)} XP)"},
                    {"t": "dim",  "s": ""},
                ]
            out.append({"t": "dim", "s": "  Use 'quests generate' to refresh missions."})

        out.append({"t": "system", "s": ""})
        return out
