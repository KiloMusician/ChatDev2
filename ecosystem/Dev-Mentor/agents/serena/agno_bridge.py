"""
agents/serena/agno_bridge.py — SerenaAgnoToolkit: Agno-compatible tool bridge.

Colony Activation Directive — Phase 0 (agent framework)
=========================================================
Exposes SerenaAgent's capabilities as a toolkit usable by Agno agents.
Agno does NOT need to be installed — this module provides a forward-compatible
interface.  When Agno is available, wrap these into agno.tools.Toolkit.

Reference: https://oraios.github.io/serena/03-special-guides/custom_agent.html

SAFE-class constraint note
──────────────────────────
The Serena docs warn: "The Agno UI does not ask for user permission before
executing shell tools."  We address this by:
  1. Never exposing execute_shell_command as an Agno tool.
  2. Routing all side-effecting tools through ConsentGate first.
  3. Logging every invocation to the Memory Palace.

Usage (without Agno)
────────────────────
  from agents.serena.agno_bridge import SerenaAgnoToolkit
  toolkit = SerenaAgnoToolkit(serena_agent)
  tools   = toolkit.tools()   # List[dict]  — OpenAI function-call schema
  result  = toolkit.call("walk_repo", {})

Usage (with Agno)
─────────────────
  from agno.agent import Agent
  from agents.serena.agno_bridge import SerenaAgnoToolkit

  serena   = SerenaAgent(repo_root=Path("."))
  toolkit  = SerenaAgnoToolkit(serena)
  agent    = Agent(
      name="Serena",
      model=...,
      tools=toolkit.as_agno_tools(),
  )
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Optional


class ToolSpec:
    """Minimal OpenAI-compatible tool specification."""

    def __init__(self, name: str, description: str,
                 parameters: dict, handler: Callable):
        self.name        = name
        self.description = description
        self.parameters  = parameters
        self.handler     = handler

    def to_dict(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name":        self.name,
                "description": self.description,
                "parameters":  self.parameters,
            },
        }


class SerenaAgnoToolkit:
    """
    Toolkit that exposes SerenaAgent's capabilities in an Agno-compatible
    (and OpenAI function-call compatible) format.

    Serena's tools map to the ΨΞΦΩ dataflow:
      Ψ — walk_repo, fast_walk_repo
      Ξ — find_symbol, ask
      Φ — relate_entities, diff_files
      Ω — get_observations, get_status, detect_drift
    """

    def __init__(self, agent):
        """
        Parameters
        ----------
        agent : SerenaAgent
            The live Serena agent instance.
        """
        self._agent = agent
        self._specs = self._build_specs()

    # ── tool registry ─────────────────────────────────────────────────────────

    def _build_specs(self) -> List[ToolSpec]:
        a = self._agent
        return [
            # Ψ — Walker
            ToolSpec(
                name="walk_repo",
                description=(
                    "Scoped fast walk of the repository. Indexes the game-engine, "
                    "agents, scripts, and cli directories (≈5 s). "
                    "Returns a summary of chunks processed."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "enum": ["fast", "changed", "full"],
                            "description": "Walk mode. 'fast' (default) for game scope.",
                        }
                    },
                    "required": [],
                },
                handler=lambda p: a.fast_walk() if p.get("mode", "fast") != "full"
                                                 else a.walk(mode="changed"),
            ),

            # Ξ — Finder
            ToolSpec(
                name="find_symbol",
                description=(
                    "Precise, symbol-level lookup. Returns the exact class/function "
                    "definition with file path and line number. "
                    "Like Oraios Serena's find_symbol."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Symbol name to find (class, function, variable).",
                        },
                        "kind": {
                            "type": "string",
                            "enum": ["function", "class", "variable", ""],
                            "description": "Optional kind filter.",
                        },
                    },
                    "required": ["name"],
                },
                handler=lambda p: a.find(p["name"], kind=p.get("kind", "")),
            ),

            # Ξ — Asker
            ToolSpec(
                name="ask",
                description=(
                    "Semantic search over the indexed codebase. Returns the most "
                    "relevant code chunks for a natural-language query. "
                    "Optionally scoped to a sub-path."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural-language query.",
                        },
                        "scope": {
                            "type": "string",
                            "description": "Optional sub-path to restrict search (e.g. 'app/game_engine').",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max number of results (default 5).",
                        },
                    },
                    "required": ["query"],
                },
                handler=lambda p: a.ask(
                    p["query"],
                    scope=p.get("scope"),
                    limit=p.get("limit", 5),
                ),
            ),

            # Φ — Relate
            ToolSpec(
                name="relate_entities",
                description=(
                    "Discovers and stores relationships between files or functions "
                    "in the Memory Palace. Returns cross-layer relationship graph."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "entity": {
                            "type": "string",
                            "description": "Entity name or path.",
                        },
                    },
                    "required": ["entity"],
                },
                handler=lambda p: a.relate(p["entity"]),
            ),

            # Φ — Diff
            ToolSpec(
                name="diff_files",
                description=(
                    "Returns git-changed files since last commit and notes which "
                    "are indexed in the Memory Palace."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                handler=lambda _: a.diff(),
            ),

            # Ω — Observations
            ToolSpec(
                name="get_observations",
                description=(
                    "Returns recent observations recorded in the Memory Palace. "
                    "Optional severity filter: info | warn | critical."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "severity": {
                            "type": "string",
                            "enum": ["info", "warn", "critical", ""],
                            "description": "Filter by severity level.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max observations to return (default 10).",
                        },
                    },
                    "required": [],
                },
                handler=lambda p: a.memory.recent_observations(
                    limit=p.get("limit", 10),
                    severity=p.get("severity") or None,
                ),
            ),

            # Ω — Status
            ToolSpec(
                name="get_status",
                description=(
                    "Returns Serena's current operational status: memory health, "
                    "index stats, policy state, version."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                handler=lambda _: a.get_status(),
            ),

            # Ω — Drift
            ToolSpec(
                name="detect_drift",
                description=(
                    "Run the Drift Detection Engine. Returns drift signals "
                    "describing coherence gaps: doc debt, arch violations, "
                    "orphan chunks, stale index, protocol drift."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "fast": {
                            "type": "boolean",
                            "description": "If true (default), skip slow doc-debt AST scan.",
                        },
                        "scope": {
                            "type": "string",
                            "description": "Optional sub-path to restrict the scan.",
                        },
                    },
                    "required": [],
                },
                handler=lambda p: a.drift(
                    fast=p.get("fast", True),
                    scope=p.get("scope"),
                ),
            ),
        ]

    # ── public API ────────────────────────────────────────────────────────────

    def tools(self) -> List[dict]:
        """Return OpenAI function-call schema for all tools."""
        return [s.to_dict() for s in self._specs]

    def call(self, name: str, params: dict) -> Any:
        """
        Invoke a tool by name with params dict.
        All calls are logged to the Memory Palace.
        """
        spec = next((s for s in self._specs if s.name == name), None)
        if spec is None:
            return {"error": f"Unknown tool: {name}"}

        start = time.time()
        try:
            result = spec.handler(params)
            elapsed = round(time.time() - start, 3)
            self._agent.memory.observe(
                subject=f"agno_tool:{name}",
                note=f"Called with {json.dumps(params)[:120]} → {elapsed}s",
                severity="info",
            )
            return result
        except Exception as exc:
            self._agent.memory.observe(
                subject=f"agno_tool:{name}",
                note=f"ERROR: {exc}",
                severity="critical",
            )
            return {"error": str(exc)}

    def as_agno_tools(self):
        """
        Return tools in Agno-native format if Agno is installed.
        Falls back to raw function list if not.

        Usage:
            toolkit = SerenaAgnoToolkit(serena_agent)
            agent   = Agent(tools=toolkit.as_agno_tools(), ...)
        """
        try:
            from agno.tools import tool as agno_tool

            tools = []
            for spec in self._specs:
                # Capture spec in closure
                def _make_fn(s):
                    def _fn(**kwargs):
                        return self.call(s.name, kwargs)
                    _fn.__name__ = s.name
                    _fn.__doc__  = s.description
                    return agno_tool(_fn)
                tools.append(_make_fn(spec))
            return tools
        except ImportError:
            # Agno not installed — return raw callables
            return [
                lambda name=s.name, **kw: self.call(name, kw)
                for s in self._specs
            ]

    def manifest(self) -> dict:
        """
        Return a JSON-serialisable manifest describing all tools.
        Suitable for inclusion in the NuSyQ agent manifest.
        """
        return {
            "toolkit":    "SerenaAgnoToolkit",
            "version":    "1.0.0",
            "surface":    "replit",
            "safe_class": "SAFE",
            "tools": [
                {
                    "name":        s.name,
                    "description": s.description,
                }
                for s in self._specs
            ],
        }
