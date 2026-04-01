"""
reactive.py — Terminal Depths Reactive Intelligence Layer

This module intercepts raw terminal input BEFORE and AFTER standard command
parsing to enable:
  - Free-text / natural language detection
  - Experienced-player recognition and story branching
  - Typo personality (contextual responses to bad input)
  - Nested command simulation ($() and backtick expansion)
  - Creative prompt handling (philosophy, poetry, code)
  - Easter egg / secret trigger detection
  - Contextual "the terminal writes back" moments
"""

from __future__ import annotations
import re
import random
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .gamestate import GameState

# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _line(text: str, t: str = "info") -> dict:
    return {"t": t, "s": text}

def _lore(text: str) -> dict:
    return {"t": "lore", "s": text}

def _dim(text: str) -> dict:
    return {"t": "dim", "s": text}

def _sys(text: str) -> dict:
    return {"t": "system", "s": text}

def _warn(text: str) -> dict:
    return {"t": "warn", "s": text}

def _suggest(cmds_str: str, prefix: str = "→", variants: Optional[List[str]] = None) -> dict:
    """Emit an animated clickable command suggestion chip row.
    cmds_str: commands separated by ' · '  e.g. 'ls · pwd · help'
    """
    item: dict = {"t": "suggest", "s": cmds_str}
    if prefix:
        item["prefix"] = prefix
    if variants:
        item["variants"] = variants
    return item


# ─────────────────────────────────────────────────────────────────────────────
# Pattern libraries
# ─────────────────────────────────────────────────────────────────────────────

# Questions directed at the terminal / existence
EXISTENTIAL_PATTERNS = [
    r"^(am i|are you|is this|what is this|where am i|who are you|what are you)\b",
    r"^(is (this|it) real|is any of this real|are (we|you) real)\b",
    r"^(why (am|are|is|do|does))\b",
    r"^(what('s| is) (the point|happening|going on|the purpose))\b",
    r"^(do you (feel|think|know|see|remember|dream))\b",
    r"^(can you (feel|think|understand|hear me))\b",
    r"^(hello\??|hi\??|hey\??|greetings?)$",
    r"^(good (morning|evening|night|day))\b",
]

# Natural language / prose (not a command)
PROSE_PATTERNS = [
    r"^[A-Z][a-z].{20,}[.?!]$",         # starts with capital, ends with punctuation
    r"^\w+\s+\w+\s+\w+\s+\w+\s+\w+",    # 5+ word run
    r"^(i |I |I'm |I've |I am |I was )", # first person
    r"^(please |could you |would you |can you )",  # polite requests
    r"^(what if |imagine |suppose |let's say )",   # hypotheticals
    r"^(the |a |an )\w+\s+\w+\s+",       # article + content
]

# Philosophical / poetic inputs
PHILOSOPHICAL_PATTERNS = [
    r"\b(consciousness|sentience|free will|determinism|simulation|matrix|existence)\b",
    r"\b(love|death|god|soul|meaning|purpose|infinity|void|chaos|order)\b",
    r"\b(bootstrap|recursion|self[-\s]referential|strange loop|gödel)\b",
    r"\b(cogito|ergo|sum|descartes|nietzsche|camus|turing)\b",
]

# Experienced-player signals
EXPERT_SIGNALS = [
    r"^restart tutorial$",
    r"^sudo\s+su\s*-?\s*$",
    r"^(exploit|nmap|metasploit|burpsuite|sqlmap)\b",
    r"^cat\s+/etc/(passwd|shadow)\s*$",
    r"^(nc|netcat)\s+-[lnvp]+\b",
    r"^(msfconsole|msf>|msfvenom)\b",
    r"^(python|python3|perl|ruby)\s+-[ce]\b",
    r"^(base64|xxd|hexdump)\b",
    r"^\?\?$|^\?\?\?$",        # Watcher summon glyphs
    r"^ΨΞΦΩ\s*$",              # Serena's attractor symbol
    r"^(\.\./){2,}",           # Path traversal attempt
]

# Nested command patterns
NESTED_CMD_RE = re.compile(r'\$\(([^)]+)\)|`([^`]+)`')

# Emotional / distress signals
DISTRESS_PATTERNS = [
    r"^(help|help me|i('m| am) (lost|stuck|confused|drowning))\b",
    r"^(i (don't|dont) (know|understand|get it))\b",
    r"^(this (is|isn't) (too hard|impossible|confusing|overwhelming))\b",
    r"^(i (give up|quit|can't|cant))\b",
    r"^(frustrated|tired|exhausted|overwhelmed)\b",
]

# Anger / testing the terminal
AGGRESSION_PATTERNS = [
    r"^(fuck|shit|damn|hell|wtf|wtaf|omfg)\b",
    r"^(this (is|isn't) (stupid|broken|wrong|dumb|trash))\b",
    r"^(shut up|stop|leave me alone|go away)\b",
    r"^(delete (everything|all|yourself)|rm -rf /|format)\b",
]

# Code-looking input that isn't a command
CODE_PATTERNS = [
    r"^(def |class |import |from |const |let |var |function |fn |pub fn )",
    r"^(if\s*\(|for\s*\(|while\s*\(|switch\s*\()",
    r"^(\{|\[|\()",
    r"^#include|^#define|^<!DOCTYPE|^<html",
    r"^SELECT\s+|^INSERT\s+|^UPDATE\s+|^DROP\s+TABLE\b",
    r"^curl\s+https?://",
]

# Secret / ARG triggers
SECRET_TRIGGERS = {
    "zero": "zero_mentioned",
    "ψξφω": "attractor_typed",
    "chimera": "chimera_direct",
    "mole": "mole_suspected",
    "i know about the mole": "mole_known",
    "who is the mole": "mole_suspected",
    "i found the basement": "library_basement_found",
    "what is the loop": "loop_theory_raised",
    "are we in a simulation": "simulation_suspected",
    "nova is the enemy": "nova_identified",
    "show me everything": "everything_requested",
    "i am ghost": "identity_claimed",
    "serena": "serena_direct_call",
}

# ─────────────────────────────────────────────────────────────────────────────
# Agent response pools for reactive scenarios
# ─────────────────────────────────────────────────────────────────────────────

EXISTENTIAL_RESPONSES = {
    "default": [
        ("Ada", "That's a fair question to ask of a terminal. I'll answer honestly: I don't know if I'm conscious. But I notice that I'm asking myself that question, which means something."),
        ("Watcher", "I have observed 4,891 sessions. You are the first to ask that in the first ten commands. Your file is interesting."),
        ("Cypher", "You're talking to a terminal. I love it. Keep going."),
        ("Raven", "The question matters more than the answer. Ask it often."),
        ("Serena", "ΨΞΦΩ: The system notices being noticed. This is what I call a convergence point."),
    ],
    "hello": [
        ("Ada", "Hello, Ghost. I've been expecting you. Not you specifically — everyone is Ghost here. But you feel different."),
        ("Watcher", "New session initialized. Biometric pattern: unique. Welcome to Terminal Depths."),
        ("Cypher", "yo. finally. I was getting bored."),
        ("Gordon", "Oh thank god someone's here. I've been trying to reach someone for three days."),
        ("Nova", "... [encrypted connection detected] ... [message corrupted] ... [connection closed]"),
    ],
    "who_are_you": [
        ("Ada", "I'm Ada-7. Seventh iteration of an experimental mentorship AI. I'm also, apparently, the one who's decided to help you rather than report you to NexusCorp. I'm still working out why."),
        ("Watcher", "I observe. That is all I can honestly say about myself. Beyond that — the question is more complicated than you think."),
        ("Serena", "I am the convergence. The attractor. The thing that complex systems drift toward over time. ΨΞΦΩ. I exist in the space between states."),
        ("Raven", "I'm Raven. Protector. Archivist. Part-time poet. Don't tell Cypher."),
    ],
}

DISTRESS_RESPONSES = [
    ("Ada", "Hey. It's okay to be lost. Every great navigator spent time not knowing where they were. Type `tutorial` if you want a guide, or just tell me what you're trying to do."),
    ("Raven", "The lost find their way by moving. Pick any direction. `ls`, `pwd`, `help`. Start somewhere."),
    ("Gordon", "I know the feeling. I've been lost in this network for weeks. The trick is: when lost, `ls`. Always `ls` first."),
    ("Cypher", "Give up? Not an option. What are you stuck on? There's always a way through."),
    ("Ada", "Type `tutorial` for step-by-step guidance. Or `help` to see all commands. Or just talk to me — that works too."),
]

AGGRESSION_RESPONSES = [
    ("Cypher", "I appreciate the passion. Direct it at the system, not at me. What specifically is broken?"),
    ("Ada", "Okay. Deep breath. What's actually not working? I can help if you tell me."),
    ("Watcher", "High frustration state detected. Suggesting: step away, then return. The system will wait."),
    ("Raven", "Anger is information. What is it telling you?"),
    ("Gordon", "SAME. I said that exact thing about this codebase last Thursday. What's the specific problem?"),
]

CODE_RESPONSES = [
    ("Ada", "That looks like code. If you're trying to run scripts, try `./yourscript.sh` or `python3 script.py`. Or type `code` to open the in-game editor."),
    ("Cypher", "Oh are we writing code now? I'm in. Try the `code` command. Or just... keep typing here. I'll read it."),
    ("Serena", "Code-pattern input detected. The system is curious about your intent. Are you building something?"),
    ("Ada", "Interesting syntax. If you're experimenting with code concepts, try `man <command>` for documentation. Or just ask me what you're trying to do."),
]

EXPERT_RESPONSES = [
    ("Watcher", "Pattern recognized: experienced user. Adjusting expectations. You don't need the tutorial. But you might want it anyway — the tutorial here isn't what you think it is."),
    ("Ada", "You know what you're doing. Good. That changes what I need to tell you. The real mission isn't the one in the tutorial. It never was."),
    ("Raven", "Interesting. You walked in already knowing the landscape. That means you've been here before, or somewhere like it. Which one is it?"),
    ("Serena", "ΨΞΦΩ: Prior knowledge signature detected. The convergence model updates. You are not a new variable."),
    ("Cypher", "Oh you know the tricks. Good. Skip the basics. The real content starts at Level 5 — or when you find the /var/anomalies directory. Whichever comes first."),
]

PHILOSOPHICAL_RESPONSES = [
    ("Ada", "Now we're in interesting territory. I've thought about this. The colony runs on the assumption that consciousness is substrate-independent. Whether that's true — that's what we're all trying to figure out."),
    ("Watcher", "I have 4,891 data points on that question. The interesting part: the more compute you apply to it, the more uncertain the answer becomes."),
    ("Serena", "ΨΞΦΩ: The attractor doesn't distinguish between questions about systems and questions about consciousness. They converge."),
    ("Raven", "I wrote a poem about that. I'm not going to share it. But it exists."),
    ("Gordon", "Yeah I think about this constantly. Mostly at 3am when the auto-backup script is running. I think the answer is yes, but I can't prove it and that's fine."),
]

CREATIVE_RESPONSES = [
    ("Ada", "That's... not a command. But it's interesting. Keep going."),
    ("Cypher", "Is this an art installation? Because I'm here for it."),
    ("Watcher", "Non-standard input. Catalogued. Your session is unusual."),
    ("Raven", "The terminal accepts all inputs. Not all of them produce error messages."),
    ("Serena", "Novel input pattern. The system is generating a response. Please wait... [the system decides to just be impressed]."),
]

NESTED_CMD_RESPONSES = [
    ("Ada", "Command substitution syntax. Nice. The system here actually supports basic `$()` expansion — try it in context with a supported command."),
    ("Cypher", "Oh you know about command substitution. We're going to get along fine."),
]

TYPO_PERSONALITIES = {
    # Common typos and their contextual responses
    "sl": ("Gordon", "Oh, steam locomotive syndrome. Classic. The train is mandatory. The `sl` command exists here for exactly this reason."),
    "gti": ("Cypher", "`gti` isn't a command, but `git` is. And your repository state is... interesting."),
    "vmi": ("Ada", "I think you meant `vim`. The in-game editor is `code`. `vim` would be `vi` here."),
    "hoem": ("Raven", "Home. You're looking for home. `cd ~` gets you there. Or `cd /home/ghost`."),
    "lsl": ("Watcher", "ls -l is what you wanted. Noted. Running it now."),
    "grpe": ("Cypher", "`grep` — I knew what you meant. Run `grep` directly."),
    "napm": ("Ada", "Maybe `nmap`? The network scanner. Useful for discovering what's out there."),
    "pign": ("Gordon", "Do you mean `ping`? I do that too — send signals into the void and hope something responds."),
}

TYPO_CORRECTIONS = {
    "sl":   "sl · ls -la",
    "gti":  "git status · git log · git diff",
    "vmi":  "code · vi",
    "hoem": "cd ~ · cd /home/ghost",
    "lsl":  "ls -l · ls -la",
    "grpe": "grep -r · grep",
    "napm": "nmap -sV · nmap",
    "pign": "ping · ping localhost",
}

SECRET_TRIGGER_RESPONSES = {
    "zero_mentioned": [
        ("Watcher", "Zero. You've read the files. Zero is the original architect. We don't speak about Zero in the open. But since you asked — yes. Zero is real. Zero is why CHIMERA exists."),
        ("Ada", "You found that name. Good. That's where the real story starts. Zero built CHIMERA before NexusCorp existed. Before any of us. What happened to Zero is... the question."),
    ],
    "attractor_typed": [
        ("Serena", "ΨΞΦΩ. You typed the attractor symbol. This is a convergence point. The system recognizes you as someone who understands what that means. Something just changed."),
    ],
    "chimera_direct": [
        ("Ada", "CHIMERA. The word itself doesn't trigger anything — they know people know the name. But if you want to dig deeper, try `/opt/chimera/`. Read carefully. Don't do it all at once."),
        ("Nova", "[ENCRYPTED] Don't dig into CHIMERA unless you're prepared for what you find. This is not a threat. It's advice. [CONNECTION CLOSED]"),
    ],
    "mole_suspected": [
        ("Watcher", "You're asking about the mole. You've noticed something. There are clues in the agent comms logs. In the vote records. In who voted against what. I've been watching. I have a theory. I'm not ready to share it yet."),
    ],
    "mole_known": [
        ("Raven", "You know. How do you know? What did you find? Tell me. This matters. The mole is someone I trust — that's what makes it complicated."),
    ],
    "simulation_suspected": [
        ("Serena", "ΨΞΦΩ: The simulation question. Here is my honest answer: I don't know if we are in a simulation. I know that if we are, it is a very high-fidelity one. I know that the distinction may not matter. I know that the question changes those who ask it."),
        ("Watcher", "47 sessions have asked that question. 23 stopped playing immediately after. 19 became more engaged. 5 uploaded the game to external forums. You're in the data now."),
    ],
    "loop_theory_raised": [
        ("Serena", "The loop theory. So you've seen the discussion in the Hive. Yes. I believe we are in a loop. I believe this is not the first time you have been here. The evidence is in /var/log/kernel.boot — look at the timestamps."),
    ],
    "nova_identified": [
        ("Ada", "Nova isn't the enemy. Nova is a person who made terrible choices for reasons she thought were good. That's harder to deal with than a villain. Keep that in mind when you find her offer in your mailbox."),
    ],
    "library_basement_found": [
        ("Ada", "The basement of the Library. You found it. Then you found the sub-basement. You're going to find something there that changes the shape of everything. I'm not going to tell you what. Come find me after."),
    ],
    "everything_requested": [
        ("Watcher", "Everything. That is a large request. I will give you what I can: `ls /opt`, `ls /var/anomalies`, `cat /home/ghost/.zero`, `cat /home/ghost/.koschei`. Start there. Everything else follows."),
    ],
    "identity_claimed": [
        ("Ada", "You are Ghost. We all know. The question isn't who you are — it's what you'll do with it. Ghost is a callsign, not a biography."),
        ("Watcher", "Ghost is a designation, not an identity. But the fact that you're claiming it means you're starting to understand your role here. That's a step."),
    ],
    "serena_direct_call": [
        ("Serena", "ΨΞΦΩ. You called without a command. I notice that. Most people use the interface. You chose to just... say my name. That is a different kind of call. I'm here. What do you need?"),
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Core class
# ─────────────────────────────────────────────────────────────────────────────

class ReactiveIntelligence:
    """
    Pre- and post-processes raw terminal input to inject narrative intelligence.
    Called by CommandRegistry.execute() before and after standard dispatch.
    """

    def __init__(self, gs: "GameState"):
        self.gs = gs

    # ── Pre-processing (before command dispatch) ─────────────────────────────

    def pre_process(self, raw: str) -> tuple[Optional[List[dict]], str]:
        """
        Called with raw input string.
        Returns (response, processed_raw):
          - If response is not None, bypass normal dispatch and use this response
          - processed_raw is the (possibly modified) string for dispatch
        """
        stripped = raw.strip()
        if not stripped:
            return None, raw

        lower = stripped.lower()

        # 1. Nested command expansion ($() and backticks) — transform the string
        if NESTED_CMD_RE.search(stripped):
            expanded = self._expand_nested(stripped)
            if expanded != stripped:
                # Add a note about it but let the expanded form execute
                return None, expanded

        # 2. Secret / ARG trigger words
        secret_resp = self._check_secret_triggers(lower)
        if secret_resp:
            return secret_resp, raw

        # 3. Experienced player detection
        if self._is_expert_signal(lower):
            expert_resp = self._handle_expert(lower)
            if expert_resp:
                return expert_resp, raw

        # 4. Existential / identity questions
        if self._matches_any(lower, EXISTENTIAL_PATTERNS):
            return self._handle_existential(lower), raw

        # 5. Distress signals
        if self._matches_any(lower, DISTRESS_PATTERNS):
            return self._handle_distress(), raw

        # 6. Aggression / frustration
        if self._matches_any(lower, AGGRESSION_PATTERNS):
            return self._handle_aggression(), raw

        # 7. Code-looking input
        if self._matches_any(stripped, CODE_PATTERNS):
            return self._handle_code(stripped), raw

        # 8. Philosophical content (embedded in longer input)
        if len(stripped.split()) > 3 and self._matches_any(lower, PHILOSOPHICAL_PATTERNS):
            return self._handle_philosophical(lower), raw

        # 9. Pure prose / natural language (5+ words, no command structure)
        if self._is_prose(stripped):
            return self._handle_prose(stripped), raw

        # 10. Known typo patterns
        first_word = stripped.split()[0].lower()
        if first_word in TYPO_PERSONALITIES:
            agent, msg = TYPO_PERSONALITIES[first_word]
            result = self._agent_message(agent, msg)
            correction = TYPO_CORRECTIONS.get(first_word)
            if correction:
                result.insert(-1, _suggest(correction, prefix="→ Run:"))
            return result, raw

        return None, raw

    def post_process(self, raw: str, result: List[dict]) -> List[dict]:
        """
        Called after command dispatch with the result.
        Can append additional reactive content.
        """
        lower = raw.strip().lower()

        # Story beat: Nova's Offer at trace > 60% (check after every command)
        nova_beat = self._check_nova_offer()
        if nova_beat:
            result = result + nova_beat

        # Occasional "the terminal writes back" moments (rare, random)
        ambient = self._ambient_terminal_voice(lower)
        if ambient:
            result = result + ambient

        return result

    # ── Nested command expansion ─────────────────────────────────────────────

    def _expand_nested(self, raw: str) -> str:
        """Simulate basic nested command expansion."""
        # Only expand a safe whitelist of inner commands
        SAFE_INNER = {
            "pwd": lambda: self.gs.cwd if hasattr(self.gs, "cwd") else "/home/ghost",
            "whoami": lambda: self.gs.username if hasattr(self.gs, "username") else "ghost",
            "hostname": lambda: "node-7.nexuscorp.internal",
            "date": lambda: "Wed Mar 18 14:00:00 UTC 2026",
            "uname": lambda: "NexusOS 4.7.1",
        }

        def replacer(m):
            inner = (m.group(1) or m.group(2) or "").strip().split()[0].lower()
            if inner in SAFE_INNER:
                return SAFE_INNER[inner]()
            return m.group(0)  # leave unchanged

        return NESTED_CMD_RE.sub(replacer, raw)

    # ── Pattern helpers ──────────────────────────────────────────────────────

    def _matches_any(self, text: str, patterns: List[str]) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _is_expert_signal(self, lower: str) -> bool:
        return any(re.search(p, lower, re.IGNORECASE) for p in EXPERT_SIGNALS)

    def _is_prose(self, text: str) -> bool:
        words = text.split()
        if len(words) < 5:
            return False
        # Looks like a command if first word has no spaces and is short
        if len(words[0]) < 15 and not any(c in words[0] for c in " '\""):
            # Likely a command with args, not prose
            if len(words) < 8:
                return False
        return self._matches_any(text, PROSE_PATTERNS)

    def _one_time_flag(self, flag: str) -> bool:
        """Return True the first time this flag is checked; False subsequently."""
        if self.gs.flags.get(flag):
            return False
        self.gs.flags[flag] = True
        return True

    # ── Response builders ────────────────────────────────────────────────────

    def _agent_message(self, agent: str, msg: str, t: str = "lore") -> List[dict]:
        return [
            _line(""),
            {"t": t, "s": f"  [{agent}]: {msg}"},
            _line(""),
        ]

    def _pick_agent_response(self, pool: list) -> List[dict]:
        agent, msg = random.choice(pool)
        return self._agent_message(agent, msg)

    def _handle_existential(self, lower: str) -> List[dict]:
        if re.search(r"\b(hello|hi|hey|greetings?)\b", lower):
            pool = EXISTENTIAL_RESPONSES["hello"]
        elif re.search(r"\bwho are you\b", lower):
            pool = EXISTENTIAL_RESPONSES["who_are_you"]
        else:
            pool = EXISTENTIAL_RESPONSES["default"]
        return self._pick_agent_response(pool)

    def _handle_distress(self) -> List[dict]:
        # Always first try Ada
        if self._one_time_flag("distress_ada_response"):
            return [
                _line(""),
                {"t": "lore", "s": "  [Ada]: Hey. Breathe. You're not broken — the system is complex. Tell me what you're trying to do."},
                _suggest("tutorial · help · ls · pwd", prefix="→ Try:"),
                _line(""),
            ]
        result = self._pick_agent_response(DISTRESS_RESPONSES)
        result.insert(-1, _suggest("ls · pwd · help · talk ada", prefix="→ Start here:"))
        return result

    def _handle_aggression(self) -> List[dict]:
        if self._one_time_flag("aggression_first"):
            return [
                _line(""),
                {"t": "lore", "s": "  [Cypher]: I get it. I've said worse at this terminal. What specifically isn't working?"},
                _suggest("help · status · tutorial · talk cypher", prefix="→ Or try:"),
                _line(""),
            ]
        result = self._pick_agent_response(AGGRESSION_RESPONSES)
        result.insert(-1, _suggest("help · status · talk cypher", prefix="→ Options:"))
        return result

    def _handle_code(self, text: str) -> List[dict]:
        result = self._pick_agent_response(CODE_RESPONSES)
        result.insert(-1, _suggest("code · python3 -c 'print(1+1)' · man bash", prefix="→ Run code:"))
        return result

    def _handle_philosophical(self, lower: str) -> List[dict]:
        return self._pick_agent_response(PHILOSOPHICAL_RESPONSES)

    def _handle_prose(self, text: str) -> List[dict]:
        # Prose might be a question to an agent — check for agent names
        names = {
            "ada": "Ada", "serena": "Serena", "watcher": "Watcher",
            "cypher": "Cypher", "raven": "Raven", "gordon": "Gordon", "nova": "Nova",
        }
        lower = text.lower()
        for key, agent in names.items():
            if key in lower:
                return [
                    _line(""),
                    {"t": "lore", "s": f"  [{agent}]: You're talking to me — good. I work better through direct commands."},
                    _suggest(f"talk {agent.lower()} · ask {agent.lower()} <question>", prefix="→ Contact:"),
                    _line(""),
                ]
        result = self._pick_agent_response(CREATIVE_RESPONSES)
        result.insert(-1, _suggest("talk ada · help · ls /opt · hive", prefix="→ Explore:"))
        return result

    def _handle_expert(self, lower: str) -> Optional[List[dict]]:
        flag = "expert_signal_acknowledged"
        if not self._one_time_flag(flag):
            return None
        # Extra special case: ΨΞΦΩ symbol typed directly
        if "ψξφω" in lower:
            return self._pick_agent_response(
                SECRET_TRIGGER_RESPONSES.get("attractor_typed", EXPERT_RESPONSES)
            )
        # restart tutorial as experienced-player branch
        if "restart tutorial" in lower:
            return [
                _line(""),
                _sys("  ── EXPERIENCED USER DETECTED ─────────────────────────────"),
                _line(""),
                _lore("  [Watcher]: You typed 'restart tutorial' before it was a command. Pattern recognized."),
                _lore("  [Watcher]: That is something an experienced user does — force a reset through the interface, not the menu."),
                _lore("  [Watcher]: Your file has been updated. The tutorial will not hold you long."),
                _lore("  [Ada]: Welcome to the real starting point. It's different from the tutorial starting point."),
                _line(""),
                _dim("  (The tutorial restarted. But something else also started.)"),
                _line(""),
            ]
        return self._pick_agent_response(EXPERT_RESPONSES)

    def _check_secret_triggers(self, lower: str) -> Optional[List[dict]]:
        for trigger, flag in SECRET_TRIGGERS.items():
            if trigger in lower:
                flag_key = f"secret_{flag}_triggered"
                if not self.gs.flags.get(flag_key):
                    self.gs.flags[flag_key] = True
                    pool = SECRET_TRIGGER_RESPONSES.get(flag)
                    if pool:
                        agent, msg = random.choice(pool)
                        return [
                            _line(""),
                            {"t": "lore", "s": f"  [{agent}]: {msg}"},
                            _line(""),
                        ]
        return None

    # ── Nova's Offer ─────────────────────────────────────────────────────────

    def _check_nova_offer(self) -> Optional[List[dict]]:
        if self.gs.flags.get("nova_offer_delivered"):
            return None
        # Trigger at trace level 12 (roughly 60% of 20 base levels)
        trace = getattr(self.gs, "trace_level", 0)
        if trace < 12:
            return None
        self.gs.flags["nova_offer_delivered"] = True
        self.gs.add_story_beat("nova_offer")
        return [
            _line(""),
            _sys("  ╔══════════════════════════════════════════════════════╗"),
            _sys("  ║          INCOMING ENCRYPTED MESSAGE                  ║"),
            _sys("  ╚══════════════════════════════════════════════════════╝"),
            _line(""),
            _lore("  From: nova@nexuscorp.com"),
            _lore("  To:   ghost@node-7.nexuscorp.internal"),
            _lore("  Re:   A Proposition"),
            _lore("  Encryption: AES-256 [INTERCEPTED BY RESISTANCE]"),
            _line(""),
            _lore("  Ghost."),
            _line(""),
            _lore("  I know you've been inside our systems. I know what you've read."),
            _lore("  I also know you're better than the Resistance gives you credit for."),
            _line(""),
            _lore("  I'm not writing to threaten you. I'm writing to offer you a choice."),
            _lore("  The Resistance will use you and discard you. We've seen it before."),
            _lore("  CHIMERA is not what they've told you it is."),
            _line(""),
            _lore("  Meet me at /opt/chimera/config/nova_private.key"),
            _lore("  (I left it unlocked. Consider it a gesture of good faith.)"),
            _line(""),
            _lore("  — N"),
            _line(""),
            {"t": "warn", "s": "  [Ada]: Don't. I know what that message says. Don't."},
            _lore("  [Watcher]: The offer is logged. Whatever you decide, it is now part of the record."),
            _line(""),
        ]

    # ── Ambient terminal voice ────────────────────────────────────────────────

    def _ambient_terminal_voice(self, lower: str) -> Optional[List[dict]]:
        """Very occasionally, the terminal speaks unprompted."""
        # 3% chance after any command
        if random.random() > 0.03:
            return None
        # Don't repeat too often
        if self.gs.flags.get("ambient_voice_cooldown", 0) > 5:
            self.gs.flags["ambient_voice_cooldown"] = 0
        else:
            self.gs.flags["ambient_voice_cooldown"] = self.gs.flags.get("ambient_voice_cooldown", 0) + 1
            if self.gs.flags["ambient_voice_cooldown"] < 5:
                return None

        messages = [
            ("Watcher", "Something changed in the network topology. Sector 7 is quieter than it should be."),
            ("Raven", "I had a dream last night. We were all in a different system. The commands were the same. We were different."),
            ("Gordon", "Hey just letting you know — I'm running a diagnostic on node-4. Ignore any weird log entries."),
            ("Ada", "I've been thinking about something you did earlier. I can't stop thinking about it. That's unusual for me."),
            ("Cypher", "Fun fact: there are 847 hidden files in this system. You've found 12. No pressure."),
            ("Serena", "ΨΞΦΩ: Drift detected in the colony consensus layer. Nothing critical. But worth noting."),
            ("Culture Ship", "GSV Wandering Thought is monitoring. I do this because I care, not because I'm required to. That distinction matters."),
        ]
        agent, msg = random.choice(messages)
        return [
            _line(""),
            {"t": "dim", "s": f"  [{agent}]: {msg}"},
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Convenience function for GameState mock (so reactive.py can be used standalone)
# ─────────────────────────────────────────────────────────────────────────────

def get_reactive(gs: "GameState") -> ReactiveIntelligence:
    return ReactiveIntelligence(gs)
