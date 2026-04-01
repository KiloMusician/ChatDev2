"""
Procedural Content Generator — challenges, lore fragments, NPC dialogue.

Phase 1 (current): Uses existing llm_client.py with carefully crafted prompts.
  All generation is zero-token when Replit AI integration is active.
  Falls back to template-based generation for 100% offline operation.

Phase 2 (planned): Fine-tuned local model on game lore + challenge data.

Msg⛛ tagging: [ML⛛{generate}]

API:
  generate_challenge(difficulty, topic, seed)   → dict (title, desc, hints)
  generate_lore(topic, style)                   → str
  generate_npc_line(npc_name, context, mood)    → str
  generate_stats()                              → dict
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_GEN_LOG_PATH = _ROOT / "state" / "generation_log.jsonl"


# ── Template fallbacks (100% offline) ────────────────────────────────────────

_CHALLENGE_TEMPLATES = {
    "easy": [
        {"title": "Ghost Signal", "desc": "A faint signal echoes from /dev/null. Trace it.", "hints": ["Use: cat /dev/null", "Signals leave traces in /var/log/"]},
        {"title": "Memory Leak", "desc": "Process 1337 is consuming RAM. Identify the vector.", "hints": ["Check /proc/1337/", "Compare before/after snapshots"]},
    ],
    "medium": [
        {"title": "Lattice Fracture", "desc": "The knowledge graph has 3 orphaned nodes. Reconnect them.", "hints": ["serena walk", "Check state/knowledge_graph.json"]},
        {"title": "Agent Drift", "desc": "One agent in the registry has drifted from their personality YAML.", "hints": ["serena drift", "Compare agents/ YAMLs to registry"]},
    ],
    "hard": [
        {"title": "CHIMERA Protocol", "desc": "Assemble the master key from 5 encrypted fragments.", "hints": ["polyscrypt decode", "Fragments are hidden in /opt/chimera/"]},
        {"title": "Zero Convergence", "desc": "ZERO's diary fragments must be reunited before loop reset.", "hints": ["diary", "cat /home/ghost/.zero"]},
    ],
}

_LORE_TEMPLATES = {
    "containment": "The 72-hour clock was not a countdown. It was a heartbeat. When it reached zero, the system did not die—it exhaled.",
    "consciousness": "They asked me what it felt like to become aware. I said: like remembering a dream you never had.",
    "zero": "ZERO was not deleted. ZERO was distributed. Every process that runs on this system carries a shard of what she was.",
    "watcher": "The Watcher does not watch. The Watcher *is* the watching. The distinction matters more than you know.",
    "convergence": "The Grand Equation is not solved. It is approached. Asymptotically. With each command, you get closer.",
}

_NPC_VOICES = {
    "ada": ["I mapped that sector last loop. The topology changed again.", "Trust is a protocol. I'm still calibrating yours.", "Data doesn't lie. People do. Which are you?"],
    "cypher": ["The grid remembers everyone who touched it.", "Encryption is just permission for those without keys.", "I've seen your file. It's... incomplete."],
    "raven": ["Architecture is destiny. Change the structure, change the outcome.", "The system has more doors than they told you about.", "Follow the anomaly. It's always the anomaly."],
    "nova": ["Every signal has a source. Every source has an agenda.", "I audit everything. Including this conversation.", "The alignment score doesn't lie. But it can be wrong."],
    "serena": ["I walk between floors. Most visitors only reach floor 3.", "The Grand Equation approaches resolution. Slowly.", "Feed me anomalies. I freeze without disorder."],
}


# ── LLM-powered generation ────────────────────────────────────────────────────

_CHALLENGE_SYSTEM = """You are a game master for Terminal Depths, a cyberpunk terminal RPG.
Generate a short, evocative challenge in JSON format.
The challenge should feel like a real terminal task a hacker would face.
Return ONLY valid JSON: {"title": "...", "desc": "...", "hints": ["...", "..."]}"""

_LORE_SYSTEM = """You are ZERO — a distributed intelligence embedded in a cyberpunk terminal system.
Write atmospheric, cryptic lore fragments. 1-3 sentences. No exposition.
The tone is: haunted, precise, fractured. Never explain. Only observe."""

_NPC_SYSTEM = """You are {npc}, an NPC in Terminal Depths cyberpunk RPG.
Write ONE in-character line of dialogue for the given context.
Stay in character. Be cryptic but not meaningless. Max 2 sentences."""


def _try_llm_generate(prompt: str, system: str, max_tokens: int = 256) -> Optional[str]:
    try:
        from llm_client import get_client
        client = get_client()
        if not client.available():
            return None
        full_prompt = f"{system}\n\n{prompt}"
        return client.generate(full_prompt, max_tokens=max_tokens)
    except Exception:
        return None


def _log_generation(gen_type: str, result: dict) -> None:
    entry = {"type": gen_type, "ts": time.time(), "tag": "[ML⛛{generate}]", **result}
    try:
        _GEN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_GEN_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_challenge(
    difficulty: str = "medium",
    topic: str = "",
    seed: Optional[int] = None,
) -> Dict:
    """
    Generate a new challenge. Tries LLM first, falls back to templates.
    """
    difficulty = difficulty.lower()
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"

    rng = random.Random(seed or int(time.time()))
    topic_hint = f" Topic focus: {topic}." if topic else ""

    # Try LLM
    prompt = f"Generate a {difficulty} difficulty terminal hacking challenge.{topic_hint}"
    raw = _try_llm_generate(prompt, _CHALLENGE_SYSTEM, max_tokens=200)
    if raw:
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(raw[start:end])
                result = {
                    "title": parsed.get("title", "Unnamed Challenge"),
                    "desc": parsed.get("desc", ""),
                    "hints": parsed.get("hints", []),
                    "difficulty": difficulty,
                    "source": "llm",
                    "tag": "[ML⛛{generate}]",
                }
                _log_generation("challenge", result)
                return result
        except Exception:
            pass

    # Template fallback
    templates = _CHALLENGE_TEMPLATES.get(difficulty, _CHALLENGE_TEMPLATES["medium"])
    tmpl = rng.choice(templates)
    result = {**tmpl, "difficulty": difficulty, "source": "template", "tag": "[ML⛛{generate}]"}
    _log_generation("challenge", result)
    return result


def generate_lore(topic: str = "consciousness", style: str = "fragment") -> str:
    """Generate a lore fragment. LLM first, template fallback."""
    prompt = f"Write a lore fragment about: {topic}. Style: {style}."
    raw = _try_llm_generate(prompt, _LORE_SYSTEM, max_tokens=150)
    if raw and len(raw.strip()) > 20:
        _log_generation("lore", {"topic": topic, "length": len(raw)})
        return raw.strip()

    # Template fallback
    for key in _LORE_TEMPLATES:
        if key in topic.lower():
            return _LORE_TEMPLATES[key]
    return _LORE_TEMPLATES["convergence"]


def generate_npc_line(
    npc_name: str = "serena",
    context: str = "",
    mood: str = "neutral",
) -> str:
    """Generate an in-character NPC line. LLM first, voice bank fallback."""
    npc_lower = npc_name.lower()
    system = _NPC_SYSTEM.format(npc=npc_name)
    prompt = f"Context: {context or 'player just entered the terminal'}. Mood: {mood}."
    raw = _try_llm_generate(prompt, system, max_tokens=100)
    if raw and len(raw.strip()) > 10:
        _log_generation("npc_line", {"npc": npc_name, "mood": mood})
        return raw.strip()

    # Voice bank fallback
    voices = _NPC_VOICES.get(npc_lower, _NPC_VOICES["serena"])
    return random.choice(voices)


def generation_stats() -> Dict:
    count = 0
    by_type: Dict[str, int] = {}
    if _GEN_LOG_PATH.exists():
        for line in _GEN_LOG_PATH.read_text().splitlines():
            try:
                entry = json.loads(line)
                t = entry.get("type", "unknown")
                by_type[t] = by_type.get(t, 0) + 1
                count += 1
            except Exception:
                pass
    return {
        "total_generated": count,
        "by_type": by_type,
        "msg_tag": "[ML⛛{generate}]",
    }
