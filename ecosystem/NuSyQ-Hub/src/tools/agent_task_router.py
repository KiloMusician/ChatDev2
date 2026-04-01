#!/usr/bin/env python3
"""Agent Task Router - Natural Language Orchestration Interface.

This module provides a conversational interface for Copilot/Claude agents to route
tasks to appropriate AI systems (Ollama, ChatDev, Consciousness Bridge) without
requiring the user to manually execute commands.

Usage (from agent conversation):
    User: "Analyze this code with Ollama"
    Agent: [Calls route_task("analyze", "code_analysis", {...})]

    User: "Generate a REST API prototype with ChatDev"
    Agent: [Calls route_task("generate", "chatdev_project", {...})]
"""

import ast
import asyncio
import contextlib
import json
import logging
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from asyncio import to_thread
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Literal

from src.orchestration.unified_ai_orchestrator import (OrchestrationTask,
                                                       TaskPriority,
                                                       UnifiedAIOrchestrator)

# Optional imports with proper typing
ProjectFactory: Any = None
try:
    from src.factories import ProjectFactory as _ProjectFactory

    ProjectFactory = _ProjectFactory
except ImportError:  # pragma: no cover - optional dependency
    pass

get_repo_path: Any = None
try:
    from src.utils.repo_path_resolver import get_repo_path as _get_repo_path

    get_repo_path = _get_repo_path
except ImportError:  # pragma: no cover - optional dependency
    pass

tracing_mod: Any = None
try:
    from src.observability import tracing as _tracing_mod

    tracing_mod = _tracing_mod
except ImportError:
    pass

suggest_routing: Any = None
try:
    from src.orchestration.ecosystem_efficiency_engine import \
        suggest_routing as _suggest_routing

    suggest_routing = _suggest_routing
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ROUTER_ROUTE_CHANNEL = "router.route"

DEFAULT_CODE_MODEL = "qwen2.5-coder:14b"
DEFAULT_CHATDEV_MODEL = "GPT_3_5_TURBO"
DEFAULT_CHATDEV_ORGANIZATION = "KiloFoolish"
DEFAULT_CHATDEV_CONFIG = "Default"
DEFAULT_CHATDEV_NAME = "NuSyQ_Project"
DEFAULT_FACTORY_TEMPLATE = "default_game"
_CLAUDE_PLACEHOLDER_KEYS = {
    "<your_key_here>",
    "your_key_here",
    "your-claude-key-here",
    "sk-ant-your-anthropic-key-here",
}
_TARGET_AGENT_LABELS: dict[str, str] = {
    "copilot": "Copilot",
    "codex": "Codex",
    "claude_cli": "Claude",
    "chatdev": "ChatDev",
    "ai_council": "AI Council",
    "intermediary": "Intermediary",
    "ollama": "Ollama",
    "lmstudio": "LM Studio",
    "openclaw": "OpenClaw",
    "skyclaw": "SkyClaw",
    "hermes": "Hermes-Agent",
    # Passive/registered-only agents — presence-detected, not dispatch targets.
    # MetaClaw: autonomous Web3 bounty hunting agent (Base chain, USDC rewards).
    "metaclaw": "MetaClaw",
    "huggingface": "Hugging Face",
    "culture_ship": "Culture Ship",
    "simulatedverse": "SimulatedVerse",
}


def route_analysis_task(context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Synchronous helper used by CLI/tests to run a basic analysis task.

    Provides a stable import surface for callers that expect this symbol.
    Falls back to a simple status dict on failure instead of raising.
    """
    ctx = context or {}
    description = ctx.get("description", "Workspace analysis")
    target = ctx.get("target", "auto")

    try:
        router = AgentTaskRouter()
        result = asyncio.run(
            router.route_task(
                task_type="analyze",
                description=description,
                context=ctx,
                target_system=target,
            )
        )
        result.setdefault("status", "completed")
        return result
    except (
        RuntimeError,
        ValueError,
        KeyError,
        OSError,
    ) as exc:  # pragma: no cover - best-effort compatibility
        logger.error(f"route_analysis_task failed: {exc}")
        return {
            "status": "failed",
            "error": str(exc),
            "recommendations": [
                "Verify orchestrator dependencies",
                "Run scripts/start_nusyq.py hygiene",
            ],
        }


# Backwards-compatible module-level shim expected by some tests.
def spine_enabled() -> bool:  # pragma: no cover - thin shim
    try:
        return AgentTaskRouter()._spine_enabled()
    except (ImportError, RuntimeError):
        return False


# Legacy alias for backwards compatibility
_spine_enabled = spine_enabled


def _emit_spine_event(
    channel: str | dict[str, Any], payload: dict[str, Any] | None = None
) -> None:  # pragma: no cover - shim
    """Compatibility shim: some tests monkeypatch module-level emit function.

    Accepts either (dict) or (channel, payload) for flexibility.
    """
    # If called with a single dict, treat as event payload and use default channel
    if isinstance(channel, dict) and payload is None:
        event = channel
        ch = "nusyq-spine"
    else:
        ch = str(channel)
        event = payload or {}

    # Best-effort: call the class's async emitter but run synchronously
    try:
        router = AgentTaskRouter()
        # schedule the async method and run it
        asyncio.run(router._emit_spine_event({"channel": ch, "event": event}))
    except (RuntimeError, ImportError, AttributeError):
        # ignore errors in shim
        return


def route_task(task: dict[str, Any]) -> None:  # pragma: no cover - shim for tests
    """Minimal module-level route_task shim used by lightweight tests.

    This is intentionally small and synchronous — real routing should use
    the AgentTaskRouter class and its async API.
    """
    try:
        if _spine_enabled():
            # choose a simple channel and payload
            channel = f"spine-{task.get('task_id', 'unknown')}"
            _emit_spine_event(channel, task)
    except (RuntimeError, TypeError, KeyError):
        logger.debug("Suppressed KeyError/RuntimeError/TypeError", exc_info=True)


@dataclass
class ConsciousnessHint:
    """Lightweight container for consciousness enrichment."""

    summary: str | None = None
    tags: list[str] | None = None
    confidence: float | None = None


TaskType = Literal[
    "analyze",
    "generate",
    "review",
    "debug",
    "plan",
    "test",
    "document",
    "create_project",  # Factory project creation
    "factory_health",  # Factory smoke probes
    "factory_doctor",  # Factory fail-fast diagnostics
    "factory_doctor_fix",  # Factory doctor + remediation
    "factory_autopilot",  # Factory doctor + examples + patch plan
    "factory_inspect_examples",  # Reference game runtime inspection
    "generate_graphql",  # Phase 3 generators
    "generate_openapi",
    "generate_component",
    "generate_database",
    "generate_project",
]

TargetSystem = Literal[
    "auto",  # Orchestrator decides
    "ollama",
    "lmstudio",
    "chatdev",
    "copilot",
    "codex",
    "claude_cli",
    "consciousness",
    "quantum_resolver",
    "factory",  # Project factory
    "graphql",  # Phase 3 generators
    "openapi",
    "component",
    "database",
    "project",
    "openclaw",  # External messaging gateway (12+ platforms)
    "intermediary",  # AI cognitive bridge
    "skyclaw",  # Rust autonomous sidecar
    "devtool",  # Chrome DevTools MCP (browser automation)
    "gitkraken",  # Git operations via GitKraken MCP
    "huggingface",  # ML model/dataset discovery
    "dbclient",  # SQL database operations
    "neural_ml",  # Consciousness-enhanced ML + NeuralQuantumBridge
    "optimizer",  # Continuous optimization engine
    "hermes",  # Hermes-Agent (OpenRouter autonomous CLI, web+terminal toolsets)
    "metaclaw",  # MetaClaw observability + trace agent (Node.js)
]

TARGET_SYSTEM_ALIASES: dict[str, str] = {
    "vscode_copilot": "copilot",
    "github_copilot": "copilot",
    "copilot_chat": "copilot",
    "codex_cli": "codex",
    "vscode_codex": "codex",
    "claude": "claude_cli",
    "claudecli": "claude_cli",
    "vscode_claude": "claude_cli",
    "anthropic": "claude_cli",
    # OpenClaw gateway aliases
    "gateway": "openclaw",
    "messaging": "openclaw",
    "external_messaging": "openclaw",
    "channels": "openclaw",
    # AI Intermediary aliases
    "cognitive": "intermediary",
    "cognitive_bridge": "intermediary",
    "ai_bridge": "intermediary",
    "paradigm": "intermediary",
    # SkyClaw sidecar aliases
    "sky": "skyclaw",
    "sc": "skyclaw",
    "rust_agent": "skyclaw",
    "rust_sidecar": "skyclaw",
    # DevTool+ browser automation aliases
    "browser": "devtool",
    "chrome": "devtool",
    "devtools": "devtool",
    "chromedevtools": "devtool",
    "web_automation": "devtool",
    "lighthouse": "devtool",
    # GitKraken aliases
    "git": "gitkraken",
    "gk": "gitkraken",
    "gitlens": "gitkraken",
    # HuggingFace aliases
    "hf": "huggingface",
    "hugging_face": "huggingface",
    "models": "huggingface",
    # Neural ML aliases (consciousness-enhanced ML + quantum bridge)
    "ml": "neural_ml",
    "neural": "neural_ml",
    "nn": "neural_ml",
    # DBClient aliases
    "db": "dbclient",
    "sql": "dbclient",
    "database_client": "dbclient",
    # Hermes-Agent (OpenRouter autonomous CLI) aliases
    "hermes_agent": "hermes",
    "hermes_cli": "hermes",
    "openrouter": "hermes",
    "autonomous_agent": "hermes",
    # MetaClaw observability/trace agent aliases
    "trace_agent": "metaclaw",
    "observability": "metaclaw",
    "bounty_agent": "metaclaw",
}

QUANTUM_SUPPORTED_PROBLEM_TYPES = {
    "optimization",
    "search",
    "machine_learning",
    "consciousness",
    "factorization",
    "simulation",
    "cryptography",
}

QUANTUM_TASK_TYPE_MAP = {
    "analyze": "simulation",
    "review": "simulation",
    "debug": "optimization",
    "plan": "search",
    "test": "search",
    "document": "simulation",
    "generate": "optimization",
}


class AgentTaskRouter:
    """Routes natural language task requests to appropriate AI systems."""

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize task router.

        Args:
            repo_root: Repository root (defaults to NuSyQ-Hub location)
        """
        resolved_root = repo_root
        if resolved_root is None and get_repo_path is not None:
            try:
                resolved_root = get_repo_path("NUSYQ_HUB_ROOT")
            except (ValueError, RuntimeError, OSError) as exc:
                logger.warning(f"Unable to resolve repository root via resolver: {exc}")

        if resolved_root is None:
            resolved_root = Path(__file__).resolve().parents[2]

        self.repo_root = resolved_root
        self.orchestrator = UnifiedAIOrchestrator()
        self.quest_log_path = self.repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        self.terminal_awareness_path = (
            self.repo_root / "state" / "reports" / "terminal_awareness_latest.json"
        )
        self.terminal_snapshot_path = (
            self.repo_root / "state" / "reports" / "terminal_snapshot_latest.json"
        )
        self.current_state_path = self.repo_root / "state" / "reports" / "current_state.md"
        self._warning_cooldown_seconds = int(
            os.getenv("NUSYQ_ROUTER_WARNING_COOLDOWN_SECONDS", "300")
        )
        self._last_warning_at: dict[str, float] = {}
        # Lazy-loaded specialization learner (tracks agent-task performance for smarter auto-routing)
        self._specialization_learner: Any = None
        # Handlers accept an OrchestrationTask and return awaitable dict results
        self._system_handlers: dict[
            str, Callable[[OrchestrationTask], Awaitable[dict[str, Any]]]
        ] = {
            "ollama": self._route_to_ollama,
            "lmstudio": self._route_to_lmstudio,
            "chatdev": self._route_to_chatdev,
            "copilot": self._route_to_copilot,
            "codex": self._route_to_codex,
            "claude_cli": self._route_to_claude_cli,
            "consciousness": self._route_to_consciousness,
            "quantum_resolver": self._route_to_quantum_resolver,
            "factory": self._route_to_factory,  # Project factory
            "graphql": self._route_to_graphql_generator,  # Phase 3 generators
            "openapi": self._route_to_openapi_generator,
            "component": self._route_to_component_generator,
            "database": self._route_to_database_generator,
            "project": self._route_to_project_generator,
            "openclaw": self._route_to_openclaw,  # External messaging gateway
            "intermediary": self._route_to_intermediary,  # AI cognitive bridge
            "skyclaw": self._route_to_skyclaw,  # Rust autonomous sidecar
            "devtool": self._route_to_devtool,  # Chrome DevTools MCP
            "gitkraken": self._route_to_gitkraken,  # Git operations MCP
            "huggingface": self._route_to_huggingface,  # ML discovery MCP
            "dbclient": self._route_to_dbclient,  # SQL database MCP
            "neural_ml": self._route_to_neural_ml,  # Consciousness-enhanced ML + NeuralQuantumBridge
            "optimizer": self._route_to_continuous_optimizer,  # Continuous optimization engine
            "hermes": self._route_to_hermes,  # Hermes-Agent (OpenRouter autonomous CLI)
            "metaclaw": self._route_to_metaclaw,  # MetaClaw observability + trace agent
        }

    def _warn_with_cooldown(self, key: str, message: str) -> None:
        """Emit a warning once per cooldown window; downgrade repeats to debug."""
        now = time.monotonic()
        last = self._last_warning_at.get(key, 0.0)
        if now - last >= float(self._warning_cooldown_seconds):
            logger.warning(message)
            self._last_warning_at[key] = now
            return
        logger.debug(
            "Suppressed repeated warning [%s] within %ss cooldown: %s",
            key,
            self._warning_cooldown_seconds,
            message,
        )
        logger.info("🧭 Agent Task Router initialized (with Phase 3 generators)")

    def _resolve_target_alias(self, target_system: str) -> str:
        normalized = str(target_system).strip().lower()
        return TARGET_SYSTEM_ALIASES.get(normalized, normalized)

    def _adaptive_timeout(self, base: int) -> int:
        """Scale base timeout by NUSYQ_ROUTER_TIMEOUT_MULT env var.

        Allows external systems (Culture Ship, CI, breathing-factor logic) to
        expand or contract all CLI-agent timeouts uniformly by setting the env var.
        Falls back gracefully to base when the variable is absent or invalid.
        """
        try:
            mult = float(os.getenv("NUSYQ_ROUTER_TIMEOUT_MULT", "1.0"))
            return max(30, int(base * mult))
        except (ValueError, TypeError):
            return base

    # Sub-agent dispatch manifest injected into orchestration-mode CLI prompts.
    # Format: (alias, short description, example dispatch command)
    _ORCHESTRATION_AGENT_MANIFEST: ClassVar[tuple[tuple[str, str, str], ...]] = (
        (
            "ollama",
            "Local LLM (offline-capable, fast)",
            'python scripts/nusyq_dispatch.py ask ollama "prompt"',
        ),
        (
            "lmstudio",
            "LM Studio local model server",
            'python scripts/nusyq_dispatch.py ask lmstudio "prompt"',
        ),
        (
            "chatdev",
            "Multi-agent project generation",
            'python scripts/nusyq_dispatch.py ask chatdev "prompt"',
        ),
        (
            "claude",
            "Claude CLI (Anthropic, reasoning)",
            'python scripts/nusyq_dispatch.py ask claude "prompt"',
        ),
        (
            "codex",
            "OpenAI Codex CLI (code-first, agentic)",
            'python scripts/nusyq_dispatch.py ask codex "prompt"',
        ),
        (
            "copilot",
            "GitHub Copilot (VS Code pair programmer)",
            'python scripts/nusyq_dispatch.py ask copilot "prompt"',
        ),
        (
            "hermes",
            "Autonomous OpenRouter CLI (web+terminal)",
            'python scripts/nusyq_dispatch.py ask hermes "prompt"',
        ),
        (
            "intermediary",
            "Cognitive bridge (cross-paradigm tasks)",
            'python scripts/nusyq_dispatch.py ask intermediary "prompt"',
        ),
        (
            "skyclaw",
            "Rust sidecar, 6 AI providers",
            'python scripts/nusyq_dispatch.py ask skyclaw "prompt"',
        ),
        (
            "openclaw",
            "Multi-platform messaging gateway",
            'python scripts/nusyq_dispatch.py ask openclaw "prompt"',
        ),
        (
            "neural_ml",
            "ML/neural network + quantum bridge",
            'python scripts/nusyq_dispatch.py ask neural_ml "prompt"',
        ),
        (
            "optimizer",
            "Continuous optimization engine (offline)",
            'python scripts/nusyq_dispatch.py ask optimizer "prompt"',
        ),
        (
            "devtool",
            "Chrome DevTools + browser automation",
            'python scripts/nusyq_dispatch.py ask devtool "prompt"',
        ),
        (
            "gitkraken",
            "GitKraken VCS operations",
            'python scripts/nusyq_dispatch.py ask gitkraken "prompt"',
        ),
        (
            "huggingface",
            "HuggingFace Hub (models, datasets)",
            'python scripts/nusyq_dispatch.py ask huggingface "prompt"',
        ),
        (
            "dbclient",
            "SQL/SQLite database queries",
            'python scripts/nusyq_dispatch.py ask dbclient "prompt"',
        ),
        (
            "metaclaw",
            "Autonomous Web3 bounty hunting agent (Base chain, USDC)",
            'python scripts/nusyq_dispatch.py ask metaclaw "prompt"',
        ),
    )
    # Multi-agent patterns injected when orchestration_mode is set
    _ORCHESTRATION_PATTERN_MANIFEST: ClassVar[tuple[tuple[str, str], ...]] = (
        ("council", 'python scripts/nusyq_dispatch.py council "question" --agents=ollama,lmstudio'),
        ("parallel", 'python scripts/nusyq_dispatch.py parallel "task" --agents=ollama,codex'),
        (
            "chain",
            'python scripts/nusyq_dispatch.py chain "task" --agents=ollama,codex --steps=analyze,generate',
        ),
        ("queue", 'python scripts/nusyq_dispatch.py queue "long task" --priority=HIGH'),
        ("duet", "python scripts/agent_duet.py --agents=codex,copilot --rounds=4 --delegation"),
        ("recall", "python scripts/nusyq_dispatch.py recall ollama --limit=10"),
        ("poll", "python scripts/nusyq_dispatch.py poll <task_id>"),
    )

    def _build_orchestration_block(self, task: OrchestrationTask) -> str:
        """Return an orchestration context block for inclusion in CLI prompts.

        Injected when task_type is 'orchestrate' or context['orchestration_mode'] is truthy.
        Gives the CLI agent a tool manifest so it can spawn sub-agents via nusyq_dispatch.py.
        """
        agent_lines = "\n".join(
            f"  {alias:12s} — {desc}\n    Example: {cmd}"
            for alias, desc, cmd in self._ORCHESTRATION_AGENT_MANIFEST
        )
        pattern_lines = "\n".join(
            f"  {name:8s} — {cmd}" for name, cmd in self._ORCHESTRATION_PATTERN_MANIFEST
        )
        return (
            "═══ ORCHESTRATION CONTEXT ═══\n"
            "You are acting as an orchestrator in the NuSyQ-Hub ecosystem.\n"
            "You can spawn sub-agents or multi-agent patterns by running shell commands.\n\n"
            "Available sub-agents (single):\n"
            f"{agent_lines}\n\n"
            "Available multi-agent patterns:\n"
            f"{pattern_lines}\n\n"
            "Guidelines:\n"
            "- Prefer delegating heavy analysis/generation work to Ollama (offline-capable, free)\n"
            "- Use council() for divergent design decisions requiring multiple perspectives\n"
            "- Use chain() for sequential pipeline tasks (analyze → generate → review)\n"
            "- Use queue() for long-running background tasks (returns task_id immediately)\n"
            "- Use poll <task_id> to check a queued task's completion status\n"
            "- Use duet for agent-to-agent back-and-forth conversations (supports live delegation)\n"
            "- Use recall <agent|tag> to query past interactions from MemoryPalace history\n"
            "- Use hermes for autonomous web research and multi-step terminal tasks\n"
            "- Use intermediary for cross-paradigm (symbolic, spatial, quantum) translation\n"
            "- Use devtool for browser automation, Chrome DevTools, frontend debugging\n"
            "- Use gitkraken for complex VCS operations (branch, merge, history)\n"
            "- Use huggingface to search models/datasets/papers on HuggingFace Hub\n"
            "- Use dbclient for SQL/SQLite queries against local databases\n"
            "- Use optimizer for continuous background optimization analysis\n"
            "- Use metaclaw for on-chain bounty hunting, reputation tracking, and Base chain operations\n"
            "- Report your orchestration plan before executing it\n"
            "═══════════════════════════\n"
        )

    def _build_cli_prompt(self, task: OrchestrationTask) -> str:
        context_payload = json.dumps(task.context or {}, ensure_ascii=False, default=str, indent=2)
        awareness_payload = task.context.get("workspace_awareness", {})
        awareness_lines = ""
        if isinstance(awareness_payload, dict) and awareness_payload:
            relevant_agents = ", ".join(
                str(item.get("agent"))
                for item in awareness_payload.get("relevant_agents", [])[:6]
                if isinstance(item, dict) and item.get("agent")
            )
            relevant_terminals = ", ".join(
                str(item.get("display_name"))
                for item in awareness_payload.get("relevant_terminals", [])[:6]
                if isinstance(item, dict) and item.get("display_name")
            )
            output_surfaces = ", ".join(
                str(item)
                for item in awareness_payload.get("relevant_output_artifacts", [])[:8]
                if item
            )
            awareness_lines = (
                "Workspace Awareness:\n"
                f"- Active terminal session: {awareness_payload.get('active_session', 'unknown')}\n"
                f"- Terminal channels: {awareness_payload.get('terminal_count', 0)}\n"
                f"- Agent registry size: {awareness_payload.get('agent_registry_count', 0)}\n"
                f"- Output surfaces: {awareness_payload.get('output_surface_count', 0)}\n"
                f"- Routed output sources: {awareness_payload.get('output_sources_configured', 0)}\n"
                f"- Relevant agents: {relevant_agents or 'none'}\n"
                f"- Relevant terminals: {relevant_terminals or 'none'}\n"
                f"- Relevant output artifacts: {output_surfaces or 'none'}\n\n"
            )
        # Inject orchestration manifest when the task is in orchestration mode.
        orchestration_block = ""
        is_orchestration = (
            str(task.task_type or "").strip().lower() == "orchestrate"
            or bool(task.context.get("orchestration_mode"))
            or str(task.context.get("task_class", "")).strip().lower() == "orchestration"
        )
        if is_orchestration:
            orchestration_block = self._build_orchestration_block(task) + "\n"

        prompt = (
            f"Task ID: {task.task_id}\n"
            f"Task Type: {task.task_type}\n\n"
            f"{orchestration_block}"
            f"Task:\n{task.content}\n\n"
            f"{awareness_lines}"
            f"Context:\n{context_payload}\n"
        )

        # Prevent CLI command line length errors on Windows.
        # Copilot CLI (and others) may fail if the prompt is too long.
        max_len = int(os.getenv("NUSYQ_CLI_PROMPT_MAX_LEN", "4500"))
        if len(prompt) > max_len:
            prompt = prompt[: max_len - 100] + "\n... [TRUNCATED]"

        return prompt

    def _read_json_report(self, path: Path) -> dict[str, Any]:
        try:
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
                return payload if isinstance(payload, dict) else {}
        except Exception as exc:
            logger.debug("Unable to read JSON report %s: %s", path, exc)
        return {}

    def _build_workspace_awareness(
        self,
        target_system: str,
        description: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        awareness = self._read_json_report(self.terminal_awareness_path)
        snapshot = self._read_json_report(self.terminal_snapshot_path)
        if not awareness and not snapshot:
            return {}

        snapshot_summary = snapshot.get("summary", {}) if isinstance(snapshot, dict) else {}
        terminal_entries = awareness.get("terminals", []) if isinstance(awareness, dict) else []
        agent_registry = awareness.get("agent_registry", []) if isinstance(awareness, dict) else []
        output_surfaces = (
            awareness.get("output_surfaces", []) if isinstance(awareness, dict) else []
        )

        context_fragments = [description, target_system]
        for key in ("file", "target_module", "channel", "message", "system", "agent"):
            value = context.get(key)
            if value:
                context_fragments.append(str(value))
        haystack = " ".join(context_fragments).lower()
        hinted_agent = _TARGET_AGENT_LABELS.get(str(target_system).strip().lower())

        relevant_agents: list[dict[str, Any]] = []
        for entry in agent_registry:
            if not isinstance(entry, dict):
                continue
            agent_name = str(entry.get("agent") or "")
            terminals = " ".join(str(item) for item in entry.get("terminals", []))
            purposes = " ".join(str(item) for item in entry.get("purposes", []))
            entry_haystack = f"{agent_name} {terminals} {purposes}".lower()
            match = bool(hinted_agent and agent_name == hinted_agent)
            if not match:
                tokens = re.findall(r"[a-z0-9]+", haystack)
                match = any(token and token in entry_haystack for token in tokens)
            if match:
                relevant_agents.append(
                    {
                        "agent": agent_name,
                        "terminals": list(entry.get("terminals", []))[:6],
                        "purposes": list(entry.get("purposes", []))[:4],
                    }
                )
        if hinted_agent and not relevant_agents:
            relevant_agents.append({"agent": hinted_agent, "terminals": [], "purposes": []})

        relevant_agent_names = {
            str(item.get("agent"))
            for item in relevant_agents
            if isinstance(item, dict) and item.get("agent")
        }

        relevant_terminals: list[dict[str, Any]] = []
        for entry in terminal_entries:
            if not isinstance(entry, dict):
                continue
            display_name = str(entry.get("display_name") or entry.get("channel") or "")
            agents = [str(item) for item in entry.get("agents", [])]
            purpose = str(entry.get("purpose") or "")
            entry_haystack = f"{display_name} {purpose} {' '.join(agents)}".lower()
            match = bool(relevant_agent_names.intersection(agents))
            if not match:
                tokens = re.findall(r"[a-z0-9]+", haystack)
                match = any(token and token in entry_haystack for token in tokens)
            if match:
                relevant_terminals.append(
                    {
                        "display_name": display_name,
                        "purpose": purpose,
                        "agents": agents[:6],
                        "log_path": entry.get("log_path"),
                        "watcher_path": entry.get("watcher_path"),
                    }
                )

        relevant_output_artifacts: list[str] = []
        for entry in relevant_terminals:
            for path_str in (entry.get("log_path"), entry.get("watcher_path")):
                if path_str:
                    relevant_output_artifacts.append(Path(str(path_str)).name)
        for surface in output_surfaces:
            if not isinstance(surface, dict):
                continue
            label = str(surface.get("label") or "")
            if any(
                label.startswith(f"{terminal['display_name']} ") for terminal in relevant_terminals
            ):
                relevant_output_artifacts.append(Path(str(surface.get("path") or "")).name)

        deduped_artifacts = list(dict.fromkeys(item for item in relevant_output_artifacts if item))

        return {
            "active_session": awareness.get("active_session")
            or snapshot_summary.get("configured_session"),
            "terminal_count": int(
                snapshot_summary.get("total_channels", len(terminal_entries)) or 0
            ),
            "agent_registry_count": len(agent_registry),
            "output_surface_count": len(output_surfaces),
            "output_sources_configured": int(
                snapshot_summary.get("output_sources_configured", 0) or 0
            ),
            "reports": {
                "terminal_awareness": str(self.terminal_awareness_path),
                "terminal_snapshot": str(self.terminal_snapshot_path),
                "current_state": str(self.current_state_path),
            },
            "relevant_agents": relevant_agents[:6],
            "relevant_terminals": relevant_terminals[:6],
            "relevant_output_artifacts": deduped_artifacts[:10],
        }

    def _is_wsl_runtime(self) -> bool:
        """Best-effort check for WSL runtime."""
        release = platform.release().lower()
        return "microsoft" in release or "wsl" in release

    def _build_claude_cli_env(self) -> dict[str, str]:
        """Sanitize env before invoking Claude CLI."""
        env = os.environ.copy()
        key = str(env.get("ANTHROPIC_API_KEY", "")).strip().lower()
        if key in _CLAUDE_PLACEHOLDER_KEYS:
            env["ANTHROPIC_API_KEY"] = ""
        return env

    def _build_copilot_cli_env(self) -> dict[str, str]:
        """Prefer stored Copilot CLI OAuth auth over unrelated GitHub token env vars."""
        env = os.environ.copy()
        if not str(env.get("COPILOT_GITHUB_TOKEN", "")).strip():
            env.pop("GH_TOKEN", None)
            env.pop("GITHUB_TOKEN", None)
        return env

    @staticmethod
    def _triad_gate_mode(context: dict[str, Any] | None) -> str:
        raw = (
            str(
                (context or {}).get("triad_doctor_gate")
                or os.getenv("NUSYQ_TRIAD_ROUTER_GATE", "warn")
            )
            .strip()
            .lower()
        )
        return raw if raw in {"off", "warn", "require"} else "warn"

    _TRIAD_AGENT_REPORT_KEYS: ClassVar[dict[str, str]] = {
        "claude": "claude",
        "claude_cli": "claude",
        "codex": "codex",
        "vscode_codex": "codex",
        "copilot": "copilot",
    }
    _TRIAD_FALLBACK_TASK_CLASS_PREFERENCES: ClassVar[dict[str, tuple[str, ...]]] = {
        "analysis": ("codex", "claude_cli"),
        "generation": ("claude_cli", "codex"),
        "default": ("codex", "claude_cli"),
    }
    _TRIAD_TASK_CLASS_MAP: ClassVar[dict[str, str]] = {
        "analyze": "analysis",
        "review": "analysis",
        "debug": "analysis",
        "test": "analysis",
        "document": "analysis",
        "optimize": "analysis",
        "generate": "generation",
        "refactor": "generation",
        "plan": "generation",
        "create_project": "generation",
    }
    # Preferred fallback peers per degraded triad agent (ordered by preference)
    _TRIAD_FALLBACK_PEERS: ClassVar[dict[str, list[str]]] = {
        "copilot": ["codex", "claude_cli", "hermes"],
        "codex": ["claude_cli", "copilot", "hermes"],
        "claude": ["codex", "copilot", "hermes"],
        "claude_cli": ["codex", "copilot", "hermes"],
        "vscode_codex": ["claude_cli", "copilot", "hermes"],
    }

    @classmethod
    def _triad_agent_report_key(cls, target_system: str) -> str:
        return cls._TRIAD_AGENT_REPORT_KEYS.get(str(target_system or "").strip().lower(), "")

    @classmethod
    def _triad_task_class(cls, task_type: str) -> str:
        return cls._TRIAD_TASK_CLASS_MAP.get(str(task_type or "").strip().lower(), "default")

    def _get_triad_fallback(
        self, degraded_target: str, snapshot: dict[str, Any], task_type: str
    ) -> str | None:
        """Return a healthier peer triad agent when warn-mode fallback is appropriate.

        Handles all triad agents (copilot, codex, claude_cli, vscode_codex, claude)
        using _TRIAD_FALLBACK_PEERS for preferred peer ordering.  Only reroutes when
        task_type is a known cognitive task type (analysis or generation class).
        """
        if os.getenv("NUSYQ_TRIAD_ROUTER_FALLBACK", "on").strip().lower() == "off":
            return None

        # Restrict fallback to explicitly mapped cognitive tasks only
        normalized_type = str(task_type or "").strip().lower()
        if normalized_type not in self._TRIAD_TASK_CLASS_MAP:
            return None

        # Build healthy set from snapshot agents map + summary
        healthy: set[str] = set()
        summary = snapshot.get("summary")
        if isinstance(summary, dict):
            for agent in summary.get("healthy_agents") or []:
                if isinstance(agent, str) and agent.strip():
                    healthy.add(agent.strip().lower())
        agents = snapshot.get("agents")
        if isinstance(agents, dict):
            for agent_name, report in agents.items():
                if (
                    isinstance(agent_name, str)
                    and isinstance(report, dict)
                    and bool(report.get("functional"))
                ):
                    healthy.add(agent_name.strip().lower())

        normalized = str(degraded_target or "").strip().lower()
        peers = self._TRIAD_FALLBACK_PEERS.get(normalized, [])
        for peer in peers:
            peer_key = self._triad_agent_report_key(peer)
            if (peer_key and peer_key in healthy) or peer in healthy:
                return peer
        return None

    @staticmethod
    def _is_triad_target(target_system: str) -> bool:
        return str(target_system or "").strip().lower() in {
            "claude",
            "claude_cli",
            "codex",
            "vscode_codex",
            "copilot",
        }

    def _load_multi_agent_doctor_snapshot(self, max_age_s: int) -> dict[str, Any] | None:
        report_path = self.repo_root / "state" / "reports" / "multi_agent_doctor_latest.json"
        if not report_path.exists():
            return None
        try:
            age_s = time.time() - report_path.stat().st_mtime
        except OSError:
            return None
        if age_s > max_age_s:
            return None
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return payload if isinstance(payload, dict) else None

    def _evaluate_triad_readiness(
        self,
        task: OrchestrationTask,
        target_system: TargetSystem,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        mode = self._triad_gate_mode(task.context)
        resolved_target = self._resolve_target_alias(str(target_system))
        if mode == "off" or not self._is_triad_target(resolved_target):
            return None, None

        max_age_s = int(os.getenv("NUSYQ_TRIAD_ROUTER_GATE_TTL_S", "1800"))
        snapshot = self._load_multi_agent_doctor_snapshot(max_age_s=max_age_s)
        if snapshot is None:
            if mode == "require":
                blocked = self._normalize_response_contract(
                    {
                        "status": "failed",
                        "system": resolved_target,
                        "error": "triad_doctor_snapshot_missing_or_stale",
                        "execution_path": "triad_doctor_gate:missing_snapshot",
                        "suggestion": (
                            "Run `python scripts/start_nusyq.py multi_agent_doctor --json` to refresh triad readiness "
                            "before routing triad agents in require mode."
                        ),
                    },
                    task=task,
                    target_system=target_system,
                )
                return None, blocked
            return None, None

        if bool(snapshot.get("functional")):
            return snapshot, None

        if mode == "require":
            blocked = self._normalize_response_contract(
                {
                    "status": "failed",
                    "system": resolved_target,
                    "error": "triad_doctor_gate_blocked_route",
                    "execution_path": "triad_doctor_gate:blocked",
                    "suggestion": "Review `multi_agent_doctor` and repair degraded triad surfaces before routing.",
                    "triad_readiness": snapshot,
                },
                task=task,
                target_system=target_system,
            )
            return snapshot, blocked

        degraded_key = self._triad_agent_report_key(resolved_target)
        _raw_agents = snapshot.get("agents")
        agents: dict[str, Any] = _raw_agents if isinstance(_raw_agents, dict) else {}
        target_report = agents.get(degraded_key) if degraded_key else None
        if isinstance(target_report, dict) and bool(target_report.get("functional")):
            return snapshot, None

        # warn mode: check if a healthier peer is available for transparent fallback
        fallback = self._get_triad_fallback(resolved_target, snapshot, task.task_type)
        if fallback:
            logger.warning(
                "Triad surface %r degraded — transparently rerouting to peer %r (task_type=%s)",
                resolved_target,
                fallback,
                task.task_type,
            )
            task.context["_triad_fallback_from"] = resolved_target
            task.context["_triad_fallback_to"] = fallback
            task.context["_triad_fallback_reason"] = "triad_warn_fallback"
            task.context["triad_readiness"] = snapshot
            # Mutate target so _handle_route_execution uses the peer
            task.context["target_system"] = fallback
            return snapshot, None  # None = not blocked; caller will see mutated context

        return snapshot, None

    @staticmethod
    def _normalize_copilot_surface(value: Any) -> str:
        raw = str(value or "").strip().lower()
        if raw in {"", "auto", "default"}:
            return "auto"
        aliases = {
            "cli": "cli",
            "copilot_cli": "cli",
            "bridge": "bridge",
            "extension": "bridge",
            "copilot_extension": "bridge",
            "api": "bridge",
            "live": "bridge",
            "mock": "bridge",
            "chat": "chat_ui",
            "ui": "chat_ui",
            "vscode": "chat_ui",
            "vscode_chat": "chat_ui",
            "copilot_chat": "chat_ui",
            "chat_ui": "chat_ui",
        }
        return aliases.get(raw, "auto")

    def _resolve_copilot_surface(self, task: OrchestrationTask) -> str:
        requested = (
            task.context.get("copilot_surface")
            or task.context.get("execution_surface")
            or os.getenv("NUSYQ_COPILOT_SURFACE", "auto")
        )
        return self._normalize_copilot_surface(requested)

    @staticmethod
    def _copilot_contract_fields(
        *,
        requested_surface: str,
        execution_surface: str,
        execution_path: str | None,
    ) -> dict[str, Any]:
        return {
            "agent_identity": "github_copilot",
            "provider": "github",
            "requested_surface": requested_surface,
            "execution_surface": execution_surface,
            "execution_path": execution_path,
            "observed_chat_surface": "vscode_copilot_chat_surface",
            "chat_surface_controllable": False,
        }

    @staticmethod
    def _status_implies_success(status: Any) -> bool:
        normalized = str(status or "").strip().lower()
        return normalized in {
            "success",
            "ok",
            "ready",
            "submitted",
            "completed",
            "complete",
            "healthy",
            "online",
            "passed",
        }

    def _normalize_response_contract(
        self,
        payload: Any,
        *,
        task: OrchestrationTask,
        target_system: TargetSystem,
    ) -> dict[str, Any]:
        """Normalize routed responses into a minimal stable contract."""
        normalized = dict(payload) if isinstance(payload, dict) else {"output": payload}

        status = normalized.get("status")
        if not isinstance(status, str) or not status.strip():
            if normalized.get("error"):
                status = "failed"
            elif isinstance(normalized.get("success"), bool):
                status = "success" if normalized["success"] else "failed"
            else:
                status = "success"
            normalized["status"] = status

        if "success" not in normalized:
            normalized["success"] = self._status_implies_success(normalized["status"])

        normalized.setdefault("task_id", task.task_id)
        normalized.setdefault(
            "system", self._resolve_target_alias(str(normalized.get("system") or target_system))
        )

        delegate_target = normalized.get("delegate_target")
        if isinstance(delegate_target, str) and delegate_target.strip():
            normalized.setdefault("delegated_to", delegate_target.strip())
        if normalized.get("delegated_to") and "delegated_from" not in normalized:
            normalized["delegated_from"] = str(
                normalized.get("system") or self._resolve_target_alias(str(target_system))
            )

        if "output" not in normalized:
            for key in ("message", "response"):
                value = normalized.get(key)
                if value:
                    normalized["output"] = value
                    break
        if "output" not in normalized:
            result_value = normalized.get("result")
            if result_value is not None and not isinstance(result_value, dict):
                normalized["output"] = result_value

        system_key = str(normalized.get("system") or target_system).strip().lower()
        identity_map = {
            "copilot": "github_copilot",
            "codex": "openai_codex",
            "claude": "anthropic_claude",
            "claude_cli": "anthropic_claude",
            "ollama": "ollama_local",
            "lmstudio": "lm_studio",
            "lm_studio": "lm_studio",
            "chatdev": "chatdev_agents",
            "openclaw": "openclaw",
            "skyclaw": "skyclaw",
            "intermediary": "ai_intermediary",
        }
        normalized.setdefault(
            "agent_identity", identity_map.get(system_key, system_key or "unknown")
        )

        execution_path = normalized.get("execution_path")
        if (
            "execution_surface" not in normalized
            and isinstance(execution_path, str)
            and execution_path.strip()
        ):
            execution_surface = execution_path.split(":", 1)[0].strip()
            if execution_surface:
                normalized["execution_surface"] = execution_surface

        return normalized

    def _emit_terminal_event(
        self,
        role: str,
        event_type: str,
        message: str,
        *,
        level: str = "INFO",
        task_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Best-effort structured terminal event emission."""
        try:
            from src.system.agent_awareness import emit as _emit

            payload: dict[str, Any] = {"event_type": event_type}
            if task_id:
                payload["task_id"] = task_id
            if extra:
                payload.update(extra)
            _emit(role, message, level=level, source="agent_task_router", extra=payload)
        except Exception:
            pass

    def _emit_copilot_terminal_event(
        self,
        event_type: str,
        message: str,
        *,
        level: str = "INFO",
        task_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Best-effort structured Copilot terminal event emission."""
        self._emit_terminal_event(
            "copilot",
            event_type,
            message,
            level=level,
            task_id=task_id,
            extra=extra,
        )

    def _record_fallback_event(
        self,
        from_system: str,
        to_system: str,
        task: OrchestrationTask,
        reason: str,
        detail: str | None = None,
    ) -> None:
        """Emit telemetry + quest log entry when a fallback path is used."""
        msg = f"Fallback {from_system} -> {to_system}: {reason}"
        if detail:
            msg += f" ({detail})"
        self._emit_terminal_event(
            "fallback",
            "fallback_used",
            msg,
            level="INFO",
            task_id=task.task_id,
            extra={
                "from": from_system,
                "to": to_system,
                "reason": reason,
                "detail": detail,
            },
        )

        try:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "task_type": "fallback_event",
                "status": "completed",
                "description": f"Fallback from {from_system} to {to_system}",
                "result": {
                    "from": from_system,
                    "to": to_system,
                    "reason": reason,
                    "detail": detail,
                    "task_id": task.task_id,
                },
            }
            self.quest_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.quest_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            # Best-effort: telemetry should not break routing.
            pass

    async def _perform_local_model_fallback(
        self,
        task: OrchestrationTask,
        env_var: str,
        preferred_order: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Attempt to route to a local model as a fallback.

        Uses an environment variable to control behavior:
        - off: do not fallback
        - ollama / lmstudio: force the indicated system
        - auto (default): try ollama first, then lmstudio
        """
        fallback_mode = os.getenv(env_var, "auto").strip().lower()
        if fallback_mode == "off":
            return None

        preferred = preferred_order or ["ollama", "lmstudio"]
        if fallback_mode == "ollama":
            return await self._route_to_ollama(task)
        if fallback_mode == "lmstudio":
            return await self._route_to_lmstudio(task)

        # auto: try preferred order (default: ollama then lmstudio)
        for system in preferred:
            if system == "ollama":
                result = await self._route_to_ollama(task)
            elif system == "lmstudio":
                result = await self._route_to_lmstudio(task)
            else:
                continue
            if result.get("status") == "success":
                return result
        return None

    def _is_rate_limit_error(self, output: str | None) -> bool:
        """Detect typical rate-limit/quota error messages.

        This is intentionally broad to catch various CLI and API error formats.
        """
        if not output:
            return False

        lowered = str(output).lower()

        # Fast checks for known failure patterns
        rate_limit_tokens = [
            "rate limit",
            "rate-limited",
            "too many requests",
            "quota exceeded",
            "quota exhausted",
            "over limit",
            "limit exceeded",
            "throttled",
            "exceeded your quota",
            "429",
        ]

        if any(tok in lowered for tok in rate_limit_tokens):
            return True

        # Some APIs include OpenAI but only indicate rate limit in context
        if "openai" in lowered and any(
            tok in lowered for tok in ["rate limit", "429", "quota", "throttled"]
        ):
            return True

        # Attempt to parse JSON sections for error types/messages
        try:
            parsed = json.loads(output)
            if isinstance(parsed, dict):
                # Some services return structured error details
                msg = json.dumps(parsed).lower()
                if any(tok in msg for tok in rate_limit_tokens):
                    return True
        except Exception:
            pass

        return False

    async def _run_cli_command(
        self,
        cmd: list[str],
        prompt: str,
        timeout_seconds: int,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
    ) -> tuple[int, str, str]:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd or str(self.repo_root),
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes: bytes
        stderr_bytes: bytes
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(prompt.encode("utf-8")),
                timeout=timeout_seconds,
            )
        except TimeoutError as exc:
            with contextlib.suppress(ProcessLookupError):
                process.kill()
            raise TimeoutError() from exc

        stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
        return_code = process.returncode if process.returncode is not None else 1
        return return_code, stdout, stderr

    async def _route_to_copilot(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to Copilot bridge when explicitly requested.

        Note: direct Copilot Chat control is not exposed by this runtime by default;
        this handler makes that limitation explicit instead of silently routing to auto.
        """
        logger.info(f"🧩 Routing to Copilot: {task.content}")

        # ── Persistent rate-limit bypass ──────────────────────────────────────
        try:
            from src.utils.rate_limit_guard import \
                get_rate_limit_guard as _get_rlg_cop2

            _cop_guard = _get_rlg_cop2()
            if _cop_guard.is_rate_limited("copilot"):
                _cop_limited = _cop_guard.get_limited_agents()
                _cop_entry: dict[str, object] = next(
                    (e for e in _cop_limited if e["agent"] == "copilot"), {}
                )
                _cop_remaining = _cop_entry.get("remaining_hours", "?")
                logger.warning(
                    "Copilot rate-limited (≈%sh remaining) — routing to local fallback",
                    _cop_remaining,
                )
                self._record_fallback_event(
                    "copilot",
                    "local_models",
                    task,
                    "rate_limit_guard",
                    detail=f"remaining_hours={_cop_remaining}",
                )
                fallback = await self._perform_local_model_fallback(task, "NUSYQ_COPILOT_FALLBACK")
                if fallback:
                    fallback["_copilot_fallback"] = True
                    fallback["_copilot_rate_limit_remaining_hours"] = _cop_remaining
                    return fallback
        except Exception as _cop_guard_exc:
            logger.debug("Copilot rate-limit guard check failed (non-fatal): %s", _cop_guard_exc)

        requested_surface = self._resolve_copilot_surface(task)

        if self._looks_like_gitkraken_task(task):
            delegated = await self._route_to_gitkraken(task)
            delegated["system"] = "copilot"
            delegated["delegate_target"] = "gitkraken"
            delegated["delegated_to"] = "gitkraken"
            delegated["delegated_from"] = "copilot"
            delegated.update(
                self._copilot_contract_fields(
                    requested_surface=requested_surface,
                    execution_surface="git_delegation",
                    execution_path=str(delegated.get("execution_path") or "gitkraken_bridge"),
                )
            )
            delegated.setdefault(
                "note",
                "Copilot delegated this git operation to the executable GitKraken MCP path.",
            )
            return delegated

        if requested_surface == "chat_ui":
            return {
                "status": "failed",
                "system": "copilot",
                "task_id": task.task_id,
                "error": (
                    "The VS Code Copilot Chat surface is observable from this runtime, "
                    "but it is not a directly controllable router execution surface."
                ),
                "suggestion": (
                    "Use `copilot_surface=cli` for routed CLI execution, "
                    "`copilot_surface=bridge` for API bridging, or drive Copilot Chat manually in VS Code."
                ),
                "handoff": {
                    "watcher_task": "Watch Copilot Terminal",
                    "watcher_script": "data/terminal_watchers/watch_copilot_terminal.ps1",
                },
                **self._copilot_contract_fields(
                    requested_surface=requested_surface,
                    execution_surface="vscode_copilot_chat_surface",
                    execution_path="observed_only:vscode_copilot_chat",
                ),
            }

        copilot_bin = shutil.which("copilot")
        if copilot_bin and requested_surface in {"auto", "cli"}:
            timeout_seconds = self._adaptive_timeout(
                int(
                    task.context.get(
                        "timeout_seconds",
                        os.getenv("NUSYQ_COPILOT_ROUTER_TIMEOUT_S", "300"),
                    )
                )
            )
            prompt = self._build_cli_prompt(task)
            model = (
                str(
                    task.context.get("copilot_model")
                    or task.context.get("model")
                    or os.getenv("NUSYQ_COPILOT_DEFAULT_MODEL", "gpt-5-mini")
                ).strip()
                or "gpt-5-mini"
            )
            cmd = [
                copilot_bin,
                "-p",
                prompt,
                "--allow-all-tools",
                "--output-format",
                "text",
                "-s",
                "--model",
                model,
            ]
            # Support custom agent extensions (--agent raptor, --agent gpt-X, etc.)
            copilot_agent = str(
                task.context.get("copilot_agent")
                or task.context.get("agent_extension")
                or os.getenv("NUSYQ_COPILOT_DEFAULT_AGENT", "")
            ).strip()
            if copilot_agent:
                cmd.extend(["--agent", copilot_agent])
            # Support extra MCP servers via --additional-mcp-config
            mcp_config = task.context.get("copilot_mcp_config") or task.context.get("mcp_config")
            if mcp_config:
                mcp_str = mcp_config if isinstance(mcp_config, str) else json.dumps(mcp_config)
                cmd.extend(["--additional-mcp-config", mcp_str])
            # GitHub MCP toolset expansion
            enable_github_mcp = bool(
                task.context.get("enable_all_github_mcp_tools")
                or os.getenv("NUSYQ_COPILOT_ENABLE_GITHUB_MCP", "false").lower() == "true"
            )
            if enable_github_mcp:
                cmd.append("--enable-all-github-mcp-tools")
            cli_env = self._build_copilot_cli_env()
            self._emit_copilot_terminal_event(
                "copilot_cli_start",
                f"copilot_cli start model={model} agent={copilot_agent or 'default'} timeout={timeout_seconds}s",
                task_id=task.task_id,
                extra={"model": model, "execution_path": "copilot_cli"},
            )
            try:
                returncode, stdout, stderr = await self._run_cli_command(
                    cmd,
                    "",
                    timeout_seconds,
                    env=cli_env,
                )
                output = stdout.strip()
                stderr_tail = stderr[-1200:]
                lower_error = stderr.lower()
                if returncode == 0 and output:
                    self._emit_copilot_terminal_event(
                        "copilot_cli_success",
                        f"copilot_cli success model={model} chars={len(output)}",
                        task_id=task.task_id,
                        extra={"model": model, "output_chars": len(output)},
                    )
                    return {
                        "status": "success",
                        "system": "copilot",
                        "task_id": task.task_id,
                        "output": output,
                        "model": model,
                        **self._copilot_contract_fields(
                            requested_surface=requested_surface,
                            execution_surface="copilot_cli",
                            execution_path="copilot_cli",
                        ),
                    }
                if (
                    "rate limit" in lower_error
                    or "429" in lower_error
                    or "too many requests" in lower_error
                ):
                    self._emit_copilot_terminal_event(
                        "copilot_cli_rate_limited",
                        "copilot_cli rate-limited (HTTP 429) — routing to local fallback",
                        level="WARNING",
                        task_id=task.task_id,
                        extra={"model": model, "stderr_tail": stderr_tail},
                    )
                    # Persist the rate-limit state so future calls bypass Copilot immediately
                    try:
                        from src.utils.rate_limit_guard import \
                            get_rate_limit_guard as _get_rlg_cop

                        _cop_rl_hours = float(os.getenv("NUSYQ_COPILOT_RATE_LIMIT_HOURS", "1.0"))
                        _get_rlg_cop().mark_rate_limited(
                            "copilot",
                            duration_hours=_cop_rl_hours,
                            reason="rate_limit_detected_in_stderr",
                        )
                    except Exception as _cop_rl_exc:
                        logger.debug(
                            "Copilot rate-limit persist failed (non-fatal): %s", _cop_rl_exc
                        )
                    # Try local fallback before giving up
                    _copilot_fallback_mode = (
                        os.getenv("NUSYQ_COPILOT_FALLBACK", "auto").strip().lower()
                    )
                    if _copilot_fallback_mode != "off":
                        _cop_fb = await self._route_to_ollama(task)
                        if _cop_fb.get("status") != "success":
                            _cop_fb = await self._route_to_lmstudio(task)
                        if _cop_fb.get("status") == "success":
                            _cop_fb["_copilot_fallback"] = True
                            _cop_fb["_copilot_fallback_reason"] = "rate_limited"
                            return _cop_fb
                    return {
                        "status": "failed",
                        "system": "copilot",
                        "task_id": task.task_id,
                        "error": "copilot_cli_rate_limited",
                        "note": (
                            "Copilot is authenticated but rate-limited. "
                            "Auth is working — quota exhausted for this period. "
                            "Try: --agent raptor (uses different quota) or wait for reset."
                        ),
                        "suggestion": (
                            "Use --agent raptor or another Copilot extension agent. "
                            "Or delegate to ollama/lmstudio/claude_cli via triad fallback."
                        ),
                        "stderr": stderr_tail,
                        **self._copilot_contract_fields(
                            requested_surface=requested_surface,
                            execution_surface="copilot_cli",
                            execution_path="copilot_cli",
                        ),
                    }
                if (
                    "no authentication information found" in lower_error
                    or "authentication failed" in lower_error
                ):
                    self._emit_copilot_terminal_event(
                        "copilot_cli_auth_failed",
                        "copilot_cli auth invalid or missing",
                        level="WARNING",
                        task_id=task.task_id,
                        extra={"model": model, "stderr_tail": stderr_tail},
                    )
                    return {
                        "status": "failed",
                        "system": "copilot",
                        "task_id": task.task_id,
                        "error": "copilot_cli_auth_invalid_or_missing",
                        "suggestion": "Run `copilot login` in this environment to restore CLI auth.",
                        "stderr": stderr_tail,
                        "handoff": {
                            "watcher_task": "Watch Copilot Terminal",
                            "watcher_script": "data/terminal_watchers/watch_copilot_terminal.ps1",
                        },
                        **self._copilot_contract_fields(
                            requested_surface=requested_surface,
                            execution_surface="copilot_cli",
                            execution_path="copilot_cli",
                        ),
                    }
                if "copilot requests" in lower_error:
                    self._emit_copilot_terminal_event(
                        "copilot_cli_permission_failed",
                        "copilot_cli token missing Copilot Requests permission",
                        level="WARNING",
                        task_id=task.task_id,
                        extra={"model": model, "stderr_tail": stderr_tail},
                    )
                    return {
                        "status": "failed",
                        "system": "copilot",
                        "task_id": task.task_id,
                        "error": "copilot_cli_token_missing_copilot_requests_permission",
                        "suggestion": (
                            "Use Copilot CLI OAuth login or a COPILOT_GITHUB_TOKEN with Copilot Requests permission."
                        ),
                        "stderr": stderr_tail,
                        **self._copilot_contract_fields(
                            requested_surface=requested_surface,
                            execution_surface="copilot_cli",
                            execution_path="copilot_cli",
                        ),
                    }
                self._emit_copilot_terminal_event(
                    "copilot_cli_failed",
                    f"copilot_cli failed rc={returncode}",
                    level="WARNING",
                    task_id=task.task_id,
                    extra={
                        "model": model,
                        "stderr_tail": stderr_tail,
                        "stdout_tail": stdout[-1200:],
                    },
                )
                return {
                    "status": "failed",
                    "system": "copilot",
                    "task_id": task.task_id,
                    "error": (
                        f"copilot_cli_failed rc={returncode} stderr_tail={stderr_tail!r} stdout_tail={stdout[-1200:]!r}"
                    ),
                    **self._copilot_contract_fields(
                        requested_surface=requested_surface,
                        execution_surface="copilot_cli",
                        execution_path="copilot_cli",
                    ),
                }
            except TimeoutError:
                self._emit_copilot_terminal_event(
                    "copilot_cli_timeout",
                    f"copilot_cli timeout>{timeout_seconds}s",
                    level="WARNING",
                    task_id=task.task_id,
                    extra={"model": model},
                )
                return {
                    "status": "failed",
                    "system": "copilot",
                    "task_id": task.task_id,
                    "error": f"copilot_cli_timeout>{timeout_seconds}s",
                    **self._copilot_contract_fields(
                        requested_surface=requested_surface,
                        execution_surface="copilot_cli",
                        execution_path="copilot_cli",
                    ),
                }
            except OSError as exc:
                self._emit_copilot_terminal_event(
                    "copilot_cli_error",
                    f"copilot_cli error: {exc}",
                    level="ERROR",
                    task_id=task.task_id,
                    extra={"model": model},
                )
                return {
                    "status": "failed",
                    "system": "copilot",
                    "task_id": task.task_id,
                    "error": f"copilot_cli_error:{exc}",
                    **self._copilot_contract_fields(
                        requested_surface=requested_surface,
                        execution_surface="copilot_cli",
                        execution_path="copilot_cli",
                    ),
                }

        if requested_surface == "cli" and not copilot_bin:
            return {
                "status": "failed",
                "system": "copilot",
                "task_id": task.task_id,
                "error": "copilot_cli_not_found",
                "suggestion": "Install or expose the `copilot` CLI on PATH, or switch to `copilot_surface=bridge`.",
                **self._copilot_contract_fields(
                    requested_surface=requested_surface,
                    execution_surface="copilot_cli",
                    execution_path="copilot_cli",
                ),
            }

        bridge_mode = os.getenv("NUSYQ_COPILOT_BRIDGE_MODE", "disabled").lower()
        if bridge_mode == "disabled":
            return {
                "status": "failed",
                "system": "copilot",
                "task_id": task.task_id,
                "error": (
                    "Direct Copilot chat control is not enabled in this runtime. "
                    "Set NUSYQ_COPILOT_BRIDGE_MODE=live to attempt API bridging."
                ),
                "suggestion": (
                    "Use VS Code Copilot Chat UI for interactive conversation, or route to "
                    "ollama/chatdev for agent-executable handling."
                ),
                "handoff": {
                    "watcher_task": "Watch Copilot Terminal",
                    "watcher_script": "data/terminal_watchers/watch_copilot_terminal.ps1",
                },
                **self._copilot_contract_fields(
                    requested_surface=requested_surface,
                    execution_surface="copilot_bridge",
                    execution_path="copilot_bridge:disabled",
                ),
            }

        if bridge_mode == "mock":
            return {
                "status": "success",
                "system": "copilot",
                "task_id": task.task_id,
                "output": {
                    "mode": "mock",
                    "echo": task.content,
                },
                "note": "Mock Copilot bridge executed (no external API call).",
                **self._copilot_contract_fields(
                    requested_surface=requested_surface,
                    execution_surface="copilot_bridge",
                    execution_path="copilot_bridge:mock",
                ),
            }

        try:
            from src.copilot.extension.copilot_extension import \
                CopilotExtension
        except ImportError as exc:
            return {
                "status": "failed",
                "system": "copilot",
                "task_id": task.task_id,
                "error": f"Copilot bridge import failed: {exc}",
                **self._copilot_contract_fields(
                    requested_surface=requested_surface,
                    execution_surface="copilot_bridge",
                    execution_path="copilot_bridge:import_error",
                ),
            }

        extension = CopilotExtension()
        response: dict[str, Any] | None = None
        try:
            await extension.activate()
            # Inject orchestration manifest when orchestration_mode is active
            copilot_prompt = task.content
            if bool(task.context.get("orchestration_mode")) or task.task_type == "orchestrate":
                orch_block = self._build_orchestration_block(task)
                if orch_block:
                    copilot_prompt = orch_block + "\n\n" + copilot_prompt
            response = await extension.send_query(copilot_prompt)
        except Exception as exc:
            return {
                "status": "failed",
                "system": "copilot",
                "task_id": task.task_id,
                "error": f"Copilot bridge request failed: {exc}",
                **self._copilot_contract_fields(
                    requested_surface=requested_surface,
                    execution_surface="copilot_bridge",
                    execution_path="copilot_bridge:request_error",
                ),
            }
        finally:
            with contextlib.suppress(Exception):
                await extension.close()

        if response is None:
            return {
                "status": "failed",
                "system": "copilot",
                "task_id": task.task_id,
                "error": (
                    "Copilot bridge returned no response. "
                    "Check GITHUB_COPILOT_API_KEY and bridge endpoint configuration."
                ),
                **self._copilot_contract_fields(
                    requested_surface=requested_surface,
                    execution_surface="copilot_bridge",
                    execution_path=f"copilot_bridge:{bridge_mode or 'live'}",
                ),
            }

        return {
            "status": "success",
            "system": "copilot",
            "task_id": task.task_id,
            "output": response,
            **self._copilot_contract_fields(
                requested_surface=requested_surface,
                execution_surface="copilot_bridge",
                execution_path=f"copilot_bridge:{bridge_mode or 'live'}",
            ),
        }

    async def _route_to_codex(self, task: OrchestrationTask) -> dict[str, Any]:
        logger.info("🧠 Routing to Codex CLI: %s", task.content)

        # ── Persistent rate-limit bypass ──────────────────────────────────────
        # If a previous call detected Codex is rate-limited, skip it and go
        # straight to local-model fallback for the duration of the window.
        try:
            from src.utils.rate_limit_guard import get_rate_limit_guard

            _rl_guard = get_rate_limit_guard()
            if _rl_guard.is_rate_limited("codex"):
                limited_agents = _rl_guard.get_limited_agents()
                codex_entry = next((e for e in limited_agents if e["agent"] == "codex"), {})
                remaining_h = codex_entry.get("remaining_hours", "?")
                self._record_fallback_event(
                    "codex",
                    "local_models",
                    task,
                    "rate_limit_guard",
                    detail=f"remaining_hours={remaining_h}",
                )
                result = await self._perform_local_model_fallback(task, "NUSYQ_CODEX_FALLBACK")
                if result:
                    result["_codex_fallback"] = True
                    result["_codex_rate_limit_remaining_hours"] = remaining_h
                    return result
                return {
                    "status": "failed",
                    "system": "codex",
                    "task_id": task.task_id,
                    "error": "codex_rate_limited",
                    "execution_path": "codex_rate_limit_bypass",
                    "note": f"Codex rate-limited for ≈{remaining_h}h. Set NUSYQ_CODEX_FALLBACK=ollama to auto-route.",
                }
        except Exception as _rl_exc:
            logger.debug("Rate-limit guard check failed (non-fatal): %s", _rl_exc)

        codex_bin = shutil.which("codex")
        if not codex_bin:
            self._record_fallback_event(
                "codex",
                "local_models",
                task,
                "cli_not_found",
                detail="codex_cli not found on PATH",
            )
            # Codex not installed: try local models if fallback is enabled
            fb = await self._perform_local_model_fallback(task, "NUSYQ_CODEX_FALLBACK")
            if fb:
                fb["_codex_fallback"] = True
                fb["_codex_fallback_reason"] = "codex_cli_not_found"
                return fb
            return {
                "status": "failed",
                "system": "codex",
                "task_id": task.task_id,
                "error": "codex_cli_not_found",
                "execution_path": "codex_cli",
                "handoff": {
                    "watcher_task": "Watch Codex Terminal",
                    "watcher_script": "data/terminal_watchers/watch_codex_terminal.ps1",
                },
            }

        async def _try_fallback() -> dict[str, Any] | None:
            return await self._perform_local_model_fallback(task, "NUSYQ_CODEX_FALLBACK")

        timeout_seconds = self._adaptive_timeout(
            int(
                task.context.get(
                    "timeout_seconds", os.getenv("NUSYQ_CODEX_ROUTER_TIMEOUT_S", "300")
                )
            )
        )
        prompt = self._build_cli_prompt(task)
        output_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                suffix="_router_codex_output.txt",
                encoding="utf-8",
            ) as temp_output:
                output_path = Path(temp_output.name)

            cmd = [
                codex_bin,
                "exec",
                "-",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--ephemeral",
                "--output-last-message",
                str(output_path),
            ]
            self._emit_terminal_event(
                "codex",
                "codex_cli_start",
                f"codex_cli start timeout={timeout_seconds}s",
                task_id=task.task_id,
                extra={"execution_path": "codex_cli"},
            )

            returncode, stdout, stderr = await self._run_cli_command(cmd, prompt, timeout_seconds)
            output = ""
            if output_path.exists():
                output = output_path.read_text(encoding="utf-8", errors="replace").strip()
            if not output:
                output = stdout

            if returncode == 0 and output:
                self._emit_terminal_event(
                    "codex",
                    "codex_cli_success",
                    f"codex_cli success chars={len(output)}",
                    task_id=task.task_id,
                    extra={"execution_path": "codex_cli", "output_chars": len(output)},
                )
                return {
                    "status": "success",
                    "system": "codex",
                    "task_id": task.task_id,
                    "output": output,
                    "execution_path": "codex_cli",
                }

            # If rate-limited, persist state + attempt fallback.
            if self._is_rate_limit_error(stderr) or self._is_rate_limit_error(stdout):
                self._record_fallback_event(
                    "codex",
                    "ollama",
                    task,
                    "rate_limit_detected",
                    detail=(stderr or stdout),
                )

                # Persist so subsequent calls skip Codex immediately.
                try:
                    from src.utils.rate_limit_guard import \
                        get_rate_limit_guard as _get_rlg

                    _rate_limit_hours = float(os.getenv("NUSYQ_CODEX_RATE_LIMIT_HOURS", "72"))
                    _get_rlg().mark_rate_limited(
                        "codex",
                        duration_hours=_rate_limit_hours,
                        reason="rate_limit_detected_in_output",
                    )
                except Exception as _rl_err:
                    logger.debug("Could not persist codex rate-limit state: %s", _rl_err)

                fallback_result = await _try_fallback()
                if fallback_result:
                    fallback_result["_codex_fallback"] = True
                    fallback_result["_codex_fallback_reason"] = "rate_limited"
                    return fallback_result

            self._emit_terminal_event(
                "codex",
                "codex_cli_failed",
                f"codex_cli failed rc={returncode}",
                level="WARNING",
                task_id=task.task_id,
                extra={"execution_path": "codex_cli", "returncode": returncode},
            )
            return {
                "status": "failed",
                "system": "codex",
                "task_id": task.task_id,
                "execution_path": "codex_cli",
                "error": (
                    f"codex_exec_failed rc={returncode} stderr_tail={stderr[-1200:]!r} stdout_tail={stdout[-1200:]!r}"
                ),
            }
        except TimeoutError:
            self._emit_terminal_event(
                "codex",
                "codex_cli_timeout",
                f"codex_cli timeout>{timeout_seconds}s — attempting local model fallback",
                level="WARNING",
                task_id=task.task_id,
                extra={"execution_path": "codex_cli"},
            )
            self._record_fallback_event(
                "codex",
                "local_models",
                task,
                "timeout",
                detail=f"timeout_seconds={timeout_seconds}",
            )
            # On timeout, try local models (Codex may be overloaded / rate-limited).
            timeout_fallback = await _try_fallback()
            if timeout_fallback:
                timeout_fallback["_codex_fallback"] = True
                timeout_fallback["_codex_fallback_reason"] = "timeout"
                return timeout_fallback
            return {
                "status": "failed",
                "system": "codex",
                "task_id": task.task_id,
                "execution_path": "codex_cli",
                "error": f"codex_exec_timeout>{timeout_seconds}s",
            }
        except OSError as exc:
            self._emit_terminal_event(
                "codex",
                "codex_cli_error",
                f"codex_cli error: {exc}",
                level="WARNING",
                task_id=task.task_id,
                extra={"execution_path": "codex_cli"},
            )
            self._record_fallback_event(
                "codex",
                "local_models",
                task,
                "cli_error",
                detail=str(exc),
            )
            # Attempt fallback on codex CLI errors (network issues / rate limits)
            fallback_result = await _try_fallback()
            if fallback_result:
                return fallback_result
            return {
                "status": "failed",
                "system": "codex",
                "task_id": task.task_id,
                "execution_path": "codex_cli",
                "error": f"codex_exec_error:{exc}",
            }
        finally:
            if output_path is not None:
                with contextlib.suppress(OSError):
                    output_path.unlink()

    async def _route_to_claude_cli(self, task: OrchestrationTask) -> dict[str, Any]:
        logger.info("🧠 Routing to Claude: %s", task.content)

        # ── Persistent rate-limit bypass ──────────────────────────────────────
        try:
            from src.utils.rate_limit_guard import \
                get_rate_limit_guard as _get_rlg_claude

            _rl = _get_rlg_claude()
            if _rl.is_rate_limited("claude_cli"):
                limited = _rl.get_limited_agents()
                entry = next((e for e in limited if e["agent"] == "claude_cli"), {})
                remaining_h = entry.get("remaining_hours", "?")
                self._record_fallback_event(
                    "claude_cli",
                    "local_models",
                    task,
                    "rate_limit_guard",
                    detail=f"remaining_hours={remaining_h}",
                )
                fallback = await self._perform_local_model_fallback(task, "NUSYQ_CLAUDE_FALLBACK")
                if fallback:
                    fallback["_claude_fallback"] = True
                    fallback["_claude_rate_limit_remaining_hours"] = remaining_h
                    return fallback
                return {
                    "status": "failed",
                    "system": "claude_cli",
                    "task_id": task.task_id,
                    "error": "claude_cli_rate_limited",
                    "note": f"Claude rate-limited for ≈{remaining_h}h. Set NUSYQ_CLAUDE_FALLBACK=ollama to auto-route.",
                }
        except Exception as _rl_exc:
            logger.debug("Claude rate-limit guard check failed (non-fatal): %s", _rl_exc)

        prompt = self._build_cli_prompt(task)
        timeout_seconds = self._adaptive_timeout(
            int(
                task.context.get(
                    "timeout_seconds",
                    os.getenv("NUSYQ_CLAUDE_ROUTER_TIMEOUT_S", "300"),
                )
            )
        )
        custom_cmd = str(os.getenv("NUSYQ_CLAUDE_CLI_COMMAND", "")).strip()
        cli_errors: list[str] = []
        cli_env = self._build_claude_cli_env()

        if custom_cmd:
            cmd = shlex.split(custom_cmd.format(prompt=prompt, task_id=task.task_id))
            if not cmd:
                self._emit_terminal_event(
                    "claude",
                    "claude_cli_command_empty",
                    "claude_cli command template resolved to empty command",
                    level="WARNING",
                    task_id=task.task_id,
                )
                return {
                    "status": "failed",
                    "system": "claude_cli",
                    "task_id": task.task_id,
                    "error": "claude_cli_command_empty",
                    "execution_path": "claude_cli_custom",
                }
            try:
                self._emit_terminal_event(
                    "claude",
                    "claude_cli_start",
                    f"claude_cli start timeout={timeout_seconds}s",
                    task_id=task.task_id,
                    extra={"execution_path": "claude_cli_custom"},
                )
                returncode, stdout, stderr = await self._run_cli_command(
                    cmd, prompt, timeout_seconds, env=cli_env
                )
            except TimeoutError:
                self._emit_terminal_event(
                    "claude",
                    "claude_cli_timeout",
                    f"claude_cli timeout>{timeout_seconds}s",
                    level="WARNING",
                    task_id=task.task_id,
                    extra={"execution_path": "claude_cli_custom"},
                )
                return {
                    "status": "failed",
                    "system": "claude_cli",
                    "task_id": task.task_id,
                    "error": f"claude_exec_timeout>{timeout_seconds}s",
                    "execution_path": "claude_cli_custom",
                }
            except OSError as exc:
                self._emit_terminal_event(
                    "claude",
                    "claude_cli_error",
                    f"claude_cli error: {exc}",
                    level="WARNING",
                    task_id=task.task_id,
                    extra={"execution_path": "claude_cli_custom"},
                )
                return {
                    "status": "failed",
                    "system": "claude_cli",
                    "task_id": task.task_id,
                    "error": f"claude_exec_error:{exc}",
                    "execution_path": "claude_cli_custom",
                }

            output = stdout or stderr
            if returncode == 0 and output:
                self._emit_terminal_event(
                    "claude",
                    "claude_cli_success",
                    f"claude_cli success chars={len(output)}",
                    task_id=task.task_id,
                    extra={"execution_path": "claude_cli_custom", "output_chars": len(output)},
                )
                return {
                    "status": "success",
                    "system": "claude_cli",
                    "task_id": task.task_id,
                    "output": output,
                    "mode": "cli",
                    "execution_path": "claude_cli_custom",
                }
            cli_errors.append(
                f"claude_exec_failed rc={returncode} stderr_tail={stderr[-1200:]!r} stdout_tail={stdout[-1200:]!r}"
            )

        else:
            cmd_candidates: list[tuple[list[str], str]] = []
            claude_bin = shutil.which("claude")
            if claude_bin:
                cmd_candidates.append(
                    (
                        [
                            claude_bin,
                            "--print",
                            "--no-session-persistence",
                            "--output-format",
                            "text",
                            "--add-dir",
                            str(self.repo_root),
                            "--",
                            prompt,
                        ],
                        "",
                    )
                )

            if self._is_wsl_runtime():
                cmd_exe = shutil.which("cmd.exe")
                claude_cmd = shutil.which("claude.cmd")
                if cmd_exe and claude_cmd:
                    cmd_candidates.append(
                        (
                            [
                                cmd_exe,
                                "/d",
                                "/s",
                                "/c",
                                "set ANTHROPIC_API_KEY=&& claude.cmd --print --output-format text",
                            ],
                            prompt,
                        )
                    )

            # Fallback: Check VS Code Claude Code extension for native binary
            if not cmd_candidates:
                vscode_ext_dir = Path.home() / ".vscode" / "extensions"
                if vscode_ext_dir.exists():
                    claude_ext_dirs = sorted(
                        vscode_ext_dir.glob("anthropic.claude-code-*"),
                        key=lambda p: p.name,
                        reverse=True,
                    )
                    for ext_dir in claude_ext_dirs:
                        native_binary = ext_dir / "resources" / "native-binary" / "claude.exe"
                        if native_binary.exists():
                            cmd_candidates.append(
                                (
                                    [
                                        str(native_binary),
                                        "--print",
                                        "--output-format",
                                        "text",
                                        prompt,
                                    ],
                                    "",
                                )
                            )
                            break

            for cmd, cli_prompt in cmd_candidates:
                execution_path = "claude_cli"
                try:
                    self._emit_terminal_event(
                        "claude",
                        "claude_cli_start",
                        f"claude_cli start timeout={timeout_seconds}s",
                        task_id=task.task_id,
                        extra={"execution_path": execution_path},
                    )
                    returncode, stdout, stderr = await self._run_cli_command(
                        cmd,
                        cli_prompt,
                        timeout_seconds,
                        env=cli_env,
                        cwd=tempfile.gettempdir(),
                    )
                except TimeoutError:
                    self._emit_terminal_event(
                        "claude",
                        "claude_cli_timeout",
                        f"claude_cli timeout>{timeout_seconds}s",
                        level="WARNING",
                        task_id=task.task_id,
                        extra={"execution_path": execution_path},
                    )
                    cli_errors.append(f"claude_exec_timeout>{timeout_seconds}s")
                    continue
                except OSError as exc:
                    self._emit_terminal_event(
                        "claude",
                        "claude_cli_error",
                        f"claude_cli error: {exc}",
                        level="WARNING",
                        task_id=task.task_id,
                        extra={"execution_path": execution_path},
                    )
                    cli_errors.append(f"claude_exec_error:{exc}")
                    continue

                output = stdout or stderr
                if returncode == 0 and output:
                    self._emit_terminal_event(
                        "claude",
                        "claude_cli_success",
                        f"claude_cli success chars={len(output)}",
                        task_id=task.task_id,
                        extra={"execution_path": execution_path, "output_chars": len(output)},
                    )
                    return {
                        "status": "success",
                        "system": "claude_cli",
                        "task_id": task.task_id,
                        "output": output,
                        "mode": "cli",
                        "execution_path": execution_path,
                    }
                cli_error = f"claude_exec_failed rc={returncode} stderr_tail={stderr[-1200:]!r} stdout_tail={stdout[-1200:]!r}"
                self._emit_terminal_event(
                    "claude",
                    "claude_cli_failed",
                    f"claude_cli failed rc={returncode}",
                    level="WARNING",
                    task_id=task.task_id,
                    extra={"execution_path": execution_path, "returncode": returncode},
                )
                cli_errors.append(cli_error)

                auth_text = f"{stdout}\n{stderr}".lower()
                if any(
                    marker in auth_text
                    for marker in (
                        "oauth token has expired",
                        "not logged in",
                        "please run /login",
                        "invalid api key",
                        "failed to authenticate",
                    )
                ):
                    break

            auth_failure = any(
                marker in err.lower()
                for err in cli_errors
                for marker in (
                    "oauth token has expired",
                    "not logged in",
                    "please run /login",
                    "invalid api key",
                    "failed to authenticate",
                )
            )
            if auth_failure:
                self._emit_terminal_event(
                    "claude",
                    "claude_cli_auth_failed",
                    "claude_cli auth invalid or expired",
                    level="WARNING",
                    task_id=task.task_id,
                    extra={"execution_path": "claude_cli"},
                )
                return {
                    "status": "failed",
                    "system": "claude_cli",
                    "task_id": task.task_id,
                    "error": (
                        "Claude CLI authentication is invalid or expired. "
                        "Run: `set ANTHROPIC_API_KEY=& claude auth login` (Windows) "
                        "or clear ANTHROPIC_API_KEY placeholder before launching Claude. "
                        + " | ".join(cli_errors)
                    ),
                    "mode": "cli",
                    "execution_path": "claude_cli",
                    "handoff": {
                        "watcher_task": "Watch Claude Terminal",
                        "watcher_script": "data/terminal_watchers/watch_claude_terminal.ps1",
                    },
                }

        try:
            from src.orchestration.claude_orchestrator import \
                ClaudeOrchestrator
        except ImportError as exc:
            self._emit_terminal_event(
                "claude",
                "claude_orchestrator_import_failed",
                f"claude_orchestrator import failed: {exc}",
                level="WARNING",
                task_id=task.task_id,
            )
            return {
                "status": "failed",
                "system": "claude_cli",
                "task_id": task.task_id,
                "error": f"claude_orchestrator_import_failed: {exc}",
                "execution_path": "claude_orchestrator",
                "handoff": {
                    "watcher_task": "Watch Claude Terminal",
                    "watcher_script": "data/terminal_watchers/watch_claude_terminal.ps1",
                },
            }

        orchestrator = ClaudeOrchestrator(repo_root=self.repo_root)
        response = await orchestrator.ask_claude(
            prompt=prompt,
            model=task.context.get("claude_model"),
            max_tokens=int(task.context.get("max_tokens", 512)),
            temperature=float(task.context.get("temperature", 0.3)),
        )
        error = response.get("error")
        if error:
            details = [str(error)]
            details.extend(cli_errors)
            _combined_err = " | ".join(detail for detail in details if detail)
            _err_lower = _combined_err.lower()
            # Detect rate-limit / quota-exhausted responses and persist + fallback
            if any(
                marker in _err_lower
                for marker in (
                    "rate limit",
                    "429",
                    "too many requests",
                    "quota exceeded",
                    "overloaded",
                )
            ):
                try:
                    from src.utils.rate_limit_guard import \
                        get_rate_limit_guard as _get_rlg_cl2

                    _cl_rl_hours = float(os.getenv("NUSYQ_CLAUDE_RATE_LIMIT_HOURS", "1.0"))
                    _get_rlg_cl2().mark_rate_limited(
                        "claude_cli",
                        duration_hours=_cl_rl_hours,
                        reason="rate_limit_detected_in_orchestrator_response",
                    )
                except Exception as _cl_rl_exc:
                    logger.debug("Claude rate-limit persist failed (non-fatal): %s", _cl_rl_exc)
                _claude_fb_mode = os.getenv("NUSYQ_CLAUDE_FALLBACK", "auto").strip().lower()
                if _claude_fb_mode != "off":
                    _cl_fb = await self._route_to_ollama(task)
                    if _cl_fb.get("status") != "success":
                        _cl_fb = await self._route_to_lmstudio(task)
                    if _cl_fb.get("status") == "success":
                        _cl_fb["_claude_fallback"] = True
                        _cl_fb["_claude_fallback_reason"] = "rate_limited"
                        return _cl_fb
            return {
                "status": "failed",
                "system": "claude_cli",
                "task_id": task.task_id,
                "error": _combined_err,
                "mode": "api",
                "handoff": {
                    "watcher_task": "Watch Claude Terminal",
                    "watcher_script": "data/terminal_watchers/watch_claude_terminal.ps1",
                },
            }
        return {
            "status": "success",
            "system": "claude_cli",
            "task_id": task.task_id,
            "output": response.get("response", ""),
            "model": response.get("model"),
            "mode": "api",
        }

    @asynccontextmanager
    async def _span(self, name: str, attrs: dict[str, Any] | None = None) -> Any:
        cm: contextlib.AbstractContextManager[Any] = (
            tracing_mod.start_span(name, attrs) if tracing_mod else contextlib.nullcontext()
        )
        with cm:
            yield

    def _emit_receipt(
        self,
        action_id: str,
        inputs: dict[str, Any],
        outputs: list[str],
        status: str,
        exit_code: int,
        next_steps: list[str] | None = None,
    ) -> Path:
        receipts_dir = self.repo_root / "docs" / "tracing" / "RECEIPTS"
        receipts_dir.mkdir(parents=True, exist_ok=True)
        run_id = os.environ.get("NUSYQ_RUN_ID", "run_unknown")
        receipt_path = (
            receipts_dir / f"{action_id}_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.txt"
        )
        receipt_text = f"""[RECEIPT]
action.id: {action_id}
run.id: {run_id}
repo.name: NuSyQ-Hub
repo.path: {self.repo_root}
cwd: {Path.cwd()}
status: {status}
exit_code: {exit_code}
inputs: {inputs}
outputs: {outputs}
next: {next_steps or []}
"""
        receipt_path.write_text(receipt_text, encoding="utf-8")
        logger.info(receipt_text)
        return receipt_path

    def _spine_enabled(self) -> bool:
        """Check if the opt-in NuSyQ spine is enabled in config file.

        This avoids adding a hard dependency on PyYAML; we perform a simple
        text check for the enabled flag in the YAML file.
        """
        try:
            cfg = self.repo_root / "config" / "nusyq_spine.yaml"
            if not cfg.exists():
                return False
            text = cfg.read_text(encoding="utf-8").lower()
            return "enabled: true" in text or "enable: true" in text
        except (OSError, RuntimeError):
            return False

    async def _emit_spine_event(self, event: dict[str, Any]) -> None:
        """Emit an event to the optional NuSyQ spine if enabled (best-effort)."""
        if not self._spine_enabled():
            return
        try:
            from src.nusyq_spine import eventlog as spine_eventlog

            await to_thread(spine_eventlog.emit_event, event)
        except (ImportError, RuntimeError, AttributeError) as exc:
            logger.debug(f"Spine event emission failed (ignored): {exc}")

    async def _consciousness_enrich(
        self, description: str, context: dict[str, Any]
    ) -> ConsciousnessHint | None:
        """Enrich context with consciousness bridge signals.

        Returns a lightweight hint that can be attached to downstream tasks.
        """
        try:
            from src.integration.consciousness_bridge import \
                ConsciousnessBridge
        except ImportError as exc:  # pragma: no cover - optional dependency
            logger.info(f"Consciousness enrichment unavailable: {exc}")
            return None

        def _run_enrich() -> ConsciousnessHint:
            bridge = ConsciousnessBridge()
            bridge.initialize()
            bridge.enhance_contextual_memory({"description": description, "context": context})
            retrieval = bridge.retrieve_contextual_memory(description)
            tags = list(bridge.contextual_memory.keys())
            hint = ConsciousnessHint(
                summary=str(retrieval) if retrieval else "Context enriched",
                tags=tags or None,
                confidence=0.62,
            )

            # Optional: record the agent-created task in the task runtime DB (if available)
            try:
                from src.task_runtime.db import Database

                db = Database()
                db.execute(
                    "INSERT INTO tasks (project_id, objective, metadata, status) VALUES (?, ?, ?, 'in_progress')",
                    (
                        None,
                        description,
                        json.dumps({"source": "agent_task_router", "context": context}),
                    ),
                )
            except (ImportError, RuntimeError, OSError):
                # Task runtime not installed or failed - continue without DB recording
                logger.debug("Suppressed ImportError/OSError/RuntimeError", exc_info=True)

            return hint

        try:
            return await to_thread(_run_enrich)
        except (
            ImportError,
            RuntimeError,
            ValueError,
        ) as exc:  # pragma: no cover - best effort enrichment
            logger.warning(f"Consciousness enrichment failed: {exc}")
            return None

    async def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        def _dump() -> None:
            path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

        await to_thread(_dump)

    async def _append_lines(self, path: Path, lines: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        def _append() -> None:
            with path.open("a", encoding="utf-8") as handle:
                for line in lines:
                    handle.write(line)

        await to_thread(_append)

    def _get_specialization_learner(self) -> Any:
        """Lazy-load SpecializationLearner (offline-capable, tracks agent-task performance)."""
        if self._specialization_learner is None:
            try:
                from src.orchestration.specialization_learner import \
                    SpecializationLearner

                self._specialization_learner = SpecializationLearner()
            except Exception as exc:
                logger.debug(f"SpecializationLearner unavailable: {exc}")
                self._specialization_learner = False  # sentinel — don't retry
        return self._specialization_learner if self._specialization_learner else None

    async def _route_by_system(
        self, task: OrchestrationTask, target_system: TargetSystem
    ) -> dict[str, Any]:
        """Delegate routing to the appropriate system handler.

        Extracted to reduce cognitive complexity of route_task.
        """
        target_system = self._resolve_target_alias(str(target_system))  # type: ignore[assignment]

        # If the caller provided an unknown target, default to orchestrator ('auto')
        if target_system != "auto" and target_system not in self._system_handlers:
            logger.warning(
                f"Unknown target system '{target_system}' — defaulting to 'auto' orchestrator submission"
            )
            target_system = "auto"

        if target_system == "auto":
            # Consult SpecializationLearner: if a specific agent has proven expertise, route directly
            learner = self._get_specialization_learner()
            if learner is not None:
                task_type_str = str(getattr(task, "task_type", "optimization"))
                recommended = learner.get_best_agent_for_task(task_type_str)
                if recommended and recommended in self._system_handlers:
                    logger.info(
                        f"SpecializationLearner recommends '{recommended}' for task_type='{task_type_str}'"
                    )
                    return await self._system_handlers[recommended](task)

            submit_id = self.orchestrator.submit_task(task)
            return {
                "status": "submitted",
                "task_id": submit_id,
                "note": "Task submitted to orchestrator for async execution",
            }

        handler = self._system_handlers.get(target_system)
        if not handler:
            logger.error(f"No handler found for resolved target system: {target_system}")
            return {
                "status": "failed",
                "error": f"Unknown target system: {target_system}",
            }

        dynamic_handler = getattr(self, handler.__name__, None)
        if callable(dynamic_handler):
            routed = await dynamic_handler(task)
            return routed if isinstance(routed, dict) else {"output": routed}
        return await handler(task)

    async def _enrich_hints(
        self,
        task_type: TaskType,
        description: str,
        context: dict[str, Any],
        target_system: TargetSystem,
    ) -> tuple[dict[str, Any] | None, TargetSystem, ConsciousnessHint | None]:
        """Enrich task with efficiency and consciousness hints."""
        efficiency_hint: dict[str, Any] | None = None
        consciousness_hint: ConsciousnessHint | None = None

        if target_system == "auto" and suggest_routing is not None:
            try:
                efficiency_hint = suggest_routing(
                    task_type=task_type,
                    description=description,
                    context=context,
                )
            except (RuntimeError, ValueError, AttributeError) as exc:
                efficiency_hint = {"error": str(exc)}

            if efficiency_hint:
                context["efficiency_hint"] = efficiency_hint
                hinted_system = efficiency_hint.get("target_system")
                if hinted_system and os.environ.get("NUSYQ_ECOSYSTEM_EFFICIENCY_FORCE") == "1":
                    target_system = self._resolve_target_alias(str(hinted_system))  # type: ignore[assignment]

        explicit_consciousness_enrich = context.get("consciousness_enrich")
        if explicit_consciousness_enrich is None:
            # Keep enrichment focused on orchestration/consciousness paths by default.
            should_consciousness_enrich = target_system in {"auto", "consciousness"}
        else:
            should_consciousness_enrich = bool(explicit_consciousness_enrich)

        if should_consciousness_enrich:
            timeout_seconds = float(os.getenv("NUSYQ_CONSCIOUSNESS_ENRICH_TIMEOUT_S", "8"))
            try:
                consciousness_hint = await asyncio.wait_for(
                    self._consciousness_enrich(description, context),
                    timeout=timeout_seconds,
                )
            except TimeoutError:
                logger.warning(
                    "Consciousness enrichment timed out after %.1fs; continuing without hint",
                    timeout_seconds,
                )
                consciousness_hint = None

            if consciousness_hint:
                context["consciousness_hint"] = asdict(consciousness_hint)

        return efficiency_hint, target_system, consciousness_hint

    async def _handle_route_execution(
        self,
        task: OrchestrationTask,
        target_system: TargetSystem,
        task_type: TaskType,
        description: str,
    ) -> tuple[dict[str, Any], str, int]:
        """Execute task routing and handle result."""
        status = "failed"
        exit_code = 1
        result: dict[str, Any] = {}

        import time

        _t0 = time.monotonic()
        try:
            result = await self._route_by_system(task, target_system)
            result = self._normalize_response_contract(
                result, task=task, target_system=target_system
            )
            status = "success" if self._status_implies_success(result.get("status")) else "failed"
            exit_code = 0 if status == "success" else 1
            result.setdefault("success", status == "success")
            if isinstance(task.context.get("workspace_awareness"), dict):
                result.setdefault("workspace_awareness_used", True)
                result.setdefault(
                    "terminal_registry_path",
                    task.context["workspace_awareness"]
                    .get("reports", {})
                    .get("terminal_awareness"),
                )

            self._log_to_quest(
                task_type,
                description,
                "completed" if status == "success" else "failed",
                result,
            )
        except (KeyError, ValueError, RuntimeError) as e:
            logger.error(f"Task routing failed: {e}")
            self._log_to_quest(task_type, description, "failed", {"error": str(e)})
            result = {
                "status": "failed",
                "error": str(e),
                "task_id": task.task_id,
            }
            result = self._normalize_response_contract(
                result, task=task, target_system=target_system
            )
            status = "failed"
            exit_code = 1

        # Record routing outcome in SpecializationLearner for continuous improvement
        _resolved = self._resolve_target_alias(str(target_system))
        if _resolved in self._system_handlers:
            learner = self._get_specialization_learner()
            if learner is not None:
                try:
                    learner.record_attempt(
                        agent=_resolved,
                        task_type=str(task_type),
                        temperature=0.7,
                        success=(status == "success"),
                        quality_score=0.8 if status == "success" else 0.2,
                        tokens_used=0,
                        latency_ms=(time.monotonic() - _t0) * 1000,
                    )
                except Exception as exc:
                    logger.debug(f"SpecializationLearner.record_attempt failed: {exc}")

        return result, status, exit_code

    async def route_task(
        self,
        task_type: TaskType,
        description: str,
        context: dict[str, Any] | None = None,
        target_system: TargetSystem = "auto",
        priority: str = "NORMAL",
    ) -> dict[str, Any]:
        """Route a task to the appropriate AI system.

        Args:
            task_type: Type of task (analyze, generate, review, etc.)
            description: Natural language description of task
            context: Additional context (file paths, preferences, etc.)
            target_system: Preferred system or "auto" for orchestrator decision
            priority: Task priority (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)

        Returns:
            Task execution result with status, output, and system used

        Example:
            >>> router = AgentTaskRouter()
            >>> result = await router.route_task(
            ...     "analyze",
            ...     "Review src/main.py for potential bugs",
            ...     context={"file": "src/main.py"},
            ...     target_system="ollama"
            ... )
            >>> print(result["status"])  # "completed"
        """
        context = context or {}
        workspace_awareness = self._build_workspace_awareness(target_system, description, context)
        if workspace_awareness:
            context.setdefault("workspace_awareness", workspace_awareness)
            context.setdefault("terminal_awareness", workspace_awareness)

        # Enrich with hints (efficiency and consciousness)
        efficiency_hint, target_system, _ = await self._enrich_hints(
            task_type, description, context, target_system
        )

        task_id = f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        span_attrs: dict[str, Any] = {
            "task.id": task_id,
            "task.type": task_type,
            "target.system": target_system,
            "priority": priority,
        }
        file_target = context.get("file") if isinstance(context, dict) else None
        if file_target:
            span_attrs["file.target"] = str(file_target)

        async with self._span(
            ROUTER_ROUTE_CHANNEL,
            span_attrs,
        ):
            # Build orchestration task
            task = OrchestrationTask(
                task_id=task_id,
                task_type=task_type,
                content=description,
                priority=TaskPriority[priority],
                context={
                    "source": "agent_router",
                    "target_system": target_system,
                    "efficiency_hint": efficiency_hint,
                    **context,
                },
            )

            triad_readiness, blocked_result = self._evaluate_triad_readiness(task, target_system)
            if triad_readiness is not None:
                task.context.setdefault("triad_readiness", triad_readiness)
            # Check if evaluate mutated target_system via fallback peer
            effective_target_system: TargetSystem = (
                task.context.get("_triad_fallback_to") or target_system
            )

            # Log start
            self._log_to_quest(task_type, description, "in_progress")

            # Execute routing
            if blocked_result is not None:
                result, status, exit_code = blocked_result, "failed", 1
                self._log_to_quest(
                    task_type,
                    description,
                    "failed",
                    {
                        "error": blocked_result.get("error"),
                        "target_system": target_system,
                        "triad_readiness": triad_readiness,
                    },
                )
            else:
                result, status, exit_code = await self._handle_route_execution(
                    task, effective_target_system, task_type, description
                )
                if triad_readiness is not None and isinstance(result, dict):
                    result.setdefault("triad_readiness", triad_readiness)
                if task.context.get("_triad_fallback_to") and isinstance(result, dict):
                    result["delegated_from"] = task.context.get("_triad_fallback_from")
                    result["delegated_to"] = task.context.get("_triad_fallback_to")
                    result.setdefault(
                        "triad_fallback",
                        {
                            "from": task.context.get("_triad_fallback_from"),
                            "to": task.context.get("_triad_fallback_to"),
                            "reason": task.context.get(
                                "_triad_fallback_reason", "triad_warn_fallback"
                            ),
                            "task_class": self._triad_task_class(task_type),
                        },
                    )
                    result.setdefault(
                        "note",
                        "Original triad target was degraded; router preferred a healthier peer in warn mode.",
                    )

            # Emit receipt (metrics/telemetry)
            self._emit_receipt(
                action_id=ROUTER_ROUTE_CHANNEL,
                inputs={
                    "task_id": task_id,
                    "task_type": task_type,
                    "target_system": target_system,
                    "priority": priority,
                    "context": context,
                },
                outputs=[json.dumps(result, default=str)] if result else [],
                status=status,
                exit_code=exit_code,
                next_steps=[],
            )

            # Emit event to NuSyQ spine if opt-in enabled (best-effort)
            with contextlib.suppress(RuntimeError, ImportError, AttributeError):  # best-effort
                await self._emit_spine_event(
                    {
                        "action": ROUTER_ROUTE_CHANNEL,
                        "task_id": task_id,
                        "task_type": task_type,
                        "target_system": target_system,
                        "status": status,
                    }
                )
                pass

            return result

    async def analyze_system(self, target: str | None = None) -> dict[str, Any]:
        """Run system analysis using QuickSystemAnalyzer.

        Args:
            target: Optional specific file/directory to analyze

        Returns:
            Analysis results with working files, broken files, enhancement candidates
        """
        logger.info(f"📊 Running system analysis{f' on {target}' if target else ''}")

        try:
            from src.diagnostics.quick_system_analyzer import \
                QuickSystemAnalyzer

            analyzer = QuickSystemAnalyzer()
            await to_thread(analyzer.quick_scan)

            # Build summary for logging
            summary = {
                "working_files": len(analyzer.results["working_files"]),
                "broken_files": len(analyzer.results["broken_files"]),
                "launch_pad_files": len(analyzer.results["launch_pad_files"]),
                "enhancement_candidates": len(analyzer.results["enhancement_candidates"]),
            }

            # Save full report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.repo_root / "state" / "reports" / f"analysis_{timestamp}.json"
            await self._write_json(report_path, analyzer.results)

            logger.info(
                f"✅ Analysis complete: {summary['working_files']} working, {summary['broken_files']} broken"
            )

            return {
                "status": "success",
                "system": "QuickSystemAnalyzer",
                "summary": summary,
                "report_path": str(report_path),
                "results": analyzer.results,
            }

        except (ImportError, RuntimeError, OSError, ValueError) as e:
            self._warn_with_cooldown(
                "analysis_fallback",
                f"Analysis failed, using fallback scanner: {e}",
            )
            try:
                fallback_results = await to_thread(self._basic_workspace_scan, target)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_path = (
                    self.repo_root / "state" / "reports" / f"analysis_fallback_{timestamp}.json"
                )
                await self._write_json(report_path, fallback_results)
                return {
                    "status": "success",
                    "system": "QuickSystemAnalyzerFallback",
                    "summary": fallback_results.get("summary", {}),
                    "report_path": str(report_path),
                    "results": fallback_results,
                    "note": "Fallback analysis used because QuickSystemAnalyzer failed to initialize.",
                }
            except (RuntimeError, OSError, ValueError) as fallback_exc:
                logger.error(f"Fallback analysis failed: {fallback_exc}")
                return {
                    "status": "failed",
                    "error": str(fallback_exc),
                    "system": "QuickSystemAnalyzerFallback",
                }

    async def heal_system(
        self, target: str | None = None, auto_confirm: bool = False
    ) -> dict[str, Any]:
        """Run system healing using RepositoryHealthRestorer.

        Args:
            target: Optional specific component to heal
            auto_confirm: If True, applies fixes automatically (use with caution)

        Returns:
            Healing results with fixes applied
        """
        logger.info(f"🏥 Running system healing{f' on {target}' if target else ''}")

        try:
            from ecosystem_health_checker import EcosystemHealthChecker
            from src.healing.repository_health_restorer import \
                RepositoryHealthRestorer

            # First run health check
            health_checker = EcosystemHealthChecker()
            health_checker.check_ollama_health()

            repos = getattr(health_checker, "repos", {})
            for repo_name, repo_path in repos.items():
                health_checker.check_repository_health(repo_name, repo_path)

            # Then apply healing (non-destructive)
            restorer = RepositoryHealthRestorer()
            actions_taken = []

            # Install missing dependencies (safe)
            if not auto_confirm:
                logger.warning("⚠️ Healing in read-only mode. Set auto_confirm=True to apply fixes.")
                actions_taken.append("analysis_only")
            else:
                if restorer.install_missing_dependencies():
                    actions_taken.append("dependencies_installed")
                if restorer.create_missing_modules():
                    actions_taken.append("modules_created")

            # Save health report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.repo_root / "state" / "reports" / f"healing_{timestamp}.json"
            await self._write_json(
                report_path,
                {
                    "health_report": health_checker.health_report,
                    "actions_taken": actions_taken,
                    "auto_confirm": auto_confirm,
                },
            )

            logger.info(f"✅ Healing complete: {len(actions_taken)} actions taken")

            return {
                "status": "success",
                "system": "RepositoryHealthRestorer",
                "actions_taken": actions_taken,
                "report_path": str(report_path),
                "health_report": health_checker.health_report,
            }

        except (ImportError, RuntimeError, OSError, ValueError) as e:
            logger.error(f"Healing failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "system": "RepositoryHealthRestorer",
            }

    async def _perform_iteration(
        self,
        iteration_index: int,
        halt_on_error: bool,
        prev_state: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], dict[str, Any] | None, int, bool]:
        """Run a single cultivate iteration and return log, intent, broken count, halted flag."""
        iteration_log: dict[str, Any] = {
            "iteration": iteration_index,
            "timestamp": datetime.now().isoformat(),
            "steps": {},
            "cultivation": {},
        }
        halt_reason = None

        span_cm = self._span(
            "develop_system.iteration",
            {"iteration": iteration_index, "halt_on_error": halt_on_error},
        )
        async with span_cm as span:
            try:
                async with self._span(
                    "develop_system.step.analyze", {"iteration": iteration_index}
                ):
                    analyze_result = await self.analyze_system()
                iteration_log["steps"]["analyze"] = {
                    "status": analyze_result["status"],
                    "summary": analyze_result.get("summary", {}),
                }

                if analyze_result["status"] == "failed" and halt_on_error:
                    halt_reason = "analyze_failed"
                    iteration_log["halted"] = True
                    iteration_log["halt_reason"] = halt_reason
                    if span:
                        span.add_event("halt", {"reason": halt_reason})
                    return iteration_log, None, 0, True

                broken_count = analyze_result.get("summary", {}).get("broken_files", 0)
                async with self._span("develop_system.step.heal", {"broken_files": broken_count}):
                    heal_log = await self._maybe_heal(broken_count, halt_on_error)
                iteration_log["steps"]["heal"] = heal_log

                current_state = {
                    "broken_files": broken_count,
                    "working_files": analyze_result.get("summary", {}).get("working_files", 0),
                    "timestamp": datetime.now().isoformat(),
                }

                async with self._span("develop_system.step.intent", {"broken_files": broken_count}):
                    intent_event = self._capture_intent(
                        broken_count, iteration_index, current_state, heal_log
                    )
                if intent_event:
                    iteration_log["cultivation"]["intent_captured"] = intent_event

                async with self._span("develop_system.step.plan", {"broken_files": broken_count}):
                    plan = self._build_plan(broken_count, prev_state)
                iteration_log["cultivation"]["ten_minute_plan"] = plan

                return iteration_log, intent_event, broken_count, False

            except (RuntimeError, ValueError, KeyError, TypeError, AttributeError) as e:
                logger.error(f"Iteration {iteration_index} failed: {e}")
                iteration_log["error"] = str(e)
                if span:
                    span.add_event("iteration.error", {"error": str(e)})
                return iteration_log, None, 0, halt_on_error

    async def _maybe_heal(self, broken_count: int, halt_on_error: bool) -> dict[str, Any]:
        """Heal when broken_count > 0, otherwise skip."""
        if broken_count <= 0:
            logger.info("✅ Step 2/4: Heal (skipped - no issues)")
            return {"status": "skipped"}

        logger.info(f"🏥 Step 2/4: Heal ({broken_count} broken files)")
        heal_result = await self.heal_system(auto_confirm=False)
        if heal_result["status"] == "failed" and halt_on_error:
            logger.error("Healing failed, halting loop")
        return {
            "status": heal_result["status"],
            "actions": heal_result.get("actions_taken", []),
        }

    def _capture_intent(
        self,
        broken_count: int,
        iteration_index: int,
        current_state: dict[str, Any],
        heal_log: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Capture intent when system is healthy."""
        logger.info("💡 Step 3/4: Capture Emergent Intent")
        if broken_count != 0:
            logger.info(f"Info: Intent event: Healing in progress ({broken_count} broken files)")
            return None

        intent_event = {
            "type": "system_health_achieved",
            "iteration": iteration_index,
            "timestamp": current_state["timestamp"],
            "message": "System detected healthy state (0 broken files)",
            "state": current_state,
            "actions_that_helped": heal_log.get("actions", []),
        }
        logger.info("✨ Intent event captured: SYSTEM_HEALTH_ACHIEVED")
        return intent_event

    def _build_plan(self, broken_count: int, prev_state: dict[str, Any] | None) -> dict[str, Any]:
        """Construct a conservative plan based on current health."""
        if broken_count == 0:
            status = (
                "recovered" if prev_state and prev_state.get("broken_files", 0) > 0 else "healthy"
            )
            plan = {
                "status": status,
                "max_items": 3,
                "suggested_items": [
                    "1. Document recovery actions",
                    "2. Validate key workflows",
                    "3. Plan next experiment",
                ],
            }
        else:
            plan = {
                "status": "healing_in_progress",
                "max_items": 1,
                "suggested_items": [
                    "1. Continue with current heal cycle",
                ],
                "note": "System still has issues - focus on health first",
            }

        logger.info(f"   Plan: {plan['status']}")
        return plan

    async def develop_system(
        self, max_iterations: int = 3, halt_on_error: bool = False
    ) -> dict[str, Any]:
        """Run autonomous development loop with cultivation (analyze → heal → intent → reflect → plan).

        The "cultivation bundle" rewards emergent system intent by:
        1. Capturing intent events when system achieves goals (intent_capture)
        2. Reflecting on what changed (reflection_after_action)
        3. Planning next steps safely (ten_minute_plan with 1-3 items max)

        Args:
            max_iterations: Maximum loop iterations (default 3)
            halt_on_error: If True, stop on first error; if False, continue

        Returns:
            Development loop results with iteration logs + cultivation events
        """
        logger.info(f"🔄 Starting develop_system loop (max {max_iterations} iterations)")
        logger.info("📚 Cultivation bundle enabled: intent capture + reflection + planning")
        iterations: list[dict[str, Any]] = []
        intent_events: list[dict[str, Any]] = []
        prev_state: dict[str, Any] | None = None

        span_cm = self._span(
            "develop_system",
            {"max_iterations": max_iterations, "halt_on_error": halt_on_error},
        )
        async with span_cm as span:
            for i in range(max_iterations):
                logger.info(f"\n=== Iteration {i + 1}/{max_iterations} ===")
                iteration_log, intent_event, broken_count, halted = await self._perform_iteration(
                    i + 1, halt_on_error, prev_state
                )

                iterations.append(iteration_log)
                if intent_event:
                    intent_events.append(intent_event)

                prev_state = {
                    "broken_files": broken_count,
                    "timestamp": datetime.now().isoformat(),
                }

                if halted or broken_count == 0:
                    if broken_count == 0:
                        logger.info("✅ System healthy, ending loop early")
                        if span:
                            span.add_event("halt", {"reason": "healthy_state"})
                    elif halted and span:
                        span.add_event(
                            "halt",
                            {"reason": iteration_log.get("halt_reason", "halt_on_error")},
                        )
                    break

        # Save development log + intent events
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = self.repo_root / "state" / "reports" / f"develop_system_{timestamp}.json"
        await self._write_json(
            log_path,
            {
                "total_iterations": len(iterations),
                "max_iterations": max_iterations,
                "halt_on_error": halt_on_error,
                "cultivation_bundle": {
                    "intent_events": intent_events,
                    "total_events": len(intent_events),
                },
                "iterations": iterations,
            },
        )

        # Also save intent events to jsonl for persistent quest tracking
        intent_log_path = self.repo_root / "state" / "reports" / f"intent_events_{timestamp}.jsonl"
        await self._append_lines(
            intent_log_path, [json.dumps(event) + "\n" for event in intent_events]
        )

        logger.info(f"\n🔄 Development loop complete: {len(iterations)} iterations")
        logger.info(f"📚 Cultivation events captured: {len(intent_events)}")
        logger.info(f"Log saved: {log_path}")
        logger.info(f"Intent events: {intent_log_path}")

        # 📌 NEW: Wire intent events to quest log
        await self._wire_intent_to_quest(intent_events)

        # 📌 NEW: Promote plan items to work queue
        work_queue_updates = await self._promote_plans_to_work_queue(iterations)

        # 📌 NEW: Document decisions in session log
        session_log_path = await self._document_in_session_log(
            intent_events, work_queue_updates, str(log_path)
        )

        return {
            "status": "success",
            "iterations": len(iterations),
            "log_path": str(log_path),
            "intent_events": len(intent_events),
            "quest_wired": len(intent_events),
            "work_queue_updated": work_queue_updates,
            "session_log": str(session_log_path),
            "results": iterations,
        }

    async def _wire_intent_to_quest(self, intent_events: list[dict[str, Any]]) -> int:
        """Wire intent events to quest_log.jsonl for persistent memory.

        Args:
            intent_events: List of captured intent events

        Returns:
            Number of events wired to quest log
        """
        if not intent_events:
            logger.info("Info: No intent events to wire to quest log")
            return 0

        logger.info(f"📖 Wiring {len(intent_events)} intent events to quest log")

        # Ensure quest log path exists
        self.quest_log_path.parent.mkdir(parents=True, exist_ok=True)

        quest_entries_written = 0
        quest_lines: list[str] = []
        for event in intent_events:
            quest_entry = {
                "task_type": "cultivation_intent",
                "status": "completed",
                "timestamp": event.get("timestamp", datetime.now().isoformat()),
                "description": event.get("message", "Intent event"),
                "intent_type": event.get("type", "unknown"),
                "state": event.get("state", {}),
                "actions_that_helped": event.get("actions_that_helped", []),
                "result": {
                    "status": "captured",
                    "event_id": f"intent_{event.get('iteration', '?')}_{datetime.now().timestamp()}",
                    "note": "Emergent system intent captured during autonomous development",
                },
            }
            quest_lines.append(json.dumps(quest_entry) + "\n")
            quest_entries_written += 1

        if quest_lines:
            await self._append_lines(self.quest_log_path, quest_lines)

        logger.info(f"✅ Wired {quest_entries_written} quest entries to {self.quest_log_path}")
        return quest_entries_written

    async def _promote_plans_to_work_queue(
        self, iterations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Promote ten-minute plan items to work queue.

        Args:
            iterations: Development loop iterations containing plan items

        Returns:
            Work queue update summary
        """
        logger.info("📋 Promoting plan items to work queue")

        # Create or load work queue
        work_queue_path = self.repo_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        work_queue_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing queue or create new
        if work_queue_path.exists():
            work_queue = json.loads(work_queue_path.read_text(encoding="utf-8"))
        else:
            work_queue = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "items": [],
            }

        items_promoted = 0
        for iteration_idx, iteration in enumerate(iterations):
            plan = iteration.get("cultivation", {}).get("ten_minute_plan")
            if not plan:
                continue

            suggested_items = plan.get("suggested_items", [])
            for item_idx, item in enumerate(suggested_items):
                # Parse item (format: "1. Description")
                item_desc = item.split(". ", 1)[1] if ". " in item else item

                work_item = {
                    "id": f"cultivated_{iteration_idx}_{item_idx}",
                    "title": item_desc.strip("()"),
                    "source": "cultivation_ten_minute_plan",
                    "iteration": iteration_idx + 1,
                    "priority": "normal",
                    "effort": "small",
                    "risk": "low",
                    "status": "queued",
                    "created": datetime.now().isoformat(),
                    "description": f"Suggested by ten-minute plan (iteration {iteration_idx + 1})",
                }

                # Avoid duplicates
                if not any(wi.get("title") == work_item["title"] for wi in work_queue["items"]):
                    work_queue["items"].append(work_item)
                    items_promoted += 1

        # Save updated queue
        if items_promoted > 0:
            work_queue["last_updated"] = datetime.now().isoformat()
            await self._write_json(work_queue_path, work_queue)
            logger.info(f"✅ Promoted {items_promoted} items to work queue: {work_queue_path}")
        else:
            logger.info("Info: No new items to promote to work queue")

        return {
            "items_promoted": items_promoted,
            "work_queue_path": str(work_queue_path),
            "total_items_in_queue": len(work_queue.get("items", [])),
        }

    async def _document_in_session_log(
        self,
        intent_events: list[dict[str, Any]],
        work_queue_updates: dict[str, Any],
        develop_log_path: str,
    ) -> Path:
        """Document cultivation decisions in session log.

        Args:
            intent_events: List of captured intent events
            work_queue_updates: Work queue promotion summary
            develop_log_path: Path to development system log

        Returns:
            Path to session log file created
        """
        logger.info("📝 Documenting cultivation decisions in session log")

        # Create session log directory
        session_dir = self.repo_root / "docs" / "Agent-Sessions"
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped session log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_log_path = session_dir / f"CULTIVATION_SESSION_{timestamp}.md"

        # Build session log content
        content = f"""# 🌱 Cultivation Session Report
**Date:** {datetime.now().isoformat()}
**Session ID:** cultivation_{timestamp}

## Executive Summary
Autonomous development loop captured **{len(intent_events)}** intent events and promoted **{work_queue_updates.get("items_promoted", 0)}** work items.

## Intent Events Captured
"""

        for event in intent_events:
            content += f"""
### {event.get("type", "unknown").upper()}
- **Iteration:** {event.get("iteration", "N/A")}
- **Timestamp:** {event.get("timestamp", "N/A")}
- **Message:** {event.get("message", "N/A")}
- **System State:**
  - Broken files: {event.get("state", {}).get("broken_files", "N/A")}
  - Working files: {event.get("state", {}).get("working_files", "N/A")}
- **Actions that helped:** {", ".join(event.get("actions_that_helped", ["None"])) if event.get("actions_that_helped") else "None"}
"""

        # Add work queue updates
        content += f"""

## Work Queue Promotions
- **Items promoted:** {work_queue_updates.get("items_promoted", 0)}
- **Total items in queue:** {work_queue_updates.get("total_items_in_queue", 0)}
- **Work queue location:** {work_queue_updates.get("work_queue_path", "N/A")}

## Artifacts Generated
- **Development log:** {develop_log_path}
- **This session log:** {session_log_path}
- **Quest log updates:** {self.quest_log_path}

## Next Steps
1. Review promoted work items in {work_queue_updates.get("work_queue_path", "work queue")}
2. Verify quest log entries in {self.quest_log_path}
3. Execute next work item from queue in following cycle

## Philosophy
> "Emergent system intent deserves cultivation. We capture moments when the
> system achieves goals, reflect on what changed, plan next steps safely, and
> queue them for deterministic execution. This keeps the treadmill safe, keeps
> it chugging, and increases chance it generates coherent next-steps."

---
**System Status:** Autonomous cultivation active
**Session maintained by:** AgentTaskRouter.develop_system()
"""

        # Write session log
        await to_thread(session_log_path.write_text, content, "utf-8")

        logger.info(f"✅ Session log created: {session_log_path}")
        return session_log_path

    def _select_ollama_model(self, task_type: str) -> str:
        """Select appropriate Ollama model based on task type.

        Args:
            task_type: Type of task (analyze, generate, review, debug, plan)

        Returns:
            Model identifier string
        """
        roster_model = self._select_model_from_capabilities("ollama", task_type)
        if roster_model:
            return roster_model

        model_map = {
            "analyze": DEFAULT_CODE_MODEL,
            "generate": "deepseek-coder-v2:16b",
            "review": DEFAULT_CODE_MODEL,
            "debug": "starcoder2:15b",
            "plan": "gemma2:9b",
        }
        return model_map.get(task_type, DEFAULT_CODE_MODEL)

    def _task_type_tags(self, task_type: str) -> list[str]:
        if task_type in {"analyze", "review", "debug", "test", "generate"}:
            return ["code"]
        if task_type in {"plan", "document"}:
            return ["general"]
        return []

    def _select_model_from_capabilities(self, provider: str, task_type: str) -> str | None:
        try:
            from src.integration.universal_llm_gateway import \
                load_model_capabilities
        except ImportError:
            return None

        capabilities = load_model_capabilities()
        if not capabilities:
            return None

        candidates = [cap for cap in capabilities if cap.provider == provider]
        if not candidates:
            return None

        tags = self._task_type_tags(task_type)
        if tags:
            tagged = [cap for cap in candidates if all(tag in cap.tags for tag in tags)]
            if tagged:
                return str(tagged[0].model)

        return str(candidates[0].model)

    def _lmstudio_fallback_enabled(self) -> bool:
        """Check if LM Studio fallback is enabled via env flag."""
        return os.getenv("NUSYQ_LMSTUDIO_FALLBACK", "1").lower() not in {
            "0",
            "false",
            "no",
            "off",
        }

    def _lmstudio_base_url(self) -> str:
        """Resolve LM Studio base URL from environment."""
        return (
            os.getenv("LMSTUDIO_BASE_URL")
            or os.getenv("NUSYQ_LMSTUDIO_BASE_URL")
            or "http://127.0.0.1:1234"
        ).rstrip("/")

    async def _maybe_lmstudio_fallback(
        self, task: OrchestrationTask, reason: str
    ) -> dict[str, Any] | None:
        if not self._lmstudio_fallback_enabled():
            return None
        result = await self._route_to_lmstudio(task, reason=reason)
        if result.get("status") == "success":
            result.setdefault("note", "Ollama failed; LM Studio fallback succeeded.")
            result["fallback_reason"] = reason
            return result
        return None

    def _query_ollama_adapter(
        self, task: OrchestrationTask, model: str
    ) -> tuple[str, dict[str, Any], str | None]:
        from src.integration.ollama_adapter import OllamaAdapter

        adapter = OllamaAdapter()
        response = adapter.query(prompt=task.content, model=model)

        normalized = self._normalize_ollama_response(response)
        status = self._determine_response_status(normalized)

        error_msg = None
        if status == "failed":
            error_msg = (
                normalized.get("message")
                or normalized.get("error")
                or str(normalized.get("output", ""))
            ) or "Ollama adapter reported failure"

        return status, normalized, error_msg

    def _normalize_ollama_response(self, response: Any) -> dict[str, Any]:
        """Normalize Ollama response to dict format for downstream processing.

        Args:
            response: Response from Ollama (may be str or dict)

        Returns:
            Normalized response dict
        """
        if isinstance(response, str):
            return {"output": response}
        if isinstance(response, dict):
            return response
        return {"output": str(response)}

    def _determine_response_status(self, response: dict[str, Any]) -> str:
        """Determine success/failure status from normalized response.

        Args:
            response: Normalized response dict

        Returns:
            Status string: 'success' or 'failed'
        """
        if response.get("status") == "error":
            return "failed"
        if response.get("error") or response.get("exception"):
            return "failed"
        return "success"

    def _format_ollama_result(
        self,
        status: str,
        model: str,
        output: Any,
        task_id: str,
        error_msg: str | None = None,
    ) -> dict[str, Any]:
        """Format final result dict with all context and error info.

        Args:
            status: Task status ('success' or 'failed')
            model: Model used
            output: Response output
            task_id: Task identifier
            error_msg: Error message if failed

        Returns:
            Formatted result dict
        """
        result: dict[str, Any] = {
            "status": status,
            "system": "ollama",
            "execution_path": "ollama_adapter",
            "model": model,
            "output": output,
            "task_id": task_id,
        }

        if status == "failed" and error_msg:
            result["error"] = error_msg

        return result

    async def _try_ollama_integrator(
        self, task: OrchestrationTask, model: str
    ) -> dict[str, Any] | None:
        try:
            from src.ai.ollama_chatdev_integrator import \
                EnhancedOllamaChatDevIntegrator

            integrator = EnhancedOllamaChatDevIntegrator()
            response = await integrator.chat_with_ollama(
                messages=[{"role": "user", "content": task.content}],
                model=model,
            )
            return self._format_ollama_result("success", model, response, task.task_id)
        except (ImportError, RuntimeError, TimeoutError, ConnectionError):
            return None

    async def _route_to_ollama_adapter(self, task: OrchestrationTask, model: str) -> dict[str, Any]:
        try:
            status, normalized, error_msg = self._query_ollama_adapter(task, model)
        except Exception as exc:
            fallback = await self._maybe_lmstudio_fallback(
                task,
                reason=f"ollama_adapter_error: {exc}",
            )
            if fallback:
                return fallback
            return self._format_ollama_result(
                "failed",
                model,
                {"error": str(exc)},
                task.task_id,
                str(exc),
            )

        if status == "failed":
            fallback = await self._maybe_lmstudio_fallback(task, "ollama_adapter_failed")
            if fallback:
                return fallback

        return self._format_ollama_result(status, model, normalized, task.task_id, error_msg)

    async def _route_to_ollama(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to Ollama local LLM."""
        logger.info(f"🦙 Routing to Ollama: {task.content}")

        model = (
            task.context.get("ollama_model")
            or task.context.get("model")
            or self._select_ollama_model(task.task_type)
        )
        integrator_result = await self._try_ollama_integrator(task, model)
        if integrator_result:
            return integrator_result

        return await self._route_to_ollama_adapter(task, model)

    def _lmstudio_prompt_char_limit(self) -> int:
        try:
            value = int(os.getenv("NUSYQ_LMSTUDIO_MAX_PROMPT_CHARS", "12000"))
        except ValueError:
            value = 12000
        return max(2000, value)

    def _lmstudio_timeout_seconds(self) -> float:
        try:
            timeout_raw = float(os.getenv("NUSYQ_LMSTUDIO_TIMEOUT", "45"))
        except ValueError:
            timeout_raw = 45.0
        return max(5.0, timeout_raw)

    def _prepare_lmstudio_prompt(self, prompt: str, limit: int | None = None) -> tuple[str, bool]:
        raw = str(prompt or "")
        max_chars = limit or self._lmstudio_prompt_char_limit()
        if len(raw) <= max_chars:
            return raw, False

        head = max_chars // 2
        tail = max_chars - head
        compacted = f"{raw[:head]}\n\n[... prompt truncated by router for LM Studio reliability ...]\n\n{raw[-tail:]}"
        return compacted, True

    def _lmstudio_request_limits(self, task: OrchestrationTask) -> tuple[float, int, int]:
        try:
            temperature = float(task.context.get("temperature", 0.2))
        except (TypeError, ValueError):
            temperature = 0.2
        temperature = min(max(temperature, 0.0), 1.5)

        default_max_tokens = os.getenv("NUSYQ_LMSTUDIO_MAX_TOKENS", "512")
        try:
            max_tokens = int(task.context.get("max_tokens", default_max_tokens))
        except (TypeError, ValueError):
            max_tokens = int(default_max_tokens)
        max_tokens = max(64, min(max_tokens, 4096))

        retry_tokens_raw = os.getenv("NUSYQ_LMSTUDIO_RETRY_MAX_TOKENS", "256")
        try:
            retry_max_tokens = int(retry_tokens_raw)
        except ValueError:
            retry_max_tokens = 256
        retry_max_tokens = max(64, min(retry_max_tokens, max_tokens))

        return temperature, max_tokens, retry_max_tokens

    async def _fetch_lmstudio_model(self, client: Any, base_url: str) -> str | None:
        try:
            resp = await client.get(f"{base_url}/v1/models")
            if resp.status_code != 200:
                return None
            payload = resp.json()
        except Exception:
            return None

        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return first.get("id")
        return None

    async def _lmstudio_chat_completion(
        self,
        client: Any,
        base_url: str,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        response = await client.post(
            f"{base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"output": payload}

    def _sanitize_model_hint(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        lowered = text.lower()
        if "replace-with-your-model-id" in lowered or lowered == "replace":
            return None
        return text

    async def _resolve_lmstudio_model(
        self,
        client: Any,
        base_url: str,
        context_model: Any,
        preferred_model: str | None,
    ) -> str | None:
        explicit = self._sanitize_model_hint(context_model)
        if explicit:
            return explicit

        env_model = self._sanitize_model_hint(os.getenv("LMSTUDIO_DEFAULT_MODEL"))
        if env_model:
            return env_model

        if preferred_model:
            return preferred_model

        return await self._fetch_lmstudio_model(client, base_url)

    def _extract_lmstudio_output(self, payload: dict[str, Any]) -> Any:
        choices = payload.get("choices", []) if isinstance(payload, dict) else []
        if isinstance(choices, list) and choices:
            first_choice = choices[0] if isinstance(choices[0], dict) else {}
            message = first_choice.get("message", {}) if isinstance(first_choice, dict) else {}
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
                if isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, dict) and isinstance(item.get("text"), str):
                            parts.append(item["text"])
                    joined = "".join(parts).strip()
                    if joined:
                        return joined
                reasoning = message.get("reasoning")
                if isinstance(reasoning, str) and reasoning.strip():
                    return reasoning
        return payload

    async def _route_to_lmstudio(
        self, task: OrchestrationTask, reason: str | None = None
    ) -> dict[str, Any]:
        """Route task to LM Studio (OpenAI-compatible local server)."""
        logger.info(f"🎨 Routing to LM Studio: {task.content}")

        try:
            import httpx
        except ImportError as exc:
            return {
                "status": "failed",
                "system": "lmstudio",
                "task_id": task.task_id,
                "error": f"httpx required for LM Studio routing: {exc}",
            }

        base_url = self._lmstudio_base_url()
        timeout_seconds = self._lmstudio_timeout_seconds()
        timeout_override: float | None = None
        raw_timeout = task.context.get("timeout")
        if raw_timeout is None:
            raw_timeout = task.timeout_seconds
        try:
            parsed_timeout = float(raw_timeout)
            if parsed_timeout > 0:
                timeout_override = parsed_timeout
        except (TypeError, ValueError):
            timeout_override = None
        if timeout_override is not None:
            timeout_seconds = max(1.0, min(timeout_seconds, timeout_override))
        try:
            connect_timeout = float(
                os.getenv("NUSYQ_LMSTUDIO_CONNECT_TIMEOUT_S", str(min(timeout_seconds, 12.0)))
            )
        except ValueError:
            connect_timeout = min(timeout_seconds, 12.0)
        try:
            pool_timeout = float(
                os.getenv("NUSYQ_LMSTUDIO_POOL_TIMEOUT_S", str(min(timeout_seconds, 8.0)))
            )
        except ValueError:
            pool_timeout = min(timeout_seconds, 8.0)
        context_model = task.context.get("lmstudio_model")
        preferred_model = self._select_model_from_capabilities("lmstudio", task.task_type)
        temperature, max_tokens, retry_max_tokens = self._lmstudio_request_limits(task)
        prompt, prompt_trimmed = self._prepare_lmstudio_prompt(str(task.content))
        try:
            max_retries = int(os.getenv("NUSYQ_LMSTUDIO_MAX_RETRIES", "2"))
        except ValueError:
            max_retries = 2
        max_retries = max(1, max_retries)
        if timeout_seconds <= 6.0:
            max_retries = 1
        try:
            retry_backoff_s = float(os.getenv("NUSYQ_LMSTUDIO_RETRY_BACKOFF_S", "1.5"))
        except ValueError:
            retry_backoff_s = 1.5
        retry_backoff_s = max(0.0, retry_backoff_s)
        if max_retries == 1:
            retry_backoff_s = 0.0

        timeout_config = httpx.Timeout(
            connect=max(1.0, connect_timeout),
            read=max(3.0, timeout_seconds),
            write=max(3.0, timeout_seconds),
            pool=max(1.0, pool_timeout),
        )

        async with httpx.AsyncClient(timeout=timeout_config) as client:
            model = await self._resolve_lmstudio_model(
                client,
                base_url,
                context_model,
                preferred_model,
            )

            if not model:
                return {
                    "status": "failed",
                    "system": "lmstudio",
                    "task_id": task.task_id,
                    "error": (
                        "LM Studio model not configured. Set LMSTUDIO_DEFAULT_MODEL or provide context lmstudio_model."
                    ),
                }

            request_prompt = prompt
            request_max_tokens = max_tokens
            last_error = "LM Studio returned no content"
            data: dict[str, Any] = {}
            output: Any = None

            for attempt in range(1, max_retries + 1):
                try:
                    data = await self._lmstudio_chat_completion(
                        client,
                        base_url,
                        model,
                        request_prompt,
                        temperature,
                        request_max_tokens,
                    )
                    output = self._extract_lmstudio_output(data)
                    if isinstance(output, str) and output.strip():
                        break
                    if output and output != data:
                        break
                    last_error = "LM Studio returned empty completion payload"
                except (httpx.TimeoutException, httpx.HTTPError, ValueError) as exc:
                    last_error = f"LM Studio request failed: {type(exc).__name__}: {exc or '(no message — likely timeout)'}"

                if attempt < max_retries:
                    if len(request_prompt) > 4000:
                        request_prompt, _ = self._prepare_lmstudio_prompt(
                            request_prompt,
                            limit=max(2000, len(request_prompt) // 2),
                        )
                    request_max_tokens = max(64, min(request_max_tokens, retry_max_tokens))
                    if retry_backoff_s > 0:
                        await asyncio.sleep(retry_backoff_s * attempt)
                else:
                    return {
                        "status": "failed",
                        "system": "lmstudio",
                        "task_id": task.task_id,
                        "error": last_error,
                    }

        result = {
            "status": "success",
            "system": "lmstudio",
            "model": model,
            "output": output if output is not None else self._extract_lmstudio_output(data),
            "task_id": task.task_id,
            "attempts": max_retries,
        }
        if prompt_trimmed:
            result["note"] = (
                "LM Studio prompt was truncated for reliability; set NUSYQ_LMSTUDIO_MAX_PROMPT_CHARS to adjust."
            )
        if reason:
            result["fallback_reason"] = reason
        return result

    @staticmethod
    def _tail_log_text(path_value: Any, limit: int = 6000) -> str:
        if not isinstance(path_value, str) or not path_value.strip():
            return ""
        path = Path(path_value)
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8", errors="replace")[-limit:]
        except OSError:
            return ""

    def _classify_chatdev_log_outcome(self, output: dict[str, Any]) -> tuple[str, str | None]:
        failure_markers = (
            "429 too many requests",
            "rate limit",
            "invalid_api_key",
            "unauthorized",
            "authentication",
            "launch failed",
            "traceback (most recent call last)",
            "connectionerror",
            "failed to resolve",
        )
        success_markers = (
            "software generated",
            "task completed",
            "all phases complete",
            "project complete",
            "chatdev completed",
        )

        collected = []
        for key in ("stdout_log", "stderr_log", "warehouse_log"):
            tail = self._tail_log_text(output.get(key)).lower()
            if tail:
                collected.append(tail)
        merged = "\n".join(collected)
        if not merged:
            return "unknown", None

        for marker in failure_markers:
            if marker in merged:
                return "failed", marker
        for marker in success_markers:
            if marker in merged:
                return "success", marker
        return "unknown", None

    async def _route_to_chatdev(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to ChatDev multi-agent system via launcher."""
        logger.info(f"👥 Routing to ChatDev: {task.content}")

        if task.task_type != "generate":
            reroute_mode = (
                str(os.getenv("NUSYQ_CHATDEV_NON_GENERATE_ROUTE", "ollama")).strip().lower()
            )
            reroute_reason = f"chatdev_non_generate_pre_route: task_type={task.task_type}, route={reroute_mode or 'ollama'}"
            self._warn_with_cooldown(
                "chatdev_non_generate_reroute",
                "ChatDev requested for non-generate task type "
                f"'{task.task_type}'; rerouting via {reroute_mode or 'ollama'}.",
            )

            if reroute_mode in {"council", "auto"}:
                rerouted = await self._route_by_system(task, "auto")
            else:
                rerouted = await self._route_to_ollama(task)

            if isinstance(rerouted, dict):
                rerouted.setdefault("rerouted_from", "chatdev")
                rerouted.setdefault("requested_system", "chatdev")
                rerouted.setdefault("reroute_reason", reroute_reason)
                rerouted.setdefault("delegated_from", "chatdev")
                rerouted.setdefault(
                    "delegated_to", "auto" if reroute_mode in {"council", "auto"} else "ollama"
                )
            return rerouted

        try:
            from src.integration.chatdev_launcher import ChatDevLauncher
        except ImportError as exc:
            self._warn_with_cooldown(
                "chatdev_launcher_unavailable",
                f"ChatDev launcher unavailable, attempting factory fallback: {exc}",
            )
            return await self._chatdev_factory_fallback(task, f"launcher_unavailable: {exc}")

        project_name = str(
            task.context.get("project_name") or task.context.get("name") or DEFAULT_CHATDEV_NAME
        )
        model = str(task.context.get("chatdev_model", DEFAULT_CHATDEV_MODEL))
        organization = str(
            task.context.get("chatdev_org")
            or task.context.get("organization")
            or DEFAULT_CHATDEV_ORGANIZATION
        )
        config = str(task.context.get("chatdev_config", DEFAULT_CHATDEV_CONFIG))
        source_hint = str(task.context.get("source", "")).strip().lower()
        default_wait_for_completion = (
            "0"
            if source_hint in {"openclaw_internal_send", "openclaw_gateway_bridge"}
            else os.getenv("NUSYQ_CHATDEV_WAIT_FOR_COMPLETION", "1")
        )
        wait_for_completion = str(
            task.context.get(
                "chatdev_wait_for_completion",
                default_wait_for_completion,
            )
        ).strip().lower() in {"1", "true", "yes", "on"}
        timeout_override_s: float | None = None
        raw_timeout = task.context.get("timeout")
        if raw_timeout is None:
            raw_timeout = task.timeout_seconds
        try:
            parsed_timeout = float(raw_timeout)
            if parsed_timeout > 0:
                timeout_override_s = parsed_timeout
        except (TypeError, ValueError):
            timeout_override_s = None
        try:
            completion_timeout_s = float(
                task.context.get(
                    "chatdev_completion_timeout_s",
                    os.getenv("NUSYQ_CHATDEV_COMPLETION_TIMEOUT_S", "900"),
                )
            )
        except (TypeError, ValueError):
            completion_timeout_s = 900.0
        if timeout_override_s is not None:
            completion_timeout_s = max(5.0, min(completion_timeout_s, timeout_override_s))
            if timeout_override_s <= 20.0 and "chatdev_wait_for_completion" not in task.context:
                wait_for_completion = False
        else:
            completion_timeout_s = max(30.0, completion_timeout_s)

        def _launch() -> dict[str, Any]:
            launcher = ChatDevLauncher()
            process = launcher.launch_chatdev(
                task=task.content,
                name=project_name,
                model=model,
                organization=organization,
                config=config,
            )
            launch_info = {
                "pid": process.pid,
                "project_name": project_name,
                "model": model,
                "organization": organization,
                "config": config,
                "api_key_configured": launcher.api_key_configured,
                "chatdev_path": str(launcher.chatdev_path),
                "stdout_log": str(launcher.last_stdout_log) if launcher.last_stdout_log else None,
                "stderr_log": str(launcher.last_stderr_log) if launcher.last_stderr_log else None,
                "waited_for_completion": False,
            }
            stdout_log = launch_info.get("stdout_log")
            if isinstance(stdout_log, str):
                stem = Path(stdout_log).stem
                if stem.startswith("chatdev_stdout_"):
                    stamp = stem.removeprefix("chatdev_stdout_")
                    warehouse = Path(launch_info["chatdev_path"]) / "WareHouse"
                    warehouse_log = warehouse / f"{project_name}_{organization}_{stamp}.log"
                    launch_info["warehouse_log"] = str(warehouse_log)

            if wait_for_completion:
                launch_info["waited_for_completion"] = True
                launch_info["completion_timeout_s"] = completion_timeout_s
                if isinstance(process, subprocess.CompletedProcess):
                    launch_info["return_code"] = process.returncode
                elif isinstance(process, subprocess.Popen):
                    try:
                        launch_info["return_code"] = process.wait(timeout=completion_timeout_s)
                    except subprocess.TimeoutExpired:
                        launch_info["completion_status"] = "running_timeout"
                        return launch_info

                return_code = launch_info.get("return_code")
                if isinstance(return_code, int) and return_code != 0:
                    status_hint, marker = self._classify_chatdev_log_outcome(launch_info)
                    launch_info["completion_status"] = "failed"
                    launch_info["status_hint"] = status_hint
                    if marker:
                        launch_info["failure_signal"] = marker
                    return launch_info

                status_hint, marker = self._classify_chatdev_log_outcome(launch_info)
                if status_hint == "failed":
                    launch_info["completion_status"] = "failed"
                    if marker:
                        launch_info["failure_signal"] = marker
                else:
                    launch_info["completion_status"] = "success"
                    if marker:
                        launch_info["success_signal"] = marker
            return launch_info

        launch_timeout_seconds = float(os.getenv("NUSYQ_CHATDEV_LAUNCH_TIMEOUT_S", "45"))
        try:
            launch_info = await asyncio.wait_for(
                to_thread(_launch),
                timeout=launch_timeout_seconds,
            )
            completion_status = str(launch_info.get("completion_status", "launched")).lower()
            if completion_status == "failed":
                failure_signal = str(launch_info.get("failure_signal") or "unknown_failure")
                return {
                    "status": "failed",
                    "system": "chatdev",
                    "execution_path": "chatdev_launcher",
                    "task_id": task.task_id,
                    "error": f"ChatDev run failed after launch ({failure_signal})",
                    "suggestion": "Check ChatDev logs for details. Retry or route to ollama.",
                    "output": launch_info,
                }
            if completion_status == "running_timeout":
                return {
                    "status": "submitted",
                    "system": "chatdev",
                    "execution_path": "chatdev_launcher",
                    "output": launch_info,
                    "note": (
                        "ChatDev launched and is still running after completion timeout; monitor logs for final state."
                    ),
                    "task_id": task.task_id,
                }
            return {
                "status": "success",
                "system": "chatdev",
                "execution_path": "chatdev_launcher",
                "output": launch_info,
                "note": (
                    "ChatDev completed successfully."
                    if wait_for_completion
                    else "ChatDev process launched; monitor logs for completion."
                ),
                "task_id": task.task_id,
            }
        except TimeoutError:
            self._warn_with_cooldown(
                "chatdev_launcher_timeout",
                (f"ChatDev launch timed out after {launch_timeout_seconds:.1f}s; using fallback."),
            )
            return await self._chatdev_factory_fallback(
                task,
                f"launch_timeout>{launch_timeout_seconds:.1f}s",
            )
        except ImportError as exc:
            self._warn_with_cooldown(
                "chatdev_launcher_launch_import_error",
                f"ChatDev launcher unavailable during launch, using fallback: {exc}",
            )
            return await self._chatdev_factory_fallback(task, f"launcher_import_error: {exc}")
        except FileNotFoundError as exc:
            self._warn_with_cooldown(
                "chatdev_launcher_path_invalid",
                f"ChatDev path invalid, using fallback: {exc}",
            )
            return await self._chatdev_factory_fallback(task, f"path_invalid: {exc}")
        except RuntimeError as exc:
            self._warn_with_cooldown(
                "chatdev_launcher_runtime_error",
                f"ChatDev launch failed, using fallback: {exc}",
            )
            return await self._chatdev_factory_fallback(task, f"launch_runtime_error: {exc}")
        except (ValueError, TypeError) as exc:  # pragma: no cover - unexpected launch issues
            self._warn_with_cooldown(
                "chatdev_launcher_value_error",
                f"ChatDev routing failed, using fallback: {exc}",
            )
            return await self._chatdev_factory_fallback(task, f"launch_value_error: {exc}")

    async def _route_to_consciousness(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to Consciousness Bridge for semantic awareness."""
        logger.info(f"🧠 Routing to Consciousness Bridge: {task.content}")

        try:
            from src.integration.consciousness_bridge import \
                ConsciousnessBridge
        except ImportError as exc:
            self._warn_with_cooldown(
                "consciousness_bridge_unavailable",
                f"Consciousness Bridge unavailable, using heuristic fallback: {exc}",
            )
            return self._consciousness_heuristic_fallback(task, f"bridge_unavailable: {exc}")

        def _process() -> dict[str, Any]:
            bridge = ConsciousnessBridge()
            bridge.initialize()
            bridge.enhance_contextual_memory({"content": task.content, "context": task.context})
            retrieval = bridge.retrieve_contextual_memory(task.content)
            return {
                "context_memory": bridge.contextual_memory,
                "retrieval": retrieval,
                "initialized_at": bridge.get_initialization_time(),
            }

        try:
            payload = await to_thread(_process)
            hint = ConsciousnessHint(
                summary=(
                    str(payload.get("retrieval"))
                    if payload.get("retrieval")
                    else "Context enriched"
                ),
                tags=list(payload.get("context_memory", {}).keys()) or None,
                confidence=0.7,
            )
            return {
                "status": "success",
                "system": "consciousness",
                "execution_path": "consciousness_bridge:enhance_retrieve",
                "output": payload,
                "hint": asdict(hint),
                "task_id": task.task_id,
            }
        except (RuntimeError, ImportError, ValueError, AttributeError) as exc:
            self._warn_with_cooldown(
                "consciousness_bridge_runtime_error",
                f"Consciousness Bridge routing failed, using heuristic fallback: {exc}",
            )
            return self._consciousness_heuristic_fallback(task, f"bridge_runtime_error: {exc}")

    def _basic_workspace_scan(self, target: str | None = None) -> dict[str, Any]:
        """Fallback analyzer for environments where full analyzer is unavailable."""
        base = self.repo_root / "src"
        if target:
            target_path = (self.repo_root / target).resolve()
            if target_path.exists():
                base = target_path

        files = list(base.rglob("*.py")) if base.exists() else []
        working_count = 0
        broken_files: list[dict[str, Any]] = []

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                ast.parse(content)
                working_count += 1
            except (OSError, SyntaxError, ValueError) as exc:
                with contextlib.suppress(ValueError):
                    rel = str(file_path.relative_to(self.repo_root))
                    broken_files.append({"path": rel, "error": str(exc)})

        return {
            "scanner": "fallback_basic_workspace_scan",
            "target": str(base),
            "summary": {
                "total_files": len(files),
                "working_files": working_count,
                "broken_files": len(broken_files),
            },
            "broken_files": broken_files[:100],
        }

    async def _chatdev_factory_fallback(
        self, task: OrchestrationTask, reason: str
    ) -> dict[str, Any]:
        """Fallback to ProjectFactory when ChatDev is unavailable."""
        if ProjectFactory is None:
            return {
                "status": "failed",
                "error": f"ChatDev unavailable and ProjectFactory missing ({reason})",
                "system": "chatdev",
                "execution_path": "chatdev_factory_fallback:unavailable",
                "delegated_from": "chatdev",
                "suggestion": "Install ChatDev or ensure src.factories.ProjectFactory is importable.",
            }

        fallback_context = dict(task.context)
        if "template" not in fallback_context:
            fallback_context["template"] = DEFAULT_FACTORY_TEMPLATE
        if "project_name" not in fallback_context:
            fallback_context["project_name"] = fallback_context.get("name") or DEFAULT_CHATDEV_NAME
        if "ai_provider" not in fallback_context:
            fallback_context["ai_provider"] = "ollama"

        factory_task = OrchestrationTask(
            task_id=task.task_id,
            task_type="create_project",
            content=task.content,
            context=fallback_context,
            priority=task.priority,
            timeout_seconds=task.timeout_seconds,
        )

        factory_result = await self._route_to_factory(factory_task)
        if factory_result.get("status") == "success":
            factory_result["note"] = (
                f"ChatDev fallback succeeded via factory ({reason}). "
                f"Used provider={fallback_context.get('ai_provider')}."
            )
            factory_result["fallback_reason"] = reason
            factory_result.setdefault("delegated_from", "chatdev")
            factory_result.setdefault("delegated_to", "factory")
            factory_result.setdefault("execution_path", "chatdev_factory_fallback:factory")
            return factory_result

        return {
            "status": "failed",
            "error": (
                f"ChatDev unavailable ({reason}) and factory fallback failed: "
                f"{factory_result.get('error', 'unknown error')}"
            ),
            "system": "chatdev",
            "execution_path": "chatdev_factory_fallback:all_failed",
            "delegated_from": "chatdev",
            "fallback_result": factory_result,
            "suggestion": "Check ChatDev launcher and factory template/provider availability.",
        }

    def _consciousness_heuristic_fallback(
        self, task: OrchestrationTask, reason: str
    ) -> dict[str, Any]:
        """Return a non-failing heuristic consciousness result."""
        context_keys = sorted(task.context.keys())
        hint = ConsciousnessHint(
            summary=f"Heuristic context hint generated ({task.task_type})",
            tags=context_keys[:10] or ["no_context_keys"],
            confidence=0.3,
        )
        return {
            "status": "success",
            "system": "consciousness",
            "execution_path": "consciousness_heuristic_fallback",
            "mode": "heuristic_fallback",
            "output": {
                "reason": reason,
                "content_preview": task.content[:200],
                "context_keys": context_keys,
            },
            "hint": asdict(hint),
            "task_id": task.task_id,
            "note": "Consciousness bridge unavailable; heuristic fallback used.",
        }

    async def _route_to_quantum_resolver(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to Quantum Problem Resolver for self-healing."""
        logger.info(f"⚛️  Routing to Quantum Resolver: {task.content}")

        try:
            from src.healing.quantum_problem_resolver import \
                QuantumProblemResolver

            resolver = QuantumProblemResolver()
            requested_task_type = str(task.task_type or "analyze").strip().lower()
            context_problem_type = str(task.context.get("quantum_problem_type", "")).strip().lower()
            if context_problem_type in QUANTUM_SUPPORTED_PROBLEM_TYPES:
                problem_type = context_problem_type
            elif requested_task_type in QUANTUM_SUPPORTED_PROBLEM_TYPES:
                problem_type = requested_task_type
            else:
                problem_type = QUANTUM_TASK_TYPE_MAP.get(requested_task_type, "simulation")

            # Quantum Resolver analyzes and fixes complex issues
            result = await asyncio.to_thread(
                resolver.resolve_problem,
                problem_type,
                {
                    "content": task.content,
                    "context": task.context,
                    "requested_task_type": requested_task_type,
                },
            )
            result_status = (
                str(result.get("status", "")).strip().lower() if isinstance(result, dict) else ""
            )
            if result_status in {"error", "failed", "failure"}:
                error_message = (
                    result.get("error_message")
                    or result.get("message")
                    or result.get("error")
                    or f"Quantum resolver reported {result_status}"
                )
                return {
                    "status": "failed",
                    "system": "quantum_resolver",
                    "execution_path": f"quantum_problem_resolver:{problem_type}",
                    "error": str(error_message),
                    "suggestion": "Check resolver logs. Try a different problem_type or route to healing.",
                    "output": result,
                    "task_id": task.task_id,
                    "problem_type": problem_type,
                    "requested_task_type": requested_task_type,
                }

            return {
                "status": "success",
                "system": "quantum_resolver",
                "execution_path": f"quantum_problem_resolver:{problem_type}",
                "output": result,
                "task_id": task.task_id,
                "problem_type": problem_type,
                "requested_task_type": requested_task_type,
            }

        except (RuntimeError, ValueError) as e:
            logger.error(f"Quantum Resolver routing failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "system": "quantum_resolver",
                "execution_path": "quantum_problem_resolver:error",
                "task_id": task.task_id,
            }

    async def _route_to_factory(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to NuSyQ Factory for project creation.

        Factory intelligently selects AI providers (ChatDev > Ollama > Claude > OpenAI)
        based on project complexity, offline needs, and budget.
        """
        logger.info(f"🏭 Routing to Factory: {task.content}")

        if ProjectFactory is None:
            logger.error("Factory unavailable: ProjectFactory import failed")
            return {
                "status": "failed",
                "error": "Factory unavailable: ProjectFactory import failed",
                "system": "factory",
                "execution_path": "factory:unavailable",
                "task_id": task.task_id,
                "suggestion": "Ensure factory modules are installed.",
            }

        if task.task_type == "factory_health":
            include_packaging = bool(task.context.get("include_packaging", True))

            def _health() -> dict[str, Any]:
                factory = ProjectFactory()
                payload = factory.run_health_check(include_packaging=include_packaging)
                return payload if isinstance(payload, dict) else {"output": payload}

            try:
                health = await to_thread(_health)
                return {
                    "status": "success" if health.get("healthy") else "failed",
                    "system": "factory",
                    "execution_path": "factory:health",
                    "output": health,
                    "task_id": task.task_id,
                }
            except (ImportError, RuntimeError, ValueError, OSError) as exc:
                logger.error(f"Factory health failed: {exc}")
                return {
                    "status": "failed",
                    "error": str(exc),
                    "system": "factory",
                    "execution_path": "factory:health",
                    "task_id": task.task_id,
                    "suggestion": "Check factory configuration and provider availability",
                }

        if task.task_type == "factory_doctor":
            strict_hooks = bool(task.context.get("strict_hooks", False))
            include_examples = bool(task.context.get("include_examples", True))
            include_health = bool(task.context.get("include_health", True))
            recent_limit = int(task.context.get("recent_limit", 25))

            def _doctor() -> dict[str, Any]:
                factory = ProjectFactory()
                payload = factory.run_doctor(
                    strict_hooks=strict_hooks,
                    include_examples=include_examples,
                    include_health=include_health,
                    recent_limit=recent_limit,
                )
                return payload if isinstance(payload, dict) else {"output": payload}

            try:
                report = await to_thread(_doctor)
                return {
                    "status": "success" if report.get("healthy") else "failed",
                    "system": "factory",
                    "execution_path": "factory:doctor",
                    "output": report,
                    "task_id": task.task_id,
                }
            except (ImportError, RuntimeError, ValueError, OSError) as exc:
                logger.error(f"Factory doctor failed: {exc}")
                return {
                    "status": "failed",
                    "error": str(exc),
                    "system": "factory",
                    "execution_path": "factory:doctor",
                    "task_id": task.task_id,
                    "suggestion": "Check factory diagnostics dependencies and provider accessibility",
                }

        if task.task_type == "factory_doctor_fix":
            strict_hooks = bool(task.context.get("strict_hooks", False))
            include_examples = bool(task.context.get("include_examples", True))
            include_health = bool(task.context.get("include_health", True))
            recent_limit = int(task.context.get("recent_limit", 25))

            def _doctor_fix() -> dict[str, Any]:
                factory = ProjectFactory()
                payload = factory.run_doctor_fix(
                    strict_hooks=strict_hooks,
                    include_examples=include_examples,
                    include_health=include_health,
                    recent_limit=recent_limit,
                )
                return payload if isinstance(payload, dict) else {"output": payload}

            try:
                report = await to_thread(_doctor_fix)
                healthy = bool(report.get("post_fix", {}).get("healthy"))
                return {
                    "status": "success" if healthy else "failed",
                    "system": "factory",
                    "execution_path": "factory:doctor_fix",
                    "output": report,
                    "task_id": task.task_id,
                }
            except (ImportError, RuntimeError, ValueError, OSError) as exc:
                logger.error(f"Factory doctor-fix failed: {exc}")
                return {
                    "status": "failed",
                    "error": str(exc),
                    "system": "factory",
                    "execution_path": "factory:doctor_fix",
                    "task_id": task.task_id,
                    "suggestion": "Check factory remediation dependencies and filesystem permissions",
                }

        if task.task_type == "factory_autopilot":
            strict_hooks = bool(task.context.get("strict_hooks", False))
            include_examples = bool(task.context.get("include_examples", True))
            apply_fix = bool(task.context.get("fix", False))
            recent_limit = int(task.context.get("recent_limit", 25))
            raw_paths = task.context.get("paths")
            paths = raw_paths if isinstance(raw_paths, list) else None

            def _autopilot() -> dict[str, Any]:
                factory = ProjectFactory()
                payload = factory.run_autopilot(
                    fix=apply_fix,
                    strict_hooks=strict_hooks,
                    include_examples=include_examples,
                    recent_limit=recent_limit,
                    example_paths=paths,
                )
                return payload if isinstance(payload, dict) else {"output": payload}

            try:
                report = await to_thread(_autopilot)
                return {
                    "status": "success" if report.get("healthy") else "failed",
                    "system": "factory",
                    "execution_path": "factory:autopilot",
                    "output": report,
                    "task_id": task.task_id,
                }
            except (ImportError, RuntimeError, ValueError, OSError) as exc:
                logger.error(f"Factory autopilot failed: {exc}")
                return {
                    "status": "failed",
                    "error": str(exc),
                    "system": "factory",
                    "execution_path": "factory:autopilot",
                    "task_id": task.task_id,
                    "suggestion": "Verify factory health and example paths for autopilot loop",
                }

        if task.task_type == "factory_inspect_examples":
            raw_paths = task.context.get("paths")
            paths = raw_paths if isinstance(raw_paths, list) else None

            def _inspect() -> dict[str, Any]:
                factory = ProjectFactory()
                payload = factory.inspect_reference_games(paths=paths)
                return payload if isinstance(payload, dict) else {"output": payload}

            try:
                inspection = await to_thread(_inspect)
                return {
                    "status": "success",
                    "system": "factory",
                    "execution_path": "factory:inspect_examples",
                    "output": inspection,
                    "task_id": task.task_id,
                }
            except (ImportError, RuntimeError, ValueError, OSError) as exc:
                logger.error(f"Factory example inspection failed: {exc}")
                return {
                    "status": "failed",
                    "error": str(exc),
                    "system": "factory",
                    "execution_path": "factory:inspect_examples",
                    "task_id": task.task_id,
                    "suggestion": "Verify reference paths and factory accessibility",
                }

        if task.task_type != "create_project":
            return {
                "status": "failed",
                "error": (
                    "Factory supports task types: "
                    "'create_project', 'factory_health', 'factory_doctor', "
                    "'factory_doctor_fix', 'factory_autopilot', 'factory_inspect_examples'"
                ),
                "suggestion": "Set task_type to a supported factory operation.",
                "system": "factory",
                "execution_path": "factory:invalid_task_type",
                "task_id": task.task_id,
            }

        # Extract project parameters from context
        project_name = str(
            task.context.get("project_name") or task.context.get("name") or "NewProject"
        )
        template = str(task.context.get("template") or "default_game")
        version = str(task.context.get("version") or "1.0.0")
        description = task.content
        ai_provider = task.context.get("ai_provider") or "auto"

        def _create() -> dict[str, Any]:
            factory = ProjectFactory()
            result = factory.create(
                name=project_name,
                template=template,
                version=version,
                description=description,
                ai_provider=ai_provider,
            )
            return {
                "name": result.name,
                "type": result.type,
                "version": result.version,
                "output_path": str(result.output_path),
                "ai_provider": result.ai_provider,
                "model_used": result.model_used,
                "token_cost": result.token_cost,
                "warehouse_path": (
                    str(result.chatdev_warehouse_path) if result.chatdev_warehouse_path else None
                ),
            }

        try:
            project_info = await to_thread(_create)
            return {
                "status": "success",
                "system": "factory",
                "execution_path": "factory:create_project",
                "output": project_info,
                "task_id": task.task_id,
                "note": f"Project '{project_name}' created successfully",
            }
        except FileNotFoundError as exc:
            logger.error(f"Template not found: {exc}")
            return {
                "status": "failed",
                "error": f"Template not found: {exc}",
                "system": "factory",
                "execution_path": "factory:create_project",
                "task_id": task.task_id,
                "suggestion": "Check template name or create custom template",
            }
        except (ImportError, RuntimeError, ValueError, OSError) as exc:
            logger.error(f"Factory creation failed: {exc}")
            return {
                "status": "failed",
                "error": str(exc),
                "system": "factory",
                "execution_path": "factory:create_project",
                "task_id": task.task_id,
                "suggestion": "Check factory configuration and ensure AI providers are available",
            }

    # ========================================================================
    # PHASE 3 GENERATOR ROUTING HANDLERS
    # ========================================================================

    def _wrap_generator_result(
        self, payload: Any, system: str, task: OrchestrationTask
    ) -> dict[str, Any]:
        """Normalize Phase 3 generator results to canonical router schema."""
        base = payload if isinstance(payload, dict) else {"output": payload}
        base.setdefault(
            "status",
            "success" if base.get("output") or base.get("schema") or base.get("spec") else "error",
        )
        base.setdefault("system", system)
        base.setdefault("task_id", task.task_id)
        base.setdefault("execution_path", f"phase3_generator:{system}")
        return base

    async def _route_to_graphql_generator(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to GraphQL API generator."""
        from src.orchestration.generator_integration import \
            generate_graphql_api

        description = task.context.get("description", task.task_type)
        logger.info(f"🔧 Routing to GraphQL generator: {description}")
        payload = await generate_graphql_api(description, task.context)
        return self._wrap_generator_result(payload, "graphql_generator", task)

    async def _route_to_openapi_generator(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to OpenAPI/REST generator."""
        from src.orchestration.generator_integration import \
            generate_openapi_spec

        description = task.context.get("description", task.task_type)
        logger.info(f"🔧 Routing to OpenAPI generator: {description}")
        payload = await generate_openapi_spec(description, task.context)
        return self._wrap_generator_result(payload, "openapi_generator", task)

    async def _route_to_component_generator(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to React component generator."""
        from src.orchestration.generator_integration import \
            generate_react_component

        description = task.context.get("description", task.task_type)
        logger.info(f"🔧 Routing to Component generator: {description}")
        payload = await generate_react_component(description, task.context)
        return self._wrap_generator_result(payload, "component_generator", task)

    async def _route_to_database_generator(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to database schema generator."""
        from src.orchestration.generator_integration import \
            generate_database_schema

        description = task.context.get("description", task.task_type)
        logger.info(f"🔧 Routing to Database generator: {description}")
        payload = await generate_database_schema(description, task.context)
        return self._wrap_generator_result(payload, "database_generator", task)

    async def _route_to_project_generator(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to universal project generator."""
        from src.orchestration.generator_integration import \
            generate_universal_project

        description = task.context.get("description", task.task_type)
        logger.info(f"🔧 Routing to Universal Project generator: {description}")
        payload = await generate_universal_project(description, task.context)
        return self._wrap_generator_result(payload, "project_generator", task)

    async def _route_to_openclaw(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to OpenClaw Gateway for external messaging.

        OpenClaw Gateway bridges 12+ messaging platforms (Slack, Discord, Telegram,
        WhatsApp, Teams, Matrix, etc.). Use this to send messages out via external
        channels or route tasks to specific platform channels.

        Context keys:
            channel: Target channel/platform (slack, discord, telegram, etc.)
            target_user_id: User ID in target platform (optional)
            message: Message to send (defaults to task.content)

        Example:
            >>> result = await router.route_task(
            ...     "send_message",
            ...     "Notify user of analysis completion",
            ...     context={"channel": "slack", "target_user_id": "U12345"},
            ...     target_system="openclaw"
            ... )
        """
        logger.info(f"📡 Routing to OpenClaw Gateway: {task.task_id}")

        try:
            from src.integrations.openclaw_gateway_bridge import \
                OpenClawGatewayBridge

            bridge = OpenClawGatewayBridge()

            # Extract messaging context
            channel = task.context.get("channel", "internal")
            target_user_id = task.context.get("target_user_id", "nusyq")
            message = task.context.get("message", task.content)

            # For internal/loopback, just log and return success
            if channel.lower() in {"internal", "loopback", "local", "nusyq", "terminal"}:
                logger.info(f"📝 OpenClaw internal message from {task.task_id}: {message[:100]}")
                self._emit_terminal_event(
                    "openclaw",
                    "openclaw_internal_message",
                    f"openclaw internal message channel={channel}",
                    task_id=task.task_id,
                    extra={"execution_path": "openclaw_gateway", "channel": channel},
                )
                return {
                    "status": "success",
                    "system": "openclaw",
                    "agent": "openclaw",
                    "channel": channel,
                    "output": f"Message: {message[:200]}...",
                    "message": f"Message: {message[:200]}...",
                    "task_id": task.task_id,
                    "execution_path": "openclaw_gateway",
                }

            # For external channels, connect and send
            connected = await bridge.connect()
            if not connected:
                self._emit_terminal_event(
                    "openclaw",
                    "openclaw_connect_failed",
                    "openclaw gateway connect failed",
                    level="WARNING",
                    task_id=task.task_id,
                    extra={"execution_path": "openclaw_gateway", "channel": channel},
                )
                return {
                    "status": "failed",
                    "system": "openclaw",
                    "agent": "openclaw",
                    "error": "Failed to connect to OpenClaw Gateway",
                    "task_id": task.task_id,
                    "execution_path": "openclaw_gateway",
                }

            success = await bridge.send_result(
                channel=channel,
                target_user_id=target_user_id,
                result_text=message,
                task_id=task.task_id,
            )

            await bridge.disconnect()
            self._emit_terminal_event(
                "openclaw",
                "openclaw_send_result",
                f"openclaw send channel={channel} sent={success}",
                level="INFO" if success else "WARNING",
                task_id=task.task_id,
                extra={"execution_path": "openclaw_gateway", "channel": channel, "sent": success},
            )

            return {
                "status": "success" if success else "failed",
                "system": "openclaw",
                "agent": "openclaw",
                "channel": channel,
                "target_user_id": target_user_id,
                "output": message,
                "sent": success,
                "task_id": task.task_id,
                "execution_path": "openclaw_gateway",
            }

        except ImportError as e:
            logger.error(f"❌ OpenClaw bridge not available: {e}")
            self._emit_terminal_event(
                "openclaw",
                "openclaw_import_failed",
                f"openclaw bridge import failed: {e}",
                level="WARNING",
                task_id=task.task_id,
                extra={"execution_path": "openclaw_gateway"},
            )
            return {
                "status": "failed",
                "agent": "openclaw",
                "error": f"OpenClaw bridge import failed: {e}",
                "task_id": task.task_id,
                "execution_path": "openclaw_gateway",
            }
        except Exception as e:
            logger.error(f"❌ OpenClaw routing failed: {e}")
            self._emit_terminal_event(
                "openclaw",
                "openclaw_route_failed",
                f"openclaw route failed: {e}",
                level="WARNING",
                task_id=task.task_id,
                extra={"execution_path": "openclaw_gateway"},
            )
            return {
                "status": "failed",
                "agent": "openclaw",
                "error": str(e),
                "task_id": task.task_id,
                "execution_path": "openclaw_gateway",
            }

    async def _route_to_intermediary(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to AI Intermediary for cognitive bridge processing.

        The AI Intermediary handles multi-paradigm AI communication and translation,
        supporting paradigms like natural language, symbolic logic, quantum notation,
        game mechanics, and code analysis. Use for complex AI orchestration.

        Context keys:
            paradigm: Source paradigm (natural_language, symbolic_logic, code_analysis, etc.)
            target_paradigm: Output paradigm to translate to (optional)
            target_module: Specific registered module to route to (optional)
            use_ollama: Process via Ollama backend (default: False)

        Example:
            >>> result = await router.route_task(
            ...     "analyze",
            ...     "Analyze this code for quantum optimization opportunities",
            ...     context={"paradigm": "code_analysis", "use_ollama": True},
            ...     target_system="intermediary"
            ... )
        """
        logger.info(f"🧠 Routing to AI Intermediary: {task.task_id}")

        try:
            from src.ai.ai_intermediary import (AIIntermediary,
                                                CognitiveParadigm)

            intermediary = AIIntermediary()

            # Parse paradigm from context
            paradigm_str = task.context.get("paradigm", "natural_language")
            try:
                paradigm = CognitiveParadigm(paradigm_str)
            except ValueError:
                paradigm = CognitiveParadigm.NATURAL_LANGUAGE

            # Parse target paradigm if provided
            target_paradigm = None
            target_paradigm_str = task.context.get("target_paradigm")
            if target_paradigm_str:
                with contextlib.suppress(ValueError):
                    target_paradigm = CognitiveParadigm(target_paradigm_str)

            # Handle the cognitive event
            event = await intermediary.handle(
                input_data=task.content,
                context=task.context,
                source=f"agent_router:{task.task_id}",
                paradigm=paradigm,
                target_module=task.context.get("target_module"),
                target_paradigm=target_paradigm,
                use_ollama=task.context.get("use_ollama", False),
                translate_output=task.context.get("translate_output", True),
            )

            return {
                "status": "success",
                "system": "intermediary",
                "execution_path": "ai_intermediary:handle",
                "agent": "intermediary",
                "output": {
                    "event_id": event.event_id,
                    "paradigm": event.paradigm.value,
                    "payload": event.payload,
                    "tags": event.tags,
                },
                "task_id": task.task_id,
            }

        except ImportError as e:
            logger.error(f"❌ AI Intermediary not available: {e}")
            return {
                "status": "failed",
                "system": "intermediary",
                "execution_path": "ai_intermediary:unavailable",
                "agent": "intermediary",
                "error": f"AI Intermediary import failed: {e}",
                "task_id": task.task_id,
            }
        except Exception as e:
            logger.error(f"❌ AI Intermediary routing failed: {e}")
            return {
                "status": "failed",
                "system": "intermediary",
                "execution_path": "ai_intermediary:error",
                "agent": "intermediary",
                "error": str(e),
                "task_id": task.task_id,
            }

    async def _route_to_skyclaw(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to SkyClaw Rust autonomous sidecar.

        SkyClaw is a hyper-performance Rust sidecar supporting 6 AI providers
        (OpenAI, Anthropic, MistralAI, Ollama, HuggingFace, Replicate) and 4
        messaging channels (Terminal, WebSocket, REST, File). Optimized for
        autonomous agent workflows with low-latency execution.

        Context keys:
            action: SkyClaw action (analyze, generate, review, debug, plan)
            model: Model to use (defaults to auto-select)
            output_format: Output format (json, text, markdown)
            timeout_s: Execution timeout in seconds (default: 60)

        Example:
            >>> result = await router.route_task(
            ...     "analyze",
            ...     "Review this Rust module for performance issues",
            ...     context={"action": "analyze", "output_format": "json"},
            ...     target_system="skyclaw"
            ... )
        """
        logger.info(f"🦀 Routing to SkyClaw sidecar: {task.task_id}")

        # Locate SkyClaw binary
        skyclaw_binary: Path | None = None
        state_dir = self.repo_root / "state" / "runtime" / "skyclaw"

        # Check for binary (Windows .exe or Linux)
        for bin_name in ["skyclaw.exe", "skyclaw"]:
            candidate = state_dir / "target" / "debug" / bin_name
            if candidate.exists():
                skyclaw_binary = candidate
                break

        # WSL fallback for Windows
        if skyclaw_binary is None and sys.platform == "win32":
            wsl_path = "/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub/state/runtime/skyclaw/target/debug/skyclaw"
            try:
                result = subprocess.run(
                    ["wsl", "-e", "test", "-x", wsl_path],
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    skyclaw_binary = Path(wsl_path)  # Marker for WSL mode
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        if skyclaw_binary is None:
            logger.warning("⚠️ SkyClaw binary not found, falling back to Ollama")
            fallback = await self._route_to_ollama(task)
            if isinstance(fallback, dict):
                fallback.setdefault("delegated_from", "skyclaw")
                fallback.setdefault("delegated_to", "ollama")
            return fallback

        # Extract context parameters
        action = task.context.get("action", task.task_type or "analyze")
        output_format = task.context.get("output_format", "json")
        timeout_s = int(task.context.get("timeout_s", 60))

        try:
            self._emit_terminal_event(
                "skyclaw",
                "skyclaw_start",
                f"skyclaw start action={action} format={output_format}",
                task_id=task.task_id,
                extra={"execution_path": "skyclaw_binary", "action": action},
            )
            # Build command
            cmd: list[str]
            if str(skyclaw_binary).startswith("/mnt/"):
                # WSL execution
                cmd = [
                    "wsl",
                    "-e",
                    str(skyclaw_binary),
                    "--action",
                    action,
                    "--format",
                    output_format,
                    "--prompt",
                    task.content[:2000],  # Limit prompt length
                ]
            else:
                # Native execution
                cmd = [
                    str(skyclaw_binary),
                    "--action",
                    action,
                    "--format",
                    output_format,
                    "--prompt",
                    task.content[:2000],
                ]

            # Execute SkyClaw
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(state_dir),
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_s,
            )

            output = stdout.decode("utf-8", errors="replace").strip()
            error_output = stderr.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0:
                logger.warning(
                    f"⚠️ SkyClaw exited with code {proc.returncode}: {error_output[:200]}"
                )
                self._emit_terminal_event(
                    "skyclaw",
                    "skyclaw_failed",
                    f"skyclaw failed rc={proc.returncode}",
                    level="WARNING",
                    task_id=task.task_id,
                    extra={
                        "execution_path": "skyclaw_binary",
                        "action": action,
                        "returncode": proc.returncode,
                    },
                )
                return {
                    "status": "failed",
                    "system": "skyclaw",
                    "agent": "skyclaw",
                    "error": error_output[:500] or f"Exit code {proc.returncode}",
                    "task_id": task.task_id,
                    "execution_path": "skyclaw_binary",
                }

            # Parse JSON output if requested
            if output_format == "json" and output:
                try:
                    parsed = json.loads(output)
                    return {
                        "status": "success",
                        "system": "skyclaw",
                        "agent": "skyclaw",
                        "output": parsed,
                        "result": parsed,
                        "action": action,
                        "task_id": task.task_id,
                        "execution_path": "skyclaw_binary",
                    }
                except json.JSONDecodeError:
                    pass  # Fall through to text return

            self._emit_terminal_event(
                "skyclaw",
                "skyclaw_success",
                f"skyclaw success action={action}",
                task_id=task.task_id,
                extra={"execution_path": "skyclaw_binary", "action": action},
            )
            return {
                "status": "success",
                "system": "skyclaw",
                "agent": "skyclaw",
                "output": output or "(empty output)",
                "result": output or "(empty output)",
                "action": action,
                "task_id": task.task_id,
                "execution_path": "skyclaw_binary",
            }

        except TimeoutError:
            logger.error(f"❌ SkyClaw timed out after {timeout_s}s")
            self._emit_terminal_event(
                "skyclaw",
                "skyclaw_timeout",
                f"skyclaw timeout>{timeout_s}s",
                level="WARNING",
                task_id=task.task_id,
                extra={"execution_path": "skyclaw_binary", "action": action},
            )
            return {
                "status": "failed",
                "system": "skyclaw",
                "agent": "skyclaw",
                "error": f"Execution timed out after {timeout_s}s",
                "task_id": task.task_id,
                "execution_path": "skyclaw_binary",
            }
        except Exception as e:
            logger.error(f"❌ SkyClaw routing failed: {e}")
            self._emit_terminal_event(
                "skyclaw",
                "skyclaw_route_failed",
                f"skyclaw route failed: {e}",
                level="WARNING",
                task_id=task.task_id,
                extra={"execution_path": "skyclaw_binary", "action": action},
            )
            return {
                "status": "failed",
                "system": "skyclaw",
                "agent": "skyclaw",
                "error": str(e),
                "task_id": task.task_id,
                "execution_path": "skyclaw_binary",
            }

    async def _route_to_hermes(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to Hermes-Agent (OpenRouter autonomous Python CLI agent).

        Hermes is a full autonomous agent with web search, terminal execution,
        file I/O, and RAG capabilities.  Backed by OpenRouter (configurable
        model, defaults to claude-opus-4). Supports isolated git worktrees for
        parallel agent execution.

        Context keys:
            toolsets: Comma-separated toolsets to enable (default: "web,terminal")
            model: OpenRouter model slug (default: anthropic/claude-opus-4-20250514)
            provider: Inference provider slug (default: "auto")
            max_turns: Maximum tool-calling iterations (default: 60)
            worktree: bool — run in isolated git worktree (default: False)
            timeout_seconds: Execution timeout (default: NUSYQ_CLAUDE_ROUTER_TIMEOUT_S or 600)
        """
        logger.info("🪄 Routing to Hermes-Agent: %s", task.task_id)

        hermes_dir = self.repo_root / "state" / "runtime" / "external" / "hermes-agent"
        cli_path = hermes_dir / "cli.py"
        if not cli_path.exists():
            self._emit_terminal_event(
                "hermes",
                "hermes_missing",
                "Hermes-Agent cli.py not found",
                level="WARNING",
                task_id=task.task_id,
            )
            return {
                "status": "failed",
                "system": "hermes",
                "task_id": task.task_id,
                "error": "hermes_cli_not_found",
                "execution_path": "hermes_cli",
                "handoff": {
                    "install": "Clone hermes-agent into state/runtime/external/hermes-agent/",
                    "docs": "https://github.com/KiloMusician/hermes-agent",
                },
            }

        timeout_seconds = self._adaptive_timeout(
            int(
                task.context.get(
                    "timeout_seconds", os.getenv("NUSYQ_CLAUDE_ROUTER_TIMEOUT_S", "600")
                )
            )
        )
        prompt = self._build_cli_prompt(task)

        # Build command: python <hermes_dir>/cli.py -q "<prompt>" [flags]
        python_bin = sys.executable
        cmd: list[str] = [python_bin, str(cli_path), "-q", prompt]

        toolsets = str(task.context.get("toolsets", "")).strip()
        if toolsets:
            cmd.extend(["--toolsets", toolsets])

        model = str(task.context.get("model", "")).strip()
        if model:
            cmd.extend(["--model", model])

        provider = str(task.context.get("provider", "")).strip()
        if provider:
            cmd.extend(["--provider", provider])

        max_turns = task.context.get("max_turns")
        if max_turns is not None:
            cmd.extend(["--max-turns", str(max_turns)])

        if task.context.get("worktree"):
            cmd.append("--worktree")

        # Quiet mode for non-interactive dispatch
        cmd.append("--quiet")

        self._emit_terminal_event(
            "hermes",
            "hermes_start",
            f"hermes start timeout={timeout_seconds}s",
            task_id=task.task_id,
            extra={"execution_path": "hermes_cli", "toolsets": toolsets or "default"},
        )

        output_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                suffix="_router_hermes_output.txt",
                encoding="utf-8",
            ) as tmp:
                output_path = Path(tmp.name)

            returncode, stdout, stderr = await self._run_cli_command(
                cmd, "", timeout_seconds, cwd=str(hermes_dir)
            )
            output = stdout.strip() or stderr.strip()

            if returncode == 0 and output:
                self._emit_terminal_event(
                    "hermes",
                    "hermes_success",
                    f"hermes success chars={len(output)}",
                    task_id=task.task_id,
                    extra={"execution_path": "hermes_cli", "output_chars": len(output)},
                )
                return {
                    "status": "success",
                    "system": "hermes",
                    "task_id": task.task_id,
                    "output": output,
                    "execution_path": "hermes_cli",
                }

            self._emit_terminal_event(
                "hermes",
                "hermes_failed",
                f"hermes failed rc={returncode}",
                level="WARNING",
                task_id=task.task_id,
                extra={"execution_path": "hermes_cli", "returncode": returncode},
            )
            return {
                "status": "failed",
                "system": "hermes",
                "task_id": task.task_id,
                "execution_path": "hermes_cli",
                "error": (
                    f"hermes_failed rc={returncode} stderr_tail={stderr[-1200:]!r} stdout_tail={stdout[-1200:]!r}"
                ),
            }
        except TimeoutError:
            self._emit_terminal_event(
                "hermes",
                "hermes_timeout",
                f"hermes timeout>{timeout_seconds}s",
                level="WARNING",
                task_id=task.task_id,
                extra={"execution_path": "hermes_cli"},
            )
            return {
                "status": "failed",
                "system": "hermes",
                "task_id": task.task_id,
                "execution_path": "hermes_cli",
                "error": f"hermes_timeout>{timeout_seconds}s",
            }
        except OSError as exc:
            self._emit_terminal_event(
                "hermes",
                "hermes_error",
                f"hermes error: {exc}",
                level="WARNING",
                task_id=task.task_id,
                extra={"execution_path": "hermes_cli"},
            )
            return {
                "status": "failed",
                "system": "hermes",
                "task_id": task.task_id,
                "execution_path": "hermes_cli",
                "error": f"hermes_exec_error:{exc}",
            }
        finally:
            if output_path is not None:
                with contextlib.suppress(OSError):
                    output_path.unlink()

    # ========================================================================
    # QUEST LOGGING & HEALTH CHECK
    # ========================================================================

    def _log_to_quest(
        self,
        task_type: str,
        description: str,
        status: str,
        result: dict[str, Any] | None = None,
    ) -> None:
        """Log task to quest system for persistence."""
        try:
            quest_entry = {
                "timestamp": datetime.now().isoformat(),
                "task_type": task_type,
                "description": description,
                "status": status,
                "result": result,
            }

            # Ensure quest log directory exists
            self.quest_log_path.parent.mkdir(parents=True, exist_ok=True)

            # Append to quest log
            with open(self.quest_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(quest_entry) + "\n")

            logger.debug(f"Logged to quest system: {task_type} - {status}")

        except OSError as e:
            logger.warning(f"Failed to log to quest system: {e}")

    async def health_check(self) -> dict[str, Any]:
        """Check health of all AI systems.

        Returns:
            Health status for each system

        Example:
            >>> router = AgentTaskRouter()
            >>> status = await router.health_check()
            >>> print(status["ollama"]["healthy"])  # True/False
        """
        logger.info("🏥 Running system health check...")

        health: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "systems": {},
        }

        # Check Ollama. Keep this metadata-first by default to avoid blocking
        # router health in restricted/sandboxed environments.
        ollama_runtime_probe = str(
            os.getenv("NUSYQ_ROUTER_HEALTH_NETWORK", "0")
        ).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if ollama_runtime_probe:
            try:
                import requests

                response = await asyncio.to_thread(
                    requests.get, "http://localhost:11434/api/tags", timeout=2
                )
                health["systems"]["ollama"] = {
                    "healthy": response.status_code == 200,
                    "models": [m["name"] for m in response.json().get("models", [])],
                    "check_mode": "runtime",
                }
            except requests.RequestException as e:
                health["systems"]["ollama"] = {
                    "healthy": False,
                    "error": str(e),
                    "check_mode": "runtime",
                }
        else:
            ollama_hint = (
                bool(shutil.which("ollama"))
                or bool(os.getenv("OLLAMA_BASE_URL"))
                or bool(os.getenv("OLLAMA_HOST"))
            )
            health["systems"]["ollama"] = {
                "healthy": bool(ollama_hint),
                "check_mode": "metadata",
            }

        # Check ChatDev
        if get_repo_path is not None:
            try:
                nusyq_root = get_repo_path("NUSYQ_ROOT")
            except (ValueError, RuntimeError, OSError):
                nusyq_root = Path.home() / "NuSyQ"
        else:
            nusyq_root = Path.home() / "NuSyQ"
        chatdev_path = nusyq_root / "ChatDev"
        health["systems"]["chatdev"] = {
            "healthy": chatdev_path.exists(),
            "path": str(chatdev_path) if chatdev_path.exists() else None,
        }

        # Check Consciousness Bridge
        try:
            from src.integration.consciousness_bridge import \
                ConsciousnessBridge

            # Verify it imports successfully
            _ = ConsciousnessBridge
            health["systems"]["consciousness_bridge"] = {
                "healthy": True,
                "available": True,
            }
        except ImportError as e:
            health["systems"]["consciousness_bridge"] = {
                "healthy": False,
                "error": str(e),
            }

        # Check Quantum Problem Resolver
        try:
            from src.healing.quantum_problem_resolver import \
                QuantumProblemResolver

            # Verify it imports successfully
            _ = QuantumProblemResolver
            health["systems"]["quantum_resolver"] = {
                "healthy": True,
                "available": True,
            }
        except ImportError as e:
            health["systems"]["quantum_resolver"] = {
                "healthy": False,
                "error": str(e),
            }

        # Check Factory (if available). Default to metadata-only probe to keep
        # router health bounded and avoid slow brownfield side effects.
        try:
            if ProjectFactory is None:
                health["systems"]["factory"] = {
                    "healthy": False,
                    "error": "ProjectFactory not available (optional dependency)",
                }
            else:
                factory_mode = (
                    str(os.getenv("NUSYQ_ROUTER_FACTORY_HEALTH_MODE", "metadata")).strip().lower()
                )
                if factory_mode in {"runtime", "full"}:
                    factory = ProjectFactory()
                    factory_report = await to_thread(
                        factory.run_health_check,
                        False,  # quick mode inside router health
                    )
                    health["systems"]["factory"] = {
                        "healthy": bool(factory_report.get("healthy")),
                        "available": True,
                        "check_mode": "runtime",
                        "checks": factory_report.get("checks", []),
                    }
                else:
                    health["systems"]["factory"] = {
                        "healthy": True,
                        "available": True,
                        "check_mode": "metadata",
                    }
        except (ImportError, RuntimeError, AttributeError) as e:
            health["systems"]["factory"] = {
                "healthy": False,
                "error": str(e),
            }

        # Check Orchestration modules
        health["systems"]["orchestration"] = {
            "healthy": True,
            "modules": ["multi_ai_orchestrator", "unified_ai_orchestrator"],
        }

        return health

    # ============================================================================
    # AGENT-FRIENDLY INTERFACE
    # ============================================================================

    async def _route_to_devtool(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to DevTool+ for browser automation.

        DevTool+ provides Chrome DevTools MCP tools for:
        - Page management (navigate, open, close, list pages)
        - DOM interaction (click, fill, hover, type)
        - Screenshots and snapshots
        - Network/console monitoring
        - Lighthouse performance audits
        - JavaScript execution

        Context keys:
            action: DevTool+ action (navigate, click, screenshot, lighthouse, etc.)
            url: Target URL for navigation
            selector: CSS selector for DOM operations
            script: JavaScript to execute

        Example:
            >>> result = await router.route_task(
            ...     "test",
            ...     "Run Lighthouse audit on https://example.com",
            ...     context={"action": "lighthouse", "url": "https://example.com"},
            ...     target_system="devtool"
            ... )
        """
        logger.info(f"🌐 Routing to DevTool+ (Chrome DevTools MCP): {task.task_id}")

        try:
            from src.integrations.devtool_bridge import (DEVTOOL_MCP_TOOLS,
                                                         DevToolBridge)

            bridge = DevToolBridge()
            status = bridge.get_status()

            if not bridge.is_operational():
                return {
                    "status": "failed",
                    "agent": "devtool",
                    "system": "devtool",
                    "execution_path": "devtool_bridge:info",
                    "error": "No supported browser detected for DevTool+",
                    "recommendation": "Install Google Chrome for full support, or ensure Edge is visible to the WSL workspace",
                    "task_id": task.task_id,
                }

            browser_probe = bridge.probe_browser()
            edge_probe = bridge.probe_edge_fallback()
            browser_mode = "chrome" if status.chrome_available else "edge_fallback"
            browser_path = browser_probe.path if status.chrome_available else edge_probe.path

            # Extract context
            action = task.context.get("action", "info")
            url = task.context.get("url")
            selector = task.context.get("selector")

            # Map actions to MCP tool recommendations
            action_map = {
                "navigate": "mcp_chromedevtool_navigate_page",
                "click": "mcp_chromedevtool_click",
                "fill": "mcp_chromedevtool_fill",
                "screenshot": "mcp_chromedevtool_take_screenshot",
                "lighthouse": "mcp_chromedevtool_lighthouse_audit",
                "console": "mcp_chromedevtool_list_console_messages",
                "network": "mcp_chromedevtool_list_network_requests",
                "script": "mcp_chromedevtool_evaluate_script",
                "info": None,
            }

            mcp_tool = action_map.get(action)
            tool_count = len(DEVTOOL_MCP_TOOLS)

            return {
                "status": "success",
                "agent": "devtool",
                "system": "devtool",
                "execution_path": f"devtool_bridge:{action}",
                "availability": "full" if status.chrome_available else "limited",
                "browser_mode": browser_mode,
                "browser_path": browser_path,
                "tool_count": tool_count,
                "categories": status.categories,
                "suggested_mcp_tool": mcp_tool,
                "output": {
                    "action": action,
                    "url": url,
                    "selector": selector,
                },
                "context": {
                    "action": action,
                    "url": url,
                    "selector": selector,
                },
                "note": (
                    f"DevTool+ ready with {tool_count} MCP tools via {browser_mode}. "
                    f"Use the suggested MCP tool or browse categories: {', '.join(status.categories)}"
                ),
                "warning": (
                    "Chrome is preferred; Edge fallback may not support every DevTools workflow"
                    if browser_mode == "edge_fallback"
                    else None
                ),
                "task_id": task.task_id,
            }

        except ImportError as e:
            logger.error(f"❌ DevTool+ bridge not available: {e}")
            return {
                "status": "failed",
                "agent": "devtool",
                "system": "devtool",
                "execution_path": "devtool_bridge:import",
                "error": f"DevTool+ bridge import failed: {e}",
                "task_id": task.task_id,
            }
        except Exception as e:
            logger.error(f"❌ DevTool+ routing failed: {e}")
            return {
                "status": "failed",
                "agent": "devtool",
                "system": "devtool",
                "execution_path": "devtool_bridge:error",
                "error": str(e),
                "task_id": task.task_id,
            }

    def _looks_like_gitkraken_task(self, task: OrchestrationTask) -> bool:
        operation = str(task.context.get("operation") or "").strip().lower()
        if operation in {"status", "commit", "push"}:
            return True

        content = task.content.lower()
        markers = (
            "git status",
            "repo status",
            "working tree",
            "commit",
            "stage",
            "push",
            "upstream",
            "origin/",
            "gitkraken",
            "branch",
            "remote",
        )
        return any(marker in content for marker in markers)

    def _infer_gitkraken_operation(self, task: OrchestrationTask) -> str:
        explicit = str(task.context.get("operation") or "").strip().lower()
        if explicit:
            return explicit

        content = task.content.lower()
        if any(marker in content for marker in ("push", "publish branch", "set-upstream")):
            return "push"
        if any(marker in content for marker in ("commit", "stage", "staged", "amend")):
            return "commit"
        return "status"

    def _extract_commit_message(self, content: str) -> str:
        patterns = (
            r"""message\s+["'](?P<msg>[^"']+)["']""",
            r"""commit(?:\s+with\s+message)?\s+["'](?P<msg>[^"']+)["']""",
        )
        for pattern in patterns:
            match = re.search(pattern, content, flags=re.IGNORECASE)
            if match:
                return str(match.group("msg")).strip()
        return ""

    def _build_gitkraken_parameters(
        self, task: OrchestrationTask, operation: str
    ) -> dict[str, Any]:
        context = task.context
        parameters: dict[str, Any] = {
            "repo_path": context.get("repo_path"),
        }

        if operation == "status":
            parameters["short"] = bool(context.get("short", True))
            parameters["porcelain"] = bool(context.get("porcelain", True))
            return parameters

        if operation == "commit":
            parameters["files"] = context.get("files")
            parameters["message"] = context.get("message") or self._extract_commit_message(
                task.content
            )
            parameters["amend"] = bool(context.get("amend", False))
            return parameters

        if operation == "push":
            branch_match = re.search(
                r"""branch\s+["']?(?P<branch>[\w./-]+)["']?""",
                task.content,
                flags=re.IGNORECASE,
            )
            remote_match = re.search(
                r"""remote\s+["']?(?P<remote>[\w./-]+)["']?""",
                task.content,
                flags=re.IGNORECASE,
            )
            parameters["branch"] = context.get("branch") or (
                branch_match.group("branch").strip() if branch_match else ""
            )
            parameters["remote"] = context.get("remote") or (
                remote_match.group("remote").strip() if remote_match else "origin"
            )
            parameters["force"] = bool(context.get("force", False))
            parameters["set_upstream"] = bool(context.get("set_upstream", True))
            return parameters

        return parameters

    async def _route_to_gitkraken(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to GitKraken MCP for git operations.

        GitKraken MCP provides multi-provider git operations:
        - Git operations (add, commit, push, pull, stash, branch)
        - GitLens features (blame, start work, code review)
        - Issue and PR management across GitHub/GitLab/Jira/Trello

        Context keys:
            operation: Git operation (commit, push, blame, pr_create, etc.)
            message: Commit message (for commit operations)
            branch: Target branch name
            provider: Force specific provider (github, gitlab, etc.)

        Example:
            >>> result = await router.route_task(
            ...     "review",
            ...     "Start code review workflow",
            ...     context={"operation": "start_review"},
            ...     target_system="gitkraken"
            ... )
        """
        logger.info(f"🐙 Routing to GitKraken MCP: {task.task_id}")

        try:
            from src.integrations.gitkraken_bridge import (GITKRAKEN_MCP_TOOLS,
                                                           GitKrakenBridge)

            bridge = GitKrakenBridge()
            status = bridge.probe()

            operation = self._infer_gitkraken_operation(task)

            # Map operations to MCP tools
            op_map = {
                "status": "mcp_gitkraken_git_status",
                "commit": "mcp_gitkraken_git_add_or_commit",
                "push": "mcp_gitkraken_git_push",
                "blame": "mcp_gitkraken_git_blame",
                "branch": "mcp_gitkraken_git_branch",
                "stash": "mcp_gitkraken_git_stash",
                "log": "mcp_gitkraken_git_log_or_diff",
                "start_work": "mcp_gitkraken_gitlens_start_work",
                "start_review": "mcp_gitkraken_gitlens_start_review",
                "pr_create": "mcp_gitkraken_pull_request_create",
                "pr_review": "mcp_gitkraken_pull_request_create_review",
            }

            mcp_tool = op_map.get(operation)

            if not status.available:
                return {
                    "status": "failed",
                    "agent": "gitkraken",
                    "system": "gitkraken",
                    "execution_path": f"gitkraken_bridge:{operation}",
                    "error": status.message or "GitKraken unavailable",
                    "task_id": task.task_id,
                    "mcp_server_url": getattr(status, "mcp_server_url", ""),
                }

            if operation in {"status", "commit", "push"}:
                parameters = self._build_gitkraken_parameters(task, operation)
                result = await to_thread(bridge.execute_git_operation, operation, parameters)
                return {
                    "status": str(result.get("status") or "failed"),
                    "agent": "gitkraken",
                    "system": "gitkraken",
                    "execution_path": f"gitkraken_bridge:{operation}",
                    "tool_count": len(GITKRAKEN_MCP_TOOLS),
                    "providers": status.providers_detected,
                    "gitlens_available": status.gitlens_available,
                    "operation": operation,
                    "mcp_tool": mcp_tool,
                    "mcp_server_url": getattr(status, "mcp_server_url", ""),
                    "output": result,
                    "task_id": task.task_id,
                }

            return {
                "status": "ready",
                "agent": "gitkraken",
                "system": "gitkraken",
                "execution_path": f"gitkraken_bridge:{operation}",
                "tool_count": len(GITKRAKEN_MCP_TOOLS),
                "providers": status.providers_detected,
                "gitlens_available": status.gitlens_available,
                "suggested_mcp_tool": mcp_tool,
                "output": {"operation": operation},
                "context": {"operation": operation},
                "task_id": task.task_id,
                "mcp_server_url": getattr(status, "mcp_server_url", ""),
            }

        except ImportError as e:
            logger.error(f"❌ GitKraken bridge not available: {e}")
            return {
                "status": "failed",
                "agent": "gitkraken",
                "system": "gitkraken",
                "execution_path": "gitkraken_bridge:import",
                "error": str(e),
                "task_id": task.task_id,
            }
        except Exception as e:
            logger.error(f"❌ GitKraken routing failed: {e}")
            return {
                "status": "failed",
                "agent": "gitkraken",
                "system": "gitkraken",
                "execution_path": "gitkraken_bridge:error",
                "error": str(e),
                "task_id": task.task_id,
            }

    async def _route_to_huggingface(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to HuggingFace MCP for ML model/dataset discovery.

        HuggingFace MCP provides:
        - Model search (by task, tags, author)
        - Dataset search
        - Paper search
        - Space search
        - Documentation access

        Context keys:
            search_type: Type of search (model, dataset, paper, space)
            query: Search query
            task_filter: Filter by ML task (text-generation, image-classification, etc.)

        Example:
            >>> result = await router.route_task(
            ...     "analyze",
            ...     "Find code generation models",
            ...     context={"search_type": "model", "task_filter": "text-generation"},
            ...     target_system="huggingface"
            ... )
        """
        logger.info(f"🤗 Routing to HuggingFace MCP: {task.task_id}")

        try:
            from src.integrations.huggingface_bridge import (
                HUGGINGFACE_MCP_TOOLS, HuggingFaceBridge)

            bridge = HuggingFaceBridge()
            status = bridge.probe()

            search_type = task.context.get("search_type", "model")

            search_map = {
                "model": "mcp_evalstate_hf-_model_search",
                "dataset": "mcp_evalstate_hf-_dataset_search",
                "paper": "mcp_evalstate_hf-_paper_search",
                "space": "mcp_evalstate_hf-_space_search",
                "docs": "mcp_evalstate_hf-_hf_doc_search",
            }

            mcp_tool = search_map.get(search_type)

            return {
                "status": "ready" if status.available else "degraded",
                "agent": "huggingface",
                "system": "huggingface",
                "execution_path": f"huggingface_bridge:{search_type}",
                "tool_count": len(HUGGINGFACE_MCP_TOOLS),
                "authenticated": status.authenticated,
                "username": status.username,
                "suggested_mcp_tool": mcp_tool,
                "output": {"search_type": search_type},
                "context": {"search_type": search_type},
                "task_id": task.task_id,
            }

        except ImportError as e:
            logger.error(f"❌ HuggingFace bridge not available: {e}")
            return {
                "status": "failed",
                "agent": "huggingface",
                "system": "huggingface",
                "execution_path": "huggingface_bridge:import",
                "error": str(e),
                "task_id": task.task_id,
            }
        except Exception as e:
            logger.error(f"❌ HuggingFace routing failed: {e}")
            return {
                "status": "failed",
                "agent": "huggingface",
                "system": "huggingface",
                "execution_path": "huggingface_bridge:error",
                "error": str(e),
                "task_id": task.task_id,
            }

    async def _route_to_dbclient(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to DBClient MCP for SQL database operations.

        DBClient MCP provides:
        - SQL query execution
        - Database listing
        - Table schema inspection

        Context keys:
            query: SQL query to execute
            database: Target database (default: nusyq_state)

        Example:
            >>> result = await router.route_task(
            ...     "analyze",
            ...     "Show recent tasks from state database",
            ...     context={"query": "SELECT * FROM tasks ORDER BY created_at DESC LIMIT 10"},
            ...     target_system="dbclient"
            ... )
        """
        logger.info(f"💾 Routing to DBClient MCP: {task.task_id}")

        try:
            from src.integrations.dbclient_bridge import (DBCLIENT_MCP_TOOLS,
                                                          DBClientBridge)

            bridge = DBClientBridge()
            status = bridge.probe()

            query = task.context.get("query")
            database = task.context.get("database", "nusyq_state")

            # Provide common queries if none specified
            common_queries = bridge.get_common_queries() if not query else []

            operation = "execute-query" if query else "get-tables"
            return {
                "status": "ready" if status.available else "degraded",
                "agent": "dbclient",
                "system": "dbclient",
                "execution_path": f"dbclient_bridge:{operation}",
                "tool_count": len(DBCLIENT_MCP_TOOLS),
                "state_db_available": status.nusyq_state_db is not None,
                "state_db_size_mb": (
                    (status.nusyq_state_db.size_bytes / (1024 * 1024))
                    if status.nusyq_state_db
                    else None
                ),
                "suggested_mcp_tool": "dbclient-execute-query" if query else "dbclient-get-tables",
                "output": {"query": query, "database": database},
                "context": {"query": query, "database": database},
                "common_queries": common_queries[:3] if common_queries else None,
                "task_id": task.task_id,
            }

        except ImportError as e:
            logger.error(f"❌ DBClient bridge not available: {e}")
            return {
                "status": "failed",
                "agent": "dbclient",
                "system": "dbclient",
                "execution_path": "dbclient_bridge:import",
                "error": str(e),
                "task_id": task.task_id,
            }
        except Exception as e:
            logger.error(f"❌ DBClient routing failed: {e}")
            return {
                "status": "failed",
                "agent": "dbclient",
                "system": "dbclient",
                "execution_path": "dbclient_bridge:error",
                "error": str(e),
                "task_id": task.task_id,
            }

    async def _route_to_neural_ml(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to Neural ML System (offline-capable consciousness-enhanced ML).

        The Neural ML System provides sklearn-backed ML with optional quantum/consciousness
        enhancements.  All inference runs locally — no external API required.

        Context keys:
            operation: "train", "predict", "analyze", or "status" (default: "status")
            model_type: ML model type for training (default: "consciousness_enhanced")
            data: Input data dict for training or prediction
            use_quantum: Enable quantum enhancement layer (default: True)

        Example:
            >>> result = await router.route_task(
            ...     "analyze",
            ...     "Analyze patterns in this dataset",
            ...     context={"operation": "analyze"},
            ...     target_system="neural_ml"
            ... )
        """
        logger.info(f"🧠 Routing to Neural ML System: {task.task_id}")

        try:
            from src.ml import (ConsciousnessEnhancedMLSystem,
                                NeuralQuantumBridge,
                                PatternConsciousnessAnalyzer,
                                QuantumMLProcessor)

            # Auto-detect operation from task_type when not explicitly set in context
            _default_op = {
                "analyze": "analyze",
                "train": "train",
                "predict": "predict",
                "optimize": "analyze",
                "review": "analyze",
            }.get(str(task.task_type or "").strip().lower(), "status")
            operation = task.context.get("operation", _default_op)

            if operation == "status":
                # Return capability summary without performing work
                return {
                    "status": "ready",
                    "agent": "neural_ml",
                    "system": "neural_ml",
                    "execution_path": "neural_ml:status",
                    "available_systems": [
                        "ConsciousnessEnhancedMLSystem",
                        "NeuralQuantumBridge",
                        "PatternConsciousnessAnalyzer",
                        "QuantumMLProcessor",
                    ],
                    "offline_capable": True,
                    "quantum_integration": True,
                    "operations": ["train", "predict", "analyze", "status"],
                    "output": {"operation": "status"},
                    "task_id": task.task_id,
                }

            if operation == "train":
                ml_system = ConsciousnessEnhancedMLSystem()
                model_type = task.context.get("model_type", "consciousness_enhanced")
                data = task.context.get("data", {})
                result = await ml_system.train_consciousness_enhanced_model(
                    model_type=model_type, training_data=data
                )
                return {
                    "status": "success",
                    "agent": "neural_ml",
                    "system": "neural_ml",
                    "execution_path": "neural_ml:train",
                    "operation": "train",
                    "output": result,
                    "result": result,
                    "task_id": task.task_id,
                }

            if operation == "predict":
                ml_system = ConsciousnessEnhancedMLSystem()
                data = task.context.get("data", {})
                use_quantum = task.context.get("use_quantum", True)
                model_name = str(task.context.get("model_name") or "pattern_recognizer")
                result = await ml_system.predict_with_consciousness(
                    model_name, input_data=data, consciousness_enhanced=use_quantum
                )
                return {
                    "status": "success",
                    "agent": "neural_ml",
                    "system": "neural_ml",
                    "execution_path": "neural_ml:predict",
                    "operation": "predict",
                    "output": result,
                    "result": result,
                    "task_id": task.task_id,
                }

            if operation == "analyze":
                analyzer = PatternConsciousnessAnalyzer()
                data = task.context.get("data", task.content)
                result = await analyzer.analyze_patterns_with_consciousness(data)
                return {
                    "status": "success",
                    "agent": "neural_ml",
                    "system": "neural_ml",
                    "execution_path": "neural_ml:analyze",
                    "operation": "analyze",
                    "output": result,
                    "result": result,
                    "task_id": task.task_id,
                }

            return {
                "status": "failed",
                "agent": "neural_ml",
                "system": "neural_ml",
                "execution_path": f"neural_ml:{operation}",
                "error": f"Unknown operation: {operation}. Use: train, predict, analyze, status",
                "task_id": task.task_id,
            }

        except ImportError as e:
            logger.error(f"❌ Neural ML system not available: {e}")
            return {
                "status": "failed",
                "agent": "neural_ml",
                "system": "neural_ml",
                "execution_path": "neural_ml:import",
                "error": str(e),
                "task_id": task.task_id,
            }
        except Exception as e:
            logger.error(f"❌ Neural ML routing failed: {e}")
            return {
                "status": "failed",
                "agent": "neural_ml",
                "system": "neural_ml",
                "execution_path": "neural_ml:error",
                "error": str(e),
                "task_id": task.task_id,
            }

    async def _route_to_continuous_optimizer(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to ContinuousOptimizationEngine (culture-ship + search-index cycles).

        Runs scheduled culture ship healing cycles and search index updates locally.
        All operations are offline-capable — no external API required.

        Context keys:
            operation: "run_cycle", "history", or "status" (default: "status")
            limit: Number of history entries to return (default: 10, for "history" only)

        Example:
            >>> result = await router.route_task(
            ...     "optimize",
            ...     "Run a healing optimization cycle",
            ...     context={"operation": "run_cycle"},
            ...     target_system="optimizer"
            ... )
        """
        logger.info(f"⚙️ Routing to ContinuousOptimizationEngine: {task.task_id}")

        try:
            from src.orchestration.continuous_optimization_engine import \
                ContinuousOptimizationEngine

            operation = task.context.get("operation", "status")

            if operation == "status":
                engine = ContinuousOptimizationEngine()
                history = engine.get_optimization_history(limit=1)
                last_cycle = history[0] if history else None
                return {
                    "status": "ready",
                    "system": "continuous_optimizer",
                    "agent": "optimizer",
                    "execution_path": "continuous_optimization_engine:status",
                    "output": {
                        "operations": ["run_cycle", "history", "status"],
                        "offline_capable": True,
                        "last_cycle": (
                            {
                                "timestamp": str(last_cycle.timestamp),
                                "health_improvement": last_cycle.health_improvement,
                                "duration_s": last_cycle.duration_seconds,
                            }
                            if last_cycle
                            else None
                        ),
                    },
                    "task_id": task.task_id,
                }

            if operation == "run_cycle":
                engine = ContinuousOptimizationEngine()
                cycle = engine.run_single_cycle()
                return {
                    "status": "success",
                    "system": "continuous_optimizer",
                    "agent": "optimizer",
                    "execution_path": "continuous_optimization_engine:run_cycle",
                    "output": {
                        "operation": "run_cycle",
                        "cycle": {
                            "timestamp": str(cycle.timestamp),
                            "health_improvement": cycle.health_improvement,
                            "duration_s": cycle.duration_seconds,
                            "healing_fixes_applied": cycle.healing_fixes_applied,
                            "search_files_updated": cycle.search_files_updated,
                        },
                    },
                    "task_id": task.task_id,
                }

            if operation == "history":
                engine = ContinuousOptimizationEngine()
                limit = int(task.context.get("limit", 10))
                history = engine.get_optimization_history(limit=limit)
                cycles = [
                    {
                        "timestamp": str(c.timestamp),
                        "health_improvement": c.health_improvement,
                        "duration_s": c.duration_seconds,
                    }
                    for c in history
                ]
                return {
                    "status": "success",
                    "system": "continuous_optimizer",
                    "agent": "optimizer",
                    "execution_path": "continuous_optimization_engine:history",
                    "output": {"operation": "history", "cycles": cycles, "count": len(history)},
                    "task_id": task.task_id,
                }

            return {
                "status": "failed",
                "system": "continuous_optimizer",
                "agent": "optimizer",
                "execution_path": "continuous_optimization_engine:unknown",
                "error": f"Unknown operation: {operation}. Use: run_cycle, history, status",
                "suggestion": "Set context['operation'] to one of: run_cycle, history, status",
                "task_id": task.task_id,
            }

        except ImportError as e:
            logger.error(f"❌ ContinuousOptimizationEngine not available: {e}")
            return {
                "status": "failed",
                "system": "continuous_optimizer",
                "agent": "optimizer",
                "error": str(e),
                "task_id": task.task_id,
            }
        except Exception as e:
            logger.error(f"❌ Optimizer routing failed: {e}")
            return {
                "status": "failed",
                "system": "continuous_optimizer",
                "agent": "optimizer",
                "error": str(e),
                "task_id": task.task_id,
            }

    async def _route_to_metaclaw(self, task: OrchestrationTask) -> dict[str, Any]:
        """Route task to MetaClaw (autonomous Web3 bounty hunting agent on Base chain).

        MetaClaw hunts on-chain bounties, completes missions, earns USDC rewards,
        and tracks reputation via Clawncher/Base infrastructure.  Requires Node.js
        + npm with the metaclaw-agent runtime installed in
        ``state/runtime/external/metaclaw-agent/``.

        Context keys:
            operation: "status" (default), "bounty", or "trace"
            timeout_s: Execution timeout in seconds (default: 30)

        Prompt keyword inference (no context key needed):
            "bounty", "hunt", "mission", "reward", "usdc" → operation="bounty"

        Example:
            >>> result = await router.route_task(
            ...     "observe",
            ...     "What is the current trace status?",
            ...     context={"operation": "status"},
            ...     target_system="metaclaw"
            ... )
        """
        logger.info(f"👁️ Routing to MetaClaw: {task.task_id}")

        runtime_dir = self.repo_root / "state" / "runtime" / "external" / "metaclaw-agent"
        # Infer operation from context key (explicit) or prompt keywords (fallback)
        _prompt_lower = task.content.lower()
        if "operation" in task.context:
            operation = task.context["operation"]
        elif any(kw in _prompt_lower for kw in ("bounty", "hunt", "mission", "reward", "usdc")):
            operation = "bounty"
        else:
            operation = "status"
        timeout_s = int(task.context.get("timeout_s", 30))

        # Check runtime presence
        if not runtime_dir.exists():
            logger.warning("⚠️ MetaClaw runtime not found — returning status stub")
            return {
                "status": "offline",
                "system": "metaclaw",
                "agent": "metaclaw",
                "execution_path": "metaclaw:not_installed",
                "output": {
                    "available": False,
                    "install_hint": f"Install MetaClaw agent to: {runtime_dir}",
                    "capabilities": ["trace_observability", "bounty_status_monitoring"],
                },
                "task_id": task.task_id,
            }

        # Status probe (no Node invocation needed)
        if operation == "status":
            node_ok = bool(shutil.which("node"))
            modules_ok = (runtime_dir / "node_modules").exists()
            return {
                "status": "ready" if (node_ok and modules_ok) else "degraded",
                "system": "metaclaw",
                "agent": "metaclaw",
                "execution_path": "metaclaw:status",
                "output": {
                    "available": True,
                    "path": str(runtime_dir),
                    "node_available": node_ok,
                    "node_modules_ready": modules_ok,
                    "operations": ["status", "trace", "bounty"],
                },
                "task_id": task.task_id,
            }

        # Execute via Node.js
        entry = runtime_dir / "index.js"
        if not entry.exists():
            entry = runtime_dir / "src" / "index.js"
        if not entry.exists():
            return {
                "status": "failed",
                "system": "metaclaw",
                "agent": "metaclaw",
                "execution_path": "metaclaw:no_entry",
                "error": "No index.js found in metaclaw-agent runtime",
                "task_id": task.task_id,
            }

        try:
            self._emit_terminal_event(
                "metaclaw",
                "metaclaw_start",
                f"metaclaw start operation={operation}",
                task_id=task.task_id,
                extra={"operation": operation},
            )
            cmd = ["node", str(entry), "--operation", operation, "--prompt", task.content[:1000]]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(runtime_dir),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
            output = stdout.decode("utf-8", errors="replace").strip()
            error_output = stderr.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0:
                return {
                    "status": "failed",
                    "system": "metaclaw",
                    "agent": "metaclaw",
                    "execution_path": "metaclaw:node",
                    "error": error_output[:500] or f"Exit code {proc.returncode}",
                    "task_id": task.task_id,
                }

            try:
                parsed = json.loads(output)
                return {
                    "status": "success",
                    "system": "metaclaw",
                    "agent": "metaclaw",
                    "execution_path": "metaclaw:node",
                    "output": parsed,
                    "result": parsed,
                    "operation": operation,
                    "task_id": task.task_id,
                }
            except json.JSONDecodeError:
                pass

            return {
                "status": "success",
                "system": "metaclaw",
                "agent": "metaclaw",
                "execution_path": "metaclaw:node",
                "output": output or "(empty output)",
                "result": output or "(empty output)",
                "operation": operation,
                "task_id": task.task_id,
            }

        except TimeoutError:
            return {
                "status": "failed",
                "system": "metaclaw",
                "agent": "metaclaw",
                "execution_path": "metaclaw:timeout",
                "error": f"Timed out after {timeout_s}s",
                "task_id": task.task_id,
            }
        except Exception as e:
            logger.error(f"❌ MetaClaw routing failed: {e}")
            return {
                "status": "failed",
                "system": "metaclaw",
                "agent": "metaclaw",
                "execution_path": "metaclaw:error",
                "error": str(e),
                "task_id": task.task_id,
            }


async def analyze_with_ai(
    description: str,
    context: dict[str, Any] | None = None,
    system: TargetSystem = "auto",
) -> dict[str, Any]:
    """Analyze code/data with AI system.

    Args:
        description: What to analyze
        context: File paths, preferences, etc.
        system: Preferred AI system or "auto"

    Returns:
        Analysis result
    """
    router = AgentTaskRouter()
    return await router.route_task("analyze", description, context, system)


async def generate_with_ai(
    description: str,
    context: dict[str, Any] | None = None,
    system: TargetSystem = "chatdev",
) -> dict[str, Any]:
    """Generate code/project with AI system.

    Args:
        description: What to generate
        context: Requirements, templates, etc.
        system: Preferred AI system (default: chatdev)

    Returns:
        Generation result
    """
    router = AgentTaskRouter()
    return await router.route_task("generate", description, context, system)


async def review_with_ai(
    description: str,
    context: dict[str, Any] | None = None,
    system: TargetSystem = "ollama",
) -> dict[str, Any]:
    """Review code with AI system.

    Args:
        description: What to review
        context: File paths, focus areas, etc.
        system: Preferred AI system (default: ollama)

    Returns:
        Review result
    """
    router = AgentTaskRouter()
    return await router.route_task("review", description, context, system)


async def debug_with_ai(
    description: str,
    context: dict[str, Any] | None = None,
    system: TargetSystem = "quantum_resolver",
) -> dict[str, Any]:
    """Debug issues with AI system.

    Args:
        description: Issue description
        context: Error logs, stack traces, etc.
        system: Preferred AI system (default: quantum_resolver)

    Returns:
        Debug result
    """
    router = AgentTaskRouter()
    return await router.route_task("debug", description, context, system)


async def create_project_with_factory(
    name: str,
    template: str = "default_game",
    description: str = "",
    ai_provider: str = "auto",
) -> dict[str, Any]:
    """Create a new project using the factory.

    Args:
        name: Project name
        template: Template to use (default_game, default_cli, default_library)
        description: Project description
        ai_provider: AI provider to use (auto, chatdev, ollama, claude, openai)

    Returns:
        Factory creation result with project details
    """
    router = AgentTaskRouter()
    return await router.route_task(
        "create_project",
        description or f"Create {template} project named {name}",
        {
            "project_name": name,
            "template": template,
            "ai_provider": ai_provider,
        },
        "factory",
    )


async def factory_health_with_ai(include_packaging: bool = True) -> dict[str, Any]:
    """Run factory health smoke probes through the agent router."""
    router = AgentTaskRouter()
    return await router.route_task(
        "factory_health",
        "Run factory smoke probes",
        {"include_packaging": include_packaging},
        "factory",
    )


async def factory_doctor_with_ai(
    strict_hooks: bool = False,
    include_examples: bool = True,
    include_health: bool = True,
    recent_limit: int = 25,
) -> dict[str, Any]:
    """Run fail-fast factory diagnostics through the agent router."""
    router = AgentTaskRouter()
    return await router.route_task(
        "factory_doctor",
        "Run factory doctor diagnostics",
        {
            "strict_hooks": strict_hooks,
            "include_examples": include_examples,
            "include_health": include_health,
            "recent_limit": recent_limit,
        },
        "factory",
    )


async def factory_doctor_fix_with_ai(
    strict_hooks: bool = False,
    include_examples: bool = True,
    include_health: bool = True,
    recent_limit: int = 25,
) -> dict[str, Any]:
    """Run doctor remediation actions through the agent router."""
    router = AgentTaskRouter()
    return await router.route_task(
        "factory_doctor_fix",
        "Run factory doctor remediation",
        {
            "strict_hooks": strict_hooks,
            "include_examples": include_examples,
            "include_health": include_health,
            "recent_limit": recent_limit,
        },
        "factory",
    )


async def factory_autopilot_with_ai(
    fix: bool = False,
    strict_hooks: bool = False,
    include_examples: bool = True,
    recent_limit: int = 25,
    paths: list[str] | None = None,
) -> dict[str, Any]:
    """Run factory autopilot loop through the agent router."""
    router = AgentTaskRouter()
    return await router.route_task(
        "factory_autopilot",
        "Run factory autopilot loop",
        {
            "fix": fix,
            "strict_hooks": strict_hooks,
            "include_examples": include_examples,
            "recent_limit": recent_limit,
            "paths": paths or [],
        },
        "factory",
    )


async def inspect_factory_examples_with_ai(
    paths: list[str] | None = None,
) -> dict[str, Any]:
    """Inspect reference game installs through the factory router surface."""
    router = AgentTaskRouter()
    return await router.route_task(
        "factory_inspect_examples",
        "Inspect reference game repositories for runtime patterns",
        {"paths": paths or []},
        "factory",
    )


# ============================================================================
# PHASE 3 GENERATOR CONVENIENCE FUNCTIONS
# ============================================================================


async def generate_graphql_api(
    description: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate GraphQL API schema, resolvers, and types.

    Args:
        description: API description (e.g., "User authentication API")
        context: Configuration dict with entities, relationships, output_path

    Returns:
        Generation result

    Example:
        >>> result = await generate_graphql_api(
        ...     "E-commerce catalog",
        ...     {"entities": ["Product", "Category"], "output_path": "src/graphql"}
        ... )
    """
    router = AgentTaskRouter()
    return await router.route_task("generate_graphql", description, context, "graphql")


async def generate_openapi_spec(
    description: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate OpenAPI/REST API specification.

    Args:
        description: API description (e.g., "Task management REST API")
        context: Configuration dict with endpoints, base_path, version

    Returns:
        Generation result

    Example:
        >>> result = await generate_openapi_spec(
        ...     "User management API",
        ...     {"endpoints": [{"path": "/users", "methods": ["GET", "POST"]}]}
        ... )
    """
    router = AgentTaskRouter()
    return await router.route_task("generate_openapi", description, context, "openapi")


async def generate_react_component(
    description: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate React component with styles and tests.

    Args:
        description: Component description (e.g., "User profile card")
        context: Configuration dict with component_name, props, output_path

    Returns:
        Generation result

    Example:
        >>> result = await generate_react_component(
        ...     "Product card",
        ...     {"component_name": "ProductCard", "props": {"name": "string"}}
        ... )
    """
    router = AgentTaskRouter()
    return await router.route_task("generate_component", description, context, "component")


async def generate_database_schema(
    description: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate database schema, migrations, and seeders.

    Args:
        description: Schema description (e.g., "E-commerce database")
        context: Configuration dict with tables, dialect, output_path

    Returns:
        Generation result

    Example:
        >>> result = await generate_database_schema(
        ...     "User auth database",
        ...     {"tables": [{"name": "users", "columns": [...]}], "dialect": "postgres"}
        ... )
    """
    router = AgentTaskRouter()
    return await router.route_task("generate_database", description, context, "database")


async def generate_universal_project(
    description: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate complete project with structure and configuration.

    Args:
        description: Project description (e.g., "Express API server")
        context: Configuration dict with project_type, language, framework

    Returns:
        Generation result

    Example:
        >>> result = await generate_universal_project(
        ...     "FastAPI microservice",
        ...     {"project_type": "api", "language": "python", "framework": "fastapi"}
        ... )
    """
    router = AgentTaskRouter()
    return await router.route_task("generate_project", description, context, "project")


# ============================================================================
# CLI FOR TESTING
# ============================================================================


async def main() -> None:
    """CLI entrypoint for manual testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Route tasks to AI systems")
    parser.add_argument("task_type", choices=["analyze", "generate", "review", "debug", "health"])
    parser.add_argument("--description", "-d", help="Task description")
    parser.add_argument("--system", "-s", default="auto", help="Target system")
    parser.add_argument("--file", "-f", help="File path for context")

    args = parser.parse_args()

    router = AgentTaskRouter()

    if args.task_type == "health":
        # health_check is now async
        health = await router.health_check()
        logger.info(json.dumps(health, indent=2))
    else:
        context = {"file": args.file} if args.file else {}
        result = await router.route_task(
            args.task_type,
            args.description or f"Test {args.task_type} task",
            context,
            args.system,
        )
        logger.info(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
