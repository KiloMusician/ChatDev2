"""
app/game_engine/procgen_quests.py — Procedural Quest Generation
================================================================
Generates new quests dynamically based on player state, story beats,
and (optionally) Ollama LLM content.

Two generation modes:
1. TEMPLATE MODE (zero-token): picks from weighted template bank,
   fills variables based on current game state
2. LLM MODE: calls Ollama qwen2.5-coder to generate narrative quests

Quest types generated:
  - RECON:   scan/investigate a specific node
  - HEIST:   extract data from a secured system
  - SOCIAL:  build trust with an agent through interactions
  - PUZZLE:  solve a challenge type (number-theory, graph, etc.)
  - FACTION: complete tasks for a specific faction
  - STORY:   advance the main narrative arc

Usage:
    from app.game_engine.procgen_quests import QuestGenerator
    gen = QuestGenerator()
    quests = gen.generate(game_state, count=3)
    for q in quests:
        print(q['title'], q['objective'])
"""
from __future__ import annotations

import json
import random
import time
import urllib.request
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Quest templates
# ---------------------------------------------------------------------------

QUEST_TEMPLATES = [
    # RECON quests
    {
        "type": "recon",
        "title_tmpl": "Surveillance: {node}",
        "objective_tmpl": "Scan {node} and identify all open services.",
        "command": "scan {node}",
        "xp": 25,
        "faction": "resistance",
        "skill": "networking",
        "nodes": ["node-1", "nexus-gateway", "watcher-relay", "darknet-relay-7"],
        "unlock_after": [],
    },
    {
        "type": "recon",
        "title_tmpl": "Log Extraction: {node}",
        "objective_tmpl": "Access {node} and read the activity logs.",
        "command": "cat /var/log/nexus.log",
        "xp": 20,
        "faction": "resistance",
        "skill": "forensics",
        "nodes": ["node-1", "chimera-control"],
        "unlock_after": [],
    },
    # HEIST quests
    {
        "type": "heist",
        "title_tmpl": "Data Exfil from {node}",
        "objective_tmpl": "Exploit {node} and exfiltrate the payload.",
        "command": "exploit {node}",
        "xp": 40,
        "faction": "shadow_council",
        "skill": "security",
        "nodes": ["nexus-db", "collector-node"],
        "unlock_after": ["root_achieved"],
    },
    {
        "type": "heist",
        "title_tmpl": "Claim {node} for the Network",
        "objective_tmpl": "Claim {node} and add it to your controlled territory.",
        "command": "nodes claim {node}",
        "xp": 35,
        "faction": "resistance",
        "skill": "hacking",
        "nodes": ["node-1", "nexus-gateway", "darknet-relay-7"],
        "unlock_after": [],
    },
    # SOCIAL quests
    {
        "type": "social",
        "title_tmpl": "Build Trust with {agent}",
        "objective_tmpl": "Send 3 messages to {agent} and reach trust level 50.",
        "command": "talk {agent}",
        "xp": 30,
        "faction": "resistance",
        "skill": "social_engineering",
        "agents": ["ada", "raven", "cypher", "gordon", "serena"],
        "unlock_after": [],
    },
    {
        "type": "social",
        "title_tmpl": "OSINT: Profile {agent}",
        "objective_tmpl": "Run OSINT on {agent} and analyze their dossier.",
        "command": "osint {agent}",
        "xp": 25,
        "faction": "watchers_circle",
        "skill": "social_engineering",
        "agents": ["ada", "cypher", "malice", "nova"],
        "unlock_after": ["ada_first_contact"],
    },
    # PUZZLE quests
    {
        "type": "puzzle",
        "title_tmpl": "Cryptographic Challenge #{level}",
        "objective_tmpl": "Solve number-theory puzzle {level} for the Archivist.",
        "command": "number-theory load {level}",
        "xp": 45,
        "faction": "specialist_guild",
        "skill": "cryptography",
        "levels": [1, 2, 3, 4, 5],
        "unlock_after": [],
    },
    {
        "type": "puzzle",
        "title_tmpl": "Graph Theory: Daedalus-7 Assignment",
        "objective_tmpl": "Complete a graph theory challenge assigned by Daedalus-7.",
        "command": "graph-theory load 1",
        "xp": 40,
        "faction": "specialist_guild",
        "skill": "programming",
        "levels": [1, 2, 3, 4],
        "unlock_after": [],
    },
    # FACTION quests
    {
        "type": "faction",
        "title_tmpl": "Resistance Task: Mole Investigation",
        "objective_tmpl": "Find evidence about the Resistance mole. Check /tmp/ and logs.",
        "command": "cat /tmp/.transfer_847b.partial",
        "xp": 50,
        "faction": "resistance",
        "skill": "forensics",
        "unlock_after": ["ada_first_contact"],
    },
    {
        "type": "faction",
        "title_tmpl": "Join the Resistance Network",
        "objective_tmpl": "Formally join the Resistance by gaining 20 reputation.",
        "command": "faction join resistance",
        "xp": 30,
        "faction": "resistance",
        "skill": "social_engineering",
        "unlock_after": [],
    },
    # STORY quests
    {
        "type": "story",
        "title_tmpl": "CHIMERA: Source Discovery",
        "objective_tmpl": "Read all CHIMERA lore and locate the control node.",
        "command": "lore chimera",
        "xp": 35,
        "faction": "anomalous",
        "skill": "terminal",
        "unlock_after": [],
    },
    {
        "type": "story",
        "title_tmpl": "Find ZERO",
        "objective_tmpl": "Explore /opt/library/.basement and read ZERO's message.",
        "command": "basement start",
        "xp": 60,
        "faction": "anomalous",
        "skill": "terminal",
        "unlock_after": [],
    },
]

# ---------------------------------------------------------------------------
# Quest generator
# ---------------------------------------------------------------------------

class QuestGenerator:
    """
    Generates contextually appropriate quests based on player state.

    Uses template-based generation by default (zero-token, deterministic).
    Optionally calls Ollama for narrative enrichment.
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:14b",
        use_llm: bool = False,  # off by default (slow cold start)
    ):
        self._ollama_url = ollama_url
        self._model = model
        self._use_llm = use_llm
        self._generated_ids: set = set()

    def _make_quest_id(self, template: dict, variant: str) -> str:
        return f"procgen_{template['type']}_{variant}_{int(time.time()) % 10000}"

    def _fill_template(self, tmpl: dict, state: dict) -> Optional[dict]:
        """Fill a quest template with game state variables."""
        try:
            node = random.choice(tmpl.get("nodes", ["node-1"]))
            agent = random.choice(tmpl.get("agents", ["ada"]))
            level = random.choice(tmpl.get("levels", [1]))
            variant = node or agent or str(level)

            quest_id = self._make_quest_id(tmpl, variant)
            if quest_id in self._generated_ids:
                return None

            title = tmpl["title_tmpl"].format(node=node, agent=agent, level=level)
            objective = tmpl["objective_tmpl"].format(node=node, agent=agent, level=level)
            command = tmpl["command"].format(node=node, agent=agent, level=level)

            self._generated_ids.add(quest_id)
            return {
                "id": quest_id,
                "title": title,
                "type": tmpl["type"],
                "objective": objective,
                "command_hint": command,
                "xp_reward": tmpl["xp"],
                "faction": tmpl["faction"],
                "skill": tmpl["skill"],
                "generated": True,
                "source": "procgen",
            }
        except (KeyError, IndexError):
            return None

    def _filter_eligible(self, templates: list, state: dict) -> list:
        """Filter templates that are appropriate for the current game state."""
        beats = set(state.get("story_beats", []))
        level = state.get("level", 1)
        eligible = []
        for tmpl in templates:
            unlock = set(tmpl.get("unlock_after", []))
            if unlock and not unlock.issubset(beats):
                continue
            if tmpl["type"] == "heist" and level < 2:
                continue
            eligible.append(tmpl)
        return eligible

    def generate(self, state: dict, count: int = 3) -> List[dict]:
        """Generate `count` contextually relevant quests."""
        eligible = self._filter_eligible(QUEST_TEMPLATES, state)
        if not eligible:
            eligible = QUEST_TEMPLATES  # fallback: all templates

        random.shuffle(eligible)
        quests = []
        attempts = 0
        for tmpl in eligible * 3:  # allow repeat passes
            if len(quests) >= count:
                break
            attempts += 1
            q = self._fill_template(tmpl, state)
            if q:
                quests.append(q)
            if attempts > count * 10:
                break

        return quests

    def generate_llm_quest(self, state: dict) -> Optional[dict]:
        """Use Ollama to generate a fully narrative quest."""
        level = state.get("level", 1)
        beats = state.get("story_beats", [])
        prompt = (
            f"Generate ONE quest for Terminal Depths, a cyberpunk hacking RPG. "
            f"Player: Level {level}, story_beats={beats[:5]}. "
            f"Output ONLY a JSON object: "
            f'{"title": "...", "objective": "...", "type": "recon|heist|social|puzzle|faction|story", "xp_reward": 30, "command_hint": "..."}'
        )
        try:
            payload = json.dumps({
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.8, "num_predict": 150},
            }).encode()
            req = urllib.request.Request(
                f"{self._ollama_url}/api/generate", payload,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            text = data.get("response", "")
            # Extract JSON from response
            import re
            m = re.search(r'\{[^{}]+\}', text)
            if m:
                q = json.loads(m.group())
                q["id"] = f"llm_quest_{int(time.time())}"
                q["generated"] = True
                q["source"] = "llm"
                return q
        except Exception:
            pass
        return None


# ---------------------------------------------------------------------------
# Wire format renderer
# ---------------------------------------------------------------------------

def render_procgen_quests(quests: List[dict]) -> List[dict]:
    """Render generated quests in Terminal Depths wire format."""
    def _sys(s): return {"t": "system", "s": s}
    def _dim(s): return {"t": "dim", "s": s}
    def _ok(s):  return {"t": "success", "s": s}
    def _info(s): return {"t": "info", "s": s}

    out = [_sys("  ═══ GENERATED MISSIONS ═══"), _dim("")]
    for i, q in enumerate(quests, 1):
        badge = {"recon": "🔍", "heist": "💀", "social": "🤝",
                 "puzzle": "🧩", "faction": "⚔", "story": "📖"}.get(q["type"], "•")
        out += [
            _info(f"  {badge} [{q['type'].upper()}] {q['title']}"),
            _dim(f"    {q['objective']}"),
            _dim(f"    → {q['command_hint']}  (+{q['xp_reward']} XP)"),
            _dim(""),
        ]
    if not quests:
        out.append(_dim("  No missions available. Explore more to unlock."))
    return out


if __name__ == "__main__":
    gen = QuestGenerator()
    mock_state = {
        "level": 3,
        "story_beats": ["first_hack", "ada_first_contact", "first_ls"],
    }
    quests = gen.generate(mock_state, count=4)
    for q in render_procgen_quests(quests):
        print(f"[{q['t']}] {q['s']}")
