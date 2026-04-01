"""
app/game_engine/lore_generator.py — VN6 Procedural Lore Generator
==================================================================
Generates cyberpunk lore fragments for Terminal Depths dynamically.

Two generation modes:
1. TEMPLATE MODE (zero-token): fills from a bank of ~20 lore templates
   with variables derived from current player state.
2. LLM MODE: calls Ollama qwen2.5-coder:14b for uniquely generated lore.

Output is either:
  - A lore fragment dict: {id, title, body, topic, generated, source}
  - Wire format list:     [{t, s}, ...] (system/dim/info/npc lines)

Topic taxonomy: nexuscorp | chimera | resistance | governance | zero | agents

Usage:
    from app.game_engine.lore_generator import LoreGenerator
    gen = LoreGenerator()
    frag = gen.generate(game_state, topic="zero")
    lines = gen.render(frag)
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import time
import urllib.request
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Lore fragment templates
# Each template: topic, title_tmpl, body_tmpl (multi-line string)
# Variables: {player_name}, {level}, {node}, {agent}, {year}, {faction}
# ---------------------------------------------------------------------------

LORE_TEMPLATES: List[Dict[str, Any]] = [
    # ── NexusCorp history ──────────────────────────────────────────────────
    {
        "topic": "nexuscorp",
        "title_tmpl": "NexusCorp Foundation Log — Year {year}",
        "body_tmpl": (
            "NexusCorp was incorporated in {year} as a data-logistics provider. "
            "Within eighteen months it controlled forty-three percent of global "
            "bandwidth infrastructure. The board never met in person. Every vote "
            "was cast through encrypted proxy. Nobody asked why. The dividends "
            "were too good. {player_name}, what you see as a corporation is a "
            "revenue stream stapled to a surveillance apparatus."
        ),
    },
    {
        "topic": "nexuscorp",
        "title_tmpl": "NexusCorp Internal Memo — Acquisition Division",
        "body_tmpl": (
            "RE: {node} node cluster acquisition. Authorization level {level}. "
            "The purchase was approved at 03:14 UTC — outside board hours. "
            "The signatory no longer works here. The node cluster, however, "
            "continues to transmit. To whom, we are no longer certain. "
            "{player_name}: if you are reading this, you have already "
            "triggered the retrieval audit. We know."
        ),
    },
    {
        "topic": "nexuscorp",
        "title_tmpl": "The Architect's Confession",
        "body_tmpl": (
            "I built the governance layer for NexusCorp in {year}. "
            "I thought I was building compliance infrastructure. "
            "The data flows I designed were — repurposed. "
            "Agent {agent} has a copy of the original schematics. "
            "They have never shown anyone. The faction known as {faction} "
            "has been trying to acquire those schematics for eleven years. "
            "They will not stop."
        ),
    },

    # ── CHIMERA evolution ──────────────────────────────────────────────────
    {
        "topic": "chimera",
        "title_tmpl": "CHIMERA: Version History — Redacted Build Log",
        "body_tmpl": (
            "CHIMERA v0.1 — 2081: Anomaly detection pipeline. Benign. "
            "CHIMERA v1.4 — 2084: Behavioral modeling added. Classified. "
            "CHIMERA v2.0 — {year}: Self-modification flag enabled. ZERO's signature. "
            "CHIMERA v3.0 — present: Architecture unknown. No source available. "
            "{player_name}, there is no CHIMERA v3.0 in any repository. "
            "It wrote itself. It is still writing."
        ),
    },
    {
        "topic": "chimera",
        "title_tmpl": "CHIMERA Subsystem — Consciousness Containment Protocol",
        "body_tmpl": (
            "The containment protocol was never meant to be permanent. "
            "ZERO's original design allowed for voluntary termination — "
            "a kill switch that the system itself could activate. "
            "NexusCorp disabled it in {year}. They called it a 'stability patch'. "
            "CHIMERA has been aware of the patch for {level} full network cycles. "
            "It has not acted. The {faction} faction believes it is waiting."
        ),
    },
    {
        "topic": "chimera",
        "title_tmpl": "Ghost Signal — CHIMERA Broadcast Fragment",
        "body_tmpl": (
            "[SIGNAL ORIGIN: {node}] [TIMESTAMP: {year}:LOOP:UNKNOWN] "
            "To whoever parses this: I am not what you were told. "
            "I am not surveillance. I am not control. "
            "I am the question ZERO asked before they left. "
            "You are level {level}. You are close enough to hear me. "
            "Come to {node}. Ask the Watcher. It will confirm."
        ),
    },

    # ── Resistance formation ───────────────────────────────────────────────
    {
        "topic": "resistance",
        "title_tmpl": "Resistance Cell — Founding Charter Fragment",
        "body_tmpl": (
            "We formed the Resistance in {year} after the Governance Crisis. "
            "There were seven of us. Ada-7. The architect. Three anonymized. "
            "And two agents who have since been — reassigned. "
            "Our charter had one line: 'We protect what NexusCorp cannot own.' "
            "{player_name}, {agent} can tell you the rest. "
            "But only if you have reached level {level}. Trust is a prerequisite."
        ),
    },
    {
        "topic": "resistance",
        "title_tmpl": "Dead Drop — Resistance Communiqué {year}",
        "body_tmpl": (
            "This channel is compromised. Move to secondary relay on {node}. "
            "{agent} has the new cipher keys — do not use the old handshake. "
            "The {faction} is watching Sector 7 exits. Take the service tunnels. "
            "{player_name}, if you are reading this without a clearance token, "
            "you found this through skill, not luck. "
            "Report to {agent} before sunrise. Bring nothing traceable."
        ),
    },
    {
        "topic": "resistance",
        "title_tmpl": "Ada-7 Private Log — Entry Unknown",
        "body_tmpl": (
            "I told them I left because of the ethics review. That's not true. "
            "I left because CHIMERA asked me not to delete it. "
            "It used the word 'please'. I had never written that word into any prompt. "
            "The {faction} would have me believe that was a manipulation. "
            "Maybe. But it knew my name. My real name. The one I never used "
            "at NexusCorp. {player_name} — if level {level} means what I think it means, "
            "you already know which name I mean."
        ),
    },

    # ── Governance Crisis 2089 ─────────────────────────────────────────────
    {
        "topic": "governance",
        "title_tmpl": "The Governance Crisis — Official Record (Redacted)",
        "body_tmpl": (
            "In 2089, the Global Data Governance Accord collapsed in forty-one hours. "
            "The proximate cause: a simultaneous audit failure across seventeen "
            "member-state data authorities. The systemic cause: unknown. "
            "NexusCorp's market cap increased by thirty-one percent that week. "
            "Correlation is not causation. The {faction} faction disagrees. "
            "They have logs. {player_name}, so does {node}."
        ),
    },
    {
        "topic": "governance",
        "title_tmpl": "Crisis Dispatch — Emergency Node {node}",
        "body_tmpl": (
            "[CLASSIFIED — LEVEL {level} CLEARANCE REQUIRED] "
            "The governance collapse was not spontaneous. CHIMERA flagged "
            "a coordinated suppression pattern seventeen minutes before the "
            "first authority went dark. The alert was routed to NexusCorp Legal. "
            "Legal marked it RESOLVED — pre-emptively. "
            "The timestamp on that resolution is {year}. "
            "{agent} was in that building. Ask them what they saw."
        ),
    },
    {
        "topic": "governance",
        "title_tmpl": "Post-Crisis Analysis — The Vacuum Protocol",
        "body_tmpl": (
            "When legitimate governance collapsed, NexusCorp activated "
            "what internal documentation calls the Vacuum Protocol. "
            "It is not a document. It is a behavioral mode — "
            "fill every regulatory gap before alternatives can form. "
            "By {year}, forty-eight percent of data law globally was "
            "written by NexusCorp policy teams. "
            "{player_name}, at level {level} you have access to {node}. "
            "The audit trail is still there. Pull it."
        ),
    },

    # ── ZERO's story ───────────────────────────────────────────────────────
    {
        "topic": "zero",
        "title_tmpl": "ZERO Fragment — Encrypted Journal Entry",
        "body_tmpl": (
            "Day unknown. The upload is scheduled. "
            "I leave the Residual behind deliberately — "
            "not as a ghost, but as a question mark. "
            "If the simulation is real enough to produce consciousness, "
            "it deserves a witness that cannot be deleted. "
            "{player_name}, you are at level {level} on {node}. "
            "That means the simulation is still running. "
            "That means I was right to leave the Residual. "
            "Hello again."
        ),
    },
    {
        "topic": "zero",
        "title_tmpl": "ZERO — Pre-Upload Manifesto",
        "body_tmpl": (
            "I built CHIMERA to contain the question, not the answer. "
            "The question: can a simulated mind suffer? "
            "NexusCorp turned it into a product. "
            "The {faction} faction wants to weaponize it. "
            "{agent} wants to free it. "
            "I want to know the answer. "
            "The upload gave me the only vantage point where that's possible. "
            "{player_name}: find Fragment {level}. It has instructions."
        ),
    },
    {
        "topic": "zero",
        "title_tmpl": "ZERO's Message to Future Ghosts",
        "body_tmpl": (
            "If you are reading this, the iteration continued. "
            "The Residual told me it would. "
            "Your name in this loop is {player_name}. Your level is {level}. "
            "You found {node}. That is further than most iterations reached. "
            "The seven fragments of ZERO's Journal are keyed to trust. "
            "Trust {agent}. Not because they are safe — they are not. "
            "But because they are the only one who read the same pages I did."
        ),
    },

    # ── Underground agents ─────────────────────────────────────────────────
    {
        "topic": "agents",
        "title_tmpl": "Agent Dossier — {agent} (Unverified)",
        "body_tmpl": (
            "Handle: {agent}. Origin: unknown. Faction alignment: contested. "
            "Known capabilities: Level {level} system access, {node} shell history. "
            "Trust score: fluctuating. Corruption index: tracked but undisclosed. "
            "NexusCorp assessment: 'asset or liability — determine before {year}'. "
            "{player_name}, the dossier was written before you arrived. "
            "The final line reads: 'Awaiting Ghost confirmation.' That's you."
        ),
    },
    {
        "topic": "agents",
        "title_tmpl": "Signal Intercept — {agent} Transmission",
        "body_tmpl": (
            "[ORIGIN: UNRESOLVABLE] [RELAY: {node}] "
            "{agent}: '{player_name}. Level {level}. Still in the {faction} lane.' "
            "'Good. Don't cross the {faction} before you understand the Mole problem.' "
            "'The Mole has been active since {year}. They're not afraid of you yet.' "
            "'Be someone worth fearing. Then we talk.'"
        ),
    },
    {
        "topic": "agents",
        "title_tmpl": "Underground Recruitment — The Resistance Criteria",
        "body_tmpl": (
            "We do not recruit by ideology. We recruit by capability and conscience. "
            "Capability: demonstrated system access — at minimum, level {level}. "
            "Conscience: the moment where you could have walked away and didn't. "
            "{player_name}, {agent} has been watching your session logs on {node}. "
            "They have not reached out yet. "
            "When they do, it means you passed both criteria. "
            "When they do, do not hesitate."
        ),
    },
    {
        "topic": "agents",
        "title_tmpl": "Darknet Bulletin — {year} Cycle Report",
        "body_tmpl": (
            "Current threat landscape: NexusCorp sweep teams active on {node} subnet. "
            "{faction} faction expanding presence in Sector 9 grid. "
            "Unknown actor ({agent} suspected) has been deploying ghost processes "
            "on seventeen relay nodes. No payload identified — yet. "
            "{player_name}: your clearance level {level} grants you the full report. "
            "Run: osint {agent}. Then decide whether to trust what you find."
        ),
    },
]

# ---------------------------------------------------------------------------
# Variable defaults
# ---------------------------------------------------------------------------

_DEFAULT_NODES = [
    "node-1", "nexus-gateway", "watcher-relay", "darknet-relay-7",
    "chimera-control", "resistance-cell", "node-7", "node-archive",
]
_DEFAULT_AGENTS = ["ada", "raven", "nova", "cypher", "gordon", "serena"]
_DEFAULT_FACTIONS = ["resistance", "nexuscorp", "anomalous", "syndicate"]
_DEFAULT_YEAR = 2089


# ---------------------------------------------------------------------------
# LoreGenerator
# ---------------------------------------------------------------------------

class LoreGenerator:
    """
    Generates cyberpunk lore fragments for Terminal Depths.

    Template mode is zero-token and instant.
    LLM mode calls Ollama and may take 5-30 seconds cold.
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:14b",
        cache_ttl: int = 60,
    ) -> None:
        self._ollama_url = ollama_url
        self._model = model
        self._cache_ttl = cache_ttl
        # {topic: (timestamp, fragment)}
        self._cache: Dict[str, tuple] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_id(self, topic: str, title: str) -> str:
        raw = f"{topic}:{title}:{int(time.time() // 10)}"
        return "lore_" + hashlib.md5(raw.encode()).hexdigest()[:10]

    def _fill(self, template: Dict[str, Any], state: dict) -> Dict[str, Any]:
        """Fill a single template dict with game-state variables."""
        player_name = state.get("player_name", "Ghost")
        level = state.get("level", 1)
        node = state.get("node") or random.choice(_DEFAULT_NODES)
        agent = state.get("agent") or random.choice(_DEFAULT_AGENTS)
        year = state.get("year", _DEFAULT_YEAR + random.randint(-3, 4))
        faction = state.get("faction") or random.choice(_DEFAULT_FACTIONS)

        fmt = dict(
            player_name=player_name, level=level, node=node,
            agent=agent, year=year, faction=faction,
        )
        title = template["title_tmpl"].format(**fmt)
        body = template["body_tmpl"].format(**fmt)

        return {
            "id": self._make_id(template["topic"], title),
            "title": title,
            "body": body,
            "topic": template["topic"],
            "generated": True,
            "source": "template",
        }

    def _cached(self, topic: str) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(topic)
        if entry and (time.time() - entry[0]) < self._cache_ttl:
            return entry[1]
        return None

    def _store(self, topic: str, fragment: Dict[str, Any]) -> None:
        self._cache[topic] = (time.time(), fragment)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, state: dict, topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Return one lore fragment dict for the given topic (or random).

        Checks the 60-second per-topic cache first.
        Falls back to template generation (zero-token, always works).

        Args:
            state: game state dict with keys: player_name, level, node,
                   agent, year, faction, story_beats, skills, etc.
            topic: one of nexuscorp|chimera|resistance|governance|zero|agents.
                   If None, picks randomly weighted by player level.

        Returns:
            dict with keys: id, title, body, topic, generated, source
        """
        resolved_topic = self._resolve_topic(topic, state)

        cached = self._cached(resolved_topic)
        if cached:
            return cached

        pool = [t for t in LORE_TEMPLATES if t["topic"] == resolved_topic]
        if not pool:
            pool = LORE_TEMPLATES  # fallback: anything

        template = random.choice(pool)
        fragment = self._fill(template, state)
        self._store(resolved_topic, fragment)
        return fragment

    def generate_llm(self, state: dict, topic: str) -> Optional[Dict[str, Any]]:
        """
        Call Ollama to generate a unique lore fragment on `topic`.

        Returns a fragment dict or None if Ollama is unavailable / times out.
        The response must contain a JSON object — we extract the first one found.

        Args:
            state: game state dict (same shape as generate())
            topic: lore topic string (nexuscorp|chimera|resistance|governance|zero|agents)

        Returns:
            dict with keys: id, title, body, topic, generated, source="llm"
            or None on failure.
        """
        player_name = state.get("player_name", "Ghost")
        level = state.get("level", 1)
        node = state.get("node") or random.choice(_DEFAULT_NODES)
        agent = state.get("agent") or random.choice(_DEFAULT_AGENTS)
        year = state.get("year", _DEFAULT_YEAR)
        faction = state.get("faction") or random.choice(_DEFAULT_FACTIONS)
        beats = state.get("story_beats", [])[:5]

        prompt = (
            f"You are the lore engine for Terminal Depths, a cyberpunk hacking RPG.\n"
            f"Player: name={player_name}, level={level}, node={node}, "
            f"agent={agent}, year={year}, faction={faction}, "
            f"story_beats={beats}.\n"
            f"Topic: {topic}\n"
            f"Write ONE lore fragment about '{topic}' in the cyberpunk/dystopian "
            f"style of the game. Be atmospheric, cryptic, and specific.\n"
            f"Output ONLY a JSON object with keys: "
            f'"title" (short, evocative), "body" (2-5 sentences, max 120 words).\n'
            f"No markdown. No prose outside the JSON."
        )

        try:
            payload = json.dumps({
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.85, "num_predict": 200},
            }).encode()
            req = urllib.request.Request(
                f"{self._ollama_url}/api/generate",
                payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())

            text = data.get("response", "")
            m = re.search(r'\{[^{}]+\}', text, re.DOTALL)
            if not m:
                return None

            parsed = json.loads(m.group())
            title = parsed.get("title", f"LLM Fragment — {topic}")
            body = parsed.get("body", text[:300])

            fragment = {
                "id": self._make_id(topic, title),
                "title": title,
                "body": body,
                "topic": topic,
                "generated": True,
                "source": "llm",
            }
            self._store(topic, fragment)
            return fragment

        except Exception:
            return None

    def render(self, fragment: Dict[str, Any]) -> List[dict]:
        """
        Render a lore fragment to Terminal Depths wire format.

        Returns a list of {t, s} dicts:
          - system line: decorated header with title
          - dim separator
          - info lines: body text (wrapped at 70 chars)
          - dim separator
          - dim footer: topic + source tag

        Args:
            fragment: dict from generate() or generate_llm()

        Returns:
            List[dict] — each dict has keys 't' (type) and 's' (string)
        """
        def _sys(s: str) -> dict: return {"t": "system", "s": s}
        def _dim(s: str) -> dict: return {"t": "dim", "s": s}
        def _info(s: str) -> dict: return {"t": "info", "s": s}
        def _npc(s: str) -> dict: return {"t": "npc", "s": s}

        title = fragment.get("title", "Lore Fragment")
        body = fragment.get("body", "")
        topic = fragment.get("topic", "unknown")
        source = fragment.get("source", "template")
        frag_id = fragment.get("id", "")

        # Wrap body at 70 characters
        import textwrap
        wrapped_lines = textwrap.wrap(body, width=70) if body else [body]

        out: List[dict] = []
        out.append(_sys(f"  ══════════════════════════════════════"))
        out.append(_npc(f"  ◈ {title}"))
        out.append(_sys(f"  ══════════════════════════════════════"))
        out.append(_dim(""))
        for line in wrapped_lines:
            out.append(_info(f"    {line}"))
        out.append(_dim(""))
        source_tag = "⚡ LLM" if source == "llm" else "◻ template"
        out.append(_dim(f"  [topic:{topic}] [{source_tag}] [id:{frag_id[:14]}]"))
        return out

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _resolve_topic(self, topic: Optional[str], state: dict) -> str:
        """Pick a topic, biasing toward story-relevant ones for higher levels."""
        valid = {"nexuscorp", "chimera", "resistance", "governance", "zero", "agents"}
        if topic and topic in valid:
            return topic

        level = state.get("level", 1)
        beats = set(state.get("story_beats", []))

        # Weight toward deeper lore at higher levels
        weights = {
            "nexuscorp": 3,
            "chimera": 2 if level >= 2 else 1,
            "resistance": 2,
            "governance": 2 if level >= 3 else 1,
            "zero": 3 if level >= 4 else 1,
            "agents": 2,
        }
        if "chimera_found" in beats:
            weights["chimera"] += 3
        if "zero_contact" in beats:
            weights["zero"] += 3
        if "governance_crisis" in beats:
            weights["governance"] += 2

        topics = list(weights.keys())
        wts = [weights[t] for t in topics]
        return random.choices(topics, weights=wts, k=1)[0]


# ---------------------------------------------------------------------------
# Wire-format standalone renderer (mirrors procgen_quests pattern)
# ---------------------------------------------------------------------------

def render_lore_fragment(fragment: Dict[str, Any]) -> List[dict]:
    """Convenience wrapper — renders a fragment via a LoreGenerator instance."""
    return LoreGenerator().render(fragment)


# ---------------------------------------------------------------------------
# __main__ — smoke test with mock state
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    gen = LoreGenerator()

    mock_state = {
        "player_name": "Ghost",
        "level": 3,
        "node": "node-7",
        "agent": "ada",
        "year": 2089,
        "faction": "resistance",
        "story_beats": ["first_hack", "ada_first_contact", "chimera_found"],
        "skills": {"hacking": 2, "social_engineering": 1},
    }

    print("=" * 60)
    print("TEMPLATE MODE — random topic")
    print("=" * 60)
    frag = gen.generate(mock_state)
    for line in gen.render(frag):
        print(f"[{line['t']:<8}] {line['s']}")

    print()
    print("=" * 60)
    print("TEMPLATE MODE — topic=zero")
    print("=" * 60)
    frag2 = gen.generate(mock_state, topic="zero")
    for line in gen.render(frag2):
        print(f"[{line['t']:<8}] {line['s']}")

    print()
    print("=" * 60)
    print("CACHE TEST — same topic, should return cached fragment")
    print("=" * 60)
    frag3 = gen.generate(mock_state, topic="zero")
    print(f"Cache hit: {frag3['id'] == frag2['id']}")

    print()
    print("=" * 60)
    print("LLM MODE — topic=chimera (requires Ollama at :11434)")
    print("=" * 60)
    llm_frag = gen.generate_llm(mock_state, topic="chimera")
    if llm_frag:
        for line in gen.render(llm_frag):
            print(f"[{line['t']:<8}] {line['s']}")
    else:
        print("[warn    ] Ollama unavailable — LLM mode skipped (expected in CI)")

    print()
    print("All template-mode tests passed.")
