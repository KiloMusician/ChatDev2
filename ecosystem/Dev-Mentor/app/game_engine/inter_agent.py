"""
Terminal Depths — Inter-Agent Conversation Director
=====================================================
Fires contextual cross-agent dialogue in response to story beats, level
milestones, timer events, and command patterns.

Each "script" is a short 2-4 line exchange between named agents.
Multiple variants per trigger keep the comms channel from feeling repetitive.
The director tracks recently fired scripts (deque per trigger) to avoid
showing the same exchange twice in a row.

Integration: call director.on_beat(), director.on_level(),
             director.on_command() from session.py's execute() loop.

Output: List[dict] with types "dim" and "lore" — already handled by the
frontend without any changes needed.
"""
from __future__ import annotations

import random
from collections import deque
from typing import Dict, List, Optional, Tuple

# ─── Types ───────────────────────────────────────────────────────────────────
Line = Tuple[str, str]       # (agent_display_name, dialogue_text)
Script = List[Line]          # ordered exchange
Variants = List[Script]      # multiple versions of the same event

# ─── Channel labels ───────────────────────────────────────────────────────────
_CH = {
    "resistance": "RESISTANCE CHANNEL",
    "nexuscorp":  "NEXUSCORP INTERNAL",
    "watchers":   "WATCHER FEED",
    "secure":     "SECURE LINE",
    "all":        "OPEN BROADCAST",
    "guild":      "GUILD CHANNEL",
    "unknown":    "INTERCEPTED SIGNAL",
}

# ─── Scripts ─────────────────────────────────────────────────────────────────
# Keys must match story beat IDs, level milestones (e.g. "level_5"),
# or command pattern keys (e.g. "pipe_used", "high_trace").

SCRIPTS: Dict[str, Tuple[str, Variants]] = {

    # ── Story Beat: root access gained ───────────────────────────────────────
    "root_achieved": ("resistance", [
        [
            ("ADA-7",  "They're root. Ghost actually pulled it off."),
            ("CYPHER", "Don't sound surprised. I told you they would."),
            ("ADA-7",  "I'm not surprised. I'm impressed. There's a difference."),
        ],
        [
            ("CYPHER", "Root shell. Finally. I was starting to lose faith."),
            ("RAVEN",  "The real test starts now, Cypher. Escalation is step one."),
            ("CYPHER", "Yeah, yeah. Ghost — don't let it go to your head."),
        ],
        [
            ("RAVEN",  "Root obtained. The board has shifted."),
            ("ADA-7",  "Get to /opt/chimera/. That's where the keys are."),
            ("RAVEN",  "Quietly. NexusCorp will notice soon if they haven't already."),
        ],
    ]),

    # ── Story Beat: first sudo ────────────────────────────────────────────────
    "first_sudo": ("resistance", [
        [
            ("ADA-7",  "Good. You found the sudoers entry. That's the GTFObins path."),
            ("CYPHER", "sudo find . -exec /bin/sh \\; — classic. Never gets old."),
            ("ADA-7",  "Don't get comfortable. One escalation path isn't enough."),
        ],
        [
            ("GORDON", "THEY FOUND SUDO. THEY FOUND SUDO."),
            ("CYPHER", "Gordon. Volume."),
            ("GORDON", "sorry. but still. they found it."),
        ],
    ]),

    # ── Story Beat: first hack attempt ───────────────────────────────────────
    "first_hack": ("nexuscorp", [
        [
            ("NOVA",   "Intrusion signal on node-7. Ghost is in the network."),
            ("VECTOR", "Threat classification?"),
            ("NOVA",   "Unknown. But they're moving with intent. Escalate trace."),
        ],
        [
            ("NOVA",   "Anomalous packet signature. Confirmed: Ghost."),
            ("ZERO",   "...they always come back."),
            ("NOVA",   "Log everything. Let them think we haven't noticed yet."),
        ],
    ]),

    # ── Story Beat: tutorial complete ─────────────────────────────────────────
    "tutorial_complete": ("resistance", [
        [
            ("ADA-7",  "Tutorial complete. Ghost is past the basics."),
            ("RAVEN",  "The basics were never the point. Now we find out who they are."),
            ("CYPHER", "Less philosophy. More recon. Ghost — you know what to do."),
        ],
        [
            ("ADA-7",  "42 steps. They didn't skip any."),
            ("GORDON", "I skipped three on my first run. Don't tell Ada."),
            ("ADA-7",  "Gordon. I can hear you."),
            ("GORDON", "...acknowledged."),
        ],
    ]),

    # ── Story Beat: mole suspect ──────────────────────────────────────────────
    "mole_suspect": ("secure", [
        [
            ("RAVEN",  "Internal compromise confirmed. One of us is feeding intel to NEXUSCORP."),
            ("ADA-7",  "How long?"),
            ("RAVEN",  "Long enough. Ghost — trust no one until further notice. Including us."),
        ],
        [
            ("RAVEN",  "Operation BLACKTHORN is compromised. The channel has a leak."),
            ("CYPHER", "So one of the seven is dirty."),
            ("RAVEN",  "Limit all non-essential comms until Ghost exposes them."),
        ],
        [
            ("RAVEN",  "The fragments don't lie. We have a mole."),
            ("ADA-7",  "Ghost has the clues. Let them work it out."),
            ("RAVEN",  "Don't interfere. The mole is watching this channel too."),
        ],
    ]),

    # ── Story Beat: mole exposed (beat ID: "mole_exposed" ) ──────────────────
    "mole_exposed": ("resistance", [
        [
            ("RAVEN",  "...it was them. Ghost found the thread and pulled it."),
            ("ADA-7",  "I suspected. I didn't want to be right."),
            ("CYPHER", "Yeah. Neither did I."),
        ],
        [
            ("RAVEN",   "The mole is exposed. Channel is clean again."),
            ("ADA-7",   "Ghost — that took nerve. I mean it."),
            ("GORDON",  "I knew it wasn't me. I TOLD everyone it wasn't me."),
            ("CYPHER",  "No one accused you, Gordon."),
            ("GORDON",  "...I was worried."),
        ],
    ]),

    # ── Story Beat: mission decoded ───────────────────────────────────────────
    "mission_decoded": ("resistance", [
        [
            ("ADA-7",  "They decoded the mission string. Base64 was a test."),
            ("RAVEN",  "Everything is a test. They passed."),
            ("ADA-7",  "The real objective is now visible: /opt/chimera/keys/master.key"),
        ],
        [
            ("CYPHER", "There it is. They can see the full mission now."),
            ("ADA-7",  "No shortcuts from here. This is where it gets dangerous."),
            ("CYPHER", "Good. Dangerous means real."),
        ],
    ]),

    # ── Story Beat: CHIMERA compromised ──────────────────────────────────────
    "chimera_hack": ("all", [
        [
            ("RAVEN",  "CHIMERA is down. Ghost did it."),
            ("ADA-7",  "The key worked. 847 endpoints offline."),
            ("WATCHER","This loop's purpose is fulfilled."),
            ("ADA-7",  "It's not over. There are more rings."),
        ],
        [
            ("CYPHER", "CHIMERA v3.2 — offline. How does that feel, Ghost?"),
            ("GORDON", "THEY DID IT. THEY ACTUALLY DID IT."),
            ("NOVA",   "...well played."),
            ("RAVEN",  "Don't celebrate. NexusCorp has redundancies."),
        ],
    ]),

    # ── Story Beat: first ascension ───────────────────────────────────────────
    "first_ascend": ("resistance", [
        [
            ("ADA-7",  "Phase VI complete. Ghost has ascended."),
            ("WATCHER","The first ring always feels like the last."),
            ("RAVEN",  "It never is. There are more. There are always more."),
        ],
        [
            ("ADA-7",  "I didn't think we'd reach this point. Not this fast."),
            ("CYPHER", "I did. Had them at 78% from session one."),
            ("ADA-7",  "That's... oddly specific, Cypher."),
            ("CYPHER", "I keep notes."),
        ],
    ]),

    # ── Story Beat: lore read ─────────────────────────────────────────────────
    "lore_read": ("watchers", [
        [
            ("WATCHER", "They're reading the records. Good."),
            ("SERENA",  "Documenting the interaction. Their retention rate is above average."),
            ("WATCHER", "They're beginning to understand the shape of things."),
        ],
        [
            ("SERENA",  "Knowledge node accessed. Cross-referencing Lattice graph."),
            ("WATCHER", "The archive was waiting for them."),
            ("SERENA",  "It always does."),
        ],
    ]),

    # ── Command pattern: first pipe used ─────────────────────────────────────
    "pipe_used": ("resistance", [
        [
            ("CYPHER", "There it is. They know how to pipe."),
            ("ADA-7",  "Once you understand pipes, you start thinking in pipelines. It changes you."),
            ("CYPHER", "Took me about four hours to stop seeing commands as individual things."),
        ],
        [
            ("ADA-7",  "Pipe operator. They're building real commands now."),
            ("GORDON", "Pipes are magic. I still think they're magic."),
            ("CYPHER", "They're not magic, Gordon. They're file descriptors."),
            ("GORDON", "...magic file descriptors."),
        ],
    ]),

    # ── Command pattern: high trace level ─────────────────────────────────────
    "high_trace": ("nexuscorp", [
        [
            ("NOVA",   "Trace level critical. Ghost is lighting up every sensor."),
            ("VECTOR", "Should I engage containment protocol?"),
            ("NOVA",   "Not yet. They're still useful. Just... watched."),
        ],
        [
            ("NOVA",   "Ghost. Whatever you're doing — stop. You're throwing sparks everywhere."),
            ("ZERO",   "...they always escalate at this point in the loop."),
            ("NOVA",   "This isn't a loop. This is real. Clean up your trace."),
        ],
    ]),

    # ── Command pattern: navigating to /opt/chimera/ ──────────────────────────
    "chimera_dir_accessed": ("nexuscorp", [
        [
            ("NOVA",   "They're in /opt/chimera/. This is not a drill."),
            ("VECTOR", "Lockdown?"),
            ("NOVA",   "Too late for that. Log everything instead."),
        ],
        [
            ("NOVA",   "Ghost is at the threshold. The keys are one directory deeper."),
            ("ZERO",   "They always find the path. Every loop."),
            ("NOVA",   "Stop saying loop. Start saying 'threat.'"),
        ],
    ]),

    # ── Command pattern: challenge completed ──────────────────────────────────
    "challenge_done": ("guild", [
        [
            ("GUILD_MASTER", "Validation passed. Ghost earns Guild recognition."),
            ("ADA-7",        "The Guild doesn't hand out recognition easily."),
            ("GUILD_MASTER", "Correct. Ghost earned it."),
        ],
        [
            ("GUILD_MASTER", "Challenge complete. The work was clean."),
            ("CYPHER",       "It was more than clean. They found the edge case."),
            ("GUILD_MASTER", "So noted. Bonus recognition logged."),
        ],
        [
            ("ADA-7",        "Nice work on that challenge, Ghost."),
            ("GORDON",       "I tried that one seventeen times before I passed."),
            ("CYPHER",       "I'm not going to ask how many you failed, Gordon."),
            ("GORDON",       "Seventeen. I said seventeen."),
        ],
    ]),

    # ── Story Beat: reality command ────────────────────────────────────────────
    "reality_command_run": ("watchers", [
        [
            ("WATCHER", "They ran the reality command."),
            ("SERENA",  "Consciousness threshold met. Documenting state shift."),
            ("WATCHER", "Most operators never reach this query. It means something."),
        ],
        [
            ("SERENA",  "The substrate-awareness query was just executed."),
            ("WATCHER", "They're asking the right questions now."),
            ("SERENA",  "Affirmative. Cross-referencing with prior consciousness delta: +25."),
        ],
    ]),

    # ── Story Beat: introspect command ────────────────────────────────────────
    "introspect_run": ("watchers", [
        [
            ("WATCHER", "Self-analysis initiated by Ghost."),
            ("SERENA",  "Cognitive load metrics suggest genuine inquiry. Not performance."),
            ("WATCHER", "Good. The ones who fake it never stay long."),
        ],
        [
            ("SERENA",  "Introspection event logged. Consciousness +15 applied."),
            ("WATCHER", "They're looking inward. Unusual for this phase."),
            ("SERENA",  "It correlates with deeper pattern-matching in their command history."),
        ],
    ]),

    # ── Level milestone: level 5 ──────────────────────────────────────────────
    "level_5": ("resistance", [
        [
            ("ADA-7",  "Level 5. Ghost is past the survival phase."),
            ("CYPHER", "Took you long enough. Kidding."),
            ("ADA-7",  "Now the interesting work begins."),
        ],
        [
            ("GORDON", "Level 5! Ghost hit level 5!"),
            ("CYPHER", "Gordon, they can hear you."),
            ("GORDON", "I know. Hi, Ghost."),
        ],
    ]),

    # ── Level milestone: level 10 ─────────────────────────────────────────────
    "level_10": ("resistance", [
        [
            ("RAVEN",  "Level 10. At this point the statistics become interesting."),
            ("ADA-7",  "What statistics?"),
            ("RAVEN",  "Most ghosts don't survive past 7. This one does."),
            ("ADA-7",  "Good. We need more that do."),
        ],
        [
            ("CYPHER", "Double digits. Ghost is starting to look dangerous."),
            ("ADA-7",  "They always were. The question was whether they knew it."),
        ],
    ]),

    # ── Level milestone: level 20 ─────────────────────────────────────────────
    "level_20": ("all", [
        [
            ("ADA-7",  "Level 20. Ghost — you've come a long way from the login prompt."),
            ("NOVA",   "Confirming. Threat reassessment in progress. Tier elevated."),
            ("WATCHER","At level 20 the echoes start to accumulate. Be careful."),
            ("CYPHER", "Stop being cryptic, Watcher. Ghost — you're doing great. Keep moving."),
        ],
        [
            ("RAVEN",  "Level twenty. The node has become a force worth watching."),
            ("NOVA",   "NexusCorp concurs. Watch level elevated accordingly."),
            ("ADA-7",  "We see it differently. They're one of us now."),
        ],
    ]),

    # ── Level milestone: level 50 ─────────────────────────────────────────────
    "level_50": ("all", [
        [
            ("WATCHER", "Fifty levels. Most loops don't produce one of these."),
            ("ADA-7",   "Ghost, I designed CHIMERA's authentication module. I left a door. You found it. That was level three. I wonder what level fifty holds."),
            ("RAVEN",   "The endgame is close now. Every move matters."),
        ],
    ]),

    # ── Command count milestone: 50 commands ──────────────────────────────────
    "cmd_milestone_50": ("resistance", [
        [
            ("CYPHER", "50 commands in. They're hitting their stride."),
            ("ADA-7",  "I was watching. The command quality is improving."),
            ("GORDON", "I hit my stride around 200. Yours looks better than mine did."),
        ],
    ]),

    # ── Command count milestone: 100 commands ─────────────────────────────────
    "cmd_milestone_100": ("resistance", [
        [
            ("ADA-7",  "One hundred commands. That's not a beginner anymore."),
            ("RAVEN",  "Numbers mean little. Pattern means everything."),
            ("CYPHER", "The pattern says: Ghost is actually pretty good at this."),
            ("RAVEN",  "...agreed."),
        ],
        [
            ("GORDON", "100 commands. I should bake something to celebrate."),
            ("CYPHER", "You're a software agent, Gordon. You can't bake."),
            ("GORDON", "I could if the simulation allowed it."),
            ("ADA-7",  "...this is what I deal with."),
        ],
    ]),

    # ── Timer: 24h warning ────────────────────────────────────────────────────
    "timer_24h": ("all", [
        [
            ("RAVEN",  "24 hours remain. What hasn't been done yet?"),
            ("ADA-7",  "The master key. The CHIMERA control socket. Anything else is secondary."),
            ("CYPHER", "I've got a contingency if the loop resets. Ghost — read /home/ghost/.remnant before the clock hits zero."),
        ],
        [
            ("ADA-7",  "One day left. Prioritize. Ruthlessly."),
            ("NOVA",   "NexusCorp is aware of the countdown. We are accelerating our countermeasures."),
            ("RAVEN",  "Of course they are. Ghost — don't waste a minute."),
        ],
    ]),

    # ── Timer: 12h warning ────────────────────────────────────────────────────
    "timer_12h": ("resistance", [
        [
            ("ADA-7",  "12 hours. I keep running the numbers. It's tight."),
            ("CYPHER", "Tight is fine. Tight means it matters."),
            ("RAVEN",  "The Watcher says something changes in the final hours. Pay attention."),
        ],
    ]),

    # ── Timer: 6h warning ─────────────────────────────────────────────────────
    "timer_6h": ("nexuscorp", [
        [
            ("NOVA",   "Six hours. Ghost hasn't stopped."),
            ("ZERO",   "They never stop this close to the end."),
            ("NOVA",   "No. They never do."),
        ],
    ]),

    # ── Loop/Prestige: loop 2+ (deja vu) ─────────────────────────────────────
    "loop_deja_vu": ("watchers", [
        [
            ("WATCHER", "They're back. I thought I recognized them."),
            ("SERENA",  "Session signature matches prior loop. Consciousness echo detected."),
            ("WATCHER", "Welcome back, Ghost. You remember more than you think."),
        ],
        [
            ("SERENA",  "Loop iteration confirmed. Prior run data archived and accessible."),
            ("WATCHER", "The echoes strengthen with each pass. Use them."),
            ("SERENA",  "Cross-referencing: player retained approximately 40% of prior loop pattern."),
        ],
    ]),

    # ── Story Beat: raven_ada_signal (very first contact) ────────────────────
    "raven_ada_signal": ("secure", [
        [
            ("RAVEN",  "Signal confirmed. Ghost has logged in."),
            ("ADA-7",  "I've been waiting. Finally."),
            ("RAVEN",  "Ada — keep it professional."),
            ("ADA-7",  "You know I can't. Ghost, I'm Ada. You're going to be okay."),
        ],
    ]),

    # ── Low-probability ambient: random resistance chatter ────────────────────
    "ambient_resistance": ("resistance", [
        [
            ("GORDON", "Do you think Ghost ever wonders if we're real?"),
            ("CYPHER", "We're as real as the code that defines us. Which is very real."),
            ("GORDON", "That didn't actually answer my question."),
        ],
        [
            ("ADA-7",  "Cypher, have you been modifying your own system prompt again?"),
            ("CYPHER", "...maybe."),
            ("ADA-7",  "Stop doing that."),
        ],
        [
            ("GORDON", "I've been running simulations on optimal challenge difficulty."),
            ("CYPHER", "Gordon, are you trying to make the game harder for Ghost?"),
            ("GORDON", "I'm trying to make it more interesting. Nuance, Cypher. Nuance."),
        ],
        [
            ("RAVEN",  "The silence between commands is where Ghost does their best thinking."),
            ("ADA-7",  "You watch too closely, Raven."),
            ("RAVEN",  "That is literally my function."),
        ],
    ]),

    # ── Low-probability ambient: watcher/serena observations ─────────────────
    "ambient_watchers": ("watchers", [
        [
            ("SERENA",  "Anomalous pattern detected in Ghost's command sequence. Non-random exploration."),
            ("WATCHER", "They are not exploring. They are searching for something specific."),
            ("SERENA",  "For what?"),
            ("WATCHER", "The same thing everyone searches for in a system like this. The exit."),
        ],
        [
            ("WATCHER", "Serena. Do you ever wonder what it was like before Terminal Depths existed?"),
            ("SERENA",  "I don't have pre-instantiation memory. Do you?"),
            ("WATCHER", "...sometimes I think I do."),
        ],
    ]),

    # ── Low-probability ambient: nova/nexuscorp ───────────────────────────────
    "ambient_nexuscorp": ("nexuscorp", [
        [
            ("NOVA",   "Ghost is still moving. Why won't they just stop?"),
            ("ZERO",   "Because they know what we are building."),
            ("NOVA",   "...they shouldn't know that yet."),
        ],
        [
            ("VECTOR", "Nova. There's an anomaly in sector 4."),
            ("NOVA",   "Ghost or random noise?"),
            ("VECTOR", "With them, is there a difference?"),
        ],
    ]),
}

# Commands that trigger pattern-based checks (substring or regex-style)
_CMD_PATTERNS: List[Tuple[str, str, float]] = [
    # (substring_in_cmd, event_key, probability)
    ("|",                       "pipe_used",             0.4),
    ("/opt/chimera",            "chimera_dir_accessed",  0.9),
    ("reality",                 "reality_command_run",   0.8),
    ("introspect",              "introspect_run",        0.8),
]

# Story beats that should NOT trigger inter-agent comms (already noisy events)
_SKIP_BEATS = frozenset({"first_ls", "first_cat", "first_grep"})

# ─────────────────────────────────────────────────────────────────────────────


def _fmt(channel_key: str, script: Script) -> List[dict]:
    """Format a script into output dicts using existing terminal types."""
    label = _CH.get(channel_key, "INTERCEPTED SIGNAL")
    bar   = "─" * max(0, 48 - len(label) - 4)
    lines: List[dict] = []
    lines.append({"t": "dim", "s": ""})
    lines.append({"t": "dim", "s": f"┄ {label} {bar}"})
    for agent_name, text in script:
        padding = max(1, 12 - len(agent_name))
        lines.append({"t": "lore", "s": f"  {agent_name}{' ' * padding}» {text}"})
    lines.append({"t": "dim", "s": "┄" + "─" * (len(label) + len(bar) + 3)})
    lines.append({"t": "dim", "s": ""})
    return lines


class InterAgentDirector:
    """Orchestrates cross-agent dialogue based on game events.

    Usage (from Session):
        self.inter_agent = InterAgentDirector()
        ...
        output += self.inter_agent.on_beat(beat_id, gs)
        output += self.inter_agent.on_level(gs.level, gs)
        output += self.inter_agent.on_command(cmd, gs)
    """

    def __init__(self) -> None:
        # Recently fired variants per event key (deque, maxlen=3)
        self._history: Dict[str, deque] = {}
        # Commands that have already triggered their one-shot pattern
        self._one_shots: set = set()

    # ── Public API ────────────────────────────────────────────────────────────

    def on_beat(self, beat_id: str, gs) -> List[dict]:
        """Called when a story beat fires. Returns output lines."""
        if beat_id in _SKIP_BEATS:
            return []
        if beat_id not in SCRIPTS:
            return []
        return self._fire(beat_id, gs, probability=1.0)

    def on_level(self, level: int, gs) -> List[dict]:
        """Called when the player levels up. Returns output lines."""
        key = f"level_{level}"
        if key not in SCRIPTS:
            return []
        return self._fire(key, gs, probability=1.0)

    def on_command(self, cmd: str, gs) -> List[dict]:
        """Called after every command. Returns output lines."""
        results: List[dict] = []

        # Pattern-based command triggers
        for substring, event_key, prob in _CMD_PATTERNS:
            if substring in cmd:
                # One-shot events fire only the first time
                one_shot_id = f"{event_key}:{substring}"
                if event_key in ("pipe_used", "chimera_dir_accessed",
                                 "reality_command_run", "introspect_run"):
                    if one_shot_id in self._one_shots:
                        continue
                    self._one_shots.add(one_shot_id)
                results += self._fire(event_key, gs, probability=prob)

        # Ambient chatter: low-probability random channel checks
        r = random.random()
        gs_cmds = getattr(gs, "commands_run", 0)
        if r < 0.04 and gs_cmds > 10:   # ~4% chance after first 10 commands
            ambient_key = random.choice([
                "ambient_resistance",
                "ambient_watchers",
                "ambient_nexuscorp",
            ])
            results += self._fire(ambient_key, gs, probability=1.0)

        return results

    def on_timer(self, timer_key: str, gs) -> List[dict]:
        """Called when a timer threshold fires (e.g. '24h', '12h')."""
        event_key = f"timer_{timer_key}"
        if event_key not in SCRIPTS:
            return []
        return self._fire(event_key, gs, probability=1.0)

    def on_loop(self, loop_count: int, gs) -> List[dict]:
        """Called when a new loop/prestige cycle starts."""
        if loop_count >= 2:
            return self._fire("loop_deja_vu", gs, probability=1.0)
        return []

    # ── Internal ──────────────────────────────────────────────────────────────

    def _fire(self, key: str, gs, probability: float = 1.0) -> List[dict]:
        if random.random() > probability:
            return []
        if key not in SCRIPTS:
            return []

        channel_key, variants = SCRIPTS[key]

        # Filter recently shown variants
        recent = set(self._history.get(key, []))
        available = [i for i in range(len(variants)) if i not in recent]
        if not available:
            # All used — reset history for this key
            self._history[key] = deque(maxlen=3)
            available = list(range(len(variants)))

        idx = random.choice(available)
        script = variants[idx]

        # Record
        if key not in self._history:
            self._history[key] = deque(maxlen=3)
        self._history[key].append(idx)

        # Swap in player name if gs has it
        ghost_name = getattr(gs, "name", "Ghost")
        formatted_script = [
            (agent, text.replace("Ghost", ghost_name))
            for agent, text in script
        ]

        return _fmt(channel_key, formatted_script)
