"""
agent_base.py — Base class and personality schema for the 71-agent system.

Every agent in the DevMentor / Terminal Depths ecosystem inherits from
AgentBase and is configured via a companion AgentPersonality dataclass
loaded from a YAML file.

Surface awareness:
  Agents are tagged with which surfaces they run on:
    replit | vscode | docker | obsidian | github_ci | game | all
  The orchestrator uses this to skip agents whose surface isn't active.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


LOG = logging.getLogger("agents")


# ──────────────────────────────────────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────────────────────────────────────

class AgentStatus(str, Enum):
    IDLE     = "idle"
    RUNNING  = "running"
    BLOCKED  = "blocked"
    DONE     = "done"
    ERROR    = "error"


class AgentTier(str, Enum):
    """Execution priority / resource tier."""
    CRITICAL  = "critical"   # always-on core agents
    HIGH      = "high"       # run on every cycle
    MEDIUM    = "medium"     # run every N cycles
    LOW       = "low"        # background / on-demand
    DORMANT   = "dormant"    # waiting for unlock condition


# ──────────────────────────────────────────────────────────────────────────────
# Personality schema (loaded from YAML)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentPersonality:
    """
    Declarative profile for a single agent.
    Loaded from agents/personalities/<name>.yaml.
    """
    # Identity
    name:        str
    codename:    str
    role:        str
    faction:     str                   = "UNALIGNED"
    tier:        str                   = AgentTier.MEDIUM.value

    # Capabilities
    skills:      List[str]            = field(default_factory=list)
    surfaces:    List[str]            = field(default_factory=lambda: ["all"])

    # Behavior
    prompt_prefix: str                = ""
    system_prompt: str                = ""
    temperature:   float              = 0.7
    max_tokens:    int                = 512

    # Narrative / lore
    lore:        str                  = ""
    voice:       str                  = "neutral"     # terse|verbose|cryptic|warm|cold|neutral

    # Unlock gate
    unlock_beat: Optional[str]        = None          # story beat required to activate
    trust_min:   int                  = 0             # minimum trust score

    # Scheduling
    cycle_every: int                  = 1             # run every N orchestrator cycles
    timeout_s:   int                  = 30

    def is_unlocked(self, beats: List[str], trust: int) -> bool:
        if self.unlock_beat and self.unlock_beat not in beats:
            return False
        if trust < self.trust_min:
            return False
        return True

    def runs_on(self, surface: str) -> bool:
        return "all" in self.surfaces or surface in self.surfaces


# ──────────────────────────────────────────────────────────────────────────────
# Agent base class
# ──────────────────────────────────────────────────────────────────────────────

class AgentBase:
    """
    Base class for all DevMentor / Terminal Depths agents.

    Subclasses implement:
        async def run(self, context: dict) -> dict
    or the synchronous:
        def run_sync(self, context: dict) -> dict

    Context dict keys (suggested — not enforced):
        surface:   str          — active surface (replit/vscode/docker/...)
        game_state: dict        — current Terminal Depths game state
        memory:    object       — persistent memory store
        llm_client: object      — LLM client (or None for zero-token agents)
        cycle:     int          — current orchestrator cycle count
    """

    def __init__(self, personality: AgentPersonality):
        self.personality = personality
        self.status: AgentStatus = AgentStatus.IDLE
        self._run_count: int     = 0
        self._last_run: float    = 0.0
        self._last_result: Optional[dict] = None
        self.logger = logging.getLogger(f"agents.{personality.codename}")

    # ------------------------------------------------------------------
    # Override this in subclasses
    # ------------------------------------------------------------------

    def run_sync(self, context: dict) -> dict:
        """
        Synchronous entry point.
        Returns a result dict with at minimum:
            { "status": "ok"|"error", "output": <any> }
        """
        raise NotImplementedError(f"{self.__class__.__name__}.run_sync is not implemented")

    # ------------------------------------------------------------------
    # Orchestrator interface (called by AgentOrchestrator)
    # ------------------------------------------------------------------

    def should_run(self, cycle: int, surface: str,
                   beats: List[str], trust: int) -> bool:
        """Decide whether this agent should run on the given cycle."""
        if not self.personality.is_unlocked(beats, trust):
            return False
        if not self.personality.runs_on(surface):
            return False
        if self.status == AgentStatus.RUNNING:
            return False
        if self.personality.tier == AgentTier.DORMANT.value:
            return False
        return cycle % max(1, self.personality.cycle_every) == 0

    def execute(self, context: dict) -> dict:
        """Wrap run_sync with error handling, timing, and status tracking."""
        self.status    = AgentStatus.RUNNING
        self._run_count += 1
        start          = time.monotonic()
        try:
            result     = self.run_sync(context)
            self.status = AgentStatus.DONE
        except Exception as exc:
            self.logger.exception("Agent %s crashed: %s", self.personality.codename, exc)
            result  = {"status": "error", "error": str(exc)}
            self.status = AgentStatus.ERROR
        finally:
            elapsed = time.monotonic() - start
            self._last_run    = time.time()
            self._last_result = result
            self.logger.debug(
                "agent=%s cycle=%s elapsed=%.2fs status=%s",
                self.personality.codename,
                context.get("cycle", "?"),
                elapsed,
                self.status.value,
            )
        return result

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "codename":    self.personality.codename,
            "name":        self.personality.name,
            "role":        self.personality.role,
            "faction":     self.personality.faction,
            "tier":        self.personality.tier,
            "surfaces":    self.personality.surfaces,
            "status":      self.status.value,
            "run_count":   self._run_count,
            "last_run":    self._last_run,
            "unlock_beat": self.personality.unlock_beat,
            "trust_min":   self.personality.trust_min,
        }

    def __repr__(self) -> str:
        return (
            f"<Agent codename={self.personality.codename!r} "
            f"status={self.status.value} runs={self._run_count}>"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────────────────

class AgentOrchestrator:
    """
    Runs all registered agents on each cycle.
    Designed to run on a single surface — instantiate one per active surface.
    """

    def __init__(self, surface: str = "replit"):
        self.surface: str             = surface
        self._agents: Dict[str, AgentBase] = {}
        self._cycle: int              = 0
        self.logger = logging.getLogger("agents.orchestrator")

    def register(self, agent: AgentBase) -> None:
        self._agents[agent.personality.codename] = agent
        self.logger.info("Registered agent: %s", agent.personality.codename)

    def tick(self, beats: List[str] = (), trust: int = 0,
             extra_context: Optional[dict] = None) -> Dict[str, dict]:
        """Run one orchestrator cycle. Returns results keyed by codename."""
        self._cycle += 1
        context = {
            "surface": self.surface,
            "cycle":   self._cycle,
            **(extra_context or {}),
        }
        results: Dict[str, dict] = {}
        for codename, agent in self._agents.items():
            if agent.should_run(self._cycle, self.surface, list(beats), trust):
                results[codename] = agent.execute(context)
        return results

    def list_agents(self, surface_filter: Optional[str] = None) -> List[dict]:
        agents = list(self._agents.values())
        if surface_filter:
            agents = [a for a in agents if a.personality.runs_on(surface_filter)]
        return [a.to_dict() for a in agents]

    def status_report(self) -> dict:
        return {
            "surface":    self.surface,
            "cycle":      self._cycle,
            "agent_count": len(self._agents),
            "agents":     {k: v.status.value for k, v in self._agents.items()},
        }
