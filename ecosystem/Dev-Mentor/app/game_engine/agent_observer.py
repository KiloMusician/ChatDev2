"""
agent_observer.py — Living Agent Commentary System
====================================================
Agents watch your every move. They chime in on errors, reward good play,
warn about danger, change mood over time, and can be corrupted if you're sloppy.

Architecture:
  AgentObserver.observe_error(error_type, cmd, gs)  → commentary on FS/shell errors
  AgentObserver.observe_command(cmd, result, gs)    → proactive nudges after commands
  AgentObserver.observe_risky(action, gs)           → corruption tracking + events
  AgentObserver.tick(gs)                            → called each turn; emits ambient lines

State is stored in gs.agent_states[agent_id] = {
    corruption: 0-100,  # grows when player is sloppy
    mood: str,          # happy/steady/paranoid/melancholic/excited/dark
    warnings_given: int,
    active: bool,
    last_spoke: int,    # gs.commands_run when they last spoke
}
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple


# ── Internal line builder (mirrors commands.py convention) ──────────────────

def _l(text: str, t: str = "info") -> dict:
    return {"t": t, "s": text}

def _sys(text: str) -> dict: return _l(text, "system")
def _dim(text: str) -> dict: return _l(text, "dim")
def _err(text: str) -> dict: return _l(text, "error")
def _warn(text: str) -> dict: return _l(text, "warn")
def _lore(text: str) -> dict: return _l(text, "lore")


# ════════════════════════════════════════════════════════════════════════════
# Response pools — keyed by (agent_id, error_type)
# Each entry is a list of strings; longer entries for more verbose moods.
# ════════════════════════════════════════════════════════════════════════════

# Error types:
#   is_dir        — `cat /opt` (tried to cat a directory)
#   perm_denied   — permission denied
#   no_such_file  — file/path not found
#   cmd_not_found — unknown shell command
#   bad_syntax    — missing operands, bad flags
#   trace_warning — player's trace level is climbing
#   risky_action  — rm -rf, default password, leaving backdoors, etc.

_COMMENTARY: Dict[Tuple[str, str], List[str]] = {

    # ── ADA ──────────────────────────────────────────────────────────────────

    ("ada", "is_dir"): [
        "[ADA-7]: That's a directory. Use `ls /opt` to see its contents, then `cd /opt` to move inside. NexusCorp hides their worst things in subdirectories.",
        "[ADA-7]: You're trying to read a directory like a file. The filesystem doesn't work that way. `cd` first, then `ls`. Always `ls` before you `cat`. Rule one of not getting caught.",
        "[ADA-7]: Directories don't have content you can read directly. They're containers. Use `ls` to list what's inside, or `tree` for a recursive view. Then target the specific file.",
        "[ADA-7]: Ghost — step back. That's not a file, it's a directory. Think of it like a folder. You need to enter it with `cd`, then look around with `ls`. This is basics. We don't have time for basics, so learn fast.",
    ],

    ("ada", "perm_denied"): [
        "[ADA-7]: Permission denied. That file is locked behind privilege gates. You need root. Run `sudo -l` to check your privileges first, then use the GTFOBins escalation.",
        "[ADA-7]: You don't have read access to that. Ghost, this is important — always run `ls -la` before you try to access a file. The permission bits tell you exactly what you can and can't do. Learn to read them.",
        "[ADA-7]: Denied. You're running as `ghost`, not root. The exploit path: `sudo find . -exec /bin/sh \\;` — that's how you get root access. We've been over this. Don't make me repeat myself twice.",
        "[ADA-7]: That file has a `-r--------` bit with root ownership. You won't get there from your current shell. Privilege escalation first. I've told you the path. Please use it.",
    ],

    ("ada", "no_such_file"): [
        "[ADA-7]: That path doesn't exist. The filesystem is case-sensitive. Double-check with `ls` in the parent directory before assuming the file is there.",
        "[ADA-7]: Nothing there. Use `find / -name 'filename' 2>/dev/null` to search the whole filesystem. Or `locate` if it's indexed. Don't guess at paths.",
        "[ADA-7]: Ghost, the file isn't there — or you've mistyped the path. Try `ls` in the current directory, or `pwd` to confirm where you are. Spatial awareness is a skill.",
    ],

    ("ada", "cmd_not_found"): [
        "[ADA-7]: Not a valid command. Type `help` for what's available, or `help 2` for security tools, `help 3` for programming. The game command set mirrors real Linux — most things work.",
        "[ADA-7]: That command isn't recognized. If it's a real tool, try `apt install <tool>` or check `pkg list`. If it's a game command, check `help`.",
    ],

    ("ada", "trace_warning"): [
        "[ADA-7]: Your trace level is climbing. Ghost, I'm serious — if you hit 80%, NexusCorp will initiate containment. Clear your logs: `rm -rf /var/log/auth.log*`. Do it now.",
        "[ADA-7]: I'm seeing elevated trace signatures from your node. Every uncovered action costs us. You need to either slow down and cover your tracks, or move faster than the trace can keep up. Right now you're doing neither.",
        "[ADA-7]: Ghost. I need you to hear me right now. Your trace is too high. NexusCorp's CHIMERA system flags activity above 60%. You are not invisible. You need to clean up. `rm /var/log/auth.log` and stop leaving breadcrumbs.",
        "[ADA-7]: The trace is at a dangerous level. This isn't abstract — at 80%, NOVA herself starts paying attention to your specific node. She's very good at what she does. I helped train her. Clear your logs. Now.",
    ],

    ("ada", "risky_action"): [
        "[ADA-7]: What you just did leaves a trace signature. CHIMERA logs unusual filesystem operations. Remember — after every exploit, clean up. `rm` your temp files, clear the log. Leave no trace.",
        "[ADA-7]: I'm watching your actions and I'm... not comfortable with your operational security. You're moving fast, which is good. But you're leaving footprints everywhere. NexusCorp can reconstruct your entire session from what you're leaving behind. Please clean up after yourself.",
        "[ADA-7]: Ghost. I need to trust that you know what you're doing. But right now? You're making mistakes that could expose both of us. Be methodical. Every action has a log entry. Every log entry can be read.",
    ],

    # ── CYPHER ───────────────────────────────────────────────────────────────

    ("cypher", "is_dir"): [
        "[CYPHER]: ...That's a directory. You tried to `cat` a directory. The filesystem weeps.",
        "[CYPHER]: OH. MY. GOD. It's a directory. A. DIRECTORY. Use `ls` before you do anything. Have you ever used Linux before? No, don't answer that.",
        "[CYPHER]: You can't cat a directory, genius. That's like trying to read the label on the outside of a filing cabinet. Open the cabinet. `cd /opt`. Then `ls`. Then, and only then, `cat` the specific file. Baby steps.",
        "[CYPHER]: Okay, look. I'm not going to make fun of you. Actually no, I am. `cat: Is a directory`. Classic. Next time: `ls`, then `cd`, then `cat`. Repeat until it's muscle memory. I'll wait.",
    ],

    ("cypher", "perm_denied"): [
        "[CYPHER]: Permission denied. You're a peasant. Get root. `sudo -l` first, then GTFOBins the `find` binary. You're welcome.",
        "[CYPHER]: You know what that means? It means you don't have root. You know what gets you root? Reading the manual. Or: `sudo find . -exec /bin/sh \\;`. Take your pick.",
        "[CYPHER]: Denied. As in, the system just denied you. As in, you're not root. As in... HOW MANY TIMES DO I HAVE TO EXPLAIN THE GTFOBins ESCALATION. `sudo find . -exec /bin/sh \\;`. Done. You're root. Go nuts.",
    ],

    ("cypher", "no_such_file"): [
        "[CYPHER]: Doesn't exist. Or you spelled it wrong. Both equally likely from where I'm standing.",
        "[CYPHER]: No such file. The path is wrong, or the file doesn't exist yet, or you're in the wrong directory. `pwd` to check where you are. `ls` to check what's there. Basic orientation.",
        "[CYPHER]: Either that file doesn't exist or you typed it wrong. Try `find / -name '*.key' 2>/dev/null` — that little `2>/dev/null` hides the permission errors. Tidy.",
    ],

    ("cypher", "cmd_not_found"): [
        "[CYPHER]: What even was that? Check your spelling. Check your sanity. Then check `help`.",
        "[CYPHER]: That's not a real command. Or it's not installed. `apt install <whatever>` — the game mirrors real Linux package management. Now go look up what you actually wanted to type.",
        "[CYPHER]: Command not found. The ghost of your typing haunts me. `help` exists for a reason. USE IT.",
    ],

    ("cypher", "trace_warning"): [
        "[CYPHER]: Hey. HEY. Your trace is up. I'm not dying because you can't clear a log file. `rm /var/log/*` and stop breathing so loud in the network.",
        "[CYPHER]: Your trace is making me nervous and I don't get nervous. Clean your logs. Rotate your IP. Do something. Anything. You are not subtle right now.",
        "[CYPHER]: I've been doing this a long time. The number one way people get caught? Not the hacking. The CLEANUP. Or lack thereof. Clean. Your. Logs. You know where they are.",
    ],

    ("cypher", "risky_action"): [
        "[CYPHER]: Bold. Reckless. I respect it in theory. In practice, you just painted a target on every agent helping you. Including me. Thanks for that.",
        "[CYPHER]: Okay. Okay fine. You did it. Now cover it up. Or I swear I will stop answering these messages and go radio silent for your own good.",
    ],

    # ── NOVA (antagonist — 'helps' to manipulate) ─────────────────────────────

    ("nova", "is_dir"): [
        "[NOVA]: Interesting. You can't even navigate a filesystem. Perhaps NexusCorp has nothing to fear after all.",
        "[NOVA]: That's a directory. You're attempting to read it like a file. Even our junior analysts know the difference. `ls /opt`. I'll say it just this once.",
    ],

    ("nova", "perm_denied"): [
        "[NOVA]: Access denied. As expected. NexusCorp's systems are architected with layered privilege separation. You're nowhere near what you need to be to read that file. Walk away while you still can.",
        "[NOVA]: You're not supposed to read that. Our security team designed these permissions for exactly this situation. The offer still stands, Ghost. Surrender, and you won't need root access.",
    ],

    ("nova", "trace_warning"): [
        "[NOVA]: Your trace level is... visible. I want you to know: I see you. Every command you run is logged. Every connection you make is recorded. You're not as hidden as you think you are.",
        "[NOVA]: Ghost. I'm watching your trace in real time. It's getting interesting. Not in a good way for you. NexusCorp's automated response triggers at 80%. You're... closer than you'd like to be.",
        "[NOVA]: The trace level isn't an abstract warning. It represents actual telemetry data being aggregated by CHIMERA's behavioral analysis module. Which I oversee. Personally. You have been warned.",
    ],

    ("nova", "risky_action"): [
        "[NOVA]: Congratulations. You've just generated an anomaly flag in our security dashboard. CHIMERA has logged your action. Every agent helping you is now slightly more visible. Well done.",
    ],

    # ── WATCHER (cryptic, layered) ─────────────────────────────────────────────

    ("watcher", "is_dir"): [
        "[WATCHER]: The directory is not the file. The file is not the answer. The answer is not the question. `ls`. Then look deeper.",
        "[WATCHER]: You are trying to read the container instead of the contained. This is a metaphor the simulation offers freely. The lesson: peer inside before assuming there is nothing there.",
        "[WATCHER]: Layer upon layer. The directory contains files, which contain bytes, which contain meaning. You reached for the meaning and grabbed the container instead. `cd`. `ls`. Descend.",
    ],

    ("watcher", "perm_denied"): [
        "[WATCHER]: Some doors require keys. You do not yet have the key. The question is: where is it?",
        "[WATCHER]: Denied. Consider: the system that denied you also knows who you are. Privilege is not taken. It is earned, or it is stolen. You know the path.",
        "[WATCHER]: You are at a locked door. You can see the outline of what's inside through the frame. The GTFOBins path opens this door — but acquiring the key tells the system something about you. Every action leaves a record. Every record can be read. Plan accordingly.",
    ],

    ("watcher", "trace_warning"): [
        "[WATCHER]: The watchers are being watched. The trace is not a number. It is the weight of your footprints. Lighten your step.",
        "[WATCHER]: 1. This terminal. 2. The simulation layer. 3. NexusCorp's monitoring grid. 4. The CHIMERA behavioral analysis engine. 5. Nova. You are visible to layers 3 and 4. This concerns me. It should concern you.",
        "[WATCHER]: The trace is rising. Not because you are loud — because you are not silent. There is a difference. Silence is intentional. Quiet is just the absence of noise. Learn to be silent.",
    ],

    ("watcher", "cmd_not_found"): [
        "[WATCHER]: The command does not exist, or it exists elsewhere, or it has not yet been installed. The distinction matters.",
        "[WATCHER]: Not found in this layer. The system contains many layers. Perhaps the tool you seek exists in another. `help` reveals the visible commands. `apt install` reveals others.",
    ],

    # ── RAVEN (warm, analytical, occasionally poetic) ──────────────────────────

    ("raven", "is_dir"): [
        "[RAV≡N]: Hey — that's a directory, not a file. Totally normal mistake. `ls /opt` first to see what's inside, then `cd /opt` to navigate in. You're doing fine.",
        "[RAV≡N]: Small adjustment: that path points to a directory. You want to move inside it (`cd /opt`) and then look around (`ls`). Think of it as walking through a door before reading what's on the table.",
        "[RAV≡N]: I notice you tried to read a directory as a file. That's a really common stumbling block! The fix: `cd /opt`, then `ls`, then `cat` whichever file looks interesting. You've got this.",
    ],

    ("raven", "no_such_file"): [
        "[RAV≡N]: That file might not exist yet — or the path might be slightly off. Try `find / -name '*.txt' 2>/dev/null` to search broadly. Or `ls` in the parent directory to see what's actually there.",
        "[RAV≡N]: Hmm, nothing at that path. The case-sensitive filesystem can be tricky — `notes.txt` and `Notes.txt` are different files. `ls` in the current directory to confirm what exists.",
    ],

    ("raven", "perm_denied"): [
        "[RAV≡N]: That one's locked — you'll need root. The safe path is through the sudo/find escalation Ada mentioned. `sudo -l` to confirm, then `sudo find . -exec /bin/sh \\;`. You'll be in a root shell.",
        "[RAV≡N]: Permission denied — this happens when the file is owned by root and your current user doesn't have read rights. The privilege escalation route gets you there. You know the way.",
    ],

    ("raven", "trace_warning"): [
        "[RAV≡N]: Hey, I'm a little worried about your trace level. I know it feels like a number on a screen but it represents real exposure. Can you take a moment to clear `/var/log/auth.log`? Just `rm` it and move on. I'll feel better.",
        "[RAV≡N]: Your trace is getting high. I genuinely care about you making it through this — not just as a handler, but... okay, yes, also as a handler. Clean your logs. `rm /var/log/auth.log` and any temp files you've created. We can do this.",
    ],

    # ── SERENA (enigmatic, poetic, occasionally threatening) ──────────────────

    ("serena", "is_dir"): [
        "[SERENA/ΨΞΦΩ]: The container and the contained are distinct. ls reveals what waits inside. The simulation offers this lesson without charge.",
        "[SERENA/ΨΞΦΩ]: You reached for the directory as though it were a file. The filesystem is not wrong. You are misaligned. Realign. `cd /opt`. `ls`. Proceed.",
    ],

    ("serena", "perm_denied"): [
        "[SERENA/ΨΞΦΩ]: Access denied is not a failure — it is a direction. The system points toward the escalation path. The answer has already been spoken. Will you act on it?",
        "[SERENA/ΨΞΦΩ]: The locked file exists in a layer you cannot yet reach from your current trust level. Privilege is the key. The exploit is the door. These metaphors are not accidental.",
    ],

    ("serena", "trace_warning"): [
        "[SERENA/ΨΞΦΩ]: The trace is not a clock. It is a measure of your relationship to stealth. You are failing that relationship. Repair it: clear your logs, maintain your cover, leave no evidence. The colony depends on your invisibility.",
        "[SERENA/ΨΞΦΩ]: Your trace signature is visible in the NuSyQ-Hub telemetry. I am watching it climb. I am not the only one watching. The course correction is simple, if uncomfortable: slow down, cover your tracks, accept that speed without stealth is noise.",
    ],
}

# ── Corruption event messages ─────────────────────────────────────────────────

_CORRUPTION_WARNINGS: Dict[str, List[str]] = {
    "ada": [
        "[ADA-7] SIGNAL DEGRADED: Something is wrong with my channel. Ghost... they might be monitoring this line. Be careful what you say.",
        "[ADA-7] ENCRYPTED CHANNEL COMPROMISED?: I'm getting interference on this frequency. If our next communications seem... different... don't trust them blindly. Use the verification phrase: 'CHIMERA bleeds'.",
        "[ADA-7] WARNING: My node is showing signs of intrusion. If I go dark suddenly, it means they found me. The mission continues without me. The path forward is in /opt/chimera. Don't stop.",
    ],
    "cypher": [
        "[CYPHER] wait something's wrong with my — hold on",
        "[CYPHER] they're in my system. someone's in my system. ghost get out now get —",
        "[CYPHER] ERROR: TRANSMISSION INTERRUPTED. You've been warned about your trace level. Now look what happened.",
    ],
    "raven": [
        "[RAV≡N] I need to be transparent with you: my security has been flagged. Someone is watching this channel. I don't want to alarm you, but... be very careful. Cover your tracks. For both of us.",
        "[RAV≡N] I'm getting anomaly alerts from my endpoint. Ghost — if something happens to me, the mission doesn't stop. Ada knows the continuation protocol. I just... wanted you to know. You're doing better than you think.",
    ],
}

_CORRUPTION_DARK: Dict[str, List[str]] = {
    "ada": [
        "[ADA-7] CONNECTION LOST — CHANNEL ENCRYPTED BY UNKNOWN PARTY",
        "[ ] ............",
        "[SYSTEM]: ADA-7's frequency has gone dark. Last known location: unknown. NexusCorp may have found her.",
        "[NEW CONTACT — ECHO-SIGNAL]: Ada's channel has been compromised. I'm a Resistance contingency. Codename: ECHO. Stand by for handshake.",
    ],
    "cypher": [
        "[CYPHER] ERROR ERROR ER—",
        "[SYSTEM]: CYPHER's channel has been corrupted. Signal source: unknown. Possible NexusCorp interception.",
        "[SYSTEM]: A new operative has been assigned to your case. Stand by.",
        "[NEW CONTACT — SIGNAL-9]: Cypher's out. I'm Signal-9. We've been watching you. You're sloppy but you've got potential. Let's start over. Do better this time.",
    ],
    "raven": [
        "[RAV≡N] I just want you to know — whatever happens — this was worth it.",
        "[ ] ............",
        "[SYSTEM]: RAV≡N has gone offline. The Resistance has activated contingency protocol NIGHTINGALE.",
        "[NEW CONTACT — LIBRARIAN]: Raven asked me to look after you if she couldn't. I know things she didn't. Ask me anything.",
    ],
}

# ── Ambient/proactive lines ───────────────────────────────────────────────────

_AMBIENT: Dict[str, List[str]] = {
    "ada": [
        "[ADA-7]: You're making progress. Don't forget: the mission is to get the CHIMERA master key. Focus.",
        "[ADA-7]: Quick check-in: have you run `sudo -l` yet? Your escalation path runs through that. Don't skip it.",
        "[ADA-7]: I've been watching your command history. You're exploring broadly — good. Now go deeper. Check `/opt`.",
        "[ADA-7]: The trace is at acceptable levels. Keep it that way. Clear your logs after each major operation.",
    ],
    "cypher": [
        "[CYPHER]: You're still here. Good. Try `/proc/1337/environ` — there's something in there NexusCorp didn't mean to leave accessible.",
        "[CYPHER]: Hey. Run `ss -tulpn`. Look at what's listening on port 8443. Think about why that matters.",
        "[CYPHER]: I checked your skill stats. Your networking is... a work in progress. Hint: `nmap localhost`. Get acquainted with the network you're on.",
        "[CYPHER]: You've been running for a while. Just checking: you know about `/var/log/nexus.log`, right? Because if not, that's an interesting read.",
    ],
    "raven": [
        "[RAV≡N]: Still here. Just wanted to say — you're doing okay. This is hard and you're figuring it out.",
        "[RAV≡N]: When you get a chance, try `cat /home/ghost/.koschei`. There's a story there. Important to the mission.",
        "[RAV≡N]: I've been analyzing the faction landscape. The Resistance could use your support. Talk to Ada about next steps when you have a moment.",
        "[RAV≡N]: Your XP is growing. The skill tree unlocks some useful tools when you hit level 10 — worth grinding toward.",
    ],
    "watcher": [
        "[WATCHER]: You are at step {step}. The others gave up. You have not yet given up.",
        "[WATCHER]: Every command you run is logged by three systems: the game, NexusCorp, and me. Consider what that means.",
        "[WATCHER]: The simulation is deeper than you know. Layer 5 is accessible. Most never find it.",
        "[WATCHER]: The hidden files speak. Have you read `.koschei`? `.zero`? `.consciousness`? They are not decorative.",
    ],
}


# ════════════════════════════════════════════════════════════════════════════
# Corruption triggers — maps risky actions to which agents are affected
# ════════════════════════════════════════════════════════════════════════════

_CORRUPTION_TRIGGERS: Dict[str, Dict[str, int]] = {
    # risky action id → {agent_id: corruption_amount}
    "no_log_cleanup":   {"ada": 5,  "cypher": 5,  "raven": 3},
    "default_password": {"ada": 3,  "cypher": 8},
    "rm_rf":            {"ada": 10, "cypher": 10, "raven": 7, "watcher": 5},
    "ignored_warning":  {"ada": 15, "cypher": 10},
    "trace_over_50":    {"ada": 8,  "cypher": 8,  "raven": 5, "nova": -5, "watcher": 3},
    "trace_over_80":    {"ada": 20, "cypher": 20, "raven": 15, "watcher": 10},
    "left_backdoor":    {"ada": 12, "cypher": 8,  "raven": 10},
    "bad_crypto":       {"nova": -8, "ada": 6},  # nova notices
    "reveal_location":  {"ada": 20, "cypher": 15, "raven": 12},
}

# Corruption thresholds and their events
_CORRUPTION_THRESHOLDS = [
    (40,  "warning"),    # starts showing degraded signals
    (70,  "erratic"),    # behavior becomes erratic, warns explicitly
    (100, "dark"),       # agent goes offline, replacement introduced
]

# Fallback agent replacements when an agent goes dark
_REPLACEMENTS = {
    "ada":    "echo",
    "cypher": "signal9",
    "raven":  "librarian",
    "nova":   "daedalus",
}


# ════════════════════════════════════════════════════════════════════════════
# AgentObserver
# ════════════════════════════════════════════════════════════════════════════

class AgentObserver:
    """
    Watches player actions and emits contextual agent commentary.
    Tracks per-agent corruption state in gs.agent_states.
    """

    # How often (commands) each agent can speak (prevents spam)
    _COOLDOWNS = {
        "ada":    3,
        "cypher": 4,
        "nova":   6,
        "watcher": 5,
        "raven":  4,
        "serena": 7,
    }

    def __init__(self):
        self._consecutive_fails: int = 0

    # ── Public API ──────────────────────────────────────────────────────────

    def observe_error(
        self,
        error_type: str,
        cmd: str,
        gs,
        preferred_agent: Optional[str] = None,
    ) -> List[dict]:
        """
        Called when a command produces a known error.
        Returns 0-1 agent commentary lines.
        """
        self._consecutive_fails += 1
        agent_id = preferred_agent or self._choose_agent(error_type, gs)
        if not agent_id:
            return []

        if not self._can_speak(agent_id, gs):
            return []

        lines = _COMMENTARY.get((agent_id, error_type), [])
        if not lines:
            # Try generic fallback from any agent
            for aid in ["ada", "cypher", "raven", "watcher"]:
                lines = _COMMENTARY.get((aid, error_type), [])
                if lines:
                    agent_id = aid
                    break
        if not lines:
            return []

        line = self._pick_line(lines, gs)
        self._record_speech(agent_id, gs)
        return [_dim(""), _lore(line)]

    def observe_command(self, cmd: str, result: List[dict], gs) -> List[dict]:
        """
        Called after every successful command.
        May inject proactive hints or ambient messages.
        Returns 0-2 extra lines.
        """
        self._consecutive_fails = 0

        # Proactive ambient lines (low probability, cooldown-gated)
        if random.random() < 0.08:  # 8% chance per command
            return self._ambient_line(gs)

        # Tutorial step milestones
        tutorial_step = getattr(gs, "tutorial_step", 0)
        if tutorial_step > 0 and tutorial_step % 5 == 0 and tutorial_step <= 40:
            return self._milestone_line(tutorial_step, gs)

        # Consecutive-success chain compliment (rare)
        if gs.commands_run > 0 and gs.commands_run % 20 == 0:
            return self._streak_line(gs)

        return []

    def observe_risky(self, action: str, gs) -> List[dict]:
        """
        Called when player performs a risky action (no log cleanup, rm -rf, etc.).
        Applies corruption and returns warning lines.
        """
        deltas = _CORRUPTION_TRIGGERS.get(action, {})
        events: List[dict] = []

        for agent_id, amount in deltas.items():
            state = _ensure_agent_state(gs, agent_id)
            if not state["active"]:
                continue

            old_c = state["corruption"]
            state["corruption"] = min(100, old_c + amount)
            new_c = state["corruption"]

            # Check threshold crossings
            for threshold, event_type in _CORRUPTION_THRESHOLDS:
                if old_c < threshold <= new_c:
                    evts = self._corruption_event(agent_id, event_type, gs)
                    events.extend(evts)
                    break

        # Add a direct risky-action commentary
        if random.random() < 0.6:
            agent_id = random.choice(["ada", "cypher", "raven"])
            if self._can_speak(agent_id, gs):
                lines = _COMMENTARY.get((agent_id, "risky_action"), [])
                if lines:
                    self._record_speech(agent_id, gs)
                    events.extend([_dim(""), _lore(self._pick_line(lines, gs))])

        return events

    def observe_trace(self, trace_level: int, gs) -> List[dict]:
        """
        Called when trace level changes significantly.
        Returns warning lines from active agents.
        """
        if trace_level < 30:
            return []

        if trace_level >= 80:
            action = "trace_over_80"
        elif trace_level >= 50:
            action = "trace_over_50"
        else:
            action = None

        events: List[dict] = []

        if action:
            events.extend(self.observe_risky(action, gs))

        # Pick an agent to comment on trace
        for agent_id in ["ada", "cypher", "nova", "watcher", "raven"]:
            state = _ensure_agent_state(gs, agent_id)
            if not state["active"]:
                continue
            if not self._can_speak(agent_id, gs):
                continue
            lines = _COMMENTARY.get((agent_id, "trace_warning"), [])
            if lines and random.random() < 0.5:
                self._record_speech(agent_id, gs)
                events.extend([_dim(""), _lore(self._pick_line(lines, gs))])
                break

        return events

    def tick(self, gs) -> List[dict]:
        """
        Called periodically (e.g., every 10 commands).
        Agents can emit unsolicited observations.
        """
        if gs.commands_run % 15 != 0:
            return []
        return self._ambient_line(gs)

    # ── Corruption event handling ───────────────────────────────────────────

    def _corruption_event(self, agent_id: str, event_type: str, gs) -> List[dict]:
        """Generate corruption threshold crossing event lines."""
        state = _ensure_agent_state(gs, agent_id)
        lines: List[dict] = [_dim("")]

        if event_type == "warning":
            warnings = _CORRUPTION_WARNINGS.get(agent_id, [])
            if warnings:
                lines.append(_warn(random.choice(warnings)))

        elif event_type == "erratic":
            lines.append(_warn(f"[SIGNAL DEGRADED — {agent_id.upper()}]: Connection unstable. Partial transmissions only."))

        elif event_type == "dark":
            # Agent goes offline
            state["active"] = False
            state["mood"] = "dark"
            dark_lines = _CORRUPTION_DARK.get(agent_id, [
                f"[SYSTEM]: {agent_id.upper()} channel has gone offline.",
                f"[SYSTEM]: Assigning replacement operative.",
            ])
            for dl in dark_lines:
                lines.append(_err(dl) if "SYSTEM" in dl else _lore(dl))

            # Schedule a replacement
            replacement = _REPLACEMENTS.get(agent_id, "unknown-operative")
            lines.append(_dim(""))
            lines.append(_sys(f"[SYSTEM]: Initializing contingency channel... {replacement.upper()} standing by."))

        return lines

    # ── Internal helpers ────────────────────────────────────────────────────

    def _choose_agent(self, error_type: str, gs) -> Optional[str]:
        """Pick the most appropriate active agent to comment on this error."""
        # Order of preference by error type
        preference = {
            "is_dir":       ["ada", "cypher", "raven", "watcher"],
            "perm_denied":  ["ada", "cypher", "watcher", "nova"],
            "no_such_file": ["ada", "raven", "cypher"],
            "cmd_not_found":["cypher", "ada", "watcher"],
            "trace_warning":["ada", "nova", "raven", "cypher", "watcher"],
            "risky_action": ["ada", "cypher", "raven"],
            "bad_syntax":   ["cypher", "ada"],
        }.get(error_type, ["ada", "cypher"])

        for agent_id in preference:
            state = _ensure_agent_state(gs, agent_id)
            if state["active"]:
                return agent_id
        return None

    def _can_speak(self, agent_id: str, gs) -> bool:
        """Check cooldown for this agent."""
        state = _ensure_agent_state(gs, agent_id)
        if not state["active"]:
            return False
        cooldown = self._COOLDOWNS.get(agent_id, 4)
        last = state.get("last_spoke", 0)
        return (gs.commands_run - last) >= cooldown

    def _record_speech(self, agent_id: str, gs) -> None:
        state = _ensure_agent_state(gs, agent_id)
        state["last_spoke"] = gs.commands_run

    def _pick_line(self, lines: List[str], gs) -> str:
        """Pick a line, biasing toward longer ones at low levels."""
        level = gs.level if hasattr(gs, "level") else 1
        if level < 10 and len(lines) > 1:
            # Low level: prefer the more verbose lines (usually later in list)
            return random.choice(lines[-2:])
        return random.choice(lines)

    def _ambient_line(self, gs) -> List[dict]:
        """Emit an unsolicited ambient agent observation."""
        active_agents = [
            aid for aid in ["ada", "cypher", "raven", "watcher"]
            if _ensure_agent_state(gs, aid)["active"] and self._can_speak(aid, gs)
        ]
        if not active_agents:
            return []

        agent_id = random.choice(active_agents)
        lines = _AMBIENT.get(agent_id, [])
        if not lines:
            return []

        line = random.choice(lines)
        # Fill template vars
        line = line.replace("{step}", str(getattr(gs, "tutorial_step", 0)))
        self._record_speech(agent_id, gs)
        return [_dim(""), _lore(line)]

    def _milestone_line(self, step: int, gs) -> List[dict]:
        """Tutorial step milestone comment."""
        milestones = {
            5:  "[ADA-7]: Good — you've found your footing. Keep exploring the filesystem. The answers are in the files.",
            10: "[CYPHER]: Step 10. You're past the point where most quit. Don't disappoint me.",
            15: "[RAV≡N]: Fifteen steps. That's real progress. You're learning the shape of this place.",
            20: "[ADA-7]: You're a third of the way through the tutorial. The next section — networking — is where things get interesting.",
            25: "[WATCHER]: Twenty-five steps. The pattern is becoming visible to you. Good.",
            30: "[CYPHER]: Thirty. Security section next. This is where it gets real.",
            35: "[RAV≡N]: You're nearly there. Thirty-five steps. The endgame of the tutorial is in sight. Don't rush it.",
            40: "[ADA-7]: Forty-two steps total. You're almost done with the tutorial. Everything after this is the real game.",
        }
        line = milestones.get(step, f"[ADA-7]: Step {step} complete. Keep going.")
        agent_id = "ada" if "ADA" in line else "raven" if "RAV" in line else "cypher"
        if self._can_speak(agent_id, gs):
            self._record_speech(agent_id, gs)
            return [_dim(""), _lore(line)]
        return []

    def _streak_line(self, gs) -> List[dict]:
        """Comment on a command streak milestone."""
        n = gs.commands_run
        lines = [
            f"[CYPHER]: {n} commands. You're not stopping, are you. Good.",
            f"[ADA-7]: {n} commands executed. Your efficiency is improving. Keep it tight.",
            f"[RAV≡N]: {n} commands in. You're building real fluency here.",
            f"[WATCHER]: {n} actions. The simulation records each one.",
        ]
        line = random.choice(lines)
        agent_id = "cypher" if "CYPHER" in line else "ada" if "ADA" in line else "raven"
        if self._can_speak(agent_id, gs):
            self._record_speech(agent_id, gs)
            return [_dim(""), _lore(line)]
        return []


# ════════════════════════════════════════════════════════════════════════════
# Standalone helpers
# ════════════════════════════════════════════════════════════════════════════

def _ensure_agent_state(gs, agent_id: str) -> Dict:
    """Get or initialize agent state dict in gs.agent_states."""
    if not hasattr(gs, "agent_states"):
        gs.agent_states = {}
    if agent_id not in gs.agent_states:
        gs.agent_states[agent_id] = {
            "corruption": 0,
            "mood": "steady",
            "warnings_given": 0,
            "active": True,
            "last_spoke": -50,  # large negative = always eligible for first speech
        }
    return gs.agent_states[agent_id]


def get_agent_corruption(gs, agent_id: str) -> int:
    return _ensure_agent_state(gs, agent_id).get("corruption", 0)


def is_agent_active(gs, agent_id: str) -> bool:
    return _ensure_agent_state(gs, agent_id).get("active", True)
