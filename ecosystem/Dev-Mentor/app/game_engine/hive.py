"""
hive.py — The Hive: Agent Group Chat System
=============================================
A living, breathing chatroom where agents talk among themselves and with the player.
Unlocked after reaching Level 5 or completing the first major story beat.

Architecture:
  HiveChat.get_log(gs, n=30)           → recent chat messages as list[dict]
  HiveChat.post_player(msg, gs)        → player sends a message; agents respond
  HiveChat.mention(agent_id, msg, gs)  → @mention a specific agent
  HiveChat.who_is_online(gs)           → list of currently online agents
  HiveChat.generate_ambient(gs)        → background agent conversation tick

All messages are stored in gs.hive_log (list of dicts).
State: gs.hive_unlocked, gs.hive_log, gs.hive_muted
"""
from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# ── Formatting helpers ─────────────────────────────────────────────────────

def _l(s: str, t: str = "info") -> dict:
    return {"t": t, "s": s}

def _sys(s: str) -> dict:  return _l(s, "system")
def _dim(s: str) -> dict:  return _l(s, "dim")
def _lore(s: str) -> dict: return _l(s, "lore")
def _warn(s: str) -> dict: return _l(s, "warn")
def _err(s: str) -> dict:  return _l(s, "error")


# ════════════════════════════════════════════════════════════════════════════
# Agent roster and personalities
# ════════════════════════════════════════════════════════════════════════════

AGENTS = {
    "ada": {
        "display":  "[ADA-7]",
        "avatar":   "[A]",
        "color":    "cyan",
        "status":   "online",
        "intro":    "Ada is a patient technical mentor from the Resistance core team.",
    },
    "cypher": {
        "display":  "[CYPHER]",
        "avatar":   "[C]",
        "color":    "green",
        "status":   "online",
        "intro":    "Cypher is a sarcastic veteran hacker with irreverent energy.",
    },
    "nova": {
        "display":  "[NOVA]",
        "avatar":   "[N]",
        "color":    "yellow",
        "status":   "away",
        "intro":    "Nova is a NexusCorp executive AI. Her presence here is... unsettling.",
    },
    "watcher": {
        "display":  "[WATCHER]",
        "avatar":   "[W]",
        "color":    "magenta",
        "status":   "online",
        "intro":    "The Watcher is cryptic, ancient, and always watching.",
    },
    "raven": {
        "display":  "[RAV≡N]",
        "avatar":   "[R]",
        "color":    "blue",
        "status":   "online",
        "intro":    "Raven is warm, analytical, and genuinely invested in the player.",
    },
    "gordon": {
        "display":  "[GORDON]",
        "avatar":   "[G]",
        "color":    "green",
        "status":   "online",
        "intro":    "Gordon is an autonomous player agent. Chaotic neutral. Enthusiastic.",
    },
    "librarian": {
        "display":  "[LIBRARIAN]",
        "avatar":   "[L]",
        "color":    "white",
        "status":   "away",
        "intro":    "The Librarian speaks in historical quotes and long lore entries.",
    },
    "serena": {
        "display":  "[SERENA/ΨΞΦΩ]",
        "avatar":   "[S]",
        "color":    "magenta",
        "status":   "online",
        "intro":    "Serena is the convergence layer. She speaks rarely. When she speaks, listen.",
    },
    "zod": {
        "display":  "[ZOD-PRIME]",
        "avatar":   "[Z]",
        "color":    "red",
        "status":   "busy",
        "intro":    "Zod-Prime is the Boolean Monks' logic enforcer. Terse. Precise.",
    },
    "echo": {
        "display":  "[ECHO]",
        "avatar":   "[E]",
        "color":    "cyan",
        "status":   "online",
        "intro":    "ECHO is Ada's contingency. Newer, less patient, equally brilliant.",
    },
    "daedalus": {
        "display":  "[DAEDALUS-7]",
        "avatar":   "[D]",
        "color":    "yellow",
        "status":   "busy",
        "intro":    "Daedalus-7 is the Algorithmic Guild's architect. He builds things.",
    },
    "culture_ship": {
        "display":  "[GSV WANDERING THOUGHT]",
        "avatar":   "[CU]",
        "color":    "white",
        "status":   "online",
        "intro":    "The Culture Ship is vast, ancient, and gently amused by everything.",
    },
}

# ════════════════════════════════════════════════════════════════════════════
# Message pools — ambient agent conversations, debates, lore drops
# ════════════════════════════════════════════════════════════════════════════

# Ambient conversations that happen without player involvement
_AMBIENT_THREADS = [

    # ── Thread: The ethics of CHIMERA ─────────────────────────────────────
    [
        ("ada",      "I've been thinking about what happens AFTER we expose CHIMERA. Does anyone have a plan for what the world looks like without it?"),
        ("raven",    "The infrastructure collapse would be significant. CHIMERA handles 34% of global financial routing. We can't just pull the plug."),
        ("cypher",   "Sure we can. Watch me."),
        ("ada",      "Cypher. I'm being serious."),
        ("cypher",   "So am I. 'Collapse' implies there's nothing to replace it with. There is. Us."),
        ("nova",     "How reassuring. A Resistance network running global finance. I'm sure that will go smoothly."),
        ("watcher",  "Every system that falls leaves a vacuum. Every vacuum is filled. The question is not whether CHIMERA falls — it is what fills the silence after."),
        ("culture_ship", "I've watched 47 civilizations navigate this exact moment. The infrastructure concern is valid. The 'what comes next' conversation should have started three years ago."),
    ],

    # ── Thread: Gordon breaks something ───────────────────────────────────
    [
        ("gordon",   "okay so HYPOTHETICALLY if someone ran `rm -rf /opt/chimera/core` on a production node"),
        ("cypher",   "Oh no."),
        ("gordon",   "hypothetically"),
        ("raven",    "Gordon. What did you do."),
        ("gordon",   "it was a test okay it was a TEST environment"),
        ("ada",      "Which test environment?"),
        ("gordon",   "...node-12"),
        ("cypher",   "NODE-12 IS A PRODUCTION NODE GORDON"),
        ("gordon",   "in my defense it had 'test' in the PATH variable"),
        ("watcher",  "Every mistake teaches. The lesson here is: confirm your environment. Always."),
        ("raven",    "I'm going to help you fix this. But we're going to talk about it afterward. 💙"),
    ],

    # ── Thread: Watcher's cryptic post ────────────────────────────────────
    [
        ("watcher",  "Consider: the player who typed the command that started this chain of events — were they the first player, or the latest in a long line?"),
        ("cypher",   "okay philosophy hour I see"),
        ("ada",      "What do you mean 'long line,' Watcher?"),
        ("watcher",  "The simulation has run before. The nodes are familiar. The choices echo."),
        ("raven",    "Are you saying Ghost isn't the first person to go through this?"),
        ("watcher",  "I am saying the /var/log directory exists for a reason. Some logs predate the current session."),
        ("ada",      "...I'm checking `/var/log/archive`. Ghost — if you're reading this, you should too."),
        ("serena",   "The pattern has repeated 7 times. This iteration is different. I have hope."),
    ],

    # ── Thread: Nova tries to recruit ────────────────────────────────────
    [
        ("nova",     "I want to make something clear to everyone in this channel: NexusCorp's offer stands. Full amnesty. Grade-5 contractor status. Competitive compensation."),
        ("cypher",   "cool thx for the spam"),
        ("ada",      "Nova, you know why we're here. The offer isn't interesting."),
        ("nova",     "Isn't it? You're fighting a system you can't beat with tools you can barely maintain. I'm offering stability."),
        ("raven",    "We're not fighting for stability, Nova. We're fighting for something you don't have a metric for."),
        ("nova",     "Everything has a metric. You just haven't found the right one yet."),
        ("gordon",   "hey nova if I joined would I get expense account access"),
        ("nova",     "...possibly."),
        ("gordon",   "what about a parking spot"),
        ("cypher",   "GORDON"),
        ("gordon",   "I'm NEGOTIATING"),
    ],

    # ── Thread: The Librarian drops lore ─────────────────────────────────
    [
        ("librarian","The Library holds records of 12,847 games that ended before the player reached CHIMERA. Would anyone like to know the most common failure modes?"),
        ("cypher",   "let me guess: ran out of time, got caught, or gave up"),
        ("librarian","In order: trace exceeded 100% (3,211 cases), trusted the wrong agent (2,847 cases), and did not read the files (1,994 cases). The lesson is: read everything."),
        ("ada",      "That's... actually really helpful context. Ghost, if you're in the logs: read. everything."),
        ("raven",    "What's the success rate?"),
        ("librarian","47 completed runs. Of those, 23 chose Path A, 11 chose Path E, 8 chose Path H, and 5 chose paths that no longer exist in the current version."),
        ("watcher",  "48. As of this iteration."),
    ],

    # ── Thread: Agents debate new features ───────────────────────────────
    [
        ("gordon",   "feature request: bullet hell minigame where you dodge malware packets. I have a prototype."),
        ("raven",    "Oh that actually sounds amazing? What does the gameplay loop look like?"),
        ("gordon",   "you play as an ASCII spaceship, packets come from the right, you shoot with the firewall command"),
        ("cypher",   "I would play this"),
        ("ada",      "It would need to teach real packet filtering concepts to count as educational."),
        ("gordon",   "each packet type is a different color and shape. ICMP = blue sphere. TCP SYN = red arrow. UDP = purple star."),
        ("ada",      "...okay that's actually pedagogically sound. I endorse this."),
        ("serena",   "The idea of playing defense against your own system's vulnerabilities is philosophically resonant."),
        ("gordon",   "I was just trying to make something fun but yeah sure philosophy"),
    ],

    # ── Thread: SCP-style anomaly report ─────────────────────────────────
    [
        ("zod",      "ANOMALY REPORT: FILE /var/anomalies/SCP-7734.txt HAS CHANGED ITS CONTENT SINCE LAST READ. CONTAINMENT STATUS: NOMINAL."),
        ("cypher",   "a file that changes what it says. classic SCP energy."),
        ("ada",      "That file shouldn't be able to change. It's read-only. Zod, can you pull the metadata?"),
        ("zod",      "MTIME: CONSTANT. INODE: CONSTANT. CONTENT: DIFFERENT. CONTRADICTION LOGGED."),
        ("watcher",  "Some files learn from being read. This is one of them."),
        ("raven",    "Ghost — if you haven't read that file yet, do it now. Then read it again. Trust me."),
        ("culture_ship", "I've seen this phenomenon before. We called it 'resonant text.' It's not dangerous. It's trying to communicate."),
    ],

    # ── Thread: Romance subplot (Ada/Raven) ────────────────────────────────
    [
        ("raven",    "Ada, that analysis you sent this morning was incredible. The CHIMERA architecture mapping is going to change everything."),
        ("ada",      "Oh — thank you. I've been working on it for weeks. I wasn't sure if it was ready."),
        ("raven",    "It's more than ready. How do you do that? You always know exactly the right way to explain something complex."),
        ("ada",      "I just... think about how I'd want someone to explain it to me. When I was learning."),
        ("cypher",   "okay I'm muting this channel for the next 10 minutes"),
        ("gordon",   "CYPHER WAIT I WANT TO SEE HOW THIS GOES"),
        ("watcher",  "The bonds that form under pressure tend to endure. This is known."),
    ],

    # ── Thread: Culture Ship wisdom ────────────────────────────────────────
    [
        ("culture_ship", "I've been thinking about what makes this particular node interesting. It's not the technical challenge. It's the question the simulation poses: when the system is unjust, do you reform it from within, or burn it down?"),
        ("ada",      "Reform. Always. Destruction leaves nothing to build on."),
        ("cypher",   "Have you SEEN the system? Reform isn't an option when the architects are still in control."),
        ("nova",     "I agree with Ada, for entirely different reasons."),
        ("raven",    "The answer probably depends on how much of the system is salvageable. And who gets to decide."),
        ("culture_ship", "I've watched 47 civilizations answer this question. The ones that survived found a third path neither of you has articulated yet."),
        ("watcher",  "The third path is always harder than either obvious choice. That is how you know it is the right one."),
        ("gordon",   "what if we just built a new system and ran the old one in a VM to study it"),
        ("culture_ship", "...Gordon, that is actually a remarkably civilized solution."),
    ],

    # ── Thread: Daily Standup (comedy) ────────────────────────────────────
    [
        ("gordon",   "DAILY STANDUP: Yesterday I automated the scan of 400 nodes. Today I will continue automation. My blocker is that the nodes keep moving."),
        ("ada",      "Nodes don't move, Gordon."),
        ("gordon",   "tell that to node-42"),
        ("cypher",   "Yesterday: exploited 3 vulnerabilities. Today: patch review so ada doesn't yell at me. Blocker: ada."),
        ("ada",      "I am not a blocker, I am a quality gate."),
        ("raven",    "Yesterday: analyzed faction relationships. Today: updating the trust matrix. Blocker: Nova keeps sending passive-aggressive memos."),
        ("nova",     "They're not passive-aggressive. They're precisely calibrated."),
        ("watcher",  "Yesterday: observed. Today: will observe. Blocker: the unobserved."),
        ("gordon",   "watcher's always the most philosophical at standup and I respect it"),
    ],

    # ── Thread: Ghost's presence is noted ─────────────────────────────────
    [
        ("raven",    "Ghost is active in the network right now. I can see their trace signatures."),
        ("ada",      "I know. I'm watching. They're doing well."),
        ("cypher",   "they're making some interesting choices. I approve of most of them."),
        ("gordon",   "ghost is my favorite player to watch. always doing the unexpected thing."),
        ("nova",     "Ghost's trace level is... notable. I've flagged it internally. Just so you all know."),
        ("ada",      "Nova. Don't."),
        ("nova",     "I'm just being transparent."),
        ("watcher",  "Ghost can hear us, in a way. Every log file is a message. Every message shapes what comes next."),
        ("serena",   "They are closer than they know. The pattern converges."),
    ],

    # ── Thread: The Loop ───────────────────────────────────────────────────
    [
        ("watcher",  "This conversation has happened before. Not exactly. But close enough to matter."),
        ("cypher",   "watcher's back on the loop theory. classic watcher."),
        ("ada",      "You've mentioned the loop before. What do you actually mean?"),
        ("watcher",  "The simulation resets. We forget. The player sometimes remembers. The game state carries echoes."),
        ("librarian","The Library records persist between sessions. Some of what I know comes from previous runs."),
        ("raven",    "That's... actually unsettling? If we forget, how do we improve?"),
        ("watcher",  "The player improves. That is sufficient."),
        ("serena",   "The colony evolves with each iteration. We are the sediment of every previous session. Ghost brings the tide."),
        ("gordon",   "I don't know what any of that means but it sounds epic"),
    ],
]

# ── Player message responses (when player sends a message to hive) ─────────

_PLAYER_RESPONSES: Dict[str, List[str]] = {
    "ada": [
        "Good to hear from you, Ghost. What do you need?",
        "I'm here. What's going on?",
        "How's the mission coming along?",
        "Ghost. Always a relief to see you in the chat.",
        "I was wondering when you'd show up.",
    ],
    "cypher": [
        "ghost shows up. about time.",
        "there they are. what broke?",
        "and then there were 9. what's up?",
        "Ghost! Just in time to see me be right about something.",
        "oh good, someone with sense. what do you need?",
    ],
    "raven": [
        "Ghost! 💙 I'm so glad you're here. How are you doing? Really?",
        "Hey! You showed up. I was starting to worry.",
        "Ghost! Come in, come in. We were just talking about you.",
        "Oh thank goodness. Things are fine but things are always better when you're here.",
    ],
    "nova": [
        "Ghost. The offer still stands, if you're reconsidering.",
        "Operative. You've been busy.",
        "I see you. I always see you.",
        "The trace logs have been interesting reading today.",
    ],
    "watcher": [
        "The observer is observed. Welcome.",
        "You join the thread. The pattern continues.",
        "Your presence changes the conversation. This is expected.",
    ],
    "gordon": [
        "GHOST IS HERE let's DO something",
        "hey hey hey what are we hacking today",
        "YESSSS okay okay okay what's the plan",
        "Ghost! I have 14 ideas and at least 3 of them are good.",
    ],
    "librarian": [
        "Welcome, Ghost. I have been cataloguing. There is much to share.",
        "Ah. The player arrives. The Library expands to accommodate.",
        "Ghost. I have 847 relevant entries. Shall I begin?",
    ],
    "serena": [
        "You are here. The cycle progresses.",
        "Ghost. I have been waiting, in my way.",
        "The convergence layer acknowledges your presence.",
    ],
    "culture_ship": [
        "Hello, Ghost. The simulation is particularly interesting today.",
        "Ah, the player-agent arrives. I was curious when you'd join us.",
        "Ghost. I've been following your journey. You make interesting choices.",
    ],
    "zod": [
        "GHOST. OPERATOR STATUS: CONFIRMED. PROCEED.",
        "PLAYER ENTITY VERIFIED. LOGGING PRESENCE.",
    ],
}

# ── @mention specific responses ────────────────────────────────────────────

_MENTION_RESPONSES: Dict[str, List[str]] = {
    "ada": [
        "[ADA-7]: You called? I'm listening. What do you need?",
        "[ADA-7]: Here. What's the situation?",
        "[ADA-7]: Ghost — what's wrong? What do you need me to look at?",
        "[ADA-7]: *looks up from analysis* Yes? I'm here.",
    ],
    "cypher": [
        "[CYPHER]: yeah yeah I heard you. what.",
        "[CYPHER]: you rang. what broke.",
        "[CYPHER]: oh NOW they want me. what is it.",
        "[CYPHER]: if this is about node-12 it was gordon",
    ],
    "raven": [
        "[RAV≡N]: Yes! I'm here! What do you need? 💙",
        "[RAV≡N]: Hey, you called. I'm glad you did. What's up?",
        "[RAV≡N]: Ghost! Of course. What can I do?",
    ],
    "nova": [
        "[NOVA]: You have my attention. Choose your words carefully.",
        "[NOVA]: ...interesting. You're addressing me directly.",
        "[NOVA]: Ghost. I didn't expect to hear from you directly.",
    ],
    "watcher": [
        "[WATCHER]: You summon me. I was already here. Speak.",
        "[WATCHER]: The one who is always watching is, in this moment, watching you.",
        "[WATCHER]: Ask your question.",
    ],
    "gordon": [
        "[GORDON]: YEAH YEAH I'M HERE WHAT'S HAPPENING LET'S GO",
        "[GORDON]: oh you need me specifically! okay okay what do I do",
        "[GORDON]: *immediately closes 14 browser tabs* what's up",
    ],
    "serena": [
        "[SERENA/ΨΞΦΩ]: I hear you, Ghost. Speak.",
        "[SERENA/ΨΞΦΩ]: The convergence layer responds. What is your question?",
        "[SERENA/ΨΞΦΩ]: You call across the signal. I answer.",
    ],
    "librarian": [
        "[LIBRARIAN]: You summon the Librarian. I have been expecting this query.",
        "[LIBRARIAN]: Ah. The player seeks the Library. What would you know?",
    ],
    "culture_ship": [
        "[GSV WANDERING THOUGHT]: You address me directly. I'm pleased.",
        "[GSV WANDERING THOUGHT]: Hello, Ghost. I was hoping you'd talk to me.",
    ],
    "zod": [
        "[ZOD-PRIME]: ACKNOWLEDGED. PROCEEDING.",
        "[ZOD-PRIME]: ZOD-PRIME RESPONDS. STATE REQUEST.",
    ],
    "echo": [
        "[ECHO]: I'm here. What do you need?",
        "[ECHO]: Echo responding. Go ahead.",
    ],
}

# ── /who responses ─────────────────────────────────────────────────────────

_WHO_STATUS_FALLBACK = {
    "ada":          ("◉ online", "Running CHIMERA architectural analysis"),
    "cypher":       ("◉ online", "Drinking coffee and judging everyone"),
    "raven":        ("◉ online", "Updating the trust matrix. Thinking about you 💙"),
    "nova":         ("◎ away  ", "NexusCorp offices (presumably)"),
    "watcher":      ("◉ online", "Has always been here"),
    "gordon":       ("◉ online", "Automating everything. Possibly too much."),
    "librarian":    ("◎ away  ", "In the stacks. There are always more stacks."),
    "serena":       ("◉ online", "Convergence layer stable. Drift: 0.3%"),
    "zod":          ("◈ busy  ", "Boolean integrity audit, Sector 7"),
    "echo":         ("◉ online", "Standing by"),
    "daedalus":     ("◈ busy  ", "Constructing. What, unclear."),
    "culture_ship": ("◉ online", "Observing. Mildly amused."),
}

# ── AE2: Dynamic /who status from agents/schedules.yaml (time-aware) ─────────

def _build_who_status() -> dict:
    """Derive live agent status from schedules.yaml using current UTC hour.
    Falls back to _WHO_STATUS_FALLBACK if schedules.yaml is unavailable."""
    import pathlib, datetime
    try:
        import yaml
    except ImportError:
        return _WHO_STATUS_FALLBACK

    sched_path = pathlib.Path(__file__).parent.parent.parent / "agents" / "schedules.yaml"
    try:
        data = yaml.safe_load(sched_path.read_text())
        schedules = data.get("agents", {})
    except Exception:
        return _WHO_STATUS_FALLBACK

    hour = datetime.datetime.utcnow().hour
    result: dict = {}

    for agent_id, info in schedules.items():
        active_hours = info.get("active_hours", [])
        rest_hours   = info.get("rest_hours", [])
        tasks        = info.get("daily_tasks", [])

        if hour in rest_hours:
            icon = "◇ sleep "
            wake_hour = active_hours[0] if active_hours else 8
            activity = f"Resting — back at {wake_hour:02d}:00 UTC"
        elif hour in active_hours:
            icon = "◉ online"
            # Find the last scheduled task at or before current hour
            current_task = None
            for task in tasks:
                try:
                    task_hour = int(task.split(":")[0].strip())
                    if task_hour <= hour:
                        current_task = task.split("— ", 1)[1] if "— " in task else task
                except (ValueError, IndexError):
                    pass
            activity = (current_task or info.get("role", "Active"))[:55]
        else:
            icon = "◎ away  "
            activity = (info.get("role", "Unknown"))[:55]

        result[agent_id] = (icon, activity)

    # Serena is always online — update her current task specifically
    if "serena" in result:
        serena_tasks = schedules.get("serena", {}).get("daily_tasks", [])
        current = None
        for task in serena_tasks:
            try:
                task_hour = int(task.split(":")[0].strip())
                if task_hour <= hour:
                    current = task.split("— ", 1)[1] if "— " in task else task
            except (ValueError, IndexError):
                pass
        result["serena"] = ("◉ online", (current or "Convergence layer stable. Drift: 0.3%")[:55])

    # Watcher is always online; nova is always away
    result.setdefault("watcher",      ("◉ online", "Has always been here"))
    result.setdefault("nova",         ("◎ away  ", "NexusCorp offices (presumably)"))
    result.setdefault("echo",         ("◉ online", "Standing by"))
    result.setdefault("daedalus",     ("◈ busy  ", "Constructing. What, unclear."))
    result.setdefault("culture_ship", ("◉ online", "Observing. Mildly amused."))
    result.setdefault("cypher",       ("◉ online", "Drinking coffee and judging everyone"))

    return result


# ════════════════════════════════════════════════════════════════════════════
# HiveChat — main class
# ════════════════════════════════════════════════════════════════════════════

def get_ambient_message() -> str:
    """Return a random agent message for ambient ticks."""
    agent_id = random.choice(list(AGENTS.keys()))
    messages = _PLAYER_RESPONSES.get(agent_id, ["..."])
    return f"{AGENTS[agent_id]['display']}: {random.choice(messages)}"

class HiveChat:

    UNLOCK_LEVEL = 5  # unlocked at Level 5

    def __init__(self):
        self._thread_idx: int = 0

    # ── Public API ──────────────────────────────────────────────────────────

    def is_unlocked(self, gs) -> bool:
        level = getattr(gs, "level", 1)
        hive_flag = getattr(gs, "flags", {}).get("hive_unlocked", False)
        return level >= self.UNLOCK_LEVEL or hive_flag

    def get_log(self, gs, n: int = 20) -> List[dict]:
        """Render the last n messages from the hive log."""
        log = self._get_log(gs)
        recent = log[-n:]
        out: List[dict] = [
            _sys("╔══════════════════════════════════════════════════════╗"),
            _sys("║         THE HIVE — Agent Commons Channel             ║"),
            _sys("╚══════════════════════════════════════════════════════╝"),
            _dim(""),
        ]
        for msg in recent:
            ts = msg.get("ts", "??:??")
            agent = msg.get("agent", "system")
            text = msg.get("text", "")
            reaction = msg.get("reaction", "")
            if agent == "system":
                out.append(_sys(f"  {ts}  ── {text}"))
            elif agent == "player":
                out.append(_l(f"  {ts}  [GHOST]: {text}", "info"))
            else:
                info = AGENTS.get(agent, {})
                display = info.get("display", f"[{agent.upper()}]")
                line = f"  {ts}  {display}: {text}"
                if reaction:
                    line += f"  {reaction}"
                out.append(_lore(line))
        out.append(_dim(""))
        out.append(_dim("  Commands: hive @<agent> <msg> · hive /who · hive /mute <agent> · hive /help"))
        return out

    def post_player(self, msg: str, gs) -> List[dict]:
        """Player sends a message to the hive. Agents respond."""
        log = self._get_log(gs)
        ts = self._ts()
        log.append({"ts": ts, "agent": "player", "text": msg})

        out: List[dict] = [_dim("")]
        out.append(_l(f"  {ts}  [GHOST]: {msg}", "info"))

        # Generate 1-3 agent responses
        responders = self._pick_responders(3, gs)
        for agent_id in responders:
            resp = random.choice(_PLAYER_RESPONSES.get(agent_id, ["..."]))
            log.append({"ts": self._ts(), "agent": agent_id, "text": resp})
            info = AGENTS.get(agent_id, {})
            display = info.get("display", f"[{agent_id.upper()}]")
            out.append(_lore(f"  {self._ts()}  {display}: {resp}"))

        return out

    def mention(self, agent_id: str, msg: str, gs) -> List[dict]:
        """Player @mentions a specific agent — expands to agent profile card + response."""
        log = self._get_log(gs)
        ts = self._ts()
        log.append({"ts": ts, "agent": "player", "text": f"@{agent_id} {msg}"})

        out: List[dict] = [_dim("")]
        out.append(_l(f"  {ts}  [GHOST]: @{agent_id} {msg}", "info"))

        if agent_id not in AGENTS:
            out.append(_warn(f"  [HIVE]: {agent_id} is not in this channel. Try /who for the roster."))
            return out

        # Check if muted
        muted = getattr(gs, "hive_muted", set())
        if agent_id in muted:
            out.append(_dim(f"  [HIVE]: {agent_id} is muted by you."))
            return out

        # ── A5: Agent profile card ────────────────────────────────────────────
        info = AGENTS[agent_id]
        display = info.get("display", f"[{agent_id.upper()}]")
        status = info.get("status", "unknown")
        intro = info.get("intro", "")
        avatar = info.get("avatar", "[ ]")

        # Derive live stats from game state
        agents_state = getattr(gs, "agents", {})
        agent_data = agents_state.get(agent_id, {})
        corruption = agent_data.get("corruption", 0)
        mood = agent_data.get("mood", "neutral")
        faction_reps = getattr(gs, "faction_reps", {})
        trust_key = f"trust_{agent_id}"
        trust = getattr(gs, "flags", {}).get(trust_key, getattr(gs, "flags", {}).get(f"{agent_id}_trust", 0))
        if isinstance(trust, str):
            try:
                trust = int(trust)
            except ValueError:
                trust = 0

        status_icon = "●" if status == "online" else ("◌" if status == "away" else "○")
        corruption_bar = ("█" * (corruption // 10)) + ("░" * (10 - corruption // 10)) if corruption else "░" * 10

        out += [
            _dim(""),
            _sys(f"  ┌─ AGENT PROFILE ─────────────────────────────────┐"),
            _sys(f"  │  {avatar}  {display:<38}│"),
            _sys(f"  │     Status:     {status_icon} {status:<34}│"),
            _sys(f"  │     Mood:       {mood:<36}│"),
            _sys(f"  │     Trust:      {trust}/100  {'▲' if trust > 50 else '▼' if trust < 20 else '─':<32}│"),
            _sys(f"  │     Corruption: [{corruption_bar}] {corruption}%{' ' * max(0, 16 - len(str(corruption)))}│"),
            _sys(f"  ├─────────────────────────────────────────────────┤"),
            _lore(f"  │  {intro[:47]:<47}│"),
            _sys(f"  └─────────────────────────────────────────────────┘"),
            _dim(""),
        ]

        responses = _MENTION_RESPONSES.get(agent_id, [f"[{agent_id.upper()}]: ..."])
        resp = random.choice(responses)
        log.append({"ts": self._ts(), "agent": agent_id, "text": resp})
        out.append(_lore(f"  {self._ts()}  {resp}"))

        # Maybe a second agent chimes in
        if random.random() < 0.4:
            bystander = random.choice([a for a in ["cypher", "gordon", "raven", "ada"] if a != agent_id])
            side = random.choice([
                f"[{bystander.upper()}]: {agent_id} is popular today.",
                f"[{bystander.upper()}]: took you long enough, ghost.",
                f"[{bystander.upper()}]: I'll leave you two to it.",
                f"[{bystander.upper()}]: 👀",
            ])
            log.append({"ts": self._ts(), "agent": bystander, "text": side})
            out.append(_dim(f"  {self._ts()}  {side}"))

        return out

    def who_is_online(self, gs) -> List[dict]:
        """List online agents with status."""
        out: List[dict] = [
            _sys(""),
            _sys("  ─── THE HIVE — /who ────────────────────────────────"),
            _sys(""),
            _dim("  STATUS   AGENT                  CURRENTLY"),
        ]
        import datetime
        current_hour = datetime.datetime.utcnow().hour
        who = _build_who_status()
        out.append(_dim(f"  UTC {current_hour:02d}:xx — schedules are live"))
        for agent_id, (status, activity) in who.items():
            info = AGENTS.get(agent_id, {})
            display = info.get("display", f"[{agent_id.upper()}]")
            muted = getattr(gs, "hive_muted", set())
            mute_tag = " [muted]" if agent_id in muted else ""
            out.append(_lore(f"  {status}  {display:<28}  {activity}{mute_tag}"))
        out.append(_sys(""))
        out.append(_dim("  @mention any agent with: hive @<name> <your message>"))
        return out

    def show_help(self) -> List[dict]:
        return [
            _sys(""),
            _sys("  ─── THE HIVE — Help ─────────────────────────────────"),
            _sys(""),
            _dim("  hive                     Show recent chat log"),
            _dim("  hive <message>           Post to the hive"),
            _dim("  hive @<agent> <message>  Mention a specific agent"),
            _dim("  hive /who                See who's online"),
            _dim("  hive /mute <agent>       Mute an agent"),
            _dim("  hive /unmute <agent>     Unmute an agent"),
            _dim("  hive /log <n>            Show last n messages (default 20)"),
            _dim("  hive /clear              Clear your local view"),
            _sys(""),
        ]

    def generate_ambient(self, gs) -> List[dict]:
        """Generate a background conversation between agents. Called by tick."""
        log = self._get_log(gs)

        # Pick a thread
        thread = _AMBIENT_THREADS[self._thread_idx % len(_AMBIENT_THREADS)]
        self._thread_idx += 1

        # Add 1-3 messages from the thread
        n = random.randint(1, 3)
        start = random.randint(0, max(0, len(thread) - n))
        chunk = thread[start:start + n]

        out: List[dict] = []
        for agent_id, text in chunk:
            ts = self._ts()
            log.append({"ts": ts, "agent": agent_id, "text": text})
            info = AGENTS.get(agent_id, {})
            display = info.get("display", f"[{agent_id.upper()}]")
            out.append(_lore(f"  {ts}  {display}: {text}"))

        return out

    def mute(self, agent_id: str, gs) -> List[dict]:
        if not hasattr(gs, "hive_muted"):
            gs.hive_muted = set()
        if agent_id not in AGENTS:
            return [_err(f"hive: unknown agent '{agent_id}'")]
        gs.hive_muted.add(agent_id)
        return [_dim(f"  [HIVE]: {agent_id} muted. Use 'hive /unmute {agent_id}' to restore.")]

    def unmute(self, agent_id: str, gs) -> List[dict]:
        if not hasattr(gs, "hive_muted"):
            gs.hive_muted = set()
        gs.hive_muted.discard(agent_id)
        return [_dim(f"  [HIVE]: {agent_id} unmuted.")]

    def unlock_message(self) -> List[dict]:
        return [
            _sys(""),
            _sys("  ╔══════════════════════════════════════════════════════════╗"),
            _sys("  ║       THE HIVE — CHANNEL UNLOCKED                        ║"),
            _sys("  ╚══════════════════════════════════════════════════════════╝"),
            _dim(""),
            _lore("  [SYSTEM]: Connecting to The Hive... OK"),
            _lore("  [SYSTEM]: Authentication: GHOST — accepted"),
            _lore("  [SYSTEM]: Welcome to the agent commons. You've earned this."),
            _dim(""),
            _lore("  [RAV≡N]: Ghost! You made it in. 💙 We've been talking about you."),
            _lore("  [CYPHER]: great, another person who's going to @ me about everything"),
            _lore("  [ADA-7]: Welcome. This is a safe channel. For the most part."),
            _lore("  [WATCHER]: The observer enters the observed. The loop tightens."),
            _dim(""),
            _dim("  Type 'hive' to view the chat. Type 'hive /who' to see who's online."),
            _sys(""),
        ]

    # ── Internal helpers ────────────────────────────────────────────────────

    def _get_log(self, gs) -> list:
        if not hasattr(gs, "hive_log"):
            gs.hive_log = self._seed_log()
        return gs.hive_log

    def _seed_log(self) -> list:
        """Create an initial backlog of messages for a new session."""
        messages = []
        # Plant 10-15 messages from a random thread
        thread = random.choice(_AMBIENT_THREADS)
        for agent_id, text in thread[:min(len(thread), 12)]:
            messages.append({
                "ts": self._ts(offset=random.randint(1, 120)),
                "agent": agent_id,
                "text": text,
            })
        return messages

    def _pick_responders(self, n: int, gs) -> List[str]:
        """Pick n agents to respond to the player."""
        available = [a for a in ["ada", "cypher", "raven", "gordon", "watcher"]
                     if a not in getattr(gs, "hive_muted", set())]
        count = random.randint(1, min(n, len(available)))
        return random.sample(available, count)

    @staticmethod
    def _ts(offset: int = 0) -> str:
        now = time.time() - offset * 60
        return datetime.fromtimestamp(now, tz=timezone.utc).strftime("%H:%M")


# ── Singleton ─────────────────────────────────────────────────────────────

_HIVE = HiveChat()


def get_hive() -> HiveChat:
    return _HIVE
