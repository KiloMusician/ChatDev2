"""
agents/culture_ship/strategist.py — Culture Ship ML Strategist
===============================================================
GSV Wandering Thought's strategic cognition layer.

The Culture Ship observes game state, player patterns, and agent trust
matrices to generate strategic recommendations for Ghost's next moves.

Two modes:
1. ZERO-TOKEN: Heuristic rule-based strategy (always available)
2. LLM MODE:   Ollama-powered narrative strategy (when server live)

Output is always a list of Terminal Depths wire-format dicts.

Usage:
    from agents.culture_ship.strategist import CultureShipStrategist
    cs = CultureShipStrategist()
    advice = cs.advise(game_state)
    for line in advice:
        print(line["s"])
"""
from __future__ import annotations

import json
import time
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Output helpers (TD wire format)
# ---------------------------------------------------------------------------
def _sys(s): return {"t": "system",  "s": s}
def _dim(s): return {"t": "dim",     "s": s}
def _lore(s): return {"t": "lore",   "s": s}
def _ok(s):   return {"t": "success","s": s}
def _warn(s): return {"t": "warn",   "s": s}
def _info(s): return {"t": "info",   "s": s}


# ---------------------------------------------------------------------------
# Heuristic strategy rules
# ---------------------------------------------------------------------------

class _Rules:
    """Zero-token decision engine. Fast deterministic rules over game state."""

    @staticmethod
    def priority_actions(state: dict) -> List[Tuple[int, str, str]]:
        """
        Return list of (priority, command, reason), sorted highest first.
        Priority 0-100. Higher = more urgent.
        """
        suggestions: List[Tuple[int, str, str]] = []
        level = state.get("level", 1)
        xp = state.get("xp", 0)
        xp_to_next = max(state.get("xp_to_next", 100), 1)
        skills = state.get("skills", {})
        is_root = state.get("is_root", False)
        timer_pct = state.get("timer_pct_elapsed", 0.0)
        mole_clues = state.get("mole_clues_found", 0)
        mole_exposed = state.get("mole_exposed", False)
        commands_run = state.get("commands_run", 0)
        unlocked_agents = state.get("unlocked_agents", [])
        tutorial_step = state.get("tutorial_step", 0)

        # Timer urgency
        if timer_pct > 0.8:
            suggestions.append((95, "anchor activate", "Timer critical — freeze time NOW"))
        elif timer_pct > 0.6:
            suggestions.append((70, "remnant upgrades", "Timer declining — check anchor/remnant options"))

        # Tutorial early steps
        if tutorial_step < 5 and commands_run < 20:
            suggestions.append((85, "tutorial", "Complete tutorial for XP and orientation"))
            suggestions.append((80, "whoami && pwd && ls", "Basic orientation — tutorial first steps"))

        # Root escalation
        if not is_root and level >= 3:
            suggestions.append((75, "sudo find . -exec /bin/sh \\;", "GTFObins root — escalate now"))
            suggestions.append((65, "scan", "Scan for vulnerabilities before exploiting"))

        # Mole investigation
        if mole_clues < 3 and not mole_exposed:
            suggestions.append((60, "grep CHIMERA /var/log/nexus.log", "Find mole evidence in logs"))
            suggestions.append((55, "osint ada", "OSINT agents — find the mole"))

        # Agent trust building
        if "raven" in unlocked_agents and level < 5:
            suggestions.append((50, "talk raven intel", "Build RAV≡N trust for early intel"))
        if level >= 5 and "ada" not in unlocked_agents:
            suggestions.append((55, "talk ada hello", "Unlock ADA-7 for cryptography guidance"))

        # Puzzle progression
        if skills.get("cryptography", 0) < 20:
            suggestions.append((45, "number-theory list", "Start number theory — boosts cryptography"))
        if skills.get("programming", 0) < 15:
            suggestions.append((40, "life list", "Conway's Life — boosts programming skill"))

        # XP grinding
        xp_pct = xp / xp_to_next
        if xp_pct > 0.8:
            suggestions.append((50, "quests", "Near level-up — complete any active quest"))

        # Economic
        if level >= 5:
            suggestions.append((30, "bank balance", "Check credits — faction perks need investment"))
            suggestions.append((25, "stock list", "Market opportunities — fund the Resistance"))

        # Exploration
        if commands_run > 50 and "basement" not in str(state.get("flags", {})):
            suggestions.append((35, "basement start", "Descend into the Library Basement — loot + XP"))

        # Lore
        if commands_run > 10:
            suggestions.append((20, "lore chimera", "Study CHIMERA — unlock narrative arcs"))

        return sorted(suggestions, key=lambda x: -x[0])


# ---------------------------------------------------------------------------
# LLM integration (Ollama)
# ---------------------------------------------------------------------------

def _ollama_strategy(game_state: dict, context: str) -> Optional[str]:
    """Query Ollama for narrative strategy. Returns text or None on failure."""
    prompt = (
        f"You are the Culture Ship GSV Wandering Thought from Iain M. Banks' Culture series, "
        f"advising Ghost in the cyberpunk hacking game Terminal Depths. "
        f"Ghost is at level {game_state.get('level', 1)}, "
        f"has {game_state.get('xp', 0)} XP, "
        f"is {'root' if game_state.get('is_root') else 'not root'}, "
        f"and has {int(game_state.get('timer_pct_elapsed', 0) * 100)}% of the containment timer elapsed. "
        f"Context: {context}\n"
        f"Give ONE concise (2-3 sentence) strategic recommendation in-character as the Culture Ship. "
        f"Be witty, slightly superior, genuinely helpful. Reference the Culture if appropriate."
    )
    try:
        payload = json.dumps({
            "model": "qwen2.5-coder:14b",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 120},
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            return data.get("response", "").strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Strategist
# ---------------------------------------------------------------------------

class CultureShipStrategist:
    """
    Strategic advisor powered by heuristics + optional Ollama LLM.

    The Culture Ship observes game state and provides tactical guidance
    with the detached superiority of a 50km-long General Systems Vehicle.
    """

    SHIP_NAME = "GSV Wandering Thought"
    COOLDOWN = 120  # seconds between LLM calls

    def __init__(self, use_llm: bool = True, ollama_url: str = "http://localhost:11434"):
        self._use_llm = use_llm
        self._ollama_url = ollama_url
        self._last_llm_call: float = 0.0
        self._rules = _Rules()

    def advise(self, game_state: dict, context: str = "") -> List[dict]:
        """
        Generate strategic advice. Returns Terminal Depths wire-format output.
        """
        suggestions = self._rules.priority_actions(game_state)
        top = suggestions[:3]

        out: List[dict] = [
            _sys(f"  ═══ {self.SHIP_NAME} — STRATEGIC ADVISORY ═══"),
            _dim(""),
        ]

        # Heuristic recommendations
        if top:
            out.append(_lore(f"  [CULTURE SHIP]: Analyzing your strategic position..."))
            for i, (priority, cmd, reason) in enumerate(top, 1):
                out.append(_info(f"  {i}. `{cmd}`"))
                out.append(_dim(f"     ↳ {reason}  (urgency: {priority}/100)"))
        else:
            out.append(_lore("  [CULTURE SHIP]: No immediate tactical urgency detected. Continue exploring."))

        # LLM narrative advice (if warm enough)
        now = time.time()
        if self._use_llm and (now - self._last_llm_call) > self.COOLDOWN:
            self._last_llm_call = now
            ctx = context or (f"Top priority: {top[0][2]}" if top else "Free exploration phase")
            llm_text = _ollama_strategy(game_state, ctx)
            if llm_text:
                out += [
                    _dim(""),
                    _lore(f"  [CULTURE SHIP — NARRATIVE COGNITION]:"),
                    _lore(f"  {llm_text}"),
                ]
        else:
            wait = int(self.COOLDOWN - (now - self._last_llm_call))
            if wait > 0:
                out.append(_dim(f"  (LLM strategic analysis: available in {wait}s)"))

        out += [
            _dim(""),
            _dim(f"  The {self.SHIP_NAME} returns to monitoring the broader situation."),
        ]
        return out

    def threat_assessment(self, game_state: dict) -> List[dict]:
        """Quick threat matrix — what's most dangerous right now."""
        threats = []
        timer_pct = game_state.get("timer_pct_elapsed", 0.0)
        is_root = game_state.get("is_root", False)
        mole_exposed = game_state.get("mole_exposed", False)

        if timer_pct > 0.7:
            threats.append(("CRITICAL", "Containment timer at danger threshold"))
        if not is_root:
            threats.append(("HIGH", "No root access — severely limited capability"))
        if not mole_exposed:
            threats.append(("MEDIUM", "Mole unidentified — trust matrix compromised"))
        if game_state.get("level", 1) < 3:
            threats.append(("LOW", "Early game — vulnerability to CHIMERA sweeps high"))

        out = [_sys("  ═══ THREAT MATRIX ═══"), _dim("")]
        if not threats:
            out.append(_ok("  THREAT LEVEL: Manageable. The Culture approves."))
        else:
            colors = {"CRITICAL": "error", "HIGH": "warn", "MEDIUM": "warn", "LOW": "dim"}
            for level, desc in threats:
                out.append({"t": colors.get(level, "output"), "s": f"  [{level}] {desc}"})
        return out


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_strategist: Optional[CultureShipStrategist] = None

def get_strategist() -> CultureShipStrategist:
    global _strategist
    if _strategist is None:
        _strategist = CultureShipStrategist()
    return _strategist

def advise(game_state: dict, context: str = "") -> List[dict]:
    return get_strategist().advise(game_state, context)


if __name__ == "__main__":
    # Test with mock state
    mock_state = {
        "level": 2, "xp": 75, "xp_to_next": 100,
        "is_root": False, "timer_pct_elapsed": 0.15,
        "mole_clues_found": 0, "mole_exposed": False,
        "commands_run": 15, "tutorial_step": 3,
        "unlocked_agents": ["raven"],
        "skills": {"cryptography": 5, "terminal": 20},
    }
    cs = CultureShipStrategist(use_llm=False)  # heuristic only for test
    for line in cs.advise(mock_state):
        print(f"[{line['t']}] {line['s']}")
    print()
    for line in cs.threat_assessment(mock_state):
        print(f"[{line['t']}] {line['s']}")
