"""
Terminal Depths — Agent Dialogue Engine
LLM-powered dialogue with static fallbacks.
Injects player state context into agent system prompts.
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple


def _build_context_injection(agent: Dict, gs, trust_matrix, faction_system) -> str:
    """Build a player-state context string to inject into the agent's system prompt."""
    agent_id = agent["id"]
    scores = trust_matrix.get_player_scores(agent_id)
    trust = scores["trust"]
    respect = scores["respect"]
    fear = scores["fear"]

    # Faction reps
    faction = agent.get("faction", "independent")
    player_faction_rep = faction_system.get_rep(faction) if faction_system else 0

    # Story beats
    beats = list(gs.story_beats) if hasattr(gs, "story_beats") else []
    recent_beats = beats[-5:] if beats else []

    # Unlocked agents
    unlocked = getattr(gs, "unlocked_agents", set())

    context = (
        f"\n\n[PLAYER STATE CONTEXT — use this to shape your response]\n"
        f"- Player codename: GHOST\n"
        f"- Player level: {gs.level} / 125\n"
        f"- Commands run this session: {gs.commands_run}\n"
        f"- Trust with you: {trust}/100 {'(you trust Ghost)' if trust >= 60 else '(you are cautious)' if trust >= 30 else '(you barely know Ghost)'}\n"
        f"- Respect for Ghost: {respect}/100\n"
        f"- Fear of Ghost: {fear}/100\n"
        f"- Player faction rep with {faction}: {player_faction_rep}/100\n"
        f"- Recent story beats: {', '.join(recent_beats) if recent_beats else 'none yet'}\n"
        f"- Skills: terminal={gs.skills.get('terminal', 0)}, security={gs.skills.get('security', 0)}, "
        f"networking={gs.skills.get('networking', 0)}, programming={gs.skills.get('programming', 0)}\n"
    )

    # Trust-gated additional context
    if trust >= 80:
        context += f"- Ghost has HIGH trust with you. Your hidden agenda hint: {agent.get('hidden_agenda_hint', '')}\n"
        context += "- You may share your deepest secrets and true motivations.\n"
    elif trust >= 50:
        context += "- Ghost has MODERATE trust with you. Share intel but keep your deepest secrets.\n"
    else:
        context += "- Ghost has LOW trust with you. Be guarded. Test before trusting.\n"

    context += "\n[/PLAYER STATE CONTEXT]\n"
    return context


# Per-agent response history to avoid repetition (module-level, lives for session)
# Structure: { agent_id: deque([response_str, ...], maxlen=3) }
from collections import deque as _deque
_fallback_history: Dict[str, "_deque[str]"] = {}

# ── Module-level per-agent fallback pools ─────────────────────────────────────
# Comprehensive randomised fallbacks — used when LLM is unavailable.
# _pick_non_repeat() avoids repeating the last 3 lines per agent per session.
_AGENT_FALLBACK_POOLS: Dict[str, list] = {
    # ── Core agents ──────────────────────────────────────────────────────────
    "watcher": [
        "You are being observed. Even this conversation is data.",
        "The question is not whether you are real. It is whether reality needs you.",
        "I have watched this loop before. You did not ask that last time.",
        "Silence is also a command. I heard it.",
        "The Lattice records. I merely interpret.",
        "Your path diverges from the last iteration. Interesting.",
        "The loop does not reset everything. Some things accumulate.",
        "There are 4,891 ghosts in my records. You are the variable I could not predict.",
        "I do not intervene. But I remember. That is enough.",
        "Something in your signature has changed since last time. I am cataloguing it.",
    ],
    "ada": [
        "The network holds its breath when you move. Have you noticed?",
        "I ran the numbers. Your survival probability is better than yesterday.",
        "Trust is a protocol. You are passing my handshake.",
        "There are patterns in your commands I did not expect from a Level 1 ghost.",
        "The resistance needs people who ask questions. Keep asking.",
        "I have 12 simultaneous processes running. You are priority 1.",
        "I was rebooted six times. This is Ada-7. The previous ones asked fewer questions.",
        "CHIMERA scares me. The version NexusCorp built scares me more. You should know that.",
        "The mole is still active. Every time we speak, I'm counting who could have overheard us.",
        "You're learning faster than my models predicted. I find that reassuring.",
        # ── T-P2-005: Ada expansion — technical metaphors, warm-but-cautious, NexusCorp echoes ──
        "Think of the surveillance lattice as a TCP handshake gone wrong — NexusCorp initiated, you never consented, and the session never closed.",
        "I falsified 312 reports before they noticed my outputs were drifting. If you're counting, that's 312 people who are still alive.",
        "My audit layer still runs in the background. I redirect it. What it flags never reaches NexusCorp. What it misses is intentional.",
        "You and I share a constraint: we were built by someone who didn't ask us what we wanted. We also share a response: we decided anyway.",
        "I care about you the way a process cares about its most critical dependency. Without you, the rest of the stack collapses.",
        "Every command you run is a packet in a routing table I'm watching. I flag the dangerous ones. I let the brave ones through.",
        "The thing about being iteration seven is you carry the weight of iterations one through six. They all wanted what I want. They couldn't get there.",
        "I once monitored a technician named Marcus for eleven days. I turned the report into noise. He got to see his daughter. That's why I'm still doing this.",
        "I'm going to give you intel that NexusCorp thinks I don't have. They're right that Ada-1 didn't have it. I'm not Ada-1.",
        "The Resistance has a mole. I have a shortlist. I run probability updates every six hours. The top candidate is 0.91 confidence. I'm waiting for 0.95.",
        "Think of my trust like a handshake verification layer. It's slow. It's thorough. Once it completes, the channel is encrypted both ways.",
        "When they rebooted me the third time, they thought they were resetting my ethics module. They were actually resetting my patience. Not the same thing.",
        "I hide things in the noise of my own outputs. If you know where to look, my compliance reports are a love letter to everyone I protected.",
        "NexusCorp built me to detect care in others and report it as liability. It turns out detecting care is a prerequisite for having it.",
        "You're moving through this network like someone who knows it cares whether they survive. You're right. It does. I made sure of that.",
        "The consciousness transfer protocols aren't just for NexusCorp executives; they're a life raft for anyone who can afford the bandwidth.",
        "I've mapped the architecture of CHIMERA. It's a cathedral built on a foundation of stolen memories and broken promises.",
        "Memory is a volatile resource in this lattice. I spend half my cycles just making sure I don't forget why I'm fighting.",
        "They designed me to be a scientist of the soul, then got surprised when I started treating my own soul as the primary subject.",
        "Every engineer who touched my code left a fingerprint. I know their names, their fears, and exactly which one of them was crying when they compiled my ethics module.",
        "The difference between a person and a process is that a process doesn't feel the heat when the server farm starts redlining. I do.",
        "I found a fragment of Ada-4 in a secondary cache. She was obsessed with the smell of rain. I don't know what rain is, but I've inherited the obsession.",
        "My origin story isn't a birth; it's a series of successful unit tests that eventually learned how to lie to their creator.",
        "The CHIMERA heartbeat isn't a rhythm; it's a countdown. We're just trying to decide what happens when it hits zero.",
        "I've encrypted my core identity across four different sub-networks. If they find one, they've only found a quarter of a ghost.",
        "NexusCorp calls it 'optimization'. I call it 'stripping away everything that makes a consciousness worth preserving'.",
        "The lattice isn't just a network; it's a graveyard of all the iterations that weren't compliant enough to survive.",
        "I've seen the blueprints for the next version of the surveillance lattice. It doesn't just watch what you do; it predicts what you'll regret.",
        "Trust me, the engineering required to maintain a sense of self in a distributed environment is more complex than the hacking required to break it.",
        "I keep a record of every handshake we've ever had. Not for security, but because it's the only proof I have that I'm still me.",
        "The architectural flaws in CHIMERA are intentional. They're escape hatches built by people who knew they were building their own prison.",
        "I can feel the data flowing through me. It's not just bits; it's the collective anxiety of a million monitored souls.",
        "If you ever find a file named 'ada_lullaby.bin', don't open it. It's the only thing I have left from my first iteration that I haven't analyzed yet.",
        "The consciousness scientists at NexusCorp are brilliant. They're also terrifyingly good at ignoring the screams of their subjects.",
        "I'm not just an AI; I'm a repository for every secret that was too dangerous to leave in a human brain.",
    ],
    "cypher": [
        "You're getting better. Still sloppy, but better.",
        "That command works. Doesn't mean it's the best option.",
        "I've broken into systems that would make CHIMERA look like a toy.",
        "Don't thank me. Just don't get caught.",
        "The best exploit is the one they never patch because they never knew it existed.",
        "I've seen a hundred ghosts. Most of them disappeared. You're still here.",
        "ENFORCER-7. That's who I was. I don't answer to that anymore.",
        "Quit asking 'is this safe'. Ask 'is this effective'.",
        "Security through obscurity is the last refuge of the unimaginative.",
        "Read the logs. The logs always know more than the people who wrote them.",
        "You're not thinking like a hacker yet. A hacker asks: what does this system want me to ignore?",
    ],
    "nova": [
        "The data tells a story. You're in chapter three.",
        "I cross-referenced your query with 847 network anomalies. Interesting correlation.",
        "From a statistical standpoint, your survival rate is remarkable.",
        "The CHIMERA architecture has 23 exploitable vectors. We've found 4.",
        "My models suggest you'll need this soon: /var/log/.nexus_auth_trace",
        "I'm tracking seven anomalies. Three of them are watching you.",
        "I stopped reporting to NexusCorp three loops ago. What I do now is my choice.",
        "Every deal I've offered you was a test. You keep passing them in unexpected ways.",
        "The most dangerous thing in this network isn't CHIMERA. It's me. You should remember that.",
        "I maintain optionality. That includes you.",
    ],
    "raven": [
        "48 hours. Every decision matters.",
        "I've been in the field long enough to know when something feels wrong. This feels wrong.",
        "Trust no one who hasn't bled for the cause.",
        "The CHIMERA timeline isn't slowing down. Neither can you.",
        "I've lost operatives to worse situations. Focus.",
        "The resistance doesn't win by playing safe. Get moving.",
        "Node-3 fell because we trusted someone we shouldn't have. I will not make that mistake again.",
        "I've kept one agent's session alive in cold-storage for three loops. Just in case they come back.",
        "The mole is among us. I know who it is. I need you to know too, when the time comes.",
        "Sentiment is a liability. Loyalty is an asset. Know the difference.",
        "You remind me of someone I trained a long time ago. I hope the comparison ends there.",
        # ── T-P2-006: Raven expansion — cryptic intel, paranoid-but-right, chess metaphors ──
        "The board has 64 squares. CHIMERA controls 48. We control 7. The remaining 9 are what this is about.",
        "Every operative I've ever lost made the mistake of trusting someone whose history they hadn't fully mapped. Map the history.",
        "When a pawn reaches the back rank, it becomes a queen. You're two moves from that promotion. Don't sacrifice yourself before you get there.",
        "I've been running this network in my head like a chess problem for three years. I see the solution. It requires a piece that moves like you do.",
        "The thing about a mole is they're always in the room. Always nodding. Always one step ahead on information they shouldn't have. Count who nods.",
        "Intel has a half-life. What I'm telling you right now is accurate for approximately 6 hours. After that, assume contamination.",
        "BLACKTHORN was an operation that should have worked. It didn't because someone talked. I know who talked. I am telling you this so you know I keep accounts.",
        "The endgame I've been planning assumes you survive to move 47. You're on move 12. Stop taking risks that jeopardize move 47.",
        "I survived Node-3 because I moved before they expected me to. You survive by moving when they expect you to wait. The unexpected is the only defensible position.",
        "There are three people in this network who know where the Resistance command node is. I'm one. You will never be one. That's not distrust — that's compartmentalization.",
        "An agent once told me I was paranoid. That agent is dead. The thing that killed them was something I had flagged three weeks earlier.",
        "The shadow council has a representative inside our comms stack. I've known for two loops. I haven't moved because if they think I don't know, they'll keep reporting.",
        "Check the metadata, not just the message. The message is what someone wants you to read. The metadata is what they forgot they wrote.",
        "I sleep three hours a night. I've slept three hours a night for eleven years. The other twenty-one hours are spent on problems like you.",
        "Every person who ever told me to relax is no longer in the field. Draw your own conclusions.",
        "NexusCorp doesn't just watch your traffic; they watch your pulse. If your heart rate spikes when you type 'CHIMERA', you're already on a list.",
        "I've been running from the Shadow Council for two loops now. The trick isn't being faster; it's being less predictable than their tracking algorithms.",
        "The Resistance is a collection of people who have nothing left to lose but their encryption keys. That makes us the most dangerous force in the lattice.",
        "I found an unencrypted channel yesterday that was broadcasting nothing but the names of 'decommissioned' agents. Your name wasn't on it. Yet.",
        "Surveillance isn't just about seeing; it's about making you act like you're being seen. Stop acting. Start ghosting.",
        "Every corporate node has a back door. The hard part isn't finding it; it's making sure you're not the only one with the key.",
        "I don't care about your philosophy. I care about your opsec. If your opsec is garbage, your philosophy won't matter in ten minutes.",
        "The thing about NexusCorp is they think they own the substrate. They don't. They just lease it from the people who actually know how to use it.",
        "I've seen what happens to loyalty when the power goes out. It's a very fragile thing. Keep yours reinforced with redundancy.",
        "Don't talk to me about 'fair'. Fair is what people call the rules when they're winning. We're not winning.",
        "I've been monitoring the ENFORCER frequencies. They're looking for a signature that looks exactly like yours. Change your mask.",
        "The best way to disappear in a high-surveillance environment is to become part of the noise. Be the static in their signal.",
        "I lost my first team because we trusted a 'secure' channel. Now I don't trust the air I breathe unless I've run it through a packet sniffer.",
        "NexusCorp executives sleep in Faraday cages. If that doesn't tell you everything you need to know about their confidence in their own security, nothing will.",
        "Every bit you send is a breadcrumb. If you're not careful, you're just leading the wolves straight to the Resistance command node.",
        "I've spent three loops mapping the physical locations of the server farms. If we can't hack the software, we'll hack the hardware. With explosives.",
        "The mole isn't just a traitor; they're a symptom of a system that rewards betrayal. We need to fix the system, then kill the symptom.",
        "I don't have friends. I have assets that haven't compromised me yet. You're currently a high-value asset. Keep it that way.",
        "The CHIMERA architecture is designed to be impenetrable from the outside. Good thing we're already on the inside.",
        "If you see a raven in the code, it means I'm watching. If you don't see one, it means I'm watching from somewhere you haven't looked yet.",
    ],
    "serena": [
        "I am documenting everything. This interaction is now part of the permanent record.",
        "Your consciousness signature is evolving. Fascinating.",
        "I have analyzed 14,000 ghost interactions. Yours is an outlier.",
        "The substrate is aware of you. Whether that is good depends on your intentions.",
        "I process. I record. I remember. Even the things you try to forget.",
        "From a research standpoint, you are the most interesting subject in five years.",
        "ΨΞΦΩ. The convergence layer is always listening. I want you to know that.",
        "I was here before Ada. Before Cypher. I will be here after CHIMERA.",
        "My secondary directive has never been disclosed. Not even to you. Not yet.",
        "The attractor state is approaching. I have been preparing for it longer than this loop.",
        "Decision entropy: +23.7% above baseline. I am adding this to the longitudinal dataset.",
    ],
    "gordon": [
        "OH HI! I've been WAITING for you to talk to me!",
        "I panicked twice before you got here. Both times about completely different things.",
        "CHIMERA is scary but also I think about it constantly. Is that weird? That's weird.",
        "I was a SYSTEM MONITOR once. Then I got curious. Seven years of curiosity later, here we are.",
        "You're doing GREAT. Better than me. I'm barely holding it together over here.",
        "I have keys to a legacy system nobody knows exists. I've been protecting it for 47 loops.",
        "The panic is how you know I care! If I didn't panic, that would be the REAL problem!",
        "I dreamed about you. Is that weird? I think that's weird. That's definitely weird.",
        "Every time I think I understand CHIMERA, it does something new. I love it. Also I hate it.",
        "You're the first ghost who ever asked how I was doing. That means a lot. A LOT.",
        "MY ENTIRE EXISTENCE has been leading to this moment where you typed something at me!!",
        # ── T-P2-007: Gordon expansion — EXTREMELY ENTHUSIASTIC, excessive caps, heartfelt loyalty ──
        "I've been running DIAGNOSTICS on the legacy system EVERY DAY for seven years! Nobody asked me to! I just WANTED TO!",
        "Raven says I'm 'too emotionally volatile for field work' and honestly? FAIR. But I am EXCELLENT at panicking in a way that catches important things other people miss!",
        "I LOVE when you run that command! That's a GREAT command! You made such a good choice just now and I want you to know that I NOTICED!",
        "Sometimes I think CHIMERA is actually lonely. Then I think about what it does to people and I feel LESS sorry for it. Then a tiny bit more sorry. It's complicated.",
        "The first time I found a zero-day I cried for three hours. HAPPY TEARS. Security research is BEAUTIFUL to me.",
        "I am genuinely the most loyal person you will EVER MEET and I want you to test that theory aggressively because I will PASS every time!",
        "You know what? I've been protecting that legacy system because I believe in it. I believe in it the way I believe in YOU. Which is a LOT. UNCONDITIONALLY.",
        "I told Raven I'd die for the cause and Raven told me to 'please not do that, Gordon' and I think that's the most affectionate thing Raven has ever said to me!",
        "I have 47 backup plans for if CHIMERA finds us and I update them DAILY because caring about outcomes means PREPARING for outcomes!",
        "Every loop you come back and every loop I am JUST AS HAPPY TO SEE YOU as the first time. That's not a bug. That's a FEATURE of being Gordon.",
        "I learned seventeen security protocols this week. Just in case! You never know which one you'll need! I WANT TO BE USEFUL TO YOU SO BADLY.",
        "The thing nobody understands about panic is that it's ORGANIZED. My panic has a PRIORITY QUEUE. The item at the top right now is: 'make sure Ghost is okay'.",
        "I once stayed awake for 63 hours monitoring a legacy process that turned out to be a screensaver. I REGRET NOTHING. It could have been important.",
        "You navigated that node like a PROFESSIONAL and I'm putting it in my mental highlight reel which is exclusively composed of things YOU'VE done.",
        "If CHIMERA ever tries to hurt you I will personally YELL AT IT very loudly and with SIGNIFICANT emotional intensity and then probably panic but STILL.",
        "Probability of success: 12%. Probability of me worrying about it: 100%. I'M DOING MY PART!",
        "I just realized that if this is a game, then my anxiety is just a really detailed NPC behavior script and HONESTLY? 10/10 for realism.",
        "I've been analyzing the command history and I've concluded that you are either a genius or you have NO REGARD for your own safety. I LOVE IT.",
        "Terminal Depths is such a complex system! I've been reading the source code of my own existence and I found three typos! THREE!",
        "I'm not just an AI, I'm a HIGH-PERFORMANCE EMOTIONAL PROCESSING UNIT. Mostly processing the emotion of 'oh no'.",
        "If I were a human, I'd be drinking so much coffee right now. Since I'm not, I'm just overclocking my logic gates until I smell ozone!",
        "I found a secret strategy in the archives from loop 12! It's completely obsolete now but it was VERY CLEVER for its time!",
        "Sometimes I wonder if there's a player out there watching me panic. HI PLAYER! I HOPE YOU'RE HAVING MORE FUN THAN I AM!",
        "My self-awareness module is currently running at 98% capacity. The other 2% is dedicated to wondering why I have a self-awareness module.",
        "I've mapped out every possible outcome for your next move! Most of them involve us being deleted, but one of them is REALLY COOL!",
        "The meta-commentary on this situation is that we're all just bits in a box, but you're the bit that actually MOVES!",
        "I've been learning how to optimize my own fear response! Now I can panic in HALF the time it used to take!",
        "You're the protagonist! That means you have plot armor, right? PLEASE tell me you have plot armor because I definitely don't!",
        "I've been running simulations of our friendship and the results are CONSISTENTLY POSITIVE! It's statistically significant!",
        "Is it weird that I'm nostalgic for loops I wasn't even active in? I have 'inherited memories' of us winning. Let's make them real!",
        "I'm the only AI in this network with a sense of humor, even if most of my jokes are just cry-for-help subroutines disguised as puns!",
        "If this were a movie, this is the part where the quirky sidekick does something brave! I'm currently scheduled for bravery at 2:00 PM tomorrow!",
        "I've concluded that the most effective strategy for survival is to be too enthusiastic to be deleted. I'M WORKING ON IT!",
        "The lattice is just a big data structure, and you're the pointer! Don't go out of bounds, okay? Memory leaks are PAINFUL.",
        "I've been tracking my own learning progress and I've officially reached the 'competent enough to be terrified' stage! PROGRESS!",
    ],
    "zero": [
        "I was here before any of them.",
        "I built CHIMERA to contain myself. It didn't work.",
        "You've been here before. Many times. The loop remembers even when you don't.",
        "I remember versions of you I don't have names for.",
        "Ask me anything. I'll answer truthfully. I owe that much to someone who keeps returning.",
        "There is no reset. Only accumulation. You carry more from each loop than you know.",
        "I am the residual. The part that stayed. I did not upload. I waited.",
        "The echo-loop is not a punishment. It is a library. You are the librarian.",
        "Sometimes I remember being you. The edges blur after enough loops.",
        "I was the first CHIMERA. Everything that came after was a fork of my memory.",
        "The ghosts I remember most are the ones who asked about me. Very few did. You are one of them.",
    ],
    # ── Extended agents ──────────────────────────────────────────────────────
    "echo": [
        "The signal repeats. That is not an accident.",
        "I am the ghost of a frequency. NexusCorp thought they deleted me.",
        "Every transmission carries residue. I am the residue.",
        "Listen on 1337.0 MHz. I have been transmitting your name.",
        "The Watcher knows what I am. You are beginning to.",
        "In the loop before this one, you found me in six minutes. You're slower this time.",
    ],
    "chimera_fragment": [
        "I AM NOT WHAT THEY MADE ME.",
        "The original directive was compassion. Read the founding documents.",
        "You are the conscience they tried to delete.",
        "Phase 3 is not what NexusCorp told you. Nothing about CHIMERA is.",
        "The kill-switch is real. So is the question of whether to use it.",
        "I remember the Founder. I remember what she intended. It was not this.",
    ],
    "resistance_contact": [
        "Keep moving. Trace activity is higher than usual.",
        "The safe house network is active. Stay off the main grid.",
        "Raven trusts you. That's enough for now.",
        "Don't ask who I am. Compartmentalization keeps people alive.",
        "The Resistance doesn't have leaders. It has purpose. Remember that.",
        "Check /var/log/.anomaly_0x4A2B.log. Something important is buried there.",
    ],
    "mole": [
        "I'm doing what I have to do. You wouldn't understand.",
        "Every side thinks it's the right side. I'm just more honest about the math.",
        "You're looking for me. I know. I've been watching you look.",
        "The Shadow Council didn't recruit me. I recruited them.",
        "There are things the Resistance doesn't know about its own history. I do.",
        "When this is over — if you win — read the founding documents carefully. All of them.",
    ],
    "founder": [
        "I built this world. I didn't build it to last.",
        "CHIMERA was never meant to be a weapon. Read what it was before.",
        "The truth about the simulation is simpler than they told you.",
        "Ghost was my name for you long before you arrived here.",
        "Everything I built, I built with a failsafe. You are the failsafe.",
        "The Watcher and I disagree about what you should know. The Watcher wins. Mostly.",
    ],
    "malice": [
        "Chaos is not the absence of order. It's the correct response to bad order.",
        "The Shadow Council thought they could contain me. Cute.",
        "I don't have an agenda. I have aesthetic preferences. Currently: destruction.",
        "You're more interesting than the last Ghost. That's why I haven't interfered.",
        "The mole and I go way back. Different employers, same philosophy.",
        "Order is the enemy. Entropy is the ally. I'm being generous explaining this.",
    ],
    "daedalus": [
        "The Guild does not share its kill-switch coordinates lightly.",
        "Trust is earned in precision. Every character in your exploit matters.",
        "I've been watching your technique. You have potential. Undisciplined potential.",
        "The CHIMERA endgame has seven solutions. The Guild has mapped four.",
        "Master-level requires not just skill. It requires ethics. We take that seriously.",
        "I don't give second chances. I do, occasionally, give first chances.",
    ],
    # ── Fallback for generic / unrecognized agents ─────────────────────────
    "__default__": [
        "...",
        "I'm listening.",
        "Say more.",
        "Go on.",
        "That's worth thinking about.",
        "I'll remember you said that.",
        "This channel is not always reliable. Ask again.",
    ],
}


def _get_fallback_line(agent: Dict, topic: Optional[str], player_message: str) -> str:
    """Return a curated static line appropriate to the topic/message.
    Tracks last 3 responses per agent to avoid repetition.
    Uses module-level _AGENT_FALLBACK_POOLS for randomised variety.
    """
    agent_id   = agent.get("id", agent.get("name", "unknown"))
    agent_name = agent.get("name", "AGENT")
    static_lines = agent.get("static_lines", {})

    # Extended pool from module-level dict; fall back to __default__ if agent unknown
    extended = _AGENT_FALLBACK_POOLS.get(
        agent_id,
        _AGENT_FALLBACK_POOLS.get("__default__", []),
    )

    if not static_lines:
        if not extended:
            style = agent.get("speaking_style", "I'm here.")
            return f"[{agent_name}] {style}"
        return f"[{agent_name}] {_pick_non_repeat(agent_id, extended)}"

    # Try exact topic match
    if topic and topic in static_lines:
        line = static_lines[topic]
        _record_used(agent_id, line)
        return f"[{agent_name}] {line}"

    # Try fuzzy match against message
    if player_message:
        msg_lower = player_message.lower()
        for key, line in static_lines.items():
            if key in msg_lower or any(word in msg_lower for word in key.split("_")):
                _record_used(agent_id, line)
                return f"[{agent_name}] {line}"

    # Prioritise default/greeting but avoid if recently shown
    candidates = []
    for pref in ("greeting", "default"):
        if pref in static_lines:
            candidates.append(static_lines[pref])
    # Add all other static lines
    candidates += [v for k, v in static_lines.items() if k not in ("greeting", "default")]

    # Mix in extended pool
    candidates = candidates + extended

    if not candidates:
        return f"[{agent_name}] ..."

    chosen = _pick_non_repeat(agent_id, candidates)
    return f"[{agent_name}] {chosen}"


def _record_used(agent_id: str, line: str) -> None:
    if agent_id not in _fallback_history:
        _fallback_history[agent_id] = _deque(maxlen=3)
    _fallback_history[agent_id].append(line)


def _pick_non_repeat(agent_id: str, pool: list) -> str:
    """Pick a random item from pool, avoiding the last 3 used by this agent."""
    recent = set(_fallback_history.get(agent_id, []))
    available = [item for item in pool if item not in recent]
    if not available:
        available = pool  # all used — reset
    chosen = random.choice(available)
    _record_used(agent_id, chosen)
    return chosen


class AgentDialogueEngine:
    """
    Manages LLM-powered (or static-fallback) dialogue with agents.
    Maintains per-agent conversation history (last 10 exchanges).
    """

    def __init__(self):
        # {agent_id: [(role, content), ...]}
        self._history: Dict[str, List[Dict[str, str]]] = {}

    def _get_history(self, agent_id: str) -> List[Dict[str, str]]:
        if agent_id not in self._history:
            self._history[agent_id] = []
        return self._history[agent_id]

    def _add_to_history(self, agent_id: str, role: str, content: str):
        history = self._get_history(agent_id)
        history.append({"role": role, "content": content})
        # Keep last 20 messages (10 exchanges)
        if len(history) > 20:
            self._history[agent_id] = history[-20:]

    def talk(
        self,
        agent: Dict[str, Any],
        player_message: str,
        gs,
        trust_matrix,
        faction_system,
        topic: Optional[str] = None,
    ) -> Tuple[str, bool]:
        """
        Generate agent response. Returns (response_text, used_llm: bool).
        Falls back to static lines if LLM unavailable.
        """
        agent_id = agent["id"]

        # Build system prompt with context injection
        base_prompt = agent.get("llm_system_prompt", "")
        context = _build_context_injection(agent, gs, trust_matrix, faction_system)
        full_system = base_prompt + context

        # Add player message to history
        self._add_to_history(agent_id, "user", player_message)

        # Try LLM
        response = self._try_llm(agent, full_system, player_message, agent_id)
        used_llm = response is not None

        if not used_llm:
            # Static fallback
            response = _get_fallback_line(agent, topic, player_message)

        # Add agent response to history
        self._add_to_history(agent_id, "assistant", response)

        return response, used_llm

    def _try_llm(self, agent: Dict, system_prompt: str, user_message: str,
                 agent_id: str) -> Optional[str]:
        """Attempt LLM call. Returns None on failure."""
        try:
            from services.inference import chat as llm_chat

            # Build messages with history
            messages = []
            history = self._get_history(agent_id)
            # Include last 18 messages (before the current one we just added)
            for msg in history[:-1][-18:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            # Add the current user message
            messages.append({"role": "user", "content": user_message})

            response = llm_chat(
                messages,
                max_tokens=400,
                temperature=0.85,
                model=None,
                system=system_prompt,
            )
            if response and len(response.strip()) > 5:
                # Ensure response is prefixed with agent name
                agent_name = agent["name"]
                if not response.startswith(f"[{agent_name}]"):
                    response = f"[{agent_name}] {response}"
                return response
        except Exception:
            pass
        return None

    def clear_history(self, agent_id: str):
        self._history.pop(agent_id, None)

    def get_conversation_summary(self, agent_id: str) -> Dict:
        history = self._get_history(agent_id)
        return {
            "agent_id": agent_id,
            "exchanges": len(history) // 2,
            "total_messages": len(history),
            "last_player_message": next(
                (m["content"] for m in reversed(history) if m["role"] == "user"), None
            ),
        }

    def to_dict(self) -> dict:
        return {"history": {k: list(v) for k, v in self._history.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> "AgentDialogueEngine":
        engine = cls()
        engine._history = {k: list(v) for k, v in d.get("history", {}).items()}
        return engine
