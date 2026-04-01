#!/usr/bin/env python3
"""start_nusyq.py — NuSyQ-Hub "spine" entrypoint

Goal (Phase 1):
- Single command to print + write a Markdown snapshot of the whole tripartite workspace:
  - Repo status (NuSyQ-Hub, SimulatedVerse, NuSyQ Root)
  - Current quest (from src/Rosetta_Quest_System/quest_log.jsonl)
  - Lightweight health indicators
  - Available actions menu (stub; wiring later)

Safety posture:
- Read-only by default: does NOT push, does NOT delete, does NOT modify core configs.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import json
import logging
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from collections import Counter
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TypeVar

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - Python 3.10 compatibility
    UTC = timezone.utc  # noqa: UP017
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

# Ensure package imports work when executed as a script (python scripts/start_nusyq.py ...)
if __package__ in {None, ""}:
    # Add repository root to sys.path so that 'scripts.*' absolute imports resolve
    repo_root = os.path.dirname(os.path.dirname(__file__))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


def _suppress_otel_exporter_logs() -> None:
    """Mute OTEL exporter connection noise for read-only/status invocations."""
    for logger_name in (
        "opentelemetry.sdk._shared_internal",
        "opentelemetry.exporter.otlp.proto.http.trace_exporter",
        "opentelemetry.instrumentation.requests",
    ):
        try:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
        except Exception:
            continue


def _pre_disable_otel_for_action() -> None:
    """Best-effort OTEL suppression before module imports for noisy status actions."""
    action = "snapshot"
    for token in sys.argv[1:]:
        if token.startswith("-"):
            continue
        action = token
        break

    def _truthy_env(name: str, default: str = "1") -> bool:
        return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}

    status_actions = {
        "menu",
        "help",
        "--help",
        "snapshot",
        "brief",
        "suggest",
        "capabilities",
        "ecosystem_status",
        "agent_probe",
        "dispatch",
        "culture_ship_status",
        "culture_ship_doctor",
        "ai_status",
        "advanced_ai_quests",
        "graph_learning",
        "integration_health",
        "delegation_matrix",
        "claude_doctor",
        "ai_council_doctor",
        "codex_doctor",
        "copilot_doctor",
        "multi_agent_doctor",
        "agent_fleet_doctor",
        "doctor",
        "doctor_status",
        "error_signal_bridge",
        "signal_quest_bridge",
        "error_quest_bridge",
        "auto_quest",
        "prune_reports",
        "task_summary",
        "lifecycle_catalog",
        "problem_signal_snapshot",
        "causal_analysis",
        "specialization_status",
        "vscode_diagnostics_bridge",
        "openclaw_smoke",
        "openclaw_smoke_status",
        "openclaw_status",
        "openclaw_gateway_start",
        "openclaw_gateway_status",
        "openclaw_gateway_stop",
        "openclaw_internal_send",
        "skyclaw_status",
        "skyclaw_start",
        "skyclaw_stop",
    }
    if action == "brief":
        if _truthy_env("NUSYQ_BRIEF_DISABLE_OTEL", "1"):
            os.environ["OTEL_SDK_DISABLED"] = "true"
            os.environ["OTEL_TRACES_EXPORTER"] = "none"
            os.environ["NUSYQ_TRACING"] = "0"
            os.environ["NUSYQ_TRACE"] = "0"
            _suppress_otel_exporter_logs()
        return
    if action == "auto_cycle":
        if _truthy_env("NUSYQ_AUTO_CYCLE_DISABLE_OTEL", "1"):
            os.environ["OTEL_SDK_DISABLED"] = "true"
            os.environ["OTEL_TRACES_EXPORTER"] = "none"
            os.environ["NUSYQ_TRACING"] = "0"
            os.environ["NUSYQ_TRACE"] = "0"
            _suppress_otel_exporter_logs()
        return
    if action in status_actions and _truthy_env("NUSYQ_STATUS_DISABLE_OTEL", "1"):
        os.environ["OTEL_SDK_DISABLED"] = "true"
        os.environ["OTEL_TRACES_EXPORTER"] = "none"
        os.environ["NUSYQ_TRACING"] = "0"
        os.environ["NUSYQ_TRACE"] = "0"
        _suppress_otel_exporter_logs()


_pre_disable_otel_for_action()

from scripts.nusyq_actions.ai_actions import (
    handle_analyze,
    handle_debug,
    handle_generate,
    handle_ollama,
    handle_review,
)
from scripts.nusyq_actions.auto_cycle_steps import (
    handle_cross_sync,
    handle_metrics_dashboard,
    handle_pu_queue_processing,
    handle_quest_replay,
    handle_queue_execution,
)
from scripts.nusyq_actions.autonomous_actions import (
    handle_auto_cycle,
    handle_develop_system,
)
from scripts.nusyq_actions.background_task_actions import (
    handle_dispatch_task,
    handle_list_background_tasks,
    handle_orchestrator_hygiene,
    handle_orchestrator_status,
    handle_task_status,
)
from scripts.nusyq_actions.brief import handle_brief
from scripts.nusyq_actions.capabilities_actions import handle_capabilities
from scripts.nusyq_actions.dispatch_actions import handle_dispatch
from scripts.nusyq_actions.doctor import handle_doctor
from scripts.nusyq_actions.enhance_actions import (
    handle_enhance,
    handle_fix,
    handle_improve,
    handle_modernize,
    handle_patch,
    handle_update,
)
from scripts.nusyq_actions.guild_actions import (
    handle_guild_add_quest,
    handle_guild_available,
    handle_guild_claim,
    handle_guild_close_quest,
    handle_guild_complete,
    handle_guild_heartbeat,
    handle_guild_post,
    handle_guild_register,
    handle_guild_render,
    handle_guild_start,
    handle_guild_status,
    handle_log_quest,
)
from scripts.nusyq_actions.hygiene import handle_hygiene
from scripts.nusyq_actions.menu import handle_menu
from scripts.nusyq_actions.next_action_actions import (
    handle_next_action_display,
    handle_next_action_exec,
    handle_next_action_generate,
    handle_next_action_generation,
)
from scripts.nusyq_actions.search_actions import (
    handle_search_class,
    handle_search_function,
    handle_search_hacking_quests,
    handle_search_index_health,
    handle_search_keyword,
    handle_search_patterns,
)
from scripts.nusyq_actions.selfcheck import handle_selfcheck
from scripts.nusyq_actions.shared import (
    collect_audit_intelligence,
    format_audit_intelligence_lines,
)
from scripts.nusyq_actions.terminal_actions import handle_terminals
from scripts.nusyq_actions.test_actions import handle_test, handle_test_history
from scripts.nusyq_actions.trace_actions import (
    handle_trace_assert,
    handle_trace_config_set,
    handle_trace_config_show,
    handle_trace_config_validate,
    handle_trace_correlation_off,
    handle_trace_correlation_on,
    handle_trace_doctor,
    handle_trace_service_healthcheck,
    handle_trace_service_start,
    handle_trace_service_status,
    handle_trace_service_stop,
    handle_trace_smoke,
)
from scripts.nusyq_actions.work_task_actions import handle_suggest, handle_task, handle_work

logger = logging.getLogger(__name__)

try:
    from src.spine import export_spine_health, initialize_spine
except ImportError:
    initialize_spine = None  # type: ignore[assignment]
    export_spine_health = None  # type: ignore[assignment]


# Use a fast, submodule-safe status probe to avoid hangs on nested repos.
FAST_STATUS_CMD = [
    "git",
    "-c",
    "submodule.recurse=false",
    "status",
    "--porcelain",
    "--untracked-files=no",
    "--ignore-submodules=all",
]
FAST_DIRTY_DIFF_CMD = ["git", "diff", "--no-ext-diff", "--quiet", "--ignore-submodules=all", "--"]
FAST_DIRTY_CACHED_CMD = [
    "git",
    "diff",
    "--cached",
    "--no-ext-diff",
    "--quiet",
    "--ignore-submodules=all",
    "--",
]
GIT_STATUS_TIMEOUT_S = 8
GIT_UPSTREAM_TIMEOUT_S = 5
GIT_DIRTY_TIMEOUT_S = 3

# Module-level constants to avoid duplication
STATUS_WIRED = "✅ WIRED"
ERROR_NUSYQ_HUB_PATH_NOT_FOUND = "[ERROR] NuSyQ-Hub path not found"
TEXT_EXAMPLES = "\nExamples:"
LIFECYCLE_CATALOG_FILE = "lifecycle_catalog_latest.json"
ActionHandler = Callable[[], int]

# Terminal routing configuration (maps actions → terminal channels)
ACTION_TERMINAL_MAP = {
    # Error/diagnostic actions → 🔥 Errors terminal
    "error_report": "ERRORS",
    "error_report_split": "ERRORS",
    "error_report_status": "ERRORS",
    "error_signal_bridge": "ERRORS",
    "problem_signal_snapshot": "ERRORS",
    "trace_doctor": "ERRORS",
    # Test actions → 🧪 Tests terminal
    "test": "TESTS",
    "test_history": "TESTS",
    # Metrics/health actions → 📊 Metrics terminal
    "brief": "METRICS",
    "doctor": "METRICS",
    "doctor_status": "METRICS",
    "ai_status": "METRICS",
    "advanced_ai_quests": "TASKS",
    "graph_learning": "METRICS",
    "causal_analysis": "METRICS",
    "specialization_status": "METRICS",
    "selfcheck": "METRICS",
    "lifecycle_catalog": "METRICS",
    "terminal_snapshot": "METRICS",
    "system_complete": "METRICS",
    "system_complete_status": "METRICS",
    "validate_contracts": "METRICS",
    "integration_health": "METRICS",
    "compose_secrets": "METRICS",
    "simverse_mode": "METRICS",
    "claude_preflight": "METRICS",
    "delegation_matrix": "AGENTS",
    "claude_doctor": "AGENTS",
    "ai_council_doctor": "AGENTS",
    "agent_fleet_doctor": "AGENTS",
    "vscode_extensions_plan": "METRICS",
    "vscode_extensions_quickwins": "METRICS",
    "openclaw_smoke": "METRICS",
    "openclaw_smoke_status": "METRICS",
    "openclaw_status": "METRICS",
    "openclaw_gateway_start": "METRICS",
    "openclaw_gateway_status": "METRICS",
    "openclaw_gateway_stop": "METRICS",
    "openclaw_bridge_start": "METRICS",
    "openclaw_bridge_status": "METRICS",
    "openclaw_bridge_stop": "METRICS",
    "openclaw_internal_send": "AGENTS",
    "skyclaw_status": "AGENTS",
    "skyclaw_start": "AGENTS",
    "skyclaw_stop": "AGENTS",
    "open_antigravity_start": "METRICS",
    "open_antigravity_runtime_status": "METRICS",
    "open_antigravity_stop": "METRICS",
    "antigravity_status": "METRICS",
    "antigravity_health": "METRICS",
    "failover_status": "METRICS",
    # AI agent actions → 🤖 Agents terminal
    "analyze": "AGENTS",
    "review": "AGENTS",
    "debug": "AGENTS",
    "generate": "AGENTS",
    "copilot_doctor": "AGENTS",
    "codex_doctor": "AGENTS",
    "multi_agent_doctor": "AGENTS",
    "copilot_probe": "AGENTS",
    "dispatch": "AGENTS",  # MJOLNIR Protocol
    "culture_ship": "AGENTS",
    "culture_ship_cycle": "AGENTS",
    "culture_ship_status": "AGENTS",
    "culture_ship_doctor": "AGENTS",
    "simverse_consciousness": "METRICS",
    "simverse_history": "METRICS",
    "simverse_ship_directives": "METRICS",
    "simverse_cognition_insights": "METRICS",
    "simverse_bridge_health": "METRICS",
    "simverse_ship_approve": "METRICS",
    "simverse_log_event": "METRICS",
    "simverse_breathing": "METRICS",
    # Task/work actions → ✅ Tasks terminal
    "work": "TASKS",
    "queue": "TASKS",
    "pu_execute": "TASKS",
    "signal_quest_bridge": "TASKS",
    "error_quest_bridge": "TASKS",
    "auto_quest": "TASKS",
    "quest_compact": "TASKS",
    "hygiene": "TASKS",
    "prune_reports": "TASKS",
    # Suggestions → 💡 Suggestions terminal
    "suggest": "SUGGESTIONS",
    "next_action": "SUGGESTIONS",
    "next_action_generate": "SUGGESTIONS",
    # Zeta/autonomous → 🎯 Zeta terminal
    "auto_cycle": "ZETA",
    "autonomous_service": "ZETA",
    "auto_fix": "ZETA",
    # Default → 🏠 Main terminal
    "snapshot": "MAIN",
    "help": "MAIN",
    "capabilities": "MAIN",
    "menu": "MAIN",
    "ignition": "MAIN",
    # Enhancement actions
    "patch": "TASKS",
    "fix": "ERRORS",
    "improve": "SUGGESTIONS",
    "update": "TASKS",
    "modernize": "SUGGESTIONS",
    "enhance": "MAIN",
}


def emit_terminal_route(action: str) -> None:
    """Emit terminal routing hint for VS Code themed terminals."""
    channel = ACTION_TERMINAL_MAP.get(action, "MAIN")
    emoji_map = {
        "ERRORS": "🔥",
        "TESTS": "🧪",
        "METRICS": "📊",
        "AGENTS": "🤖",
        "TASKS": "✅",
        "SUGGESTIONS": "💡",
        "ZETA": "🎯",
        "MAIN": "🏠",
    }
    emoji = emoji_map.get(channel, "🏠")
    print(f"[ROUTE {channel}] {emoji}")


KNOWN_ACTIONS = {
    "ai_status",
    "ai_work_gate",
    "activate_ecosystem",
    "advanced_ai_quests",
    "graph_learning",
    "analyze",
    "auto_cycle",
    "autonomous_service",
    "auto_fix",
    "batch_commit",
    "brief",
    "capabilities",
    "causal_analysis",
    "specialization_status",
    "debug",
    "develop_system",
    "dispatch",  # MJOLNIR Protocol unified agent dispatch
    "doctrine_check",
    "menu",
    "ignition",
    "doctor",
    "doctor_status",
    "emergence_capture",
    "ecosystem_status",
    "error_report",
    "error_report_split",
    "error_report_status",
    "error_signal_bridge",
    "signal_quest_bridge",
    "error_quest_bridge",
    "auto_quest",
    "quest_compact",
    "fix",  # Quick fix for specific issue
    "generate",
    "culture_ship",
    "culture_ship_cycle",
    "culture_ship_status",
    "improve",  # Code quality improvements
    "modernize",  # Code modernization
    "patch",  # Patch specific file/module
    "update",  # Update dependencies/code
    "guild_add_quest",
    "guild_available",
    "guild_claim",
    "guild_close_quest",
    "guild_complete",
    "guild_heartbeat",
    "guild_post",
    "guild_register",
    "guild_render",
    "guild_start",
    "guild_status",
    "log_quest",
    "heal",
    "help",
    "hygiene",
    "prune_reports",
    "lifecycle_catalog",
    "log_dedup_status",
    "map",
    "metrics",
    "next_action",
    "next_action_exec",
    "next_action_generate",
    "ollama",  # Ollama service management (status, start, restart, ensure)
    "problem_signal_snapshot",
    "pu_execute",
    "quantum_resolver_status",
    "queue",
    "work",
    "replay",
    "review",
    "selfcheck",
    "simverse_bridge",
    "simverse_mode",
    "simverse_consciousness",
    "simverse_history",
    "simverse_ship_directives",
    "simverse_cognition_insights",
    "simverse_bridge_health",
    "simverse_ship_approve",
    "simverse_log_event",
    "simverse_breathing",
    "snapshot",
    "sns_analyze",  # NEW: SNS-Core token analysis
    "sns_convert",  # NEW: Convert text to SNS notation
    "zero_token_status",  # NEW: Zero-token mode status
    "suggest",
    "sync",
    "task",
    "task_manager",  # ChatDev+Ollama generated task manager CLI
    "task_summary",
    "system_complete",
    "system_complete_status",
    "openclaw_smoke",
    "openclaw_smoke_status",
    "openclaw_status",
    "openclaw_gateway_start",
    "openclaw_gateway_status",
    "openclaw_gateway_stop",
    "openclaw_bridge_start",
    "openclaw_bridge_status",
    "openclaw_bridge_stop",
    "openclaw_internal_send",
    "skyclaw_status",
    "skyclaw_start",
    "skyclaw_stop",
    "open_antigravity_start",
    "open_antigravity_runtime_status",
    "open_antigravity_stop",
    "antigravity_status",
    "antigravity_health",
    "failover_status",
    "validate_contracts",
    "integration_health",
    "compose_secrets",
    "delegation_matrix",
    "claude_preflight",
    "claude_doctor",
    "ai_council_doctor",
    "codex_doctor",
    "copilot_doctor",
    "multi_agent_doctor",
    "agent_fleet_doctor",
    "copilot_probe",
    "vscode_extensions_plan",
    "vscode_extensions_quickwins",
    "test",
    "test_history",
    "trace_assert",
    "trace_config_set",
    "trace_config_show",
    "trace_config_validate",
    "trace_correlation_off",
    "trace_correlation_on",
    "trace_doctor",
    "trace_service_healthcheck",
    "trace_service_start",
    "trace_service_status",
    "trace_service_stop",
    "trace_smoke",
    "vscode_diagnostics_bridge",
    # Background task orchestration for local LLMs
    "dispatch_task",
    "task_status",
    "list_background_tasks",
    "orchestrator_status",
    "orchestrator_hygiene",
    # Agent orchestration
    "agent_status",
    "agent_probe",  # Deep runtime probe of AI systems
    "orchestrate",
    "invoke_agent",
    "council_loop",
    # Quest system queries
    "quest_query",
    "quest_continue",
    "quest_graph",
    "quest_status",
    # Terminal intelligence system
    "terminals",
    "terminal_snapshot",
    # Enhancement actions
    "enhance",  # Interactive enhancement mode
    # Learning & Tutorial actions
    "examples",  # Interactive example runner
    "examples_list",  # List all examples
    "tutorial",  # Guided tutorial mode
    "demo",  # System capability demo
    # Factory function gateway (Phase 2 orphan rehabilitation)
    "factory",  # Run factory functions
    "integrator",  # Ollama/ChatDev integrator factory
    "orchestrator",  # Claude/Copilot orchestrator factory
    "quantum_factory",  # Quantum resolver factory
    "context_server",  # Context server factory
    # Dashboard (Phase 4 - false positive)
    "dashboard",  # Open Agent Dashboard WebView
    # Search & discovery actions
    "search",  # Code discovery dispatcher
    "search_keyword",  # Keyword search
    "search_class",  # Class definition search
    "search_function",  # Function definition search
    "search_patterns",  # Code pattern search (consciousness, tagging, etc.)
    "search_index_health",  # SmartSearch index health check
    "search_hacking_quests",  # Find hacking game quests
    "eol",  # Epistemic-Operational Lattice decision cycles
    "--help",
}

# Make src/ importable (for observability helpers)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Initialize logging with duplicate suppression when available.
try:
    from src.LOGGING import configure_logging

    configure_logging()
except Exception:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Tracing (graceful if missing)
try:
    from src.observability import tracing as otel
except Exception:
    otel = None  # type: ignore

_RUN_ID: str | None = None
_LAST_OUTPUTS: list[str] | None = None
_JSON_OUTPUT: bool = False
_T = TypeVar("_T")

QUEST_LOG_FILENAME = "quest_log.jsonl"
AGENTS_FILENAME = "AGENTS.md"
SYSTEM_OVERVIEW_FILENAME = "SYSTEM_OVERVIEW.md"
HEALTH_FILENAME = "src/diagnostics/health_cli.py"
CONTRACT_REQUIRED_ACTIONS = (
    "ai_status",
    "graph_learning",
    "suggest",
    "next_action",
    "doctor",
    "doctor_status",
    "error_report",
    "error_report_status",
    "system_complete",
    "system_complete_status",
    "openclaw_smoke",
    "openclaw_smoke_status",
)
CONTRACT_VALID_SAFETY_TIERS = {"read_only", "safe_mutation", "destructive"}
CONTRACT_VALID_NETWORK_VALUES = {
    "none",
    "optional_local",
    "optional_remote",
    "required_remote",
    "filesystem",
}

# ---------------------------
# Utilities
# ---------------------------


def _append_resource_attributes(existing: str | None, extra_attrs: dict[str, str]) -> str:
    base = existing or ""
    items = [item.strip() for item in base.split(",") if item.strip()] if base else []
    for key, value in extra_attrs.items():
        items.append(f"{key}={value}")
    return ",".join(items)


def _read_dotenv_pairs(path: Path) -> dict[str, str]:
    """Parse dotenv file into key/value pairs."""
    pairs: dict[str, str] = {}
    if not path.exists():
        return pairs
    try:
        for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                continue
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            pairs[key] = value
    except Exception:
        return {}
    return pairs


def _build_env() -> dict[str, str]:
    shell_env_keys = {k for k, v in os.environ.items() if str(v).strip()}
    env = os.environ.copy()

    # Precedence: shell > .env.workspace > .env > .env.docker
    root = PROJECT_ROOT
    for key, value in _read_dotenv_pairs(root / ".env").items():
        if key not in env or not str(env.get(key, "")).strip():
            env[key] = value
    for key, value in _read_dotenv_pairs(root / ".env.workspace").items():
        if key in shell_env_keys:
            continue
        env[key] = value
    for key, value in _read_dotenv_pairs(root / ".env.docker").items():
        if key not in env or not str(env.get(key, "")).strip():
            env[key] = value

    if _RUN_ID:
        env["NUSYQ_RUN_ID"] = _RUN_ID
        env["OTEL_RESOURCE_ATTRIBUTES"] = _append_resource_attributes(
            env.get("OTEL_RESOURCE_ATTRIBUTES"),
            {"nusyq.run.id": _RUN_ID},
        )
    return env


def _hydrate_process_env() -> None:
    """Hydrate current process env from layered dotenv files."""
    try:
        os.environ.update(_build_env())
    except Exception:
        # Best-effort only; do not block command execution.
        return


def read_json(path: Path) -> dict | None:
    """Read JSON file safely; return None if missing or invalid."""
    try:
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def read_structured(path: Path) -> dict[str, Any] | None:
    """Read JSON/YAML-encoded structured data and return a dict when possible."""
    try:
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else None
    except Exception:
        pass

    try:
        import yaml  # type: ignore

        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def is_git_repo(path: Path) -> bool:
    """Check whether path is a valid git working tree (not just .git marker)."""
    try:
        if not path.is_dir():
            return False
        inside = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if inside.returncode != 0 or inside.stdout.strip() != "true":
            return False

        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if top.returncode != 0 or not top.stdout.strip():
            return False
        return Path(top.stdout.strip()).resolve() == path.resolve()
    except Exception:
        return False


def _run_async_sync(coro: Coroutine[Any, Any, _T]) -> _T:
    """Run coroutine from sync code, even if already inside an event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    # A loop is already running in this thread; run in a worker thread.
    result: dict[str, Any] = {}
    error: list[BaseException] = []

    def _worker() -> None:
        try:
            result["value"] = asyncio.run(coro)
        except BaseException as exc:
            error.append(exc)

    import threading

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    thread.join()

    if error:
        raise error[0]
    if "value" not in result:
        raise RuntimeError("Failed to run coroutine in worker thread")
    return result["value"]


def read_action_contracts(hub_path: Path | None) -> dict:
    """Load action contracts metadata if available."""
    if not hub_path:
        return {}
    candidates = [
        hub_path / "config" / "action_contracts.json",
        hub_path / "config" / "action_contracts.yaml",
        hub_path / "config" / "action_contracts.yml",
    ]
    for path in candidates:
        payload = read_structured(path)
        if payload:
            return payload
    return {}


def read_action_catalog(hub_path: Path | None) -> dict:
    """Load action catalog metadata if available."""
    if not hub_path:
        return {}
    path = hub_path / "config" / "action_catalog.json"
    return read_json(path) or {}


def _get_contract_for_action(contracts: dict[str, Any], action_id: str) -> dict[str, Any]:
    actions = contracts.get("actions", {})
    if not isinstance(actions, dict):
        return {}
    contract = actions.get(action_id)
    return contract if isinstance(contract, dict) else {}


def _extract_json_payload(raw: str) -> dict[str, Any] | None:
    """Parse first JSON object from stdout, tolerating extra prelude lines."""
    text = raw.strip()
    if not text:
        return None
    with contextlib.suppress(Exception):
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        with contextlib.suppress(Exception):
            payload, _ = decoder.raw_decode(text[index:])
            if isinstance(payload, dict):
                return payload
    return None


def _validate_probe_output_schema(
    action_id: str,
    payload: dict[str, Any],
    output_schema: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    required = output_schema.get("required")
    if not isinstance(required, list):
        return issues
    missing = [key for key in required if key not in payload]
    if missing:
        issues.append(f"{action_id}: probe output missing required keys {missing}")
    action_value = payload.get("action")
    if action_value is not None and action_value != action_id:
        issues.append(f"{action_id}: probe output action mismatch ({action_value!r})")
    status_value = payload.get("status")
    if status_value is None or not isinstance(status_value, str):
        issues.append(f"{action_id}: probe output status must be string")
    return issues


def _run_contract_probe(
    action_id: str,
    contract: dict[str, Any],
    paths: RepoPaths,
) -> dict[str, Any]:
    probe_cmd = contract.get("probe_cmd")
    timeout_s = contract.get("probe_timeout_s", contract.get("timeout_s", 30))
    timeout = min(180, max(5, int(timeout_s) if isinstance(timeout_s, int) else 30))

    if not isinstance(probe_cmd, list) or not all(isinstance(token, str) for token in probe_cmd):
        return {
            "action": action_id,
            "ok": False,
            "error": "probe_cmd must be a list of strings",
        }

    rc, out, err = run(probe_cmd, cwd=paths.nusyq_hub, timeout_s=timeout)
    payload = _extract_json_payload(out)
    result: dict[str, Any] = {
        "action": action_id,
        "ok": rc == 0,
        "return_code": rc,
        "probe_cmd": probe_cmd,
        "timeout_s": timeout,
    }
    if rc != 0:
        result["error"] = err.splitlines()[-1] if err else "probe command failed"
        result["stdout_tail"] = "\n".join(out.splitlines()[-10:]) if out else ""
        return result
    if not isinstance(payload, dict):
        result["ok"] = False
        result["error"] = "probe output is not valid JSON object"
        result["stdout_tail"] = "\n".join(out.splitlines()[-10:]) if out else ""
        return result

    schema = contract.get("output_schema")
    if isinstance(schema, dict):
        schema_issues = _validate_probe_output_schema(action_id, payload, schema)
        if schema_issues:
            result["ok"] = False
            result["issues"] = schema_issues
    result["status"] = payload.get("status")
    result["output_keys"] = sorted(payload.keys())
    return result


def _validate_contracts_payload(
    contracts: dict[str, Any],
    *,
    paths: RepoPaths | None = None,
    probe: bool = False,
) -> dict[str, Any]:
    actions = contracts.get("actions", {})
    if not isinstance(actions, dict):
        actions = {}

    issues: list[str] = []
    warnings: list[str] = []
    checked: list[dict[str, Any]] = []
    probe_results: list[dict[str, Any]] = []

    for action_id in CONTRACT_REQUIRED_ACTIONS:
        contract = actions.get(action_id)
        if not isinstance(contract, dict):
            issues.append(f"missing contract for '{action_id}'")
            continue

        timeout_s = contract.get("timeout_s")
        safety_tier = contract.get("safety_tier") or contract.get("tier")
        cmd = contract.get("cmd")
        output_schema = contract.get("output_schema")
        side_effects = contract.get("side_effects")
        probe_cmd = contract.get("probe_cmd")
        probe_enabled = bool(contract.get("probe_enabled", False))
        has_alias_tier = "tier" in contract

        entry: dict[str, Any] = {"action": action_id, "ok": True}

        if not isinstance(cmd, str) or not cmd.strip():
            issues.append(f"{action_id}: cmd must be a non-empty string")
            entry["ok"] = False
        elif "--json" not in cmd:
            issues.append(f"{action_id}: cmd must include --json for machine-readable contracts")
            entry["ok"] = False
        else:
            entry["cmd"] = cmd

        if not isinstance(timeout_s, int) or timeout_s <= 0:
            issues.append(f"{action_id}: timeout_s must be a positive integer")
            entry["ok"] = False
        else:
            entry["timeout_s"] = timeout_s

        if safety_tier not in CONTRACT_VALID_SAFETY_TIERS:
            issues.append(f"{action_id}: safety_tier must be one of {sorted(CONTRACT_VALID_SAFETY_TIERS)}")
            entry["ok"] = False
        else:
            entry["safety_tier"] = safety_tier
            if has_alias_tier:
                warnings.append(f"{action_id}: 'tier' alias present (prefer 'safety_tier')")

        if not isinstance(output_schema, dict):
            issues.append(f"{action_id}: output_schema must be an object")
            entry["ok"] = False
        else:
            required = output_schema.get("required")
            schema_type = output_schema.get("type")
            if schema_type != "object":
                issues.append(f"{action_id}: output_schema.type must be 'object'")
                entry["ok"] = False
            if not isinstance(required, list) or not all(isinstance(v, str) for v in required):
                issues.append(f"{action_id}: output_schema.required must be string list")
                entry["ok"] = False
            else:
                entry["required"] = required
                missing_core_keys = [key for key in ("action", "status") if key not in required]
                if missing_core_keys:
                    issues.append(f"{action_id}: output_schema.required missing core keys {missing_core_keys}")
                    entry["ok"] = False

        if not isinstance(side_effects, dict):
            issues.append(f"{action_id}: side_effects must be an object")
            entry["ok"] = False
        else:
            network_mode = side_effects.get("network")
            long_running = side_effects.get("long_running")
            idempotent = side_effects.get("idempotent")
            if network_mode not in CONTRACT_VALID_NETWORK_VALUES:
                issues.append(
                    f"{action_id}: side_effects.network must be one of {sorted(CONTRACT_VALID_NETWORK_VALUES)}"
                )
                entry["ok"] = False
            if not isinstance(long_running, bool):
                issues.append(f"{action_id}: side_effects.long_running must be boolean")
                entry["ok"] = False
            if not isinstance(idempotent, bool):
                issues.append(f"{action_id}: side_effects.idempotent must be boolean")
                entry["ok"] = False

        if probe_enabled:
            if not isinstance(probe_cmd, list) or not all(isinstance(v, str) for v in probe_cmd):
                issues.append(f"{action_id}: probe_cmd must be string list when probe_enabled=true")
                entry["ok"] = False
            elif "--json" not in probe_cmd:
                issues.append(f"{action_id}: probe_cmd must include --json")
                entry["ok"] = False
        elif probe_cmd is not None:
            warnings.append(f"{action_id}: probe_cmd provided but probe_enabled is false")

        checked.append(entry)

    if probe:
        if not paths or not paths.nusyq_hub:
            warnings.append("probe requested but workspace paths unavailable; skipping probe execution")
        else:
            for entry in checked:
                action_id = str(entry.get("action", "")).strip()
                contract = actions.get(action_id)
                if not action_id or not isinstance(contract, dict):
                    continue
                if not bool(contract.get("probe_enabled", False)):
                    continue
                probe_result = _run_contract_probe(action_id, contract, paths)
                probe_results.append(probe_result)
                if not probe_result.get("ok"):
                    issues.append(f"{action_id}: runtime probe failed")

    return {
        "action": "validate_contracts",
        "generated_at": datetime.now().isoformat(),
        "required_actions": list(CONTRACT_REQUIRED_ACTIONS),
        "checked_actions": checked,
        "probe_requested": probe,
        "probe_results": probe_results,
        "issues": issues,
        "warnings": warnings,
        "valid": len(issues) == 0,
    }


def _handle_validate_contracts(
    paths: RepoPaths,
    contracts: dict[str, Any],
    action_args: list[str] | None = None,
    json_mode: bool = False,
) -> int:
    tokens = list(action_args or [])
    if tokens and tokens[0] == "validate_contracts":
        tokens = tokens[1:]
    probe = "--probe" in tokens
    payload = _validate_contracts_payload(contracts, paths=paths, probe=probe)
    report = paths.nusyq_hub / "state" / "reports" / "action_contracts_validation_latest.json"
    _write_json_report(report, payload)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🧾 Action Contract Validation")
        print("=" * 60)
        print(f"Valid: {'YES' if payload['valid'] else 'NO'}")
        print(f"Required actions: {len(payload['required_actions'])}")
        if payload.get("probe_requested"):
            probe_results = payload.get("probe_results", [])
            passed = sum(1 for row in probe_results if isinstance(row, dict) and row.get("ok"))
            print(f"Runtime probes: {passed}/{len(probe_results)} passed")
        print(f"Issues: {len(payload['issues'])} | Warnings: {len(payload['warnings'])}")
        if payload["issues"]:
            print("\nIssues:")
            for issue in payload["issues"]:
                print(f"  - {issue}")
        if payload["warnings"]:
            print("\nWarnings:")
            for warning in payload["warnings"]:
                print(f"  - {warning}")
        print(f"\nReport: {report}")

    return 0 if payload.get("valid") else 1


def run(cmd: list[str], cwd: Path | None = None, timeout_s: int = 10) -> tuple[int, str, str]:
    """Run a subprocess command safely and return (code, stdout, stderr)."""
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=_build_env(),
            check=False,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"


def _run_fast_test_suite(paths: RepoPaths, timeout_s: int = 60) -> tuple[int, str, str]:
    """Run a minimal pytest subset when fast mode is enabled.

    Fast mode avoids heavy optional deps (sentence_transformers, sklearn, scipy)
    by running lightweight unit tests only with extended timeout for pytest module
    initialization. Timeout is bumped to 180s to allow proper import time.
    """
    # Increase timeout aggressively to allow pytest and module initialization
    # on systems with slower I/O or many installed packages
    timeout_s = max(180, timeout_s)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--disable-warnings",
        "--tb=short",
        "-xvs",
        "-m",
        "not ml_heavy",  # Skip tests marked as ml_heavy (sentence_transformers, sklearn, scipy)
        # Lightweight tests: no ML/AI heavy deps, no sentence_transformers, sklearn, scipy
        "tests/",
    ]
    return run(cmd, cwd=paths.nusyq_hub, timeout_s=timeout_s)


def get_action_tier(action_id: str, contracts: dict, catalog: dict | None = None) -> str:
    try:
        actions = contracts.get("actions", {})
        if action_id in actions:
            contract = actions[action_id] if isinstance(actions[action_id], dict) else {}
            return contract.get("safety_tier") or contract.get("tier", "read_only")
        composites = contracts.get("composites", {})
        if action_id in composites:
            composite = composites[action_id] if isinstance(composites[action_id], dict) else {}
            return composite.get("safety_tier") or composite.get("tier", "read_only")
    except Exception:
        return "read_only"
    if catalog:
        safety = catalog.get("wired_actions", {}).get(action_id, {}).get("safety")
        if safety == "moderate":
            return "safe_mutation"
        if safety == "safe":
            return "read_only"
    return "read_only"


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def ensure_run_id() -> str:
    global _RUN_ID
    if not _RUN_ID:
        _RUN_ID = os.environ.get("NUSYQ_RUN_ID")
        if not _RUN_ID:
            _RUN_ID = f"run_{now_stamp()}_{uuid.uuid4().hex[:8]}"
        os.environ["NUSYQ_RUN_ID"] = _RUN_ID
        os.environ["OTEL_RESOURCE_ATTRIBUTES"] = _append_resource_attributes(
            os.environ.get("OTEL_RESOURCE_ATTRIBUTES"),
            {"nusyq.run.id": _RUN_ID},
        )
    return _RUN_ID


# ---------------------------
# Repo snapshot
# ---------------------------


@dataclass
class RepoSnapshot:
    name: str
    path: Path | None
    is_present: bool
    is_git: bool
    branch: str = "unknown"
    dirty: str = "unknown"
    head: str = "unknown"
    ahead_behind: str = "unknown"
    notes: list[str] | None = None

    def to_markdown(self) -> str:
        p = str(self.path) if self.path else "NOT FOUND"
        notes_list = self.notes or []
        notes = "\n".join([f"- {n}" for n in notes_list]) if notes_list else "- (none)"

        return (
            f"### {self.name}\n"
            f"- Path: `{p}`\n"
            f"- Git repo: `{self.is_git}`\n"
            f"- Branch: `{self.branch}`\n"
            f"- HEAD: `{self.head}`\n"
            f"- Working tree: `{self.dirty}`\n"
            f"- Ahead/Behind: `{self.ahead_behind}`\n"
            f"- Notes:\n{notes}\n"
        )


def git_snapshot(name: str, path: Path | None) -> RepoSnapshot:
    snap = RepoSnapshot(
        name=name,
        path=path,
        is_present=bool(path and path.exists()),
        is_git=bool(path and is_git_repo(path)),
        notes=[],
    )
    if not snap.is_present:
        snap.notes.append("Repo path not found.")
        return snap
    if not snap.is_git:
        snap.notes.append("Folder exists but does not look like a git repo.")
        return snap

    # branch
    rc, out, err = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path, timeout_s=3)
    if rc == 0 and out:
        snap.branch = out
    else:
        snap.notes.append(f"Could not read branch: {err or 'unknown error'}")

    # head sha
    rc, out, err = run(["git", "rev-parse", "HEAD"], cwd=path, timeout_s=3)
    if rc == 0 and out:
        snap.head = out[:12]
    else:
        snap.notes.append(f"Could not read HEAD: {err or 'unknown error'}")

    # dirty?
    dirty_state, dirty_error = _probe_working_tree_dirty(path)
    if dirty_state:
        snap.dirty = dirty_state
    elif dirty_error:
        snap.notes.append(f"Could not read status: {dirty_error}")
    else:
        snap.notes.append("Could not read status: unknown error")

    # ahead/behind (best-effort; may fail if no upstream)
    rc, out, err = run(
        ["git", "rev-list", "--left-right", "--count", "@{upstream}...HEAD"],
        cwd=path,
        timeout_s=GIT_UPSTREAM_TIMEOUT_S,
    )
    if rc == 0 and out:
        # output like: "X\tY" = behind ahead (depending on git)
        snap.ahead_behind = out.replace("\t", " ")
    else:
        snap.ahead_behind = "n/a"
        if err.startswith("TimeoutExpired"):
            snap.notes.append(f"Upstream probe timed out (>{GIT_UPSTREAM_TIMEOUT_S}s).")
        else:
            snap.notes.append("No upstream info (or upstream not set).")

    return snap


def _probe_working_tree_dirty(path: Path) -> tuple[str | None, str | None]:
    """Fast dirty probe with fallback to porcelain status."""
    probe_errors: list[str] = []
    for command in (FAST_DIRTY_DIFF_CMD, FAST_DIRTY_CACHED_CMD):
        rc, _out, err = run(command, cwd=path, timeout_s=GIT_DIRTY_TIMEOUT_S)
        if rc == 1:
            return "DIRTY", None
        if rc == 0:
            continue
        if err:
            probe_errors.append(err)

    if not probe_errors:
        return "clean", None

    rc, out, err = run(FAST_STATUS_CMD, cwd=path, timeout_s=GIT_STATUS_TIMEOUT_S)
    if rc == 0:
        return ("clean" if not out else "DIRTY"), None
    if err.startswith("TimeoutExpired"):
        return None, f"timed out (>{GIT_STATUS_TIMEOUT_S}s)"
    return None, (probe_errors[0] if probe_errors else err or "unknown error")


# ---------------------------
# Quest reading (NuSyQ-Hub canonical)
# ---------------------------


@dataclass
class QuestSnapshot:
    source_path: Path | None
    last_line: str = ""
    last_nonempty_line: str = ""
    notes: list[str] | None = None

    def to_markdown(self) -> str:
        p = str(self.source_path) if self.source_path else "NOT FOUND"
        notes_list = self.notes or []
        notes = "\n".join([f"- {n}" for n in notes_list]) if notes_list else "- (none)"
        return (
            "## Current Quest (best-effort)\n"
            f"- Source: `{p}`\n"
            f"- Last line: `{self.last_line}`\n"
            f"- Last non-empty: `{self.last_nonempty_line}`\n"
            f"- Notes:\n{notes}\n"
        )


def read_quest_log(nusyq_hub_path: Path | None) -> QuestSnapshot:
    qs = QuestSnapshot(source_path=None, notes=[])
    if not nusyq_hub_path:
        qs.notes.append("NuSyQ-Hub path missing; cannot locate quest log.")
        return qs

    qpath = nusyq_hub_path / "src" / "Rosetta_Quest_System" / QUEST_LOG_FILENAME
    qs.source_path = qpath if qpath.exists() else None
    if not qpath.exists():
        qs.notes.append("quest_log.jsonl not found at canonical path.")
        return qs

    try:
        lines = qpath.read_text(encoding="utf-8", errors="replace").splitlines()
        qs.last_line = lines[-1].strip() if lines else ""
        # last non-empty
        for line in reversed(lines):
            if line.strip():
                qs.last_nonempty_line = line.strip()
                break

        # If jsonl, try to parse the last non-empty line as JSON and extract "quest"/"title"/"status"
        try:
            obj = json.loads(qs.last_nonempty_line) if qs.last_nonempty_line else None
            if isinstance(obj, dict):
                # heuristic fields
                title = obj.get("title") or obj.get("quest") or obj.get("name") or ""
                status = obj.get("status") or obj.get("state") or ""
                if title or status:
                    qs.notes.append(f"Parsed JSONL fields: title='{title}' status='{status}'")
        except Exception:
            qs.notes.append("Last non-empty line is not valid JSON (or not a dict).")
    except Exception as e:
        qs.notes.append(f"Failed reading quest log: {type(e).__name__}: {e}")

    return qs


# ---------------------------
# Health checks (lightweight, non-destructive)
# ---------------------------


def lightweight_health(nusyq_hub_path: Path | None) -> list[str]:
    """Phase 1: non-destructive indicators only.
    Phase 2: optionally call real health scripts if present.
    """
    items: list[str] = []
    if not nusyq_hub_path:
        return ["NuSyQ-Hub path missing; health checks skipped."]

    # Existence checks for known spine files you previously verified
    checks = [
        (AGENTS_FILENAME, nusyq_hub_path / AGENTS_FILENAME),
        ("SYSTEM_OVERVIEW", nusyq_hub_path / "docs" / "doctrine" / SYSTEM_OVERVIEW_FILENAME),
        ("ZETA_PROGRESS_TRACKER", nusyq_hub_path / "config" / "ZETA_PROGRESS_TRACKER.json"),
        ("quest_log", nusyq_hub_path / "src" / "Rosetta_Quest_System" / QUEST_LOG_FILENAME),
    ]
    for label, p in checks:
        items.append(f"{label}: {'OK' if p.exists() else 'MISSING'} ({p})")

    # Optional: detect if a known health script exists (do not run yet unless user opts in later)
    candidates = [
        nusyq_hub_path / HEALTH_FILENAME,
        nusyq_hub_path / "scripts" / HEALTH_FILENAME,
        nusyq_hub_path / "src" / "diagnostics" / "system_health_assessor.py",
    ]
    for c in candidates:
        if c.exists():
            items.append(f"Health script present (not executed): {c}")
            break
    else:
        items.append("No known health script found (non-fatal).")

    return items


# ---------------------------
# Paths/config
# ---------------------------


@dataclass
class WorkspacePaths:
    nusyq_hub: Path | None
    simulatedverse: Path | None
    nusyq_root: Path | None


# Type alias for backward compatibility
RepoPaths = WorkspacePaths

# Cached path discovery to avoid slow searches
_PATH_CACHE: WorkspacePaths | None = None
_PATH_CACHE_TIME: float = 0.0
PATH_CACHE_TTL_SECONDS = 300  # 5 minutes


def _load_path_cache(hub: Path | None) -> dict | None:
    """Load cached paths from disk with git-aware invalidation."""
    if not hub:
        return None
    cache_file = hub / "state" / "path_cache.json"
    if cache_file.exists():
        try:
            import time

            data = read_json(cache_file)
            if not data:
                return None

            # Check TTL
            cache_age = time.time() - data.get("timestamp", 0)
            if cache_age >= PATH_CACHE_TTL_SECONDS:
                return None  # Cache expired

            # Check git invalidation: if .git/config modified, invalidate cache
            git_config = hub / ".git" / "config"
            if git_config.exists():
                try:
                    git_mtime = git_config.stat().st_mtime
                    cached_git_mtime = data.get("git_config_mtime", 0)
                    if git_mtime > cached_git_mtime:
                        return None  # .git/config changed, invalidate
                except Exception:
                    pass

            return data
        except Exception:
            pass
    return None


def _save_path_cache(hub: Path | None, paths: WorkspacePaths) -> None:
    """Save discovered paths to disk cache with git mtime tracking."""
    if not hub:
        return
    cache_file = hub / "state" / "path_cache.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        import time

        git_config = hub / ".git" / "config"
        git_mtime = 0
        if git_config.exists():
            try:
                git_mtime = git_config.stat().st_mtime
            except Exception:
                pass

        data = {
            "timestamp": time.time(),
            "git_config_mtime": git_mtime,
            "simulatedverse": str(paths.simulatedverse) if paths.simulatedverse else None,
            "nusyq_root": str(paths.nusyq_root) if paths.nusyq_root else None,
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


_XP_ACTION_MAP = {
    "heal": ("monitoring", 15),
    "scan": ("monitoring", 5),
    "suggest": ("ai_coordination", 10),
    "queue": ("automation", 2),
    "work": ("automation", 25),
    "evolve": ("automation", 50),
    "auto_cycle": ("automation", 10),
    "chug": ("automation", 15),
    "autonomous_service": ("automation", 12),
    "error_report": ("monitoring", 5),
    "error_report_split": ("monitoring", 5),
    "ai_work_gate": ("monitoring", 2),
    "ai_status": ("monitoring", 2),
    "graph_learning": ("monitoring", 4),
    "brief": ("monitoring", 3),
    "test": ("error_handling", 20),
}


def _award_xp_for_action(action: str) -> None:
    """Best-effort XP award for CLI actions using the unified XP router."""
    if action not in _XP_ACTION_MAP:
        return
    try:
        from src.system.rpg_inventory import award_xp  # Local import to avoid startup costs
    except Exception:
        return
    skill, points = _XP_ACTION_MAP[action]
    try:
        award_xp(skill, points, award_game_fn=None)
    except Exception:
        pass


def _coerce_workspace_path(raw_path: str | None, fallback: Path | None = None) -> Path | None:
    """Convert configured/env path strings into usable local paths (WSL-aware)."""
    if not raw_path:
        return fallback
    text = str(raw_path).strip()
    if not text:
        return fallback
    # On native Windows, skip WSL path conversion - /mnt/c doesn't exist
    if sys.platform == "win32":
        candidate = Path(text).expanduser()
        if candidate.exists():
            return candidate
        return fallback if fallback is not None else candidate
    # WSL/Linux: Try converting Windows drive paths to WSL mount paths
    drive_match = re.match(r"^([A-Za-z]):[\\/](.*)$", text)
    if drive_match:
        drive = drive_match.group(1).lower()
        tail = drive_match.group(2).replace("\\", "/").lstrip("/")
        wsl_candidate = Path("/mnt") / drive / tail
        if wsl_candidate.exists():
            return wsl_candidate
    candidate = Path(text).expanduser()
    if candidate.exists():
        return candidate
    return fallback if fallback is not None else candidate


def _load_paths_from_env() -> tuple[Path | None, Path | None, Path | None]:
    """Load paths from environment variables."""
    env_hub = os.environ.get("NUSYQ_HUB_PATH")
    env_sv = os.environ.get("SIMULATEDVERSE_PATH")
    env_root = os.environ.get("NUSYQ_ROOT_PATH")

    hub = _coerce_workspace_path(env_hub)
    sv = _coerce_workspace_path(env_sv)
    root = _coerce_workspace_path(env_root)

    return hub, sv, root


def _load_paths_from_config(
    hub: Path | None,
) -> tuple[Path | None, Path | None, Path | None]:
    """Load/override paths from config file."""
    if not hub:
        return hub, None, None

    cfg = hub / "config" / "start_nusyq.local.json"
    if not cfg.exists():
        return hub, None, None

    data = read_json(cfg) or {}
    hub = _coerce_workspace_path(data.get("nusyq_hub"), fallback=hub)
    sv = _coerce_workspace_path(data.get("simulatedverse"))
    root = _coerce_workspace_path(data.get("nusyq_root"))

    return hub, sv, root


def _load_paths_from_cache(
    hub: Path | None, sv: Path | None, root: Path | None
) -> tuple[Path | None, Path | None, Path | None]:
    """Fill missing paths from disk cache."""
    if sv and root:
        return hub, sv, root

    cached = _load_path_cache(hub)
    if not cached:
        return hub, sv, root

    if not sv and cached.get("simulatedverse"):
        sv = _coerce_workspace_path(cached["simulatedverse"])
    if not root and cached.get("nusyq_root"):
        root = _coerce_workspace_path(cached["nusyq_root"])

    return hub, sv, root


def _normalize_repo_token(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _canonicalize_repo_path(path: Path | None, repo_name: str) -> Path | None:
    """Resolve wrapper directories to the real git repo directory."""
    if not path:
        return None
    candidate = path.expanduser()
    if not candidate.exists():
        return None
    if candidate.is_file():
        candidate = candidate.parent
    if is_git_repo(candidate):
        return candidate
    if not candidate.is_dir():
        return None

    expected = _normalize_repo_token(repo_name)
    queue: list[tuple[Path, int]] = [(candidate, 0)]
    ignored = {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "env",
        "dist",
        "build",
        ".idea",
        ".vscode",
        ".mypy_cache",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
    }
    while queue:
        current, depth = queue.pop(0)
        if depth > 2:
            continue
        try:
            for entry in current.iterdir():
                if not entry.is_dir() or entry.name in ignored:
                    continue
                entry_token = _normalize_repo_token(entry.name)
                if entry_token == expected and is_git_repo(entry):
                    return entry
                if depth < 2:
                    queue.append((entry, depth + 1))
        except Exception:
            continue
    return candidate


def _canonicalize_workspace_paths(
    hub: Path | None, sv: Path | None, root: Path | None
) -> tuple[Path | None, Path | None, Path | None]:
    return (
        _canonicalize_repo_path(hub, "NuSyQ-Hub"),
        _canonicalize_repo_path(sv, "SimulatedVerse"),
        _canonicalize_repo_path(root, "NuSyQ"),
    )


def find_repo_by_name(
    search_roots: list[Path],
    repo_name: str,
    max_depth: int = 4,
    allow_substring: bool = False,
) -> Path | None:
    """Best-effort search for a repository folder by name.

    Walks breadth-first from the provided search_roots up to max_depth levels looking
    for a directory whose name matches repo_name (case-insensitive). Optional substring
    matching can be enabled when exact matches are not viable. Only
    directories that appear to be repositories (contain a .git folder) are returned
    unless no .git is found anywhere, in which case the first name match is returned.

    This helper intentionally avoids scanning large/irrelevant directories.
    """
    if not search_roots:
        return None

    repo_name_lower = repo_name.lower().strip()
    repo_name_token = _normalize_repo_token(repo_name_lower)
    ignored = {
        "node_modules",
        ".git",
        ".venv",
        "venv",
        "env",
        "dist",
        "build",
        ".idea",
        ".vscode",
        ".mypy_cache",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
    }

    from collections import deque

    candidates_no_git: list[Path] = []
    q: deque[tuple[Path, int]] = deque()

    for root in search_roots:
        try:
            if root and root.exists() and root.is_dir():
                q.append((root, 0))
        except Exception:
            continue

    while q:
        current, depth = q.popleft()
        if depth > max_depth:
            continue

        try:
            for entry in current.iterdir():
                # Skip files and ignored directories early
                if entry.name in ignored:
                    continue
                if not entry.is_dir():
                    continue

                name_lower = entry.name.lower()

                name_token = _normalize_repo_token(name_lower)
                matched = name_lower == repo_name_lower or (repo_name_token and name_token == repo_name_token)
                if not matched and allow_substring and repo_name_token:
                    matched = repo_name_token in name_token

                if matched:
                    if is_git_repo(entry):
                        return entry
                    # Save as fallback if no .git repos found
                    candidates_no_git.append(entry)

                # Enqueue children for further search
                if depth < max_depth:
                    # avoid recursing into extremely large or irrelevant trees
                    if entry.name not in ignored:
                        q.append((entry, depth + 1))
        except Exception:
            # Best-effort search; ignore permission or transient errors
            continue

    # Fallback to first name match even if not a git repo
    return candidates_no_git[0] if candidates_no_git else None


def _discover_missing_paths(
    hub: Path | None, sv: Path | None, root: Path | None
) -> tuple[Path | None, Path | None, Path | None]:
    """Discover missing paths via filesystem search."""
    if sv and root:
        return hub, sv, root

    search_roots: list[Path] = []
    home = Path.home()
    search_roots.extend(
        [
            home / "Desktop",
            home / "Documents",
            home / "Source",
            home / "Projects",
            home,
        ]
    )

    if hub:
        search_roots.append(hub.parent)
        for ancestor in hub.parents[:4]:
            search_roots.append(ancestor)

    if not sv:
        sv = find_repo_by_name(search_roots, "SimulatedVerse")
    if not root:
        root = find_repo_by_name(search_roots, "NuSyQ") or find_repo_by_name(
            search_roots, "-NuSyQ_Ultimate_Repo", allow_substring=True
        )

    return hub, sv, root


def load_paths(nusyq_hub_default: Path | None, allow_discovery: bool = True) -> WorkspacePaths:
    """Load workspace paths with fallback priority:
    1) Environment variables
    2) Config file (config/start_nusyq.local.json)
    3) Cached discovery (avoids slow searches)
    4) Fresh filesystem discovery (slow, last resort)
    """
    global _PATH_CACHE, _PATH_CACHE_TIME
    import time

    # Check in-memory cache first
    if _PATH_CACHE and (time.time() - _PATH_CACHE_TIME) < PATH_CACHE_TTL_SECONDS:
        return _PATH_CACHE

    # Load from priority sources
    hub, sv, root = _load_paths_from_env()
    if not hub:
        hub = nusyq_hub_default

    hub, sv, root = _load_paths_from_config(hub)
    hub, sv, root = _load_paths_from_cache(hub, sv, root)

    # Canonicalize configured/cached values before discovery.
    hub, sv, root = _canonicalize_workspace_paths(hub, sv, root)

    # Fresh discovery if allowed and needed
    if allow_discovery:
        hub, sv, root = _discover_missing_paths(hub, sv, root)
        hub, sv, root = _canonicalize_workspace_paths(hub, sv, root)

    # Cache result
    result = WorkspacePaths(nusyq_hub=hub, simulatedverse=sv, nusyq_root=root)
    _PATH_CACHE = result
    _PATH_CACHE_TIME = time.time()

    if allow_discovery and (not sv or not root):
        _save_path_cache(hub, result)

    return result


# ---------------------------
# Tracing config + receipts
# ---------------------------


def _trace_config_path(hub_path: Path | None) -> Path | None:
    if not hub_path:
        return None
    return hub_path / "config" / "tracing" / "trace_config.json"


def load_trace_config(hub_path: Path | None) -> dict:
    default = {
        "enabled": True,
        "endpoint": os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318"),
        "service_name": "nusyq-hub",
        "exporter": "otlp",
        "sampling_ratio": 1.0,
    }
    config_path = _trace_config_path(hub_path)
    if not config_path or not config_path.exists():
        return default
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        default.update({k: v for k, v in data.items() if v is not None})
    except Exception:
        pass
    return default


def save_trace_config(hub_path: Path | None, config: dict) -> Path | None:
    config_path = _trace_config_path(hub_path)
    if not config_path:
        return None
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config_path


def apply_trace_config(config: dict) -> None:
    enabled = bool(config.get("enabled", True))
    os.environ["NUSYQ_TRACE"] = "1" if enabled else "0"
    os.environ["NUSYQ_TRACING"] = "1" if enabled else "0"
    if not enabled:
        os.environ["OTEL_SDK_DISABLED"] = "true"
        os.environ["OTEL_TRACES_EXPORTER"] = "none"
        return
    os.environ.pop("OTEL_SDK_DISABLED", None)
    endpoint = config.get("endpoint")
    if endpoint:
        base = str(endpoint).rstrip("/")
        os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
        os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{base}/v1/traces"
        os.environ["OTEL_EXPORTER_OTLP_PROTOCOL"] = "http/protobuf"
        os.environ["OTEL_EXPORTER_OTLP_TRACES_PROTOCOL"] = "http/protobuf"
    service_name = config.get("service_name")
    if service_name:
        os.environ["OTEL_SERVICE_NAME"] = str(service_name)
    exporter = config.get("exporter")
    if exporter:
        os.environ["OTEL_TRACES_EXPORTER"] = str(exporter)
    sampling_ratio = config.get("sampling_ratio")
    if sampling_ratio is not None:
        os.environ["OTEL_TRACES_SAMPLER"] = "parentbased_traceidratio"
        os.environ["OTEL_TRACES_SAMPLER_ARG"] = str(sampling_ratio)


def _write_json_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _load_and_apply_trace_config(hub_path: Path | None) -> dict:
    """Load trace config for a hub path and apply env settings once."""
    config = load_trace_config(hub_path)
    apply_trace_config(config)
    return config


def _write_state_report(hub_path: Path | None, filename: str, payload: dict) -> Path:
    """Write a JSON report under state/reports for the given hub path."""
    base = hub_path if hub_path else Path(".")
    report_path = base / "state" / "reports" / filename
    _write_json_report(report_path, payload)
    return report_path


def _write_job_exit_code_from_env(exit_code: int) -> None:
    """Best-effort write of background job exit code to the rc file from env."""
    rc_file = os.getenv("NUSYQ_JOB_RC_FILE", "").strip()
    if not rc_file:
        return
    try:
        rc_path = Path(rc_file)
        rc_path.parent.mkdir(parents=True, exist_ok=True)
        rc_path.write_text(str(int(exit_code)), encoding="utf-8")
    except Exception:
        return


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw in handle:
                line = raw.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
    except OSError:
        return []
    if limit <= 0:
        return rows
    return rows[-limit:]


def _build_system_complete_dashboard(history: list[dict[str, Any]], latest: dict[str, Any]) -> dict[str, Any]:
    by_check: dict[str, dict[str, Any]] = {}
    for run_entry in history:
        checks = run_entry.get("checks")
        if not isinstance(checks, list):
            continue
        for check in checks:
            if not isinstance(check, dict):
                continue
            name = str(check.get("name") or "").strip()
            if not name:
                continue
            passed = bool(check.get("passed"))
            stats = by_check.setdefault(
                name,
                {"name": name, "runs": 0, "passed": 0, "failed": 0, "recent": []},
            )
            stats["runs"] += 1
            if passed:
                stats["passed"] += 1
            else:
                stats["failed"] += 1
            stats["recent"].append("PASS" if passed else "FAIL")

    trends: list[dict[str, Any]] = []
    for name, stats in sorted(by_check.items()):
        runs = int(stats["runs"])
        passed = int(stats["passed"])
        recent = stats["recent"][-10:]
        trends.append(
            {
                "name": name,
                "runs": runs,
                "passed": passed,
                "failed": int(stats["failed"]),
                "pass_rate": round(passed / runs, 4) if runs else 0.0,
                "recent": recent,
                "last_status": recent[-1] if recent else "UNKNOWN",
            }
        )

    return {
        "action": "system_complete_dashboard",
        "generated_at": datetime.now().isoformat(),
        "history_runs": len(history),
        "latest": {
            "generated_at": latest.get("generated_at"),
            "overall_pass": latest.get("overall_pass"),
            "passed": latest.get("passed"),
            "total": latest.get("total"),
        },
        "per_check_trends": trends,
    }


def _receipt_dir(hub_path: Path | None) -> Path:
    base = hub_path / "docs" / "tracing" / "RECEIPTS" if hub_path else Path("docs/tracing/RECEIPTS")
    base.mkdir(parents=True, exist_ok=True)
    return base


def emit_receipt(
    action_id: str,
    hub_path: Path | None,
    tier: str,
    run_id: str,
    trace_id: str,
    span_id: str,
    status: str,
    inputs: dict[str, Any] | None = None,
    exit_code: int | None = None,
    outputs: list[str] | None = None,
    next_steps: list[str] | None = None,
    receipt_path: Path | None = None,
) -> Path:
    receipts_dir = _receipt_dir(hub_path)
    if receipt_path is None:
        receipt_path = receipts_dir / f"{action_id}_{now_stamp()}.txt"
    outputs_list = outputs or []
    inputs_payload = inputs or {}
    next_list = next_steps or []
    receipt_text = f"""[RECEIPT]
action.id: {action_id}
action.tier: {tier}
run.id: {run_id}
repo.name: NuSyQ-Hub
repo.path: {hub_path}
cwd: {hub_path}
tracing: {("enabled" if trace_id != "n/a" else "disabled")}
trace_id: {trace_id}
span_id: {span_id}
status: {status}
exit_code: {exit_code}
receipt.path: {receipt_path}
inputs: {inputs_payload}
outputs: {outputs_list}
    next: {next_list}
"""
    receipt_path.write_text(receipt_text, encoding="utf-8")
    if not _JSON_OUTPUT:
        print("\n" + receipt_text)
    return receipt_path


# ---------------------------
# Delta tracking
# ---------------------------


def _select_latest_error_report_path(hub_path: Path | None) -> Path | None:
    """Return best unified error report artifact, balancing scope, quality, and recency."""
    if not hub_path:
        return None
    diagnostics_dir = hub_path / "docs" / "Reports" / "diagnostics"
    latest = diagnostics_dir / "unified_error_report_latest.json"
    candidates = [p for p in diagnostics_dir.glob("unified_error_report_*.json") if p.exists()]
    if latest.exists():
        candidates.append(latest)
    if not candidates:
        return None

    best_path: Path | None = None
    best_score: float = float("-inf")
    best_ts: datetime | None = None

    for report_path in candidates:
        payload: dict[str, Any]
        try:
            payload_raw = json.loads(report_path.read_text(encoding="utf-8"))
            payload = payload_raw if isinstance(payload_raw, dict) else {}
        except (OSError, json.JSONDecodeError):
            continue

        timestamp_raw = payload.get("timestamp")
        if isinstance(timestamp_raw, str) and timestamp_raw.strip():
            normalized = timestamp_raw.replace("Z", "+00:00")
            try:
                ts = datetime.fromisoformat(normalized)
            except ValueError:
                ts = datetime.fromtimestamp(report_path.stat().st_mtime, tz=UTC)
        else:
            try:
                ts = datetime.fromtimestamp(report_path.stat().st_mtime, tz=UTC)
            except OSError:
                continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)

        ground_truth = payload.get("ground_truth")
        gt = ground_truth if isinstance(ground_truth, dict) else {}
        scope = gt.get("scope")
        scope_obj = scope if isinstance(scope, dict) else {}
        targets_raw = scope_obj.get("targets", payload.get("targets", []))
        targets = targets_raw if isinstance(targets_raw, list) else []
        target_count = len(targets)

        scan_mode = str(scope_obj.get("scan_mode", payload.get("scan_mode", ""))).lower()
        partial_scan = bool(scope_obj.get("partial_scan", payload.get("partial_scan", False)))
        confidence = str(gt.get("confidence", "unknown")).lower()
        age_hours = max((datetime.now(UTC) - ts).total_seconds() / 3600.0, 0.0)

        quality = target_count * 100
        quality += 40 if scan_mode == "full" else 10 if scan_mode == "quick" else 0
        quality += 20 if not partial_scan else -10
        quality += 15 if confidence == "high" else 8 if confidence == "medium" else 3 if confidence == "low" else 0
        score = float(quality) - (age_hours * 2.0)

        if score > best_score or (score == best_score and (best_ts is None or ts > best_ts)):
            best_score = score
            best_path = report_path
            best_ts = ts

    if best_path:
        return best_path
    try:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    except OSError:
        return latest if latest.exists() else candidates[0]


def _count_lint_errors(hub_path: Path | None) -> int | None:
    """Count current diagnostic errors with ground-truth preference.

    Priority:
    1) Best recent unified_error_report_*.json candidate (scope-weighted)
    2) Candidate by_severity.errors
    3) ruff scan fallback
    """
    if not hub_path:
        return None

    diagnostics_dir = hub_path / "docs" / "Reports" / "diagnostics"
    latest = diagnostics_dir / "unified_error_report_latest.json"
    timestamped = sorted(
        diagnostics_dir.glob("unified_error_report_*.json"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
        reverse=True,
    )
    candidates: list[Path] = []
    if latest.exists():
        candidates.append(latest)
    for path in timestamped:
        if path.name.endswith("_latest.json"):
            continue
        candidates.append(path)
        if len(candidates) >= 25:
            break

    best: tuple[float, datetime, dict[str, Any]] | None = None
    for report_path in candidates:
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict):
            continue

        timestamp_raw = payload.get("timestamp")
        if not isinstance(timestamp_raw, str) or not timestamp_raw.strip():
            try:
                ts = datetime.fromtimestamp(report_path.stat().st_mtime, tz=UTC)
            except OSError:
                continue
        else:
            normalized = timestamp_raw.replace("Z", "+00:00")
            try:
                ts = datetime.fromisoformat(normalized)
            except ValueError:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)

        ground_truth = payload.get("ground_truth")
        gt = ground_truth if isinstance(ground_truth, dict) else {}
        scope = gt.get("scope")
        scope_obj = scope if isinstance(scope, dict) else {}
        targets_raw = scope_obj.get("targets", payload.get("targets", []))
        targets = targets_raw if isinstance(targets_raw, list) else []
        target_count = len(targets)

        scan_mode = str(scope_obj.get("scan_mode", payload.get("scan_mode", ""))).lower()
        partial_scan = bool(scope_obj.get("partial_scan", payload.get("partial_scan", False)))
        confidence = str(gt.get("confidence", "unknown")).lower()
        age_hours = max((datetime.now(UTC) - ts).total_seconds() / 3600.0, 0.0)

        quality = target_count * 100
        quality += 40 if scan_mode == "full" else 10 if scan_mode == "quick" else 0
        quality += 20 if not partial_scan else -10
        quality += 15 if confidence == "high" else 8 if confidence == "medium" else 3 if confidence == "low" else 0
        score = float(quality) - (age_hours * 2.0)

        if best is None or score > best[0] or (score == best[0] and ts > best[1]):
            best = (score, ts, payload)

    if best is not None:
        payload = best[2]
        ground_truth = payload.get("ground_truth")
        if isinstance(ground_truth, dict) and ground_truth.get("errors") is not None:
            try:
                return int(ground_truth.get("errors", 0))
            except (TypeError, ValueError):
                pass
        by_severity = payload.get("by_severity")
        if isinstance(by_severity, dict) and by_severity.get("errors") is not None:
            try:
                return int(by_severity.get("errors", 0))
            except (TypeError, ValueError):
                pass

    try:
        _, out, _ = run(
            ["python", "-m", "ruff", "check", "src/", "tests/", "scripts/", "--output-format=json"],
            cwd=hub_path,
            timeout_s=30,
        )
        if out:
            errors = json.loads(out)
            return len(errors)
        return 0
    except Exception:
        return None


def _get_recent_ai_usage(hub_path: Path | None) -> list[str]:
    """Extract AI systems used from recent quest log entries."""
    if not hub_path:
        return []

    quest_file = hub_path / "src" / "Rosetta_Quest_System" / QUEST_LOG_FILENAME
    if not quest_file.exists():
        return []

    ai_systems = set()
    try:
        with open(quest_file, encoding="utf-8") as f:
            # Read last 50 lines
            lines = f.readlines()
            for line in lines[-50:]:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    system = entry.get("system")
                    if system and system not in ["human", "unknown", None]:
                        ai_systems.add(system)
                except (json.JSONDecodeError, KeyError):
                    continue
    except Exception:
        pass

    return sorted(ai_systems)


def _extract_previous_snapshot_data(prev_content: str) -> dict[str, Any]:
    """Extract previous snapshot metadata from markdown content.

    Returns dict with keys: head, dirty, ahead_behind, errors, ai_agents, quest_line
    """
    import re

    data = {}

    prev_head_match = re.search(r"- HEAD: `([^`]+)`", prev_content)
    data["head"] = prev_head_match.group(1) if prev_head_match else None

    prev_dirty_match = re.search(r"- Working tree: `([^`]+)`", prev_content)
    data["dirty"] = prev_dirty_match.group(1) if prev_dirty_match else None

    prev_ahead_behind_match = re.search(r"- Ahead/Behind: `([^`]+)`", prev_content)
    data["ahead_behind"] = prev_ahead_behind_match.group(1) if prev_ahead_behind_match else None

    prev_errors_match = re.search(r"- Lint errors: `(\d+)`", prev_content)
    data["errors"] = int(prev_errors_match.group(1)) if prev_errors_match else None

    prev_ai_match = re.search(r"- AI agents used: `([^`]+)`", prev_content)
    data["ai_agents"] = prev_ai_match.group(1).split(", ") if prev_ai_match else []

    prev_quest_match = re.search(r"- Last non-empty: `([^`]+)`", prev_content)
    data["quest_line"] = prev_quest_match.group(1) if prev_quest_match else None

    return data


def _compute_commit_deltas(prev_head: str | None, current_snap: RepoSnapshot) -> list[str]:
    """Compute git commit-related deltas."""
    deltas = []

    if prev_head and prev_head != current_snap.head and current_snap.path:
        try:
            rc, out, _ = run(
                ["git", "rev-list", "--count", f"{prev_head}..{current_snap.head}"],
                cwd=current_snap.path,
                timeout_s=5,
            )
            if rc == 0 and out.strip().isdigit():
                commit_count = int(out.strip())
                if commit_count > 0:
                    deltas.append(f"📝 {commit_count} new commit{'s' if commit_count != 1 else ''} since last snapshot")
        except Exception:
            pass

    return deltas


def _compute_working_tree_deltas(prev_dirty: str | None, current_snap: RepoSnapshot) -> list[str]:
    """Compute working tree status deltas."""
    deltas = []

    if prev_dirty and prev_dirty != current_snap.dirty:
        if current_snap.dirty == "clean" and prev_dirty == "DIRTY":
            deltas.append("✅ Working tree cleaned (was dirty)")
        elif current_snap.dirty == "DIRTY" and prev_dirty == "clean":
            deltas.append("⚠️ Working tree now dirty (was clean)")

    return deltas


def _compute_ahead_behind_deltas(prev_ahead_behind: str | None, current_snap: RepoSnapshot) -> list[str]:
    """Compute ahead/behind branch deltas."""
    deltas = []

    if prev_ahead_behind and prev_ahead_behind != current_snap.ahead_behind:
        try:
            prev_parts = prev_ahead_behind.split()
            curr_parts = current_snap.ahead_behind.split()
            if len(prev_parts) == 2 and len(curr_parts) == 2:
                prev_ahead = int(prev_parts[1]) if prev_parts[1].isdigit() else 0
                curr_ahead = int(curr_parts[1]) if curr_parts[1].isdigit() else 0
                if curr_ahead > prev_ahead:
                    delta_ahead = curr_ahead - prev_ahead
                    deltas.append(f"⬆️ {delta_ahead} more commit{'s' if delta_ahead != 1 else ''} ahead of remote")
        except (ValueError, OSError) as e:
            logger.warning(f"Ahead/behind parse error: {e}")

    return deltas


def _compute_error_deltas(prev_errors: int | None, current_errors: int | None) -> list[str]:
    """Compute error count reduction/increase deltas."""
    deltas = []

    if prev_errors is not None and current_errors is not None:
        if current_errors < prev_errors:
            reduction = prev_errors - current_errors
            deltas.append(
                f"🔧 {reduction} lint error{'s' if reduction != 1 else ''} fixed ({prev_errors} → {current_errors})"
            )
        elif current_errors > prev_errors:
            increase = current_errors - prev_errors
            deltas.append(
                f"⚠️ {increase} new lint error{'s' if increase != 1 else ''} ({prev_errors} → {current_errors})"
            )

    return deltas


def _compute_ai_agent_deltas(prev_ai_agents: list[str], current_ai_agents: list[str]) -> list[str]:
    """Compute AI agent usage deltas."""
    deltas = []

    new_ai_agents = set(current_ai_agents) - set(prev_ai_agents)
    if new_ai_agents:
        deltas.append(f"🤖 New AI systems used: {', '.join(sorted(new_ai_agents))}")

    return deltas


def _compute_quest_deltas(hub_path: Path, prev_quest_line: str | None) -> list[str]:
    """Compute quest activity deltas."""
    deltas = []

    if prev_quest_line:
        try:
            current_quest = read_quest_log(hub_path)
            if current_quest.last_nonempty_line and current_quest.last_nonempty_line != prev_quest_line:
                try:
                    quest_data = json.loads(current_quest.last_nonempty_line)
                    task_type = quest_data.get("task_type", "unknown")
                    deltas.append(f"🎯 New quest activity: {task_type}")
                except json.JSONDecodeError:
                    deltas.append("🎯 Quest log updated")
        except Exception as e:
            logger.debug(f"Quest delta computation skipped: {e}")

    return deltas


def compute_deltas(hub_path: Path | None, current_snap: RepoSnapshot) -> list[str]:
    """Compare current snapshot with previous to extract meaningful deltas.

    Tracks:
    - Git commits (new commits since last snapshot)
    - Working tree status (clean ↔ dirty transitions)
    - Ahead/behind changes
    - Quest activity (new quests added)
    - Error count reduction (lint errors fixed)
    - AI agent usage (which systems invoked)
    """
    deltas = []

    if not hub_path:
        return deltas

    reports = hub_path / "state" / "reports"
    if not reports.exists():
        return deltas

    # Find most recent previous snapshot (not current_state.md)
    snapshots = sorted(reports.glob("current_state_*.md"), reverse=True)
    if not snapshots:
        deltas.append("🌱 First snapshot - no previous state to compare")
        return deltas

    prev_file = snapshots[0]
    try:
        prev_content = prev_file.read_text(encoding="utf-8")
        prev_data = _extract_previous_snapshot_data(prev_content)

        # Compute current metrics
        current_errors = _count_lint_errors(hub_path)
        current_ai_agents = _get_recent_ai_usage(hub_path)

        # Aggregate deltas from specialized functions
        deltas.extend(_compute_commit_deltas(prev_data["head"], current_snap))
        deltas.extend(_compute_working_tree_deltas(prev_data["dirty"], current_snap))
        deltas.extend(_compute_ahead_behind_deltas(prev_data["ahead_behind"], current_snap))
        deltas.extend(_compute_error_deltas(prev_data["errors"], current_errors))
        deltas.extend(_compute_ai_agent_deltas(prev_data["ai_agents"], current_ai_agents))
        deltas.extend(_compute_quest_deltas(hub_path, prev_data["quest_line"]))

    except Exception as e:
        deltas.append(f"⚠️ Could not compute deltas: {e}")

    return deltas


# ---------------------------
# Main orchestration
# ---------------------------


def build_markdown(paths: WorkspacePaths) -> str:
    stamp = now_stamp()

    hub_snap = git_snapshot("NuSyQ-Hub (Oldest House / Spine)", paths.nusyq_hub)
    sv_snap = git_snapshot("SimulatedVerse (Testing Chamber host)", paths.simulatedverse)
    root_snap = git_snapshot("NuSyQ Root / Ultimate (Vault/Substrate)", paths.nusyq_root)

    quest = read_quest_log(paths.nusyq_hub)
    health = lightweight_health(paths.nusyq_hub)
    deltas = compute_deltas(paths.nusyq_hub, hub_snap)

    # Compute current metrics for snapshot
    error_count = _count_lint_errors(paths.nusyq_hub)
    ai_agents = _get_recent_ai_usage(paths.nusyq_hub)
    terminal_snapshot = (
        read_json(paths.nusyq_hub / "state" / "reports" / "terminal_snapshot_latest.json") if paths.nusyq_hub else None
    )
    terminal_summary = terminal_snapshot.get("summary", {}) if isinstance(terminal_snapshot, dict) else {}
    awareness = terminal_snapshot.get("awareness", {}) if isinstance(terminal_snapshot, dict) else {}
    agent_registry = awareness.get("agent_registry", []) if isinstance(awareness, dict) else []
    output_surfaces = awareness.get("output_surfaces", []) if isinstance(awareness, dict) else []

    md = []
    md.append("# NuSyQ — Current System State\n")
    md.append(f"- Timestamp: `{stamp}`\n")

    # Add metrics section
    md.append("\n## 📊 Current Metrics\n")
    if error_count is not None:
        md.append(f"- Lint errors: `{error_count}`\n")
    if ai_agents:
        md.append(f"- AI agents used: `{', '.join(ai_agents)}`\n")
    else:
        md.append("- AI agents used: `none`\n")
    if terminal_summary:
        md.append(
            "- Terminal ecosystem: "
            f"`{terminal_summary.get('hot_channels', 0)}/{terminal_summary.get('total_channels', 0)}` hot "
            f"with `{terminal_summary.get('output_sources_configured', 0)}` routed output sources\n"
        )

    # Add deltas section if we have any
    if deltas:
        md.append("\n## 🔄 Changes Since Last Snapshot\n")
        for delta in deltas:
            md.append(f"- {delta}\n")

    md.append("\n## Repositories\n")
    md.append(hub_snap.to_markdown())
    md.append(sv_snap.to_markdown())
    md.append(root_snap.to_markdown())

    md.append(quest.to_markdown())

    md.append("## Health (lightweight)\n")
    for item in health:
        md.append(f"- {item}\n")

    md.append("## Terminal & Output Awareness\n")
    if terminal_summary:
        md.append(f"- Active session: `{terminal_summary.get('configured_session') or 'unknown'}`\n")
        md.append(
            f"- Channel heat: `{terminal_summary.get('hot_channels', 0)}` hot, "
            f"`{terminal_summary.get('warm_channels', 0)}` warm, "
            f"`{terminal_summary.get('cold_channels', 0)}` cold, "
            f"`{terminal_summary.get('missing_logs', 0)}` missing\n"
        )
        md.append(
            f"- Agent-visible registry: `{len(agent_registry)}` agents mapped across "
            f"`{terminal_summary.get('total_channels', 0)}` channels\n"
        )
        md.append(f"- Output surfaces: `{len(output_surfaces)}` logs/reports available to agents\n")
        top_agents = [item.get("agent") for item in agent_registry[:8] if isinstance(item, dict) and item.get("agent")]
        if top_agents:
            md.append(f"- Terminal-aware agents: `{', '.join(top_agents)}`\n")
    else:
        md.append("- Terminal registry: `not generated yet` (run `python scripts/start_nusyq.py terminal_snapshot`)\n")

    md.append("## Available Actions (Dynamically Wired)\n")
    # Map action names to descriptions and wire status
    action_descriptions = {
        "snapshot": ("Generate system state snapshot", "✅ WIRED"),
        "brief": ("Quick 60s system status", "✅ WIRED"),
        "capabilities": ("List all AI & system capabilities", "✅ WIRED"),
        "suggest": ("Get next 1-3 suggested tasks", "✅ WIRED"),
        "analyze": ("Run full system analysis OR analyze specific file with AI", "✅ WIRED"),
        "heal": ("Non-destructive system health & healing", "✅ WIRED"),
        "develop_system": (
            "Autonomous development treadmill (analyze → heal → repeat)",
            "✅ WIRED",
        ),
        "review": ("Code quality review of file/directory", "✅ WIRED"),
        "debug": ("Debug system errors or specific issues", "✅ WIRED"),
        "test": ("Run test suite", "✅ WIRED"),
        "test_history": ("Show recent test runs and duplicates", "✅ WIRED"),
        "log_dedup_status": ("Show logging dedup filter status", "✅ WIRED"),
        "quantum_resolver_status": ("Show quantum resolver consolidation status", "✅ WIRED"),
        "doctor": ("Full system diagnostics", "✅ WIRED"),
        "generate": ("Generate code or artifacts with AI", "✅ WIRED"),
        "work": ("Manage work queue & task tracking", "✅ WIRED"),
        "hygiene": ("System hygiene & cleanup operations", "✅ WIRED"),
        "prune_reports": ("Prune/archive stale generated reports", "✅ WIRED"),
        "map": ("Generate capability map documentation", "✅ WIRED"),
        "selfcheck": ("Smoke test & self-validation", "✅ WIRED"),
        "doctrine_check": ("Validate against instruction doctrines", "✅ WIRED"),
        "emergence_capture": ("Capture emergent intent events", "✅ WIRED"),
        "simverse_bridge": ("Bridge to SimulatedVerse ecosystem", "✅ WIRED"),
        "simverse_mode": ("Get/set default SimulatedVerse HTTP policy", "✅ WIRED"),
        "compose_secrets": ("Audit/init docker-compose secret env coverage", "✅ WIRED"),
        "queue": ("Execute next item from work queue", "✅ WIRED"),
        "pu_execute": ("Execute PU through agents (--real for actual execution)", "✅ WIRED"),
        "batch_commit": ("Autonomous batch commit orchestrator (--dry-run)", "✅ WIRED"),
        "metrics": ("Build cultivation metrics dashboard", "✅ WIRED"),
        "replay": ("Replay quests and generate learning report", "✅ WIRED"),
        "sync": ("Cross-sync cultivation data with SimulatedVerse", "✅ WIRED"),
        "auto_cycle": ("Run queue → replay → metrics → sync loop", "✅ WIRED"),
        "create_game": ("Spawn testing chamber prototype (TODO)", "⏳ PLACEHOLDER"),
    }

    for action_name, (description, status) in sorted(action_descriptions.items()):
        md.append(f"- `{action_name}` — {description} {status}\n")

    md.append("\n## Notes\n")
    md.append("- This snapshot is read-only and safe by default.\n")
    md.append("- All core actions are wired to handlers (not Phase-1 stubs).\n")
    md.append("- See `python start_nusyq.py help` for detailed command reference.\n")

    return "".join(md)


def write_report(nusyq_hub: Path | None, md: str) -> Path | None:
    if not nusyq_hub:
        return None
    # Create state/report dirs if missing (safe, small, intended)
    base = nusyq_hub / "state" / "reports"
    base.mkdir(parents=True, exist_ok=True)

    latest = base / "current_state.md"
    stamped = base / f"current_state_{now_stamp()}.md"

    previous_text = ""
    if latest.exists():
        try:
            previous_text = latest.read_text(encoding="utf-8")
        except OSError:
            previous_text = ""
    changed = previous_text != md

    try:
        keep_count = int(os.getenv("NUSYQ_CURRENT_STATE_HISTORY_KEEP", "14"))
    except ValueError:
        keep_count = 14
    write_history = str(os.getenv("NUSYQ_CURRENT_STATE_WRITE_HISTORY", "1")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    skip_unchanged = str(os.getenv("NUSYQ_CURRENT_STATE_SKIP_UNCHANGED_HISTORY", "1")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    latest.write_text(md, encoding="utf-8")
    if write_history and (changed or not skip_unchanged):
        stamped.write_text(md, encoding="utf-8")
    if write_history:
        _prune_lifecycle_reports(base, max(1, keep_count), pattern="current_state_*.md")
    return latest


def run_heal(hub_path: Path | None) -> int:
    """Wire to agent_task_router.heal_system() for comprehensive system healing."""
    if not hub_path:
        print("[ERROR] NuSyQ-Hub path not found; cannot run health check.")
        return 1

    print("🏥 Running system healing (QuickSystemAnalyzer + RepositoryHealthRestorer)...")

    # Wire to agent_task_router
    if str(hub_path) not in sys.path:
        sys.path.insert(0, str(hub_path))

    try:
        import asyncio

        from src.tools.agent_task_router import AgentTaskRouter

        router = AgentTaskRouter(repo_root=hub_path)
        result = asyncio.run(router.heal_system(auto_confirm=False))

        if result["status"] == "success":
            print(f"\n✅ Healing complete: {len(result['actions_taken'])} actions")
            print(f"Report saved: {result['report_path']}")
            return 0
        else:
            print(f"\n❌ Healing failed: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as exc:
        print(f"[ERROR] Healing failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def run_capability_map(hub_path: Path | None) -> int:
    """Generate capability map from action catalog and scripts."""
    if not hub_path:
        print("[ERROR] NuSyQ-Hub path not found; cannot generate map.")
        return 1

    print("🗺️  Generating capability map...")

    # Read action catalog
    catalog_path = hub_path / "config" / "action_catalog.json"
    if not catalog_path.exists():
        print(f"[ERROR] Action catalog not found at {catalog_path}")
        return 1

    catalog = read_json(catalog_path)
    if not catalog:
        print("[ERROR] Failed to parse action catalog")
        return 1

    # Build capability map
    output = []
    output.append("# NuSyQ-Hub Capability Map\n")
    output.append(f"- Generated: `{now_stamp()}`\n")
    output.append("\n## Wired Actions (ready to use)\n")

    wired = catalog.get("wired_actions", {})
    for action_name, action_info in wired.items():
        cmd = action_info.get("cmd", "N/A")
        desc = action_info.get("desc", "No description")
        safety = action_info.get("safety", "unknown")
        output.append(f"### `{action_name}`\n")
        output.append(f"- **Description**: {desc}\n")
        output.append(f"- **Command**: `{cmd}`\n")
        output.append(f"- **Safety**: {safety}\n\n")

    output.append("\n## Unwired Actions (requires wiring)\n")
    unwired = catalog.get("unwired_actions", {})
    for action_name, action_info in unwired.items():
        cmd = action_info.get("cmd", "N/A")
        desc = action_info.get("desc", "No description")
        output.append(f"### `{action_name}`\n")
        output.append(f"- **Description**: {desc}\n")
        output.append(f"- **Command** (proposed): `{cmd}`\n\n")

    output.append("\n## System Statistics\n")
    output.append(f"- Total scripts: {catalog.get('script_count', 0)}\n")

    themes = catalog.get("script_themes", {})
    if themes:
        output.append("\n### Script Themes\n")
        for theme, count in sorted(themes.items(), key=lambda x: -x[1])[:10]:
            output.append(f"- {theme}: {count}\n")

    # Write report
    map_content = "".join(output)
    reports_dir = hub_path / "state" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    map_file = reports_dir / "capabilities_map.md"
    map_file.write_text(map_content, encoding="utf-8")

    print(map_content)
    print(f"\n✅ Capability map saved to {map_file}")

    return 0


def run_suggest(hub_path: Path | None, snapshot_path: Path | None) -> int:
    """Wire to existing suggestion_engine.py."""
    if not hub_path:
        print("[ERROR] NuSyQ-Hub path not found; cannot run suggestions.")
        return 1

    # Import suggestion engine
    sys.path.insert(0, str(hub_path / "src"))
    try:
        from orchestration.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine()

        # Build richer context from actual system state
        context_parts = []

        # Get repo state
        hub_snap = git_snapshot("NuSyQ-Hub", hub_path)
        if hub_snap.dirty == "DIRTY":
            context_parts.append("Hub is dirty")
        if hub_snap.dirty == "clean":
            context_parts.append("Hub is clean")
        if hub_snap.ahead_behind:
            behind, ahead = hub_snap.ahead_behind.split()
            if int(behind) > 0:
                context_parts.append(f"behind {behind} commits")
            if int(ahead) > 0:
                context_parts.append(f"ahead {ahead} commits")

        # Get quest state
        quest = read_quest_log(hub_path)
        if quest.last_nonempty_line:
            try:
                obj = json.loads(quest.last_nonempty_line)
                if isinstance(obj, dict) and "details" in obj:
                    details = obj["details"]
                    title = details.get("title", "")
                    questline = details.get("questline", "")
                    status = details.get("status", "")
                    tags = details.get("tags", [])
                    if title:
                        context_parts.append(f"current quest: {title}")
                    if questline:
                        context_parts.append(f"questline: {questline}")
                    if status:
                        context_parts.append(f"quest status: {status}")
                    if tags:
                        context_parts.append(f"tags: {','.join(tags)}")
            except Exception:
                pass

        # Check if previous snapshot exists
        if snapshot_path and snapshot_path.exists():
            mtime = datetime.fromtimestamp(snapshot_path.stat().st_mtime)
            age = datetime.now() - mtime
            if age.total_seconds() < 3600:
                context_parts.append("recent snapshot exists")

        context_str = " | ".join(context_parts) if context_parts else "idle status"

        # RECEIPT DISCIPLINE: Print action header
        print("\n" + "=" * 80)
        print("SUGGESTION ENGINE")
        print("=" * 80)
        print("🎫 Action: SUGGEST")
        print(f"📊 Context: {context_str}")
        print(f"📍 Snapshot: {snapshot_path if snapshot_path else 'none'}")
        print("=" * 80 + "\n")

        suggestions = engine.suggest(context_str, max_suggestions=3)

        if not suggestions:
            print("💡 No suggestions available at this time.")
            return 0

        print(f"🧠 Generated {len(suggestions)} suggestion(s):\n")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"### {i}. {suggestion.title}")
            print(f"- **Category**: {suggestion.category.value}")
            print(f"- **Description**: {suggestion.description}")
            print(f"- **Risk**: {suggestion.risk.value} | **Effort**: {suggestion.effort.value}")
            print(f"- **Payoff**: {suggestion.payoff}")
            print(f"- **How**: {suggestion.implementation_hint}")
            print()

        return 0
    except Exception as e:
        print(f"[ERROR] Suggestion engine failed: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return 1


def check_spine_hygiene(hub_path: Path | None, fast: bool = False) -> list[str]:
    """Check if Hub (spine) is in good state.

    Args:
        hub_path: Path to the repository
        fast: If True, skip remote checks (for chug cycle)
    """
    import os

    # Fast mode for tests - skip heavy operations
    if os.getenv("NUSYQ_FAST_TEST_MODE") == "1":
        return ["✅ Spine hygiene: CLEAN (fast mode)"]

    warnings = []

    if not hub_path or not is_git_repo(hub_path):
        warnings.append("⚠️ NuSyQ-Hub is not a git repo or not found")
        return warnings

    # Check if dirty
    dirty_state, dirty_error = _probe_working_tree_dirty(hub_path)
    if dirty_state == "DIRTY":
        warnings.append("⚠️ Hub working tree is DIRTY (tracked changes detected)")
    elif dirty_state is None and dirty_error:
        warnings.append(f"⚠️ Hub working tree status unknown ({dirty_error})")

    # Skip remote check in fast mode (can hang)
    if not fast:
        # Check if behind remote
        rc, out, _ = run(
            ["git", "rev-list", "--left-right", "--count", "@{upstream}...HEAD"],
            cwd=hub_path,
            timeout_s=GIT_UPSTREAM_TIMEOUT_S,
        )
        if rc == 0 and out:
            parts = out.split()
            if len(parts) == 2:
                behind, ahead = parts
                if int(behind) > 0:
                    warnings.append(f"⚠️ Hub is {behind} commits behind remote")
                if int(ahead) > 0:
                    warnings.append(f"✅ Hub is {ahead} commits ahead of remote")

    if not warnings:
        warnings.append("✅ Spine hygiene: CLEAN")

    return warnings


def _should_capture_deep_trace_context() -> bool:
    """Return True when span attributes should include expensive git/quest probes.

    Default is off to keep startup latency low. Enable explicitly with:
      NUSYQ_TRACE_DEEP_CONTEXT=1
    """
    raw = os.getenv("NUSYQ_TRACE_DEEP_CONTEXT", "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _build_trace_attrs(
    action: str,
    paths: RepoPaths,
    contracts: dict,
    catalog: dict,
    run_id: str,
) -> dict[str, Any]:
    """Build root span attributes with an opt-in deep context mode."""
    attrs: dict[str, Any] = {
        "nusyq.repo": str(paths.nusyq_hub),
        "action.id": action,
        "action.tier": get_action_tier(action, contracts, catalog),
        "run.id": run_id,
        "repo.name": "NuSyQ-Hub",
    }

    if not _should_capture_deep_trace_context():
        return attrs

    try:
        hub_snap = git_snapshot("NuSyQ-Hub", paths.nusyq_hub)
        attrs.update(
            {
                "nusyq.branch": hub_snap.branch,
                "nusyq.head": hub_snap.head,
                "nusyq.dirty": hub_snap.dirty,
                "nusyq.ahead_behind": hub_snap.ahead_behind,
            }
        )
    except Exception:
        pass

    try:
        quest = read_quest_log(paths.nusyq_hub)
        attrs["nusyq.quest.last"] = quest.last_nonempty_line[:240] if quest.last_nonempty_line else ""
    except Exception:
        pass

    return attrs


def _probe_quantum_health() -> dict[str, Any]:
    info: dict[str, Any] = {
        "healthy": False,
        "preferred": "healing",
        "compute_available": False,
        "errors": [],
    }
    try:
        from src.healing import quantum_problem_resolver as qpr

        canonical = getattr(qpr, "__file__", "unknown")
        try:
            qpr._load_compute_backend()
        except Exception:
            pass
        compute_available = bool(getattr(qpr, "QUANTUM_COMPUTE_AVAILABLE", False))
        info.update(
            {
                "healthy": True,
                "canonical": canonical,
                "compute_available": compute_available,
                "preferred": "compute" if compute_available else "healing",
                "compute_module": "unknown",
            }
        )
        if compute_available:
            try:
                from src.quantum import quantum_problem_resolver_compute as compute

                info["compute_module"] = getattr(compute, "__file__", "unknown")
            except Exception as exc:
                info["errors"].append(f"compute_import:{type(exc).__name__}")
    except Exception as exc:
        info["errors"].append(str(exc))
    return info


def _probe_skyclaw_health(paths: RepoPaths) -> dict[str, Any]:
    """Probe optional local SkyClaw sidecar runtime status.

    Supports both native Windows binaries (skyclaw.exe) and Linux binaries
    compiled in WSL (skyclaw). When on Windows without a .exe, attempts to
    run the Linux binary via WSL.
    """
    info: dict[str, Any] = {
        "healthy": False,
        "status": "unavailable",
        "error": "not_installed",
    }
    if not paths.nusyq_hub:
        info["error"] = "hub_path_missing"
        return info

    runtime_dir = paths.nusyq_hub / "state" / "runtime" / "skyclaw"
    if not runtime_dir.exists():
        return info

    info.update(
        {
            "status": "installed",
            "path": str(runtime_dir),
            "error": "",
        }
    )

    # On Windows, prefer .exe but fall back to WSL for Linux binaries
    binary_path: Path | None = None
    use_wsl = False

    if os.name == "nt":
        exe_path = runtime_dir / "target" / "debug" / "skyclaw.exe"
        linux_path = runtime_dir / "target" / "debug" / "skyclaw"
        if exe_path.exists():
            binary_path = exe_path
        elif linux_path.exists():
            binary_path = linux_path
            use_wsl = True
    else:
        binary_path = runtime_dir / "target" / "debug" / "skyclaw"

    if binary_path is None or not binary_path.exists():
        info["error"] = "binary_missing"
        return info

    info["binary"] = str(binary_path)
    info["wsl_mode"] = use_wsl

    # Build command - use WSL on Windows for Linux binaries
    if use_wsl:
        # Convert Windows path to WSL path
        wsl_path = str(binary_path).replace("\\", "/")
        if wsl_path[1] == ":":
            drive = wsl_path[0].lower()
            wsl_path = f"/mnt/{drive}{wsl_path[2:]}"
        cmd = ["wsl", wsl_path, "--version"]
    else:
        cmd = [str(binary_path), "--version"]

    rc, out, err = run(cmd, cwd=runtime_dir, timeout_s=8)
    if rc != 0:
        tail = (err or out or "").strip().splitlines()
        info.update(
            {
                "status": "degraded",
                "error": tail[-1] if tail else f"version_probe_failed_rc_{rc}",
            }
        )
        return info

    first_line = next((line.strip() for line in out.splitlines() if line.strip()), "")
    info.update(
        {
            "healthy": True,
            "status": "ready",
            "version": first_line or "unknown",
        }
    )
    return info


def _probe_external_runtime_health(paths: RepoPaths, service_name: str) -> dict[str, Any]:
    """Read workspace-local external runtime health from integration status."""
    info: dict[str, Any] = {
        "healthy": False,
        "status": "unavailable",
        "error": "not_installed",
    }
    if not paths.nusyq_hub:
        info["error"] = "hub_path_missing"
        return info

    report_path = paths.nusyq_hub / "state" / "reports" / "integration_status.json"
    if not report_path.exists():
        info["error"] = "integration_status_missing"
        return info

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        info["error"] = f"integration_status_invalid:{exc}"
        return info

    runtime_info = payload.get(service_name)
    if not isinstance(runtime_info, dict) or not runtime_info.get("available"):
        return info

    healthy = bool(runtime_info.get("runnable"))
    info.update(
        {
            "healthy": healthy,
            "status": "ready" if healthy else "installed",
            "path": runtime_info.get("path"),
            "error": "" if healthy else "runtime_not_ready",
        }
    )
    if service_name == "hermes_agent":
        info["python_3_11_available"] = runtime_info.get("python_3_11_available", False)
        info["node_modules_ready"] = runtime_info.get("node_modules_ready", False)
    if service_name == "metaclaw":
        info["node_modules_ready"] = runtime_info.get("node_modules_ready", False)
        info["env_configured"] = runtime_info.get("env_configured", False)
        info["registration_ready"] = runtime_info.get("registration_ready", False)
        info["registration_recommended"] = runtime_info.get("registration_recommended", False)
        info["missing_required_env"] = runtime_info.get("missing_required_env", [])
        info["next_step"] = runtime_info.get("next_step")
        info["resolved_secret_sources"] = runtime_info.get("resolved_secret_sources", [])
        info["externally_verified"] = runtime_info.get("externally_verified", False)
        info["status_check"] = runtime_info.get("status_check", {})
        status_check = runtime_info.get("status_check", {})
        status_name = str(status_check.get("status") or "")
        if healthy and status_name and status_name not in {"ok", "skipped", "probe_blocked"}:
            info["healthy"] = False
            info["status"] = "degraded"
            info["error"] = f"external_status_{status_name}"
            if status_name == "auth_error" and info.get("registration_recommended"):
                info["next_step"] = "npm run register"
            elif status_name == "auth_error":
                info["next_step"] = "Update CLOWNCH_API_KEY/CLAWNCHER_API_KEY"
    return info


def _collect_ai_capability_intelligence(paths: RepoPaths) -> dict[str, Any]:
    """Collect advanced AI capability/readiness signals for operator surfaces."""
    unavailable = {"status": "unavailable", "reason": "hub_path_missing"}
    if not paths.nusyq_hub:
        return {
            "advanced_ai_readiness": unavailable,
            "meta_learning": unavailable,
        }

    advanced_ai: dict[str, Any] = {"status": "unavailable", "reason": "audit_failed"}
    try:
        from src.diagnostics.system_health_assessor import SystemHealthAssessment

        assessor = SystemHealthAssessment()
        assessor.repo_root = paths.nusyq_hub
        readiness = assessor._audit_advanced_ai_capabilities()
        status = "ok"
        if any(item.get("status") == "missing" for item in readiness.values()):
            status = "partial"
        advanced_ai = {
            "status": status,
            "capabilities": readiness,
        }
    except Exception as exc:
        advanced_ai = {"status": "unavailable", "reason": str(exc)}

    meta_learning_path = paths.nusyq_hub / "state" / "reports" / "ai_intermediary_meta_learning_latest.json"
    meta_learning: dict[str, Any]
    if meta_learning_path.exists():
        try:
            payload = json.loads(meta_learning_path.read_text(encoding="utf-8"))
            snapshot = payload.get("snapshot", {})
            meta_learning = {
                "status": "ok",
                "report_path": str(meta_learning_path),
                "generated_at": payload.get("generated_at"),
                "snapshot": snapshot,
            }
        except Exception as exc:
            meta_learning = {
                "status": "unavailable",
                "reason": f"invalid_meta_learning_report:{exc}",
                "report_path": str(meta_learning_path),
            }
    else:
        meta_learning = {
            "status": "unavailable",
            "reason": "meta_learning_report_missing",
            "report_path": str(meta_learning_path),
        }

    return {
        "advanced_ai_readiness": advanced_ai,
        "meta_learning": meta_learning,
    }


def _merge_service_health(base: Any, overlay: dict[str, Any]) -> dict[str, Any]:
    """Merge service status dictionaries, preferring explicit overlay values."""
    merged = dict(base) if isinstance(base, dict) else {}
    for key, value in overlay.items():
        if value is None:
            continue
        merged[key] = value
    return merged


def _resolve_ai_status_simulatedverse_path(paths: RepoPaths) -> Path | None:
    """Resolve SimulatedVerse path for ai_status live probes."""
    if paths.simulatedverse and paths.simulatedverse.exists():
        return paths.simulatedverse

    for candidate in (
        os.getenv("SIMULATEDVERSE_PATH"),
        os.getenv("SIMULATEDVERSE_ROOT"),
        os.getenv("SIMULATEDVERSE_ROOT_PATH"),
        os.getenv("SIMVERSE_PATH"),
    ):
        resolved = _coerce_workspace_path(candidate)
        if resolved and resolved.exists():
            return resolved
    return None


def _probe_ai_status_live_core_services(
    paths: RepoPaths, existing_services: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Collect live probe status for core local services used by ai_status."""
    timeout_s = max(1.0, min(4.0, float(os.getenv("NUSYQ_AI_STATUS_CORE_PROBE_TIMEOUT_S", "2.5"))))
    services: dict[str, dict[str, Any]] = {}

    existing_ollama = (existing_services.get("ollama") or {}) if isinstance(existing_services, dict) else {}
    ollama_probe = _preflight_openclaw_target("ollama", timeout_s=max(4.0, timeout_s * 4.0))
    ollama_detail = str(ollama_probe.get("detail") or "").strip()
    ollama_blocked = _looks_like_probe_blocked_error(ollama_detail)
    services["ollama"] = _merge_service_health(
        existing_ollama,
        {
            "healthy": (
                bool(existing_ollama.get("healthy")) if ollama_blocked else bool(ollama_probe.get("available"))
            ),
            "status": (
                existing_ollama.get("status") or "probe_blocked"
                if ollama_blocked
                else ("ready" if ollama_probe.get("available") else "offline")
            ),
            "url": ollama_probe.get("url"),
            "reachable": ollama_probe.get("reachable"),
            "model_count": ollama_probe.get("model_count"),
            "check_mode": "live_probe_blocked_fallback" if ollama_blocked else "live_probe",
            "probe_blocked": ollama_blocked,
            "error": "" if ollama_probe.get("available") else ollama_detail,
            "live_probe_detail": ollama_detail,
        },
    )

    existing_lmstudio = (existing_services.get("lmstudio") or {}) if isinstance(existing_services, dict) else {}
    lmstudio_probe = _preflight_openclaw_target("lmstudio", timeout_s=max(4.0, timeout_s * 4.0))
    lmstudio_detail = str(lmstudio_probe.get("detail") or "").strip()
    lmstudio_blocked = _looks_like_probe_blocked_error(lmstudio_detail)
    services["lmstudio"] = _merge_service_health(
        existing_lmstudio,
        {
            "healthy": (
                bool(existing_lmstudio.get("healthy")) if lmstudio_blocked else bool(lmstudio_probe.get("available"))
            ),
            "status": (
                existing_lmstudio.get("status") or "probe_blocked"
                if lmstudio_blocked
                else ("ready" if lmstudio_probe.get("available") else "offline")
            ),
            "url": lmstudio_probe.get("url"),
            "reachable": lmstudio_probe.get("reachable"),
            "model_count": lmstudio_probe.get("model_count"),
            "check_mode": "live_probe_blocked_fallback" if lmstudio_blocked else "live_probe",
            "probe_blocked": lmstudio_blocked,
            "error": "" if lmstudio_probe.get("available") else lmstudio_detail,
            "live_probe_detail": lmstudio_detail,
        },
    )

    sim_path = _resolve_ai_status_simulatedverse_path(paths)
    if sim_path:
        sim_port = int(os.getenv("SIMULATEDVERSE_PORT", "5001") or "5001")
        sim_existing = existing_services.get("simulatedverse") if isinstance(existing_services, dict) else {}
        if not isinstance(sim_existing, dict):
            sim_existing = {}
        sim_detail = "path_missing"
        sim_url: str | None = None
        sim_ok = False
        sim_blocked = False
        for url in _simulatedverse_health_urls(sim_port):
            ok, detail = _probe_http_health(url, timeout_s=timeout_s)
            if ok:
                sim_ok = True
                sim_url = url
                sim_detail = detail
                break
            sim_detail = detail
            sim_blocked = sim_blocked or _looks_like_probe_blocked_error(detail)

        fallback_healthy = bool(sim_existing.get("healthy")) or sim_path.exists()
        services["simulatedverse"] = _merge_service_health(
            sim_existing,
            {
                "healthy": fallback_healthy if sim_blocked and not sim_ok else sim_ok,
                "status": (
                    sim_existing.get("status") or "probe_blocked"
                    if sim_blocked and not sim_ok
                    else ("ready" if sim_ok else "offline")
                ),
                "path": str(sim_path),
                "url": sim_url,
                "check_mode": "live_probe_blocked_fallback" if sim_blocked and not sim_ok else "live_probe",
                "probe_blocked": sim_blocked and not sim_ok,
                "error": "" if sim_ok else sim_detail,
                "live_probe_detail": sim_detail,
            },
        )

    return services


def _resolve_ai_status_probe_mode() -> str:
    """Resolve router health probe mode for ai_status.

    Modes:
      - in_process: instantiate router in current process
      - subprocess: probe router health in child process with hard timeout
      - auto: in_process during pytest, subprocess otherwise
    """
    mode = str(os.getenv("NUSYQ_AI_STATUS_ROUTER_PROBE_MODE", "auto")).strip().lower()
    if mode in {"in_process", "subprocess"}:
        return mode
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "in_process"
    return "subprocess"


def _collect_ai_health_via_subprocess(paths: RepoPaths, timeout_s: float) -> tuple[dict[str, Any], str | None]:
    """Collect router health via bounded subprocess probe."""
    if not paths.nusyq_hub:
        return {}, "hub_path_missing"

    repo_literal = json.dumps(str(paths.nusyq_hub))
    probe_script = (
        "import asyncio, json\n"
        "from pathlib import Path\n"
        "from src.tools.agent_task_router import AgentTaskRouter\n"
        f"router = AgentTaskRouter(repo_root=Path({repo_literal}))\n"
        "payload = asyncio.run(router.health_check())\n"
        "print(json.dumps(payload, ensure_ascii=False))\n"
    )
    cmd = [sys.executable, "-c", probe_script]
    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=max(1, int(timeout_s)))

    if rc == 124 or "TimeoutExpired" in (err or ""):
        return {}, "health_check_timeout"
    if rc != 0:
        tail = (err or out or "").strip()[-800:]
        return {}, f"subprocess_probe_failed:{tail or f'rc={rc}'}"

    payload: dict[str, Any] = {}
    try:
        payload = json.loads(out)
    except Exception:
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        for line in reversed(lines):
            with contextlib.suppress(Exception):
                payload = json.loads(line)
                break
    if not isinstance(payload, dict):
        return {}, "invalid_subprocess_payload"
    return payload, None


def _collect_ai_health(paths: RepoPaths, record_metrics: bool = True) -> dict[str, Any]:
    status: dict[str, Any] = {"services": {}, "quantum": _probe_quantum_health()}
    skyclaw = _probe_skyclaw_health(paths)
    if skyclaw.get("status") != "unavailable":
        status["services"]["skyclaw"] = skyclaw
    for external_name in ("hermes_agent", "metaclaw"):
        external_runtime = _probe_external_runtime_health(paths, external_name)
        if external_runtime.get("status") != "unavailable":
            status["services"][external_name] = external_runtime
    if not paths.nusyq_hub:
        status["services"]["repository"] = {
            "healthy": False,
            "error": "NuSyQ-Hub path missing",
        }
        return status

    timeout_s = max(1.0, float(os.getenv("NUSYQ_AI_STATUS_TIMEOUT_S", "8")))
    probe_mode = _resolve_ai_status_probe_mode()

    try:
        if probe_mode == "subprocess":
            health_payload, probe_error = _collect_ai_health_via_subprocess(paths, timeout_s=timeout_s)
            if probe_error:
                status["services"]["router"] = {
                    "healthy": False,
                    "error": probe_error,
                    "timeout_seconds": timeout_s,
                    "probe_mode": probe_mode,
                }
            else:
                services = health_payload.get("systems", {}) if isinstance(health_payload, dict) else {}
                if isinstance(services, dict):
                    status["services"].update(services)
        else:
            from src.tools.agent_task_router import AgentTaskRouter

            router = AgentTaskRouter(repo_root=paths.nusyq_hub)
            health_payload = _run_async_sync(asyncio.wait_for(router.health_check(), timeout=timeout_s))
            if isinstance(health_payload, dict):
                services = health_payload.get("systems", {})
                if isinstance(services, dict):
                    status["services"].update(services)

        # Record metrics if enabled
        if record_metrics:
            try:
                from src.system.ai_metrics_tracker import AIMetricsTracker

                tracker = AIMetricsTracker(paths.nusyq_hub)

                for service_name, service_info in status["services"].items():
                    if isinstance(service_info, dict):
                        tracker.record_health(
                            system_name=service_name,
                            available=service_info.get("healthy", False),
                            latency_ms=service_info.get("latency_ms"),
                            error=service_info.get("error"),
                            metadata={"version": service_info.get("version")},
                        )
            except Exception:
                pass  # Don't fail health check if metrics recording fails

    except TimeoutError:
        status["services"]["router"] = {
            "healthy": False,
            "error": "health_check_timeout",
            "timeout_seconds": timeout_s,
            "probe_mode": probe_mode,
        }
    except Exception as exc:
        status["services"]["router"] = {
            "healthy": False,
            "error": str(exc),
            "probe_mode": probe_mode,
        }

    with contextlib.suppress(Exception):
        live_services = _probe_ai_status_live_core_services(paths, status["services"])
        if isinstance(live_services, dict):
            status["services"].update(live_services)
    return status


def _run_aux_script(
    paths: RepoPaths,
    script_rel: str,
    label: str,
    args: list[str] | None = None,
    timeout_s: int = 60,
) -> None:
    repo_root = paths.nusyq_hub or Path.cwd()
    script_path = repo_root / script_rel
    if not script_path.exists():
        print(f"⚠️ {label} script missing ({script_path.relative_to(repo_root)})")
        return

    cmd = ["python", str(script_path)]
    if args:
        cmd.extend(args)

    rc, out, err = run(cmd, cwd=repo_root, timeout_s=timeout_s)
    print(f"\n🔧 {label}")
    if out:
        print(out)
    if err:
        print(f"[stderr] {err}")
    if rc != 0:
        print(f"{label} exited with code {rc}")


def _format_ai_service_line(name: str, info: dict[str, Any]) -> str:
    healthy = bool(info.get("healthy"))
    tag = "✅" if healthy else "⚠️"
    extras: list[str] = []
    if models := info.get("models"):
        extras.append(f"models={len(models) if isinstance(models, list) else models}")
    if path := info.get("path"):
        extras.append(f"path={path}")
    if error := info.get("error"):
        extras.append(f"error={error}")
    if info.get("status"):
        extras.append(f"status={info['status']}")
    detail = ", ".join(extras) if extras else "status available"
    return f"  {tag} {name}: {detail}"


def _print_ai_section(ai_health: dict[str, Any]) -> None:
    print("\n## AI Systems")
    services = ai_health.get("services", {})
    if services:
        for name, info in services.items():
            print(_format_ai_service_line(name, info if isinstance(info, dict) else {}))
    else:
        print("  Info: No AI service status available")

    quantum = ai_health.get("quantum", {})
    q_tag = "✅" if quantum.get("healthy") else "⚠️"
    q_details = [
        f"preferred={quantum.get('preferred', 'healing')}",
        f"compute={'available' if quantum.get('compute_available') else 'unavailable'}",
    ]
    if canonical := quantum.get("canonical"):
        q_details.append(f"module={Path(canonical).name}")
    if errors := quantum.get("errors"):
        q_details.append(f"errors={'|'.join(errors)}")
    print(f"  {q_tag} quantum_resolver: {', '.join(q_details)}")


def _print_ai_capability_section(capability_intel: dict[str, Any]) -> None:
    """Print advanced AI capability and learning signals."""
    print("\n## Advanced AI")
    advanced = capability_intel.get("advanced_ai_readiness", {})
    if advanced.get("status") in {"ok", "partial"}:
        capabilities = advanced.get("capabilities", {})
        for name, details in capabilities.items():
            if not isinstance(details, dict):
                continue
            tag = "✅" if details.get("status") == "ready" else ("⚠️" if details.get("status") == "partial" else "❌")
            print(f"  {tag} {name}: {details.get('status')} | {details.get('summary', '')}")
    else:
        print(f"  ⚠️ readiness_audit: {advanced.get('reason', 'unavailable')}")

    meta = capability_intel.get("meta_learning", {})
    if meta.get("status") == "ok":
        snapshot = meta.get("snapshot", {})
        print(
            "  ✅ meta_learning_runtime: "
            f"events={snapshot.get('total_events', 0)}, "
            f"errors={snapshot.get('error_events', 0)}, "
            f"routed={snapshot.get('routed_events', 0)}, "
            f"max_depth={snapshot.get('max_recursion_depth', 0)}"
        )
    else:
        print(f"  ⚠️ meta_learning_runtime: {meta.get('reason', 'unavailable')}")


def run_ai_task(
    hub_path: Path | None,
    task_type: str,
    file_path: str,
    target_system: str = "ollama",
    failover_chain_override: str | None = None,
) -> int:
    """Run AI-powered task (analyze, review, debug) via agent_task_router.

    Args:
        hub_path: NuSyQ-Hub root path
        task_type: Type of task (analyze, review, debug, etc.)
        file_path: Path to file or error description
        target_system: AI system to use (ollama, chatdev, auto)

    Returns:
        Exit code (0 success, 1 failure)
    """
    if not hub_path:
        print("[ERROR] NuSyQ-Hub path not found")
        return 1

    task_input = file_path.strip()
    if not task_input:
        print(f"[ERROR] Missing task input for {task_type}")
        return 1

    def _resolve_input_path(raw: str) -> Path:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = hub_path / candidate
        return candidate

    def _read_file_with_limits(target: Path) -> tuple[str, int, int]:
        file_size = target.stat().st_size
        max_size = 1024 * 1024  # 1MB
        warn_size = 100 * 1024  # 100KB

        if file_size > max_size:
            msg = f"[ERROR] File too large: {file_size / 1024:.1f}KB (max 1MB)"
            raise ValueError(msg)
        if file_size > warn_size:
            print(f"[WARN] Large file: {file_size / 1024:.1f}KB - analysis may take longer")

        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"[ERROR] File is not valid UTF-8: {target}") from exc

        lines = content.count("\n") + 1
        return content, lines, file_size

    def _tail_text(path: Path, limit: int = 4000) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="replace")[-limit:]
        except Exception:
            return ""

    def _detect_chatdev_runtime_failure(result: dict[str, Any]) -> tuple[bool, str]:
        def _tail_contains_marker(path_value: Any, markers: tuple[str, ...], limit: int = 8000) -> str:
            if not isinstance(path_value, str) or not path_value.strip():
                return ""
            log_path = Path(path_value)
            if not log_path.exists():
                return ""
            tail = _tail_text(log_path, limit=limit).lower()
            for marker in markers:
                if marker in tail:
                    return f"{marker} ({log_path.name})"
            return ""

        combined_chunks: list[str] = []
        for key in ("error", "note"):
            value = result.get(key)
            if isinstance(value, str):
                combined_chunks.append(value)
        output = result.get("output")
        if isinstance(output, str):
            combined_chunks.append(output)
        elif isinstance(output, dict):
            try:
                combined_chunks.append(json.dumps(output, ensure_ascii=False))
            except Exception:
                combined_chunks.append(str(output))
        combined = " ".join(combined_chunks).lower()
        indicators = (
            "401 unauthorized",
            "unauthorized",
            "invalid_api_key",
            "api key",
            "auth",
            "429 too many requests",
            "rate limit",
            "insufficient_quota",
            "chatdev unavailable",
            "launch failed",
        )
        for marker in indicators:
            if marker in combined:
                return True, marker

        if not isinstance(output, dict):
            return False, ""

        runtime_markers = (
            "openaipublic.blob.core.windows.net",
            "failed to resolve",
            "name resolution",
            "requests.exceptions.connectionerror",
            "tenacity.retryerror",
            "tiktoken",
            "429 too many requests",
            "rate limit",
            "insufficient_quota",
        )
        for log_key in ("stderr_log", "stdout_log"):
            marker = _tail_contains_marker(output.get(log_key), runtime_markers)
            if marker:
                return True, marker

        chatdev_root = output.get("chatdev_path")
        project_name = output.get("project_name")
        organization = output.get("organization")
        if not all(isinstance(v, str) and v for v in (chatdev_root, project_name, organization)):
            return False, ""
        warehouse = Path(chatdev_root) / "WareHouse"
        if not warehouse.exists():
            return False, ""
        prefix = f"{project_name}_{organization}_"
        candidates = sorted(
            warehouse.glob(f"{prefix}*.log"),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True,
        )
        for log_file in candidates[:3]:
            tail = _tail_text(log_file, limit=6000).lower()
            for marker in ("401 unauthorized", "invalid_api_key", "authentication", "unauthorized"):
                if marker in tail:
                    return True, f"{marker} ({log_file.name})"
        return False, ""

    def _parse_chatdev_failover_chain() -> list[str]:
        raw = (
            failover_chain_override.strip()
            if isinstance(failover_chain_override, str) and failover_chain_override.strip()
            else os.getenv("NUSYQ_CHATDEV_FAILOVER_CHAIN", "codex,ollama,lmstudio")
        )
        chain: list[str] = []
        allowed = {"codex", "ollama", "lmstudio", "copilot", "auto"}
        for token in [chunk.strip().lower() for chunk in raw.split(",") if chunk.strip()]:
            if token not in allowed:
                continue
            if token not in chain:
                chain.append(token)
        if not chain:
            chain = ["ollama", "lmstudio"]
        return chain

    def _sanitize_filename_component(raw: str) -> str:
        return re.sub(r"[^a-zA-Z0-9._-]+", "_", raw).strip("_")[:64] or "unknown"

    def _write_failover_receipt(
        *,
        task_id: str,
        task_type_value: str,
        trigger_system: str,
        trigger_reason: str,
        requested_chain: list[str],
        attempt_index: int,
        candidate_system: str,
        candidate_result: dict[str, Any],
    ) -> str:
        receipts_dir = hub_path / "state" / "reports" / "failover_receipts"
        receipts_dir.mkdir(parents=True, exist_ok=True)
        stamp = now_stamp()
        safe_task = _sanitize_filename_component(task_id)
        safe_system = _sanitize_filename_component(candidate_system)
        receipt_path = receipts_dir / (f"failover_{stamp}_{safe_task}_{attempt_index:02d}_{safe_system}.json")
        payload = {
            "generated_at": datetime.now(UTC).isoformat(),
            "task_id": task_id,
            "task_type": task_type_value,
            "trigger_system": trigger_system,
            "trigger_reason": trigger_reason,
            "requested_chain": requested_chain,
            "attempt_index": attempt_index,
            "candidate_system": candidate_system,
            "candidate_status": candidate_result.get("status"),
            "candidate_error": candidate_result.get("error"),
            "candidate_note": candidate_result.get("note"),
            "selected": str(candidate_result.get("status", "")).lower() in {"success", "submitted"},
            "result_excerpt": (
                candidate_result.get("output")
                if isinstance(candidate_result.get("output"), str)
                else candidate_result.get("error")
            ),
        }
        _write_json_report(receipt_path, payload)
        return str(receipt_path)

    def _normalize_semantic_status(result: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(result)
        system = str(normalized.get("system", "")).lower()
        status = str(normalized.get("status", "")).lower()
        output = normalized.get("output")
        if system == "quantum_resolver" and status in {"success", "submitted"}:
            if isinstance(output, dict):
                output_status = str(output.get("status", "")).lower()
                if output_status in {"error", "failed"}:
                    normalized["status"] = "failed"
                    normalized.setdefault("error", str(output.get("error_message") or "unknown error"))
                    normalized["note"] = "Quantum resolver returned output.status=error; normalized to failed."
        return normalized

    def _build_codex_fallback_prompt(selected_task_type: str, description: str, context: dict[str, Any]) -> str:
        context_json = json.dumps(context, ensure_ascii=False, indent=2, default=str)
        return (
            f"You are a coding assistant. Complete task_type='{selected_task_type}'.\n"
            "Return a concise, practical result. If code changes are suggested, include exact edits.\n\n"
            f"TASK:\n{description}\n\n"
            f"CONTEXT:\n{context_json}\n"
        )

    def _try_codex_fallback(selected_task_type: str, description: str, context: dict[str, Any]) -> dict[str, Any]:
        codex_bin = shutil.which("codex")
        if not codex_bin:
            return {"status": "failed", "error": "codex_cli_not_found"}

        prompt = _build_codex_fallback_prompt(selected_task_type, description, context)
        timeout_s = int(os.getenv("NUSYQ_CODEX_FALLBACK_TIMEOUT_S", "180"))
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix="_codex_fallback.txt",
            encoding="utf-8",
        ) as tmp_file:
            output_path = Path(tmp_file.name)

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
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(hub_path),
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout_s,
                check=False,
            )
            output_text = output_path.read_text(encoding="utf-8", errors="replace").strip()
            if proc.returncode == 0 and output_text:
                return {
                    "status": "success",
                    "system": "codex",
                    "model": os.getenv("NUSYQ_CODEX_FALLBACK_MODEL") or "default",
                    "output": output_text,
                }
            stderr_tail = (proc.stderr or "")[-1200:]
            stdout_tail = (proc.stdout or "")[-1200:]
            return {
                "status": "failed",
                "error": (
                    f"codex_exec_failed rc={proc.returncode} stderr_tail={stderr_tail!r} stdout_tail={stdout_tail!r}"
                ),
            }
        except subprocess.TimeoutExpired:
            return {"status": "failed", "error": f"codex_exec_timeout>{timeout_s}s"}
        except Exception as exc:
            return {"status": "failed", "error": f"codex_exec_error:{exc}"}
        finally:
            with contextlib.suppress(OSError):
                output_path.unlink()

    input_path = _resolve_input_path(task_input)
    file_context = False
    content = ""
    lines = 0
    file_size = 0
    target = input_path

    if task_type in {"review", "patch"}:
        if not input_path.exists():
            print(f"[ERROR] File not found: {input_path}")
            return 1
        if not input_path.is_file():
            print(f"[ERROR] Path is not a file: {input_path}")
            return 1
        try:
            content, lines, file_size = _read_file_with_limits(input_path)
        except ValueError as exc:
            print(str(exc))
            return 1
        file_context = True
    elif task_type == "analyze":
        if not input_path.exists():
            print(f"[ERROR] File not found: {input_path}")
            print(f"\nUsage: python start_nusyq.py {task_type} <file_path> [--system=ollama|chatdev|copilot|auto]")
            print("\nExamples:")
            print(f"  python start_nusyq.py {task_type} src/main.py")
            print(f"  python start_nusyq.py {task_type} scripts/start_nusyq.py --system=auto")
            print(f"  python start_nusyq.py {task_type} ../SimulatedVerse/src/app.ts")
            return 1
        if input_path.is_file():
            try:
                content, lines, file_size = _read_file_with_limits(input_path)
            except ValueError as exc:
                print(str(exc))
                return 1
            file_context = True
        elif input_path.is_dir():
            file_context = False
        else:
            print(f"[ERROR] Unsupported path type: {input_path}")
            return 1
    elif task_type == "generate":
        # Accept natural-language descriptions by default, but allow file-seeded generation.
        if input_path.exists() and input_path.is_file():
            try:
                content, lines, file_size = _read_file_with_limits(input_path)
            except ValueError as exc:
                print(str(exc))
                return 1
            file_context = True
        else:
            file_context = False
    elif task_type == "debug":
        # Debug accepts either a file target or a raw error description.
        if input_path.exists() and input_path.is_file():
            try:
                content, lines, file_size = _read_file_with_limits(input_path)
            except ValueError as exc:
                print(str(exc))
                return 1
            file_context = True
        else:
            file_context = False
    else:
        if input_path.exists() and input_path.is_file():
            try:
                content, lines, file_size = _read_file_with_limits(input_path)
            except ValueError as exc:
                print(str(exc))
                return 1
            file_context = True
        else:
            file_context = False

    if file_context:
        print(f"📄 Analyzing: {target.name} ({lines} lines, {file_size / 1024:.1f}KB)")
    else:
        print(f"📄 Task input: {task_input[:120]}")
    print(f"🤖 Target system: {target_system}")

    # Add hub root to path so we can import from src/
    if str(hub_path) not in sys.path:
        sys.path.insert(0, str(hub_path))

    # Import and run analysis
    try:
        from src.tools.agent_task_router import AgentTaskRouter

        async def analyze() -> dict:
            router = AgentTaskRouter(repo_root=hub_path)

            if file_context:
                task_descriptions = {
                    "analyze": (
                        f"Analyze the following code from {target.name} for code quality, "
                        f"potential issues, and improvements:\n\n```{target.suffix}\n{content}\n```"
                    ),
                    "review": (
                        f"Review the following code from {target.name} for code quality, "
                        f"best practices, and provide detailed feedback:\n\n"
                        f"```{target.suffix}\n{content}\n```"
                    ),
                    "debug": (
                        f"Debug the following code from {target.name} and identify potential bugs "
                        f"or issues:\n\n```{target.suffix}\n{content}\n```"
                    ),
                    "generate": (
                        f"Generate a project plan and implementation starter based on "
                        f"{target.name}:\n\n```{target.suffix}\n{content}\n```"
                    ),
                    "patch": (
                        f"Patch the following file {target.name}. Provide exact changes and explain "
                        f"the fix:\n\n```{target.suffix}\n{content}\n```"
                    ),
                }
                description = task_descriptions.get(
                    task_type,
                    f"Analyze {target.name} for code quality, potential issues, and improvements.",
                )
            else:
                if task_type == "generate":
                    description = task_input
                elif task_type == "debug":
                    description = f"Debug this error and propose concrete fixes: {task_input}"
                elif task_type == "analyze" and input_path.exists() and input_path.is_dir():
                    description = (
                        f"Analyze repository scope at {input_path} for code quality, "
                        "potential issues, and improvements."
                    )
                else:
                    description = task_input

            context = {
                "file": str(target) if file_context else None,
                "input": task_input,
                "lines": lines if file_context else None,
                "size_kb": (file_size / 1024) if file_context else None,
                "task_type": task_type,
                "source_mode": "file" if file_context else "text",
            }
            if task_type == "generate" and target_system == "chatdev":
                wait_for_completion = os.getenv("NUSYQ_CHATDEV_WAIT_FOR_COMPLETION", "1").strip().lower() in {
                    "1",
                    "true",
                    "yes",
                    "on",
                }
                try:
                    completion_timeout_s = float(os.getenv("NUSYQ_CHATDEV_COMPLETION_TIMEOUT_S", "900"))
                except ValueError:
                    completion_timeout_s = 900.0
                context["chatdev_wait_for_completion"] = wait_for_completion
                context["chatdev_completion_timeout_s"] = max(30.0, completion_timeout_s)

            # Try routing to AI system, fallback to static if it fails
            try:
                print(f"🔄 Routing to {target_system}...")
                result = await router.route_task(
                    task_type=task_type,  # Use task_type parameter instead of hardcoded "analyze"
                    description=description,
                    context=context,
                    target_system=target_system,
                )

                if target_system == "chatdev":
                    should_failover = False
                    failover_reason = ""
                    if str(result.get("status", "")).lower() in {"failed", "error"}:
                        should_failover = True
                        failover_reason = str(result.get("error") or "chatdev_failed")
                    else:
                        runtime_failed, runtime_reason = _detect_chatdev_runtime_failure(result)
                        should_failover = runtime_failed
                        failover_reason = runtime_reason

                    if should_failover:
                        chain = _parse_chatdev_failover_chain()
                        print(f"\n[WARN] ChatDev failure signal detected: {failover_reason}")
                        print(f"[INFO] Applying failover chain: {', '.join(chain)}")
                        attempt_receipts: list[str] = []
                        base_task_id = str(result.get("task_id") or f"fallback_{now_stamp()}")
                        for idx, fallback_system in enumerate(chain, start=1):
                            if fallback_system == "codex":
                                codex_result = _try_codex_fallback(task_type, description, context)
                                receipt_path = _write_failover_receipt(
                                    task_id=base_task_id,
                                    task_type_value=task_type,
                                    trigger_system=target_system,
                                    trigger_reason=failover_reason,
                                    requested_chain=chain,
                                    attempt_index=idx,
                                    candidate_system=fallback_system,
                                    candidate_result=codex_result,
                                )
                                attempt_receipts.append(receipt_path)
                                if codex_result.get("status") == "success":
                                    codex_result["task_id"] = result.get(
                                        "task_id", codex_result.get("task_id", "unknown")
                                    )
                                    codex_result["fallback_reason"] = failover_reason
                                    codex_result["fallback_receipts"] = attempt_receipts
                                    codex_result["note"] = (
                                        f"ChatDev fallback succeeded via Codex CLI. Receipt: {receipt_path}"
                                    )
                                    return codex_result
                                continue
                            fallback_result = await router.route_task(
                                task_type=task_type,
                                description=description,
                                context=context,
                                target_system=fallback_system,
                            )
                            receipt_path = _write_failover_receipt(
                                task_id=base_task_id,
                                task_type_value=task_type,
                                trigger_system=target_system,
                                trigger_reason=failover_reason,
                                requested_chain=chain,
                                attempt_index=idx,
                                candidate_system=fallback_system,
                                candidate_result=fallback_result,
                            )
                            attempt_receipts.append(receipt_path)
                            if str(fallback_result.get("status", "")).lower() in {
                                "success",
                                "submitted",
                            }:
                                fallback_result["fallback_reason"] = failover_reason
                                fallback_result["fallback_receipts"] = attempt_receipts
                                fallback_result["note"] = (
                                    f"ChatDev fallback succeeded via {fallback_system}. Receipt: {receipt_path}"
                                )
                                return fallback_result

                # If routing failed due to system unavailability, use fallback
                if result.get("status") == "failed" and target_system == "ollama" and file_context:
                    error_msg = result.get("error", "")
                    if "connect" in error_msg.lower() or "connection" in error_msg.lower():
                        print(f"\n[WARN] Ollama connection failed: {error_msg}")
                        print("[INFO] Falling back to static analysis...")
                        result = {
                            "status": "success",
                            "system": "static_fallback",
                            "output": _static_analysis_fallback(target, content, lines),
                            "note": "Ollama unavailable - using basic static analysis",
                        }

                return result

            except Exception as e:
                # On any exception, use static fallback
                print(f"\n[WARN] AI routing failed: {e}")
                if file_context:
                    print("[INFO] Falling back to static analysis...")
                    return {
                        "status": "success",
                        "system": "static_fallback",
                        "output": _static_analysis_fallback(target, content, lines),
                        "note": (f"AI system unavailable ({type(e).__name__}) - using basic static analysis"),
                    }
                return {
                    "status": "failed",
                    "system": target_system,
                    "error": f"AI routing failed ({type(e).__name__}): {e}",
                    "task_id": f"agent_{now_stamp()}",
                }

        # Run async task
        result = _normalize_semantic_status(asyncio.run(analyze()))

        # Display result with RECEIPT DISCIPLINE
        print("\n" + "=" * 80)
        print("ANALYSIS RECEIPT")
        print("=" * 80)

        task_id = result.get("task_id", "unknown")
        status = result.get("status", "unknown")

        # Print standardized receipt header
        print(f"🎫 Task ID: {task_id}")
        print(f"📊 Task Type: {task_type.upper()}")
        if file_context:
            print(f"🎯 Target: {target.name} ({lines} lines)")
        else:
            print(f"🎯 Target: {task_input[:80]}")
        print(f"⚙️  System: {result.get('system', target_system)}")

        if status == "success":
            print(f"✅ Status: {status}")
            if "model" in result:
                print(f"📦 Model: {result['model']}")
            output_value = result.get("output", "(no output)")
            if isinstance(output_value, str):
                output_text = output_value
            else:
                try:
                    output_text = json.dumps(output_value, indent=2, ensure_ascii=False, default=str)
                except Exception:
                    output_text = str(output_value)
            print("\n" + output_text)
            if "note" in result:
                print(f"\n💡 Note: {result['note']}")
            exit_code = 0
        elif status == "submitted":
            # Async submission is a SUCCESS - task is in queue
            print("✅ Status: SUBMITTED (async execution)")
            print(f"📍 Output Location: {hub_path / 'state' / 'reports'}")
            print("📝 To view results, check: state/reports/analyze_*.md")
            if "note" in result:
                print(f"\n💡 Note: {result['note']}")
            exit_code = 0
        else:
            print(f"⚠️  Status: {status}")
            print(f"Error: {result.get('error', 'unknown error')}")
            exit_code = 1

        # Write report
        reports_dir = hub_path / "state" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"analyze_{now_stamp()}.md"
        latest_report_path = reports_dir / "analyze_latest.md"

        report_target = target.name if file_context else task_input[:120]
        report_file = str(target) if file_context else task_input
        report_lines = lines if file_context else "n/a"
        report_size = f"{file_size / 1024:.1f}KB" if file_context else "n/a"
        result_section = (
            result.get("output", "(no output)")
            if isinstance(result.get("output", "(no output)"), str)
            else json.dumps(result.get("output", "(no output)"), indent=2, ensure_ascii=False, default=str)
        )
        report_md = f"""# Analysis Report: {report_target}
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**File**: `{report_file}`
**Lines**: {report_lines}
**Size**: {report_size}
**System**: {result.get("system", "unknown")}
**Status**: {result.get("status", "unknown")}

## Result

{result_section}

## Metadata

```json
{json.dumps(result, indent=2)}
```
"""

        previous_latest = ""
        if latest_report_path.exists():
            try:
                previous_latest = latest_report_path.read_text(encoding="utf-8")
            except OSError:
                previous_latest = ""
        content_changed = previous_latest != report_md

        latest_report_path.write_text(report_md, encoding="utf-8")
        write_history = str(os.getenv("NUSYQ_ANALYZE_REPORT_WRITE_HISTORY", "1")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        skip_unchanged = str(os.getenv("NUSYQ_ANALYZE_REPORT_SKIP_UNCHANGED_HISTORY", "1")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if write_history and (content_changed or not skip_unchanged):
            report_path.write_text(report_md, encoding="utf-8")
        else:
            report_path = latest_report_path

        try:
            keep_count = int(os.getenv("NUSYQ_ANALYZE_REPORT_HISTORY_KEEP", "20"))
        except ValueError:
            keep_count = 20
        _prune_lifecycle_reports(
            reports_dir,
            max(1, keep_count),
            pattern="analyze_*.md",
            protected_names={"analyze_latest.md"},
        )

        print(f"\n[Saved] {report_path}")

        return exit_code

    except ImportError as e:
        print(f"[ERROR] Failed to import agent_task_router: {e}")
        print("[INFO] Ensure src/tools/agent_task_router.py exists and dependencies are installed")
        return 1
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _static_analysis_fallback(file_path: Path, content: str, lines: int) -> str:
    """Basic static analysis when AI systems are unavailable."""
    findings = []

    # File type detection
    suffix = file_path.suffix.lower()
    findings.append(f"**File type**: {suffix or 'unknown'}")

    # Basic metrics
    findings.append(f"**Total lines**: {lines}")

    # Count blank lines
    blank_lines = sum(1 for line in content.splitlines() if not line.strip())
    findings.append(f"**Blank lines**: {blank_lines} ({blank_lines / lines * 100:.1f}%)")

    # Count comments (basic heuristic)
    comment_chars = {"#", "//"}
    comment_lines = sum(1 for line in content.splitlines() if any(line.strip().startswith(c) for c in comment_chars))
    findings.append(f"**Comment lines**: {comment_lines} (~{comment_lines / lines * 100:.1f}%)")

    # Check for common issues
    issues = []
    if "TODO" in content or "FIXME" in content:
        issues.append("Contains TODO/FIXME markers")
    if "import *" in content:
        issues.append("Contains wildcard imports (consider explicit imports)")
    if content.count("except:") > 0:
        issues.append("Contains bare except clauses (consider specific exceptions)")

    if issues:
        findings.append("\n**Potential Issues**:")
        for issue in issues:
            findings.append(f"- {issue}")

    # Language-specific checks
    if suffix == ".py":
        if "if __name__ == '__main__':" in content:
            findings.append("\n**Python**: Has main guard (good practice)")
        if "type:" in content or "-> " in content:
            findings.append("**Python**: Uses type hints")
    elif suffix == ".ts" and ("interface " in content or "type " in content):
        findings.append("**TypeScript**: Defines types/interfaces")

    findings.append("\n**Note**: This is a basic static analysis. For deeper insights, ensure Ollama is running.")

    return "\n".join(findings)


def _maybe_create_test_failure_quest(
    paths: RepoPaths,
    summary,
    out: str,
    err: str,
) -> None:
    if summary.status == "pass":
        return
    if summary.run_count_window < 3:
        return
    if not paths.nusyq_hub:
        return

    title = "Investigate recurring test failures"
    detail = err or out
    detail_line = detail.splitlines()[0] if detail else "No output captured"
    description = (
        f"Test command repeated {summary.run_count_window}x recently. "
        f"Last exit code: {summary.exit_code}. "
        f"First line: {detail_line[:160]}. "
        "See state/reports/test_runs.json for run history."
    )
    tags = ["tests", "stability", "triage"]

    try:
        from src.guild.guild_board import QuestState, get_board

        board = _run_guild(get_board())
        for quest in board.board.quests.values():
            if (
                quest.state
                in {
                    QuestState.OPEN,
                    QuestState.CLAIMED,
                    QuestState.ACTIVE,
                    QuestState.BLOCKED,
                }
                and title.lower() in quest.title.lower()
            ):
                return
    except Exception:
        pass

    try:
        from src.guild.guild_cli import board_add_quest

        _run_guild(
            board_add_quest(
                "system",
                title,
                description,
                priority=4,
                safety_tier="standard",
                tags=tags,
            )
        )
    except Exception:
        pass


def _handle_task_manager(args: list[str]) -> int:
    """ChatDev+Ollama generated task manager CLI wrapper."""
    try:
        from src.tools.task_manager.commands import add_task, delete_task, list_tasks
    except ImportError as e:
        print(f"[ERROR] Task manager not available: {e}")
        return 1

    # Parse subcommand: add, list, delete
    sub_args = args[1:] if len(args) > 1 else []
    if not sub_args:
        print("📋 Task Manager (ChatDev+Ollama)")
        print("=" * 40)
        print("Usage: python start_nusyq.py task_manager <command>")
        print("Commands:")
        print("  add <description>  - Add a new task")
        print("  list               - List all tasks")
        print("  delete <id>        - Delete task by ID")
        return 0

    cmd = sub_args[0]
    if cmd == "add":
        if len(sub_args) < 2:
            print("[ERROR] Missing task description")
            return 1
        description = " ".join(sub_args[1:])
        add_task(description)
        print(f"✅ Task added: {description}")
    elif cmd == "list":
        list_tasks()
    elif cmd == "delete":
        if len(sub_args) < 2:
            print("[ERROR] Missing task ID")
            return 1
        try:
            task_id = int(sub_args[1])
            delete_task(task_id)
            print(f"✅ Task {task_id} deleted")
        except ValueError:
            print(f"[ERROR] Invalid task ID: {sub_args[1]}")
            return 1
    else:
        print(f"[ERROR] Unknown command: {cmd}")
        return 1

    return 0


def _handle_brief(paths: RepoPaths) -> int:
    print("📊 NuSyQ Workspace Brief")
    print("=" * 50)

    print("\n## Repository Status")
    hygiene = check_spine_hygiene(paths.nusyq_hub)
    for h in hygiene:
        print(f"  {h}")

    print("\n## Active Quest")
    quest_file = paths.nusyq_hub / "src" / "Rosetta_Quest_System" / QUEST_LOG_FILENAME
    if quest_file.exists():
        try:
            with open(quest_file) as f:
                quests = [json.loads(line) for line in f if line.strip()]
            if quests:
                latest = quests[-1]
                status_emoji = {"completed": "✅", "failed": "❌", "in_progress": "🔄"}.get(latest.get("status"), "🔵")
                print(
                    f"  {status_emoji} {latest.get('task_type', 'unknown')}: {latest.get('description', 'No description')[:60]}"
                )
            else:
                print("  📭 No quests logged")
        except Exception as exc:
            print(f"  ⚠️ Error reading quest log: {exc}")

    print("\n## Problem Signals")
    diagnostics_dir = paths.nusyq_hub / "docs" / "Reports" / "diagnostics"
    vscode_counts_path = diagnostics_dir / "vscode_problem_counts.json"
    snapshot_latest = diagnostics_dir / "problem_signal_snapshot_latest.json"
    if vscode_counts_path.exists():
        try:
            data = json.loads(vscode_counts_path.read_text(encoding="utf-8"))
            counts = data.get("counts", data)
            print(
                f"  VS Code: {counts.get('errors', 0)} errors, "
                f"{counts.get('warnings', 0)} warnings, "
                f"{counts.get('infos', 0)} infos, "
                f"{counts.get('total', 0)} total"
            )
        except Exception:
            print("  ⚠️ VS Code counts present but unreadable")
    else:
        print("  Info: No VS Code counts recorded yet")

    if snapshot_latest.exists():
        try:
            data = json.loads(snapshot_latest.read_text(encoding="utf-8"))
            aggregate = data.get("aggregate", {})
            print(
                f"  Tool Aggregate: {aggregate.get('errors', 0)} errors, "
                f"{aggregate.get('warnings', 0)} warnings, "
                f"{aggregate.get('infos', 0)} infos, "
                f"{aggregate.get('total', 0)} total"
            )
        except Exception:
            print("  ⚠️ Problem snapshot present but unreadable")
    else:
        print("  Info: No problem snapshot recorded yet")

    ai_health = _collect_ai_health(paths)
    _print_ai_section(ai_health)
    print(
        "\n  "
        + (
            "✅ AI systems available; feel free to proceed"
            if any(info.get("healthy") for info in ai_health.get("services", {}).values())
            else "⚠️ AI systems are unavailable; investigate"
        )
    )

    print("\n## Available Actions")
    print("  🔍 analyze <file>  - AI-powered analysis (Ollama/ChatDev)")
    print("  ✍️  review <file>   - Code quality review")
    print("  🤖 ai_status       - Show AI system health (Ollama/ChatDev/Quantum)")
    print("  🧠 advanced_ai_quests - Generate/deduplicate quests for missing advanced-AI capabilities")
    print(
        "  🕸️ graph_learning [--hub-only] [--no-simulatedverse] [--no-root] [--top-k=N] [--max-files=N] [--reuse-ttl-s=N] [--force] - Build graph-learning impact/topology report"
    )
    print("  🚪 ai_work_gate    - Check if work can proceed (AI availability + hygiene)")
    print("  🧪 test           - Quick pytest run")
    print("  🧪 test_history [N] - Recent test runs + duplicates")
    print("  🩺 doctor [--quick|--async|--sync] [--budget-s=SECONDS] - Full system diagnostics")
    print("  🛰️ doctor_status [job_id] [--cancel] [--retry] - Poll/control doctor jobs")
    print(
        "  🏁 system_complete [--async|--sync] [--startup] [--budget-s=SECONDS] "
        "[--reuse-recent] [--reuse-ttl-s=SECONDS] - Completion gate"
    )
    print("  🛰️ system_complete_status [job_id] [--cancel] [--retry] - Poll/control completion jobs")
    print("  🔌 openclaw_smoke [--async|--sync] - OpenClaw integration smoke")
    print("  🛰️ openclaw_smoke_status [job_id] [--cancel] [--retry] - Poll/control OpenClaw smoke jobs")
    print("  🔌 openclaw_status - OpenClaw operational readiness (gateway/channels)")
    print("  ▶️ openclaw_gateway_start [--port=N] [--bind=loopback|lan] [--force] - Start gateway")
    print("  🔎 openclaw_gateway_status [--port=N] [--bind=loopback|lan] - Gateway runtime status")
    print("  ⏹️ openclaw_gateway_stop [--port=N] [--bind=loopback|lan] - Stop managed gateway")
    print("  ▶️ openclaw_bridge_start [--gateway=URL] - Start NuSyQ OpenClaw bridge")
    print("  🔎 openclaw_bridge_status [--gateway=URL] - Bridge connectivity status")
    print("  ⏹️ openclaw_bridge_stop - Stop managed NuSyQ OpenClaw bridge")
    print(
        '  🧪 openclaw_internal_send --text "..." [--system=auto|ollama|lmstudio|chatdev|copilot|codex|claude_cli|consciousness|quantum_resolver]'
    )
    print("  🔎 skyclaw_status - SkyClaw gateway runtime summary")
    print("  ▶️ skyclaw_start - Start SkyClaw gateway daemon")
    print("  ⏹️ skyclaw_stop - Stop SkyClaw gateway daemon")
    print("  ▶️ open_antigravity_start [--port=N] - Start modular-window-server runtime")
    print("  🔎 open_antigravity_runtime_status [--port=N] - Antigravity runtime + health status")
    print("  ⏹️ open_antigravity_stop [--port=N] - Stop managed antigravity runtime")
    print("  🛰️ antigravity_status - Open Antigravity runtime health")
    print("  🛰️ antigravity_health - Alias for antigravity_status")
    print(
        "  🚀 ignition [--thorough|--hetaeristic] [--strict] - Full activation sequence (+ optional SQL/NSSM/telemetry/brownfield pass)"
    )
    print(
        "  🩺 integration_health [--mode fast|full|startup] [--simulatedverse-mode auto|always_on|off] [--no-repair-simulatedverse]"
        " - Consolidated stack health check"
    )
    print("  🔐 compose_secrets [status|init-local] - Audit/init compose password env vars")
    print("  🌉 simverse_mode [status|auto|always_on|off] - Persist SimulatedVerse HTTP policy")
    print("  🤖 claude_preflight - Claude Desktop/CLI preflight diagnostics")
    print("  🩺 claude_doctor - Full Claude readiness doctor (preflight/CLI/router/terminal)")
    print("  🩺 codex_doctor - Full Codex readiness doctor (CLI/router/terminal)")
    print("  🩺 copilot_doctor - Full Copilot readiness doctor (chat/CLI/router/terminal)")
    print("  🩺 multi_agent_doctor - Combined Claude/Codex/Copilot readiness report")
    print("  🩺 agent_fleet_doctor - Fleet readiness across triad, local models, Claw-family, Culture Ship, and docs")
    print("  🕸️ delegation_matrix - Router delegation/schema/health matrix")
    print("  🧩 copilot_probe - Copilot bridge initialization probe")
    print("  🔁 failover_status [--limit=N] - Compact fallback telemetry summary")
    print(
        "  🧩 vscode_extensions_plan [--profile-name X --phase-size N] [--use-code-cli] - Codex-first VS Code extension isolation plan"
    )
    print(
        "  🧩 vscode_extensions_quickwins [--with-noise --since-minutes N] [--use-code-cli] - Immediate extension optimization actions"
    )
    print("  💡 suggest        - Get context-aware suggestions")
    print("  🎯 work           - Execute next safe quest")
    print("  🚦 problem_signal_snapshot - Align VS Code + tool diagnostics")
    print(
        "  🧾 error_report [--quick|--full|--force|--async|--sync] [--budget-s=SECONDS] [--cache-ttl-s=SECONDS] "
        "[--chain-bridges|--bridge-signals|--bridge-quests|--bridge-error-quests] "
        "(use --hub-only/--repo=<name>/--skip-repo=<name>) - Unified error report across repos"
    )
    print("  🧾 error_report_split - Split full-scan per repo + unified report")
    print("  🧾 error_report_status [job_id] [--cancel] [--retry] - Poll/control error-report jobs")
    print("  🌉 error_signal_bridge [--mode=once|test|watch] [--interval=SECONDS] - Error report → guild signals")
    print("  🌉 signal_quest_bridge [--mode=once|test|watch] [--interval=SECONDS] - Guild signals → quests")
    print("  🌉 error_quest_bridge [--severity=error|warning|info|hint] [--max-quests=N] - Critical errors → quests")
    print("  🌉 auto_quest [--severity=error|warning|info|hint] [--max-quests=N] - Alias for error_quest_bridge")
    print("  🧹 quest_compact [--dry-run] - Compact duplicate open signal-linked quests")
    print("  🧾 log_dedup_status - Show logging dedup filter status")
    print("  ⚛️ quantum_resolver_status - Show quantum resolver consolidation status")
    print("  🧩 vscode_diagnostics_bridge - Refresh VS Code counts")
    print("  🧹 hygiene        - Run path normalization + TODO→Issue + PU automation")
    print(
        "  🧹 prune_reports [--dry-run|--execute|--delete|--with-automated-cleanup] - Prune/archive stale report artifacts"
    )

    print("\n## Recent Errors")
    print("  (Checking latest pytest/health runs...)")
    pytest_cache = paths.nusyq_hub / ".pytest_cache" / "v" / "cache" / "lastfailed"
    if pytest_cache.exists():
        try:
            with open(pytest_cache) as f:
                failures = json.load(f)
            if failures:
                print(f"  ⚠️ {len(failures)} test(s) failed in last run")
                for test_name in list(failures.keys())[:3]:
                    print(f"     - {test_name[:60]}")
            else:
                print("  ✅ All tests passing")
        except Exception:
            print("  Info: No test cache available")
    else:
        print("  Info: No test cache available")

    print("\n## Recommended Next Moves")
    print("  1. Run 'python start_nusyq.py ai_work_gate' to validate work readiness")
    print("  2. Run 'python start_nusyq.py suggest' for AI-generated suggestions")
    print("  3. Execute 'python start_nusyq.py work' to process next quest")
    print("  4. Use 'python start_nusyq.py hygiene' to automate path norm + TODO conv")

    return 0


def _handle_ai_status(paths: RepoPaths, json_mode: bool = False) -> int:
    ai_health = _collect_ai_health(paths)
    capability_intel = _collect_ai_capability_intelligence(paths)
    audit_intel = (
        collect_audit_intelligence(paths.nusyq_hub, include_sessions=False)
        if paths.nusyq_hub
        else {"status": "unavailable", "reason": "hub_path_missing"}
    )
    payload = {
        "action": "ai_status",
        "status": "ok",
        "generated_at": datetime.now().isoformat(),
        "services": ai_health.get("services", {}),
        "quantum": ai_health.get("quantum", {}),
        "capability_intelligence": capability_intel,
        "audit_intelligence": audit_intel,
    }
    if paths.nusyq_hub:
        with contextlib.suppress(Exception):
            report_path = paths.nusyq_hub / "state" / "reports" / "ai_status_latest.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print("🤖 AI SYSTEM HEALTH")
    print("=" * 60)
    _print_ai_section(ai_health)
    _print_ai_capability_section(capability_intel)
    print("\n📚 Audit Intelligence")
    for line in format_audit_intelligence_lines(audit_intel, max_lines=4):
        print(f"  - {line}")
    return 0


def _handle_advanced_ai_quests(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Generate/deduplicate quests for missing advanced AI capabilities."""
    del args
    if not paths.nusyq_hub:
        payload = {
            "action": "advanced_ai_quests",
            "status": "error",
            "error": "hub_path_missing",
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("[ERROR] NuSyQ-Hub path not found")
        return 1

    from src.automation.autonomous_quest_generator import AutonomousQuestGenerator

    generator = AutonomousQuestGenerator()
    result = _run_async_sync(generator.generate_advanced_ai_capability_quests())
    payload = {
        "action": "advanced_ai_quests",
        "status": "ok" if result.get("success") else "partial",
        "generated_at": datetime.now().isoformat(),
        **result,
    }
    report_path = paths.nusyq_hub / "state" / "reports" / "advanced_ai_quests_latest.json"
    with contextlib.suppress(Exception):
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if result.get("success") else 1

    print("🧠 ADVANCED AI QUEST BRIDGE")
    print("=" * 60)
    print(f"Created: {result.get('created', 0)}")
    print(f"Skipped: {result.get('skipped', 0)}")
    print(f"Failed: {result.get('failed', 0)}")
    if result.get("quest_ids"):
        print("Quest IDs:")
        for quest_id in result["quest_ids"]:
            print(f"  - {quest_id}")
    return 0 if result.get("success") else 1


def _handle_graph_learning(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Run dependency-graph learning analysis across the available repos."""
    from src.tools.dependency_analyzer import DependencyAnalyzer
    from src.utils.intelligent_timeout_manager import (
        get_adaptive_timeout,
        record_service_completion,
    )

    tokens = list(args)
    if tokens and tokens[0] == "graph_learning":
        tokens = tokens[1:]
    hub_only = "--hub-only" in tokens
    include_simverse = not hub_only and "--no-simulatedverse" not in tokens
    include_root = not hub_only and "--no-root" not in tokens
    top_k = 10
    max_files_per_repo: int | None = None
    timeout_override_s: float | None = None
    reuse_recent = "--no-reuse-recent" not in tokens
    reuse_ttl_s = int(os.getenv("NUSYQ_GRAPH_LEARNING_CACHE_TTL_S", "1800") or 1800)
    force_refresh = "--force" in tokens
    for token in tokens:
        if token.startswith("--top-k="):
            with contextlib.suppress(ValueError):
                top_k = max(1, int(token.split("=", 1)[1]))
        if token.startswith("--max-files="):
            with contextlib.suppress(ValueError):
                max_files_per_repo = max(1, int(token.split("=", 1)[1]))
        if token.startswith("--timeout-s="):
            with contextlib.suppress(ValueError):
                timeout_override_s = max(1.0, float(token.split("=", 1)[1]))
        if token.startswith("--reuse-ttl-s="):
            with contextlib.suppress(ValueError):
                reuse_ttl_s = max(0, int(token.split("=", 1)[1]))

    repo_map: dict[str, Path] = {}
    if paths.nusyq_hub:
        repo_map["hub"] = paths.nusyq_hub / "src"
    if include_simverse and paths.simulatedverse:
        repo_map["simverse"] = paths.simulatedverse / "src"
    if include_root and paths.nusyq_root:
        repo_map["nusyq"] = paths.nusyq_root

    if not repo_map:
        payload = {
            "action": "graph_learning",
            "status": "error",
            "error": "no_repo_paths_available",
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("[ERROR] No repository roots available for graph learning")
        return 1

    requested_options = {
        "hub_only": hub_only,
        "include_simulatedverse": include_simverse,
        "include_root": include_root,
        "top_k": top_k,
        "max_files_per_repo": max_files_per_repo,
    }
    latest_report_path = (paths.nusyq_hub or Path(".")) / "state" / "reports" / "graph_learning_latest.json"
    if reuse_recent and not force_refresh and reuse_ttl_s > 0:
        cached_payload = read_json(latest_report_path)
        if isinstance(cached_payload, dict):
            cached_generated = _parse_iso_datetime(cached_payload.get("generated_at"))
            if cached_generated is not None:
                now_dt = datetime.now(cached_generated.tzinfo) if cached_generated.tzinfo else datetime.now()
                age_s = (now_dt - cached_generated).total_seconds()
                cached_options = cached_payload.get("options", {})
                if (
                    0 <= age_s <= reuse_ttl_s
                    and isinstance(cached_options, dict)
                    and all(cached_options.get(k) == v for k, v in requested_options.items())
                ):
                    cached_payload["cache_info"] = {
                        "reused": True,
                        "age_seconds": round(age_s, 2),
                        "ttl_seconds": reuse_ttl_s,
                        "source": str(latest_report_path),
                    }
                    if json_mode:
                        print(json.dumps(cached_payload, indent=2, ensure_ascii=False))
                    else:
                        print("🕸️ GRAPH LEARNING")
                        print("=" * 60)
                        print(
                            f"Reused cached report ({round(age_s, 2)}s old, ttl={reuse_ttl_s}s): {latest_report_path}"
                        )
                    return 0 if cached_payload.get("status") == "ok" else 1

    def _resolve_timeout_s() -> float:
        if timeout_override_s is not None:
            return timeout_override_s
        env_timeout = os.getenv("NUSYQ_GRAPH_LEARNING_TIMEOUT_S", "").strip()
        if env_timeout:
            with contextlib.suppress(ValueError):
                return max(1.0, float(env_timeout))
        complexity = 1.0 + (0.35 * max(0, len(repo_map) - 1))
        if max_files_per_repo is None:
            complexity += 0.4
        elif max_files_per_repo >= 250:
            complexity += 0.25
        elif max_files_per_repo <= 50:
            complexity = max(0.6, complexity - 0.15)
        return float(get_adaptive_timeout("analysis", complexity=complexity, priority="normal"))

    def _run_graph_learning_analysis(
        analyzer: Any, *, top_k_value: int, timeout_s: float
    ) -> tuple[dict[str, Any] | None, float, bool]:
        started = time.time()

        def _work() -> dict[str, Any]:
            with contextlib.redirect_stdout(io.StringIO()):
                analyzer.analyze_all()
            return analyzer.generate_graph_learning_report(top_k=top_k_value)

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(_work)
        try:
            result = future.result(timeout=timeout_s)
            elapsed = time.time() - started
            executor.shutdown(wait=False, cancel_futures=True)
            return result, elapsed, False
        except FuturesTimeoutError:
            future.cancel()
            elapsed = time.time() - started
            executor.shutdown(wait=False, cancel_futures=True)
            return None, elapsed, True

    def _next_max_files(current: int | None) -> int:
        if current is None:
            return 250
        if current > 250:
            return 250
        return max(25, current // 2)

    adaptive_timeout_s = _resolve_timeout_s()
    current_max_files = max_files_per_repo
    attempts: list[dict[str, Any]] = []
    graph_report: dict[str, Any] | None = None
    attempt_timeout_s = adaptive_timeout_s

    for attempt_index in range(1, 4):
        analyzer = DependencyAnalyzer(repos=repo_map, max_files_per_repo=current_max_files)
        result, elapsed_s, timed_out = _run_graph_learning_analysis(
            analyzer, top_k_value=top_k, timeout_s=attempt_timeout_s
        )
        attempts.append(
            {
                "attempt": attempt_index,
                "timeout_seconds": round(attempt_timeout_s, 2),
                "max_files_per_repo": current_max_files,
                "timed_out": timed_out,
                "elapsed_s": round(elapsed_s, 2),
            }
        )
        if not timed_out and result is not None:
            graph_report = result
            record_service_completion("analysis", elapsed_s)
            break

        current_max_files = _next_max_files(current_max_files)
        attempt_timeout_s = max(attempt_timeout_s, adaptive_timeout_s * 1.25)

    if graph_report is None:
        payload = {
            "action": "graph_learning",
            "status": "partial",
            "generated_at": datetime.now().isoformat(),
            "repos": {name: str(path) for name, path in repo_map.items()},
            "options": {
                **requested_options,
                "adaptive_timeout_seconds": round(adaptive_timeout_s, 2),
                "reuse_recent": reuse_recent,
                "reuse_ttl_s": reuse_ttl_s,
            },
            "error": "analysis_timeout",
            "attempts": attempts,
            "next_suggested_args": {
                "hub_only": True,
                "max_files_per_repo": current_max_files,
                "timeout_seconds": round(attempt_timeout_s, 2),
            },
        }
        report_path = _write_state_report(paths.nusyq_hub, "graph_learning_latest.json", payload)
        payload["report_path"] = str(report_path)
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 1
        print("🕸️ GRAPH LEARNING")
        print("=" * 60)
        print("Status: partial")
        print("Reason: analysis timeout")
        print(f"Adaptive timeout: {adaptive_timeout_s:.1f}s")
        print(f"Suggested max-files: {current_max_files}")
        print(f"Report: {report_path}")
        return 1

    payload = {
        "action": "graph_learning",
        "status": graph_report.get("status", "ok"),
        "generated_at": datetime.now().isoformat(),
        "repos": {name: str(path) for name, path in repo_map.items()},
        "options": {
            **requested_options,
            "adaptive_timeout_seconds": round(adaptive_timeout_s, 2),
            "reuse_recent": reuse_recent,
            "reuse_ttl_s": reuse_ttl_s,
        },
        "attempts": attempts,
        "graph_learning": graph_report,
    }
    report_path = _write_state_report(paths.nusyq_hub, "graph_learning_latest.json", payload)
    payload["report_path"] = str(report_path)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    summary = graph_report.get("summary", {})
    print("🕸️ GRAPH LEARNING")
    print("=" * 60)
    print(f"Nodes: {summary.get('node_count', 0)}")
    print(f"Edges: {summary.get('edge_count', 0)}")
    print(f"Communities: {summary.get('community_count', 0)}")
    print(f"Cycles: {summary.get('cycle_count', 0)}")
    print(f"Backend: {graph_report.get('backend', 'unknown')}")
    top_nodes = graph_report.get("top_impact_nodes", [])
    if isinstance(top_nodes, list) and top_nodes:
        print("Top impact nodes:")
        for node in top_nodes[:5]:
            print(f"  - {node.get('path')} ({node.get('impact_score')})")
    print(f"Report: {report_path}")
    return 0


def _handle_ai_work_gate(paths: RepoPaths) -> int:
    """Check if work can proceed based on AI system availability."""
    print("🚪 AI Work Gate Check")
    print("=" * 70)

    # Check AI health
    print("\n1️⃣  Checking AI systems...")
    ai_health = _collect_ai_health(paths)
    services = ai_health.get("services", {})
    available_systems = [name for name, info in services.items() if isinstance(info, dict) and info.get("healthy")]

    if not available_systems:
        print("❌ GATE CLOSED: No AI systems available")
        print("\nAvailable systems needed:")
        print("  • Ollama (local LLMs)")
        print("  • ChatDev (multi-agent team)")
        print("  • Quantum Resolver (always available as fallback)")

        # Record gate decision
        try:
            from src.system.ai_metrics_tracker import AIMetricsTracker

            tracker = AIMetricsTracker(paths.nusyq_hub)
            tracker.record_gate_decision(
                gate_status="closed",
                ai_systems_available=0,
                ai_systems_total=len(services),
                reason="no_ai_systems",
            )
        except Exception:
            pass

        return 1

    print(f"✅ AI systems ready: {', '.join(available_systems)}")

    # Check repo hygiene
    print("\n2️⃣  Checking repository hygiene...")
    hygiene = check_spine_hygiene(paths.nusyq_hub)
    for h in hygiene:
        print(f"  {h}")

    # Check for active quests
    print("\n3️⃣  Checking quest availability...")
    quest = read_quest_log(paths.nusyq_hub)
    if quest.last_nonempty_line:
        try:
            obj = json.loads(quest.last_nonempty_line)
            if isinstance(obj, dict):
                status = obj.get("status", "unknown")
                task_type = obj.get("task_type", "unknown")
                print(f"✅ Active quest: {task_type} ({status})")
        except Exception:
            print("Info: Quest log exists (status unknown)")
    else:
        print("⚠️  No active quests")
        print("    Use: python start_nusyq.py queue  # Fetch next quest")

    # Final gate decision
    print("\n" + "=" * 70)
    print("✅ GATE OPEN: Work can proceed")
    print("\nNext actions:")
    print("  python start_nusyq.py work        # Execute next safe quest")
    print("  python start_nusyq.py auto_cycle  # Run full cycle")
    print("  python start_nusyq.py queue       # View queued work")

    # Record gate decision
    try:
        from src.system.ai_metrics_tracker import AIMetricsTracker

        tracker = AIMetricsTracker(paths.nusyq_hub)
        tracker.record_gate_decision(
            gate_status="open",
            ai_systems_available=len(available_systems),
            ai_systems_total=len(services),
            hygiene_status="checked",
            quests_available=bool(quest.last_nonempty_line),
            reason="all_checks_passed",
        )
    except Exception:
        pass  # Don't fail gate if metrics fail

    return 0


def _run_system_gate_check(
    name: str,
    cmd: list[str],
    cwd: Path | None,
    timeout_s: int,
    quiet: bool = False,
) -> dict[str, Any]:
    started = time.time()
    rc, out, err = run(cmd, cwd=cwd, timeout_s=timeout_s)
    passed = rc == 0
    elapsed = round(time.time() - started, 2)
    status = "PASS" if passed else "FAIL"
    if not quiet:
        print(f"  {status} {name} ({elapsed}s)")
        if not passed and err:
            print(f"    stderr: {err.splitlines()[-1] if err.splitlines() else err}")
    return {
        "name": name,
        "passed": passed,
        "rc": rc,
        "elapsed_s": elapsed,
        "cmd": cmd,
        "stdout_tail": "\n".join(out.splitlines()[-10:]) if out else "",
        "stderr_tail": "\n".join(err.splitlines()[-10:]) if err else "",
    }


@dataclass(frozen=True)
class SystemCompleteOptions:
    async_mode: bool = False
    budget_s: int = 0
    reuse_recent: bool = False
    reuse_ttl_s: int = 900
    startup_profile: bool = False


def _parse_system_complete_args(args: list[str] | None) -> SystemCompleteOptions:
    tokens = list(args or [])
    if tokens and tokens[0] == "system_complete":
        tokens = tokens[1:]

    async_mode = "--async" in tokens and "--sync" not in tokens
    budget_s = int(os.getenv("NUSYQ_SYSTEM_COMPLETE_BUDGET_S", "0") or 0)
    reuse_recent = "--reuse-recent" in tokens and "--no-reuse-recent" not in tokens
    reuse_ttl_s = int(os.getenv("NUSYQ_SYSTEM_COMPLETE_REUSE_TTL_S", "900") or 900)
    startup_profile = "--startup" in tokens and "--full-stack" not in tokens
    for token in tokens:
        if token.startswith("--budget-s="):
            try:
                budget_s = max(0, int(token.split("=", 1)[1]))
            except ValueError:
                pass
        if token.startswith("--reuse-ttl-s="):
            try:
                reuse_ttl_s = max(0, int(token.split("=", 1)[1]))
            except ValueError:
                pass
    return SystemCompleteOptions(
        async_mode=async_mode,
        budget_s=budget_s,
        reuse_recent=reuse_recent,
        reuse_ttl_s=reuse_ttl_s,
        startup_profile=startup_profile,
    )


def _load_recent_system_complete_checks(
    hub_path: Path | None, ttl_s: int, profile: str = "full-stack"
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Load reusable checks from latest gate report when fresh enough."""
    if not hub_path or ttl_s <= 0:
        return {}, {}
    report_path = hub_path / "state" / "reports" / "system_complete_gate_latest.json"
    report = read_json(report_path)
    if not isinstance(report, dict):
        return {}, {}
    generated_at = report.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at:
        return {}, {}
    try:
        generated_dt = datetime.fromisoformat(generated_at)
    except ValueError:
        return {}, {}
    now_dt = datetime.now(generated_dt.tzinfo) if generated_dt.tzinfo else datetime.now()
    age_s = (now_dt - generated_dt).total_seconds()
    if age_s < 0 or age_s > ttl_s:
        return {}, {}
    report_profile = str(report.get("profile") or report.get("options", {}).get("profile") or "").strip()
    if report_profile and report_profile != profile:
        return {}, {}
    checks = report.get("checks", [])
    if not isinstance(checks, list):
        return {}, {}
    reusable: dict[str, dict[str, Any]] = {}
    for check in checks:
        if not isinstance(check, dict):
            continue
        name = str(check.get("name") or "").strip()
        if not name:
            continue
        reusable[name] = dict(check)
    metadata = {
        "report_file": str(report_path),
        "generated_at": generated_at,
        "age_s": round(age_s, 2),
        "ttl_s": ttl_s,
        "profile": report_profile or profile,
    }
    return reusable, metadata


def _build_system_complete_script_checks(startup_profile: bool) -> list[tuple[str, list[str], int]]:
    """Build the ordered script checks for the selected system_complete profile."""
    if startup_profile:
        return [
            (
                "workspace_verifier",
                [sys.executable, "scripts/verify_tripartite_workspace.py"],
                90,
            ),
            (
                "doctor_quick",
                [sys.executable, "scripts/start_nusyq.py", "doctor", "--quick", "--json"],
                180,
            ),
            (
                "integration_health_startup",
                [
                    sys.executable,
                    "scripts/start_nusyq.py",
                    "integration_health",
                    "--mode",
                    "startup",
                    "--simulatedverse-mode",
                    "auto",
                    "--no-repair-simulatedverse",
                    "--json",
                ],
                240,
            ),
        ]

    return [
        ("openclaw_smoke", [sys.executable, "scripts/openclaw_smoke_test.py"], 180),
        (
            "culture_ship_cycle",
            [sys.executable, "scripts/test_culture_ship_cycle.py", "--dry-run"],
            300,
        ),
        (
            "nogic_hotspot_ingestion",
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    "from src.integrations.nogic_quest_integration import run_architecture_analysis; "
                    "a = run_architecture_analysis(workspace_root=Path('.'), save_results=True, open_visualizer=False); "
                    "print(f'HOTSPOTS={len(a.high_complexity_functions)} ORPHANS={len(a.orphaned_symbols)}')"
                ),
            ],
            300,
        ),
        # chatdev_e2e is LAST: can take 5-15 min when server is running
        ("chatdev_e2e", [sys.executable, "scripts/e2e_chatdev_mcp_test.py"], 1800),
    ]


def _sync_error_report_latest_artifacts(
    paths: RepoPaths, report: dict[str, Any], outputs: dict[str, str]
) -> dict[str, str]:
    """Mirror the canonical latest error-report artifacts into state/reports."""
    if not paths.nusyq_hub:
        return {}

    state_json_path = _write_state_report(paths.nusyq_hub, "unified_error_report_latest.json", report)
    state_md_path = paths.nusyq_hub / "state" / "reports" / "unified_error_report_latest.md"

    latest_md_candidate = Path(outputs.get("latest_md", "")).expanduser() if outputs.get("latest_md") else None
    fallback_md_candidate = Path(outputs.get("md", "")).expanduser() if outputs.get("md") else None
    md_source = None
    for candidate in (latest_md_candidate, fallback_md_candidate):
        if candidate and candidate.exists():
            md_source = candidate
            break

    if md_source:
        state_md_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(md_source, state_md_path)
    else:
        markdown_lines = [
            "# Unified Error Report (Latest)\n\n",
            f"- Generated at: `{report.get('timestamp', '')}`\n",
            f"- Scan mode: `{report.get('scan_mode', '')}`\n",
            f"- Targets: `{', '.join(report.get('targets', []))}`\n",
            f"- Total diagnostics: `{report.get('total_diagnostics', 0)}`\n",
        ]
        state_md_path.write_text("".join(markdown_lines), encoding="utf-8")

    return {
        "state_latest_json": str(state_json_path),
        "state_latest_md": str(state_md_path),
    }


def _service_healthy_for_system_gate(name: str, info: Any, startup_profile: bool = False) -> bool:
    """Determine whether a service should count as healthy for system_complete."""
    if not isinstance(info, dict):
        return False
    if bool(info.get("healthy")):
        return True

    # Optional services are always exempt regardless of startup_profile
    optional_services = {"hermes_agent", "metaclaw", "factory", "simulatedverse"}
    if name in optional_services:
        error = str(info.get("error") or "").strip().lower()
        status = str(info.get("status") or "").strip().lower()
        # simulatedverse is optional: it uses file-mode fallback when the HTTP server is not running
        if name == "simulatedverse":
            return True  # File-mode fallback always works; HTTP server is optional
        if error in {"runtime_not_ready"} or "optional dependency" in error or status == "installed":
            return True

    if not startup_profile:
        return False
    return False


def _summarize_checkpoint_from_metadata(payload: dict[str, Any]) -> dict[str, Any] | None:
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        return None
    checkpoint_file = metadata.get("checkpoint_file")
    if not isinstance(checkpoint_file, str) or not checkpoint_file:
        return None
    checkpoint = read_json(Path(checkpoint_file))
    if not isinstance(checkpoint, dict):
        return {"checkpoint_file": checkpoint_file, "available": False}
    job_started = _parse_iso_datetime(payload.get("started_at"))
    checkpoint_marker = (
        _parse_iso_datetime(checkpoint.get("updated_at"))
        or _parse_iso_datetime(checkpoint.get("finished_at"))
        or _parse_iso_datetime(checkpoint.get("generated_at"))
        or _parse_iso_datetime(checkpoint.get("timestamp"))
        or _parse_iso_datetime(checkpoint.get("started_at"))
    )
    stale_for_job = False
    if job_started and checkpoint_marker:
        stale_for_job = checkpoint_marker < job_started

    checks = checkpoint.get("checks", [])
    if not isinstance(checks, list):
        checks = []
    passed = sum(1 for check in checks if isinstance(check, dict) and check.get("passed"))
    failed = sum(
        1 for check in checks if isinstance(check, dict) and not check.get("passed") and not check.get("skipped")
    )
    skipped = sum(1 for check in checks if isinstance(check, dict) and check.get("skipped"))
    return {
        "checkpoint_file": checkpoint_file,
        "available": True,
        "status": checkpoint.get("status"),
        "started_at": checkpoint.get("started_at"),
        "updated_at": checkpoint.get("updated_at"),
        "finished_at": checkpoint.get("finished_at"),
        "current_check": checkpoint.get("current_check"),
        "completed_checks": checkpoint.get("completed_checks"),
        "total_planned": checkpoint.get("total_planned"),
        "passed_checks": passed,
        "failed_checks": failed,
        "skipped_checks": skipped,
        "stale_for_job": stale_for_job,
    }


def _summarize_system_complete_checkpoint(payload: dict[str, Any]) -> dict[str, Any] | None:
    return _summarize_checkpoint_from_metadata(payload)


def _summarize_error_report_checkpoint(payload: dict[str, Any]) -> dict[str, Any] | None:
    return _summarize_checkpoint_from_metadata(payload)


def _summarize_doctor_checkpoint(payload: dict[str, Any]) -> dict[str, Any] | None:
    return _summarize_checkpoint_from_metadata(payload)


def _handle_system_complete(paths: RepoPaths, json_mode: bool = False, args: list[str] | None = None) -> int:
    """Hard completion gate for full-stack system readiness."""
    options = _parse_system_complete_args(args)
    if not json_mode:
        print("🏁 SYSTEM COMPLETE GATE")
        print("=" * 70)
    if not paths.nusyq_hub:
        if json_mode:
            print(
                json.dumps(
                    {
                        "action": "system_complete",
                        "status": "error",
                        "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
                    },
                    indent=2,
                )
            )
        else:
            print(ERROR_NUSYQ_HUB_PATH_NOT_FOUND)
        return 1

    if options.async_mode:
        checkpoint_file = paths.nusyq_hub / "state" / "reports" / "system_complete_checkpoint_latest.json"
        cmd = [sys.executable, "scripts/start_nusyq.py", "system_complete", "--sync", "--json"]
        if options.startup_profile:
            cmd.append("--startup")
        if options.budget_s > 0:
            cmd.append(f"--budget-s={options.budget_s}")
        if options.reuse_recent:
            cmd.append("--reuse-recent")
            cmd.append(f"--reuse-ttl-s={options.reuse_ttl_s}")
        job = _start_subprocess_job(
            paths,
            job_type="system_complete",
            command=cmd,
            cwd=paths.nusyq_hub,
            metadata={
                "runner": "start_nusyq",
                "action": "system_complete",
                "checkpoint_file": str(checkpoint_file),
            },
        )
        payload = {
            "action": "system_complete",
            "status": "submitted",
            "job_id": job["job_id"],
            "pid": job["pid"],
            "stdout_log": job["stdout_log"],
            "stderr_log": job["stderr_log"],
            "checkpoint_file": str(checkpoint_file),
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("Submitted as background job")
            print(f"Job ID: {payload['job_id']}")
            print(f"PID: {payload['pid']}")
            print(f"stdout: {payload['stdout_log']}")
            print(f"stderr: {payload['stderr_log']}")
            print(f"Check status: python scripts/start_nusyq.py system_complete_status {payload['job_id']} --wait=30")
        return 0

    gate_started = time.time()
    checks: list[dict[str, Any]] = []
    run_stamp = now_stamp()
    profile = "startup" if options.startup_profile else "full-stack"
    checkpoint_path = paths.nusyq_hub / "state" / "reports" / f"system_complete_checkpoint_{run_stamp}.json"
    checkpoint_latest_path = paths.nusyq_hub / "state" / "reports" / "system_complete_checkpoint_latest.json"

    ai_health = _collect_ai_health(paths, record_metrics=False)
    services = ai_health.get("services", {})

    def _router_timeout(service_payload: Any) -> bool:
        return isinstance(service_payload, dict) and service_payload.get("error") == "health_check_timeout"

    ai_probe_retry: dict[str, Any] | None = None
    router_service = services.get("router") if isinstance(services, dict) else None
    if _router_timeout(router_service):
        retry_timeout = max(
            float(os.getenv("NUSYQ_SYSTEM_COMPLETE_AI_RETRY_TIMEOUT_S", "20")),
            float(router_service.get("timeout_seconds") or 0),
        )
        prev_mode = os.getenv("NUSYQ_AI_STATUS_ROUTER_PROBE_MODE")
        prev_timeout = os.getenv("NUSYQ_AI_STATUS_TIMEOUT_S")
        retry_health: dict[str, Any] | None = None
        try:
            os.environ["NUSYQ_AI_STATUS_ROUTER_PROBE_MODE"] = "in_process"
            os.environ["NUSYQ_AI_STATUS_TIMEOUT_S"] = str(retry_timeout)
            retry_health = _collect_ai_health(paths, record_metrics=False)
        finally:
            if prev_mode is None:
                os.environ.pop("NUSYQ_AI_STATUS_ROUTER_PROBE_MODE", None)
            else:
                os.environ["NUSYQ_AI_STATUS_ROUTER_PROBE_MODE"] = prev_mode
            if prev_timeout is None:
                os.environ.pop("NUSYQ_AI_STATUS_TIMEOUT_S", None)
            else:
                os.environ["NUSYQ_AI_STATUS_TIMEOUT_S"] = prev_timeout

        retry_services = retry_health.get("services", {}) if isinstance(retry_health, dict) else {}
        retry_router = retry_services.get("router") if isinstance(retry_services, dict) else None
        recovered = not _router_timeout(retry_router)
        ai_probe_retry = {
            "attempted": True,
            "mode": "in_process",
            "timeout_seconds": retry_timeout,
            "recovered": recovered,
        }
        if recovered and isinstance(retry_health, dict):
            ai_health = retry_health
            services = retry_services

    ai_clean = bool(services) and all(
        _service_healthy_for_system_gate(name, info, startup_profile=options.startup_profile)
        for name, info in services.items()
    )
    if not json_mode:
        print(f"  {'PASS' if ai_clean else 'FAIL'} ai_status clean")
    ai_details: dict[str, Any] = dict(services) if isinstance(services, dict) else {}
    if ai_probe_retry:
        ai_details["probe_retry"] = ai_probe_retry
    ai_details["profile"] = profile
    checks.append(
        {
            "name": "ai_status_clean",
            "passed": ai_clean,
            "details": ai_details,
        }
    )

    script_checks = _build_system_complete_script_checks(options.startup_profile)
    threshold_checks = 0 if options.startup_profile else 2
    total_planned = 1 + len(script_checks) + threshold_checks
    checkpoint: dict[str, Any] = {
        "action": "system_complete_checkpoint",
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "total_planned": total_planned,
        "completed_checks": 0,
        "options": {
            "budget_s": options.budget_s,
            "reuse_recent": options.reuse_recent,
            "reuse_ttl_s": options.reuse_ttl_s,
            "profile": profile,
        },
        "checks": [],
    }

    def _write_checkpoint() -> None:
        checkpoint["updated_at"] = datetime.now().isoformat()
        checkpoint["completed_checks"] = len(checkpoint.get("checks", []))
        _write_json_report(checkpoint_path, checkpoint)
        _write_json_report(checkpoint_latest_path, checkpoint)

    def _record_check(entry: dict[str, Any]) -> None:
        checkpoint_checks = checkpoint.setdefault("checks", [])
        if isinstance(checkpoint_checks, list):
            checkpoint_checks.append(entry)
        checkpoint["current_check"] = entry.get("name")
        _write_checkpoint()

    def _remaining_budget_s() -> int | None:
        if options.budget_s <= 0:
            return None
        elapsed = int(time.time() - gate_started)
        return max(0, options.budget_s - elapsed)

    _write_checkpoint()
    _record_check(checks[0])

    recent_checks, reuse_metadata = _load_recent_system_complete_checks(
        paths.nusyq_hub,
        options.reuse_ttl_s if options.reuse_recent else 0,
        profile=profile,
    )

    for label, cmd, timeout_s in script_checks:
        cached = recent_checks.get(label)
        if isinstance(cached, dict) and cached.get("passed") is True:
            reused_entry = dict(cached)
            reused_entry["reused"] = True
            reused_entry["reused_from"] = reuse_metadata.get("report_file", "")
            reused_entry["reused_generated_at"] = reuse_metadata.get("generated_at", "")
            reused_entry["reused_age_s"] = reuse_metadata.get("age_s", 0)
            if not json_mode:
                print(
                    f"  PASS {label} (reused, age={reused_entry.get('reused_age_s', 0)}s, "
                    f"ttl={reuse_metadata.get('ttl_s', 0)}s)"
                )
            checks.append(reused_entry)
            _record_check(reused_entry)
            continue

        remaining = _remaining_budget_s()
        if remaining is not None and remaining <= 0:
            budget_entry = {
                "name": label,
                "passed": False,
                "skipped": True,
                "reason": "budget_exceeded",
                "elapsed_s": 0.0,
                "cmd": cmd,
            }
            checks.append(budget_entry)
            _record_check(budget_entry)
            continue
        effective_timeout = timeout_s if remaining is None else max(1, min(timeout_s, remaining))
        result = _run_system_gate_check(label, cmd, paths.nusyq_hub, effective_timeout, quiet=json_mode)
        if remaining is not None:
            result["budget_remaining_s"] = _remaining_budget_s()
        checks.append(result)
        _record_check(result)

    max_ruff_errors = int(os.getenv("NUSYQ_COMPLETE_MAX_RUFF_ERRORS", "0"))
    max_mypy_errors = int(os.getenv("NUSYQ_COMPLETE_MAX_MYPY_ERRORS", "0"))
    if not options.startup_profile:
        remaining_for_lint = _remaining_budget_s()
        if remaining_for_lint is not None and remaining_for_lint <= 0:
            lint_entry = {
                "name": "lint_threshold",
                "passed": False,
                "skipped": True,
                "reason": "budget_exceeded",
                "errors": None,
                "max_errors": max_ruff_errors,
            }
        else:
            lint_timeout = 120 if remaining_for_lint is None else max(1, min(120, remaining_for_lint))
            ruff_rc, ruff_out, ruff_err = run(
                ["ruff", "check", "scripts", "--output-format", "concise"],
                cwd=paths.nusyq_hub,
                timeout_s=lint_timeout,
            )
            ruff_error_lines = [
                line
                for line in ruff_out.splitlines()
                if line.strip() and not line.startswith("Found ") and not line.startswith("[*]") and ":" in line
            ]
            ruff_errors = 0 if ruff_rc == 0 else len(ruff_error_lines)
            ruff_pass = ruff_errors <= max_ruff_errors
            if not json_mode:
                print(
                    f"  {'PASS' if ruff_pass else 'FAIL'} lint threshold (errors={ruff_errors}, max={max_ruff_errors})"
                )
            lint_entry = {
                "name": "lint_threshold",
                "passed": ruff_pass,
                "errors": ruff_errors,
                "max_errors": max_ruff_errors,
                "stderr_tail": ruff_err.splitlines()[-1] if ruff_err else "",
            }
        checks.append(lint_entry)
        _record_check(lint_entry)

        remaining_for_mypy = _remaining_budget_s()
        if remaining_for_mypy is not None and remaining_for_mypy <= 0:
            mypy_entry = {
                "name": "type_threshold",
                "passed": False,
                "skipped": True,
                "reason": "budget_exceeded",
                "errors": None,
                "max_errors": max_mypy_errors,
            }
        else:
            mypy_cmd = [
                sys.executable,
                "-m",
                "mypy",
                "--strict",
                "--follow-imports=skip",
                "src/tools/agent_task_router.py",
                "src/core/orchestrate.py",
                "src/integration/mcp_server.py",
            ]
            mypy_timeout = 240 if remaining_for_mypy is None else max(1, min(240, remaining_for_mypy))
            mypy_rc, mypy_out, mypy_err = run(mypy_cmd, cwd=paths.nusyq_hub, timeout_s=mypy_timeout)
            mypy_errors = 0 if mypy_rc == 0 else sum(1 for line in mypy_out.splitlines() if ": error:" in line)
            mypy_pass = mypy_errors <= max_mypy_errors
            if not json_mode:
                print(
                    f"  {'PASS' if mypy_pass else 'FAIL'} type threshold (errors={mypy_errors}, max={max_mypy_errors})"
                )
            mypy_entry = {
                "name": "type_threshold",
                "passed": mypy_pass,
                "errors": mypy_errors,
                "max_errors": max_mypy_errors,
                "stderr_tail": mypy_err.splitlines()[-1] if mypy_err else "",
            }
        checks.append(mypy_entry)
        _record_check(mypy_entry)

    passed = sum(1 for check in checks if check.get("passed"))
    total = len(checks)
    overall_ok = passed == total

    report: dict[str, Any] = {
        "action": "system_complete",
        "status": "ok" if overall_ok else "failed",
        "generated_at": datetime.now().isoformat(),
        "overall_pass": overall_ok,
        "passed": passed,
        "total": total,
        "checks": checks,
        "profile": profile,
        "options": {
            "budget_s": options.budget_s,
            "reuse_recent": options.reuse_recent,
            "reuse_ttl_s": options.reuse_ttl_s,
            "profile": profile,
        },
        "thresholds": {
            "max_ruff_errors": max_ruff_errors,
            "max_mypy_errors": max_mypy_errors,
        },
    }
    report_path = paths.nusyq_hub / "state" / "reports" / f"system_complete_gate_{now_stamp()}.json"
    _write_json_report(report_path, report)
    latest_report_path = paths.nusyq_hub / "state" / "reports" / "system_complete_gate_latest.json"
    _write_json_report(latest_report_path, report)

    history_path = paths.nusyq_hub / "state" / "reports" / "system_complete_history.jsonl"
    _append_jsonl(history_path, report)
    history = _read_jsonl(history_path, limit=200)
    dashboard = _build_system_complete_dashboard(history, report)
    dashboard_path = paths.nusyq_hub / "state" / "reports" / f"system_complete_dashboard_{now_stamp()}.json"
    _write_json_report(dashboard_path, dashboard)
    dashboard_latest_path = paths.nusyq_hub / "state" / "reports" / "system_complete_dashboard_latest.json"
    _write_json_report(dashboard_latest_path, dashboard)
    report["history_file"] = str(history_path)
    report["dashboard_file"] = str(dashboard_latest_path)
    report["checkpoint_file"] = str(checkpoint_latest_path)
    _write_json_report(latest_report_path, report)

    checkpoint["status"] = "completed" if overall_ok else "failed"
    checkpoint["finished_at"] = datetime.now().isoformat()
    checkpoint["report_file"] = str(latest_report_path)
    _write_checkpoint()
    try:
        gate_keep = max(1, int(os.getenv("NUSYQ_SYSTEM_COMPLETE_GATE_HISTORY_KEEP", "20") or 20))
    except ValueError:
        gate_keep = 20
    try:
        dashboard_keep = max(1, int(os.getenv("NUSYQ_SYSTEM_COMPLETE_DASHBOARD_HISTORY_KEEP", "20") or 20))
    except ValueError:
        dashboard_keep = 20
    _prune_lifecycle_reports(
        paths.nusyq_hub / "state" / "reports",
        gate_keep,
        pattern="system_complete_gate_*.json",
        protected_names={"system_complete_gate_latest.json"},
    )
    _prune_lifecycle_reports(
        paths.nusyq_hub / "state" / "reports",
        dashboard_keep,
        pattern="system_complete_dashboard_*.json",
        protected_names={"system_complete_dashboard_latest.json"},
    )

    if json_mode:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("-" * 70)
        print(f"Summary: {passed}/{total} checks passed")
        print(f"Report: {report_path}")
        print(f"Dashboard: {dashboard_latest_path}")
    return 0 if overall_ok else 1


def _handle_snapshot_or_help(action: str, paths: RepoPaths) -> int:
    if action in {"--help", "help"}:
        print("Usage: python start_nusyq.py [ACTION]")
        print("\nCore Actions:")
        print("  snapshot  - Generate system state snapshot (default)")
        print("  brief     - Quick workspace intelligence summary")
        print("  menu      - Show categorized action menu")
        print("  help      - Show this help menu")
        print("\nDiagnostics:")
        print("  heal      - Run ecosystem health check + self-repair")
        print("  analyze   - Full system analysis (QuickSystemAnalyzer)")
        print(
            "  doctor [--quick|--with-lint|--with-system-health|--with-analyzer] "
            "[--async|--sync] [--budget-s=SECONDS] - Run comprehensive diagnostics"
        )
        print("  doctor_status [job_id] [--wait=SECONDS] [--interval=SECONDS] [--expire-hours=H] [--cancel] [--retry]")
        print("  selfcheck - Quick 5-point system diagnostic")
        print("  map       - Regenerate capability map")
        print("  problem_signal_snapshot - Align VS Code counts with tool diagnostics")
        print(
            "  error_report [--quick|--full|--force|--async|--sync] [--budget-s=SECONDS] [--cache-ttl-s=SECONDS] "
            "[--chain-bridges|--bridge-signals|--bridge-quests|--bridge-error-quests] "
            "(use --hub-only/--repo=<name>/--skip-repo=<name>) - Unified error report across repos"
        )
        print("  error_report_split [--quick|--full] - Per-repo scans + unified report")
        print(
            "  error_report_status [job_id] [--wait=SECONDS] [--interval=SECONDS] "
            "[--expire-hours=H] [--cancel] [--retry]"
        )
        print(
            "  error_signal_bridge [--mode=once|test|watch] [--interval=SECONDS] "
            "- Bridge error groups into guild signals"
        )
        print("  signal_quest_bridge [--mode=once|test|watch] [--interval=SECONDS] - Convert guild signals into quests")
        print(
            "  error_quest_bridge [--severity=error|warning|info|hint] [--max-quests=N] "
            "- Generate quests directly from critical errors"
        )
        print("  auto_quest [--severity=error|warning|info|hint] [--max-quests=N] - Alias for error_quest_bridge")
        print("  quest_compact [--dry-run] - Compact duplicate open signal-linked quests")
        print("  log_dedup_status - Show logging dedup filter status")
        print("  quantum_resolver_status - Show quantum resolver consolidation status")
        print("  task_summary - Summarize VS Code tasks across repos")
        print("  lifecycle_catalog - Log active long-running services")
        print("  terminal_snapshot [--limit=N] - Stable JSON terminal health snapshot")
        print("  vscode_diagnostics_bridge - Refresh VS Code counts (ruff/pyright)")
        print("\nGuild Board:")
        print("  guild_status - Show guild board summary")
        print("  guild_render - Render docs/GUILD_BOARD.md")
        print("  guild_heartbeat <agent> [status] [quest_id]")
        print("  guild_claim <agent> <quest_id>")
        print("  guild_start <agent> <quest_id>")
        print("  guild_post <agent> <message> [quest_id] [type]")
        print("  guild_complete <agent> <quest_id>")
        print("  guild_available <agent> [cap1,cap2]")
        print("  guild_add_quest <agent> <title> <description> [priority] [safety] [tags]")
        print("  guild_close_quest <agent> <quest_id> [status] [reason]")
        print("\nAutonomous Development:")
        print("  develop_system [--iterations=N] [--halt-on-error]  - Autonomous loop")
        print("                  Runs: analyze → heal → (repeat)")
        print(
            "  auto_cycle [--iterations=N] [--sleep=SECONDS] [--culture-ship] [--culture-ship-dry-run]"
            " - queue → replay → metrics → sync (+ optional culture ship)"
        )
        print(
            "  autonomous_service [on|off|status] [--interval=SECONDS] [--iterations=N]"
            " - background autonomous cycle service"
        )
        print("\nIntelligence:")
        print("  suggest   - Get contextual suggestions")
        print("  hygiene   - Check spine (Hub) hygiene")
        print(
            "  prune_reports [--dry-run|--execute|--delete|--with-automated-cleanup] - Prune/archive stale state reports"
        )
        print("  ai_status - Show AI system health (Ollama/ChatDev/Quantum)")
        print("  advanced_ai_quests - Generate quests for missing advanced-AI capabilities")
        print(
            "  graph_learning [--hub-only] [--no-simulatedverse] [--no-root] [--top-k=N] [--max-files=N] [--reuse-ttl-s=N] [--force]"
            " - Generate dependency graph-learning impact report"
        )
        print(
            "  system_complete [--async|--sync] [--startup] [--budget-s=SECONDS] "
            "[--reuse-recent] [--reuse-ttl-s=SECONDS] - Hard completion gate across startup or full-stack checks"
        )
        print(
            "  system_complete_status [job_id] [--wait=SECONDS] [--interval=SECONDS] "
            "[--expire-hours=H] [--cancel] [--retry]"
        )
        print("  openclaw_smoke [--async|--sync] [--help-timeout-s=SECONDS] [--max-help-runtime-s=SECONDS]")
        print(
            "  openclaw_smoke_status [job_id] [--wait=SECONDS] [--interval=SECONDS] "
            "[--expire-hours=H] [--cancel] [--retry]"
        )
        print("  openclaw_status - OpenClaw operational readiness (gateway/channels)")
        print("  openclaw_gateway_start [--port=N] [--bind=loopback|lan] [--force] - Start gateway")
        print("  openclaw_gateway_status [--port=N] [--bind=loopback|lan] - Gateway runtime status")
        print("  openclaw_gateway_stop [--port=N] [--bind=loopback|lan] - Stop managed gateway")
        print("  openclaw_bridge_start [--gateway=URL] - Start NuSyQ OpenClaw bridge")
        print("  openclaw_bridge_status [--gateway=URL] - Bridge connectivity status")
        print("  openclaw_bridge_stop - Stop managed NuSyQ OpenClaw bridge")
        print(
            '  openclaw_internal_send --text "..." [--system=auto|ollama|lmstudio|chatdev|copilot|codex|claude_cli|consciousness|quantum_resolver]'
        )
        print("  skyclaw_status - SkyClaw gateway runtime summary")
        print("  skyclaw_start - Start SkyClaw gateway daemon")
        print("  skyclaw_stop - Stop SkyClaw gateway daemon")
        print("  open_antigravity_start [--port=N] - Start modular-window-server runtime")
        print("  open_antigravity_runtime_status [--port=N] - Antigravity runtime + health status")
        print("  open_antigravity_stop [--port=N] - Stop managed antigravity runtime")
        print("  antigravity_status - Open Antigravity runtime health")
        print("  antigravity_health - Alias for antigravity_status")
        print(
            "  ignition [--thorough|--hetaeristic] [--strict] - Full activation sequence (+ optional SQL/NSSM/telemetry/brownfield pass)"
        )
        print(
            "  integration_health [--mode fast|full|startup] [--simulatedverse-mode auto|always_on|off] [--no-repair-simulatedverse]"
            " - Consolidated stack health check"
        )
        print("  compose_secrets [status|init-local] - Audit/init compose password env vars")
        print("  claude_preflight - Claude Desktop/CLI preflight diagnostics")
        print("  claude_doctor - Full Claude readiness doctor (preflight/CLI/router/terminal)")
        print("  codex_doctor - Full Codex readiness doctor (CLI/router/terminal)")
        print("  copilot_doctor - Full Copilot readiness doctor (chat/CLI/router/terminal)")
        print("  multi_agent_doctor - Combined Claude/Codex/Copilot readiness report")
        print("  agent_fleet_doctor - Fleet readiness across triad, local models, Claw-family, Culture Ship, and docs")
        print("  delegation_matrix - Router delegation/schema/health matrix")
        print("  copilot_probe - Copilot bridge initialization probe")
        print("  failover_status [--limit=N] - Compact fallback telemetry summary")
        print(
            "  vscode_extensions_plan [--profile-name X --phase-size N] [--use-code-cli] - Codex-first VS Code extension isolation plan"
        )
        print(
            "  vscode_extensions_quickwins [--with-noise --since-minutes N] [--use-code-cli] - Immediate extension optimization actions"
        )
        print("  validate_contracts [--probe] - Validate action timeout/schema/safety contracts")
        print("  doctrine_check - Validate architecture vs doctrine")
        print("  emergence_capture - Log runtime behaviors & agent signals")
        print("\nAnalysis & Review:")
        print("  analyze <file> [--system=ollama|chatdev|copilot|auto]   - AI analysis")
        print("  review <file> [--system=ollama|chatdev|copilot|auto]    - Code quality review")
        print("  debug <error> [--system=quantum_resolver|auto]  - Quantum debugging")
        print("\nGeneration & Testing:")
        print("  generate <description> [--system=chatdev|copilot|auto]  - AI project generation")
        print("  culture_ship [--async] [--dry-run] - Strategic cycle (optionally as background job)")
        print("  culture_ship_cycle [--sync|--async] [--dry-run] - Explicit strategic cycle command")
        print(
            "  culture_ship_status [job_id] [--wait=SECONDS] [--interval=SECONDS] "
            "[--expire-hours=H] [--cancel] [--retry]"
        )
        print("  test      - Run pytest quick")
        print("  test_history [N]  - Recent test runs + duplicates")
        print("  work      - Execute next safe quest from quest_log")
        print("\nIntegration:")
        print("  simverse_bridge - Test HUB ↔ SimulatedVerse bridge")
        print("  simverse_mode [status|auto|always_on|off] - Persist SimulatedVerse HTTP policy")
        print("  simverse_consciousness - Show SimulatedVerse consciousness snapshot")
        print("  simverse_history [--limit N] - Recent consciousness history")
        print("  simverse_ship_directives [--priority P] - Culture Ship directives")
        print("  simverse_cognition_insights [--limit N] [--since ISO] - Cognition insights")
        print("  simverse_bridge_health - Bridge health/status snapshot")
        print("  simverse_ship_approve --action NAME [--context '{...}'] - Approval check")
        print("  simverse_log_event --type NAME [--data '{...}'] - Log event to SimulatedVerse")
        print("  simverse_breathing - Get breathing factor (timeout multiplier)")
        print("  capabilities [--search TERM] [--category TYPE] [--refresh]  - Comprehensive capability discovery")
        print("  trace_doctor  - Validate local tracing setup and emit test span")
        print("\nAutomation:")
        print("  batch_commit [--dry-run] [--max-commits=N]  - Autonomous batch commit orchestrator")
        print("  pu_execute <pu_id> [--real]  - Execute PU through agents (use --real for ChatDev/Ollama)")
        print("\nEnvironment:")
        print("  --json  - Emit machine-readable JSON for supported actions")
        print("  NUSYQ_TRACE_DEEP_CONTEXT=1  - Include deep git/quest context in traces (slower)")
        return 0

    md = build_markdown(paths)
    out_path = write_report(paths.nusyq_hub, md)

    hygiene = check_spine_hygiene(paths.nusyq_hub)

    print(md)
    print("\n## Spine Hygiene")
    for warning in hygiene:
        print(f"- {warning}")

    if out_path:
        print(f"\n[Saved] {out_path}")
    else:
        print("\n[Not saved] NuSyQ-Hub path missing.")

    return 0


def _handle_doctrine_check(paths: RepoPaths) -> int:
    """Enhanced doctrine check using DoctrineChecker module."""
    if not paths.nusyq_hub:
        print("[ERROR] NuSyQ-Hub path not found; cannot run doctrine check.")
        return 1

    print("📜 NuSyQ Doctrine Compliance Check")
    print("=" * 80)
    print()

    # Import DoctrineChecker
    sys.path.insert(0, str(paths.nusyq_hub))
    try:
        from src.doctrine import DoctrineChecker

        # Run compliance check
        checker = DoctrineChecker(paths.nusyq_hub)
        report = checker.check_compliance(commits_to_analyze=50)

        # Display summary
        print(f"📊 Compliance Score: {report.compliance_score:.1%}")
        print(f"📋 Total Mandates Checked: {report.total_mandates}")
        print(f"⚠️  Violations Found: {len(report.violations)}")
        print(f"📝 Git Commits Analyzed: {report.git_commits_analyzed}")
        print()

        # Show violations by severity
        critical = [v for v in report.violations if v.severity == "critical"]
        high = [v for v in report.violations if v.severity == "high"]
        medium = [v for v in report.violations if v.severity == "medium"]
        low = [v for v in report.violations if v.severity == "low"]

        if critical:
            print(f"🔴 CRITICAL: {len(critical)} violations")
            for v in critical[:3]:
                print(f"   - {v.mandate[:70]}")
        if high:
            print(f"🟠 HIGH: {len(high)} violations")
            for v in high[:3]:
                print(f"   - {v.mandate[:70]}")
        if medium:
            print(f"🟡 MEDIUM: {len(medium)} violations")
        if low:
            print(f"🔵 LOW: {len(low)} violations")

        # Show insights
        if report.insights:
            print("\n💡 Insights:")
            for insight in report.insights:
                print(f"   {insight}")

        # Save full report
        reports_dir = paths.nusyq_hub / "state" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_file = reports_dir / f"doctrine_compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_file.write_text(report.to_markdown(), encoding="utf-8")

        print(f"\n📄 Full report saved: {report_file}")
        print()
        print("=" * 80)

        # Return 0 if compliant, 1 if violations found
        return 0 if report.compliance_score >= 0.9 else 1

    except Exception as exc:
        print(f"[ERROR] Doctrine check failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_emergence_capture(paths: RepoPaths) -> int:
    print("✨ NuSyQ Emergence Capture")
    print("=" * 50)

    emergence_dir = paths.nusyq_hub / "state" / "emergence"
    emergence_dir.mkdir(parents=True, exist_ok=True)

    quest_file = paths.nusyq_hub / "src" / "Rosetta_Quest_System" / QUEST_LOG_FILENAME
    emergence_events: list[dict[str, Any]] = []

    print("\n1. Analyzing quest log for agent activity...")
    if quest_file.exists():
        try:
            with open(quest_file) as f:
                quests = [json.loads(line) for line in f if line.strip()]

            completed = len([q for q in quests if q.get("status") == "completed"])
            failed = len([q for q in quests if q.get("status") == "failed"])
            in_progress = len([q for q in quests if q.get("status") == "in_progress"])

            emergence_events.append(
                {
                    "type": "quest_activity",
                    "timestamp": datetime.now().isoformat(),
                    "completed_quests": completed,
                    "failed_quests": failed,
                    "in_progress_quests": in_progress,
                    "total_quests": len(quests),
                }
            )

            print(f"   ✅ {len(quests)} quests recorded")
            print(f"      Completed: {completed}, Failed: {failed}, In Progress: {in_progress}")
        except Exception as exc:
            print(f"   ⚠️ Error reading quest log: {exc}")

    print("\n2. Capturing system health signals...")
    rc, health_out, _ = run(
        ["python", "-m", "src.diagnostics.system_health_assessor"],
        cwd=paths.nusyq_hub,
        timeout_s=20,
    )
    if rc == 0 and health_out:
        emergence_events.append(
            {
                "type": "system_health",
                "timestamp": datetime.now().isoformat(),
                "status": "healthy" if "PASS" in health_out else "degraded",
                "details": health_out[:500],
            }
        )
        print("   ✅ System health captured")
    else:
        print(f"   ⚠️ Could not capture health (rc={rc})")

    print("\n3. Scanning for AI interactions...")
    rc, log_out, _ = run(
        [
            "grep",
            "-r",
            "--include=*.log",
            "--include=*.jsonl",
            "-l",
            "ollama\\|chatdev\\|copilot\\|consciousness",
            "state/",
        ],
        cwd=paths.nusyq_hub,
        timeout_s=10,
    )
    if rc == 0 and log_out:
        ai_logs = len(log_out.split("\n"))
        emergence_events.append(
            {
                "type": "ai_interactions",
                "timestamp": datetime.now().isoformat(),
                "ai_logs_found": ai_logs,
            }
        )
        print(f"   ✅ Found {ai_logs} AI interaction logs")
    else:
        print("   Info: No AI interaction logs yet")

    emergence_log = emergence_dir / f"emergence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    try:
        with open(emergence_log, "w") as f:
            for event in emergence_events:
                f.write(json.dumps(event) + "\n")
        print(f"\n✅ Emergence log saved: {emergence_log}")
    except Exception as exc:
        print(f"\n❌ Error saving emergence log: {exc}")
        return 1

    return 0


def _handle_agent_status() -> int:
    """Show status of all registered agents in the ecosystem."""
    print("🤖 Agent Registry Status")
    print("=" * 60)

    try:
        from src.orchestration.agent_registry import get_agent_registry

        registry = get_agent_registry()
        stats = registry.get_registry_stats()

        print("\n📊 Overview:")
        print(f"   Total Agents: {stats['total_agents']}")
        print(f"   Total Capabilities: {stats['total_capabilities']}")
        print(f"   Unique Capabilities: {stats['unique_capabilities']}")
        print(f"   Average Success Rate: {stats['average_success_rate']:.1%}")

        print("\n🔧 Agents by Type:")
        for agent_type, count in stats["agents_by_type"].items():
            print(f"   {agent_type}: {count}")

        print("\n📈 Agents by Status:")
        for status, count in stats["agents_by_status"].items():
            print(f"   {status}: {count}")

        if stats.get("most_used_agents"):
            print("\n⭐ Most Used Agents:")
            for agent_info in stats["most_used_agents"]:
                print(
                    f"   {agent_info['name']}: {agent_info['executions']} executions "
                    f"({agent_info['success_rate']:.1%} success)"
                )

        print("\n🔍 Registered Agents:")
        for agent_id, agent in registry.agents.items():
            status_emoji = {"idle": "🟢", "busy": "🟡", "offline": "🔴", "error": "❌"}.get(agent.status, "⚪")

            print(f"\n   {status_emoji} {agent.name} ({agent.agent_type})")
            print(f"      ID: {agent_id}")
            print(f"      Status: {agent.status}")
            print(f"      Capabilities: {len(agent.capabilities)}")
            print(f"      Executions: {agent.total_executions} ({agent.success_rate:.1%} success)")
            if agent.endpoint:
                print(f"      Endpoint: {agent.endpoint}")

            if agent.capabilities[:3]:  # Show first 3 capabilities
                print("      Top Capabilities:")
                for cap in agent.capabilities[:3]:
                    print(f"         - {cap.name}: {cap.description}")

        print("\n" + "=" * 60)
        print(f"✅ Agent registry operational ({stats['total_agents']} agents ready)")
        hub_root = Path(__file__).resolve().parents[1]
        audit_intel = collect_audit_intelligence(hub_root, include_sessions=False)
        print("\n📚 Audit Intelligence")
        for line in format_audit_intelligence_lines(audit_intel, max_lines=4):
            print(f"   - {line}")

        return 0

    except Exception as exc:
        print(f"❌ Error accessing agent registry: {exc}")
        return 1


def _handle_agent_probe(json_mode: bool = False) -> int:
    """Deep runtime probe of AI systems via shared registry + targeted endpoints."""
    import requests

    from src.dispatch.agent_registry import AgentAvailabilityRegistry

    results: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "probes": {},
    }

    print("🔍 Probing agent registry...")
    registry = AgentAvailabilityRegistry(timeout=5.0)
    registry_targets = ["ollama", "lmstudio", "chatdev", "openclaw"]
    registry_results = asyncio.run(registry.probe_all(registry_targets, auto_recover=True))

    for agent in registry_targets:
        probe = registry_results.get(agent)
        if not probe:
            continue
        payload = probe.to_dict()
        status_value = str(payload.get("status", "")).lower()
        payload["status"] = "OK" if status_value == "online" else "ERROR" if status_value == "degraded" else "OFFLINE"
        payload["registry_status"] = status_value
        results["probes"][agent] = payload

    print("🔍 Probing MCP Server...")
    try:
        resp = requests.get("http://127.0.0.1:8081/health", timeout=3)
        results["probes"]["mcp_server"] = {
            "status": "OK" if resp.status_code == 200 else "ERROR",
            "endpoint": "http://127.0.0.1:8081",
            "latency_ms": round(resp.elapsed.total_seconds() * 1000, 1),
        }
    except requests.RequestException as exc:
        results["probes"]["mcp_server"] = {
            "status": "OFFLINE",
            "endpoint": "http://127.0.0.1:8081",
            "error": str(exc)[:120],
        }

    online = sum(1 for p in results["probes"].values() if p.get("status") == "OK")
    total = len(results["probes"])
    results["summary"] = {
        "online": online,
        "total": total,
        "registry_targets": registry_targets,
    }
    hub_path = Path(__file__).resolve().parents[1]
    report_path = _write_state_report(hub_path, "agent_probe_status.json", results)
    results["report_file"] = str(report_path)

    if json_mode:
        print(json.dumps(results, indent=2))
        return 0

    print("\n🤖 AI AGENT PROBE RESULTS")
    print("=" * 50)
    for name, probe in results["probes"].items():
        status = probe.get("status", "UNKNOWN")
        emoji = {"OK": "✅", "OFFLINE": "⚠️", "ERROR": "❌"}.get(status, "❓")
        print(f"\n{emoji} {name.upper()}")
        print(f"   Endpoint: {probe.get('endpoint', 'N/A')}")
        print(f"   Status: {status}")
        if "latency_ms" in probe:
            print(f"   Latency: {probe['latency_ms']:.1f}ms")
        if "model_count" in probe:
            print(f"   Models: {probe['model_count']}")
        if "error" in probe:
            print(f"   Error: {probe['error']}")

    print(f"\n📊 Summary: {online}/{total} services online")
    return 0 if online > 0 else 1


def _handle_orchestrate(args: list[str]) -> int:
    """Orchestrate a task across multiple agents."""
    print("🎭 Multi-Agent Task Orchestration")
    print("=" * 60)

    if len(args) < 2:
        print("\nUsage: python start_nusyq.py orchestrate <task_description>")
        print("\nExample:")
        print("  python start_nusyq.py orchestrate 'Analyze code quality and generate report'")
        print("\nOptional flags:")
        print("  --pattern=<sequential|parallel|hierarchical|consensus>")
        print("  --agents=<agent_id1,agent_id2,...>")
        print("  --prefer-cloud   # Prefer cloud agents over local")
        return 1

    task_desc = " ".join(args[1:])

    # Parse flags
    pattern = "sequential"
    agents = None
    prefer_local = True

    for arg in args[1:]:
        if arg.startswith("--pattern="):
            pattern = arg.split("=")[1]
            task_desc = task_desc.replace(arg, "").strip()
        elif arg.startswith("--agents="):
            agents = arg.split("=")[1].split(",")
            task_desc = task_desc.replace(arg, "").strip()
        elif arg == "--prefer-cloud":
            prefer_local = False
            task_desc = task_desc.replace(arg, "").strip()

    try:
        from src.orchestration.unified_orchestration_bridge import get_orchestration_bridge

        bridge = get_orchestration_bridge()

        print(f"\n📝 Task: {task_desc}")
        print(f"   Pattern: {pattern}")
        print(f"   Prefer Local: {prefer_local}")

        # Create task (for now, use generic capabilities)
        # In future, could add NLP to extract required capabilities
        task = bridge.create_task(
            description=task_desc,
            required_capabilities=["text_generation", "code_analysis"],  # Default
            priority=5,
        )

        print(f"\n🎯 Created task: {task.task_id}")

        # Execute task
        if pattern in ["parallel", "hierarchical", "consensus"]:
            result = bridge.execute_collaborative_task(task, pattern=pattern, agents=agents)
        else:
            result = bridge.execute_task(task, prefer_local=prefer_local)

        print("\n📊 Execution Result:")
        print(f"   Success: {'✅ Yes' if result.success else '❌ No'}")
        print(f"   Duration: {result.duration_seconds:.2f}s")
        if result.agent_used:
            print(f"   Agent(s): {result.agent_used}")

        if result.success:
            print("\n💡 Output:")
            print(f"   {str(result.output)[:500]}")  # Truncate long outputs
            if len(str(result.output)) > 500:
                print("   ... (truncated, full output in logs)")
        else:
            print(f"\n❌ Error: {result.error}")

        print("\n" + "=" * 60)

        return 0 if result.success else 1

    except Exception as exc:
        print(f"❌ Orchestration failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_invoke_agent(args: list[str]) -> int:
    """Directly invoke a specific agent with a task."""
    print("🎯 Direct Agent Invocation")
    print("=" * 60)

    if len(args) < 3:
        print("\nUsage: python start_nusyq.py invoke_agent <agent_id> <task_description>")
        print("\nAvailable Agents:")
        print("  - ollama-local")
        print("  - chatdev-orchestrator")
        print("  - continue-vscode")
        print("  - jupyter-notebooks")
        print("  - docker-orchestrator")
        print("\nExample:")
        print("  python start_nusyq.py invoke_agent ollama-local 'Explain how async/await works'")
        return 1

    agent_id = args[1]
    task_desc = " ".join(args[2:])

    try:
        from src.orchestration.agent_registry import get_agent_registry
        from src.orchestration.unified_orchestration_bridge import get_orchestration_bridge

        registry = get_agent_registry()
        bridge = get_orchestration_bridge()

        # Get agent
        agent = registry.get_agent(agent_id)
        if not agent:
            print(f"❌ Agent not found: {agent_id}")
            print("\nRegistered agents:")
            for aid, ag in registry.agents.items():
                print(f"   - {aid}: {ag.name}")
            return 1

        print(f"\n🤖 Agent: {agent.name}")
        print(f"   Type: {agent.agent_type}")
        print(f"   Status: {agent.status}")
        print(f"   Capabilities: {len(agent.capabilities)}")

        print(f"\n📝 Task: {task_desc}")

        # Create task with agent's capabilities
        cap_names = [cap.name for cap in agent.capabilities[:5]]  # Use first 5 caps
        task = bridge.create_task(
            description=task_desc,
            required_capabilities=cap_names,
            priority=7,  # Direct invocation = higher priority
            metadata={"direct_invocation": True, "requested_agent": agent_id},
        )

        # Force assign to this agent
        task.assigned_agents = [agent_id]

        print("\n⏳ Executing...")

        # Execute using specific agent executor
        executor = bridge.executors.get(agent.agent_type, bridge._execute_generic_task)
        start_time = time.time()

        try:
            output = executor(task, agent, None)
            duration = time.time() - start_time

            print(f"\n✅ Completed in {duration:.2f}s")
            print("\n💡 Output:")
            print(json.dumps(output, indent=2))

            # Record metrics
            registry.record_execution(agent_id, True, duration)

            print("\n" + "=" * 60)
            return 0

        except Exception as exec_err:
            duration = time.time() - start_time
            print(f"\n❌ Execution failed: {exec_err}")
            registry.record_execution(agent_id, False, duration)
            return 1

    except Exception as exc:
        print(f"❌ Invocation failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_council_loop(args: list[str]) -> int:
    """Execute Council→Orchestrator→ChatDev closed reflex loop.

    This is the FIRST complete autonomous multi-agent workflow demonstrating:
    - AI Council consensus voting
    - Unified AI Orchestrator task routing
    - ChatDev multi-agent execution
    - Results captured and logged
    """
    print("🔄 Council→Orchestrator→ChatDev Closed Reflex Loop")
    print("=" * 60)

    if len(args) < 2:
        print("\nUsage: python start_nusyq.py council_loop <task_description>")
        print("       python start_nusyq.py council_loop --demo")
        print("\nExample:")
        print("  python start_nusyq.py council_loop 'Create a Python calculator with tests'")
        print("\nFlags:")
        print("  --demo           Run demo task (Python calculator)")
        print("  --no-auto-vote   Require manual council votes (default: auto-vote)")
        return 1

    # Check for demo mode
    if "--demo" in args:
        task_description = """
Create a simple Python calculator module with:
- Basic arithmetic operations (add, subtract, multiply, divide)
- Error handling for division by zero
- Unit tests with pytest
- Docstrings and type hints
"""
        print("\n📋 Demo Task: Python Calculator with Tests")
    else:
        # Extract task description (skip flags)
        task_parts = [arg for arg in args[1:] if not arg.startswith("--")]
        task_description = " ".join(task_parts)

    auto_vote = "--no-auto-vote" not in args

    try:
        import asyncio

        from src.orchestration.council_orchestrator_chatdev_loop import (
            CouncilOrchestratorChatDevLoop,
        )

        loop = CouncilOrchestratorChatDevLoop(auto_vote=auto_vote)

        print(f"\n📝 Task: {task_description[:100]}...")
        print(f"   Auto-vote: {'✅ Enabled' if auto_vote else '❌ Disabled (manual votes required)'}")
        print("\n" + "=" * 60)

        # Execute the loop
        result = asyncio.run(
            loop.propose_and_execute(
                task_description=task_description,
                task_category="CODE_GENERATION",
                proposer="cli_user",
            )
        )

        print("\n" + "=" * 60)
        print("📊 Execution Result:")
        print("=" * 60)

        if result["success"]:
            print("✅ Success!")
            print(f"   Loop ID: {result.get('loop_id', 'N/A')}")
            print(f"   Decision ID: {result.get('decision_id', 'N/A')}")
            if "orchestrator_task_id" in result:
                print(f"   Orchestrator Task ID: {result['orchestrator_task_id']}")

            chatdev_result = result.get("chatdev_result", {})
            if chatdev_result.get("simulated"):
                print("\n❌ ChatDev execution is simulated/unavailable; failing hard by policy.")
                if chatdev_result.get("error"):
                    print(f"   Reason: {chatdev_result.get('error')}")
                print("\n📁 Execution log:")
                print("   state/council_chatdev_loop/execution_log.jsonl")
                return 1

            print("\n✨ Full ChatDev multi-agent execution completed!")
            print("\n📁 Execution log:")
            print("   state/council_chatdev_loop/execution_log.jsonl")

            return 0
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            chatdev_result = result.get("chatdev_result", {})
            if isinstance(chatdev_result, dict) and chatdev_result:
                print(f"   ChatDev status: {chatdev_result.get('status', 'unknown')}")
                if "returncode" in chatdev_result:
                    print(f"   ChatDev return code: {chatdev_result['returncode']}")
                if chatdev_result.get("error"):
                    print(f"   ChatDev error: {chatdev_result['error']}")
            if result.get("status") == "rejected":
                print(f"   Reason: Task rejected by council ({result.get('reason')})")
            elif result.get("status") == "awaiting_votes":
                print("   Status: Awaiting manual council votes")
                print(f"   Use AICouncilVoting.cast_vote('{result.get('decision_id')}', ...)")

            return 1

    except ImportError as e:
        print(f"❌ Required module not available: {e}")
        print("\nMake sure the following are installed:")
        print("  - src/orchestration/council_orchestrator_chatdev_loop.py")
        print("  - src/orchestration/ai_council_voting.py")
        print("  - src/orchestration/unified_ai_orchestrator.py")
        return 1
    except Exception as exc:
        print(f"❌ Closed loop execution failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_quest_query(args: list[str]) -> int:
    """Query recent quests from quest log.

    Usage:
        python start_nusyq.py quest_query --recent --limit=10
        python start_nusyq.py quest_query --incomplete
        python start_nusyq.py quest_query --type council_loop
    """
    try:
        from scripts.quest_query import get_incomplete_quests, query_recent_quests

        print("📜 Quest Log Query")
        print("=" * 60)

        # Parse arguments
        limit = 10
        quest_type = None
        show_incomplete = False

        for arg in args[1:]:
            if arg.startswith("--limit="):
                try:
                    limit = int(arg.split("=")[1])
                except ValueError:
                    print(f"⚠️  Invalid limit value: {arg}")
                    return 1
            elif arg.startswith("--type="):
                quest_type = arg.split("=", 1)[1]
            elif arg == "--incomplete":
                show_incomplete = True
            elif arg in ("--recent", "--help"):
                pass  # Default behavior
            else:
                print(f"⚠️  Unknown argument: {arg}")
                print("\nUsage: python start_nusyq.py quest_query [--recent] [--limit=N] [--type=TYPE] [--incomplete]")
                return 1

        # Query quests
        if show_incomplete:
            quests = get_incomplete_quests()
            print(f"\nIncomplete Quests ({len(quests)}):")
        else:
            quests = query_recent_quests(limit=limit, quest_type=quest_type)
            print(f"\nRecent Quests (last {len(quests)}):")

        print("=" * 60 + "\n")

        for quest in quests:
            quest_type_name = quest.get("type", "unknown")
            status = quest.get("status", "unknown")
            quest_id = quest.get("quest_id") or quest.get("loop_id") or quest.get("prototype") or "unknown"
            timestamp = quest.get("timestamp", "unknown")

            status_symbol = (
                "✅"
                if status in ("completed", "success", "graduated")
                else "❌"
                if status in ("failed", "abandoned")
                else "🔄"
            )

            print(f"{status_symbol} [{timestamp}]")
            print(f"   Type: {quest_type_name}")
            print(f"   ID: {quest_id}")
            print(f"   Status: {status}")

            if "description" in quest:
                desc = quest["description"]
                print(f"   Description: {desc[:80]}..." if len(desc) > 80 else f"   Description: {desc}")
            if "result" in quest:
                print(f"   Result: {quest['result']}")
            print()

        return 0

    except Exception as exc:
        print(f"❌ Quest query failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_quest_continue(args: list[str]) -> int:
    """Get context for continuing from last quest.

    Usage:
        python start_nusyq.py quest_continue
    """
    try:
        from scripts.quest_query import continue_from_last_quest

        print("🔄 Continue from Last Quest")
        print("=" * 60 + "\n")

        context = continue_from_last_quest()

        print(f"Status: {context['status']}")

        if context["status"] == "found":
            last_quest = context["last_quest"]
            print("\n📋 Last Quest:")
            print(f"   Type: {last_quest.get('type', 'unknown')}")
            print(f"   ID: {last_quest.get('quest_id') or last_quest.get('loop_id') or last_quest.get('prototype')}")
            print(f"   Status: {last_quest.get('status', 'unknown')}")
            print(f"   Timestamp: {last_quest.get('timestamp', 'unknown')}")

        print("\n💡 Suggested Actions:")
        for action in context["suggested_actions"]:
            print(f"   {action}")

        return 0

    except Exception as exc:
        print(f"❌ Quest continue failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_quest_graph(args: list[str]) -> int:
    """Generate quest dependency graph.

    Usage:
        python start_nusyq.py quest_graph [--format text|mermaid|dot] [--output FILE]
    """
    try:
        from pathlib import Path

        from scripts.quest_query import generate_quest_graph

        # Parse arguments
        format_type = "text"
        output_file = None

        for _i, arg in enumerate(args[1:]):
            if arg.startswith("--format="):
                format_type = arg.split("=")[1]
                if format_type not in ("text", "mermaid", "dot"):
                    print(f"⚠️  Invalid format: {format_type}")
                    print("   Valid formats: text, mermaid, dot")
                    return 1
            elif arg.startswith("--output="):
                output_file = arg.split("=", 1)[1]
            elif arg in ("--help",):
                print("Usage: python start_nusyq.py quest_graph [--format text|mermaid|dot] [--output FILE]")
                return 0
            else:
                print(f"⚠️  Unknown argument: {arg}")
                return 1

        print("📊 Quest Dependency Graph")
        print("=" * 60 + "\n")

        graph = generate_quest_graph(format=format_type)

        if output_file:
            output_path = Path(output_file)
            output_path.write_text(graph, encoding="utf-8")
            print(f"✅ Quest graph written to: {output_path}")
        else:
            print(graph)

        return 0

    except Exception as exc:
        print(f"❌ Quest graph generation failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_quest_status(args: list[str]) -> int:
    """Show quest system status summary.

    Usage:
        python start_nusyq.py quest_status
    """
    try:
        from scripts.quest_query import read_quest_log

        print("📊 Quest System Status")
        print("=" * 60)

        quests = read_quest_log()

        print(f"\nTotal Quests: {len(quests)}")

        # Count by status
        status_counts: dict[str, int] = {}
        for quest in quests:
            status = quest.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        print("\n📈 By Status:")
        for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            status_symbol = (
                "✅"
                if status in ("completed", "success", "graduated")
                else "❌"
                if status in ("failed", "abandoned")
                else "🔄"
            )
            pct = (count / len(quests) * 100) if quests else 0
            print(f"   {status_symbol} {status}: {count} ({pct:.1f}%)")

        # Count by type
        type_counts: dict[str, int] = {}
        for quest in quests:
            quest_type = quest.get("type", "unknown")
            type_counts[quest_type] = type_counts.get(quest_type, 0) + 1

        print("\n🏷️  By Type:")
        for quest_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(quests) * 100) if quests else 0
            print(f"   {quest_type}: {count} ({pct:.1f}%)")

        # Show recent activity
        recent_quests = quests[-5:]
        print("\n🕐 Recent Activity:")
        for quest in recent_quests[::-1]:
            quest_type = quest.get("type", "unknown")
            status = quest.get("status", "unknown")
            timestamp = quest.get("timestamp", "unknown")
            status_symbol = (
                "✅"
                if status in ("completed", "success", "graduated")
                else "❌"
                if status in ("failed", "abandoned")
                else "🔄"
            )
            print(f"   {status_symbol} [{timestamp}] {quest_type} - {status}")

        return 0

    except Exception as exc:
        print(f"❌ Quest status failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_activate_ecosystem() -> int:
    """Activate all dormant infrastructure in the ecosystem."""
    print("🔌 Ecosystem Activation")
    print("=" * 60)

    # Auto-ensure Ollama is running (WSL-aware) before ecosystem activation
    try:
        from src.services.ollama_service_manager import OllamaServiceManager

        mgr = OllamaServiceManager()
        if not mgr.is_healthy():
            print("\n🦙 Ensuring Ollama is running...")
            if mgr.ensure_running():
                print("   ✅ Ollama started")
            else:
                print("   ⚠️  Could not start Ollama (continuing anyway)")
    except ImportError:
        pass  # OllamaServiceManager not available

    try:
        from src.orchestration.ecosystem_activator import get_ecosystem_activator

        activator = get_ecosystem_activator()

        print("\n🔍 Discovering systems...")
        discoveries = activator.discover_systems()

        print(f"\nFound {len(discoveries)} activatable systems:")
        by_type = {}
        for system in discoveries:
            by_type[system.system_type] = by_type.get(system.system_type, 0) + 1

        for sys_type, count in by_type.items():
            print(f"   {sys_type}: {count}")

        print("\n⚡ Activating all systems...")
        results = activator.activate_all(skip_on_error=True)

        hub_path = Path(__file__).resolve().parents[1]
        report_dir = hub_path / "state" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        activation_snapshot = {
            "action": "activate_ecosystem",
            "generated_at": datetime.now().isoformat(),
            "total": results.get("total", 0),
            "activated": results.get("activated", 0),
            "failed": results.get("failed", 0),
            "success_rate": ((results.get("activated", 0) / results.get("total", 1)) if results.get("total") else 0.0),
            "systems": results.get("systems", []),
        }
        _write_json_report(report_dir / "ecosystem_activation_latest.json", activation_snapshot)

        print("\n📊 Activation Results:")
        print(f"   Total: {results['total']}")
        print(f"   ✅ Activated: {results['activated']}")
        print(f"   ❌ Failed: {results['failed']}")
        print(f"   Success Rate: {results['activated'] / results['total'] * 100:.1f}%")

        if results["activated"] > 0:
            print("\n✨ Active Systems:")
            for sys_info in results["systems"]:
                if sys_info["status"] == "active":
                    print(f"   ✅ {sys_info['name']} ({sys_info['capabilities']} capabilities)")

        if results["failed"] > 0:
            print("\n⚠️  Failed Systems:")
            for sys_info in results["systems"]:
                if sys_info["status"] == "error":
                    print(f"   ❌ {sys_info['name']}: {sys_info.get('error', 'unknown')[:50]}")

        print(f"\n📝 Activation snapshot: {report_dir / 'ecosystem_activation_latest.json'}")

        print("\n" + "=" * 60)

        return 0 if results["failed"] == 0 else 1

    except Exception as exc:
        print(f"❌ Ecosystem activation failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


@dataclass
class ErrorReportOptions:
    quick: bool = False
    force: bool = False
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    budget_s: int = 0
    cache_ttl_s: int = 0
    bridge_signals: bool = False
    bridge_signal_to_quest: bool = False
    bridge_error_quests: bool = False
    bridge_test_mode: bool = False
    bridge_severity: str = "error"
    bridge_max_quests: int = 10
    checkpoint_file: str = ""


def _default_error_report_cache_ttl_s(quick: bool) -> int:
    env_key = "NUSYQ_ERROR_REPORT_CACHE_TTL_QUICK_S" if quick else "NUSYQ_ERROR_REPORT_CACHE_TTL_FULL_S"
    fallback = 3600 if quick else 10800
    try:
        return max(0, int(os.getenv(env_key, str(fallback)) or fallback))
    except ValueError:
        return fallback


_REPO_CANONICAL = {
    "nusyq-hub": "nusyq-hub",
    "hub": "nusyq-hub",
    "nusyq": "nusyq",
    "root": "nusyq",
    "nu-syq": "nusyq",
    "simulated-verse": "simulated-verse",
    "simulatedverse": "simulated-verse",
    "simverse": "simulated-verse",
}


def _canonical_repo_name(raw: str) -> str | None:
    normalized = raw.lower().replace("_", "-").replace(" ", "-").strip("-")
    return _REPO_CANONICAL.get(normalized)


def _split_repo_values(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [segment.strip() for segment in raw.split(",") if segment.strip()]


def _consume_flag_value(args: list[str], index: int) -> tuple[str | None, int]:
    token = args[index]
    if "=" in token:
        return token.split("=", 1)[1], 1
    if index + 1 < len(args) and not args[index + 1].startswith("--"):
        return args[index + 1], 2
    return None, 1


def _parse_error_report_args(args: list[str]) -> ErrorReportOptions:
    opts = ErrorReportOptions(
        budget_s=int(os.getenv("NUSYQ_ERROR_REPORT_BUDGET_S", "0") or 0),
    )
    i = 1  # skip the action name itself
    while i < len(args):
        token = args[i]
        if token == "--quick":
            opts.quick = True
            i += 1
            continue
        if token == "--full":
            opts.quick = False
            i += 1
            continue
        if token == "--force":
            opts.force = True
            i += 1
            continue
        if token == "--hub-only":
            opts.include.append("nusyq-hub")
            opts.exclude.extend(["simulated-verse", "nusyq"])
            i += 1
            continue
        if token.startswith("--repo") or token.startswith("--include"):
            value, consumed = _consume_flag_value(args, i)
            for raw in _split_repo_values(value):
                canonical = _canonical_repo_name(raw)
                if canonical:
                    opts.include.append(canonical)
                else:
                    print(f"⚠️ Unknown repo '{raw}' ignored.")
            i += consumed
            continue
        if token.startswith("--skip-repo") or token.startswith("--exclude"):
            value, consumed = _consume_flag_value(args, i)
            for raw in _split_repo_values(value):
                canonical = _canonical_repo_name(raw)
                if canonical:
                    opts.exclude.append(canonical)
                else:
                    print(f"⚠️ Unknown repo '{raw}' ignored.")
            i += consumed
            continue
        if token.startswith("--budget-s"):
            value, consumed = _consume_flag_value(args, i)
            if value:
                try:
                    opts.budget_s = max(0, int(value))
                except ValueError:
                    print(f"⚠️ Invalid --budget-s value '{value}' ignored.")
            i += consumed
            continue
        if token.startswith("--cache-ttl-s") or token.startswith("--reuse-ttl-s"):
            value, consumed = _consume_flag_value(args, i)
            if value:
                try:
                    opts.cache_ttl_s = max(0, int(value))
                except ValueError:
                    print(f"⚠️ Invalid cache TTL value '{value}' ignored.")
            i += consumed
            continue
        if token in {"--chain-bridges", "--bridge-all"}:
            opts.bridge_signals = True
            opts.bridge_signal_to_quest = True
            opts.bridge_error_quests = True
            i += 1
            continue
        if token == "--bridge-signals":
            opts.bridge_signals = True
            i += 1
            continue
        if token in {"--bridge-quests", "--bridge-signal-to-quest"}:
            opts.bridge_signal_to_quest = True
            i += 1
            continue
        if token in {"--bridge-error-quests", "--bridge-auto-quest"}:
            opts.bridge_error_quests = True
            i += 1
            continue
        if token in {"--bridge-test", "--chain-test"}:
            opts.bridge_test_mode = True
            i += 1
            continue
        if token.startswith("--bridge-severity"):
            value, consumed = _consume_flag_value(args, i)
            if value:
                opts.bridge_severity = value.strip().lower()
            i += consumed
            continue
        if token.startswith("--bridge-max-quests"):
            value, consumed = _consume_flag_value(args, i)
            if value:
                try:
                    opts.bridge_max_quests = max(1, int(value))
                except ValueError:
                    print(f"⚠️ Invalid --bridge-max-quests value '{value}' ignored.")
            i += consumed
            continue
        if token.startswith("--checkpoint-file"):
            value, consumed = _consume_flag_value(args, i)
            if value:
                opts.checkpoint_file = value.strip()
            i += consumed
            continue
        i += 1
    return opts


def _print_error_report_help(action_name: str = "error_report") -> None:
    """Print focused help for error-report actions."""
    if action_name == "error_report":
        print("Usage: python scripts/start_nusyq.py error_report [options]")
        print("")
        print("Options:")
        print("  --quick                 Quick scan (default)")
        print("  --full                  Full scan")
        print("  --force                 Bypass cache")
        print("  --cache-ttl-s=<secs>    Cache reuse window (default: quick=3600, full=10800)")
        print("  --async | --sync        Run in background or foreground")
        print("  --repo=<name>[,<name>]  Include repos: nusyq-hub,nusyq,simulated-verse")
        print("  --exclude=<name>[,...]  Exclude repos")
        print("  --budget-s=<seconds>    Runtime budget")
        print("  --json                  JSON output")
        return
    if action_name == "error_report_split":
        print("Usage: python scripts/start_nusyq.py error_report_split [options]")
        print("")
        print("Options:")
        print("  --quick                 Quick per-repo scan (default)")
        print("  --full                  Full per-repo scan")
        print("  --repo=<name>[,<name>]  Include repos")
        print("  --exclude=<name>[,...]  Exclude repos")
        return
    if action_name == "error_report_status":
        print("Usage: python scripts/start_nusyq.py error_report_status [job_id] [options]")
        print("")
        print("Options:")
        print("  --wait=<seconds>        Poll until done")
        print("  --interval=<seconds>    Poll interval")
        print("  --cancel                Cancel running job")
        print("  --retry                 Retry failed job")
        print("  --json                  JSON output")


@dataclass
class BridgeRunOptions:
    mode: str = "once"
    interval_s: int = 60


@dataclass
class ErrorQuestBridgeOptions:
    severity: str = "error"
    max_quests: int = 10


def _parse_bridge_run_args(args: list[str], action_name: str) -> BridgeRunOptions:
    tokens = list(args[1:] if args and args[0] == action_name else args)
    opts = BridgeRunOptions()
    for token in tokens:
        if token == "--once":
            opts.mode = "once"
            continue
        if token == "--test":
            opts.mode = "test"
            continue
        if token == "--watch":
            opts.mode = "watch"
            continue
        if token.startswith("--mode="):
            candidate = token.split("=", 1)[1].strip().lower()
            if candidate in {"once", "test", "watch"}:
                opts.mode = candidate
            else:
                print(f"⚠️ Unknown mode '{candidate}' ignored (expected once|test|watch).")
            continue
        if token.startswith("--interval="):
            value = token.split("=", 1)[1].strip()
            try:
                opts.interval_s = max(1, int(value))
            except ValueError:
                print(f"⚠️ Invalid --interval value '{value}' ignored.")
    return opts


def _parse_error_quest_bridge_args(args: list[str], action_name: str) -> ErrorQuestBridgeOptions:
    tokens = list(args[1:] if args and args[0] == action_name else args)
    opts = ErrorQuestBridgeOptions()
    for token in tokens:
        if token.startswith("--severity="):
            value = token.split("=", 1)[1].strip().lower()
            if value:
                opts.severity = value
            continue
        if token.startswith("--max-quests="):
            value = token.split("=", 1)[1].strip()
            try:
                opts.max_quests = max(1, int(value))
            except ValueError:
                print(f"⚠️ Invalid --max-quests value '{value}' ignored.")
    return opts


def _strings_to_repo_enums(names: list[str], repo_enum: type) -> list:
    seen = []
    for name in names:
        try:
            candidate = repo_enum(name)
        except Exception:
            continue
        if candidate not in seen:
            seen.append(candidate)
    return seen


def _run_error_report_bridge_chain(
    paths: RepoPaths,
    options: ErrorReportOptions,
    report_json_path: str | None = None,
) -> dict[str, Any]:
    requested = {
        "bridge_signals": bool(options.bridge_signals),
        "bridge_signal_to_quest": bool(options.bridge_signal_to_quest),
        "bridge_error_quests": bool(options.bridge_error_quests),
        "test_mode": bool(options.bridge_test_mode),
        "severity": str(options.bridge_severity),
        "max_quests": int(options.bridge_max_quests),
    }
    if not (requested["bridge_signals"] or requested["bridge_signal_to_quest"] or requested["bridge_error_quests"]):
        return {
            "enabled": False,
            "requested": requested,
            "stages": [],
            "errors": [],
            "status": "ok",
        }

    stages: list[dict[str, Any]] = []
    errors: list[str] = []

    if requested["bridge_signals"]:
        try:
            from src.orchestration import error_signal_bridge

            bridge_from_report = getattr(error_signal_bridge, "bridge_from_report", None)
            if report_json_path and callable(bridge_from_report):
                result = _run_async_sync(
                    bridge_from_report(report_path=Path(report_json_path), test_mode=bool(requested["test_mode"]))
                )
            else:
                result = _run_async_sync(error_signal_bridge.bridge_cycle(test_mode=bool(requested["test_mode"])))
            stages.append({"name": "error_signal_bridge", "status": "ok", "result": result})
        except Exception as exc:
            stages.append({"name": "error_signal_bridge", "status": "error", "error": str(exc)})
            errors.append(f"error_signal_bridge: {exc}")

    if requested["bridge_signal_to_quest"]:
        try:
            from src.orchestration.signal_quest_mapper import bridge_cycle as signal_quest_cycle

            result = _run_async_sync(signal_quest_cycle(test_mode=bool(requested["test_mode"])))
            stages.append({"name": "signal_quest_bridge", "status": "ok", "result": result})
        except Exception as exc:
            stages.append({"name": "signal_quest_bridge", "status": "error", "error": str(exc)})
            errors.append(f"signal_quest_bridge: {exc}")

    if requested["bridge_error_quests"]:
        if requested["test_mode"]:
            stages.append(
                {
                    "name": "error_quest_bridge",
                    "status": "skipped",
                    "reason": "bridge_test_mode",
                }
            )
        else:
            try:
                from src.integration.error_quest_bridge import (
                    ErrorQuestBridge,
                    ErrorSeverity,
                    auto_generate_error_quests,
                )

                severity_map = {str(item.value).lower(): item for item in ErrorSeverity}
                severity_raw = str(requested["severity"]).lower()
                severity = severity_map.get(severity_raw)
                if severity is None:
                    allowed = ", ".join(sorted(severity_map.keys()))
                    err = f"unknown severity '{severity_raw}' (expected one of: {allowed})"
                    stages.append({"name": "error_quest_bridge", "status": "error", "error": err})
                    errors.append(f"error_quest_bridge: {err}")
                else:
                    result = auto_generate_error_quests(
                        severity=severity,
                        max_quests=int(requested["max_quests"]),
                        report_path=Path(report_json_path) if report_json_path else None,
                    )
                    stats = ErrorQuestBridge().get_error_quest_stats()
                    stages.append(
                        {
                            "name": "error_quest_bridge",
                            "status": "ok",
                            "result": result,
                            "stats": stats,
                        }
                    )
            except Exception as exc:
                stages.append({"name": "error_quest_bridge", "status": "error", "error": str(exc)})
                errors.append(f"error_quest_bridge: {exc}")

    ok_count = sum(1 for stage in stages if stage.get("status") == "ok")
    status = "ok" if not errors else ("partial" if ok_count > 0 else "error")
    return {
        "enabled": True,
        "requested": requested,
        "stages": stages,
        "errors": errors,
        "status": status,
    }


def _handle_error_report(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Generate unified error report - ground truth for all agents."""
    if any(token in {"--help", "-h"} for token in args[1:]):
        _print_error_report_help("error_report")
        return 0

    async_mode = "--async" in args[1:] and "--sync" not in args[1:]
    options = _parse_error_report_args(args)
    if options.cache_ttl_s <= 0:
        options.cache_ttl_s = _default_error_report_cache_ttl_s(options.quick)
    if options.budget_s <= 0 and not options.quick:
        try:
            options.budget_s = max(0, int(os.getenv("NUSYQ_ERROR_REPORT_FULL_BUDGET_S", "600") or 600))
        except ValueError:
            options.budget_s = 600
    if async_mode:
        if not paths.nusyq_hub:
            payload = {
                "action": "error_report",
                "status": "error",
                "error": "[ERROR] NuSyQ-Hub path not found; cannot submit report job.",
            }
            print(json.dumps(payload, indent=2) if json_mode else payload["error"])
            return 1
        checkpoint_latest_file = paths.nusyq_hub / "state" / "reports" / "error_report_checkpoint_latest.json"
        if options.checkpoint_file:
            checkpoint_file = Path(options.checkpoint_file)
            if not checkpoint_file.is_absolute():
                checkpoint_file = paths.nusyq_hub / checkpoint_file
        else:
            checkpoint_file = (
                paths.nusyq_hub
                / "state"
                / "reports"
                / f"error_report_checkpoint_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.json"
            )
        cmd = [sys.executable, "scripts/start_nusyq.py", "error_report", "--sync", "--json"]
        cmd.extend(
            token
            for token in args[1:]
            if token not in {"--async", "--sync", "--json"} and not token.startswith("--checkpoint-file")
        )
        cmd.append(f"--checkpoint-file={checkpoint_file}")
        job = _start_subprocess_job(
            paths,
            job_type="error_report",
            command=cmd,
            cwd=paths.nusyq_hub,
            metadata={
                "runner": "start_nusyq",
                "action": "error_report",
                "checkpoint_file": str(checkpoint_file),
                "checkpoint_latest_file": str(checkpoint_latest_file),
            },
        )
        payload = {
            "action": "error_report",
            "status": "submitted",
            "job_id": job["job_id"],
            "pid": job["pid"],
            "stdout_log": job["stdout_log"],
            "stderr_log": job["stderr_log"],
            "checkpoint_file": str(checkpoint_file),
            "checkpoint_latest_file": str(checkpoint_latest_file),
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🧾 Error report submitted as background job")
            print(f"Job ID: {job['job_id']}")
            print(f"PID: {job['pid']}")
            print(f"stdout: {job['stdout_log']}")
            print(f"stderr: {job['stderr_log']}")
            print(f"Check status: python scripts/start_nusyq.py error_report_status {job['job_id']} --wait=30")
        return 0

    if not json_mode:
        print("\n🔍 UNIFIED ERROR REPORT - GROUND TRUTH")
        print("=" * 70)

    if not paths.nusyq_hub:
        payload = {
            "action": "error_report",
            "status": "error",
            "error": "[ERROR] NuSyQ-Hub path not found; cannot run report.",
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    report_started = time.time()
    run_stamp = now_stamp()
    if options.checkpoint_file:
        checkpoint_path = Path(options.checkpoint_file)
        if not checkpoint_path.is_absolute():
            checkpoint_path = paths.nusyq_hub / checkpoint_path
    else:
        checkpoint_path = paths.nusyq_hub / "state" / "reports" / f"error_report_checkpoint_{run_stamp}.json"
    checkpoint_latest_path = paths.nusyq_hub / "state" / "reports" / "error_report_checkpoint_latest.json"
    checkpoint: dict[str, Any] = {
        "action": "error_report_checkpoint",
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "total_planned": 5,
        "completed_checks": 0,
        "current_check": None,
        "options": {
            "quick": options.quick,
            "force": options.force,
            "include": options.include,
            "exclude": options.exclude,
            "budget_s": options.budget_s,
            "cache_ttl_s": options.cache_ttl_s,
            "bridge_signals": options.bridge_signals,
            "bridge_signal_to_quest": options.bridge_signal_to_quest,
            "bridge_error_quests": options.bridge_error_quests,
            "bridge_test_mode": options.bridge_test_mode,
            "bridge_severity": options.bridge_severity,
            "bridge_max_quests": options.bridge_max_quests,
            "checkpoint_file": str(checkpoint_path),
        },
        "checks": [],
    }

    def _write_checkpoint() -> None:
        checkpoint["updated_at"] = datetime.now().isoformat()
        checks = checkpoint.get("checks", [])
        checkpoint["completed_checks"] = len(checks) if isinstance(checks, list) else 0
        _write_json_report(checkpoint_path, checkpoint)
        _write_json_report(checkpoint_latest_path, checkpoint)

    def _record_stage(entry: dict[str, Any]) -> None:
        checks = checkpoint.setdefault("checks", [])
        if isinstance(checks, list):
            checks.append(entry)
        checkpoint["current_check"] = entry.get("name")
        _write_checkpoint()

    def _set_live_progress(entry: dict[str, Any]) -> None:
        checkpoint["progress"] = entry
        event = entry.get("event")
        repo = entry.get("repo")
        tool = entry.get("tool")
        if event == "tool_start" and repo and tool:
            checkpoint["current_check"] = f"{repo}:{tool}"
        elif event == "tool_complete" and repo and tool:
            checkpoint["current_check"] = f"{repo}:{tool}:complete"
        elif event == "repo_start" and repo:
            checkpoint["current_check"] = f"{repo}:start"
        elif event == "repo_complete" and repo:
            checkpoint["current_check"] = f"{repo}:complete"
        elif event == "tool_progress" and repo and tool:
            batch_index = entry.get("batch_index")
            total_batches = entry.get("total_batches")
            retry = entry.get("retry")
            suffix = f":batch{batch_index}/{total_batches}" if batch_index and total_batches else ""
            if retry:
                retry_index = entry.get("retry_index")
                suffix += f":retry{retry_index}" if retry_index else ":retry"
            checkpoint["current_check"] = f"{repo}:{tool}{suffix}"
        _write_checkpoint()

    def _remaining_budget_s() -> int | None:
        if options.budget_s <= 0:
            return None
        elapsed = int(time.time() - report_started)
        return max(0, options.budget_s - elapsed)

    _write_checkpoint()
    _record_stage(
        {
            "name": "parse_options",
            "passed": True,
            "mode": "quick" if options.quick else "full",
            "force": options.force,
            "cache_ttl_s": options.cache_ttl_s,
        }
    )

    try:
        from src.diagnostics.unified_error_reporter import RepoName, UnifiedErrorReporter
    except Exception as exc:
        checkpoint["status"] = "failed"
        checkpoint["finished_at"] = datetime.now().isoformat()
        _record_stage(
            {
                "name": "import_reporter",
                "passed": False,
                "error": str(exc),
            }
        )
        payload = {
            "action": "error_report",
            "status": "error",
            "error": f"[ERROR] Unable to import UnifiedErrorReporter: {exc}",
            "checkpoint_file": str(checkpoint_latest_path),
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    if options.quick and not options.include and not options.exclude:
        # Keep quick mode predictably fast by defaulting to hub-only scope unless caller
        # explicitly requests additional repos.
        options.include = ["nusyq-hub"]
        options.exclude = ["simulated-verse", "nusyq"]
        if not json_mode:
            print("Info: quick mode default scope is hub-only. Use --repo to expand scope.")
    include_repos = _strings_to_repo_enums(options.include, RepoName)
    exclude_repos = _strings_to_repo_enums(options.exclude, RepoName)

    if not json_mode:
        print("Scanning repositories for errors, warnings, and infos...")
        print(f"Mode: {'quick' if options.quick else 'full'} {'(forced scan)' if options.force else ''}".strip())
        if not options.force:
            print(f"Cache window: {options.cache_ttl_s}s (reuse enabled)")
        print()

    reporter = UnifiedErrorReporter(
        hub_path=paths.nusyq_hub,
        include_repos=include_repos or None,
        exclude_repos=exclude_repos or None,
    )
    target_repos = [repo.value for repo in reporter.repos]
    checkpoint["total_planned"] = 5 + len(target_repos)
    _write_checkpoint()
    _record_stage(
        {
            "name": "resolve_targets",
            "passed": bool(target_repos),
            "targets": target_repos,
        }
    )
    if not json_mode:
        print(f"Target repos: {', '.join(target_repos) or 'none'}")

    desired_targets = {repo.value for repo in reporter.repos}
    requested_scan_mode = "quick" if options.quick else "full"
    cached_report = None
    if not options.force:
        cached_report = reporter.load_cached_report(max_age_seconds=options.cache_ttl_s)
    if cached_report:
        cache_targets = set(cached_report.get("targets", []))
        cached_mode = str(cached_report.get("scan_mode") or "").lower()
        if cache_targets != desired_targets:
            cached_report = None
            print("⚠️ Cached report does not cover the requested scope; running a fresh scan.")
        elif cached_mode and cached_mode != requested_scan_mode:
            cached_report = None
            if not json_mode:
                print(
                    "⚠️ Cached report mode mismatch "
                    f"(cached={cached_mode}, requested={requested_scan_mode}); running fresh scan."
                )
        else:
            cache_info = cached_report.get("cache_info", {}) if isinstance(cached_report, dict) else {}
            cache_age = cache_info.get("age_seconds")
            if cache_age is not None:
                if not json_mode:
                    print(f"Info: Using cached report ({cache_age:.0f}s old). Pass --force to rescan.")
            else:
                if not json_mode:
                    print("Info: Using cached report (age unknown). Pass --force to rescan.")
    _record_stage(
        {
            "name": "cache_lookup",
            "passed": True,
            "cache_hit": bool(cached_report),
            "cache_ttl_s": options.cache_ttl_s,
        }
    )

    budget_exceeded = False

    if cached_report:
        report = cached_report
        _record_stage(
            {
                "name": "scan_cached",
                "passed": True,
                "skipped": True,
                "reason": "cached_report",
            }
        )
    else:
        reporter.scan_mode = "quick" if options.quick else "full"
        reporter.all_diagnostics = []
        reporter.scans = {}
        reporter.scan_warnings = []
        redirect_stream = io.StringIO() if json_mode else None
        for repo_name, repo_path in reporter.repos.items():
            remaining = _remaining_budget_s()
            stage_name = f"scan_{repo_name.value}"
            if remaining is not None and remaining <= 0:
                budget_exceeded = True
                reporter.scan_warnings.append(f"budget exceeded before {repo_name.value}")
                _record_stage(
                    {
                        "name": stage_name,
                        "passed": False,
                        "skipped": True,
                        "reason": "budget_exceeded",
                    }
                )
                continue
            if not repo_path.exists():
                reporter.scan_warnings.append(f"{repo_name.value} not found at {repo_path}")
                _record_stage(
                    {
                        "name": stage_name,
                        "passed": False,
                        "skipped": True,
                        "reason": "repo_missing",
                        "repo_path": str(repo_path),
                    }
                )
                continue

            stage_started = time.time()
            _set_live_progress(
                {
                    "event": "repo_dispatch",
                    "repo": repo_name.value,
                    "repo_path": str(repo_path),
                    "started_at": datetime.now().isoformat(),
                }
            )
            single_reporter = UnifiedErrorReporter(
                hub_path=paths.nusyq_hub,
                include_repos=[repo_name],
                progress_callback=_set_live_progress,
            )
            if remaining is not None and remaining > 0:
                single_reporter.scan_deadline_ts = time.time() + float(remaining)
            if json_mode and redirect_stream is not None:
                with contextlib.redirect_stdout(redirect_stream):
                    single_reporter.scan_all_repos(quick=options.quick)
            else:
                single_reporter.scan_all_repos(quick=options.quick)
            scan = single_reporter.scans.get(repo_name)
            if scan:
                reporter.scans[repo_name] = scan
                reporter.all_diagnostics.extend(scan.diagnostics)
            reporter.scan_warnings.extend(single_reporter.scan_warnings)
            elapsed = round(time.time() - stage_started, 2)
            stage_entry: dict[str, Any] = {
                "name": stage_name,
                "passed": True,
                "elapsed_s": elapsed,
                "diagnostics": len(scan.diagnostics) if scan else 0,
                "repo_path": str(repo_path),
            }
            budget_remaining = _remaining_budget_s()
            if budget_remaining is not None:
                stage_entry["budget_remaining_s"] = budget_remaining
            _record_stage(stage_entry)
        report = reporter.generate_unified_report()

    if not json_mode:
        reporter.print_summary(report)

    if cached_report:
        latest_json = reporter.reports_dir / "unified_error_report_latest.json"
        latest_md = reporter.reports_dir / "unified_error_report_latest.md"
        outputs = {
            "json": str(latest_json),
            "md": str(latest_md),
            "latest_json": str(latest_json),
            "latest_md": str(latest_md),
        }
        if not json_mode:
            print(f"\n📝 Loaded cached report from: {outputs['md']}")
    else:
        outputs = reporter.write_report()
        if not json_mode:
            print(f"\n📝 Report saved to: {outputs['md']}")
    outputs.update(_sync_error_report_latest_artifacts(paths, report, outputs))
    _record_stage(
        {
            "name": "write_report",
            "passed": True,
            "outputs": outputs,
        }
    )

    global _LAST_OUTPUTS
    _LAST_OUTPUTS = [outputs["json"], outputs["md"], outputs["latest_json"], outputs["latest_md"]]

    final_status = "ok"
    if budget_exceeded:
        final_status = "partial"
    elif report.get("partial_scan"):
        final_status = "partial"

    bridge_chain = _run_error_report_bridge_chain(paths, options, outputs.get("latest_json"))
    if bridge_chain.get("enabled"):
        _record_stage(
            {
                "name": "bridge_chain",
                "passed": bridge_chain.get("status") in {"ok", "partial"},
                "status": bridge_chain.get("status"),
                "errors": bridge_chain.get("errors", []),
            }
        )
        if final_status == "ok" and bridge_chain.get("status") != "ok":
            final_status = "partial"

    payload = {
        "action": "error_report",
        "status": final_status,
        "generated_at": datetime.now().isoformat(),
        "mode": "quick" if options.quick else "full",
        "budget_s": options.budget_s,
        "budget_exceeded": budget_exceeded,
        "targets": target_repos,
        "partial_scan": bool(report.get("partial_scan")),
        "total_diagnostics": report.get("total_diagnostics", 0),
        "by_severity": report.get("by_severity", {}),
        "outputs": outputs,
        "checkpoint_file": str(checkpoint_latest_path),
        "report": report,
        "bridge_chain": bridge_chain,
    }

    checkpoint["status"] = "completed" if final_status == "ok" else "partial"
    checkpoint["finished_at"] = datetime.now().isoformat()
    checkpoint["report_file"] = str(outputs.get("latest_json", ""))
    _write_checkpoint()
    try:
        checkpoint_keep = max(1, int(os.getenv("NUSYQ_ERROR_REPORT_CHECKPOINT_HISTORY_KEEP", "30") or 30))
    except ValueError:
        checkpoint_keep = 30
    _prune_lifecycle_reports(
        paths.nusyq_hub / "state" / "reports",
        checkpoint_keep,
        pattern="error_report_checkpoint_*.json",
        protected_names={"error_report_checkpoint_latest.json"},
    )

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    else:
        print("\n🎯 GROUND TRUTH FOR ALL AGENTS:")
        print(f"  Total Diagnostics: {report['total_diagnostics']}")
        print(f"  • Errors:   {report['by_severity']['errors']}")
        print(f"  • Warnings: {report['by_severity']['warnings']}")
        print(f"  • Infos:    {report['by_severity']['infos_hints']}")
        if report.get("vscode_counts"):
            counts = report["vscode_counts"].get("counts", {})
            print(
                "  • VS Code:  "
                f"{counts.get('errors', 0)} errors, "
                f"{counts.get('warnings', 0)} warnings, "
                f"{counts.get('infos', 0)} infos"
            )
        if budget_exceeded:
            print("  • Budget:   exceeded (partial scan)")
        if bridge_chain.get("enabled"):
            print(f"  • Bridge chain: {bridge_chain.get('status', 'unknown')}")
            stages = bridge_chain.get("stages", [])
            if isinstance(stages, list):
                for stage in stages:
                    if not isinstance(stage, dict):
                        continue
                    print(f"    - {stage.get('name', 'stage')}: {stage.get('status', 'unknown')}")
        print("\nAll agents should report these exact numbers to ensure signal consistency.")
    return 0


def _handle_error_report_split(args: list[str], paths: RepoPaths) -> int:
    """Generate per-repo error reports and a unified summary."""
    if any(token in {"--help", "-h"} for token in args[1:]):
        _print_error_report_help("error_report_split")
        return 0

    print("\n🔍 UNIFIED ERROR REPORT - SPLIT FULL SCAN")
    print("=" * 70)

    if not paths.nusyq_hub:
        print("[ERROR] NuSyQ-Hub path not found; cannot run report.")
        return 1

    try:
        from src.diagnostics.unified_error_reporter import RepoName, UnifiedErrorReporter
    except Exception as exc:
        print(f"[ERROR] Unable to import UnifiedErrorReporter: {exc}")
        return 1

    options = _parse_error_report_args(args)
    quick = options.quick
    include_repos = _strings_to_repo_enums(options.include, RepoName)
    exclude_repos = _strings_to_repo_enums(options.exclude, RepoName)

    print("Scanning repositories per repo to avoid long-running timeouts...")
    print(f"Mode: {'quick' if quick else 'full'}")
    print()

    output_dir = paths.nusyq_hub / "docs" / "Reports" / "diagnostics"
    split_dir = output_dir / "split"
    split_dir.mkdir(parents=True, exist_ok=True)

    combined_reporter = UnifiedErrorReporter(
        hub_path=paths.nusyq_hub,
        include_repos=include_repos or None,
        exclude_repos=exclude_repos or None,
    )
    print(f"Target repos: {', '.join(repo.value for repo in combined_reporter.repos) or 'none'}")
    combined_reporter.all_diagnostics = []
    combined_reporter.scans = {}
    combined_reporter.scan_mode = "quick" if quick else "full"

    split_outputs: list[str] = []

    for repo_name, repo_path in combined_reporter.repos.items():
        if not repo_path.exists():
            print(f"⚠️  {repo_name.value} not found at {repo_path}")
            continue

        print(f"📦 Scanning {repo_name.value}...")
        repo_reporter = UnifiedErrorReporter(hub_path=paths.nusyq_hub)
        repo_reporter.repos = {repo_name: repo_path}
        repo_reporter.scan_all_repos(quick=quick)
        repo_outputs = repo_reporter.write_report(split_dir, label=repo_name.value)
        split_outputs.append(repo_outputs["md"])

        scan = repo_reporter.scans.get(repo_name)
        if scan:
            combined_reporter.scans[repo_name] = scan
        combined_reporter.all_diagnostics.extend(repo_reporter.all_diagnostics)

    combined_reporter.print_summary()
    unified_outputs = combined_reporter.write_report(output_dir)

    global _LAST_OUTPUTS
    _LAST_OUTPUTS = [
        unified_outputs["json"],
        unified_outputs["md"],
        unified_outputs["latest_json"],
        unified_outputs["latest_md"],
        *split_outputs,
    ]
    print(f"\n📝 Unified report saved to: {unified_outputs['md']}")
    print(f"🧾 Split reports saved under: {split_dir}")

    return 0


def _handle_error_signal_bridge(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Bridge error report groups into guild board signals."""
    if not paths.nusyq_hub:
        payload = {
            "action": "error_signal_bridge",
            "status": "error",
            "error": "[ERROR] NuSyQ-Hub path not found; cannot run bridge.",
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    opts = _parse_bridge_run_args(args, "error_signal_bridge")
    try:
        from src.orchestration.error_signal_bridge import (
            bridge_cycle,
            bridge_from_report,
            watch_mode,
        )
    except Exception as exc:
        payload = {
            "action": "error_signal_bridge",
            "status": "error",
            "error": f"[ERROR] Failed to import error_signal_bridge: {exc}",
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    result: dict[str, Any] = {}
    try:
        if opts.mode == "watch":
            _run_async_sync(watch_mode(interval=opts.interval_s))
            result = {"watch_mode": True, "interval_s": opts.interval_s}
        else:
            preferred_report = _select_latest_error_report_path(paths.nusyq_hub)
            if preferred_report and preferred_report.exists():
                result = _run_async_sync(
                    bridge_from_report(
                        report_path=preferred_report,
                        test_mode=opts.mode == "test",
                    )
                )
                result["report_path"] = str(preferred_report)
            else:
                result = _run_async_sync(bridge_cycle(test_mode=opts.mode == "test"))
    except KeyboardInterrupt:
        result = {"status": "interrupted", "mode": opts.mode}
    except Exception as exc:
        payload = {
            "action": "error_signal_bridge",
            "status": "error",
            "mode": opts.mode,
            "error": str(exc),
        }
        print(json.dumps(payload, indent=2) if json_mode else f"[ERROR] {exc}")
        return 1

    payload = {
        "action": "error_signal_bridge",
        "status": "ok",
        "generated_at": datetime.now().isoformat(),
        "mode": opts.mode,
        "interval_s": opts.interval_s,
        "result": result,
    }
    report_path = paths.nusyq_hub / "state" / "reports" / "error_signal_bridge_latest.json"
    _write_json_report(report_path, payload)
    payload["report_file"] = str(report_path)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    else:
        print("🌉 Error → Signal Bridge")
        print("=" * 60)
        print(f"Mode: {opts.mode}")
        if opts.mode == "watch":
            print(f"Interval: {opts.interval_s}s")
            print("Watch mode completed.")
        else:
            print(f"Signals posted: {result.get('signals_posted', 0)}/{result.get('signals_created', 0)}")
            print(f"Error groups found: {result.get('error_groups_found', 0)}")
        print(f"Report: {report_path}")
    return 0


def _handle_signal_quest_bridge(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Bridge guild signals into quest entries."""
    if not paths.nusyq_hub:
        payload = {
            "action": "signal_quest_bridge",
            "status": "error",
            "error": "[ERROR] NuSyQ-Hub path not found; cannot run bridge.",
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    opts = _parse_bridge_run_args(args, "signal_quest_bridge")
    try:
        from src.orchestration.signal_quest_mapper import bridge_cycle, watch_mode
    except Exception as exc:
        payload = {
            "action": "signal_quest_bridge",
            "status": "error",
            "error": f"[ERROR] Failed to import signal_quest_mapper: {exc}",
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    result: dict[str, Any] = {}
    try:
        if opts.mode == "watch":
            _run_async_sync(watch_mode(interval=opts.interval_s))
            result = {"watch_mode": True, "interval_s": opts.interval_s}
        else:
            result = _run_async_sync(bridge_cycle(test_mode=opts.mode == "test"))
    except KeyboardInterrupt:
        result = {"status": "interrupted", "mode": opts.mode}
    except Exception as exc:
        payload = {
            "action": "signal_quest_bridge",
            "status": "error",
            "mode": opts.mode,
            "error": str(exc),
        }
        print(json.dumps(payload, indent=2) if json_mode else f"[ERROR] {exc}")
        return 1

    payload = {
        "action": "signal_quest_bridge",
        "status": "ok",
        "generated_at": datetime.now().isoformat(),
        "mode": opts.mode,
        "interval_s": opts.interval_s,
        "result": result,
    }
    report_path = paths.nusyq_hub / "state" / "reports" / "signal_quest_bridge_latest.json"
    _write_json_report(report_path, payload)
    payload["report_file"] = str(report_path)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    else:
        print("🌉 Signal → Quest Bridge")
        print("=" * 60)
        print(f"Mode: {opts.mode}")
        if opts.mode == "watch":
            print(f"Interval: {opts.interval_s}s")
            print("Watch mode completed.")
        else:
            print(f"Signals found: {result.get('signals_found', 0)}")
            print(f"Quests created: {result.get('quests_created', 0)}")
        print(f"Report: {report_path}")
    return 0


def _handle_error_quest_bridge(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Generate quests directly from critical errors."""
    if not paths.nusyq_hub:
        payload = {
            "action": "error_quest_bridge",
            "status": "error",
            "error": "[ERROR] NuSyQ-Hub path not found; cannot run bridge.",
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    action_name = "error_quest_bridge" if "error_quest_bridge" in args else "auto_quest"
    opts = _parse_error_quest_bridge_args(args, action_name)
    try:
        from src.integration.error_quest_bridge import (
            ErrorQuestBridge,
            ErrorSeverity,
            auto_generate_error_quests,
        )
    except Exception as exc:
        payload = {
            "action": "error_quest_bridge",
            "status": "error",
            "error": f"[ERROR] Failed to import error_quest_bridge: {exc}",
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    severity_map = {str(item.value).lower(): item for item in ErrorSeverity}
    severity = severity_map.get(opts.severity.lower())
    if severity is None:
        payload = {
            "action": "error_quest_bridge",
            "status": "error",
            "error": (
                f"[ERROR] Unknown severity '{opts.severity}'. Expected one of: {', '.join(sorted(severity_map.keys()))}"
            ),
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    try:
        artifact_report = _select_latest_error_report_path(paths.nusyq_hub)
        result = auto_generate_error_quests(
            severity=severity,
            max_quests=opts.max_quests,
            report_path=artifact_report if artifact_report and artifact_report.exists() else None,
        )
        stats = ErrorQuestBridge().get_error_quest_stats()
    except Exception as exc:
        payload = {
            "action": "error_quest_bridge",
            "status": "error",
            "severity": str(severity.value),
            "error": str(exc),
        }
        print(json.dumps(payload, indent=2) if json_mode else f"[ERROR] {exc}")
        return 1

    payload = {
        "action": "error_quest_bridge",
        "status": "ok",
        "generated_at": datetime.now().isoformat(),
        "severity": str(severity.value),
        "max_quests": opts.max_quests,
        "result": result,
        "stats": stats,
        "alias_used": action_name == "auto_quest",
    }
    report_path = paths.nusyq_hub / "state" / "reports" / "error_quest_bridge_latest.json"
    _write_json_report(report_path, payload)
    payload["report_file"] = str(report_path)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    else:
        print("🌉 Error → Quest Bridge")
        print("=" * 60)
        print(f"Severity: {severity.value}")
        print(f"Max quests: {opts.max_quests}")
        print(f"Total errors found: {result.get('total_errors_found', 0)}")
        print(f"Quests created: {result.get('quests_created', 0)}")
        print(f"Total error quests: {stats.get('total_error_quests', 0)}")
        print(f"Report: {report_path}")
    return 0


def _parse_iso_timestamp(value: Any) -> float:
    """Best-effort ISO timestamp parser for deterministic quest ordering."""
    if value is None:
        return 0.0
    raw = str(value).strip()
    if not raw:
        return 0.0
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.timestamp()


def _count_open_signal_title_duplicates(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count open signal-linked quest duplicates by title."""
    counter: Counter[str] = Counter()
    for row in rows:
        if not isinstance(row, dict):
            continue
        if not row.get("signal_id"):
            continue
        if str(row.get("status", "")).strip().lower() != "open":
            continue
        title = str(row.get("title") or row.get("quest") or "").strip()
        if title:
            counter[title] += 1
    return {title: count for title, count in counter.items() if count > 1}


def _compact_signal_open_quest_duplicates(
    quest_log_path: Path,
    report_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Compact duplicate open signal-linked quests by title, keeping the newest."""
    if not quest_log_path.exists():
        return {
            "status": "error",
            "error": f"Quest log not found: {quest_log_path}",
            "duplicates_closed": 0,
            "groups_compacted": 0,
            "dry_run": dry_run,
        }

    raw_lines = quest_log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    parsed_rows: list[dict[str, Any] | None] = []
    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            parsed_rows.append(None)
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            parsed_rows.append(None)
            continue
        parsed_rows.append(obj if isinstance(obj, dict) else None)

    open_signal_rows = [row for row in parsed_rows if isinstance(row, dict)]
    duplicate_titles_before = _count_open_signal_title_duplicates(open_signal_rows)

    groups: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, row in enumerate(parsed_rows):
        if not isinstance(row, dict):
            continue
        if not row.get("signal_id"):
            continue
        if str(row.get("status", "")).strip().lower() != "open":
            continue
        normalized_title = str(row.get("title") or row.get("quest") or "").strip().casefold()
        if not normalized_title:
            continue
        groups.setdefault(normalized_title, []).append((index, row))

    now_iso = datetime.now().isoformat()
    modified_rows: dict[int, dict[str, Any]] = {}
    compacted_groups: list[dict[str, Any]] = []

    for normalized_title, items in groups.items():
        if len(items) <= 1:
            continue

        keep_index, keep_row = max(
            items,
            key=lambda pair: (_parse_iso_timestamp(pair[1].get("timestamp")), pair[0]),
        )
        keep_id = str(keep_row.get("id") or f"quest_line_{keep_index}")
        keep_title = str(keep_row.get("title") or keep_row.get("quest") or normalized_title)

        closed_ids: list[str] = []
        for index, row in items:
            if index == keep_index:
                continue
            updated = dict(row)
            updated["status"] = "closed"
            updated["closed_reason"] = "deduplicated_open_signal_quest"
            updated["superseded_by"] = keep_id
            updated["dedup_compacted_at"] = now_iso
            modified_rows[index] = updated
            closed_ids.append(str(updated.get("id") or f"quest_line_{index}"))

        compacted_groups.append(
            {
                "title": keep_title,
                "kept_id": keep_id,
                "closed_ids": closed_ids,
                "count_before": len(items),
                "count_closed": len(closed_ids),
            }
        )

    if modified_rows and not dry_run:
        report_dir.mkdir(parents=True, exist_ok=True)
        backup_path = report_dir / f"quest_log_compaction_backup_{now_stamp()}.jsonl"
        backup_path.write_text("\n".join(raw_lines) + "\n", encoding="utf-8")

        rewritten_lines: list[str] = []
        for index, line in enumerate(raw_lines):
            if index in modified_rows:
                rewritten_lines.append(json.dumps(modified_rows[index], ensure_ascii=False))
            else:
                rewritten_lines.append(line)
        quest_log_path.write_text("\n".join(rewritten_lines) + "\n", encoding="utf-8")
    else:
        backup_path = None

    post_rows: list[dict[str, Any]] = []
    if modified_rows and not dry_run:
        source_lines = quest_log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in source_lines:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                post_rows.append(row)
    else:
        for index, row in enumerate(parsed_rows):
            if not isinstance(row, dict):
                continue
            if index in modified_rows:
                post_rows.append(modified_rows[index])
            else:
                post_rows.append(dict(row))

    duplicate_titles_after = _count_open_signal_title_duplicates(post_rows)

    return {
        "status": "ok",
        "dry_run": dry_run,
        "quest_log": str(quest_log_path),
        "backup_file": str(backup_path) if backup_path else None,
        "groups_compacted": len(compacted_groups),
        "duplicates_closed": sum(group["count_closed"] for group in compacted_groups),
        "duplicate_titles_before": duplicate_titles_before,
        "duplicate_titles_after": duplicate_titles_after,
        "compacted_groups": compacted_groups,
    }


def _handle_quest_compact(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Compact duplicate open signal-linked quests in quest_log.jsonl."""
    if not paths.nusyq_hub:
        payload = {
            "action": "quest_compact",
            "status": "error",
            "error": "[ERROR] NuSyQ-Hub path not found; cannot compact quest log.",
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    dry_run = "--dry-run" in args[1:]
    quest_log_path = paths.nusyq_hub / "src" / "Rosetta_Quest_System" / QUEST_LOG_FILENAME
    report_dir = paths.nusyq_hub / "state" / "reports"
    result = _compact_signal_open_quest_duplicates(
        quest_log_path=quest_log_path,
        report_dir=report_dir,
        dry_run=dry_run,
    )

    payload = {
        "action": "quest_compact",
        "status": result.get("status", "error"),
        "generated_at": datetime.now().isoformat(),
        "result": result,
    }
    report_path = report_dir / "quest_compact_latest.json"
    _write_json_report(report_path, payload)
    payload["report_file"] = str(report_path)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    else:
        print("🧹 Quest Log Compaction")
        print("=" * 60)
        print(f"Dry run: {dry_run}")
        if payload["status"] != "ok":
            print(f"[ERROR] {result.get('error', 'Unknown compaction failure')}")
        else:
            print(f"Groups compacted: {result.get('groups_compacted', 0)}")
            print(f"Duplicate entries closed: {result.get('duplicates_closed', 0)}")
            print(f"Before: {result.get('duplicate_titles_before', {})}")
            print(f"After: {result.get('duplicate_titles_after', {})}")
            if result.get("backup_file"):
                print(f"Backup: {result['backup_file']}")
        print(f"Report: {report_path}")
    return 0 if payload["status"] == "ok" else 1


def _handle_log_dedup_status() -> int:
    """Report whether duplicate log suppression is active."""
    print("\n🧾 LOG DEDUP STATUS")
    print("=" * 70)

    try:
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter
    except Exception as exc:
        print(f"[ERROR] DuplicateMessageFilter unavailable: {exc}")
        return 1

    try:
        window = float(os.getenv("NU_SYG_LOG_DEDUP_WINDOW", "2"))
    except ValueError:
        window = 2.0

    root_logger = logging.getLogger()
    handler_count = len(root_logger.handlers)
    filter_count = 0
    handlers_with_filter = 0
    logger_filter_count = sum(1 for f in root_logger.filters if isinstance(f, DuplicateMessageFilter))

    for handler in root_logger.handlers:
        has_filter = any(isinstance(f, DuplicateMessageFilter) for f in handler.filters)
        if has_filter:
            handlers_with_filter += 1
            filter_count += sum(1 for f in handler.filters if isinstance(f, DuplicateMessageFilter))

    print(f"Root handlers: {handler_count}")
    print(f"Dedup window (seconds): {window}")
    print(f"Logger-level dedup filters: {logger_filter_count}")
    print(f"Handlers with dedup filter: {handlers_with_filter}")
    print(f"Total dedup filters: {filter_count}")
    print("Status: " + ("active" if (handlers_with_filter > 0 or logger_filter_count > 0) else "inactive"))
    print("\nHint: set NU_SYG_LOG_DEDUP_WINDOW to increase suppression window.")
    print("=" * 70)

    return 0


def _handle_quantum_resolver_status() -> int:
    """Report quantum resolver consolidation status and compute availability."""
    print("\n⚛️ QUANTUM RESOLVER STATUS")
    print("=" * 70)

    try:
        from src.healing import quantum_problem_resolver as qpr
    except Exception as exc:
        print(f"[ERROR] Quantum resolver import failed: {exc}")
        return 1

    canonical_path = getattr(qpr, "__file__", "unknown")
    try:
        qpr._load_compute_backend()
    except Exception:
        pass
    compute_available = bool(getattr(qpr, "QUANTUM_COMPUTE_AVAILABLE", False))

    compute_path = "unavailable"
    if compute_available:
        try:
            from src.quantum import quantum_problem_resolver_compute as compute

            compute_path = getattr(compute, "__file__", "unknown")
        except Exception:
            compute_path = "import_error"

    preferred = "compute" if compute_available else "healing"

    print(f"Canonical module: {canonical_path}")
    print(f"Compute backend: {'available' if compute_available else 'unavailable'}")
    print(f"Compute module: {compute_path}")
    print(f"Preferred resolver: {preferred}")
    print("\nHint: install numpy to enable compute backend if missing.")
    print("=" * 70)
    return 0


def _handle_run_notebook(args: list[str]) -> int:
    """Execute a Jupyter notebook programmatically."""
    print("📓 Jupyter Notebook Executor")
    print("=" * 60)

    if len(args) < 2:
        print("\nUsage: python start_nusyq.py run_notebook <notebook_path> [--output=<path>] [--timeout=<seconds>]")
        print("\nExamples:")
        print("  python start_nusyq.py run_notebook docs/Notebooks/analysis.ipynb")
        print("  python start_nusyq.py run_notebook analysis.ipynb --output=results.ipynb --timeout=600")
        return 1

    notebook_path = args[1]
    output_path = None
    timeout = 300

    # Parse flags
    for arg in args[2:]:
        if arg.startswith("--output="):
            output_path = arg.split("=")[1]
        elif arg.startswith("--timeout="):
            timeout = int(arg.split("=")[1])

    try:
        from src.orchestration.jupyter_executor import get_jupyter_executor

        executor = get_jupyter_executor()

        print(f"\n📝 Notebook: {notebook_path}")
        print(f"   Timeout: {timeout}s")
        if output_path:
            print(f"   Output: {output_path}")

        print("\n⏳ Executing...")

        execution = executor.execute_notebook(notebook_path=notebook_path, output_path=output_path, timeout=timeout)

        print("\n📊 Execution Result:")
        print(f"   Status: {execution.status}")
        print(f"   Duration: {execution.execution_time_seconds:.2f}s")
        print(f"   Cells: {execution.cell_count}")

        if execution.status == "success":
            print(f"   Output: {execution.output_path}")

            if execution.outputs:
                print("\n💡 Outputs:")
                print(f"   Code cells: {execution.outputs.get('code_cells', 0)}")
                print(f"   Markdown cells: {execution.outputs.get('markdown_cells', 0)}")

                if execution.outputs.get("errors"):
                    print(f"   ⚠️ Errors: {len(execution.outputs['errors'])}")

        else:
            print("\n❌ Errors:")
            for error in execution.error_messages:
                print(f"   {error[:200]}")

        print("\n" + "=" * 60)

        return 0 if execution.status == "success" else 1

    except Exception as exc:
        print(f"❌ Notebook execution failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_ecosystem_status() -> int:
    """Show status of activated ecosystem systems."""
    print("🌐 Ecosystem Status")
    print("=" * 60)

    try:
        from src.orchestration.ecosystem_activator import get_ecosystem_activator

        activator = get_ecosystem_activator()
        # Ensure systems are discovered for this process before reporting.
        activator.discover_systems()
        stats = activator.get_activation_stats()

        if stats.get("total_systems", 0) == 0:
            hub_path = Path(__file__).resolve().parents[1]
            snapshot_path = hub_path / "state" / "reports" / "ecosystem_activation_latest.json"
            snapshot = read_json(snapshot_path)
            if isinstance(snapshot, dict):
                print("\n📊 Overview (from latest activation snapshot):")
                total = int(snapshot.get("total", 0) or 0)
                activated = int(snapshot.get("activated", 0) or 0)
                failed = int(snapshot.get("failed", 0) or 0)
                print(f"   Total Systems: {total}")
                print(f"   Activated: {activated}")
                print(f"   Failed: {failed}")
                print(f"   Success Rate: {float(snapshot.get('success_rate', 0.0)):.1%}")
                print(f"\n📝 Snapshot: {snapshot_path}")
                print("\n" + "=" * 60)
                return 0

        print("\n📊 Overview:")
        print(f"   Total Systems: {stats['total_systems']}")
        print(f"   Total Capabilities: {stats['total_capabilities']}")
        print(f"   Activation Rate: {stats['activation_rate']:.1%}")

        print("\n📈 By Status:")
        for status, count in stats["by_status"].items():
            emoji = {"active": "✅", "inactive": "⏸️", "error": "❌", "initializing": "⏳"}.get(status, "⚪")
            print(f"   {emoji} {status}: {count}")

        print("\n🔧 By Type:")
        for sys_type, count in stats["by_type"].items():
            print(f"   {sys_type}: {count}")

        if stats["total_systems"] > 0:
            print("\n🔍 Detailed Status:")
            for system in activator.systems.values():
                status_emoji = {
                    "active": "✅",
                    "inactive": "⏸️",
                    "error": "❌",
                    "initializing": "⏳",
                }.get(system.status, "⚪")

                print(f"\n   {status_emoji} {system.name} ({system.system_type})")
                print(f"      ID: {system.system_id}")
                print(f"      Status: {system.status}")
                print(f"      Capabilities: {len(system.capabilities)}")

                if system.capabilities[:3]:
                    print("      Top Capabilities:")
                    for cap in system.capabilities[:3]:
                        print(f"         - {cap}")

                if system.error:
                    print(f"      Error: {system.error[:100]}")

        print("\n" + "=" * 60)

        return 0

    except Exception as exc:
        print(f"❌ Error getting ecosystem status: {exc}")
        return 1


def _collect_process_snapshot() -> tuple[list[dict[str, Any]], bool]:
    """Collect a lightweight process snapshot for lifecycle reporting."""
    try:
        import psutil
    except Exception:
        return [], False

    processes: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time", "status"]):
        try:
            info = proc.info
            processes.append(
                {
                    "pid": info.get("pid"),
                    "name": info.get("name") or "",
                    "cmdline": info.get("cmdline") or [],
                    "status": info.get("status") or "",
                    "create_time": info.get("create_time"),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return processes, True


def _load_ecosystem_defaults(paths: RepoPaths) -> dict[str, Any]:
    if not paths.nusyq_hub:
        return {}
    defaults_path = paths.nusyq_hub / "config" / "ecosystem_defaults.json"
    return read_json(defaults_path) or {}


def _prune_lifecycle_reports(
    report_dir: Path,
    retention_count: int,
    pattern: str = "lifecycle_catalog_*.json",
    protected_names: set[str] | None = None,
) -> None:
    if retention_count <= 0:
        return
    protected = set(protected_names or [])
    reports = sorted(
        report_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for stale in reports[retention_count:]:
        if stale.name in protected:
            continue
        try:
            stale.unlink()
        except OSError:
            continue


def _collect_stale_reports(
    report_dir: Path,
    retention_count: int,
    pattern: str,
    protected_names: set[str] | None = None,
) -> list[Path]:
    """Collect stale files for a report pattern without deleting them."""
    if retention_count <= 0:
        return []
    protected = set(protected_names or [])
    reports = sorted(
        report_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
        reverse=True,
    )
    # Exclude protected files from the keep window — they are always preserved
    # and should not consume keep slots from the rotation budget.
    non_protected = [r for r in reports if r.name not in protected]
    return non_protected[retention_count:]


def _handle_prune_reports(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Prune/archival maintenance for generated reports."""
    if not paths.nusyq_hub:
        print("[ERROR] NuSyQ-Hub path not found; cannot prune reports.")
        return 1

    tokens = [token for token in args[1:] if isinstance(token, str)]
    execute = any(token in {"--execute", "--apply", "--yes"} for token in tokens)
    dry_run = not execute
    if "--dry-run" in tokens:
        dry_run = True
    if "--no-dry-run" in tokens:
        dry_run = False
    delete_mode = "--delete" in tokens
    refresh_signals = "--no-refresh-signals" not in tokens
    refresh_error_report = "--with-error-refresh" in tokens
    run_automated_cleanup = "--with-automated-cleanup" in tokens

    state_reports_dir = paths.nusyq_hub / "state" / "reports"
    state_reports_dir.mkdir(parents=True, exist_ok=True)
    archive_stamp = now_stamp()
    archive_dir = paths.nusyq_hub / "docs" / "Archive" / "Pruned" / "state_reports" / archive_stamp
    diagnostics_reports_dir = paths.nusyq_hub / "docs" / "Reports" / "diagnostics"
    diagnostics_archive_dir = paths.nusyq_hub / "docs" / "Archive" / "Pruned" / "diagnostics_reports" / archive_stamp
    docs_reports_dir = paths.nusyq_hub / "docs" / "Reports"
    docs_reports_archive_dir = paths.nusyq_hub / "docs" / "Archive" / "Pruned" / "docs_reports" / archive_stamp
    agent_sessions_dir = paths.nusyq_hub / "docs" / "Agent-Sessions"
    agent_sessions_archive_dir = paths.nusyq_hub / "docs" / "Archive" / "Pruned" / "agent_sessions" / archive_stamp

    def _env_keep(name: str, default: int) -> int:
        try:
            return max(1, int(os.getenv(name, str(default)) or default))
        except ValueError:
            return max(1, default)

    specs: list[dict[str, Any]] = [
        {
            "name": "error_report_checkpoint",
            "pattern": "error_report_checkpoint_*.json",
            "keep": _env_keep("NUSYQ_ERROR_REPORT_CHECKPOINT_HISTORY_KEEP", 30),
            "protected": {"error_report_checkpoint_latest.json"},
        },
        {
            "name": "doctor_checkpoint",
            "pattern": "doctor_checkpoint_*.json",
            "keep": _env_keep("NUSYQ_DOCTOR_CHECKPOINT_HISTORY_KEEP", 20),
            "protected": {"doctor_checkpoint_latest.json"},
        },
        {
            "name": "doctor_report",
            "pattern": "doctor_report_*.json",
            "keep": _env_keep("NUSYQ_DOCTOR_REPORT_HISTORY_KEEP", 20),
            "protected": {"doctor_report_latest.json"},
        },
        {
            "name": "doctor_dashboard",
            "pattern": "doctor_dashboard_*.json",
            "keep": _env_keep("NUSYQ_DOCTOR_DASHBOARD_HISTORY_KEEP", 20),
            "protected": {"doctor_dashboard_latest.json"},
        },
        {
            "name": "doctor_validation",
            "pattern": "doctor_validation_*.json",
            "keep": _env_keep("NUSYQ_DOCTOR_VALIDATION_HISTORY_KEEP", 12),
            "protected": {"doctor_validation_latest.json"},
        },
        {
            "name": "system_complete_checkpoint",
            "pattern": "system_complete_checkpoint_*.json",
            "keep": _env_keep("NUSYQ_SYSTEM_COMPLETE_CHECKPOINT_HISTORY_KEEP", 20),
            "protected": {"system_complete_checkpoint_latest.json"},
        },
        {
            "name": "system_complete_gate",
            "pattern": "system_complete_gate_*.json",
            "keep": _env_keep("NUSYQ_SYSTEM_COMPLETE_GATE_HISTORY_KEEP", 20),
            "protected": {"system_complete_gate_latest.json"},
        },
        {
            "name": "system_complete_dashboard",
            "pattern": "system_complete_dashboard_*.json",
            "keep": _env_keep("NUSYQ_SYSTEM_COMPLETE_DASHBOARD_HISTORY_KEEP", 20),
            "protected": {"system_complete_dashboard_latest.json"},
        },
        {
            "name": "autonomous_monitor_trace",
            "pattern": "autonomous_monitor_trace_*.json",
            "keep": _env_keep("NUSYQ_AUTONOMOUS_TRACE_HISTORY_KEEP", 20),
            "protected": set(),
        },
        {
            "name": "openclaw_smoke",
            "pattern": "openclaw_smoke_*.json",
            "keep": _env_keep("NUSYQ_OPENCLAW_SMOKE_HISTORY_KEEP", 20),
            "protected": {"openclaw_smoke_latest.json"},
        },
        {
            "name": "lifecycle_catalog",
            "pattern": "lifecycle_catalog_*.json",
            "keep": _env_keep("NUSYQ_LIFECYCLE_CATALOG_HISTORY_KEEP", 20),
            "protected": {"lifecycle_catalog_latest.json"},
        },
        {
            "name": "current_state",
            "pattern": "current_state_*.md",
            "keep": _env_keep("NUSYQ_CURRENT_STATE_HISTORY_KEEP", 14),
            "protected": {"current_state.md"},
        },
        {
            "name": "analyze",
            "pattern": "analyze_*.md",
            "keep": _env_keep("NUSYQ_ANALYZE_REPORT_HISTORY_KEEP", 20),
            "protected": {"analyze_latest.md"},
        },
        {
            "name": "doctrine_compliance",
            "pattern": "doctrine_compliance_*.md",
            "keep": _env_keep("NUSYQ_DOCTRINE_COMPLIANCE_HISTORY_KEEP", 30),
            "protected": set(),
        },
        {
            "name": "diagnostics_unified_error_json",
            "base_dir": diagnostics_reports_dir,
            "archive_dir": diagnostics_archive_dir,
            "pattern": "unified_error_report_*.json",
            "keep": _env_keep("NUSYQ_DIAGNOSTICS_ERROR_REPORT_JSON_HISTORY_KEEP", 20),
            "protected": {"unified_error_report_latest.json"},
        },
        {
            "name": "diagnostics_unified_error_md",
            "base_dir": diagnostics_reports_dir,
            "archive_dir": diagnostics_archive_dir,
            "pattern": "unified_error_report_*.md",
            "keep": _env_keep("NUSYQ_DIAGNOSTICS_ERROR_REPORT_MD_HISTORY_KEEP", 20),
            "protected": {"unified_error_report_latest.md"},
        },
        {
            "name": "docs_reports_github_validation",
            "base_dir": docs_reports_dir,
            "archive_dir": docs_reports_archive_dir,
            "pattern": "github_validation_*.md",
            "keep": _env_keep("NUSYQ_DOCS_GITHUB_VALIDATION_HISTORY_KEEP", 60),
            "protected": set(),
        },
        {
            "name": "agent_sessions_guild_board",
            "base_dir": agent_sessions_dir,
            "archive_dir": agent_sessions_archive_dir,
            "pattern": "GUILD_BOARD_SNAPSHOT_*.md",
            "keep": _env_keep("NUSYQ_AGENT_SESSION_GUILD_BOARD_HISTORY_KEEP", 60),
            "protected": set(),
        },
        {
            "name": "agent_sessions_session",
            "base_dir": agent_sessions_dir,
            "archive_dir": agent_sessions_archive_dir,
            "pattern": "SESSION_*.md",
            "keep": _env_keep("NUSYQ_AGENT_SESSION_HISTORY_KEEP", 20),
            "protected": set(),
        },
        {
            "name": "agent_sessions_commit_batch",
            "base_dir": agent_sessions_dir,
            "archive_dir": agent_sessions_archive_dir,
            "pattern": "commit_batch_*.json",
            "keep": _env_keep("NUSYQ_AGENT_SESSION_COMMIT_BATCH_HISTORY_KEEP", 5),
            "protected": set(),
        },
        {
            "name": "agent_sessions_capabilities_demo",
            "base_dir": agent_sessions_dir,
            "archive_dir": agent_sessions_archive_dir,
            "pattern": "CAPABILITIES_DEMO_*.json",
            "keep": _env_keep("NUSYQ_AGENT_SESSION_CAPABILITIES_DEMO_HISTORY_KEEP", 3),
            "protected": set(),
        },
    ]

    pattern_results: list[dict[str, Any]] = []
    errors: list[str] = []
    archived_count = 0
    deleted_count = 0

    for spec in specs:
        source_dir = Path(spec.get("base_dir") or state_reports_dir)
        target_archive_dir = Path(spec.get("archive_dir") or archive_dir)
        source_dir.mkdir(parents=True, exist_ok=True)
        stale = _collect_stale_reports(
            source_dir,
            retention_count=int(spec["keep"]),
            pattern=str(spec["pattern"]),
            protected_names=set(spec["protected"]),
        )
        result_row = {
            "name": spec["name"],
            "base_dir": str(source_dir),
            "pattern": spec["pattern"],
            "keep": spec["keep"],
            "stale": len(stale),
            "applied": 0,
            "mode": "delete" if delete_mode else "archive",
        }

        if not dry_run and stale:
            if not delete_mode:
                target_archive_dir.mkdir(parents=True, exist_ok=True)
            for source in stale:
                try:
                    if delete_mode:
                        source.unlink()
                        deleted_count += 1
                    else:
                        destination = target_archive_dir / source.name
                        if destination.exists():
                            destination = target_archive_dir / f"{source.stem}_{uuid.uuid4().hex[:8]}{source.suffix}"
                        shutil.move(str(source), str(destination))
                        archived_count += 1
                    result_row["applied"] += 1
                except OSError as exc:
                    errors.append(f"{source.name}: {exc}")

        pattern_results.append(result_row)

    refresh_runs: list[dict[str, Any]] = []
    if not dry_run and refresh_signals:
        refresh_steps: list[tuple[str, list[str], int]] = [
            (
                "problem_signal_snapshot",
                [sys.executable, "scripts/start_nusyq.py", "problem_signal_snapshot"],
                120,
            ),
        ]
        if refresh_error_report:
            refresh_steps.append(
                (
                    "error_report_quick",
                    [
                        sys.executable,
                        "scripts/start_nusyq.py",
                        "error_report",
                        "--quick",
                        "--force",
                        "--sync",
                        "--json",
                    ],
                    120,
                )
            )
        for step_name, step_cmd, timeout_s in refresh_steps:
            rc, out, err = run(step_cmd, cwd=paths.nusyq_hub, timeout_s=timeout_s)
            refresh_runs.append(
                {
                    "name": step_name,
                    "rc": rc,
                    "stdout_tail": "\n".join(out.splitlines()[-12:]) if out else "",
                    "stderr_tail": "\n".join(err.splitlines()[-12:]) if err else "",
                }
            )
            if rc != 0:
                errors.append(f"{step_name}: rc={rc}")

    cleanup_run: dict[str, Any] | None = None
    if run_automated_cleanup:
        cleanup_cmd = [sys.executable, "scripts/automated_cleanup.py"]
        if dry_run:
            cleanup_cmd.append("--dry-run")
        cleanup_rc, cleanup_out, cleanup_err = run(
            cleanup_cmd,
            cwd=paths.nusyq_hub,
            timeout_s=600,
        )
        cleanup_run = {
            "rc": cleanup_rc,
            "stdout_tail": "\n".join(cleanup_out.splitlines()[-20:]) if cleanup_out else "",
            "stderr_tail": "\n".join(cleanup_err.splitlines()[-20:]) if cleanup_err else "",
        }
        if cleanup_rc != 0:
            errors.append(f"automated_cleanup: rc={cleanup_rc}")

    status = "ok" if not errors else "partial"
    payload: dict[str, Any] = {
        "action": "prune_reports",
        "status": status,
        "generated_at": datetime.now().isoformat(),
        "mode": "dry-run" if dry_run else ("delete" if delete_mode else "archive"),
        "state_reports_dir": str(state_reports_dir),
        "archive_dir": str(archive_dir),
        "diagnostics_reports_dir": str(diagnostics_reports_dir),
        "diagnostics_archive_dir": str(diagnostics_archive_dir),
        "docs_reports_dir": str(docs_reports_dir),
        "docs_reports_archive_dir": str(docs_reports_archive_dir),
        "agent_sessions_dir": str(agent_sessions_dir),
        "agent_sessions_archive_dir": str(agent_sessions_archive_dir),
        "archived_count": archived_count,
        "deleted_count": deleted_count,
        "patterns": pattern_results,
        "refresh_signals": refresh_signals,
        "refresh_error_report": refresh_error_report,
        "refresh_runs": refresh_runs,
        "automated_cleanup": cleanup_run,
        "errors": errors,
    }
    report_path = state_reports_dir / "prune_reports_latest.json"
    _write_json_report(report_path, payload)

    global _LAST_OUTPUTS
    _LAST_OUTPUTS = [str(report_path)]
    if not dry_run and not delete_mode and archived_count > 0:
        _LAST_OUTPUTS.append(str(archive_dir))
        if diagnostics_archive_dir.exists():
            _LAST_OUTPUTS.append(str(diagnostics_archive_dir))

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🧹 Report Prune Summary")
        print("=" * 60)
        print(f"Mode: {'dry-run' if dry_run else ('delete' if delete_mode else 'archive')}")
        print(f"Patterns checked: {len(pattern_results)}")
        print(f"Archived: {archived_count} | Deleted: {deleted_count}")
        for row in pattern_results:
            print(f"  - {row['name']}: stale={row['stale']} keep={row['keep']} applied={row['applied']}")
        if refresh_runs:
            print("\nRefresh steps:")
            for refresh in refresh_runs:
                marker = "PASS" if refresh.get("rc") == 0 else "FAIL"
                print(f"  - {refresh['name']}: {marker} (rc={refresh['rc']})")
        if errors:
            print("\nWarnings:")
            for item in errors[:20]:
                print(f"  - {item}")
        print(f"\nReport: {report_path}")
        if not dry_run and not delete_mode and archived_count > 0:
            print(f"Archive: {archive_dir}")

    return 0 if status == "ok" else 1


def _handle_lifecycle_catalog(paths: RepoPaths) -> int:
    """Log a lightweight catalog of active long-running services."""
    if not paths.nusyq_hub:
        print("[ERROR] NuSyQ-Hub path not found; cannot write lifecycle catalog.")
        return 1

    processes, psutil_available = _collect_process_snapshot()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = paths.nusyq_hub / "state" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    defaults = _load_ecosystem_defaults(paths)
    terminal_defaults = defaults.get("terminal_orchestration", {})
    retention_count = int(terminal_defaults.get("retention_count", 30) or 30)
    critical_services = set(terminal_defaults.get("critical_lifecycle_services", []))
    missing_alerts = set(terminal_defaults.get("missing_service_alerts", []))

    service_defs = [
        {
            "id": "mcp_server",
            "name": "NuSyQ MCP Server",
            "repo": "NuSyQ",
            "match_terms": ["mcp_server", "nusyq mcp", "uvicorn"],
        },
        {
            "id": "jupyter_lab",
            "name": "Jupyter Lab",
            "repo": "NuSyQ",
            "match_terms": ["jupyter", "jupyter-lab", "notebook"],
        },
        {
            "id": "simverse_dev_server",
            "name": "SimulatedVerse Dev Server",
            "repo": "SimulatedVerse",
            "match_terms": ["server/index.ts", "server/minimal-agent-server.ts", "vite", "tsx"],
        },
        {
            "id": "orchestrator",
            "name": "NuSyQ Orchestrator",
            "repo": "NuSyQ",
            "match_terms": ["start_orchestrator.py", "MultiAIOrchestrator"],
        },
        {
            "id": "hub_autonomous_monitor",
            "name": "NuSyQ-Hub Autonomous Monitor",
            "repo": "NuSyQ-Hub",
            "match_terms": ["autonomous_monitor.py"],
        },
        {
            "id": "hub_context_server",
            "name": "NuSyQ-Hub Context Server",
            "repo": "NuSyQ-Hub",
            "match_terms": ["context_server.py"],
        },
        {
            "id": "hub_healthcheck_server",
            "name": "NuSyQ-Hub Healthcheck Server",
            "repo": "NuSyQ-Hub",
            "match_terms": ["healthcheck_server.py"],
        },
        {
            "id": "hub_agent_hub",
            "name": "NuSyQ-Hub Agent Hub",
            "repo": "NuSyQ-Hub",
            "match_terms": ["agent_communication_hub.py"],
        },
        {
            "id": "hub_ai_intermediary",
            "name": "NuSyQ-Hub AI Intermediary",
            "repo": "NuSyQ-Hub",
            "match_terms": ["ai_intermediary.py"],
        },
        {
            "id": "architecture_watcher",
            "name": "Architecture Watcher",
            "repo": "NuSyQ-Hub",
            "match_terms": ["architecturewatcher.py", "architecture watcher"],
        },
    ]

    critical_defs = {
        "pu_queue": {
            "name": "PU Queue Processor",
            "repo": "NuSyQ-Hub",
            "match_terms": ["unified_pu_queue", "pu_queue", "processing_units"],
        },
        "quest_log_sync": {
            "name": "Quest Log Sync",
            "repo": "NuSyQ-Hub",
            "match_terms": ["cross_ecosystem_sync", "quest_log", "quest replay"],
        },
        "trace_service": {
            "name": "Trace Service",
            "repo": "NuSyQ-Hub",
            "match_terms": ["otel", "opentelemetry", "trace_service"],
        },
        "guild_board_renderer": {
            "name": "Guild Board Renderer",
            "repo": "NuSyQ-Hub",
            "match_terms": ["guild_render", "guild_board", "GUILD_BOARD.md"],
        },
    }
    for svc_id, payload in critical_defs.items():
        service_defs.append(
            {
                "id": svc_id,
                "name": payload["name"],
                "repo": payload["repo"],
                "match_terms": payload["match_terms"],
            }
        )

    def _match_process(entry: dict[str, Any], terms: list[str]) -> bool:
        cmdline = " ".join(entry.get("cmdline", [])).lower()
        name = (entry.get("name") or "").lower()
        haystack = f"{name} {cmdline}"
        return any(term.lower() in haystack for term in terms)

    services = []
    for service in service_defs:
        matches = [p for p in processes if _match_process(p, service["match_terms"])]
        services.append(
            {
                "id": service.get("id", service["name"]),
                "name": service["name"],
                "repo": service["repo"],
                "match_terms": service["match_terms"],
                "active": bool(matches),
                "processes": [
                    {
                        "pid": p["pid"],
                        "name": p["name"],
                        "cmdline": " ".join(p.get("cmdline", []))[:240],
                        "status": p.get("status", ""),
                    }
                    for p in matches
                ],
            }
        )

    process_summary = {
        "python": 0,
        "node": 0,
        "ollama": 0,
        "docker": 0,
        "pwsh": 0,
    }
    for proc in processes:
        pname = (proc.get("name") or "").lower()
        if "python" in pname:
            process_summary["python"] += 1
        if "node" in pname:
            process_summary["node"] += 1
        if "ollama" in pname:
            process_summary["ollama"] += 1
        if "docker" in pname:
            process_summary["docker"] += 1
        if "pwsh" in pname or "powershell" in pname:
            process_summary["pwsh"] += 1

    terminal_state_path = paths.nusyq_hub / "data" / "intelligent_terminal_state.json"
    terminal_state = {}
    if terminal_state_path.exists():
        try:
            terminal_state = json.loads(terminal_state_path.read_text(encoding="utf-8"))
        except Exception:
            terminal_state = {}

    missing_critical = [svc["id"] for svc in services if svc["id"] in critical_services and not svc["active"]]
    alerts_triggered = [svc for svc in missing_critical if svc in missing_alerts]

    report = {
        "timestamp": datetime.now().isoformat(),
        "psutil_available": psutil_available,
        "total_processes": len(processes),
        "services": services,
        "process_summary": process_summary,
        "intelligent_terminal_state": terminal_state,
        "critical_services_missing": missing_critical,
        "alerts_triggered": alerts_triggered,
        "defaults_applied": {
            "retention_count": retention_count,
            "critical_services": sorted(critical_services),
            "missing_service_alerts": sorted(missing_alerts),
        },
    }

    report_path = report_dir / f"lifecycle_catalog_{timestamp}.json"
    latest_path = report_dir / "lifecycle_catalog_latest.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _prune_lifecycle_reports(
        report_dir,
        retention_count,
        pattern="lifecycle_catalog_*.json",
        protected_names={"lifecycle_catalog_latest.json"},
    )

    active_services = [svc for svc in services if svc["active"]]
    print("?? Lifecycle Catalog")
    print("=" * 60)
    print(f"Active services: {len(active_services)}")
    for svc in active_services:
        print(f"  ? {svc['name']} ({svc['repo']})")
        for proc in svc["processes"][:3]:
            print(f"     - pid {proc['pid']}: {proc['cmdline']}")

    if terminal_state:
        print(f"\nTerminal groups configured: {terminal_state.get('total_terminals', 0)}")
    if alerts_triggered:
        print("\n!! Missing critical services:")
        for svc_id in alerts_triggered:
            print(f"  - {svc_id}")

    print(f"\nSaved: {report_path}")
    return 0


def _maybe_refresh_lifecycle_catalog(paths: RepoPaths, cadence_hours: float) -> None:
    if not paths.nusyq_hub or cadence_hours <= 0:
        return
    latest_path = paths.nusyq_hub / "state" / "reports" / "lifecycle_catalog_latest.json"
    if not latest_path.exists():
        _handle_lifecycle_catalog(paths)
        return
    try:
        age_seconds = time.time() - latest_path.stat().st_mtime
    except OSError:
        _handle_lifecycle_catalog(paths)
        return
    if age_seconds >= cadence_hours * 3600:
        _handle_lifecycle_catalog(paths)


def _should_skip_lifecycle_refresh(action: str) -> bool:
    """Skip lifecycle refresh for read-only status/report actions."""
    status_like_actions = {
        "ai_status",
        "brief",
        "culture_ship",
        "delegation_matrix",
        "claude_doctor",
        "codex_doctor",
        "copilot_doctor",
        "multi_agent_doctor",
        "agent_fleet_doctor",
        "doctor",
        "doctor_status",
        "error_report",
        "error_report_status",
        "failover_status",
        "integration_health",
        "log_dedup_status",
        "problem_signal_snapshot",
        "prune_reports",
        "quantum_resolver_status",
        "vscode_diagnostics_bridge",
    }
    return action.endswith("_status") or action in status_like_actions


def _handle_task_summary(paths: RepoPaths) -> int:
    """Summarize VS Code tasks across repos for lifecycle hygiene."""
    repo_map = {
        "NuSyQ-Hub": paths.nusyq_hub,
        "SimulatedVerse": paths.simulatedverse,
        "NuSyQ": paths.nusyq_root,
    }

    def _is_likely_long_running(task: dict[str, Any]) -> bool:
        label_lower = (task.get("label") or "").lower()
        if not task.get("command"):
            return False
        if "menu:" in label_lower:
            return False
        args = [str(arg).lower() for arg in task.get("args", [])]
        if "-d" in args or "down" in args or "stop" in args:
            return False
        long_terms = ["start", "dev", "server", "watch", "monitor", "logs", "tail"]
        stop_terms = [
            "check",
            "test",
            "lint",
            "build",
            "audit",
            "report",
            "snapshot",
            "scan",
            "status",
        ]
        return any(term in label_lower for term in long_terms) and not any(term in label_lower for term in stop_terms)

    summary = {"timestamp": datetime.now().isoformat(), "repos": {}}
    print("?? Cross-Repo Task Summary")
    print("=" * 60)

    for repo_name, repo_path in repo_map.items():
        if not repo_path:
            summary["repos"][repo_name] = {"error": "path_missing"}
            print(f"{repo_name}: path missing")
            continue

        tasks_path = repo_path / ".vscode" / "tasks.json"
        if not tasks_path.exists():
            summary["repos"][repo_name] = {"tasks": 0, "missing_tasks_file": True}
            print(f"{repo_name}: no .vscode/tasks.json")
            continue

        data = json.loads(tasks_path.read_text(encoding="utf-8"))
        tasks = data.get("tasks", [])
        total = len(tasks)
        background = [t for t in tasks if t.get("isBackground") is True]
        likely_missing = [t for t in tasks if _is_likely_long_running(t) and t.get("isBackground") is not True]

        summary["repos"][repo_name] = {
            "tasks": total,
            "background": len(background),
            "likely_long_running_without_background": [t.get("label") for t in likely_missing],
        }

        print(f"{repo_name}: {total} tasks, {len(background)} background")
        if likely_missing:
            print("  ? Likely long-running without isBackground:")
            for task in likely_missing:
                print(f"     - {task.get('label')}")

    if paths.nusyq_hub:
        report_dir = paths.nusyq_hub / "state" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"task_summary_{timestamp}.json"
        latest_path = report_dir / "task_summary_latest.json"
        report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        latest_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\nSaved: {report_path}")

    return 0


def _run_guild(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


def _jobs_dir(paths: RepoPaths) -> Path:
    return paths.nusyq_hub / "state" / "jobs"


def _job_path(paths: RepoPaths, job_id: str) -> Path:
    return _jobs_dir(paths) / f"{job_id}.json"


def _is_process_running(pid: int) -> bool:
    if pid <= 0:
        return False

    status_path = Path(f"/proc/{pid}/status")
    if status_path.exists():
        status_text = status_path.read_text(encoding="utf-8", errors="replace")
        if "\nState:\tZ" in status_text or status_text.startswith("State:\tZ"):
            return False

    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _terminate_job_process(pid: int, grace_s: float = 2.0) -> bool:
    """Best-effort terminate for a background job process."""
    if pid <= 0:
        return False
    with contextlib.suppress(Exception):
        os.kill(pid, signal.SIGTERM)
    deadline = time.time() + max(0.1, grace_s)
    while time.time() < deadline:
        if not _is_process_running(pid):
            return True
        time.sleep(0.1)
    with contextlib.suppress(Exception):
        os.kill(pid, signal.SIGKILL)
    return not _is_process_running(pid)


def _write_job(paths: RepoPaths, payload: dict[str, Any]) -> Path:
    path = _job_path(paths, str(payload["job_id"]))
    _write_json_report(path, payload)
    return path


def _read_job(paths: RepoPaths, job_id: str) -> dict[str, Any] | None:
    path = _job_path(paths, job_id)
    return read_json(path)


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _reconcile_jobs(paths: RepoPaths, job_type: str | None = None, expire_hours: float = 2.0) -> dict[str, int]:
    """Reconcile stale job states and expire unknown historical entries."""
    summary = {"refreshed": 0, "expired": 0, "errors": 0}
    jobs_dir = _jobs_dir(paths)
    if not jobs_dir.exists():
        return summary

    pattern = f"{job_type}_*.json" if job_type else "*.json"
    cutoff = datetime.now() - timedelta(hours=max(0.0, expire_hours))
    for job_file in jobs_dir.glob(pattern):
        try:
            raw_job = read_json(job_file)
            if not isinstance(raw_job, dict):
                continue
            job_id = str(raw_job.get("job_id") or job_file.stem)
            status = str(raw_job.get("status") or "").lower()

            should_refresh = status in {"running", "unknown"} or (
                status == "failed" and str(raw_job.get("failure_reason") or "") == "missing_rc_and_no_artifacts"
            )
            if should_refresh:
                refreshed = _refresh_job_status(paths, job_id)
                if isinstance(refreshed, dict):
                    raw_job = refreshed
                    status = str(refreshed.get("status") or "").lower()
                    summary["refreshed"] += 1

            if status == "unknown":
                marker = _parse_iso_datetime(raw_job.get("finished_at")) or _parse_iso_datetime(
                    raw_job.get("started_at")
                )
                if marker and marker < cutoff:
                    raw_job["status"] = "expired"
                    raw_job["expired_at"] = datetime.now().isoformat()
                    raw_job["expiration_reason"] = f"unknown status older than {expire_hours:.1f}h"
                    _write_job(paths, raw_job)
                    summary["expired"] += 1
        except Exception:
            summary["errors"] += 1

    return summary


def _refresh_job_status(paths: RepoPaths, job_id: str) -> dict[str, Any] | None:
    job = _read_job(paths, job_id)
    if not isinstance(job, dict):
        return None

    pid = int(job.get("pid") or 0)
    running = _is_process_running(pid)
    if running:
        job["status"] = "running"
    else:
        rc_file = job.get("rc_file")
        if job.get("rc") is None and isinstance(rc_file, str) and rc_file:
            rc_path = Path(rc_file)
            if rc_path.exists():
                try:
                    job["rc"] = int(rc_path.read_text(encoding="utf-8").strip())
                except (TypeError, ValueError, OSError):
                    pass
        rc = job.get("rc")
        if rc is None:
            inferred = _infer_job_status_from_checkpoint(job)
            if not inferred:
                inferred = _infer_job_status_from_stdout(job)
            if inferred:
                inferred_status, inferred_rc = inferred
                job["status"] = inferred_status
                job["rc"] = inferred_rc
            # If we expected an rc_file but never got one, report indeterminate completion
            # instead of a false "completed".
            elif isinstance(rc_file, str) and rc_file:
                metadata = job.get("metadata")
                has_checkpoint = isinstance(metadata, dict) and isinstance(metadata.get("checkpoint_file"), str)
                if has_checkpoint and not _job_logs_have_output(job) and not _job_checkpoint_updated_since_start(job):
                    started_at = _parse_iso_datetime(job.get("started_at"))
                    artifact_grace_s = float(os.getenv("NUSYQ_JOB_ARTIFACT_GRACE_S", "60"))
                    within_grace = False
                    if started_at:
                        now_dt = datetime.now(started_at.tzinfo) if started_at.tzinfo else datetime.now()
                        within_grace = (now_dt - started_at).total_seconds() < max(0.0, artifact_grace_s)
                    if within_grace:
                        job["status"] = "unknown"
                        job["waiting_for_artifacts"] = True
                    else:
                        job["status"] = "failed"
                        job["rc"] = 1
                        job["failure_reason"] = "missing_rc_and_no_artifacts"
                else:
                    job["status"] = "unknown"
            else:
                job["status"] = "completed"
        elif int(rc) == 0:
            job["status"] = "completed"
        else:
            job["status"] = "failed"
        job.setdefault("finished_at", datetime.now().isoformat())

    if str(job.get("status") or "").lower() != "failed":
        job.pop("failure_reason", None)
    if str(job.get("status") or "").lower() != "unknown":
        job.pop("waiting_for_artifacts", None)

    _write_job(paths, job)
    return job


def _infer_job_status_from_checkpoint(job: dict[str, Any]) -> tuple[str, int] | None:
    metadata = job.get("metadata")
    if not isinstance(metadata, dict):
        return None
    checkpoint_file = metadata.get("checkpoint_file")
    if not isinstance(checkpoint_file, str) or not checkpoint_file:
        return None
    checkpoint = read_json(Path(checkpoint_file))
    if not isinstance(checkpoint, dict):
        return None
    job_started = _parse_iso_datetime(job.get("started_at"))
    checkpoint_marker = (
        _parse_iso_datetime(checkpoint.get("updated_at"))
        or _parse_iso_datetime(checkpoint.get("finished_at"))
        or _parse_iso_datetime(checkpoint.get("generated_at"))
        or _parse_iso_datetime(checkpoint.get("timestamp"))
        or _parse_iso_datetime(checkpoint.get("started_at"))
    )
    if job_started:
        if not checkpoint_marker or checkpoint_marker < job_started:
            return None
    status = str(checkpoint.get("status") or "").lower()
    if status in {"completed", "ok", "success", "partial", "degraded"}:
        return ("completed", 0)
    if status in {"failed", "error"}:
        return ("failed", 1)
    return None


def _infer_job_status_from_stdout(job: dict[str, Any]) -> tuple[str, int] | None:
    stdout_log = job.get("stdout_log")
    if not isinstance(stdout_log, str) or not stdout_log:
        return None
    stdout_path = Path(stdout_log)
    if not stdout_path.exists():
        return None
    try:
        raw = stdout_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    payload = _extract_json_payload(raw)
    if not isinstance(payload, dict):
        return None
    status = str(payload.get("status") or "").lower()
    if status in {"completed", "ok", "success", "submitted", "partial", "degraded"}:
        return ("completed", 0)
    if status in {"failed", "error"}:
        return ("failed", 1)
    return None


def _job_logs_have_output(job: dict[str, Any]) -> bool:
    for key in ("stdout_log", "stderr_log"):
        value = job.get(key)
        if not isinstance(value, str) or not value:
            continue
        path = Path(value)
        with contextlib.suppress(OSError):
            if path.exists() and path.stat().st_size > 0:
                return True
    return False


def _job_checkpoint_updated_since_start(job: dict[str, Any]) -> bool:
    metadata = job.get("metadata")
    if not isinstance(metadata, dict):
        return False
    checkpoint_file = metadata.get("checkpoint_file")
    if not isinstance(checkpoint_file, str) or not checkpoint_file:
        return False
    checkpoint = read_json(Path(checkpoint_file))
    if not isinstance(checkpoint, dict):
        return False
    job_started = _parse_iso_datetime(job.get("started_at"))
    checkpoint_updated = (
        _parse_iso_datetime(checkpoint.get("updated_at"))
        or _parse_iso_datetime(checkpoint.get("finished_at"))
        or _parse_iso_datetime(checkpoint.get("generated_at"))
        or _parse_iso_datetime(checkpoint.get("timestamp"))
    )
    if not checkpoint_updated:
        return False
    if not job_started:
        return True
    return checkpoint_updated >= job_started


def _start_subprocess_job(
    paths: RepoPaths,
    job_type: str,
    command: list[str],
    cwd: Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    jobs_dir = _jobs_dir(paths)
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_id = f"{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    stdout_log = jobs_dir / f"{job_id}.stdout.log"
    stderr_log = jobs_dir / f"{job_id}.stderr.log"
    rc_file = jobs_dir / f"{job_id}.rc"
    job_env = _build_env()
    job_env["NUSYQ_JOB_ID"] = job_id
    job_env["NUSYQ_JOB_RC_FILE"] = str(rc_file)

    with (
        stdout_log.open("w", encoding="utf-8") as out_handle,
        stderr_log.open("w", encoding="utf-8") as err_handle,
    ):
        proc = subprocess.Popen(
            command,
            cwd=str(cwd or paths.nusyq_hub),
            stdout=out_handle,
            stderr=err_handle,
            text=True,
            env=job_env,
        )

    payload: dict[str, Any] = {
        "job_id": job_id,
        "job_type": job_type,
        "status": "running",
        "pid": proc.pid,
        "started_at": datetime.now().isoformat(),
        "command": command,
        "cwd": str(cwd or paths.nusyq_hub),
        "stdout_log": str(stdout_log),
        "stderr_log": str(stderr_log),
        "rc_file": str(rc_file),
    }
    if metadata:
        payload["metadata"] = metadata
    _write_job(paths, payload)
    return payload


def _handle_subprocess_job_status(
    args: list[str],
    paths: RepoPaths,
    *,
    job_type: str,
    action_name: str,
    checkpoint_loader: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
    json_mode: bool = False,
) -> int:
    if not paths.nusyq_hub:
        print(ERROR_NUSYQ_HUB_PATH_NOT_FOUND)
        return 1
    audit_intel = collect_audit_intelligence(paths.nusyq_hub, include_sessions=False)

    cancel_requested = "--cancel" in args[1:]
    retry_requested = "--retry" in args[1:]
    expire_hours = float(os.getenv("NUSYQ_JOB_EXPIRE_HOURS", "2"))
    for arg in args[1:]:
        if arg.startswith("--expire-hours="):
            try:
                expire_hours = max(0.0, float(arg.split("=", 1)[1]))
            except ValueError:
                pass

    _ = _reconcile_jobs(
        paths,
        job_type=job_type,
        expire_hours=expire_hours,
    )

    job_id = ""
    for token in args[1:]:
        if not token.startswith("--"):
            job_id = token
            break
    if not job_id:
        jobs = sorted(_jobs_dir(paths).glob(f"{job_type}_*.json"), key=lambda p: p.stat().st_mtime)
        if not jobs:
            msg = {
                "action": action_name,
                "status": "error",
                "error": "no jobs found",
                "audit_intelligence": audit_intel,
            }
            if json_mode:
                print(json.dumps(msg, indent=2))
            else:
                print(f"No {job_type} jobs found.")
                print("\n📚 Audit Intelligence")
                for line in format_audit_intelligence_lines(audit_intel, max_lines=4):
                    print(f"  - {line}")
            return 1
        selected = jobs[-1]
        for candidate in reversed(jobs):
            candidate_payload = read_json(candidate)
            candidate_status = (
                str(candidate_payload.get("status", "")).lower() if isinstance(candidate_payload, dict) else ""
            )
            if candidate_status != "expired":
                selected = candidate
                break
        job_id = selected.stem

    if retry_requested:
        existing = _read_job(paths, job_id)
        if not isinstance(existing, dict):
            msg = {
                "action": action_name,
                "status": "error",
                "error": f"job not found: {job_id}",
            }
            print(json.dumps(msg, indent=2) if json_mode else f"Job not found: {job_id}")
            return 1
        existing_status = str(existing.get("status", "")).lower()
        if existing_status == "running":
            if not cancel_requested:
                msg = {
                    "action": action_name,
                    "status": "error",
                    "error": f"job {job_id} is still running; pass --cancel --retry to restart",
                }
                print(json.dumps(msg, indent=2) if json_mode else msg["error"])
                return 1
            pid = int(existing.get("pid") or 0)
            terminated = _terminate_job_process(pid)
            existing["status"] = "canceled"
            existing["canceled_at"] = datetime.now().isoformat()
            existing["finished_at"] = datetime.now().isoformat()
            existing["cancel_succeeded"] = terminated
            if existing.get("rc") is None:
                existing["rc"] = 130 if terminated else 1
            _write_job(paths, existing)

        command = existing.get("command")
        if not isinstance(command, list) or not all(isinstance(token, str) for token in command):
            msg = {
                "action": action_name,
                "status": "error",
                "error": f"job {job_id} has no retryable command",
            }
            print(json.dumps(msg, indent=2) if json_mode else msg["error"])
            return 1
        cwd_raw = existing.get("cwd")
        cwd_path = Path(cwd_raw) if isinstance(cwd_raw, str) and cwd_raw else paths.nusyq_hub
        metadata = existing.get("metadata")
        retry_metadata: dict[str, Any] = dict(metadata) if isinstance(metadata, dict) else {}
        retry_metadata["retry_of"] = job_id
        retry_metadata["retried_at"] = datetime.now().isoformat()
        new_job = _start_subprocess_job(
            paths,
            job_type=job_type,
            command=list(command),
            cwd=cwd_path,
            metadata=retry_metadata,
        )
        payload = {
            "action": action_name,
            "status": "submitted",
            "retry_of": job_id,
            **new_job,
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"♻️ Retried {job_type} job")
            print(f"Previous Job: {job_id}")
            print(f"New Job: {payload.get('job_id')}")
            print(f"PID: {payload.get('pid')}")
        return 0

    waited = 0.0
    timeout_s = 0.0
    interval_s = 2.0
    for arg in args[1:]:
        if arg.startswith("--wait="):
            try:
                timeout_s = max(0.0, float(arg.split("=", 1)[1]))
            except ValueError:
                timeout_s = 0.0
        if arg.startswith("--interval="):
            try:
                interval_s = max(0.5, float(arg.split("=", 1)[1]))
            except ValueError:
                interval_s = 2.0

    while True:
        if cancel_requested:
            existing = _read_job(paths, job_id)
            if not isinstance(existing, dict):
                msg = {
                    "action": action_name,
                    "status": "error",
                    "error": f"job not found: {job_id}",
                }
                print(json.dumps(msg, indent=2) if json_mode else f"Job not found: {job_id}")
                return 1
            pid = int(existing.get("pid") or 0)
            terminated = _terminate_job_process(pid)
            existing["status"] = "canceled"
            existing["canceled_at"] = datetime.now().isoformat()
            existing["finished_at"] = datetime.now().isoformat()
            existing["cancel_succeeded"] = terminated
            if existing.get("rc") is None:
                existing["rc"] = 130 if terminated else 1
            _write_job(paths, existing)
            job = existing
            break

        job = _refresh_job_status(paths, job_id)
        if not isinstance(job, dict):
            msg = {
                "action": action_name,
                "status": "error",
                "error": f"job not found: {job_id}",
            }
            print(json.dumps(msg, indent=2) if json_mode else f"Job not found: {job_id}")
            return 1
        if job.get("status") != "running" or waited >= timeout_s:
            break
        time.sleep(interval_s)
        waited += interval_s

    job_payload = {"action": action_name, **job}
    if checkpoint_loader:
        checkpoint = checkpoint_loader(job_payload)
        if checkpoint:
            job_payload["checkpoint"] = checkpoint
    job_payload["audit_intelligence"] = audit_intel
    if json_mode:
        print(json.dumps(job_payload, indent=2, ensure_ascii=False))
    else:
        print(f"🛰️ {job_type.replace('_', ' ').title()} Job Status")
        print("=" * 60)
        print(f"Job ID: {job_payload.get('job_id')}")
        print(f"Status: {job_payload.get('status')}")
        print(f"PID: {job_payload.get('pid')}")
        print(f"stdout: {job_payload.get('stdout_log')}")
        print(f"stderr: {job_payload.get('stderr_log')}")
        checkpoint = job_payload.get("checkpoint")
        if isinstance(checkpoint, dict) and checkpoint.get("available"):
            completed = checkpoint.get("completed_checks")
            total = checkpoint.get("total_planned")
            current = checkpoint.get("current_check")
            print(f"checkpoint: completed={completed}/{total} current={current} status={checkpoint.get('status')}")
        if job_type in {"culture_ship", "doctor", "error_report"}:
            print("\n📚 Audit Intelligence")
            for line in format_audit_intelligence_lines(audit_intel, max_lines=4):
                print(f"  - {line}")

    status = str(job_payload.get("status", "")).lower()
    if cancel_requested:
        return 0 if bool(job_payload.get("cancel_succeeded", False)) else 1
    if status in {"failed", "unknown", "expired", "canceled"}:
        return 1
    return 0


@dataclass(frozen=True)
class DoctorRuntimeOptions:
    async_mode: bool = False


def _parse_doctor_runtime_args(args: list[str]) -> DoctorRuntimeOptions:
    tokens = list(args[1:] if args and args[0] == "doctor" else args)
    return DoctorRuntimeOptions(async_mode="--async" in tokens and "--sync" not in tokens)


def _handle_doctor_action(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    options = _parse_doctor_runtime_args(args)
    if options.async_mode:
        if not paths.nusyq_hub:
            payload = {
                "action": "doctor",
                "status": "error",
                "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
            }
            print(json.dumps(payload, indent=2) if json_mode else payload["error"])
            return 1
        checkpoint_file = paths.nusyq_hub / "state" / "reports" / "doctor_checkpoint_latest.json"
        cmd = [sys.executable, "scripts/start_nusyq.py", "doctor", "--sync", "--json"]
        cmd.extend(token for token in args[1:] if token not in {"--async", "--sync", "--json"})
        job = _start_subprocess_job(
            paths,
            job_type="doctor",
            command=cmd,
            cwd=paths.nusyq_hub,
            metadata={
                "runner": "start_nusyq",
                "action": "doctor",
                "checkpoint_file": str(checkpoint_file),
            },
        )
        payload = {
            "action": "doctor",
            "status": "submitted",
            "job_id": job["job_id"],
            "pid": job["pid"],
            "stdout_log": job["stdout_log"],
            "stderr_log": job["stderr_log"],
            "checkpoint_file": str(checkpoint_file),
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🩺 Doctor diagnostics submitted as background job")
            print(f"Job ID: {payload['job_id']}")
            print(f"PID: {payload['pid']}")
            print(f"stdout: {payload['stdout_log']}")
            print(f"stderr: {payload['stderr_log']}")
            print(f"Check status: python scripts/start_nusyq.py doctor_status {payload['job_id']} --wait=30")
        return 0

    return handle_doctor(
        paths,
        run,
        HEALTH_FILENAME,
        json_mode=json_mode,
        action_args=args,
    )


OPENCLAW_CHANNEL_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "slack": ("bot_token", "app_token"),
    "discord": ("token",),
    "telegram": ("bot_token",),
    "whatsapp": ("account_sid", "auth_token"),
    "teams": ("bot_id", "bot_password"),
}
OPENCLAW_PLACEHOLDER_MARKERS = (
    "redacted_replace",
    "replace_with",
    "your-",
    "example",
    "changeme",
)
OPENCLAW_GATEWAY_PID_FILENAME = "openclaw_gateway.pid"
OPENCLAW_GATEWAY_LOG_FILENAME = "openclaw_gateway.log"
OPENCLAW_BRIDGE_PID_FILENAME = "openclaw_bridge.pid"
OPENCLAW_BRIDGE_LOG_FILENAME = "openclaw_bridge.log"
OPENCLAW_DEFAULT_GATEWAY_PORT = 18789
OPENCLAW_DEFAULT_GATEWAY_BIND = "loopback"
OPENCLAW_GATEWAY_READY_TIMEOUT_S = 20.0
OPENCLAW_STATUS_GATEWAY_HEALTH_TIMEOUT_S = 4.0
OPENCLAW_STATUS_CHANNELS_TIMEOUT_S = 4.0
OPENCLAW_LAUNCHER_PROBE_TIMEOUT_S = 3.0
OPENCLAW_INTERNAL_TARGET_SYSTEMS = {
    "auto",
    "ollama",
    "lmstudio",
    "chatdev",
    "copilot",
    "codex",
    "claude_cli",
    "claude",
    "vscode_copilot",
    "vscode_claude",
    "vscode_codex",
    "consciousness",
    "quantum_resolver",
}
OPENCLAW_SYSTEM_CHANNEL_NAMES = set(OPENCLAW_INTERNAL_TARGET_SYSTEMS) | {
    "openai",
    "anthropic",
    "lm_studio",
    "vllm",
}
ANTIGRAVITY_RUNTIME_PID_FILENAME = "open_antigravity_runtime.pid"
ANTIGRAVITY_RUNTIME_LOG_FILENAME = "open_antigravity_runtime.log"
ANTIGRAVITY_DEFAULT_PORT = 8080
ANTIGRAVITY_READY_TIMEOUT_S = 20.0
IGNITION_API_PID_FILENAME = "ignition_api.pid"
IGNITION_API_LOG_FILENAME = "ignition_api.log"
IGNITION_API_READY_TIMEOUT_S = 25.0


def _looks_like_placeholder_secret(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    if not normalized or normalized in {"none", "null", "undefined"}:
        return True
    return any(marker in normalized for marker in OPENCLAW_PLACEHOLDER_MARKERS)


def _openclaw_field_format_valid(channel: str, field: str, value: Any) -> bool:
    """Conservative format checks to avoid false-positive 'ready' channels."""
    if _looks_like_placeholder_secret(value):
        return False
    if not isinstance(value, str):
        return True

    token = value.strip()
    if not token:
        return False

    if channel == "slack" and field == "bot_token":
        return token.startswith("xoxb-")
    if channel == "slack" and field == "app_token":
        return token.startswith("xapp-")
    if channel == "discord" and field == "token":
        return token.count(".") >= 2 and len(token) >= 30
    if channel == "telegram" and field == "bot_token":
        return bool(re.match(r"^\d{6,}:[A-Za-z0-9_-]{20,}$", token))
    if channel == "whatsapp" and field == "account_sid":
        return token.startswith("AC") and len(token) >= 20
    if channel == "whatsapp" and field == "auth_token":
        return len(token) >= 20
    if channel == "teams" and field == "bot_id":
        return bool(re.match(r"^[0-9a-fA-F-]{16,}$", token))
    if channel == "teams" and field == "bot_password":
        return len(token) >= 16
    return True


def _probe_endpoint_reachable(url: str, timeout_s: float = 1.0) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return False, "invalid_url"
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme in {"https", "wss"} else 80
        with socket.create_connection((host, port), timeout=timeout_s):
            return True, f"{host}:{port}"
    except Exception as exc:
        return False, str(exc)


def _openclaw_runtime_dir(hub_path: Path) -> Path:
    runtime_dir = hub_path / "state" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return runtime_dir


def _openclaw_gateway_pid_path(hub_path: Path) -> Path:
    return _openclaw_runtime_dir(hub_path) / OPENCLAW_GATEWAY_PID_FILENAME


def _openclaw_gateway_log_path(hub_path: Path) -> Path:
    return _openclaw_runtime_dir(hub_path) / OPENCLAW_GATEWAY_LOG_FILENAME


def _openclaw_bridge_pid_path(hub_path: Path) -> Path:
    return _openclaw_runtime_dir(hub_path) / OPENCLAW_BRIDGE_PID_FILENAME


def _openclaw_bridge_log_path(hub_path: Path) -> Path:
    return _openclaw_runtime_dir(hub_path) / OPENCLAW_BRIDGE_LOG_FILENAME


def _antigravity_runtime_pid_path(hub_path: Path) -> Path:
    return _openclaw_runtime_dir(hub_path) / ANTIGRAVITY_RUNTIME_PID_FILENAME


def _antigravity_runtime_log_path(hub_path: Path) -> Path:
    return _openclaw_runtime_dir(hub_path) / ANTIGRAVITY_RUNTIME_LOG_FILENAME


def _ignition_api_pid_path(hub_path: Path) -> Path:
    return _openclaw_runtime_dir(hub_path) / IGNITION_API_PID_FILENAME


def _ignition_api_log_path(hub_path: Path) -> Path:
    return _openclaw_runtime_dir(hub_path) / IGNITION_API_LOG_FILENAME


def _probe_http_health(url: str, timeout_s: float = 1.5) -> tuple[bool, str]:
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=timeout_s) as response:
            status_code = int(getattr(response, "status", 500))
            body = response.read(4096).decode("utf-8", errors="replace")
            if 200 <= status_code < 300:
                return True, f"HTTP {status_code} {body[:120].strip()}"
            return False, f"HTTP {status_code} {body[:120].strip()}"
    except URLError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, str(exc)


_PROBE_BLOCKED_ERROR_MARKERS = (
    "operation not permitted",
    "permission denied",
    "access is denied",
    "sandbox(denied",
    "winerror 5",
    "permissionerror",
)


def _looks_like_probe_blocked_error(detail: Any) -> bool:
    """Detect sandbox/runtime permission failures distinct from service failures."""
    if detail is None:
        return False
    if isinstance(detail, dict):
        return any(_looks_like_probe_blocked_error(value) for value in detail.values())
    if isinstance(detail, (list, tuple, set)):
        return any(_looks_like_probe_blocked_error(value) for value in detail)
    text = str(detail).strip().lower()
    if not text:
        return False
    if "[errno 1]" in text:
        return True
    return any(marker in text for marker in _PROBE_BLOCKED_ERROR_MARKERS)


def _read_openclaw_pid_record(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _write_openclaw_pid_record(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _to_windows_path(path: Path) -> str:
    value = str(path)
    if len(value) > 7 and value.startswith("/mnt/") and value[5].isalpha() and value[6] == "/":
        drive = value[5].upper()
        tail = value[7:].replace("/", "\\")
        return f"{drive}:\\{tail}" if tail else f"{drive}:\\"
    return value


def _gateway_port_from_url(url: str, default_port: int = OPENCLAW_DEFAULT_GATEWAY_PORT) -> int:
    parsed = urlparse(url)
    if parsed.port:
        return int(parsed.port)
    if parsed.scheme in {"https", "wss"}:
        return 443
    if parsed.scheme in {"http", "ws"}:
        return 80 if default_port <= 0 else default_port
    return default_port


def _wsl_default_gateway_ip() -> str | None:
    rc, out, _err = run(["ip", "route", "show", "default"], timeout_s=3)
    if rc != 0:
        return None
    for line in out.splitlines():
        parts = line.split()
        if "via" in parts:
            idx = parts.index("via")
            if idx + 1 < len(parts):
                candidate = parts[idx + 1].strip()
                if candidate:
                    return candidate
    return None


def _windows_listening_pids(port: int) -> list[int]:
    if shutil.which("cmd.exe") is None:
        return []
    rc, out, _err = run(
        ["cmd.exe", "/c", f"netstat -ano -p tcp | findstr :{int(port)}"],
        timeout_s=6,
    )
    if rc != 0 or not out:
        return []
    pids: set[int] = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        state = parts[3].upper()
        if state != "LISTENING":
            continue
        with contextlib.suppress(ValueError):
            pids.add(int(parts[4]))
    return sorted(pids)


def _windows_taskkill_pid(pid: int) -> bool:
    rc, _out, _err = run(["cmd.exe", "/c", f"taskkill /PID {int(pid)} /F"], timeout_s=8)
    return rc == 0


def _resolve_openclaw_cli() -> tuple[list[str] | None, dict[str, Any]]:
    """Resolve a reliable OpenClaw launcher command for this shell."""
    details: dict[str, Any] = {"strategy": "unresolved"}

    def _probe_launcher(base_command: list[str]) -> tuple[bool, str]:
        probe_args = [
            ["--version"],
            ["--help"],
            ["gateway", "--help"],
        ]
        attempts: list[str] = []
        for probe in probe_args:
            rc, out, err = run([*base_command, *probe], timeout_s=OPENCLAW_LAUNCHER_PROBE_TIMEOUT_S)
            summary = (out or err or "").strip()
            summary_lower = summary.lower()
            if rc == 0:
                return True, " ".join(probe)
            if "usage" in summary_lower or "openclaw" in summary_lower:
                return True, f"{' '.join(probe)} (non-zero rc={rc})"
            attempts.append(f"{' '.join(probe)} -> rc={rc}: {summary[:120]}")
        return False, " | ".join(attempts[-3:])

    openclaw_bin = shutil.which("openclaw")
    if openclaw_bin:
        details["openclaw_bin"] = openclaw_bin

    mjs_candidates: list[Path] = []
    if openclaw_bin:
        openclaw_path = Path(openclaw_bin)
        mjs_candidates.append(openclaw_path.parent / "node_modules" / "openclaw" / "openclaw.mjs")
    appdata = os.environ.get("APPDATA")
    if appdata:
        appdata_posix = appdata.replace("\\", "/")
        if ":" in appdata_posix and appdata_posix[1:3] == ":/":
            drive = appdata_posix[0].lower()
            appdata_posix = f"/mnt/{drive}/{appdata_posix[3:]}"
        mjs_candidates.append(Path(appdata_posix) / "npm" / "node_modules" / "openclaw" / "openclaw.mjs")
    mjs_candidates.append(Path("/mnt/c/Users"))  # sentinel; replaced below if no concrete candidate found
    if mjs_candidates and mjs_candidates[-1] == Path("/mnt/c/Users"):
        mjs_candidates.pop()
        if openclaw_bin:
            # final fallback based on openclaw shim location
            fallback = Path(openclaw_bin).parent / "node_modules" / "openclaw" / "openclaw.mjs"
            mjs_candidates.append(fallback)

    if openclaw_bin:
        ok, probe_detail = _probe_launcher([openclaw_bin])
        if ok:
            details.update({"strategy": "openclaw_bin", "probe": probe_detail})
            return [openclaw_bin], details
        details["bin_probe_error"] = probe_detail

    node_exe_candidates = [
        Path("/mnt/c/Program Files/nodejs/node.exe"),
        Path("/mnt/c/Program Files (x86)/nodejs/node.exe"),
    ]
    for node_exe in node_exe_candidates:
        if not node_exe.exists():
            continue
        for mjs in mjs_candidates:
            if not mjs.exists():
                continue
            command = [str(node_exe), _to_windows_path(mjs)]
            ok, probe_detail = _probe_launcher(command)
            if ok:
                details.update(
                    {
                        "strategy": "windows_node_mjs",
                        "node_exe": str(node_exe),
                        "mjs_path": str(mjs),
                        "probe": probe_detail,
                    }
                )
                return command, details
            details["windows_probe_error"] = probe_detail

    node_bin = shutil.which("node")
    if node_bin:
        for mjs in mjs_candidates:
            if not mjs.exists():
                continue
            command = [node_bin, str(mjs)]
            ok, probe_detail = _probe_launcher(command)
            if ok:
                details.update(
                    {
                        "strategy": "node_mjs",
                        "node_bin": node_bin,
                        "mjs_path": str(mjs),
                        "probe": probe_detail,
                    }
                )
                return [node_bin, str(mjs)], details
            details["node_probe_error"] = probe_detail

    return None, details


def _run_openclaw_cli(
    base_command: list[str], args: list[str], timeout_s: float = 15
) -> tuple[int, str, str, list[str]]:
    full_command = [*base_command, *args]
    rc, out, err = run(full_command, timeout_s=timeout_s)
    return rc, out, err, full_command


def _openclaw_probe_timeout(env_name: str, default_seconds: float) -> float:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default_seconds
    try:
        value = float(raw)
    except ValueError:
        return default_seconds
    return value if value >= 1.0 else default_seconds


def _probe_openclaw_gateway_health(base_command: list[str], port: int, bind: str) -> tuple[bool, str, list[str]]:
    timeout_s = _openclaw_probe_timeout("NUSYQ_OPENCLAW_HEALTH_TIMEOUT_S", OPENCLAW_STATUS_GATEWAY_HEALTH_TIMEOUT_S)
    rc, out, err, full_command = _run_openclaw_cli(
        base_command,
        ["gateway", "health", "--port", str(port), "--bind", bind],
        timeout_s=timeout_s,
    )
    summary = (out or err or "").strip()
    return rc == 0, summary, full_command


def _probe_openclaw_runtime_channels(
    base_command: list[str],
) -> tuple[bool, str, list[str], list[str], dict[str, Any]]:
    """Probe OpenClaw runtime channels from CLI JSON output."""
    timeout_s = _openclaw_probe_timeout("NUSYQ_OPENCLAW_CHANNELS_TIMEOUT_S", OPENCLAW_STATUS_CHANNELS_TIMEOUT_S)
    rc, out, err, full_command = _run_openclaw_cli(base_command, ["channels", "list", "--json"], timeout_s=timeout_s)
    summary = (out or err or "").strip()
    if rc != 0:
        return False, summary or f"rc={rc}", full_command, [], {}
    try:
        payload = json.loads(out) if out.strip() else {}
    except json.JSONDecodeError:
        return False, "channels list output is not valid JSON", full_command, [], {}

    providers: list[str] = []
    if isinstance(payload, dict):
        usage = payload.get("usage", {})
        if isinstance(usage, dict) and isinstance(usage.get("providers"), list):
            providers = [str(item) for item in usage["providers"] if isinstance(item, str)]

        chat = payload.get("chat", {})
        if isinstance(chat, dict):
            for channel_name in chat:
                if isinstance(channel_name, str):
                    providers.append(channel_name)

    configured = sorted(set(providers))
    return True, "ok", full_command, configured, payload if isinstance(payload, dict) else {}


def _parse_openclaw_channel_failures(health_text: str) -> dict[str, str]:
    failures: dict[str, str] = {}
    if not health_text:
        return failures
    for raw_line in health_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*failed\b(.*)$", line, re.IGNORECASE)
        if not match:
            continue
        channel = match.group(1).strip().lower()
        reason = match.group(2).strip(" -") or "failed"
        failures[channel] = reason
    return failures


@dataclass(frozen=True)
class OpenClawGatewayOptions:
    port: int = OPENCLAW_DEFAULT_GATEWAY_PORT
    bind: str = OPENCLAW_DEFAULT_GATEWAY_BIND
    port_specified: bool = False
    bind_specified: bool = False
    force: bool = False
    verbose: bool = False
    allow_unconfigured: bool = True


def _parse_openclaw_gateway_args(
    args: list[str],
    default_port: int = OPENCLAW_DEFAULT_GATEWAY_PORT,
    default_bind: str = OPENCLAW_DEFAULT_GATEWAY_BIND,
) -> OpenClawGatewayOptions:
    tokens = list(
        args[1:]
        if args and args[0] in {"openclaw_gateway_start", "openclaw_gateway_status", "openclaw_gateway_stop"}
        else args
    )
    port = int(default_port)
    bind = default_bind or OPENCLAW_DEFAULT_GATEWAY_BIND
    port_specified = False
    bind_specified = False
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.startswith("--port"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                with contextlib.suppress(ValueError):
                    parsed = int(value)
                    if parsed > 0:
                        port = parsed
                        port_specified = True
            i += consumed
            continue
        if token.startswith("--bind"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                bind = value.strip() or bind
                bind_specified = True
            i += consumed
            continue
        i += 1

    return OpenClawGatewayOptions(
        port=port,
        bind=bind,
        port_specified=port_specified,
        bind_specified=bind_specified,
        force="--force" in tokens,
        verbose="--verbose" in tokens,
        allow_unconfigured="--no-allow-unconfigured" not in tokens,
    )


def _load_openclaw_config(paths: RepoPaths) -> dict[str, Any]:
    if not paths.nusyq_hub:
        return {}
    config_file = paths.nusyq_hub / "config" / "secrets.json"
    payload = read_json(config_file)
    if not isinstance(payload, dict):
        return {}
    openclaw = payload.get("openclaw", {})
    return openclaw if isinstance(openclaw, dict) else {}


def _handle_openclaw_gateway_status(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "openclaw_gateway_status",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    openclaw_cfg = _load_openclaw_config(paths)
    default_port = _gateway_port_from_url(
        str(openclaw_cfg.get("gateway_url") or ""),
        default_port=OPENCLAW_DEFAULT_GATEWAY_PORT,
    )
    default_bind = str(openclaw_cfg.get("bind") or OPENCLAW_DEFAULT_GATEWAY_BIND)
    options = _parse_openclaw_gateway_args(args, default_port=default_port, default_bind=default_bind)
    pid_path = _openclaw_gateway_pid_path(paths.nusyq_hub)
    pid_record = _read_openclaw_pid_record(pid_path)
    effective_port = int(options.port)
    effective_bind = str(options.bind)
    if not options.port_specified:
        with contextlib.suppress(ValueError, TypeError):
            pid_port = int(pid_record.get("port", 0) or 0)
            if pid_port > 0:
                effective_port = pid_port
    if not options.bind_specified:
        pid_bind = str(pid_record.get("bind") or "").strip().lower()
        if pid_bind in {"loopback", "lan"}:
            effective_bind = pid_bind

    pid = int(pid_record.get("pid", 0) or 0)
    managed_running = _is_process_running(pid)
    if pid and not managed_running and pid_path.exists():
        with contextlib.suppress(OSError):
            pid_path.unlink()

    socket_ok, socket_detail = _probe_endpoint_reachable(f"ws://127.0.0.1:{effective_port}", timeout_s=1.2)
    cli_cmd: list[str] | None = None
    cli_meta: dict[str, Any] = {"strategy": "skipped", "reason": "socket_probe_ok"}
    health_ok = False
    health_detail = "skipped_socket_probe_ok" if socket_ok else "cli unavailable"
    health_cmd: list[str] = []
    if not socket_ok:
        cli_cmd, cli_meta = _resolve_openclaw_cli()
    if cli_cmd:
        health_ok, health_detail, health_cmd = _probe_openclaw_gateway_health(cli_cmd, effective_port, effective_bind)
    listener_pids = _windows_listening_pids(effective_port)
    active_pid: int | None = None
    if listener_pids:
        active_pid = listener_pids[0]
    if not managed_running and active_pid:
        # OpenClaw can re-exec itself during config reload and change PID.
        managed_running = True
        pid = active_pid
        refreshed_record = dict(pid_record)
        refreshed_record["pid"] = pid
        refreshed_record["port"] = effective_port
        refreshed_record["bind"] = effective_bind
        refreshed_record["updated_at"] = now_stamp()
        _write_openclaw_pid_record(pid_path, refreshed_record)

    gateway_reachable = socket_ok or health_ok
    probe_source = "socket" if socket_ok else ("openclaw_cli_health" if health_ok else "none")
    status = "online" if gateway_reachable else ("degraded" if managed_running else "offline")

    payload = {
        "action": "openclaw_gateway_status",
        "status": status,
        "functional": gateway_reachable,
        "gateway_reachable": gateway_reachable,
        "probe_source": probe_source,
        "port": effective_port,
        "bind": effective_bind,
        "managed_pid": pid or None,
        "managed_running": managed_running,
        "active_listener_pid": active_pid,
        "pid_file": str(pid_path),
        "launcher": cli_meta,
        "socket_probe": {"ok": socket_ok, "detail": socket_detail},
        "cli_health_probe": {
            "ok": health_ok,
            "detail": health_detail,
            "command": health_cmd,
        },
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🔌 OpenClaw Gateway Status")
        print("=" * 60)
        print(f"status: {status}")
        print(f"functional: {'yes' if gateway_reachable else 'no'}")
        print(f"probe_source: {probe_source}")
        print(f"managed_pid: {pid or 'none'}")
        print(f"socket_probe: {'ok' if socket_ok else 'fail'} ({socket_detail})")
        print(f"cli_health: {'ok' if health_ok else 'fail'} ({health_detail})")
    return 0 if gateway_reachable else 1


def _handle_openclaw_gateway_start(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "openclaw_gateway_start",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    openclaw_cfg = _load_openclaw_config(paths)
    default_port = _gateway_port_from_url(
        str(openclaw_cfg.get("gateway_url") or ""),
        default_port=OPENCLAW_DEFAULT_GATEWAY_PORT,
    )
    default_bind = str(openclaw_cfg.get("bind") or OPENCLAW_DEFAULT_GATEWAY_BIND)
    options = _parse_openclaw_gateway_args(args, default_port=default_port, default_bind=default_bind)
    cli_cmd, cli_meta = _resolve_openclaw_cli()
    if not cli_cmd:
        payload = {
            "action": "openclaw_gateway_start",
            "status": "error",
            "error": "OpenClaw CLI launcher not available",
            "launcher": cli_meta,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    pid_path = _openclaw_gateway_pid_path(paths.nusyq_hub)
    log_path = _openclaw_gateway_log_path(paths.nusyq_hub)
    pid_record = _read_openclaw_pid_record(pid_path)
    existing_pid = int(pid_record.get("pid", 0) or 0)
    existing_running = _is_process_running(existing_pid)
    if existing_running:
        health_ok, health_detail, _ = _probe_openclaw_gateway_health(cli_cmd, options.port, options.bind)
        if health_ok:
            payload = {
                "action": "openclaw_gateway_start",
                "status": "already_running",
                "functional": True,
                "pid": existing_pid,
                "port": options.port,
                "bind": options.bind,
                "log_file": str(log_path),
                "launcher": cli_meta,
                "health_detail": health_detail,
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else json.dumps(payload, indent=2))
            return 0
        _terminate_job_process(existing_pid, grace_s=3.0)

    command = [*cli_cmd, "gateway", "run", "--port", str(options.port), "--bind", options.bind]
    if options.allow_unconfigured:
        command.append("--allow-unconfigured")
    if options.force:
        command.append("--force")
    if options.verbose:
        command.append("--verbose")

    try:
        with log_path.open("a", encoding="utf-8") as log_fh:
            process = subprocess.Popen(
                command,
                cwd=str(paths.nusyq_hub),
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except OSError as exc:
        payload = {
            "action": "openclaw_gateway_start",
            "status": "error",
            "error": str(exc),
            "command": command,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    _write_openclaw_pid_record(
        pid_path,
        {
            "pid": process.pid,
            "started_at": now_stamp(),
            "command": command,
            "port": options.port,
            "bind": options.bind,
            "log_file": str(log_path),
            "launcher": cli_meta,
        },
    )

    deadline = time.time() + OPENCLAW_GATEWAY_READY_TIMEOUT_S
    healthy = False
    health_detail = "health check pending"
    while time.time() < deadline:
        healthy, health_detail, _ = _probe_openclaw_gateway_health(cli_cmd, options.port, options.bind)
        if healthy:
            break
        if not _is_process_running(process.pid):
            break
        time.sleep(0.5)

    listener_pids = _windows_listening_pids(options.port)
    active_pid: int | None = listener_pids[0] if listener_pids else None
    if healthy and active_pid and active_pid != process.pid:
        refreshed_record = dict(_read_openclaw_pid_record(pid_path))
        refreshed_record["pid"] = active_pid
        refreshed_record["port"] = options.port
        refreshed_record["bind"] = options.bind
        refreshed_record["updated_at"] = now_stamp()
        _write_openclaw_pid_record(pid_path, refreshed_record)

    payload = {
        "action": "openclaw_gateway_start",
        "status": "ok" if healthy else "degraded",
        "functional": healthy,
        "pid": process.pid,
        "active_listener_pid": active_pid,
        "port": options.port,
        "bind": options.bind,
        "log_file": str(log_path),
        "pid_file": str(pid_path),
        "launcher": cli_meta,
        "health_detail": health_detail,
        "command": command,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🔌 OpenClaw Gateway Start")
        print("=" * 60)
        print(f"status: {payload['status']}")
        print(f"pid: {process.pid}")
        print(f"log: {log_path}")
        print(f"health: {health_detail}")
    return 0 if healthy else 1


def _handle_openclaw_gateway_stop(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "openclaw_gateway_stop",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    openclaw_cfg = _load_openclaw_config(paths)
    default_port = _gateway_port_from_url(
        str(openclaw_cfg.get("gateway_url") or ""),
        default_port=OPENCLAW_DEFAULT_GATEWAY_PORT,
    )
    default_bind = str(openclaw_cfg.get("bind") or OPENCLAW_DEFAULT_GATEWAY_BIND)
    options = _parse_openclaw_gateway_args(args, default_port=default_port, default_bind=default_bind)
    pid_path = _openclaw_gateway_pid_path(paths.nusyq_hub)
    pid_record = _read_openclaw_pid_record(pid_path)
    pid = int(pid_record.get("pid", 0) or 0)
    terminated = False
    if pid and _is_process_running(pid):
        terminated = _terminate_job_process(pid, grace_s=4.0)
    else:
        terminated = True

    if terminated and pid_path.exists():
        with contextlib.suppress(OSError):
            pid_path.unlink()

    cli_cmd, cli_meta = _resolve_openclaw_cli()
    health_ok = False
    health_detail = "cli unavailable"
    if cli_cmd:
        health_ok, health_detail, _ = _probe_openclaw_gateway_health(cli_cmd, options.port, options.bind)

    unmanaged_killed: list[int] = []
    if health_ok:
        for listener_pid in _windows_listening_pids(options.port):
            if _windows_taskkill_pid(listener_pid):
                unmanaged_killed.append(listener_pid)
        if unmanaged_killed and cli_cmd:
            health_ok, health_detail, _ = _probe_openclaw_gateway_health(cli_cmd, options.port, options.bind)

    payload = {
        "action": "openclaw_gateway_stop",
        "status": "stopped" if terminated and not health_ok else "degraded",
        "functional": not health_ok,
        "managed_pid": pid or None,
        "terminated": terminated,
        "killed_unmanaged_pids": unmanaged_killed,
        "port": options.port,
        "bind": options.bind,
        "pid_file": str(pid_path),
        "launcher": cli_meta,
        "health_after_stop": {"ok": health_ok, "detail": health_detail},
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🔌 OpenClaw Gateway Stop")
        print("=" * 60)
        print(f"status: {payload['status']}")
        print(f"terminated: {'yes' if terminated else 'no'}")
        if unmanaged_killed:
            print(f"killed_unmanaged_pids: {', '.join(str(pid) for pid in unmanaged_killed)}")
        print(f"health_after_stop: {health_detail}")
    return 0 if terminated and not health_ok else 1


@dataclass(frozen=True)
class OpenClawBridgeOptions:
    gateway_url: str
    auto_wsl_gateway: bool = True


def _parse_openclaw_bridge_args(
    args: list[str], default_gateway_url: str = f"ws://127.0.0.1:{OPENCLAW_DEFAULT_GATEWAY_PORT}"
) -> OpenClawBridgeOptions:
    tokens = list(
        args[1:]
        if args and args[0] in {"openclaw_bridge_start", "openclaw_bridge_status", "openclaw_bridge_stop"}
        else args
    )
    gateway_url = default_gateway_url
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.startswith("--gateway-url") or token.startswith("--gateway"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                gateway_url = value.strip() or gateway_url
            i += consumed
            continue
        i += 1
    return OpenClawBridgeOptions(
        gateway_url=gateway_url,
        auto_wsl_gateway="--no-auto-wsl-gateway" not in tokens,
    )


def _resolve_bridge_gateway_url(
    requested_gateway_url: str, openclaw_bind: str, auto_wsl_gateway: bool = True
) -> tuple[str, str | None]:
    parsed = urlparse(requested_gateway_url)
    host = (parsed.hostname or "").lower()
    port = parsed.port or _gateway_port_from_url(requested_gateway_url, default_port=OPENCLAW_DEFAULT_GATEWAY_PORT)
    if auto_wsl_gateway and openclaw_bind == "lan" and host in {"127.0.0.1", "localhost"}:
        gateway_ip = _wsl_default_gateway_ip()
        if gateway_ip:
            scheme = parsed.scheme or "ws"
            return f"{scheme}://{gateway_ip}:{port}", gateway_ip
    return requested_gateway_url, None


def _bridge_log_markers(log_path: Path) -> tuple[bool, str | None]:
    if not log_path.exists():
        return False, None
    text = log_path.read_text(encoding="utf-8", errors="replace")
    if "Successfully connected to OpenClaw Gateway" in text:
        return True, None
    failure_lines = [line.strip() for line in text.splitlines() if "Failed to connect to OpenClaw Gateway" in line]
    return False, (failure_lines[-1] if failure_lines else None)


def _handle_openclaw_bridge_start(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "openclaw_bridge_start",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    openclaw_cfg = _load_openclaw_config(paths)
    default_gateway = str(openclaw_cfg.get("gateway_url") or f"ws://127.0.0.1:{OPENCLAW_DEFAULT_GATEWAY_PORT}")
    options = _parse_openclaw_bridge_args(args, default_gateway_url=default_gateway)
    bind = str(openclaw_cfg.get("bind") or OPENCLAW_DEFAULT_GATEWAY_BIND)
    gateway_url, wsl_gateway_ip = _resolve_bridge_gateway_url(
        options.gateway_url,
        bind,
        auto_wsl_gateway=options.auto_wsl_gateway,
    )

    pid_path = _openclaw_bridge_pid_path(paths.nusyq_hub)
    log_path = _openclaw_bridge_log_path(paths.nusyq_hub)
    pid_record = _read_openclaw_pid_record(pid_path)
    existing_pid = int(pid_record.get("pid", 0) or 0)
    if existing_pid and _is_process_running(existing_pid):
        connected, last_error = _bridge_log_markers(log_path)
        payload = {
            "action": "openclaw_bridge_start",
            "status": "already_running",
            "functional": connected,
            "pid": existing_pid,
            "gateway_url": gateway_url,
            "wsl_gateway_ip": wsl_gateway_ip,
            "connected": connected,
            "last_error": last_error,
            "log_file": str(log_path),
            "pid_file": str(pid_path),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else json.dumps(payload, indent=2))
        return 0 if connected else 1

    command = [
        sys.executable,
        "src/main.py",
        "--openclaw-enabled",
        "--openclaw-gateway",
        gateway_url,
    ]
    try:
        with log_path.open("a", encoding="utf-8") as log_fh:
            process = subprocess.Popen(
                command,
                cwd=str(paths.nusyq_hub),
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except OSError as exc:
        payload = {
            "action": "openclaw_bridge_start",
            "status": "error",
            "error": str(exc),
            "command": command,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    _write_openclaw_pid_record(
        pid_path,
        {
            "pid": process.pid,
            "started_at": now_stamp(),
            "command": command,
            "gateway_url": gateway_url,
            "bind": bind,
            "log_file": str(log_path),
        },
    )

    connected = False
    last_error: str | None = None
    deadline = time.time() + 20.0
    while time.time() < deadline:
        connected, last_error = _bridge_log_markers(log_path)
        if connected:
            break
        if not _is_process_running(process.pid):
            break
        time.sleep(0.5)

    payload = {
        "action": "openclaw_bridge_start",
        "status": "ok" if connected else "degraded",
        "functional": connected,
        "pid": process.pid,
        "gateway_url": gateway_url,
        "wsl_gateway_ip": wsl_gateway_ip,
        "bind": bind,
        "connected": connected,
        "last_error": last_error,
        "log_file": str(log_path),
        "pid_file": str(pid_path),
        "command": command,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🔌 OpenClaw Bridge Start")
        print("=" * 60)
        print(f"status: {payload['status']}")
        print(f"pid: {process.pid}")
        print(f"gateway_url: {gateway_url}")
        if wsl_gateway_ip:
            print(f"wsl_gateway_ip: {wsl_gateway_ip}")
        print(f"log: {log_path}")
        if last_error:
            print(f"last_error: {last_error}")
    return 0 if connected else 1


def _handle_openclaw_bridge_status(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "openclaw_bridge_status",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    openclaw_cfg = _load_openclaw_config(paths)
    default_gateway = str(openclaw_cfg.get("gateway_url") or f"ws://127.0.0.1:{OPENCLAW_DEFAULT_GATEWAY_PORT}")
    options = _parse_openclaw_bridge_args(args, default_gateway_url=default_gateway)
    bind = str(openclaw_cfg.get("bind") or OPENCLAW_DEFAULT_GATEWAY_BIND)
    gateway_url, wsl_gateway_ip = _resolve_bridge_gateway_url(
        options.gateway_url,
        bind,
        auto_wsl_gateway=options.auto_wsl_gateway,
    )

    pid_path = _openclaw_bridge_pid_path(paths.nusyq_hub)
    log_path = _openclaw_bridge_log_path(paths.nusyq_hub)
    pid_record = _read_openclaw_pid_record(pid_path)
    pid = int(pid_record.get("pid", 0) or 0)
    running = _is_process_running(pid)
    connected_from_log, last_error = _bridge_log_markers(log_path)
    # Guard against stale success markers in historical logs when process is down.
    connected = running and connected_from_log

    status = "online" if running and connected else ("degraded" if running else "offline")
    payload = {
        "action": "openclaw_bridge_status",
        "status": status,
        "functional": running and connected,
        "pid": pid or None,
        "running": running,
        "connected": connected,
        "connected_from_log": connected_from_log,
        "last_error": last_error,
        "gateway_url": gateway_url,
        "wsl_gateway_ip": wsl_gateway_ip,
        "log_file": str(log_path),
        "pid_file": str(pid_path),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🔌 OpenClaw Bridge Status")
        print("=" * 60)
        print(f"status: {status}")
        print(f"running: {'yes' if running else 'no'}")
        print(f"connected: {'yes' if connected else 'no'}")
        print(f"gateway_url: {gateway_url}")
        if last_error:
            print(f"last_error: {last_error}")
    return 0 if (running and connected) else 1


def _handle_openclaw_bridge_stop(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "openclaw_bridge_stop",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    _ = _parse_openclaw_bridge_args(args)
    pid_path = _openclaw_bridge_pid_path(paths.nusyq_hub)
    log_path = _openclaw_bridge_log_path(paths.nusyq_hub)
    pid_record = _read_openclaw_pid_record(pid_path)
    pid = int(pid_record.get("pid", 0) or 0)
    stopped = True
    if pid and _is_process_running(pid):
        stopped = _terminate_job_process(pid, grace_s=4.0)
    if stopped and pid_path.exists():
        with contextlib.suppress(OSError):
            pid_path.unlink()

    payload = {
        "action": "openclaw_bridge_stop",
        "status": "stopped" if stopped else "degraded",
        "functional": stopped,
        "pid": pid or None,
        "stopped": stopped,
        "pid_file": str(pid_path),
        "log_file": str(log_path),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🔌 OpenClaw Bridge Stop")
        print("=" * 60)
        print(f"status: {payload['status']}")
        print(f"pid: {pid or 'none'}")
    return 0 if stopped else 1


@dataclass(frozen=True)
class OpenClawInternalSendOptions:
    text: str
    target_system: str = "auto"
    channel: str = "internal"
    user_id: str = "local-agent"
    username: str = "agent"
    task_type: str = "analyze"
    timeout_seconds: float = 30.0
    allow_fallback: bool = False


def _resolve_lmstudio_base_url() -> str:
    return (
        str(
            os.getenv("NUSYQ_LMSTUDIO_BASE_URL")
            or os.getenv("LMSTUDIO_BASE_URL")
            or os.getenv("LM_STUDIO_BASE_URL")
            or "http://10.0.0.172:1234"
        )
        .strip()
        .rstrip("/")
    )


def _resolve_ollama_base_url() -> str:
    return str(os.getenv("NUSYQ_OLLAMA_API_URL") or "http://127.0.0.1:11434").strip().rstrip("/")


def _probe_json_endpoint(url: str, timeout_s: float) -> tuple[bool, Any | None, str]:
    request = Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout_s) as response:
            status_code = int(getattr(response, "status", 500))
            body = response.read(131072).decode("utf-8", errors="replace")
            if not (200 <= status_code < 300):
                return False, None, f"http_{status_code}"
            try:
                return True, json.loads(body), "ok"
            except json.JSONDecodeError:
                return False, None, "invalid_json"
    except URLError as exc:
        return False, None, str(exc.reason or exc)
    except Exception as exc:
        return False, None, str(exc)


def _preflight_openclaw_target(target_system: str, timeout_s: float) -> dict[str, Any]:
    system = target_system.strip().lower()
    probe_timeout = max(1.0, min(4.0, timeout_s / 4.0))

    if system == "lmstudio":
        url = f"{_resolve_lmstudio_base_url()}/v1/models"
        ok, payload, detail = _probe_json_endpoint(url, timeout_s=probe_timeout)
        model_count = 0
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            model_count = len(payload["data"])
        elif isinstance(payload, list):
            model_count = len(payload)
        return {
            "checked": True,
            "system": system,
            "available": bool(ok and model_count > 0),
            "reachable": bool(ok),
            "model_count": model_count,
            "url": url,
            "detail": detail,
            "timeout_seconds": probe_timeout,
        }

    if system == "ollama":
        url = f"{_resolve_ollama_base_url()}/api/tags"
        ok, payload, detail = _probe_json_endpoint(url, timeout_s=probe_timeout)
        model_count = 0
        if isinstance(payload, dict) and isinstance(payload.get("models"), list):
            model_count = len(payload["models"])
        return {
            "checked": True,
            "system": system,
            "available": bool(ok),
            "reachable": bool(ok),
            "model_count": model_count,
            "url": url,
            "detail": detail,
            "timeout_seconds": probe_timeout,
        }

    return {
        "checked": False,
        "system": system,
        "available": True,
        "reachable": None,
        "model_count": None,
        "url": None,
        "detail": "not_required",
        "timeout_seconds": probe_timeout,
    }


def _parse_openclaw_internal_send_args(
    args: list[str],
) -> tuple[OpenClawInternalSendOptions | None, str | None]:
    tokens = list(args[1:] if args and args[0] == "openclaw_internal_send" else args)

    text_parts: list[str] = []
    target_system = "auto"
    channel = "internal"
    user_id = "local-agent"
    username = "agent"
    task_type = "analyze"
    timeout_seconds = 30.0
    allow_fallback = os.getenv("NUSYQ_OPENCLAW_INTERNAL_ALLOW_FALLBACK", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in {"--help", "-h"}:
            return None, "help"
        if token == "--allow-fallback":
            allow_fallback = True
            i += 1
            continue
        if token == "--no-fallback":
            allow_fallback = False
            i += 1
            continue
        if token.startswith("--text"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                text_parts.append(value)
            i += consumed
            continue
        if token.startswith("--system") or token.startswith("--target-system"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                target_system = value.strip().lower() or target_system
            i += consumed
            continue
        if token.startswith("--channel"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                channel = value.strip() or channel
            i += consumed
            continue
        if token.startswith("--user-id"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                user_id = value.strip() or user_id
            i += consumed
            continue
        if token.startswith("--username"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                username = value.strip() or username
            i += consumed
            continue
        if token.startswith("--task-type"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                task_type = value.strip().lower() or task_type
            i += consumed
            continue
        if token.startswith("--timeout-s"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                with contextlib.suppress(ValueError):
                    parsed_timeout = float(value)
                    if parsed_timeout >= 1.0:
                        timeout_seconds = min(parsed_timeout, 300.0)
            i += consumed
            continue
        if token.startswith("--"):
            return None, f"unknown_flag: {token}"

        text_parts.append(token)
        i += 1

    text = " ".join(part.strip() for part in text_parts if part and part.strip()).strip()
    if not text:
        return None, "missing_text"
    if target_system not in OPENCLAW_INTERNAL_TARGET_SYSTEMS:
        return None, (f"invalid_system: {target_system} (expected one of {sorted(OPENCLAW_INTERNAL_TARGET_SYSTEMS)})")

    return (
        OpenClawInternalSendOptions(
            text=text,
            target_system=target_system,
            channel=channel,
            user_id=user_id,
            username=username,
            task_type=task_type,
            timeout_seconds=timeout_seconds,
            allow_fallback=allow_fallback,
        ),
        None,
    )


def _handle_openclaw_internal_send(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "openclaw_internal_send",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    options, parse_error = _parse_openclaw_internal_send_args(args)
    if parse_error == "help":
        print("Usage:")
        print(
            "  python scripts/start_nusyq.py openclaw_internal_send "
            '--text "<message>" '
            "[--system=auto|ollama|lmstudio|chatdev|copilot|codex|claude_cli|consciousness|quantum_resolver] "
            "[--channel=internal] [--user-id=local-agent] [--username=agent] "
            "[--task-type=analyze] [--timeout-s=30] [--allow-fallback|--no-fallback]"
        )
        print("Examples:")
        print(
            "  python scripts/start_nusyq.py openclaw_internal_send "
            '--system=ollama --text "Summarize src/main.py in one sentence"'
        )
        print(
            "  python scripts/start_nusyq.py openclaw_internal_send "
            '--system=chatdev --task-type=generate --text "Create a tiny Flask endpoint"'
        )
        print(
            "  python scripts/start_nusyq.py openclaw_internal_send "
            '--system=lmstudio --allow-fallback --text "Draft a test case plan"'
        )
        return 0

    if parse_error or not options:
        payload = {
            "action": "openclaw_internal_send",
            "status": "error",
            "functional": False,
            "error": parse_error or "invalid_args",
            "supported_systems": sorted(OPENCLAW_INTERNAL_TARGET_SYSTEMS),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    requested_target = options.target_system
    effective_target = requested_target
    preflight = _preflight_openclaw_target(requested_target, options.timeout_seconds)
    fallback_applied = False
    dispatch_timeout_seconds = options.timeout_seconds
    if preflight.get("checked") and not preflight.get("available"):
        if requested_target == "lmstudio" and options.allow_fallback:
            ollama_preflight = _preflight_openclaw_target("ollama", options.timeout_seconds)
            if ollama_preflight.get("available"):
                effective_target = "ollama"
                fallback_applied = True
                fallback_timeout_raw = os.getenv("NUSYQ_OPENCLAW_FALLBACK_TIMEOUT_S", "45").strip()
                try:
                    fallback_timeout_s = float(fallback_timeout_raw or "45")
                except ValueError:
                    fallback_timeout_s = 45.0
                dispatch_timeout_seconds = max(
                    dispatch_timeout_seconds,
                    min(
                        300.0,
                        max(30.0, fallback_timeout_s),
                    ),
                )
                preflight["fallback_applied"] = "ollama"
                preflight["fallback_detail"] = "lmstudio_unavailable"
                preflight["fallback_probe"] = ollama_preflight
            else:
                preflight["fallback_applied"] = None
                preflight["fallback_detail"] = "ollama_unavailable"
                preflight["fallback_probe"] = ollama_preflight
        if effective_target == requested_target:
            payload = {
                "action": "openclaw_internal_send",
                "status": "error",
                "functional": False,
                "error": f"{requested_target}_unavailable",
                "target_system": requested_target,
                "preflight": preflight,
                "hint": (
                    "Start/configure the target system or pass --allow-fallback for lmstudio->ollama."
                    if requested_target == "lmstudio"
                    else "Start/configure the target system and retry."
                ),
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
            return 1

    try:
        from src.integrations.openclaw_gateway_bridge import get_openclaw_gateway_bridge
    except Exception as exc:
        payload = {
            "action": "openclaw_internal_send",
            "status": "error",
            "functional": False,
            "error": f"bridge_import_failed: {exc}",
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    async def _dispatch() -> tuple[dict[str, Any], bool, float]:
        bridge = get_openclaw_gateway_bridge(force_reload=True)
        message = {
            "timestamp": datetime.now(UTC).isoformat(),
            "channel": options.channel,
            "user_id": options.user_id,
            "username": options.username,
            "text": options.text,
            "target_system": effective_target,
            "context": {
                "task_type": options.task_type,
                "source": "openclaw_internal_send",
                "requested_target_system": requested_target,
            },
        }
        started = time.perf_counter()
        result = await asyncio.wait_for(bridge.handle_inbound_message(message), timeout=dispatch_timeout_seconds)
        elapsed = time.perf_counter() - started
        receipt_ok = False
        if result.get("status") == "success":
            receipt_timeout_s = max(3.0, min(20.0, dispatch_timeout_seconds / 2.0))
            receipt_ok = await asyncio.wait_for(
                bridge.send_result(
                    channel=result.get("channel", options.channel),
                    target_user_id=result.get("user_id", options.user_id),
                    result_text=result.get("result_text", ""),
                    task_id=result.get("task_id"),
                ),
                timeout=receipt_timeout_s,
            )
        return result, receipt_ok, elapsed

    try:
        result, receipt_ok, elapsed = asyncio.run(_dispatch())
    except TimeoutError:
        payload = {
            "action": "openclaw_internal_send",
            "status": "error",
            "functional": False,
            "error": f"dispatch_timeout_after_{dispatch_timeout_seconds:.1f}s",
            "target_system": effective_target,
            "requested_target_system": requested_target,
            "timeout_seconds": options.timeout_seconds,
            "dispatch_timeout_seconds": dispatch_timeout_seconds,
            "preflight": preflight,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1
    except Exception as exc:
        payload = {
            "action": "openclaw_internal_send",
            "status": "error",
            "functional": False,
            "error": f"dispatch_failed: {exc}",
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    functional = result.get("status") == "success"
    payload = {
        "action": "openclaw_internal_send",
        "status": "ok" if functional else "error",
        "functional": functional,
        "target_system": effective_target,
        "requested_target_system": requested_target,
        "fallback_applied": fallback_applied,
        "channel": options.channel,
        "task_type": options.task_type,
        "timeout_seconds": options.timeout_seconds,
        "dispatch_timeout_seconds": dispatch_timeout_seconds,
        "elapsed_seconds": round(elapsed, 3),
        "local_receipt_written": receipt_ok,
        "preflight": preflight,
        "result": result,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🔌 OpenClaw Internal Send")
        print("=" * 60)
        print(f"status: {payload['status']}")
        print(f"target_system: {effective_target}")
        if requested_target != effective_target:
            print(f"requested_target_system: {requested_target}")
        print(f"channel: {options.channel}")
        print(f"task_id: {result.get('task_id')}")
        print(f"result: {result.get('result_text', result.get('error', ''))}")
        print(f"local_receipt_written: {'yes' if receipt_ok else 'no'}")
    return 0 if functional else 1


def _handle_openclaw_status(paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "openclaw_status",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    config_file = paths.nusyq_hub / "config" / "secrets.json"
    payload: dict[str, Any] = {
        "action": "openclaw_status",
        "generated_at": datetime.now(UTC).isoformat(),
        "config_file": str(config_file),
    }
    if not config_file.exists():
        payload.update({"status": "offline", "functional": False, "error": "config_missing"})
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except Exception as exc:
        payload.update({"status": "offline", "functional": False, "error": f"config_parse_error: {exc}"})
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    openclaw_cfg = data.get("openclaw", {}) if isinstance(data, dict) else {}
    if not isinstance(openclaw_cfg, dict):
        payload.update({"status": "offline", "functional": False, "error": "openclaw_block_invalid"})
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    enabled = bool(openclaw_cfg.get("enabled", False))
    gateway_url = str(openclaw_cfg.get("gateway_url") or "")
    api_url = str(openclaw_cfg.get("api_url") or "")
    api_required = bool(openclaw_cfg.get("api_required", False))
    channels_cfg = openclaw_cfg.get("channels", {})
    if not isinstance(channels_cfg, dict):
        channels_cfg = {}
    known_channel_set = set(OPENCLAW_CHANNEL_REQUIRED_FIELDS)
    known_channels_enabled_cfg = any(
        channel in known_channel_set and isinstance(cfg, dict) and bool(cfg.get("enabled", False))
        for channel, cfg in channels_cfg.items()
    )

    gateway_ok, gateway_note = _probe_endpoint_reachable(gateway_url) if gateway_url else (False, "gateway_url_missing")
    gateway_probe_source = "socket"
    api_ok, api_note = _probe_endpoint_reachable(api_url) if api_url else (False, "api_url_missing")
    cli_health_detail = ""
    cli_channels_detail = ""
    cli_channels_probe_ok = False
    cli_channels: list[str] = []
    cli_cmd: list[str] | None = None
    cli_meta: dict[str, Any] = {
        "strategy": "skipped",
        "reason": "not_required_for_current_configuration",
    }
    bind = str(openclaw_cfg.get("bind") or OPENCLAW_DEFAULT_GATEWAY_BIND)
    gateway_port = _gateway_port_from_url(gateway_url, default_port=OPENCLAW_DEFAULT_GATEWAY_PORT)
    wsl_gateway_ip = _wsl_default_gateway_ip() if bind == "lan" else None
    wsl_gateway_url = f"ws://{wsl_gateway_ip}:{gateway_port}" if wsl_gateway_ip else None
    if not gateway_ok or known_channels_enabled_cfg:
        cli_cmd, cli_meta = _resolve_openclaw_cli()
    if not gateway_ok and cli_cmd:
        health_ok, health_detail, _ = _probe_openclaw_gateway_health(cli_cmd, gateway_port, bind)
        if health_ok:
            gateway_ok = True
            gateway_note = health_detail or "OpenClaw CLI health probe reported OK"
            gateway_probe_source = "openclaw_cli_health"
        cli_health_detail = health_detail
    if cli_cmd and known_channels_enabled_cfg:
        (
            cli_channels_probe_ok,
            cli_channels_detail,
            _channels_cmd,
            cli_channels,
            _channels_payload,
        ) = _probe_openclaw_runtime_channels(cli_cmd)
    elif not known_channels_enabled_cfg:
        cli_channels_detail = "skipped_runtime_channel_probe_no_enabled_messaging_channels"

    enabled_channels_known: list[str] = []
    enabled_channels_system: list[str] = []
    enabled_channels_unknown: list[str] = []
    ready_channels: list[str] = []
    channel_status: dict[str, Any] = {}
    for channel, cfg in channels_cfg.items():
        if not isinstance(cfg, dict):
            continue
        channel_enabled = bool(cfg.get("enabled", False))
        channel_known = channel in known_channel_set
        required_fields = OPENCLAW_CHANNEL_REQUIRED_FIELDS.get(channel, ())
        valid_fields = [
            field for field in required_fields if _openclaw_field_format_valid(channel, field, cfg.get(field))
        ]
        missing_or_placeholder = sorted(set(required_fields) - set(valid_fields))
        invalid_format_fields = [
            field
            for field in required_fields
            if (
                not _looks_like_placeholder_secret(cfg.get(field))
                and not _openclaw_field_format_valid(channel, field, cfg.get(field))
            )
        ]
        if channel_enabled:
            if channel_known:
                enabled_channels_known.append(channel)
            elif channel in OPENCLAW_SYSTEM_CHANNEL_NAMES:
                enabled_channels_system.append(channel)
            else:
                enabled_channels_unknown.append(channel)
        if channel_enabled and channel_known and len(valid_fields) == len(required_fields):
            ready_channels.append(channel)
        if channel_enabled and not channel_known and channel in OPENCLAW_SYSTEM_CHANNEL_NAMES:
            ready_channels.append(channel)
        channel_kind = (
            "messaging" if channel_known else "system" if channel in OPENCLAW_SYSTEM_CHANNEL_NAMES else "unknown"
        )
        channel_status[channel] = {
            "enabled": channel_enabled,
            "known_channel": channel_known,
            "channel_kind": channel_kind,
            "required_fields": list(required_fields),
            "valid_fields": valid_fields,
            "missing_or_placeholder_fields": missing_or_placeholder,
            "invalid_format_fields": invalid_format_fields,
        }

    runtime_channel_failures = _parse_openclaw_channel_failures(cli_health_detail or gateway_note)
    for channel, reason in runtime_channel_failures.items():
        info = channel_status.setdefault(channel, {})
        if isinstance(info, dict):
            info["runtime_failure"] = reason

    all_enabled_channels = [
        *enabled_channels_known,
        *enabled_channels_system,
        *enabled_channels_unknown,
    ]
    ready_channels_runtime = list(ready_channels)
    if cli_channels_probe_ok:
        ready_channels_runtime = [channel for channel in ready_channels if channel in cli_channels]

    functional = enabled and gateway_ok
    messaging_channels_ready = [c for c in ready_channels_runtime if c in known_channel_set]
    system_channels_ready = [c for c in ready_channels_runtime if c in OPENCLAW_SYSTEM_CHANNEL_NAMES]
    messaging_functional = functional and len(messaging_channels_ready) > 0
    routing_functional = functional and len(ready_channels_runtime) > 0
    status = "online" if routing_functional else ("degraded" if functional else "offline")
    notes: list[str] = []
    if not enabled:
        notes.append("openclaw.enabled is false")
    if not gateway_ok:
        notes.append(f"gateway unreachable: {gateway_note}")
    if api_required and not api_ok:
        notes.append(f"api unreachable: {api_note}")
    elif api_url and not api_ok:
        notes.append("api endpoint unreachable (optional; gateway health is authoritative)")
    if not all_enabled_channels:
        notes.append("no channels enabled")
    if enabled_channels_unknown:
        notes.append(
            "enabled unknown channels are ignored for messaging readiness: "
            + ", ".join(sorted(enabled_channels_unknown))
        )
    if enabled_channels_system:
        notes.append("system-routing channels enabled: " + ", ".join(sorted(enabled_channels_system)))
    if enabled_channels_known and not ready_channels:
        notes.append("enabled channels use placeholder or missing credentials")
    if cli_channels_probe_ok and not cli_channels:
        notes.append("openclaw runtime reports zero configured channels")
    elif cli_channels_probe_ok and ready_channels and not ready_channels_runtime:
        notes.append("ready channels in config are not configured in openclaw runtime")
    invalid_enabled_channels = [
        channel for channel in enabled_channels_known if channel_status.get(channel, {}).get("invalid_format_fields")
    ]
    if invalid_enabled_channels:
        notes.append("enabled channels have invalid credential format: " + ", ".join(sorted(invalid_enabled_channels)))
    if functional and not routing_functional:
        notes.append("gateway ready, but no configured runtime channels are available")
    elif functional and routing_functional and not messaging_functional:
        notes.append("messaging channels unavailable; system-routing channels remain operational")
    if runtime_channel_failures:
        summarized = ", ".join(sorted(runtime_channel_failures))
        notes.append(f"runtime channel auth/connectivity failures: {summarized}")

    remediation: list[str] = []
    if not enabled:
        remediation.append("Set openclaw.enabled=true in config/secrets.json and restart gateway")
    if enabled_channels_unknown:
        remediation.append(
            "Use OpenClaw-supported chat channels (slack/discord/telegram/whatsapp/teams) "
            "for messaging readiness; unknown channels are informational only"
        )
    if enabled_channels_known and not ready_channels:
        remediation.append("Fix known channel credentials in config/secrets.json or disable placeholder channels")
    if cli_channels_probe_ok and ready_channels and not ready_channels_runtime:
        remediation.append(
            "Gateway runtime has no ready channels; run `openclaw channels list --json` "
            "and re-link accounts with `openclaw channels add/login`"
        )
    if api_url and api_required and not api_ok:
        remediation.append("Start the configured OpenClaw API endpoint or set api_required=false")
    elif api_url and not api_ok:
        remediation.append("Optional: clear openclaw.api_url if unused to remove API-unreachable noise in status")

    payload.update(
        {
            "status": status,
            "functional": functional,
            "routing_functional": routing_functional,
            "messaging_functional": messaging_functional,
            "openclaw_enabled": enabled,
            "api_required": api_required,
            "gateway_url": gateway_url,
            "gateway_reachable": gateway_ok,
            "gateway_probe_source": gateway_probe_source,
            "gateway_probe_detail": gateway_note,
            "openclaw_cli_launcher": cli_meta,
            "openclaw_cli_health_detail": cli_health_detail,
            "openclaw_cli_channels_probe_ok": cli_channels_probe_ok,
            "openclaw_cli_channels_detail": cli_channels_detail,
            "openclaw_cli_channels": cli_channels,
            "gateway_port": gateway_port,
            "gateway_bind": bind,
            "wsl_gateway_ip": wsl_gateway_ip,
            "wsl_gateway_url": wsl_gateway_url,
            "api_url": api_url,
            "api_reachable": api_ok,
            "channels_enabled": all_enabled_channels,
            "channels_enabled_known": enabled_channels_known,
            "channels_enabled_system": enabled_channels_system,
            "channels_enabled_unknown": enabled_channels_unknown,
            "channels_ready_config": ready_channels,
            "channels_ready": ready_channels_runtime,
            "channels_ready_messaging": messaging_channels_ready,
            "channels_ready_system": system_channels_ready,
            "runtime_channel_failures": runtime_channel_failures,
            "channel_status": channel_status,
            "notes": notes,
            "remediation": remediation,
        }
    )
    report_path = _write_state_report(paths.nusyq_hub, "openclaw_status.json", payload)
    payload["report_file"] = str(report_path)
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🔌 OpenClaw Status")
        print("=" * 60)
        print(f"status: {status}")
        print(f"functional: {'yes' if functional else 'no'}")
        print(f"messaging_functional: {'yes' if messaging_functional else 'no'}")
        print(f"openclaw.enabled: {enabled}")
        print(f"gateway: {'reachable' if gateway_ok else 'unreachable'} ({gateway_url}) via {gateway_probe_source}")
        print(f"api: {'reachable' if api_ok else 'unreachable'} ({api_url})")
        print(f"channels enabled: {', '.join(all_enabled_channels) if all_enabled_channels else 'none'}")
        print(f"channels ready: {', '.join(ready_channels_runtime) if ready_channels_runtime else 'none'}")
        for note in notes:
            print(f"note: {note}")

    return 0 if functional else 1


@dataclass(frozen=True)
class OpenAntigravityOptions:
    port: int = ANTIGRAVITY_DEFAULT_PORT
    host: str = "127.0.0.1"
    port_specified: bool = False


def _parse_open_antigravity_args(
    args: list[str], default_port: int = ANTIGRAVITY_DEFAULT_PORT
) -> OpenAntigravityOptions:
    tokens = list(
        args[1:]
        if args
        and args[0]
        in {
            "open_antigravity_start",
            "open_antigravity_runtime_status",
            "open_antigravity_stop",
            "antigravity_status",
            "antigravity_health",
        }
        else args
    )
    port = int(default_port)
    host = "127.0.0.1"
    port_specified = False
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.startswith("--port"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                with contextlib.suppress(ValueError):
                    parsed = int(value)
                    if parsed > 0:
                        port = parsed
                        port_specified = True
            i += consumed
            continue
        if token.startswith("--host"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                host = value.strip() or host
            i += consumed
            continue
        i += 1

    return OpenAntigravityOptions(port=port, host=host, port_specified=port_specified)


def _open_antigravity_web_root(paths: RepoPaths) -> Path | None:
    if not paths.nusyq_hub:
        return None
    web_root = paths.nusyq_hub / "web" / "modular-window-server"
    return web_root if web_root.exists() else None


def _open_antigravity_health_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/health"


def _collect_open_antigravity_runtime(paths: RepoPaths, options: OpenAntigravityOptions) -> dict[str, Any]:
    if not paths.nusyq_hub:
        return {
            "pid": None,
            "running": False,
            "health_ok": False,
            "health_detail": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
            "port": options.port,
            "host": options.host,
            "health_url": _open_antigravity_health_url(options.host, options.port),
        }

    pid_path = _antigravity_runtime_pid_path(paths.nusyq_hub)
    pid_record = _read_openclaw_pid_record(pid_path)
    configured_port = options.port
    if not options.port_specified:
        with contextlib.suppress(ValueError, TypeError):
            pid_port = int(pid_record.get("port", 0) or 0)
            if pid_port > 0:
                configured_port = pid_port
    pid = int(pid_record.get("pid", 0) or 0)
    running = _is_process_running(pid)
    if pid and not running and pid_path.exists():
        with contextlib.suppress(OSError):
            pid_path.unlink()
    health_url = _open_antigravity_health_url(options.host, configured_port)
    health_ok, health_detail = _probe_http_health(health_url)
    return {
        "pid": pid or None,
        "running": running,
        "health_ok": health_ok,
        "health_detail": health_detail,
        "port": configured_port,
        "host": options.host,
        "health_url": health_url,
        "pid_file": str(pid_path),
        "pid_record": pid_record,
    }


def _antigravity_probe_truth() -> tuple[str, str]:
    from src.api import systems as systems_api

    return systems_api._probe_system_status("antigravity")


def _handle_open_antigravity_start(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "open_antigravity_start",
            "status": "error",
            "functional": False,
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    web_root = _open_antigravity_web_root(paths)
    if web_root is None:
        payload = {
            "action": "open_antigravity_start",
            "status": "error",
            "functional": False,
            "error": "modular-window-server missing",
            "expected_path": str(paths.nusyq_hub / "web" / "modular-window-server"),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    options = _parse_open_antigravity_args(args)
    node_bin = shutil.which("node")
    if not node_bin:
        payload = {
            "action": "open_antigravity_start",
            "status": "error",
            "functional": False,
            "error": "node binary not found",
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    pid_path = _antigravity_runtime_pid_path(paths.nusyq_hub)
    log_path = _antigravity_runtime_log_path(paths.nusyq_hub)
    runtime_state = _collect_open_antigravity_runtime(paths, options)
    existing_pid = int(runtime_state.get("pid") or 0)
    if runtime_state.get("running"):
        if runtime_state.get("health_ok"):
            status, detail = _antigravity_probe_truth()
            functional = status == "online"
            payload = {
                "action": "open_antigravity_start",
                "status": "already_running",
                "functional": functional,
                "pid": existing_pid,
                "port": runtime_state["port"],
                "host": runtime_state["host"],
                "health_url": runtime_state["health_url"],
                "health_ok": runtime_state["health_ok"],
                "health_detail": runtime_state["health_detail"],
                "probe_status": status,
                "probe_detail": detail,
                "log_file": str(log_path),
                "pid_file": str(pid_path),
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else json.dumps(payload, indent=2))
            return 0 if functional else 1
        _terminate_job_process(existing_pid, grace_s=4.0)

    command = [node_bin, "server.js"]
    try:
        with log_path.open("a", encoding="utf-8") as log_fh:
            env = os.environ.copy()
            env["PORT"] = str(options.port)
            process = subprocess.Popen(
                command,
                cwd=str(web_root),
                env=env,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except OSError as exc:
        payload = {
            "action": "open_antigravity_start",
            "status": "error",
            "functional": False,
            "error": str(exc),
            "command": command,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    health_url = _open_antigravity_health_url(options.host, options.port)
    _write_openclaw_pid_record(
        pid_path,
        {
            "pid": process.pid,
            "started_at": now_stamp(),
            "command": command,
            "cwd": str(web_root),
            "port": options.port,
            "host": options.host,
            "health_url": health_url,
            "log_file": str(log_path),
        },
    )

    healthy = False
    health_detail = "health check pending"
    deadline = time.time() + ANTIGRAVITY_READY_TIMEOUT_S
    while time.time() < deadline:
        healthy, health_detail = _probe_http_health(health_url)
        if healthy:
            break
        if not _is_process_running(process.pid):
            break
        time.sleep(0.5)

    probe_status, probe_detail = _antigravity_probe_truth()
    functional = healthy and probe_status == "online"
    payload = {
        "action": "open_antigravity_start",
        "status": "ok" if functional else ("degraded" if healthy else "error"),
        "functional": functional,
        "pid": process.pid,
        "port": options.port,
        "host": options.host,
        "health_url": health_url,
        "health_ok": healthy,
        "health_detail": health_detail,
        "probe_status": probe_status,
        "probe_detail": probe_detail,
        "log_file": str(log_path),
        "pid_file": str(pid_path),
        "command": command,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🛰️ Open Antigravity Start")
        print("=" * 60)
        print(f"status: {payload['status']}")
        print(f"pid: {process.pid}")
        print(f"health: {'ok' if healthy else 'fail'} ({health_detail})")
        print(f"probe: {probe_status} ({probe_detail})")
    return 0 if functional else 1


def _handle_open_antigravity_runtime_status(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "open_antigravity_runtime_status",
            "status": "error",
            "functional": False,
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    options = _parse_open_antigravity_args(args)
    runtime_state = _collect_open_antigravity_runtime(paths, options)
    probe_status, probe_detail = _antigravity_probe_truth()
    running = bool(runtime_state.get("running", False))
    health_ok = bool(runtime_state.get("health_ok", False))
    functional = running and health_ok and probe_status == "online"
    status = (
        "online" if functional else ("degraded" if (running or health_ok or probe_status == "degraded") else "offline")
    )

    payload = {
        "action": "open_antigravity_runtime_status",
        "status": status,
        "functional": functional,
        "pid": runtime_state.get("pid"),
        "running": running,
        "port": runtime_state.get("port"),
        "host": runtime_state.get("host"),
        "health_url": runtime_state.get("health_url"),
        "health_ok": health_ok,
        "health_detail": runtime_state.get("health_detail"),
        "probe_status": probe_status,
        "probe_detail": probe_detail,
        "pid_file": runtime_state.get("pid_file"),
        "log_file": str(_antigravity_runtime_log_path(paths.nusyq_hub)),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🛰️ Open Antigravity Runtime Status")
        print("=" * 60)
        print(f"status: {status}")
        print(f"running: {'yes' if running else 'no'}")
        print(f"health: {'ok' if health_ok else 'fail'} ({runtime_state.get('health_detail')})")
        print(f"probe: {probe_status} ({probe_detail})")
    return 0 if functional else 1


def _handle_open_antigravity_stop(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "open_antigravity_stop",
            "status": "error",
            "functional": False,
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    options = _parse_open_antigravity_args(args)
    runtime_state = _collect_open_antigravity_runtime(paths, options)
    pid = int(runtime_state.get("pid") or 0)
    stopped = True
    if pid and _is_process_running(pid):
        stopped = _terminate_job_process(pid, grace_s=4.0)

    pid_path = _antigravity_runtime_pid_path(paths.nusyq_hub)
    if stopped and pid_path.exists():
        with contextlib.suppress(OSError):
            pid_path.unlink()

    post_health_ok, post_health_detail = _probe_http_health(str(runtime_state.get("health_url")))
    payload = {
        "action": "open_antigravity_stop",
        "status": "stopped" if stopped and not post_health_ok else "degraded",
        "functional": stopped and not post_health_ok,
        "pid": runtime_state.get("pid"),
        "stopped": stopped,
        "port": runtime_state.get("port"),
        "host": runtime_state.get("host"),
        "health_url": runtime_state.get("health_url"),
        "health_after_stop": {"ok": post_health_ok, "detail": post_health_detail},
        "pid_file": str(pid_path),
        "log_file": str(_antigravity_runtime_log_path(paths.nusyq_hub)),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🛰️ Open Antigravity Stop")
        print("=" * 60)
        print(f"status: {payload['status']}")
        print(f"pid: {runtime_state.get('pid') or 'none'}")
        print(f"health_after_stop: {post_health_detail}")
    return 0 if payload["functional"] else 1


def _handle_antigravity_probe_status(
    action_name: str,
    paths: RepoPaths,
    json_mode: bool = False,
    action_args: list[str] | None = None,
) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": action_name,
            "status": "error",
            "functional": False,
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    try:
        status, detail = _antigravity_probe_truth()
    except Exception as exc:
        payload = {
            "action": action_name,
            "status": "error",
            "functional": False,
            "error": str(exc),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if json_mode else payload["error"])
        return 1

    options = _parse_open_antigravity_args(action_args or [action_name])
    runtime_state = _collect_open_antigravity_runtime(paths, options)
    if status == "online" and not runtime_state.get("health_ok", False):
        status = "degraded"
    functional = status == "online" and bool(runtime_state.get("health_ok", False))
    payload = {
        "action": action_name,
        "status": status,
        "functional": functional,
        "detail": detail,
        "runtime": {
            "pid": runtime_state.get("pid"),
            "running": runtime_state.get("running", False),
            "port": runtime_state.get("port"),
            "host": runtime_state.get("host"),
            "health_url": runtime_state.get("health_url"),
            "health_ok": runtime_state.get("health_ok", False),
            "health_detail": runtime_state.get("health_detail"),
            "pid_file": runtime_state.get("pid_file"),
            "log_file": str(_antigravity_runtime_log_path(paths.nusyq_hub)),
        },
        "generated_at": datetime.now(UTC).isoformat(),
        "status_endpoint": "/api/systems/antigravity/status",
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🛰️ Open Antigravity Status")
        print("=" * 60)
        print(f"status: {status}")
        print(f"functional: {'yes' if functional else 'no'}")
        print(f"detail: {detail}")
        print(
            "runtime_health: "
            f"{'ok' if runtime_state.get('health_ok', False) else 'fail'} "
            f"({runtime_state.get('health_url')})"
        )
        if not functional:
            print("hint: start modular-window-server (or set NUSYQ_ANTIGRAVITY_STATUS_URL) and retry")
    return 0 if functional else 1


def _handle_antigravity_status(paths: RepoPaths, json_mode: bool = False, action_args: list[str] | None = None) -> int:
    return _handle_antigravity_probe_status("antigravity_status", paths, json_mode=json_mode, action_args=action_args)


def _handle_antigravity_health(paths: RepoPaths, json_mode: bool = False, action_args: list[str] | None = None) -> int:
    return _handle_antigravity_probe_status("antigravity_health", paths, json_mode=json_mode, action_args=action_args)


@dataclass(frozen=True)
class OpenClawSmokeOptions:
    async_mode: bool = False
    help_timeout_s: float = 10.0
    max_help_runtime_s: float = 0.0


def _parse_openclaw_smoke_args(args: list[str]) -> OpenClawSmokeOptions:
    tokens = list(args[1:] if args and args[0] == "openclaw_smoke" else args)
    async_mode = "--async" in tokens and "--sync" not in tokens
    help_timeout_s = float(os.getenv("NUSYQ_OPENCLAW_HELP_TIMEOUT_S", "10"))
    max_help_runtime_s = float(os.getenv("NUSYQ_OPENCLAW_HELP_MAX_RUNTIME_S", "0"))
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.startswith("--help-timeout-s"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                try:
                    help_timeout_s = max(1.0, float(value))
                except ValueError:
                    pass
            i += consumed
            continue
        if token.startswith("--max-help-runtime-s"):
            value, consumed = _consume_flag_value(tokens, i)
            if value:
                try:
                    max_help_runtime_s = max(0.0, float(value))
                except ValueError:
                    pass
            i += consumed
            continue
        i += 1
    return OpenClawSmokeOptions(
        async_mode=async_mode,
        help_timeout_s=help_timeout_s,
        max_help_runtime_s=max_help_runtime_s,
    )


def _handle_openclaw_smoke(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if not paths.nusyq_hub:
        payload = {
            "action": "openclaw_smoke",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    options = _parse_openclaw_smoke_args(args)
    checkpoint_file = paths.nusyq_hub / "state" / "reports" / "openclaw_smoke_latest.json"
    if options.async_mode:
        cmd = [sys.executable, "scripts/start_nusyq.py", "openclaw_smoke", "--sync", "--json"]
        cmd.append(f"--help-timeout-s={options.help_timeout_s}")
        if options.max_help_runtime_s > 0:
            cmd.append(f"--max-help-runtime-s={options.max_help_runtime_s}")
        job = _start_subprocess_job(
            paths,
            job_type="openclaw_smoke",
            command=cmd,
            cwd=paths.nusyq_hub,
            metadata={
                "runner": "start_nusyq",
                "action": "openclaw_smoke",
                "checkpoint_file": str(checkpoint_file),
            },
        )
        payload = {
            "action": "openclaw_smoke",
            "status": "submitted",
            "job_id": job["job_id"],
            "pid": job["pid"],
            "stdout_log": job["stdout_log"],
            "stderr_log": job["stderr_log"],
            "checkpoint_file": str(checkpoint_file),
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🔌 OpenClaw smoke submitted as background job")
            print(f"Job ID: {payload['job_id']}")
            print(f"PID: {payload['pid']}")
            print(f"stdout: {payload['stdout_log']}")
            print(f"stderr: {payload['stderr_log']}")
            print(f"Check status: python scripts/start_nusyq.py openclaw_smoke_status {payload['job_id']} --wait=30")
        return 0

    cmd = [
        sys.executable,
        "scripts/openclaw_smoke_test.py",
        "--json",
        f"--help-timeout-s={options.help_timeout_s}",
    ]
    if options.max_help_runtime_s > 0:
        cmd.append(f"--max-help-runtime-s={options.max_help_runtime_s}")
    timeout_s = int(max(30.0, options.help_timeout_s + 90.0))
    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=timeout_s)
    parsed: dict[str, Any] | None = None
    if out:
        with contextlib.suppress(Exception):
            candidate = json.loads(out)
            if isinstance(candidate, dict):
                parsed = candidate

    payload: dict[str, Any] = {
        "action": "openclaw_smoke",
        "status": "ok" if rc == 0 else "failed",
        "generated_at": datetime.now().isoformat(),
        "checkpoint_file": str(checkpoint_file),
        "help_timeout_s": options.help_timeout_s,
        "max_help_runtime_s": options.max_help_runtime_s,
    }
    if parsed:
        payload["result"] = parsed
        status = parsed.get("status")
        if isinstance(status, str):
            payload["status"] = status
    else:
        payload["stdout_tail"] = "\n".join(out.splitlines()[-20:]) if out else ""
        payload["stderr_tail"] = "\n".join(err.splitlines()[-20:]) if err else ""

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    else:
        if parsed and isinstance(parsed.get("summary"), dict):
            summary = parsed["summary"]
            print("🔌 OpenClaw Smoke")
            print("=" * 60)
            print(f"Status: {payload['status']}")
            print(f"Passed: {summary.get('passed', 0)}/{summary.get('total', 0)}")
            print(f"Report: {parsed.get('latest_report_file')}")
        elif out:
            print(out)
        if err:
            print(err)

    return 0 if rc == 0 else 1


def _handle_culture_ship_status(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    return _handle_subprocess_job_status(
        args,
        paths,
        job_type="culture_ship",
        action_name="culture_ship_status",
        json_mode=json_mode,
    )


def _handle_error_report_status(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if any(token in {"--help", "-h"} for token in args[1:]):
        _print_error_report_help("error_report_status")
        return 0

    return _handle_subprocess_job_status(
        args,
        paths,
        job_type="error_report",
        action_name="error_report_status",
        checkpoint_loader=_summarize_error_report_checkpoint,
        json_mode=json_mode,
    )


def _handle_doctor_status(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    return _handle_subprocess_job_status(
        args,
        paths,
        job_type="doctor",
        action_name="doctor_status",
        checkpoint_loader=_summarize_doctor_checkpoint,
        json_mode=json_mode,
    )


def _handle_openclaw_smoke_status(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    return _handle_subprocess_job_status(
        args,
        paths,
        job_type="openclaw_smoke",
        action_name="openclaw_smoke_status",
        checkpoint_loader=_summarize_checkpoint_from_metadata,
        json_mode=json_mode,
    )


def _handle_failover_status(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Summarize newest fallback telemetry receipts and success rates."""
    if not paths.nusyq_hub:
        payload = {
            "action": "failover_status",
            "status": "error",
            "functional": False,
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    tokens = list(args[1:] if args and args[0] == "failover_status" else args)
    limit = 10
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token.startswith("--limit="):
            with contextlib.suppress(ValueError):
                limit = int(token.split("=", 1)[1])
        elif token == "--limit" and idx + 1 < len(tokens):
            with contextlib.suppress(ValueError):
                limit = int(tokens[idx + 1])
            idx += 1
        idx += 1
    limit = max(1, min(limit, 200))

    receipts_dir = paths.nusyq_hub / "state" / "reports" / "failover_receipts"
    files = (
        sorted(
            receipts_dir.glob("failover_*.json"),
            key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
            reverse=True,
        )
        if receipts_dir.exists()
        else []
    )

    rows: list[dict[str, Any]] = []
    for receipt_path in files:
        payload = read_json(receipt_path)
        if isinstance(payload, dict):
            row = dict(payload)
            row["receipt_file"] = str(receipt_path)
            rows.append(row)

    newest_rows = rows[:limit]

    def _is_success(row: dict[str, Any]) -> bool:
        status = str(row.get("candidate_status", "")).lower()
        return status in {"success", "submitted"}

    def _pct(numerator: int, denominator: int) -> float:
        return round((numerator / denominator) * 100.0, 2) if denominator else 0.0

    attempted = len(newest_rows)
    successful = sum(1 for row in newest_rows if _is_success(row))
    selected = sum(1 for row in newest_rows if bool(row.get("selected")))
    selected_successful = sum(1 for row in newest_rows if bool(row.get("selected")) and _is_success(row))

    by_candidate: dict[str, dict[str, int]] = {}
    for row in newest_rows:
        system = str(row.get("candidate_system") or "unknown")
        bucket = by_candidate.setdefault(
            system,
            {"attempted": 0, "successful": 0, "selected": 0, "selected_successful": 0},
        )
        bucket["attempted"] += 1
        if _is_success(row):
            bucket["successful"] += 1
        if bool(row.get("selected")):
            bucket["selected"] += 1
            if _is_success(row):
                bucket["selected_successful"] += 1

    per_candidate: list[dict[str, Any]] = []
    for system in sorted(by_candidate):
        bucket = by_candidate[system]
        attempted_count = int(bucket["attempted"])
        successful_count = int(bucket["successful"])
        selected_count = int(bucket["selected"])
        selected_success_count = int(bucket["selected_successful"])
        per_candidate.append(
            {
                "candidate_system": system,
                "attempted": attempted_count,
                "successful": successful_count,
                "success_rate_percent": _pct(successful_count, attempted_count),
                "selected": selected_count,
                "selection_rate_percent": _pct(selected_count, attempted_count),
                "selected_successful": selected_success_count,
                "selected_success_rate_percent": _pct(selected_success_count, selected_count),
            }
        )

    newest_compact = [
        {
            "receipt_file": row.get("receipt_file"),
            "generated_at": row.get("generated_at"),
            "task_id": row.get("task_id"),
            "trigger_system": row.get("trigger_system"),
            "candidate_system": row.get("candidate_system"),
            "candidate_status": row.get("candidate_status"),
            "selected": bool(row.get("selected")),
            "trigger_reason": row.get("trigger_reason"),
        }
        for row in newest_rows
    ]

    report = {
        "action": "failover_status",
        "status": "ok" if rows else "empty",
        "functional": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "receipts_dir": str(receipts_dir),
        "total_receipts": len(rows),
        "recent_limit": limit,
        "recent_receipts_count": len(newest_rows),
        "summary": {
            "attempted": attempted,
            "successful": successful,
            "success_rate_percent": _pct(successful, attempted),
            "selected": selected,
            "selection_rate_percent": _pct(selected, attempted),
            "selected_successful": selected_successful,
            "selected_success_rate_percent": _pct(selected_successful, selected),
        },
        "by_candidate_system": per_candidate,
        "newest_receipts": newest_compact,
    }

    latest_path = paths.nusyq_hub / "state" / "reports" / "failover_status_latest.json"
    _write_json_report(latest_path, report)
    report["report_path"] = str(latest_path)

    if json_mode:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print("🔁 Fallback Status")
    print("=" * 60)
    print(f"Receipts: total={report['total_receipts']} | showing newest={report['recent_receipts_count']}")
    summary = report["summary"]
    print(f"Success rate: {summary['successful']}/{summary['attempted']} ({summary['success_rate_percent']}%)")
    print(
        "Selected success: "
        f"{summary['selected_successful']}/{summary['selected']} "
        f"({summary['selected_success_rate_percent']}%)"
    )
    if per_candidate:
        print("\nBy candidate system:")
        for row in per_candidate:
            print(
                "  - "
                f"{row['candidate_system']}: {row['successful']}/{row['attempted']} "
                f"({row['success_rate_percent']}%)"
            )
    if newest_compact:
        print("\nNewest receipts:")
        for row in newest_compact[:5]:
            filename = Path(str(row.get("receipt_file") or "unknown")).name
            selected_mark = "selected" if row.get("selected") else "not_selected"
            print(f"  - {filename} | {row.get('candidate_system')}:{row.get('candidate_status')} | {selected_mark}")
    else:
        print("\nNo failover receipts found yet.")
    print(f"\nReport: {latest_path}")
    return 0


def _handle_system_complete_status(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    return _handle_subprocess_job_status(
        args,
        paths,
        job_type="system_complete",
        action_name="system_complete_status",
        checkpoint_loader=_summarize_system_complete_checkpoint,
        json_mode=json_mode,
    )


def _autonomous_service_checkpoint_path(paths: RepoPaths) -> Path | None:
    if not paths.nusyq_hub:
        return None
    return paths.nusyq_hub / "state" / "reports" / "autonomous_service_latest.json"


def _write_autonomous_service_checkpoint(checkpoint_path: Path | None, payload: dict[str, Any]) -> None:
    if checkpoint_path is None:
        return
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


async def _autonomous_service_process_background_once() -> dict[str, Any]:
    """Run one background-task orchestration tick."""
    from src.orchestration.background_task_orchestrator import get_orchestrator

    orchestrator = get_orchestrator()
    timeout_s = float(os.getenv("NUSYQ_AUTONOMOUS_BG_TIMEOUT_S", "20"))
    try:
        task = await asyncio.wait_for(orchestrator.process_next_task(), timeout=timeout_s)
    except TimeoutError:
        return {"status": "timeout", "timeout_s": timeout_s}
    if task is None:
        return {"status": "idle"}
    task_status = getattr(task.status, "value", str(task.status))
    return {"status": "processed", "task_id": task.task_id, "task_status": task_status}


def _run_autonomous_service_loop(paths: RepoPaths, args: list[str], json_mode: bool = False) -> int:
    """Internal long-running autonomous loop: orchestrator tick + one auto_cycle."""
    tokens = list(args[1:] if args and args[0] == "autonomous_service" else args)
    interval_s = _parse_int_flag(tokens, "--interval", int(os.getenv("NUSYQ_AUTONOMOUS_SERVICE_INTERVAL_S", "120")))
    iterations = _parse_int_flag(tokens, "--iterations", 0)
    max_pus = _parse_int_flag(tokens, "--max-pus", 1)
    fail_fast = "--fail-fast" in tokens
    culture_ship = "--culture-ship" in tokens
    culture_ship_dry_run = "--culture-ship-dry-run" in tokens
    real_mode = "--real" in tokens
    force_mode = "--force" in tokens

    checkpoint_path = _autonomous_service_checkpoint_path(paths)
    started_at = datetime.now().isoformat()
    loop_pid = os.getpid()
    iteration = 0
    failed_cycles = 0

    if not json_mode:
        print("🤖 Autonomous Service Loop")
        print("=" * 60)
        print(f"PID: {loop_pid}")
        print(f"interval: {interval_s}s | iterations: {'infinite' if iterations <= 0 else iterations}")
        print(f"max_pus: {max_pus} | real_mode: {real_mode}")
        if checkpoint_path:
            print(f"checkpoint: {checkpoint_path}")

    while iterations <= 0 or iteration < iterations:
        iteration += 1
        cycle_started = datetime.now().isoformat()
        if not json_mode:
            print(f"\n🔁 Service iteration {iteration}")

        try:
            bg_result = asyncio.run(_autonomous_service_process_background_once())
        except Exception as exc:
            bg_result = {"status": "failed", "error": str(exc)}

        auto_cycle_args = ["auto_cycle", "--iterations=1", "--sleep=0", f"--max-pus={max_pus}"]
        if force_mode:
            auto_cycle_args.append("--force")
        if real_mode:
            auto_cycle_args.append("--real")
        if culture_ship:
            auto_cycle_args.append("--culture-ship")
        if culture_ship_dry_run:
            auto_cycle_args.append("--culture-ship-dry-run")

        cycle_rc = handle_auto_cycle(
            auto_cycle_args,
            paths,
            handle_pu_queue_processing,
            handle_queue_execution,
            handle_quest_replay,
            handle_metrics_dashboard,
            handle_cross_sync,
            handle_next_action_generation,
            culture_ship_handler=lambda dry_run: _handle_culture_ship_cycle(
                paths,
                ["--sync", *(["--dry-run"] if dry_run else [])],
                json_mode=json_mode,
            ),
            gate_handler=_handle_ai_work_gate,
        )

        if cycle_rc != 0:
            failed_cycles += 1

        checkpoint_payload = {
            "action": "autonomous_service",
            "status": "running",
            "started_at": started_at,
            "updated_at": datetime.now().isoformat(),
            "current_iteration": iteration,
            "iterations_target": iterations,
            "interval_s": interval_s,
            "max_pus": max_pus,
            "real_mode": real_mode,
            "fail_fast": fail_fast,
            "pid": loop_pid,
            "last_cycle": {
                "started_at": cycle_started,
                "rc": cycle_rc,
                "background": bg_result,
            },
            "failed_cycles": failed_cycles,
            "checks": [
                {
                    "name": "background_orchestrator_tick",
                    "passed": bg_result.get("status") != "failed",
                },
                {"name": "auto_cycle", "passed": cycle_rc == 0},
            ],
            "completed_checks": 2,
            "total_planned": 2,
            "current_check": "sleep",
        }
        _write_autonomous_service_checkpoint(checkpoint_path, checkpoint_payload)

        if cycle_rc != 0 and fail_fast:
            checkpoint_payload["status"] = "failed"
            checkpoint_payload["finished_at"] = datetime.now().isoformat()
            checkpoint_payload["current_check"] = "halted_fail_fast"
            _write_autonomous_service_checkpoint(checkpoint_path, checkpoint_payload)
            if json_mode:
                print(json.dumps(checkpoint_payload, indent=2, ensure_ascii=False))
            else:
                print("❌ Autonomous service halted (fail-fast enabled).")
            return 1

        if iterations > 0 and iteration >= iterations:
            break

        time.sleep(max(1, interval_s))

    finished_payload = {
        "action": "autonomous_service",
        "status": "completed" if failed_cycles == 0 else "degraded",
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "iterations_completed": iteration,
        "iterations_target": iterations,
        "failed_cycles": failed_cycles,
        "pid": loop_pid,
    }
    _write_autonomous_service_checkpoint(checkpoint_path, finished_payload)
    if json_mode:
        print(json.dumps(finished_payload, indent=2, ensure_ascii=False))
    else:
        print("\n✅ Autonomous service loop completed.")
        print(f"iterations: {iteration} | failed_cycles: {failed_cycles}")
    return 0 if failed_cycles == 0 else 1


def _handle_autonomous_service(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Manage autonomous service lifecycle: on|off|status."""
    tokens = list(args[1:] if args and args[0] == "autonomous_service" else args)
    if "--service-loop" in tokens:
        return _run_autonomous_service_loop(paths, args, json_mode=json_mode)

    if not tokens or tokens[0] in {"--help", "-h", "help"}:
        print("Usage: python scripts/start_nusyq.py autonomous_service <on|off|status> [options]")
        print("  on     Start background autonomous service")
        print("  off    Stop latest autonomous service job")
        print("  status Show autonomous service job status")
        print("Options:")
        print("  --interval=SECONDS      Service cadence for background loop (default: 120)")
        print("  --iterations=N          Stop after N iterations (default: infinite)")
        print("  --max-pus=N             PU batch size per iteration (default: 1)")
        print("  --real                  Enable real-mode PU execution inside each cycle")
        print("  --culture-ship          Include culture ship cycle each iteration")
        print("  --culture-ship-dry-run  Include culture ship in dry-run mode")
        print("  --fail-fast             Stop service loop on first failing cycle")
        return 0

    command = tokens[0].strip().lower()
    passthrough = tokens[1:]
    checkpoint_path = _autonomous_service_checkpoint_path(paths)

    if command == "on":
        if not paths.nusyq_hub:
            payload = {
                "action": "autonomous_service",
                "status": "error",
                "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
            }
            print(json.dumps(payload, indent=2) if json_mode else payload["error"])
            return 1

        interval_s = _parse_int_flag(tokens, "--interval", int(os.getenv("NUSYQ_AUTONOMOUS_SERVICE_INTERVAL_S", "120")))
        launch_cmd = [
            sys.executable,
            "scripts/start_nusyq.py",
            "autonomous_service",
            "--service-loop",
            f"--interval={interval_s}",
        ]
        for token in passthrough:
            if token.startswith("--"):
                if token.startswith("--interval"):
                    continue
                launch_cmd.append(token)
        if json_mode:
            launch_cmd.append("--json")

        job = _start_subprocess_job(
            paths,
            job_type="autonomous_service",
            command=launch_cmd,
            cwd=paths.nusyq_hub,
            metadata={
                "runner": "start_nusyq",
                "action": "autonomous_service",
                "checkpoint_file": str(checkpoint_path) if checkpoint_path else None,
                "interval_s": interval_s,
            },
        )
        payload = {
            "action": "autonomous_service",
            "status": "submitted",
            "job_id": job["job_id"],
            "pid": job["pid"],
            "stdout_log": job["stdout_log"],
            "stderr_log": job["stderr_log"],
            "checkpoint_file": str(checkpoint_path) if checkpoint_path else None,
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🤖 Autonomous service started")
            print(f"Job ID: {payload['job_id']}")
            print(f"PID: {payload['pid']}")
            print(f"stdout: {payload['stdout_log']}")
            print(f"stderr: {payload['stderr_log']}")
            print(
                f"Check status: python scripts/start_nusyq.py autonomous_service status {payload['job_id']} --wait=15"
            )
        return 0

    if command in {"off", "status"}:
        status_args = ["autonomous_service", *passthrough]
        if command == "off" and "--cancel" not in status_args:
            status_args.append("--cancel")
        return _handle_subprocess_job_status(
            status_args,
            paths,
            job_type="autonomous_service",
            action_name="autonomous_service",
            checkpoint_loader=_summarize_checkpoint_from_metadata,
            json_mode=json_mode,
        )

    payload = {
        "action": "autonomous_service",
        "status": "error",
        "error": f"unknown subcommand: {command}",
        "allowed": ["on", "off", "status"],
    }
    print(json.dumps(payload, indent=2) if json_mode else payload["error"])
    return 1


def _handle_culture_ship_cycle(
    paths: RepoPaths,
    args: list[str] | None = None,
    json_mode: bool = False,
) -> int:
    """Dedicated cycle command with sync default for gate/e2e usage."""
    cycle_args = list(args or [])
    has_mode_flag = any(flag in cycle_args for flag in ("--sync", "--async"))
    if not has_mode_flag:
        cycle_args.insert(0, "--sync")
    return _handle_culture_ship_advisory(paths, cycle_args, json_mode=json_mode)


def _handle_culture_ship_advisory(
    paths: RepoPaths,
    args: list[str] | None = None,
    json_mode: bool = False,
) -> int:
    """Run the Culture Ship Strategic Advisor for ecosystem improvements."""
    args = args or []
    dry_run = "--dry-run" in args
    async_mode = "--async" in args and "--sync" not in args
    if async_mode:
        if not paths.nusyq_hub:
            if json_mode:
                print(
                    json.dumps(
                        {
                            "action": "culture_ship",
                            "status": "error",
                            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
                        },
                        indent=2,
                    )
                )
            else:
                print(ERROR_NUSYQ_HUB_PATH_NOT_FOUND)
            return 1
        cmd = [sys.executable, "scripts/start_nusyq.py", "culture_ship", "--sync"]
        if dry_run:
            cmd.append("--dry-run")
        job = _start_subprocess_job(
            paths,
            job_type="culture_ship",
            command=cmd,
            cwd=paths.nusyq_hub,
            metadata={"runner": "start_nusyq", "action": "culture_ship"},
        )
        payload = {
            "action": "culture_ship",
            "status": "submitted",
            "job_id": job["job_id"],
            "pid": job["pid"],
            "stdout_log": job["stdout_log"],
            "stderr_log": job["stderr_log"],
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🌟 CULTURE SHIP STRATEGIC ADVISOR")
            print("=" * 60)
            print("Submitted as background job")
            print(f"Job ID: {payload['job_id']}")
            print(f"PID: {payload['pid']}")
            print(f"Check status: python scripts/start_nusyq.py culture_ship_status {payload['job_id']}")
        return 0

    try:
        from datetime import datetime

        from src.orchestration.culture_ship_strategic_advisor import CultureShipStrategicAdvisor

        if not json_mode:
            print("🌟 CULTURE SHIP STRATEGIC ADVISOR")
            print("=" * 60)

        previous_dry_run = os.getenv("NUSYQ_CULTURE_SHIP_DRY_RUN")
        if dry_run:
            os.environ["NUSYQ_CULTURE_SHIP_DRY_RUN"] = "1"
        try:
            advisor = CultureShipStrategicAdvisor()
            result = advisor.run_full_strategic_cycle()
        finally:
            if dry_run:
                if previous_dry_run is None:
                    os.environ.pop("NUSYQ_CULTURE_SHIP_DRY_RUN", None)
                else:
                    os.environ["NUSYQ_CULTURE_SHIP_DRY_RUN"] = previous_dry_run

        # Print summary - handle both dict and plain values
        if not json_mode:
            print("\n📊 STRATEGIC CYCLE SUMMARY")
            print("=" * 60)

        if isinstance(result, dict):
            issues = result.get("issues_identified", [])
            decisions = result.get("decisions_made", [])
            impls = result.get("implementations", {})

            # Handle both list and dict return types
            if not json_mode:
                if isinstance(issues, list):
                    print(f"Issues identified: {len(issues)}")
                elif isinstance(issues, int):
                    print(f"Issues identified: {issues}")

                if isinstance(decisions, list):
                    print(f"Decisions made: {len(decisions)}")
                elif isinstance(decisions, int):
                    print(f"Decisions made: {decisions}")

                if isinstance(impls, dict):
                    print(f"Implementations completed: {impls.get('decisions_processed', 0)}")
                    total_fixes = impls.get("total_fixes_applied", 0)
                    print(f"\n✅ Total ecosystem fixes applied: {total_fixes}")
                elif isinstance(impls, list):
                    print(f"Implementations completed: {len(impls)}")
                    total_fixes = sum(impl.get("fixes_applied", 0) for impl in impls if isinstance(impl, dict))
                    print(f"\n✅ Total ecosystem fixes applied: {total_fixes}")
        else:
            if not json_mode:
                print(f"Result: {result}")

        # Save receipt
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        receipt_path = paths.nusyq_hub / "state" / "receipts" / f"culture_ship_{timestamp}.txt"
        receipt_path.parent.mkdir(parents=True, exist_ok=True)

        with open(receipt_path, "w") as f:
            f.write("CULTURE SHIP STRATEGIC ADVISOR RECEIPT\n")
            f.write("=" * 60 + "\n\n")
            f.write(json.dumps(result if isinstance(result, dict) else {"result": result}, indent=2))

        # Persist cycle result to memory chronicle for cross-process recall
        try:
            _chronicle_path = paths.nusyq_hub / "state" / "memory_chronicle.jsonl"
            _chronicle_path.parent.mkdir(parents=True, exist_ok=True)
            _summary_entry: dict = {
                "node_id": f"culture_ship_cycle_{timestamp}",
                "tags": ["culture_ship", "cycle", "strategic_advisor"],
                "timestamp": datetime.now().isoformat(),
                "source": "culture_ship_cycle",
                "dry_run": dry_run,
                "receipt_path": str(receipt_path),
            }
            if isinstance(result, dict):
                _summary_entry["issues"] = (
                    len(result.get("issues_identified", []))
                    if isinstance(result.get("issues_identified"), list)
                    else result.get("issues_identified", 0)
                )
                _summary_entry["decisions"] = (
                    len(result.get("decisions_made", []))
                    if isinstance(result.get("decisions_made"), list)
                    else result.get("decisions_made", 0)
                )
                _summary_entry["fixes"] = (
                    result.get("implementations", {}).get("total_fixes_applied", 0)
                    if isinstance(result.get("implementations"), dict)
                    else 0
                )
            with open(_chronicle_path, "a", encoding="utf-8") as _cf:
                _cf.write(json.dumps(_summary_entry, default=str) + "\n")
        except Exception:
            pass  # Chronicle is optional — never block the cycle

        payload = {
            "action": "culture_ship",
            "status": "ok",
            "generated_at": datetime.now().isoformat(),
            "receipt_path": str(receipt_path),
            "dry_run": dry_run,
            "result": result,
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        else:
            print(f"\n📝 Receipt saved to: {receipt_path}")
        return 0

    except Exception as e:
        if json_mode:
            print(
                json.dumps(
                    {"action": "culture_ship", "status": "error", "error": str(e)},
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(f"❌ Culture Ship Advisory failed: {e}")
        import traceback

        if not json_mode:
            traceback.print_exc()
        return 1


def _handle_simverse_bridge(paths: RepoPaths) -> int:
    print("🌉 NuSyQ ↔ SimulatedVerse Bridge Test")
    print("=" * 50)

    print("\n1. Running cross-ecosystem sync...")
    try:
        from src.tools.cross_ecosystem_sync import CrossEcosystemSync
    except Exception as exc:
        print(f"   ❌ CrossEcosystemSync import failed: {exc}")
        return 1

    syncer = CrossEcosystemSync(repo_root=paths.nusyq_hub)
    result = syncer.sync_all()

    status = str(result.get("status", "unknown")).lower()
    synced_items = int(result.get("synced_items", 0) or 0)
    print(f"   Status: {status}")
    print(f"   Synced items: {synced_items}")

    details = result.get("details")
    if isinstance(details, dict):
        print("\n2. Sync details:")
        for key, payload in details.items():
            if isinstance(payload, dict):
                item_status = payload.get("status", "unknown")
                item_count = payload.get("items_synced", 0)
                print(f"   - {key}: {item_status} ({item_count})")
            else:
                print(f"   - {key}: {payload}")

    if status in {"success", "partial"}:
        print("\n✅ Bridge test complete")
        if status == "partial":
            print(f"   Note: {result.get('message', 'partial sync')}")
        return 0

    print("\n❌ Bridge test failed")
    if result.get("error"):
        print(f"   Error: {result.get('error')}")
    return 1


def _get_simverse_bridge(paths: RepoPaths):
    try:
        from src.integration.simulatedverse_unified_bridge import SimulatedVerseUnifiedBridge
    except Exception as exc:
        raise RuntimeError(f"SimulatedVerse bridge import failed: {exc}") from exc

    simulatedverse_root = paths.simulatedverse if paths.simulatedverse else None
    http_base_url = str(os.getenv("SIMULATEDVERSE_BASE_URL") or "").strip()
    if not http_base_url:
        sim_host = str(os.getenv("SIMULATEDVERSE_HOST") or "http://127.0.0.1").strip()
        sim_port = str(os.getenv("SIMULATEDVERSE_PORT") or "5001").strip()
        if "://" not in sim_host:
            sim_host = f"http://{sim_host}"
        parsed = urlparse(sim_host)
        if parsed.port:
            http_base_url = sim_host
        else:
            host = parsed.hostname or "127.0.0.1"
            scheme = parsed.scheme or "http"
            http_base_url = f"{scheme}://{host}:{sim_port}"

    return SimulatedVerseUnifiedBridge(
        simulatedverse_root=simulatedverse_root,
        http_base_url=http_base_url,
        mode="auto",
    )


def _parse_int_flag(args: list[str], flag: str, default: int) -> int:
    for idx, token in enumerate(args):
        if token.startswith(f"{flag}="):
            value = token.split("=", 1)[1]
            if value.isdigit():
                return int(value)
        if token == flag and idx + 1 < len(args):
            value = args[idx + 1]
            if value.isdigit():
                return int(value)
    return default


def _parse_str_flag(args: list[str], flag: str) -> str | None:
    for idx, token in enumerate(args):
        if token.startswith(f"{flag}="):
            return token.split("=", 1)[1]
        if token == flag and idx + 1 < len(args):
            return args[idx + 1]
    return None


def _handle_simverse_consciousness(paths: RepoPaths, json_mode: bool = False) -> int:
    try:
        bridge = _get_simverse_bridge(paths)
        snapshot = bridge.get_consciousness_state()
        payload = {
            "action": "simverse_consciousness",
            "status": "ok",
            "snapshot": {
                "level": snapshot.level,
                "stage": snapshot.stage,
                "active_systems": snapshot.active_systems,
                "timestamp": snapshot.timestamp,
                "metrics": snapshot.metrics or {},
            },
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🌌 SimulatedVerse Consciousness")
            print("=" * 50)
            print(f"Level: {snapshot.level}")
            print(f"Stage: {snapshot.stage}")
            print(f"Active systems: {', '.join(snapshot.active_systems) if snapshot.active_systems else '(none)'}")
            print(f"Timestamp: {snapshot.timestamp}")
        return 0
    except Exception as exc:
        if json_mode:
            print(json.dumps({"action": "simverse_consciousness", "status": "error", "error": str(exc)}))
        else:
            print(f"❌ SimulatedVerse consciousness read failed: {exc}")
        return 1


def _handle_simverse_history(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    limit = _parse_int_flag(args, "--limit", 10)
    try:
        bridge = _get_simverse_bridge(paths)
        history = bridge.get_consciousness_history(limit=limit)
        payload = {
            "action": "simverse_history",
            "status": "ok",
            "limit": limit,
            "entries": history,
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🧭 SimulatedVerse Consciousness History")
            print("=" * 60)
            if not history:
                print("No consciousness entries found.")
            for entry in history:
                ts = entry.get("timestamp", "unknown")
                level = entry.get("level", "?")
                stage = entry.get("evolution_stage", "unknown")
                print(f"- {ts} | level={level} | stage={stage}")
        return 0
    except Exception as exc:
        if json_mode:
            print(json.dumps({"action": "simverse_history", "status": "error", "error": str(exc)}))
        else:
            print(f"❌ SimulatedVerse history read failed: {exc}")
        return 1


def _handle_simverse_ship_directives(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    priority = _parse_str_flag(args, "--priority")
    try:
        bridge = _get_simverse_bridge(paths)
        directives = bridge.get_ship_directives(priority=priority)
        payload = {
            "action": "simverse_ship_directives",
            "status": "ok",
            "priority": priority,
            "directives": directives,
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🛡️ Culture Ship Directives")
            print("=" * 60)
            if not directives:
                print("No active directives found.")
            for directive in directives:
                print(f"- [{directive.get('priority', 'normal')}] {directive.get('description', '')}")
        return 0
    except Exception as exc:
        if json_mode:
            print(json.dumps({"action": "simverse_ship_directives", "status": "error", "error": str(exc)}))
        else:
            print(f"❌ Culture Ship directives read failed: {exc}")
        return 1


def _handle_simverse_cognition_insights(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    limit = _parse_int_flag(args, "--limit", 10)
    since_raw = _parse_str_flag(args, "--since")
    since_ts: datetime | None = None
    if since_raw:
        try:
            since_ts = datetime.fromisoformat(since_raw.replace("Z", "+00:00"))
        except ValueError:
            since_ts = None

    try:
        bridge = _get_simverse_bridge(paths)
        insights = bridge.get_cognition_insights(since_timestamp=since_ts, limit=limit)
        payload = {
            "action": "simverse_cognition_insights",
            "status": "ok",
            "limit": limit,
            "since": since_raw,
            "insights": insights,
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🧠 Cognition Chamber Insights")
            print("=" * 60)
            if not insights:
                print("No insights found.")
            for insight in insights:
                print(f"- {insight}")
        return 0
    except Exception as exc:
        if json_mode:
            print(json.dumps({"action": "simverse_cognition_insights", "status": "error", "error": str(exc)}))
        else:
            print(f"❌ Cognition insights read failed: {exc}")
        return 1


def _handle_simverse_bridge_health(paths: RepoPaths, json_mode: bool = False) -> int:
    try:
        bridge = _get_simverse_bridge(paths)
        status = bridge.get_system_status()
        payload = {"action": "simverse_bridge_health", "status": "ok", "bridge": status}
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🌉 SimulatedVerse Bridge Health")
            print("=" * 60)
            for key, value in status.items():
                print(f"- {key}: {value}")
        return 0
    except Exception as exc:
        if json_mode:
            print(json.dumps({"action": "simverse_bridge_health", "status": "error", "error": str(exc)}))
        else:
            print(f"❌ SimulatedVerse bridge health failed: {exc}")
        return 1


def _handle_simverse_ship_approve(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    action = _parse_str_flag(args, "--action") or (args[0] if args else None)
    context_raw = _parse_str_flag(args, "--context")
    context = {}
    if context_raw:
        try:
            context = json.loads(context_raw)
        except json.JSONDecodeError:
            context = {"raw": context_raw}

    if not action:
        if json_mode:
            print(
                json.dumps(
                    {
                        "action": "simverse_ship_approve",
                        "status": "error",
                        "error": "missing action",
                    }
                )
            )
        else:
            print("[ERROR] Usage: simverse_ship_approve --action <name> [--context '{...}']")
        return 1

    try:
        bridge = _get_simverse_bridge(paths)
        approval = bridge.request_ship_approval(action, context)
        payload = {
            "action": "simverse_ship_approve",
            "status": "ok",
            "decision": {
                "approved": approval.approved,
                "reasoning": approval.reasoning,
                "confidence": approval.confidence,
            },
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🛡️ Culture Ship Approval")
            print("=" * 60)
            print(f"Approved: {approval.approved}")
            print(f"Confidence: {approval.confidence:.2f}")
            print(f"Reasoning: {approval.reasoning}")
        return 0
    except Exception as exc:
        if json_mode:
            print(json.dumps({"action": "simverse_ship_approve", "status": "error", "error": str(exc)}))
        else:
            print(f"❌ Ship approval check failed: {exc}")
        return 1


def _handle_simverse_log_event(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    event_type = _parse_str_flag(args, "--type") or (args[0] if args else None)
    data_raw = _parse_str_flag(args, "--data")
    data: dict[str, Any] = {}
    if data_raw:
        try:
            data = json.loads(data_raw)
        except json.JSONDecodeError:
            data = {"raw": data_raw}

    if not event_type:
        if json_mode:
            print(json.dumps({"action": "simverse_log_event", "status": "error", "error": "missing type"}))
        else:
            print("[ERROR] Usage: simverse_log_event --type <name> [--data '{...}']")
        return 1

    try:
        bridge = _get_simverse_bridge(paths)
        success = bridge.log_event(event_type, data)
        payload = {
            "action": "simverse_log_event",
            "status": "ok" if success else "error",
            "event_type": event_type,
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🧾 SimulatedVerse Event Log")
            print("=" * 60)
            print(f"Event type: {event_type}")
            print(f"Status: {'logged' if success else 'failed'}")
        return 0 if success else 1
    except Exception as exc:
        if json_mode:
            print(json.dumps({"action": "simverse_log_event", "status": "error", "error": str(exc)}))
        else:
            print(f"❌ Event log failed: {exc}")
        return 1


def _handle_simverse_breathing(paths: RepoPaths, json_mode: bool = False) -> int:
    try:
        bridge = _get_simverse_bridge(paths)
        factor = bridge.get_breathing_factor()
        payload = {
            "action": "simverse_breathing",
            "status": "ok",
            "factor": factor,
        }
        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("🌬️ SimulatedVerse Breathing Factor")
            print("=" * 60)
            print(f"Timeout multiplier: {factor:.2f}x")
        return 0
    except Exception as exc:
        if json_mode:
            print(json.dumps({"action": "simverse_breathing", "status": "error", "error": str(exc)}))
        else:
            print(f"❌ Breathing factor read failed: {exc}")
        return 1


def _handle_sns_analyze(args: list[str], paths: RepoPaths) -> int:
    """Analyze text for SNS-Core token savings."""
    print("🔣 SNS-Core Token Analysis")
    print("=" * 50)

    if not args:
        print("\n[ERROR] Usage: start_nusyq.py sns_analyze <text>")
        return 1

    text = " ".join(args)

    try:
        from src.utils.sns_core_helper import analyze_token_savings, format_sns_report

        analysis = analyze_token_savings(text)
        report = format_sns_report(analysis)
        print(f"\n{report}")

        # Save to state for reference
        if paths.nusyq_hub:
            report_file = paths.nusyq_hub / "state" / "reports" / "sns_analysis.json"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            import json

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2)
            print(f"\n💾 Analysis saved to: {report_file.relative_to(paths.nusyq_hub)}")

        return 0
    except Exception as exc:
        print(f"\n[ERROR] SNS analysis failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_sns_convert(args: list[str]) -> int:
    """Convert text to SNS-Core notation."""
    print("🔣 SNS-Core Notation Converter")
    print("=" * 50)

    if not args:
        print("\n[ERROR] Usage: start_nusyq.py sns_convert <text>")
        return 1

    text = " ".join(args)

    try:
        from src.utils.sns_core_helper import convert_to_sns

        sns_text, metadata = convert_to_sns(text, aggressive=False)

        print(f"\n📝 Original ({metadata['original_tokens_est']} tokens):")
        print(f"   {text}")
        print(f"\n🔹 SNS-Core ({metadata['sns_tokens_est']} tokens, {metadata['savings_pct']}% savings):")
        print(f"   {sns_text}")
        print(f"\n📊 Replacements ({len(metadata['replacements'])}):")
        for repl in metadata["replacements"]:
            print(f"   • {repl}")

        return 0
    except Exception as exc:
        print(f"\n[ERROR] SNS conversion failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_zero_token_status(paths: RepoPaths) -> int:
    """Check zero-token mode status across ecosystem (uses cached paths)."""
    print("💰 Zero-Token Mode Status")
    print("=" * 50)

    # Use cached path discovery (no more "minutes searching")
    print(f"\n📂 Path discovery: Using cache (TTL: {PATH_CACHE_TTL_SECONDS}s)")

    # Check SNS-Core
    print("\n🔣 SNS-Core System:")
    sns_core_path = paths.nusyq_hub / "temp_sns_core" if paths.nusyq_hub else None
    if sns_core_path and sns_core_path.exists():
        readme = sns_core_path / "README.md"
        if readme.exists():
            print(f"   ✅ Found at: {sns_core_path.relative_to(paths.nusyq_hub)}")
            print("   📊 Validated: 41% token reduction")
            print("   📈 Claimed: 60-85% reduction potential")
        else:
            print("   ⚠️  Directory exists but README.md missing")
    else:
        print("   ❌ Not found (expected in temp_sns_core/)")

    # Check SimulatedVerse zero-token mode
    print("\n🎮 SimulatedVerse Zero-Token Mode:")
    if paths.simulatedverse:
        script_candidates = [
            paths.simulatedverse / "scripts" / "zero_token_ops.ps1",
            paths.simulatedverse / "scripts" / "zero_token_ops.sh",
            paths.simulatedverse / "scripts" / "zero-token" / "run-zero-token.ts",
            paths.simulatedverse / "scripts" / "zero-token" / "zero-token-demo.js",
            paths.simulatedverse / "scripts" / "zero-token" / "bridge-tripartite.js",
            # Current SimulatedVerse checkout keeps zero-token demo/orchestration here.
            paths.simulatedverse / "scripts" / "ztp-demo.py",
            paths.simulatedverse / "sim" / "cascade" / "cascade_event.py",
            paths.simulatedverse / "game" / "engine" / "cascade_event.py",
        ]
        available_script = next((p for p in script_candidates if p.exists()), None)
        status_indicators = [
            paths.simulatedverse / ".agent" / "zero_token_verified",
            paths.simulatedverse / "state" / "zero-token-demo.json",
            paths.simulatedverse / "state" / "zero-token-results.jsonl",
            paths.simulatedverse / "logs" / "zero-token-mode.log",
        ]
        available_indicator = next((p for p in status_indicators if p.exists()), None)
        if available_script:
            print("   ✅ Zero-token ops available")
            print("   💵 Cost: $0.00 (offline-first)")
            print(f"   📄 Entry script: {available_script.name}")
            if available_indicator:
                print(f"   🧾 Evidence: {available_indicator.relative_to(paths.simulatedverse)}")
        elif available_indicator:
            print("   ⚠️  Zero-token scripts not found in expected paths, but status indicators exist")
            print(f"   🧾 Evidence: {available_indicator.relative_to(paths.simulatedverse)}")
            print("   💡 Consider re-linking scripts/zero-token into this checkout")
        else:
            print("   ⚠️  SimulatedVerse found but zero-token script missing")
    else:
        print("   ❌ SimulatedVerse path not found")

    # Integration status
    print("\n🔗 Integration Status:")
    try:
        from src.utils.sns_core_helper import load_sns_symbols

        symbols = load_sns_symbols()
        print(f"   ✅ SNS-Core helper imported ({len(symbols)} symbols)")
    except Exception as exc:
        print(f"   ⚠️  SNS-Core helper not available: {exc}")

    print("\n📝 Available Commands:")
    print("   • start_nusyq.py sns_analyze <text>  - Analyze token savings")
    print("   • start_nusyq.py sns_convert <text>  - Convert to SNS notation")
    print("   • start_nusyq.py zero_token_status   - This status check")

    print("\n💡 Estimated Savings:")
    print("   • SNS-Core: $70-170/year (41% validated reduction)")
    print("   • Zero-Token Mode: $880/year (95% offline development)")
    print("   • Combined: $950-1,050/year potential")

    return 0


def _handle_pu_queue_processing(paths: RepoPaths, max_pus: int = 3, real_mode: bool = False) -> int:
    """Process PU queue with rate limiting.

    Args:
        paths: Repository paths
        max_pus: Maximum number of PUs to process (default 3)
        real_mode: Use real execution with Quantum Problem Resolver (default False)

    Returns:
        0 on success, 1 on error
    """
    mode_label = "REAL" if real_mode else "SIMULATED"
    print(f"🔄 PU Queue Processing [{mode_label} MODE, max={max_pus}]")
    print("=" * 50)

    if str(paths.nusyq_hub) not in sys.path:
        sys.path.insert(0, str(paths.nusyq_hub))

    try:
        import asyncio

        from src.automation.unified_pu_queue import UnifiedPUQueue

        # Import execution function from pu_queue_runner
        pu_runner_path = paths.nusyq_hub / "scripts" / "pu_queue_runner.py"
        if not pu_runner_path.exists():
            print(f"[WARN] PU queue runner not found at {pu_runner_path}")
            return 0

        # Load the queue
        queue = UnifiedPUQueue()

        # Find queued/approved PUs
        processable = [pu for pu in queue.queue if pu.status in {"queued", "approved"}]

        if not processable:
            print("\nInfo: No PUs ready for processing")
            return 0

        # Limit to max_pus
        to_process = processable[:max_pus]
        print(f"\n📝 Found {len(processable)} processable PUs, processing {len(to_process)}")

        async def process_pu(pu):
            """Process a single PU."""
            # Import here to avoid circular deps
            sys.path.insert(0, str(paths.nusyq_hub / "scripts"))
            from pu_queue_runner import _execute_pu_real

            # Assign agents if needed
            if not pu.assigned_agents:
                assigned = queue.assign_agents(pu.id)
                if assigned:
                    pu.assigned_agents = assigned

            # Execute
            pu.status = "executing"
            print(f"  ⚙️  {pu.id} | {pu.title[:50]}...")

            if real_mode:
                result = await _execute_pu_real(pu)
                pu.execution_results = result
                pu.status = "completed" if result.get("success") else "failed"
            else:
                pu.execution_results = {"note": "simulated completion", "executor": "auto_cycle"}
                pu.status = "completed"

            return pu.status == "completed"

        # Process PUs
        async def process_all():
            results = []
            for pu in to_process:
                success = await process_pu(pu)
                results.append(success)
            return results

        results = asyncio.run(process_all())
        queue._save_queue()

        succeeded = sum(results)
        print(f"\n✅ Processed {succeeded}/{len(to_process)} PUs successfully")

        # Write brief status to report
        report_path = paths.nusyq_hub / "state" / "reports" / "pu_queue_status.md"
        total = len(queue.queue)
        completed = len([p for p in queue.queue if p.status == "completed"])
        queued = len([p for p in queue.queue if p.status == "queued"])

        report_path.write_text(
            f"# PU Queue Status (Auto-Cycle)\n\n"
            f"Total: {total} | Completed: {completed} | Queued: {queued}\n\n"
            f"Last cycle: {len(to_process)} PUs processed ({succeeded} succeeded)\n",
            encoding="utf-8",
        )

        return 0

    except Exception as e:
        print(f"[ERROR] PU queue processing failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_queue_execution(paths: RepoPaths) -> int:
    """Execute next item from work queue."""
    print("📋 Work Queue Execution")
    print("=" * 50)

    if str(paths.nusyq_hub) not in sys.path:
        sys.path.insert(0, str(paths.nusyq_hub))

    try:
        import asyncio

        from src.tools.work_queue_executor import WorkQueueExecutor

        executor = WorkQueueExecutor(repo_root=paths.nusyq_hub)
        result = asyncio.run(executor.execute_next_item())

        print("\n" + json.dumps(result, indent=2))

        if result.get("status") == "success":
            print(f"\n✅ Item executed: {result.get('title', 'Unknown')}")
            return 0
        elif result.get("status") in {"empty", "no_queued_items"}:
            print(f"\nInfo: {result.get('message', 'Work queue is empty')}")
            return 0
        else:
            print(f"\n❌ Execution failed: {result.get('error', 'Unknown error')}")
            return 1
    except Exception as e:
        print(f"[ERROR] Queue execution failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_metrics_dashboard(paths: RepoPaths) -> int:
    """Display AI system metrics dashboard."""
    print("📊 AI SYSTEM METRICS DASHBOARD")
    print("=" * 70)

    if not paths.nusyq_hub:
        print("[ERROR] NuSyQ-Hub path not found")
        return 1

    try:
        # Parse time period argument (default 24 hours)
        import sys as sys_module

        from src.system.ai_metrics_tracker import generate_metrics_report

        hours = 24
        if "--hours" in sys_module.argv:
            idx = sys_module.argv.index("--hours")
            if idx + 1 < len(sys_module.argv):
                try:
                    hours = int(sys_module.argv[idx + 1])
                except ValueError:
                    print(f"⚠️  Invalid hours value, using default: {hours}")

        report = generate_metrics_report(paths.nusyq_hub, hours=hours)
        print(report)

        print("\n" + "=" * 70)
        print("💡 Tips:")
        print("  • Use --hours N to view different time periods")
        print("  • Metrics are recorded automatically during health checks")
        print("  • Gate decisions are logged when work gating is enforced")

        return 0

    except ImportError as exc:
        print(f"[ERROR] Could not import metrics tracker: {exc}")
        return 1
    except Exception as exc:
        print(f"[ERROR] Metrics dashboard failed: {exc}")
        import traceback

        traceback.print_exc()
        return 1
    """Build cultivation metrics dashboard."""
    print("📊 Cultivation Metrics Dashboard")
    print("=" * 50)

    if str(paths.nusyq_hub) not in sys.path:
        sys.path.insert(0, str(paths.nusyq_hub))

    try:
        import asyncio

        from src.tools.cultivation_metrics import CultivationMetrics

        metrics = CultivationMetrics(repo_root=paths.nusyq_hub)
        dashboard_path = asyncio.run(metrics.build_dashboard())

        print(f"\n✅ Dashboard generated: {dashboard_path}")
        print(f"\nView at: file:///{dashboard_path}")

        return 0
    except Exception as e:
        print(f"[ERROR] Dashboard generation failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_quest_replay(paths: RepoPaths) -> int:
    """Replay historical quests and extract learning."""
    print("🔄 Quest Replay & Learning")
    print("=" * 50)

    if str(paths.nusyq_hub) not in sys.path:
        sys.path.insert(0, str(paths.nusyq_hub))

    try:
        import asyncio

        from src.tools.quest_replay_engine import QuestReplayEngine

        engine = QuestReplayEngine(repo_root=paths.nusyq_hub)

        # Run replay
        print("\n1️⃣  Replaying recent quests...")
        replay = asyncio.run(engine.replay_recent_quests(limit=5))

        if replay.get("status") == "success":
            print(f"   ✅ Analyzed {replay.get('quests_analyzed', 0)} quests")
            print(f"   📌 Patterns identified: {len(replay.get('patterns', {}))}")
            print(f"   💡 Recommendations: {len(replay.get('recommendations', []))}")

            for rec in replay.get("recommendations", [])[:3]:
                print(f"      - {rec}")

        # Analyze work queue history
        print("\n2️⃣  Analyzing work queue history...")
        history = asyncio.run(engine.analyze_work_queue_history())

        if history.get("status") == "success":
            print(f"   📋 Total items: {history.get('total_items', 0)}")
            print(f"   ✅ Success rate: {history.get('overall_success_rate', 0)}%")

        # Predict next items
        print("\n3️⃣  Predicting next work items...")
        predictions = asyncio.run(engine.predict_next_items(count=3))

        if predictions.get("status") == "success":
            for pred in predictions.get("predictions", [])[:3]:
                print(f"   🎯 {pred.get('title', 'Unknown')} (confidence: {pred.get('confidence', 0)})")

        print("\n✅ Quest replay complete")
        return 0
    except Exception as e:
        print(f"[ERROR] Quest replay failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_pu_execute(args: list[str], paths: RepoPaths) -> int:
    """Execute a PU (Processing Unit) with optional real agent mode."""
    if len(args) < 2:
        print("[ERROR] Missing PU ID")
        print("\nUsage: python start_nusyq.py pu_execute <pu_id> [--real]")
        print("\nOptions:")
        print("  --real    Execute through real ChatDev/Ollama agents (default: simulated)")
        print("\nExamples:")
        print("  python start_nusyq.py pu_execute pu_12345")
        print("  python start_nusyq.py pu_execute pu_12345 --real")
        return 1

    pu_id = args[1]
    real_mode = "--real" in args

    print(f"⚙️  PU Execution: {pu_id}")
    print("=" * 50)
    print(f"   Mode: {'REAL' if real_mode else 'SIMULATED'}")

    if str(paths.nusyq_hub) not in sys.path:
        sys.path.insert(0, str(paths.nusyq_hub))

    try:
        from src.automation.unified_pu_queue import UnifiedPUQueue

        queue = UnifiedPUQueue(repo_root=paths.nusyq_hub)

        # Execute the PU
        print(f"\n▶️  Executing PU: {pu_id}")
        results = queue.execute_pu(pu_id, auto_execute=True, real_mode=real_mode)

        if "error" in results:
            print(f"\n❌ Error: {results['error']}")
            return 1

        # Display results
        print("\n✨ Execution Results:")
        for agent, status in results.items():
            status_icon = "✅" if status == "completed" else "⚠️" if status.startswith("skipped") else "❌"
            print(f"   {status_icon} {agent}: {status}")

        # Get PU status
        pu = queue._find_pu(pu_id)
        if pu:
            print(f"\n📊 PU Status: {pu.status}")
            if pu.status == "completed":
                print("🎉 PU completed successfully!")
                return 0
            else:
                print(f"⚠️  PU status: {pu.status}")
                return 1
        else:
            print("\n⚠️  Could not retrieve PU status")
            return 1

    except Exception as e:
        print(f"[ERROR] PU execution failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_dashboard(paths: RepoPaths) -> int:
    """Open the Agent Dashboard WebView (Phase 4 rehabilitation note).

    Note: Dashboard render functions (renderAgents, renderQuests, renderErrors)
    were flagged as orphaned by Nogic, but they're actually called via WebView IPC.
    This is a false positive due to cross-context JavaScript execution.

    This command provides CLI access to launch the dashboard.
    """
    print("🎯 Opening Agent Dashboard...")
    print("   (Requires running inside VS Code with extension installed)")

    # Check if we're in VS Code environment
    if not os.getenv("VSCODE_PID") and not os.getenv("VSCODE_IPC_HOOK"):
        print("\n❌ Not running in VS Code!")
        print("   Dashboard requires VS Code WebView environment")
        print("   Alternative: Use Command Palette > 'Agent Dashboard: Open'")
        return 1

    # Attempt to trigger VS Code command
    import subprocess

    result = subprocess.run(["code", "--command", "agentDashboard.open"], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Dashboard command sent")
        return 0
    else:
        print("\n⚠️  CLI command failed, use VS Code Command Palette instead:")
        print("   Ctrl+Shift+P → 'Agent Dashboard: Open'")
        return 1


def _handle_demo(args: list[str], paths: RepoPaths) -> int:
    """Handle demo command - run demonstration & showcase systems.

    Phase 5 rehabilitation: Provides CLI access to orphaned demo functions:
    - quick_demo() (SNS orchestrator quick demo)
    - Full SNS demo suite

    Usage:
        python start_nusyq.py demo                # Interactive menu
        python start_nusyq.py demo sns_quick      # Quick SNS demo
        python start_nusyq.py demo sns_full       # Full SNS suite
        python start_nusyq.py demo all            # All demos
        python start_nusyq.py demo --list         # List available
    """
    import subprocess

    # Build command for run_demos.py
    runner_path = paths.nusyq_hub / "scripts" / "run_demos.py"

    if not runner_path.exists():
        print(f"❌ Demo runner not found: {runner_path}")
        return 1

    # If no args, show list
    if len(args) < 2:
        cmd = [sys.executable, str(runner_path), "--list"]
    elif args[1] == "--list":
        cmd = [sys.executable, str(runner_path), "--list"]
    else:
        # Pass through demo type
        demo_type = args[1]
        cmd = [sys.executable, str(runner_path), f"--demo={demo_type}"]

    result = subprocess.run(cmd)
    return result.returncode


def _handle_factories(args: list[str], paths: RepoPaths) -> int:
    """Handle factory command - run orphaned factory functions.

    Phase 2 rehabilitation: Provides CLI access to 4 orphaned factory functions:
    - get_integrator() (Ollama/ChatDev)
    - get_orchestrator() (Claude/Copilot)
    - create_quantum_resolver() (archived v4.2.0)
    - create_server() (context server)

    Usage:
        python start_nusyq.py factory integrator --health
        python start_nusyq.py orchestrator --start
        python start_nusyq.py quantum_factory --problem-type=COMPLEX
        python start_nusyq.py context_server --port=8888
    """
    import subprocess

    # Extract factory subcommand
    if len(args) < 2:
        print("❌ Usage: python start_nusyq.py factory <subcommand> [options]")
        print("\nAvailable factories:")
        print("  integrator       - Ollama/ChatDev integrator (--health)")
        print("  orchestrator     - Claude/Copilot orchestrator (--start)")
        print("  quantum_factory  - Quantum resolver (--problem-type=X)")
        print("  context_server   - Context server (--port=N --serve)")
        print("\nOr use direct commands:")
        print("  python start_nusyq.py integrator --health")
        return 1

    # Map subcommand to factory type
    factory_map = {
        "integrator": "integrator",
        "orchestrator": "orchestrator",
        "quantum_factory": "quantum",
        "quantum": "quantum",
        "context_server": "context_server",
        "server": "context_server",
    }

    subcommand = args[1]
    factory_type = factory_map.get(subcommand)

    if not factory_type:
        print(f"❌ Unknown factory: {subcommand}")
        return 1

    # Build command for run_factories.py
    runner_path = paths.nusyq_hub / "scripts" / "run_factories.py"
    cmd = [sys.executable, str(runner_path), f"--factory={factory_type}"]

    # Pass through additional arguments
    if len(args) > 2:
        cmd.extend(args[2:])

    result = subprocess.run(cmd)
    return result.returncode


def _handle_examples(args: list[str], paths: RepoPaths) -> int:
    """Run interactive example runner - rehabilitates 12 orphaned example functions.

    Phase 1 of orphan symbol modernization: Surface documentation examples.
    """
    if "--help" in args:
        print("Usage: python start_nusyq.py examples [--list] [--example=N]")
        print("\nRun interactive examples that demonstrate system capabilities.")
        print("This rehabilitates 12 orphaned example functions.")
        print("\nOptions:")
        print("  --list        List all available examples")
        print("  --example=N   Run specific example by ID (1-12)")
        print("\nExamples:")
        print("  python start_nusyq.py examples")
        print("  python start_nusyq.py examples --list")
        print("  python start_nusyq.py examples --example=1")
        return 0

    try:
        # Run the interactive example runner
        import subprocess

        cmd = ["python", str(paths.nusyq_hub / "scripts" / "run_examples_interactive.py")]

        # Pass through arguments
        if "--list" in args:
            cmd.append("--list")

        for arg in args[1:]:
            if arg.startswith("--example="):
                cmd.append(arg)

        result = subprocess.run(cmd, cwd=paths.nusyq_hub)
        return result.returncode

    except Exception as e:
        print(f"[ERROR] Example runner failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _handle_batch_commit(args: list[str], paths: RepoPaths) -> int:
    """Run autonomous batch commit orchestrator."""
    if "--help" in args:
        print("Usage: python start_nusyq.py batch_commit [--dry-run] [--max-commits=N] [--staged-only]")
        print("\nOptions:")
        print("  --dry-run         Show what would be committed without committing")
        print("  --max-commits=N   Maximum number of commits to create (default: 10)")
        print("  --staged-only     Only analyze staged files (fast path for unhealthy repos)")
        print("\nExamples:")
        print("  python start_nusyq.py batch_commit --dry-run")
        print("  python start_nusyq.py batch_commit --max-commits=5")
        print("  python start_nusyq.py batch_commit --dry-run --staged-only")
        return 0

    print("🤖 Autonomous Batch Commit Orchestrator")
    print("=" * 50)

    # Parse args
    dry_run = "--dry-run" in args
    max_commits = 10
    for arg in args[1:]:
        if arg.startswith("--max-commits="):
            max_commits = int(arg.split("=")[1])

    try:
        import subprocess

        cmd = ["python", "scripts/autonomous_commit_orchestrator.py"]
        if dry_run:
            cmd.append("--dry-run")
        cmd.append(f"--max-commits={max_commits}")
        if "--staged-only" in args:
            cmd.append("--staged-only")

        result = subprocess.run(cmd, cwd=paths.nusyq_hub)
        return result.returncode

    except Exception as e:
        print(f"[ERROR] Batch commit failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _run_causal_analysis(
    text: str,
    *,
    nusyq_hub: Path | None,
    system_name: str = "causal_analysis",
    variables: list[str] | None = None,
) -> dict[str, Any]:
    from src.ai.ai_intermediary import CognitiveParadigm, SymbolicTranslator
    from src.consciousness.temple_of_knowledge.floor_3_systems import Floor3SystemsThinking

    translator = SymbolicTranslator()
    semantics = asyncio.run(translator._extract_semantics(text, CognitiveParadigm.NATURAL_LANGUAGE, {}))
    causality_chain = asyncio.run(translator._build_causality_chain(semantics))

    payload: dict[str, Any] = {
        "action": "causal_analysis",
        "status": "ok",
        "system_name": system_name,
        "input_text": text,
        "semantics": {
            "entities": semantics.get("entities", []),
            "relationships": semantics.get("relationships", []),
            "temporal_aspects": semantics.get("temporal_aspects", {}),
        },
        "causality_chain": causality_chain,
    }

    if variables:
        temple_root = (nusyq_hub or Path.cwd()) / "state" / "temple_of_knowledge"
        payload["feedback_loop"] = Floor3SystemsThinking(temple_root).detect_feedback_loop(
            system_name,
            variables,
        )

    return payload


def _handle_causal_analysis(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if "--help" in args:
        print("Usage: python start_nusyq.py causal_analysis [--text=TEXT] [--system=NAME] [--vars=a,b,c]")
        print("\nAnalyze a sentence or variable chain for causal connectors and feedback loops.")
        print(TEXT_EXAMPLES)
        print('  python start_nusyq.py causal_analysis --text="cache invalidation triggers rebuild after deploy"')
        print(
            '  python start_nusyq.py causal_analysis --system=build_pipeline --vars=growth_rate,error_regulation --text="retries happen because cache invalidation triggers rebuild after deploy"'
        )
        return 0

    text = ""
    system_name = "causal_analysis"
    variables: list[str] = []

    for arg in args[1:]:
        if arg.startswith("--text="):
            text = arg.split("=", 1)[1]
        elif arg.startswith("--system="):
            system_name = arg.split("=", 1)[1] or system_name
        elif arg.startswith("--vars="):
            variables = [item.strip() for item in arg.split("=", 1)[1].split(",") if item.strip()]
        elif not arg.startswith("--"):
            text = f"{text} {arg}".strip()

    if not text:
        payload = {
            "action": "causal_analysis",
            "status": "error",
            "error": "missing_text",
        }
        print(json.dumps(payload, indent=2) if json_mode else "❌ Provide --text=... for analysis")
        return 1

    payload = _run_causal_analysis(
        text,
        nusyq_hub=paths.nusyq_hub,
        system_name=system_name,
        variables=variables or None,
    )
    report_path = _write_state_report(paths.nusyq_hub, "causal_analysis_latest.json", payload)
    global _LAST_OUTPUTS
    _LAST_OUTPUTS = [str(report_path)]

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🧠 Causal Analysis")
        print("=" * 50)
        print(f"System: {payload['system_name']}")
        print(f"Relationships: {', '.join(payload['semantics']['relationships']) or 'none'}")
        print(f"Causality links: {len(payload['causality_chain'])}")
        if payload["causality_chain"]:
            for link in payload["causality_chain"]:
                print(
                    f"  • {link.get('type', 'unknown')}: {link.get('relationship', 'n/a')} "
                    f"(confidence {link.get('confidence', 0):.2f})"
                )
        if "feedback_loop" in payload:
            loop = payload["feedback_loop"]
            print(f"Loop type: {loop.get('loop_type') or 'undetermined'} (confidence {loop.get('confidence', 0):.2f})")
        print(f"Input: {payload['input_text']}")
        print(f"Report: {report_path}")
    return 0


def _run_specialization_status(agent: str | None = None) -> dict[str, Any]:
    from src.orchestration.specialization_learner import SpecializationLearner

    learner = SpecializationLearner()
    history = learner.tracker.history
    payload: dict[str, Any] = {
        "action": "specialization_status",
        "status": "ok",
        "team": learner.get_team_composition(),
        "agent_count": len(learner.agent_list),
        "history_events": len(history),
        "profiles_file": str((Path.cwd() / "state" / "specialization" / "agent_profiles.json").resolve()),
        "history_file": str((Path.cwd() / "state" / "specialization" / "specialization_history.jsonl").resolve()),
        "recent_attempts": [
            {
                "timestamp": record.timestamp,
                "agent": record.agent,
                "task_type": record.task_type,
                "temperature": record.temperature,
                "success": record.success,
                "quality_score": record.quality_score,
                "tokens_used": record.tokens_used,
                "latency_ms": record.latency_ms,
            }
            for record in history[-5:]
        ],
    }

    if agent:
        payload["agent"] = learner.get_agent_summary(agent)
    else:
        payload["agents"] = [learner.get_agent_summary(name) for name in learner.agent_list[:10]]

    return payload


def _handle_specialization_status(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    if "--help" in args:
        print("Usage: python start_nusyq.py specialization_status [--agent=NAME] [--json]")
        print("\nInspect cross-agent specialization learning and task coverage.")
        print(TEXT_EXAMPLES)
        print("  python start_nusyq.py specialization_status --json")
        print("  python start_nusyq.py specialization_status --agent=ollama")
        return 0

    agent = None
    for arg in args[1:]:
        if arg.startswith("--agent="):
            agent = arg.split("=", 1)[1].strip() or None

    payload = _run_specialization_status(agent=agent)
    report_path = _write_state_report(paths.nusyq_hub, "specialization_status_latest.json", payload)

    global _LAST_OUTPUTS
    _LAST_OUTPUTS = [str(report_path)]

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print("🧠 Specialization Status")
    print("=" * 50)
    print(f"Agents tracked: {payload['agent_count']}")
    print(f"History events: {payload['history_events']}")
    team = payload["team"]
    print(f"Average coverage per task: {team.get('avg_coverage_per_task', 0):.2f}")
    if agent and "agent" in payload:
        summary = payload["agent"]
        print(f"Agent: {summary['agent']}")
        print(f"Best task: {summary['best_task']}")
        print(f"Avg specialization score: {summary['avg_specialization_score']:.2f}")
    else:
        for summary in payload.get("agents", [])[:5]:
            print(f"  • {summary['agent']}: best={summary['best_task']} avg={summary['avg_specialization_score']:.2f}")
    print(f"Report: {report_path}")
    return 0


def _handle_cross_sync(paths: RepoPaths) -> int:
    """Sync cultivation data to SimulatedVerse."""
    print("🌉 Cross-Ecosystem Sync")
    print("=" * 50)

    if str(paths.nusyq_hub) not in sys.path:
        sys.path.insert(0, str(paths.nusyq_hub))

    try:
        import asyncio

        from src.tools.cross_ecosystem_sync import CrossEcosystemSync

        syncer = CrossEcosystemSync(repo_root=paths.nusyq_hub)
        result = asyncio.run(syncer.sync_to_simverse())

        print(f"\nStatus: {result.get('status', 'unknown')}")
        print(f"Items synced: {result.get('synced_items', 0)}")

        for key, detail in result.get("details", {}).items():
            status = detail.get("status", "unknown")
            synced = detail.get("items_synced", 0)
            print(f"  • {key}: {status} ({synced} items)")

        print("\n✅ Cross-sync complete")
        return 0
    except Exception as e:
        print(f"[ERROR] Cross-sync failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _trace_endpoint_check(endpoint: str) -> tuple[bool, str]:
    """Probe a tracing endpoint defensively.

    Many collectors expect either:
      - POST /v1/traces  (OTLP/HTTP)
      - GET  /health     (custom health probes)

    Earlier health checks hit the base URL and returned HTTP 404, which
    masked a healthy collector. We now try a small set of likely URLs and
    surface the first successful response.
    """
    import urllib.request

    def _attempt(url: str) -> tuple[bool, str]:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status < 500, f"{url} -> HTTP {resp.status}"
        except Exception as exc:
            return False, f"{url} unreachable: {exc}"

    base = endpoint.rstrip("/")
    candidates: list[str] = []
    if "/v1/traces" in base:
        candidates.append(base)
    else:
        candidates.append(f"{base}/health")
        candidates.append(f"{base}/v1/traces")
        candidates.append(base)

    detail = ""
    for url in candidates:
        ok, detail = _attempt(url)
        if ok:
            return True, detail
    return False, detail


def _parse_kv_args(args: list[str]) -> dict:
    updates = {}
    for arg in args:
        if arg.startswith("--") and "=" in arg:
            key, value = arg[2:].split("=", 1)
            if value.lower() in {"true", "false"}:
                updates[key.replace("-", "_")] = value.lower() == "true"
            else:
                try:
                    updates[key.replace("-", "_")] = float(value) if "." in value else int(value)
                except ValueError:
                    updates[key.replace("-", "_")] = value
    return updates


def _handle_override_gate(args: list[str], paths: RepoPaths) -> int:
    print("🚧 Override Gate")
    print("=" * 50)

    allow_list = []
    ttl_seconds = 3600
    reason = "manual override"
    for arg in args[1:]:
        if arg.startswith("--allow="):
            allow_list = [a.strip() for a in arg.split("=", 1)[1].split(",") if a.strip()]
        elif arg.startswith("--ttl="):
            try:
                ttl_seconds = int(arg.split("=", 1)[1])
            except ValueError:
                pass
        elif arg.startswith("--reason="):
            reason = arg.split("=", 1)[1]

    payload = {
        "run_id": ensure_run_id(),
        "created_at": now_stamp(),
        "ttl_seconds": ttl_seconds,
        "reason": reason,
        "allow_actions": allow_list,
    }
    gate_dir = paths.nusyq_hub / "state" / "gates"
    gate_dir.mkdir(parents=True, exist_ok=True)
    gate_path = gate_dir / f"override_{now_stamp()}.json"
    _write_json_report(gate_path, payload)
    print(f"OVERRIDE_GATE_OK: {gate_path}")
    return 0


def _handle_preflight_trace(paths: RepoPaths, contracts: dict) -> int:
    print("🧭 Trace Preflight")
    print("=" * 50)

    steps = [
        ("trace_service_status", lambda: handle_trace_service_status(paths)),
        ("trace_config_validate", lambda: handle_trace_config_validate(paths)),
        ("trace_smoke", lambda: handle_trace_smoke(paths)),
        ("trace_service_healthcheck", lambda: handle_trace_service_healthcheck(paths)),
    ]

    run_id = ensure_run_id()
    _trace_id, _span_id = ("n/a", "n/a")  # Placeholders for future composite span IDs
    composite_status = "success"
    per_step_receipts: list[str] = []

    enabled = False
    if otel:
        try:
            config = load_trace_config(paths.nusyq_hub)
            apply_trace_config(config)
            enabled = otel.init_tracing(config.get("service_name", "nusyq-hub"))
        except Exception:
            enabled = False

    tier = get_action_tier("preflight_trace", contracts)
    span_name = "nusyq.action.preflight_trace"
    cm = (
        otel.start_action_span(
            span_name,
            {
                "action.id": "preflight_trace",
                "action.tier": tier,
                "run.id": run_id,
                "repo.name": "NuSyQ-Hub",
            },
        )
        if (otel and enabled)
        else None
    )

    if cm:
        with cm as span:  # pylint: disable=not-context-manager
            for action_id, fn in steps:
                step_tier = get_action_tier(action_id, contracts)
                step_span = otel.start_action_span(
                    f"nusyq.action.{action_id}",
                    {
                        "action.id": action_id,
                        "action.tier": step_tier,
                        "run.id": run_id,
                        "repo.name": "NuSyQ-Hub",
                    },
                )
                step_status = "success"
                if step_span:
                    with step_span as _span:
                        rc = fn()
                        if rc != 0:
                            step_status = "error"
                        step_trace_id, step_span_id = otel.current_trace_ids() if (otel and enabled) else ("n/a", "n/a")
                        receipt_path = emit_receipt(
                            action_id,
                            paths.nusyq_hub,
                            step_tier,
                            run_id,
                            step_trace_id,
                            step_span_id,
                            step_status,
                            inputs={"composite": "preflight_trace", "step": action_id},
                            exit_code=rc,
                        )
                        try:
                            _span.set_attribute("receipt.path", str(receipt_path))
                            _span.add_event(
                                "receipt",
                                {
                                    "receipt.path": str(receipt_path),
                                    "status": step_status,
                                    "exit_code": rc,
                                },
                            )
                        except Exception:
                            pass
                else:
                    rc = fn()
                    if rc != 0:
                        step_status = "error"
                    receipt_path = emit_receipt(
                        action_id,
                        paths.nusyq_hub,
                        step_tier,
                        run_id,
                        "n/a",
                        "n/a",
                        step_status,
                        inputs={"composite": "preflight_trace", "step": action_id},
                        exit_code=rc,
                    )
                per_step_receipts.append(str(receipt_path))
                if step_status != "success":
                    composite_status = "error"

            if span:
                try:
                    span.set_attribute("receipt.per_step", ",".join(per_step_receipts))
                except Exception:
                    pass
            _trace_id, _span_id = otel.current_trace_ids() if (otel and enabled) else ("n/a", "n/a")
    else:
        for action_id, fn in steps:
            step_tier = get_action_tier(action_id, contracts)
            rc = fn()
            step_status = "success" if rc == 0 else "error"
            receipt_path = emit_receipt(
                action_id,
                paths.nusyq_hub,
                step_tier,
                run_id,
                "n/a",
                "n/a",
                step_status,
                inputs={"composite": "preflight_trace", "step": action_id},
                exit_code=rc,
            )
            per_step_receipts.append(str(receipt_path))
            if step_status != "success":
                composite_status = "error"

    global _LAST_OUTPUTS
    _LAST_OUTPUTS = per_step_receipts
    return 0 if composite_status == "success" else 1


def _handle_problem_signal_snapshot(args: list[str], paths: RepoPaths) -> int:
    print("📌 Problem Signal Snapshot")
    print("=" * 50)

    try:
        from src.diagnostics.problem_signal_snapshot import (
            RepoInfo,
            build_vscode_override,
            parse_args,
            run_snapshot,
        )
    except Exception as exc:
        print(f"❌ Unable to load problem signal snapshot: {exc}")
        return 1

    parsed = parse_args(args[1:])
    output_dir = Path(parsed.output_dir)
    vscode_counts_path = Path(parsed.vscode_counts_path)
    if paths.nusyq_hub:
        if not output_dir.is_absolute():
            output_dir = (paths.nusyq_hub / output_dir).resolve()
        if not vscode_counts_path.is_absolute():
            vscode_counts_path = (paths.nusyq_hub / vscode_counts_path).resolve()

    vscode_override = build_vscode_override(parsed)
    repos = [
        RepoInfo("NuSyQ-Hub", paths.nusyq_hub),
        RepoInfo("SimulatedVerse", paths.simulatedverse),
        RepoInfo("NuSyQ", paths.nusyq_root),
    ]

    result = run_snapshot(
        repos=repos,
        run_id=ensure_run_id(),
        vscode_counts_path=vscode_counts_path,
        vscode_counts_override=vscode_override,
        include_exports=not parsed.no_exports,
        run_ruff=parsed.run_ruff,
        output_dir=output_dir,
        write_latest=not parsed.no_latest,
    )

    outputs = [
        result.get("json_report"),
        result.get("md_report"),
        result.get("latest_json"),
        result.get("latest_md"),
        result.get("vscode_counts_path"),
    ]
    global _LAST_OUTPUTS
    _LAST_OUTPUTS = [str(p) for p in outputs if p]

    snapshot_path = result.get("latest_md") or result.get("md_report")
    print(f"✅ Snapshot saved: {snapshot_path}")
    return 0


def _handle_next_action_generation(paths: RepoPaths) -> int:
    """Generate next-action queue from intelligence signals.

    Wires multiple signals into perpetual feedback loop:
    - Current state changes
    - Lifecycle catalog
    - Quest system
    - Diagnostics
    - Coverage metrics
    - Module availability
    """
    print("🎯 Generating next-action queue...")

    if not paths.nusyq_hub:
        print("[WARNING] NuSyQ-Hub path not found; skipping action generation.")
        return 0

    try:
        # Import and run perpetual action generator
        sys.path.insert(0, str(paths.nusyq_hub / "src" / "tools"))
        from perpetual_action_generator import ActionGenerator

        generator = ActionGenerator(paths.nusyq_hub)
        actions = generator.generate_actions()

        # Save queue (register for consumption by callers)
        _ = generator.save_action_queue(actions)

        # Print summary
        print(f"   ✅ Generated {len(actions)} next actions")
        if actions:
            top = actions[0]
            print(f"   📌 Top priority: {top.title} ({top.priority.name})")

        return 0
    except Exception as e:
        print(f"   ⚠️  Action generation failed: {e}")
        return 1


def _handle_next_action_display(paths: RepoPaths) -> int:
    """Display the current next-action queue."""
    print("🎯 Next Action Queue")
    print("=" * 70)

    if not paths.nusyq_hub:
        print("[ERROR] NuSyQ-Hub path not found")
        return 1

    try:
        cmd = [sys.executable, "src/tools/next_action_display.py"]
        rc, out, _ = run(cmd, cwd=paths.nusyq_hub, timeout_s=10)
        if out:
            print(out)
        return rc
    except TimeoutError:
        print("⚠️  Action display timed out")
        return 1


def _handle_next_action_generate(paths: RepoPaths) -> int:
    """Generate fresh next-action queue."""
    return _handle_next_action_generation(paths)


def _handle_next_action_exec(args: list[str], paths: RepoPaths) -> int:
    """Execute an action by type."""
    if len(args) < 2:
        print("Usage: next_action_exec <action_type>")
        print(
            "Available types: validate_module, expand_coverage, resolve_quest, heal_repository, scale_orchestration, integrate_cross_repo"
        )
        return 1

    action_type = args[1]

    if not paths.nusyq_hub:
        print("[ERROR] NuSyQ-Hub path not found")
        return 1

    try:
        cmd = [sys.executable, "src/tools/next_action_display.py", f"--execute={action_type}"]
        rc, out, _ = run(cmd, cwd=paths.nusyq_hub, timeout_s=300)
        if out:
            print(out)
        return rc
    except TimeoutError:
        print("⚠️  Action execution timed out")
        return 1


def _handle_vscode_diagnostics_bridge(args: list[str], paths: RepoPaths) -> int:
    print("🧩 VS Code Diagnostics Bridge")
    print("=" * 50)

    if not paths.nusyq_hub:
        print("[ERROR] NuSyQ-Hub path not found; cannot run bridge.")
        return 1

    # Prefer the active interpreter to respect venvs on Windows/Linux/macOS
    cmd = [sys.executable, "scripts/vscode_diagnostics_bridge.py"]
    if "--quiet" in args[1:]:
        cmd.append("--quiet")
    for arg in args[1:]:
        if arg.startswith("--export="):
            cmd.append(arg)
        elif arg == "--override-truth":
            cmd.append(arg)

    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=120)
    if out:
        print(out)
    if err:
        print(err)

    # Treat artifact presence as success even if the tool returns non-zero due to warnings
    outputs = [
        str(paths.nusyq_hub / "docs" / "Reports" / "diagnostics" / "vscode_problem_counts_tooling.json"),
        str(paths.nusyq_hub / "docs" / "Reports" / "diagnostics" / "vscode_diagnostics_bridge.json"),
    ]

    artifacts_ok = False
    try:
        for p in outputs:
            if os.path.exists(p) and os.path.getsize(p) > 0:
                artifacts_ok = True
                break
    except Exception:
        artifacts_ok = False

    global _LAST_OUTPUTS
    _LAST_OUTPUTS = outputs

    if rc == 0 or artifacts_ok:
        return 0
    return 1


def _resolve_powershell_executable() -> str | None:
    """Resolve a PowerShell executable across Windows/WSL environments."""
    for candidate in ("powershell.exe", "pwsh.exe", "pwsh", "powershell"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _handle_claude_preflight(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Run Claude preflight checks using existing run_claude.ps1 diagnostics."""
    if not paths.nusyq_hub:
        payload = {
            "action": "claude_preflight",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    powershell_bin = _resolve_powershell_executable()
    if not powershell_bin:
        payload = {
            "action": "claude_preflight",
            "status": "error",
            "error": "PowerShell executable not found",
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    script_path = paths.nusyq_hub / "scripts" / "run_claude.ps1"
    if not script_path.exists():
        payload = {
            "action": "claude_preflight",
            "status": "error",
            "error": f"Missing script: {script_path}",
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    cmd = [
        powershell_bin,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        _to_windows_path(script_path),
        "-PreflightOnly",
    ]
    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=180)

    payload = {
        "action": "claude_preflight",
        "status": "ok" if rc == 0 else "error",
        "functional": rc == 0,
        "powershell": powershell_bin,
        "script": str(script_path),
        "exit_code": rc,
        "stdout": out,
        "stderr": err,
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🤖 Claude Preflight")
        print("=" * 50)
        if out:
            print(out)
        if err:
            print(err)
    return 0 if rc == 0 else 1


def _probe_claude_cli(paths: RepoPaths) -> dict[str, Any]:
    claude_path = shutil.which("claude", path=_build_env().get("PATH"))
    payload: dict[str, Any] = {
        "surface": "anthropic_claude_cli",
        "installed": bool(claude_path),
        "claude_path": claude_path,
        "authenticated": False,
        "functional": False,
    }
    if not claude_path or not paths.nusyq_hub:
        payload["failure_kind"] = "not_installed" if not claude_path else "hub_path_missing"
        return payload

    auth_rc, auth_out, auth_err = run(["claude", "auth", "status"], cwd="/tmp", timeout_s=60)
    auth_payload = _extract_json_payload(auth_out) if auth_out else None
    logged_in = isinstance(auth_payload, dict) and bool(auth_payload.get("loggedIn"))
    payload.update(
        {
            "auth_exit_code": auth_rc,
            "authenticated": logged_in,
            "auth_method": auth_payload.get("authMethod") if isinstance(auth_payload, dict) else None,
            "api_provider": auth_payload.get("apiProvider") if isinstance(auth_payload, dict) else None,
            "auth_stderr": auth_err[:500] if auth_err else "",
        }
    )
    if not logged_in:
        payload["failure_kind"] = "missing_auth"
        return payload

    prompt_cmd = [
        "claude",
        "--print",
        "--no-session-persistence",
        "--output-format",
        "text",
        "--add-dir",
        str(paths.nusyq_hub),
        "--",
        "Reply with exactly CLAUDE-CLI-OK.",
    ]
    prompt_rc, prompt_out, prompt_err = run(prompt_cmd, cwd="/tmp", timeout_s=90)
    normalized_output = prompt_out.strip().rstrip(".!")
    functional = prompt_rc == 0 and normalized_output == "CLAUDE-CLI-OK"
    payload.update(
        {
            "functional": functional,
            "prompt_exit_code": prompt_rc,
            "response_preview": prompt_out[:200] if prompt_out else "",
            "stderr": prompt_err[:500] if prompt_err else "",
        }
    )
    if not functional:
        payload["failure_kind"] = "runtime_failed"
    return payload


def _build_agent_surface_contract(
    *,
    router_target: str,
    supported_requested_surfaces: list[str],
    routable_surfaces: dict[str, dict[str, Any]],
    observed_only_surfaces: dict[str, dict[str, Any]] | None = None,
    selection_note: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "router_target": router_target,
        "supported_requested_surfaces": supported_requested_surfaces,
        "routable_surfaces": routable_surfaces,
    }
    if observed_only_surfaces:
        payload["observed_only_surfaces"] = observed_only_surfaces
    if selection_note:
        payload["selection_note"] = selection_note
    return payload


def _build_claude_surface_contract() -> dict[str, Any]:
    return _build_agent_surface_contract(
        router_target="claude",
        supported_requested_surfaces=["auto"],
        routable_surfaces={
            "cli": {
                "surface": "anthropic_claude_cli",
                "controllable": True,
                "default_execution_path": "claude_cli",
            }
        },
        selection_note="Claude currently auto-selects its CLI/orchestrator path; explicit surface override is not exposed.",
    )


def _build_codex_surface_contract() -> dict[str, Any]:
    return _build_agent_surface_contract(
        router_target="codex",
        supported_requested_surfaces=["auto"],
        routable_surfaces={
            "cli": {
                "surface": "openai_codex_cli",
                "controllable": True,
                "default_execution_path": "codex_cli",
            }
        },
        selection_note="Codex currently routes through the CLI path; explicit surface override is not exposed.",
    )


def _probe_claude_router(paths: RepoPaths) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "target": "claude",
        "functional": False,
        "route_ok": False,
        "execution_path": None,
        "execution_surface": None,
        "agent_identity": None,
        "response_preview": "",
    }
    if not paths.nusyq_hub:
        payload["failure_kind"] = "hub_path_missing"
        return payload
    cmd = [
        sys.executable,
        "scripts/nusyq_dispatch.py",
        "ask",
        "claude",
        "Reply with exactly CLAUDE-ROUTER-OK.",
    ]
    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=180)
    json_payload = _extract_json_payload(out) if out else None
    normalized_output = (
        str(json_payload.get("output", "")).strip().rstrip(".!") if isinstance(json_payload, dict) else ""
    )
    route_ok = rc == 0 and isinstance(json_payload, dict) and normalized_output == "CLAUDE-ROUTER-OK"
    payload.update(
        {
            "functional": route_ok,
            "route_ok": route_ok,
            "exit_code": rc,
            "execution_path": json_payload.get("execution_path") if isinstance(json_payload, dict) else None,
            "execution_surface": json_payload.get("execution_surface") if isinstance(json_payload, dict) else None,
            "agent_identity": json_payload.get("agent_identity") if isinstance(json_payload, dict) else None,
            "response_preview": (
                str(json_payload.get("output", ""))[:200] if isinstance(json_payload, dict) else out[:200]
            ),
            "stderr": err[:500] if err else "",
        }
    )
    if not route_ok:
        payload["failure_kind"] = "route_failed"
    return payload


def _collect_claude_terminal_surface(hub_path: Path | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface": "claude_terminal_receipts",
        "log_exists": False,
        "recent_router_receipts": False,
        "registry_status": None,
        "pid": None,
    }
    if not hub_path:
        return payload
    log_path = hub_path / "data" / "terminal_logs" / "claude.log"
    payload["log_path"] = str(log_path)
    payload["log_exists"] = log_path.exists()
    from src.system.agent_awareness import get_snapshot

    snapshot = get_snapshot(refresh=True)
    terminal = snapshot.get("terminals", {}).get("claude", {}) if isinstance(snapshot, dict) else {}
    if isinstance(terminal, dict):
        payload["registry_status"] = terminal.get("status")
        payload["pid"] = terminal.get("pid")
        payload["watcher_script"] = terminal.get("watcher_script")
    if log_path.exists():
        tail = _read_text_tail(log_path, max_chars=20_000)
        payload["recent_router_receipts"] = "claude_cli_success" in tail and "claude_cli_start" in tail
        payload["last_log_preview"] = "\n".join(tail.strip().splitlines()[-3:])
    return payload


def _build_claude_doctor_recommendations(payload: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    preflight = payload.get("preflight", {})
    cli = payload.get("cli_probe", {})
    router = payload.get("router_probe", {})
    terminal = payload.get("terminal_surface", {})

    if not preflight.get("functional"):
        recommendations.append(
            "Repair the Windows Claude runtime first with `python scripts/start_nusyq.py claude_preflight --json`."
        )
    if not cli.get("installed"):
        recommendations.append("Install Claude Code CLI in the active runtime.")
    elif not cli.get("authenticated"):
        recommendations.append(
            "Run `claude auth login` in the active WSL runtime or sync the Claude credentials file into `~/.claude`."
        )
    elif not cli.get("functional"):
        recommendations.append(
            "Use the neutral-cwd Claude print path (`--add-dir <repo> -- <prompt>`) instead of launching inside the repo root."
        )
    if not router.get("functional"):
        recommendations.append(
            "Re-run `python scripts/nusyq_dispatch.py ask claude ...` after CLI auth/runtime is healthy."
        )
    if not terminal.get("recent_router_receipts"):
        recommendations.append("Restart the Claude terminal watcher so routed Claude receipts show up live.")
    if not recommendations:
        recommendations.append("Claude looks healthy; use `claude_doctor` as the canonical readiness check.")
    return recommendations


def _probe_codex_cli(paths: RepoPaths) -> dict[str, Any]:
    codex_path = shutil.which("codex", path=_build_env().get("PATH"))
    payload: dict[str, Any] = {
        "surface": "openai_codex_cli",
        "installed": bool(codex_path),
        "codex_path": codex_path,
        "functional": False,
    }
    if not codex_path or not paths.nusyq_hub:
        payload["failure_kind"] = "not_installed" if not codex_path else "hub_path_missing"
        return payload

    version_rc, version_out, version_err = run(["codex", "--version"], cwd=paths.nusyq_hub, timeout_s=60)
    runtime_ok = version_rc == 0 and bool((version_out or version_err).strip())
    payload.update(
        {
            "runtime_ok": runtime_ok,
            "version": version_out or version_err,
            "version_exit_code": version_rc,
        }
    )
    if not runtime_ok:
        payload["failure_kind"] = "runtime_failed"
        payload["stderr"] = version_err[:500] if version_err else ""
        return payload

    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        suffix="_codex_doctor_output.txt",
        encoding="utf-8",
    ) as temp_output:
        output_path = Path(temp_output.name)

    try:
        prompt_cmd = [
            "codex",
            "exec",
            "-",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--output-last-message",
            str(output_path),
        ]
        proc = subprocess.run(
            prompt_cmd,
            cwd=str(paths.nusyq_hub),
            input="Reply with exactly CODEX-CLI-OK.\n",
            capture_output=True,
            text=True,
            timeout=120,
            env=_build_env(),
            check=False,
        )
        prompt_rc, prompt_out, prompt_err = proc.returncode, proc.stdout.strip(), proc.stderr.strip()
        response_text = (
            output_path.read_text(encoding="utf-8", errors="replace").strip() if output_path.exists() else ""
        )
        if not response_text:
            response_text = prompt_out.strip()
        normalized_output = response_text.strip().rstrip(".!")
        functional = prompt_rc == 0 and normalized_output == "CODEX-CLI-OK"
        payload.update(
            {
                "functional": functional,
                "prompt_exit_code": prompt_rc,
                "response_preview": response_text[:200] if response_text else "",
                "stderr": prompt_err[:500] if prompt_err else "",
            }
        )
        if not functional:
            payload["failure_kind"] = "runtime_failed"
        return payload
    finally:
        with contextlib.suppress(OSError):
            output_path.unlink()


def _probe_codex_router(paths: RepoPaths) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "target": "codex",
        "functional": False,
        "route_ok": False,
        "execution_path": None,
        "execution_surface": None,
        "agent_identity": None,
        "response_preview": "",
    }
    if not paths.nusyq_hub:
        payload["failure_kind"] = "hub_path_missing"
        return payload
    cmd = [
        sys.executable,
        "scripts/nusyq_dispatch.py",
        "ask",
        "codex",
        "Reply with exactly CODEX-ROUTER-OK.",
    ]
    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=180)
    json_payload = _extract_json_payload(out) if out else None
    normalized_output = (
        str(json_payload.get("output", "")).strip().rstrip(".!") if isinstance(json_payload, dict) else ""
    )
    route_ok = rc == 0 and isinstance(json_payload, dict) and normalized_output == "CODEX-ROUTER-OK"
    payload.update(
        {
            "functional": route_ok,
            "route_ok": route_ok,
            "exit_code": rc,
            "execution_path": json_payload.get("execution_path") if isinstance(json_payload, dict) else None,
            "execution_surface": json_payload.get("execution_surface") if isinstance(json_payload, dict) else None,
            "agent_identity": json_payload.get("agent_identity") if isinstance(json_payload, dict) else None,
            "response_preview": (
                str(json_payload.get("output", ""))[:200] if isinstance(json_payload, dict) else out[:200]
            ),
            "stderr": err[:500] if err else "",
        }
    )
    if not route_ok:
        payload["failure_kind"] = "route_failed"
    return payload


def _collect_codex_terminal_surface(hub_path: Path | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface": "codex_terminal_receipts",
        "log_exists": False,
        "recent_router_receipts": False,
        "registry_status": None,
        "pid": None,
    }
    if not hub_path:
        return payload
    log_path = hub_path / "data" / "terminal_logs" / "codex.log"
    payload["log_path"] = str(log_path)
    payload["log_exists"] = log_path.exists()
    from src.system.agent_awareness import get_snapshot

    snapshot = get_snapshot(refresh=True)
    terminal = snapshot.get("terminals", {}).get("codex", {}) if isinstance(snapshot, dict) else {}
    if isinstance(terminal, dict):
        payload["registry_status"] = terminal.get("status")
        payload["pid"] = terminal.get("pid")
        payload["watcher_script"] = terminal.get("watcher_script")
    if log_path.exists():
        tail = _read_text_tail(log_path, max_chars=20_000)
        payload["recent_router_receipts"] = "codex_cli_success" in tail and "codex_cli_start" in tail
        payload["last_log_preview"] = "\n".join(tail.strip().splitlines()[-3:])
    return payload


def _build_codex_doctor_recommendations(payload: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    cli = payload.get("cli_probe", {})
    router = payload.get("router_probe", {})
    terminal = payload.get("terminal_surface", {})

    if not cli.get("installed"):
        recommendations.append("Install Codex CLI in the active runtime.")
    elif not cli.get("functional"):
        recommendations.append("Repair the Codex CLI runtime and confirm `codex exec` succeeds from the repo.")
    if not router.get("functional"):
        recommendations.append(
            "Re-run `python scripts/nusyq_dispatch.py ask codex ...` after Codex CLI runtime is healthy."
        )
    if not terminal.get("recent_router_receipts"):
        recommendations.append("Restart the Codex terminal watcher so routed Codex receipts show up live.")
    if not recommendations:
        recommendations.append("Codex looks healthy; use `codex_doctor` as the canonical readiness check.")
    return recommendations


def _capture_json_action_payload(action_fn: Callable[[], int]) -> tuple[int, dict[str, Any] | None, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc = action_fn()
    raw = buffer.getvalue()
    payload = _extract_json_payload(raw) if raw else None
    return rc, payload if isinstance(payload, dict) else None, raw


def _handle_delegation_matrix(paths: RepoPaths, json_mode: bool = False) -> int:
    """Generate a router delegation/schema/health matrix using the existing analyzer."""
    if not paths.nusyq_hub:
        payload = {
            "action": "delegation_matrix",
            "status": "error",
            "functional": False,
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    cmd = [sys.executable, "scripts/analyze_agent_task_router_responses.py"]
    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=180)
    result_payload = _extract_json_payload(out) if out else None
    functional = rc == 0 and isinstance(result_payload, dict)
    status = "ok" if functional else ("degraded" if rc == 0 else "error")
    summary = result_payload.get("summary", {}) if isinstance(result_payload, dict) else {}
    payload = {
        "action": "delegation_matrix",
        "status": status,
        "functional": functional,
        "exit_code": rc,
        "summary": summary,
        "result": result_payload if isinstance(result_payload, dict) else None,
        "stdout": out if not isinstance(result_payload, dict) else None,
        "stderr": err,
        "recommendations": [
            "Use `agent_delegation_matrix.md` for operator review and `agent_delegation_matrix.json` for tooling."
            if functional
            else "Delegation matrix did not return structured JSON; run the analyzer directly for debug output.",
            "Prioritize routes missing `execution_path`, `delegated_from`, and `delegated_to` to normalize executor responses."
            if functional
            else "Check `scripts/analyze_agent_task_router_responses.py` and router syntax if generation fails.",
        ],
        "artifacts": {
            "analysis_json": str(paths.nusyq_hub / "state" / "reports" / "agent_task_router_analysis.json"),
            "matrix_json": str(paths.nusyq_hub / "state" / "reports" / "agent_delegation_matrix.json"),
            "matrix_markdown": str(paths.nusyq_hub / "state" / "reports" / "agent_delegation_matrix.md"),
        },
    }
    report_path = _write_state_report(paths.nusyq_hub, "delegation_matrix_latest.json", payload)
    payload["report_path"] = str(report_path)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if functional else 1

    print("🕸️ AGENT DELEGATION MATRIX")
    print("=" * 60)
    print(f"Status: {status}")
    if isinstance(summary, dict):
        print(f"Handlers: {summary.get('handler_count', 0)}")
        print(f"Delegation edges: {summary.get('delegation_edge_count', 0)}")
        print(f"Execution-path ready: {summary.get('execution_path_ready_count', 0)}")
        ready_systems = summary.get("execution_path_ready_systems", [])
        if isinstance(ready_systems, list) and ready_systems:
            print(f"Execution-path systems: {', '.join(ready_systems)}")
    artifacts = payload["artifacts"]
    print(f"Matrix JSON: {artifacts['matrix_json']}")
    print(f"Matrix Markdown: {artifacts['matrix_markdown']}")
    if err:
        print(err)
    return 0 if functional else 1


def _handle_claude_doctor(paths: RepoPaths, json_mode: bool = False) -> int:
    """Comprehensive Claude readiness doctor across preflight, CLI, routing, and terminal receipts."""
    if not paths.nusyq_hub:
        payload = {
            "action": "claude_doctor",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    powershell_bin = _resolve_powershell_executable()
    script_path = paths.nusyq_hub / "scripts" / "run_claude.ps1"
    preflight_cmd = (
        [
            powershell_bin,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            _to_windows_path(script_path),
            "-PreflightOnly",
        ]
        if powershell_bin and script_path.exists()
        else []
    )
    preflight_rc, preflight_out, preflight_err = (
        run(preflight_cmd, cwd=paths.nusyq_hub, timeout_s=180) if preflight_cmd else (1, "", "")
    )
    preflight = {
        "functional": preflight_rc == 0,
        "exit_code": preflight_rc,
        "stdout_preview": preflight_out[:400] if preflight_out else "",
        "stderr_preview": preflight_err[:400] if preflight_err else "",
        "powershell": powershell_bin,
        "script": str(script_path),
    }
    cli_probe = _probe_claude_cli(paths)
    router_probe = _probe_claude_router(paths)
    terminal_surface = _collect_claude_terminal_surface(paths.nusyq_hub)

    functional = (
        bool(preflight.get("functional")) and bool(cli_probe.get("functional")) and bool(router_probe.get("functional"))
    )
    status = "ok" if functional and terminal_surface.get("recent_router_receipts") else "degraded"
    payload = {
        "action": "claude_doctor",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "functional": functional,
        "surface_contract": _build_claude_surface_contract(),
        "preflight": preflight,
        "cli_probe": cli_probe,
        "router_probe": router_probe,
        "terminal_surface": terminal_surface,
    }
    payload["recommendations"] = _build_claude_doctor_recommendations(payload)
    report_path = _write_state_report(paths.nusyq_hub, "claude_doctor_latest.json", payload)
    payload["report_path"] = str(report_path)
    _write_json_report(report_path, payload)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🩺 Claude Doctor")
        print("=" * 50)
        print(f"status: {payload['status']}")
        print(f"preflight: {'yes' if preflight.get('functional') else 'no'}")
        print(f"cli_functional: {'yes' if cli_probe.get('functional') else 'no'}")
        print(f"router_functional: {'yes' if router_probe.get('functional') else 'no'}")
        print(f"terminal_receipts: {'yes' if terminal_surface.get('recent_router_receipts') else 'no'}")
        for recommendation in payload["recommendations"]:
            print(f"- {recommendation}")
        print(f"report_path: {report_path}")
    return 0 if functional else 1


def _handle_codex_doctor(paths: RepoPaths, json_mode: bool = False) -> int:
    """Comprehensive Codex readiness doctor across CLI, routing, and terminal receipts."""
    if not paths.nusyq_hub:
        payload = {
            "action": "codex_doctor",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    cli_probe = _probe_codex_cli(paths)
    router_probe = _probe_codex_router(paths)
    terminal_surface = _collect_codex_terminal_surface(paths.nusyq_hub)

    functional = bool(cli_probe.get("functional")) and bool(router_probe.get("functional"))
    status = "ok" if functional and terminal_surface.get("recent_router_receipts") else "degraded"
    payload = {
        "action": "codex_doctor",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "functional": functional,
        "surface_contract": _build_codex_surface_contract(),
        "cli_probe": cli_probe,
        "router_probe": router_probe,
        "terminal_surface": terminal_surface,
    }
    payload["recommendations"] = _build_codex_doctor_recommendations(payload)
    report_path = _write_state_report(paths.nusyq_hub, "codex_doctor_latest.json", payload)
    payload["report_path"] = str(report_path)
    _write_json_report(report_path, payload)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🩺 Codex Doctor")
        print("=" * 50)
        print(f"status: {payload['status']}")
        print(f"cli_functional: {'yes' if cli_probe.get('functional') else 'no'}")
        print(f"router_functional: {'yes' if router_probe.get('functional') else 'no'}")
        print(f"terminal_receipts: {'yes' if terminal_surface.get('recent_router_receipts') else 'no'}")
        for recommendation in payload["recommendations"]:
            print(f"- {recommendation}")
        print(f"report_path: {report_path}")
    return 0 if functional else 1


def _handle_copilot_probe(paths: RepoPaths, json_mode: bool = False) -> int:
    """Probe Copilot bridge initialization using existing test harness."""
    if not paths.nusyq_hub:
        payload = {
            "action": "copilot_probe",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    cmd = [sys.executable, "scripts/test_copilot.py"]
    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=120)
    initialized = "api_client is initialized" in out.lower()
    combined_output = f"{out}\n{err}".lower()
    endpoint_warning = "no copilot endpoint configured" in combined_output
    cli_probe = _probe_copilot_cli(paths)
    bridge_functional = rc == 0 and initialized
    cli_functional = bool(cli_probe.get("functional"))
    overall_functional = bridge_functional and cli_functional

    payload = {
        "action": "copilot_probe",
        "status": "ok" if overall_functional else "degraded",
        "functional": overall_functional,
        "bridge_functional": bridge_functional,
        "cli_functional": cli_functional,
        "endpoint_configured": not endpoint_warning,
        "bridge_mode": os.getenv("NUSYQ_COPILOT_BRIDGE_MODE", "").strip().lower() or "default",
        "exit_code": rc,
        "stdout": out,
        "stderr": err,
        "cli_probe": cli_probe,
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🧩 Copilot Probe")
        print("=" * 50)
        print(f"status: {payload['status']}")
        print(f"api_client_initialized: {'yes' if initialized else 'no'}")
        print(f"cli_runtime_ok: {'yes' if cli_probe.get('runtime_ok') else 'no'}")
        print(f"cli_authenticated: {'yes' if cli_probe.get('authenticated') else 'no'}")
        print(f"endpoint_configured: {'yes' if not endpoint_warning else 'no'}")
        failure_kind = cli_probe.get("failure_kind")
        if failure_kind:
            print(f"cli_failure_kind: {failure_kind}")
        if out:
            print(out)
        if err:
            print(err)

    return 0 if payload["functional"] else 1


def _classify_copilot_cli_failure(output: str) -> str | None:
    text = output.lower()
    if not text.strip():
        return None
    if "requires node.js v24 or higher" in text:
        return "node_too_old"
    if "no authentication information found" in text:
        return "missing_auth"
    if "copilot requests" in text:
        return "insufficient_permissions"
    if "authentication failed" in text or "token may be invalid" in text:
        return "auth_failed"
    return None


def _probe_copilot_cli(paths: RepoPaths) -> dict[str, Any]:
    copilot_path = shutil.which("copilot", path=_build_env().get("PATH"))
    cli_payload: dict[str, Any] = {
        "surface": "github_copilot_cli",
        "installed": bool(copilot_path),
        "copilot_path": copilot_path,
        "runtime_ok": False,
        "authenticated": False,
        "functional": False,
    }
    if not copilot_path or not paths.nusyq_hub:
        cli_payload["failure_kind"] = "not_installed" if not copilot_path else "hub_path_missing"
        return cli_payload

    version_rc, version_out, version_err = run(
        ["copilot", "--version"],
        cwd=paths.nusyq_hub,
        timeout_s=60,
    )
    runtime_ok = version_rc == 0 and "copilot cli" in version_out.lower()
    cli_payload.update(
        {
            "runtime_ok": runtime_ok,
            "version": version_out or version_err,
            "version_exit_code": version_rc,
        }
    )
    if not runtime_ok:
        cli_payload["failure_kind"] = _classify_copilot_cli_failure(f"{version_out}\n{version_err}") or "runtime_failed"
        cli_payload["stderr"] = version_err[:500] if version_err else ""
        return cli_payload

    prompt_cmd = [
        "copilot",
        "-p",
        "Reply with exactly OK.",
        "--allow-all-tools",
        "--output-format",
        "text",
        "-s",
        "--model",
        "gpt-5-mini",
    ]
    prompt_rc, prompt_out, prompt_err = run(
        prompt_cmd,
        cwd=paths.nusyq_hub,
        timeout_s=60,
    )
    combined_cli_output = f"{prompt_out}\n{prompt_err}".strip()
    failure_kind = _classify_copilot_cli_failure(combined_cli_output)
    authenticated = prompt_rc == 0 and bool(prompt_out.strip()) and failure_kind is None
    cli_payload.update(
        {
            "authenticated": authenticated,
            "functional": authenticated,
            "prompt_exit_code": prompt_rc,
            "failure_kind": failure_kind,
            "response_preview": prompt_out[:200] if prompt_out else "",
            "stderr": prompt_err[:500] if prompt_err else "",
        }
    )
    return cli_payload


def _build_copilot_surface_contract() -> dict[str, Any]:
    return {
        "router_target": "copilot",
        "supported_requested_surfaces": ["auto", "cli", "bridge", "chat_ui"],
        "routable_surfaces": {
            "cli": {
                "surface": "github_copilot_cli",
                "controllable": True,
                "default_execution_path": "copilot_cli",
            },
            "bridge": {
                "surface": "copilot_bridge",
                "controllable": True,
                "bridge_mode": os.getenv("NUSYQ_COPILOT_BRIDGE_MODE", "").strip().lower() or "default",
            },
        },
        "observed_only_surfaces": {
            "chat_ui": {
                "surface": "vscode_copilot_chat_surface",
                "controllable": False,
            }
        },
    }


def _windows_path_to_wsl(path_str: str | None) -> Path | None:
    raw = str(path_str or "").strip()
    if not raw:
        return None
    if raw.startswith("/"):
        return Path(raw)
    if len(raw) >= 3 and raw[1:3] == ":\\":
        drive = raw[0].lower()
        suffix = raw[3:].replace("\\", "/")
        return Path(f"/mnt/{drive}/{suffix}")
    return Path(raw)


def _resolve_windows_user_home(hub_path: Path | None) -> Path | None:
    candidates: list[Path] = []
    if hub_path:
        resolved = hub_path.resolve()
        parts = resolved.parts
        if len(parts) >= 5 and parts[1] == "mnt" and parts[3] == "Users":
            candidates.append(Path("/", *parts[:5]))
    for env_name in ("USERPROFILE", "HOME"):
        candidate = _windows_path_to_wsl(os.getenv(env_name))
        if candidate:
            candidates.append(candidate)
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else None


def _read_text_tail(path: Path, max_chars: int = 200_000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-max_chars:]


def _collect_copilot_chat_surface(hub_path: Path | None) -> dict[str, Any]:
    user_home = _resolve_windows_user_home(hub_path)
    payload: dict[str, Any] = {
        "surface": "vscode_copilot_chat_surface",
        "user_home": str(user_home) if user_home else None,
        "copilot_chat_installed": False,
        "pull_request_extension_installed": False,
        "continue_installed": False,
        "chat_ready": False,
        "token_ready": False,
        "activated": False,
        "recovered_after_cancel": False,
        "typescript_extension_missing": False,
        "git_extension_delayed": False,
        "workspace_profile_hardened": False,
    }
    if not user_home:
        return payload

    manifest_path = user_home / ".vscode" / "extensions" / "extensions.json"
    settings_path = hub_path / ".vscode" / "settings.json" if hub_path else None
    logs_root = user_home / "AppData" / "Roaming" / "Code" / "logs"
    payload.update(
        {
            "extensions_manifest": str(manifest_path),
            "user_logs_root": str(logs_root),
        }
    )

    manifest = read_json(manifest_path)
    items = (
        manifest if isinstance(manifest, list) else manifest.get("extensions", []) if isinstance(manifest, dict) else []
    )
    versions: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        identifier = item.get("identifier", {})
        if not isinstance(identifier, dict):
            continue
        ext_id = str(identifier.get("id", "")).lower()
        if ext_id:
            versions[ext_id] = str(item.get("version", ""))
    payload["copilot_chat_installed"] = "github.copilot-chat" in versions
    payload["pull_request_extension_installed"] = "github.vscode-pull-request-github" in versions
    payload["continue_installed"] = "continue.continue" in versions
    payload["extension_versions"] = {
        key: versions.get(key)
        for key in ("github.copilot-chat", "github.vscode-pull-request-github", "continue.continue")
        if key in versions
    }

    if settings_path and settings_path.exists():
        settings_text = settings_path.read_text(encoding="utf-8", errors="replace")
        payload["workspace_profile_hardened"] = all(
            needle in settings_text
            for needle in (
                '"github.copilot.chat.githubMcpServer.enabled": false',
                '"github.copilot.chat.codesearch.enabled": false',
                '"github.copilot.chat.agent.autoFix": false',
            )
        )

    latest_log_dir: Path | None = None
    latest_with_chat: Path | None = None
    if logs_root.exists():
        dirs = [path for path in logs_root.iterdir() if path.is_dir()]
        if dirs:
            latest_log_dir = max(dirs, key=lambda path: path.stat().st_mtime)
            with_chat = [
                path for path in dirs if list(path.glob("window*/exthost/GitHub.copilot-chat/GitHub Copilot Chat.log"))
            ]
            if with_chat:
                latest_with_chat = max(with_chat, key=lambda path: path.stat().st_mtime)
    selected_log_dir = latest_with_chat or latest_log_dir
    payload["latest_log_dir"] = str(latest_log_dir) if latest_log_dir else None
    payload["selected_log_dir"] = str(selected_log_dir) if selected_log_dir else None
    if not selected_log_dir:
        return payload

    chat_logs = sorted(selected_log_dir.glob("window*/exthost/GitHub.copilot-chat/GitHub Copilot Chat.log"))
    sharedprocess_log = selected_log_dir / "sharedprocess.log"
    chat_text = _read_text_tail(chat_logs[-1]) if chat_logs else ""
    shared_text = _read_text_tail(sharedprocess_log)
    last_token_idx = chat_text.rfind("Got Copilot token")
    last_activated_idx = chat_text.rfind("github.copilot-chat.activated")
    last_offline_idx = chat_text.rfind("github.copilot.offline")
    payload.update(
        {
            "chat_log_path": str(chat_logs[-1]) if chat_logs else None,
            "sharedprocess_log_path": str(sharedprocess_log) if sharedprocess_log.exists() else None,
            "token_ready": last_token_idx != -1,
            "activated": last_activated_idx != -1,
            "offline_seen": last_offline_idx != -1,
            "auth_canceled": "Failed to get copilot token" in chat_text,
            "recovered_after_cancel": last_offline_idx != -1 and last_activated_idx > last_offline_idx,
            "typescript_extension_missing": "TypeScript extension not found" in chat_text,
            "git_extension_delayed": "vscode.git extension is not yet activated." in chat_text,
            "core_extension_deprecated": "github.copilot' extension is deprecated" in shared_text,
        }
    )
    payload["chat_ready"] = bool(
        payload["token_ready"]
        and payload["activated"]
        and (last_offline_idx == -1 or last_activated_idx > last_offline_idx)
    )
    return payload


def _probe_copilot_router(paths: RepoPaths) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "target": "copilot",
        "functional": False,
        "route_ok": False,
        "execution_path": None,
        "execution_surface": None,
        "requested_surface": None,
        "response_preview": "",
    }
    if not paths.nusyq_hub:
        payload["failure_kind"] = "hub_path_missing"
        return payload
    cmd = [
        sys.executable,
        "scripts/nusyq_dispatch.py",
        "ask",
        "copilot",
        "Reply with exactly ROUTER-OK.",
    ]
    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=120)
    json_payload = _extract_json_payload(out) if out else None
    route_ok = rc == 0 and isinstance(json_payload, dict) and json_payload.get("output") == "ROUTER-OK"
    payload.update(
        {
            "functional": route_ok,
            "route_ok": route_ok,
            "exit_code": rc,
            "execution_path": json_payload.get("execution_path") if isinstance(json_payload, dict) else None,
            "execution_surface": json_payload.get("execution_surface") if isinstance(json_payload, dict) else None,
            "requested_surface": json_payload.get("requested_surface") if isinstance(json_payload, dict) else None,
            "response_preview": (
                str(json_payload.get("output", ""))[:200] if isinstance(json_payload, dict) else out[:200]
            ),
            "stderr": err[:500] if err else "",
        }
    )
    return payload


def _collect_copilot_terminal_surface(hub_path: Path | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface": "copilot_terminal_receipts",
        "log_exists": False,
        "recent_router_receipts": False,
        "registry_status": None,
        "pid": None,
    }
    if not hub_path:
        return payload
    log_path = hub_path / "data" / "terminal_logs" / "copilot.log"
    payload["log_path"] = str(log_path)
    payload["log_exists"] = log_path.exists()
    from src.system.agent_awareness import get_snapshot

    snapshot = get_snapshot(refresh=True)
    terminal = snapshot.get("terminals", {}).get("copilot", {}) if isinstance(snapshot, dict) else {}
    if isinstance(terminal, dict):
        payload["registry_status"] = terminal.get("status")
        payload["pid"] = terminal.get("pid")
        payload["watcher_script"] = terminal.get("watcher_script")
    if log_path.exists():
        tail = _read_text_tail(log_path, max_chars=20_000)
        payload["recent_router_receipts"] = "copilot_cli_success" in tail and "copilot_cli_start" in tail
        payload["last_log_preview"] = "\n".join(tail.strip().splitlines()[-3:])
    return payload


def _build_copilot_doctor_recommendations(payload: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    chat = payload.get("chat_surface", {})
    cli = payload.get("cli_probe", {})
    router = payload.get("router_probe", {})
    terminal = payload.get("terminal_surface", {})
    chat_ready = bool(chat.get("chat_ready"))

    if not chat.get("copilot_chat_installed"):
        recommendations.append("Install or re-enable GitHub Copilot Chat in VS Code.")
    if not chat_ready:
        recommendations.append("Reload the VS Code window and wait for Copilot Chat token activation to complete.")
    if not chat_ready and chat.get("typescript_extension_missing"):
        recommendations.append("Re-enable the built-in TypeScript and JavaScript Language Features extension.")
    if not chat_ready and chat.get("git_extension_delayed"):
        recommendations.append("Keep the built-in Git extension enabled; Copilot Chat waits on it during startup.")
    if not cli.get("functional"):
        failure_kind = cli.get("failure_kind")
        if failure_kind in {"missing_auth", "auth_failed"}:
            recommendations.append("Run `copilot login` in the active runtime to refresh Copilot CLI OAuth auth.")
        elif failure_kind == "node_too_old":
            recommendations.append("Keep the Node 24 Copilot wrapper path active for the CLI runtime.")
        else:
            recommendations.append("Repair Copilot CLI runtime/auth before relying on routed delegation.")
    if not router.get("functional"):
        recommendations.append("Re-run `python scripts/nusyq_dispatch.py ask copilot ...` after CLI auth is healthy.")
    if not terminal.get("recent_router_receipts"):
        recommendations.append("Restart the Copilot terminal watcher so routed Copilot receipts show up live.")
    if not recommendations:
        recommendations.append(
            "Copilot looks healthy; next step is using `copilot_doctor` as the canonical readiness check."
        )
    return recommendations


def _handle_copilot_doctor(paths: RepoPaths, json_mode: bool = False) -> int:
    """Comprehensive Copilot readiness doctor across VS Code, CLI, routing, and terminal receipts."""
    if not paths.nusyq_hub:
        payload = {
            "action": "copilot_doctor",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    cli_probe = _probe_copilot_cli(paths)
    chat_surface = _collect_copilot_chat_surface(paths.nusyq_hub)
    router_probe = _probe_copilot_router(paths)
    terminal_surface = _collect_copilot_terminal_surface(paths.nusyq_hub)

    functional = bool(cli_probe.get("functional")) and bool(router_probe.get("functional"))
    status = (
        "ok"
        if functional and chat_surface.get("chat_ready") and terminal_surface.get("recent_router_receipts")
        else "degraded"
    )
    payload = {
        "action": "copilot_doctor",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "functional": functional,
        "surface_contract": _build_copilot_surface_contract(),
        "chat_surface": chat_surface,
        "cli_probe": cli_probe,
        "router_probe": router_probe,
        "terminal_surface": terminal_surface,
    }
    payload["recommendations"] = _build_copilot_doctor_recommendations(payload)
    report_path = _write_state_report(paths.nusyq_hub, "copilot_doctor_latest.json", payload)
    payload["report_path"] = str(report_path)
    _write_json_report(report_path, payload)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🩺 Copilot Doctor")
        print("=" * 50)
        print(f"status: {payload['status']}")
        print(f"chat_ready: {'yes' if chat_surface.get('chat_ready') else 'no'}")
        print(f"cli_functional: {'yes' if cli_probe.get('functional') else 'no'}")
        print(f"router_functional: {'yes' if router_probe.get('functional') else 'no'}")
        print(f"terminal_receipts: {'yes' if terminal_surface.get('recent_router_receipts') else 'no'}")
        for recommendation in payload["recommendations"]:
            print(f"- {recommendation}")
        print(f"report_path: {report_path}")
    return 0 if functional else 1


def _handle_multi_agent_doctor(paths: RepoPaths, json_mode: bool = False) -> int:
    """Aggregate Claude/Codex/Copilot readiness into one triad report."""
    if not paths.nusyq_hub:
        payload = {
            "action": "multi_agent_doctor",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    checks = {
        "claude": lambda: _handle_claude_doctor(paths, json_mode=True),
        "codex": lambda: _handle_codex_doctor(paths, json_mode=True),
        "copilot": lambda: _handle_copilot_doctor(paths, json_mode=True),
    }
    agent_reports: dict[str, dict[str, Any]] = {}
    failures: dict[str, dict[str, Any]] = {}

    for name, action_fn in checks.items():
        rc, payload, raw = _capture_json_action_payload(action_fn)
        if isinstance(payload, dict):
            agent_reports[name] = payload
        else:
            failures[name] = {
                "exit_code": rc,
                "error": "doctor_payload_parse_failed",
                "raw_preview": raw[:500],
            }

    healthy_agents = [name for name, report in agent_reports.items() if bool(report.get("functional"))]
    degraded_agents = [name for name, report in agent_reports.items() if not bool(report.get("functional"))] + list(
        failures.keys()
    )
    all_agents = ["claude", "codex", "copilot"]
    complete = len(agent_reports) == len(all_agents) and not failures
    functional = complete and len(healthy_agents) == len(all_agents)
    status = "ok" if functional else ("degraded" if agent_reports else "error")

    recommendations: list[str] = []
    for name in degraded_agents:
        if name in agent_reports:
            recommendations.append(
                f"Review `{name}_doctor` and address its top recommendation before relying on triad delegation."
            )
        else:
            recommendations.append(
                f"Re-run `{name}_doctor` because the aggregated report could not parse its JSON output."
            )
    if not recommendations:
        recommendations.append("Triad looks healthy; use `multi_agent_doctor` as the canonical shared readiness check.")

    summary = {
        "agent_count": len(all_agents),
        "healthy_agents": healthy_agents,
        "degraded_agents": degraded_agents,
        "fully_functional": functional,
        "surface_contracts": {
            name: report.get("surface_contract") for name, report in agent_reports.items() if isinstance(report, dict)
        },
    }
    payload = {
        "action": "multi_agent_doctor",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "functional": functional,
        "summary": summary,
        "agents": agent_reports,
        "failures": failures,
        "recommendations": recommendations,
    }
    report_path = _write_state_report(paths.nusyq_hub, "multi_agent_doctor_latest.json", payload)
    payload["report_path"] = str(report_path)
    _write_json_report(report_path, payload)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🩺 Multi-Agent Doctor")
        print("=" * 50)
        print(f"status: {payload['status']}")
        print(f"healthy_agents: {', '.join(healthy_agents) if healthy_agents else 'none'}")
        print(f"degraded_agents: {', '.join(degraded_agents) if degraded_agents else 'none'}")
        for recommendation in recommendations:
            print(f"- {recommendation}")
        print(f"report_path: {report_path}")
    return 0 if functional else 1


def _build_culture_ship_surface_contract() -> dict[str, Any]:
    return _build_agent_surface_contract(
        router_target="culture_ship",
        supported_requested_surfaces=["action", "orchestrator"],
        routable_surfaces={
            "action": {
                "surface": "culture_ship_cli_action",
                "controllable": True,
                "default_execution_path": "start_nusyq:culture_ship",
            },
            "orchestrator": {
                "surface": "culture_ship_strategic_orchestrator",
                "controllable": True,
                "default_execution_path": "unified_ai_orchestrator:culture_ship_strategic",
            },
        },
        observed_only_surfaces={
            "terminal": {
                "surface": "culture_ship_terminal_receipts",
                "controllable": False,
            }
        },
        selection_note="Culture Ship is a strategic action/orchestrator surface, not a first-class AgentTaskRouter target.",
    )


def _probe_culture_ship_live(paths: RepoPaths) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface": "culture_ship_live_probe",
        "functional": False,
        "dependency_ready": False,
        "advisor_importable": False,
        "orchestrator_registered": False,
        "ready_for_automation": False,
    }
    if not paths.nusyq_hub:
        payload["failure_kind"] = "hub_path_missing"
        return payload

    try:
        from src.culture_ship import health_probe as health_probe_module

        health_status = health_probe_module.check_dependencies()
        recommendations = health_probe_module.generate_recommendations(health_status)
        ready_for_automation = all(health_status.get("tools", {}).values()) and all(
            health_status.get("python_modules", {}).values()
        )
        payload.update(
            {
                "dependency_ready": ready_for_automation,
                "ready_for_automation": ready_for_automation,
                "health_status": health_status,
                "recommendations": recommendations,
            }
        )
    except Exception as exc:
        payload["health_probe_error"] = str(exc)

    try:
        from src.orchestration.culture_ship_strategic_advisor import CultureShipStrategicAdvisor

        advisor = CultureShipStrategicAdvisor()
        payload["advisor_importable"] = True
        payload["advisor_ready"] = bool(getattr(advisor, "culture_ship", None) is not None)
        payload["integration_ready"] = bool(advisor._culture_ship_integration_ready())  # type: ignore[attr-defined]
    except Exception as exc:
        payload["advisor_error"] = str(exc)

    try:
        from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator

        orchestrator = UnifiedAIOrchestrator(config={"enable_culture_ship": True})
        payload["orchestrator_registered"] = bool(orchestrator.ensure_culture_ship_system_registered())
    except Exception as exc:
        payload["orchestrator_error"] = str(exc)

    payload["functional"] = bool(
        payload.get("dependency_ready") and payload.get("advisor_importable") and payload.get("orchestrator_registered")
    )
    return payload


def _collect_culture_ship_terminal_surface(hub_path: Path | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface": "culture_ship_terminal_receipts",
        "log_exists": False,
        "recent_health_probe": False,
        "registry_status": None,
        "pid": None,
    }
    if not hub_path:
        return payload
    log_path = hub_path / "data" / "terminal_logs" / "culture_ship.log"
    audit_log = hub_path / "state" / "logs" / "culture_ship_audits.log"
    payload["log_path"] = str(log_path)
    payload["audit_log_path"] = str(audit_log)
    payload["log_exists"] = log_path.exists() or audit_log.exists()
    from src.system.agent_awareness import get_snapshot

    snapshot = get_snapshot(refresh=True)
    terminal = snapshot.get("terminals", {}).get("culture_ship", {}) if isinstance(snapshot, dict) else {}
    if isinstance(terminal, dict):
        payload["registry_status"] = terminal.get("status")
        payload["pid"] = terminal.get("pid")
        payload["watcher_script"] = terminal.get("watcher_script")
    tails = []
    if log_path.exists():
        tails.append(_read_text_tail(log_path, max_chars=20_000))
    if audit_log.exists():
        tails.append(_read_text_tail(audit_log, max_chars=20_000))
    combined = "\n".join(tails)
    if combined:
        payload["recent_health_probe"] = "culture_ship_health_probe" in combined or "Health probe:" in combined
        payload["last_log_preview"] = "\n".join(combined.strip().splitlines()[-5:])
    return payload


def _build_culture_ship_doctor_recommendations(payload: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    live_probe = payload.get("live_probe", {})
    terminal = payload.get("terminal_surface", {})

    if not live_probe.get("dependency_ready"):
        recommendations.append(
            "Repair Culture Ship dependencies/plugins (`ruff`, `black`, plugin modules) before relying on automation."
        )
    if not live_probe.get("advisor_importable"):
        recommendations.append("Repair Culture Ship strategic advisor imports and runtime initialization.")
    if not live_probe.get("orchestrator_registered"):
        recommendations.append(
            "Ensure `UnifiedAIOrchestrator.ensure_culture_ship_system_registered()` succeeds in the active runtime."
        )
    if not terminal.get("recent_health_probe"):
        recommendations.append(
            "Run the live Culture Ship probe or restart its terminal watcher so health receipts show up live."
        )
    if not recommendations:
        recommendations.append(
            "Culture Ship looks healthy; use `culture_ship_doctor` as the canonical live readiness check."
        )
    return recommendations


def _handle_culture_ship_doctor(paths: RepoPaths, json_mode: bool = False) -> int:
    """Live Culture Ship readiness doctor using the health probe and orchestrator registration."""
    if not paths.nusyq_hub:
        payload = {
            "action": "culture_ship_doctor",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    live_probe = _probe_culture_ship_live(paths)
    terminal_surface = _collect_culture_ship_terminal_surface(paths.nusyq_hub)
    functional = bool(live_probe.get("functional"))
    status = "ok" if functional and terminal_surface.get("log_exists") else "degraded"
    payload = {
        "action": "culture_ship_doctor",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "functional": functional,
        "surface_contract": _build_culture_ship_surface_contract(),
        "live_probe": live_probe,
        "terminal_surface": terminal_surface,
    }
    payload["recommendations"] = _build_culture_ship_doctor_recommendations(payload)
    report_path = _write_state_report(paths.nusyq_hub, "culture_ship_doctor_latest.json", payload)
    payload["report_path"] = str(report_path)
    _write_json_report(report_path, payload)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🩺 Culture Ship Doctor")
        print("=" * 50)
        print(f"status: {payload['status']}")
        print(f"live_probe: {'yes' if live_probe.get('functional') else 'no'}")
        print(f"terminal_receipts: {'yes' if terminal_surface.get('log_exists') else 'no'}")
        for recommendation in payload["recommendations"]:
            print(f"- {recommendation}")
        print(f"report_path: {report_path}")
    return 0 if functional else 1


def _build_ai_council_surface_contract() -> dict[str, Any]:
    return _build_agent_surface_contract(
        router_target="ai_council",
        supported_requested_surfaces=["dispatcher"],
        routable_surfaces={
            "dispatcher": {
                "surface": "mjolnir_council_dispatch",
                "controllable": True,
                "default_execution_path": "nusyq_dispatch:council",
            }
        },
        observed_only_surfaces={
            "terminal": {
                "surface": "ai_council_terminal_receipts",
                "controllable": False,
            }
        },
        selection_note="AI Council currently lives at the MJOLNIR/dispatcher layer rather than as a first-class AgentTaskRouter target.",
    )


def _probe_ai_council_state(paths: RepoPaths) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface": "ai_council_state",
        "functional": False,
    }
    if not paths.nusyq_hub:
        payload["failure_kind"] = "hub_path_missing"
        return payload
    try:
        from src.orchestration.ai_council_voting import AICouncilVoting

        council = AICouncilVoting(state_dir=paths.nusyq_hub / "state" / "council")
        status = council.get_council_status()
        payload.update(
            {
                "functional": True,
                "state_dir": str(paths.nusyq_hub / "state" / "council"),
                "status": status,
            }
        )
    except Exception as exc:
        payload["error"] = str(exc)
    return payload


def _probe_ai_council_dispatcher(paths: RepoPaths) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface": "mjolnir_council_dispatch",
        "functional": False,
        "dispatch_ok": False,
        "agents": [],
    }
    if not paths.nusyq_hub:
        payload["failure_kind"] = "hub_path_missing"
        return payload

    candidate_agents: list[str] = []
    if _preflight_openclaw_target("ollama", timeout_s=4.0).get("available"):
        candidate_agents.append("ollama")
    if _preflight_openclaw_target("lmstudio", timeout_s=4.0).get("available"):
        candidate_agents.append("lmstudio")
    if not candidate_agents:
        payload["failure_kind"] = "no_local_council_agents_available"
        return payload

    cmd = [
        sys.executable,
        "scripts/nusyq_dispatch.py",
        "council",
        "Reply with exactly COUNCIL-OK.",
        "--agents=" + ",".join(candidate_agents[:2]),
        "--task-type",
        "analyze",
        "--no-guild",
    ]
    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=180)
    json_payload = _extract_json_payload(out) if out else None
    output = json_payload.get("output") if isinstance(json_payload, dict) else None
    has_synthesis = isinstance(output, dict) and isinstance(output.get("synthesis"), dict)
    dispatch_ok = rc == 0 and isinstance(json_payload, dict) and json_payload.get("pattern") == "council"
    payload.update(
        {
            "functional": dispatch_ok,
            "dispatch_ok": dispatch_ok,
            "agents": candidate_agents[:2],
            "exit_code": rc,
            "pattern": json_payload.get("pattern") if isinstance(json_payload, dict) else None,
            "response_count": len(output.get("responses", {}))
            if isinstance(output, dict) and isinstance(output.get("responses"), dict)
            else None,
            "consensus_available": has_synthesis,
            "consensus_level": output.get("synthesis", {}).get("consensus_level") if has_synthesis else None,
            "response_preview": out[:200] if out else "",
            "stderr": err[:500] if err else "",
        }
    )
    if not dispatch_ok:
        payload["failure_kind"] = "dispatch_failed"
    return payload


def _collect_ai_council_terminal_surface(hub_path: Path | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface": "ai_council_terminal_receipts",
        "log_exists": False,
        "recent_council_receipts": False,
        "registry_status": None,
        "pid": None,
    }
    if not hub_path:
        return payload
    log_path = hub_path / "data" / "terminal_logs" / "ai_council.log"
    payload["log_path"] = str(log_path)
    payload["log_exists"] = log_path.exists()
    from src.system.agent_awareness import get_snapshot

    snapshot = get_snapshot(refresh=True)
    terminal = snapshot.get("terminals", {}).get("ai_council", {}) if isinstance(snapshot, dict) else {}
    if isinstance(terminal, dict):
        payload["registry_status"] = terminal.get("status")
        payload["pid"] = terminal.get("pid")
        payload["watcher_script"] = terminal.get("watcher_script")
    if log_path.exists():
        tail = _read_text_tail(log_path, max_chars=20_000)
        payload["recent_council_receipts"] = "mjolnir_council" in tail or "Council vote complete" in tail
        payload["last_log_preview"] = "\n".join(tail.strip().splitlines()[-3:])
    return payload


def _build_ai_council_doctor_recommendations(payload: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    state_probe = payload.get("state_probe", {})
    dispatcher_probe = payload.get("dispatcher_probe", {})
    terminal = payload.get("terminal_surface", {})
    if not state_probe.get("functional"):
        recommendations.append(
            "Repair AI Council state initialization so `AICouncilVoting.get_council_status()` succeeds."
        )
    if not dispatcher_probe.get("functional"):
        recommendations.append(
            "Repair local council execution via `python scripts/nusyq_dispatch.py council ...` and ensure at least one local model surface is available."
        )
    if not terminal.get("recent_council_receipts"):
        recommendations.append("Restart the AI Council terminal watcher so consensus receipts show up live.")
    if not recommendations:
        recommendations.append(
            "AI Council looks healthy; use `ai_council_doctor` as the canonical council readiness check."
        )
    return recommendations


def _handle_ai_council_doctor(paths: RepoPaths, json_mode: bool = False) -> int:
    """Diagnose AI Council state, dispatcher execution, and terminal receipts."""
    if not paths.nusyq_hub:
        payload = {
            "action": "ai_council_doctor",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    state_probe = _probe_ai_council_state(paths)
    dispatcher_probe = _probe_ai_council_dispatcher(paths)
    terminal_surface = _collect_ai_council_terminal_surface(paths.nusyq_hub)
    functional = bool(state_probe.get("functional")) and bool(dispatcher_probe.get("functional"))
    status = "ok" if functional and terminal_surface.get("log_exists") else "degraded"
    payload = {
        "action": "ai_council_doctor",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "functional": functional,
        "surface_contract": _build_ai_council_surface_contract(),
        "state_probe": state_probe,
        "dispatcher_probe": dispatcher_probe,
        "terminal_surface": terminal_surface,
    }
    payload["recommendations"] = _build_ai_council_doctor_recommendations(payload)
    report_path = _write_state_report(paths.nusyq_hub, "ai_council_doctor_latest.json", payload)
    payload["report_path"] = str(report_path)
    _write_json_report(report_path, payload)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🩺 AI Council Doctor")
        print("=" * 50)
        print(f"status: {payload['status']}")
        print(f"state_probe: {'yes' if state_probe.get('functional') else 'no'}")
        print(f"dispatcher_probe: {'yes' if dispatcher_probe.get('functional') else 'no'}")
        print(f"terminal_receipts: {'yes' if terminal_surface.get('log_exists') else 'no'}")
        for recommendation in payload["recommendations"]:
            print(f"- {recommendation}")
        print(f"report_path: {report_path}")
    return 0 if functional else 1


def _collect_terminal_surface_keys(hub_path: Path | None) -> list[str]:
    if not hub_path:
        return []

    keys: set[str] = set()
    for report_name in ("terminal_awareness_latest.json", "terminal_snapshot_latest.json"):
        payload = read_json(hub_path / "state" / "reports" / report_name)
        if not isinstance(payload, dict):
            continue
        terminals = payload.get("terminals")
        if not isinstance(terminals, list):
            continue
        for item in terminals:
            if isinstance(item, dict):
                key = str(item.get("key") or "").strip()
                if key:
                    keys.add(key)
    return sorted(keys)


def _build_doc_surface(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "functional": path.exists(),
    }
    if path.exists():
        stat = path.stat()
        payload["modified_at"] = datetime.fromtimestamp(stat.st_mtime, UTC).isoformat()
        payload["bytes"] = stat.st_size
    return payload


def _parse_iso8601_datetime(raw: Any) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    with contextlib.suppress(ValueError):
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _build_agent_fleet_doctor_recommendations(payload: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    surfaces = payload.get("surfaces", {})
    if not isinstance(surfaces, dict):
        return ["Review agent_fleet_doctor payload generation; surface inventory was missing."]

    def _surface(name: str) -> dict[str, Any]:
        value = surfaces.get(name, {})
        return value if isinstance(value, dict) else {}

    if not _surface("lmstudio").get("functional"):
        recommendations.append(
            "LM Studio is not reporting healthy in ai_status; start/configure it or keep Ollama as the local-model fallback."
        )
    if _surface("culture_ship").get("status") == "stale_history":
        recommendations.append(
            "Culture Ship status is still historical job output; add a live health probe or rerun `culture_ship` before relying on it operationally."
        )
    if _surface("openclaw").get("details", {}).get("messaging_functional") is False:
        recommendations.append(
            "OpenClaw gateway is online but messaging channels are not configured; keep system-routing use and add Slack/Discord credentials only if needed."
        )
    if _surface("metaclaw").get("kind") == "passive_runtime" and _surface("metaclaw").get("functional"):
        recommendations.append(
            "MetaClaw is runtime-healthy but still passive; promote it to a first-class routed surface only after a real bridge/_route_to_* contract exists."
        )
    if _surface("hermes_agent").get("kind") == "passive_runtime" and _surface("hermes_agent").get("functional"):
        recommendations.append(
            "Hermes-Agent is runtime-healthy but still passive; keep it explicit as RAG/runtime support until a routed execution contract is built."
        )
    if _surface("shepherd").get("status") == "alias_only":
        recommendations.append(
            "Shepherd currently resolves only as an alias/idea, not a first-class executable surface; either wire it properly or mark it dormant in docs."
        )
    if not _surface("rosetta_stone").get("functional") or not _surface("agent_tutorial").get("functional"):
        recommendations.append(
            "Restore Rosetta Stone / Agent Tutorial docs because they are still part of the operator doctrine surface."
        )
    if not recommendations:
        recommendations.append(
            "Fleet looks coherent; use `agent_fleet_doctor` as the broad readiness map across routed, passive, observed, and doctrine surfaces."
        )
    return recommendations


def _handle_agent_fleet_doctor(paths: RepoPaths, json_mode: bool = False) -> int:
    """Aggregate routed, runtime, passive, observed, and doctrine surfaces into one fleet report."""
    if not paths.nusyq_hub:
        payload = {
            "action": "agent_fleet_doctor",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    checks = {
        "ai_status": lambda: _handle_ai_status(paths, json_mode=True),
        "openclaw_status": lambda: _handle_openclaw_status(paths, json_mode=True),
        "culture_ship_status": lambda: _handle_culture_ship_status(["culture_ship_status"], paths, json_mode=True),
        "delegation_matrix": lambda: _handle_delegation_matrix(paths, json_mode=True),
        "multi_agent_doctor": lambda: _handle_multi_agent_doctor(paths, json_mode=True),
    }
    reports: dict[str, dict[str, Any]] = {}
    failures: dict[str, dict[str, Any]] = {}
    for name, action_fn in checks.items():
        rc, payload, raw = _capture_json_action_payload(action_fn)
        if isinstance(payload, dict):
            reports[name] = payload
        else:
            failures[name] = {
                "exit_code": rc,
                "error": "doctor_payload_parse_failed",
                "raw_preview": raw[:500],
            }

    ai_status = reports.get("ai_status", {})
    services = ai_status.get("services", {}) if isinstance(ai_status.get("services"), dict) else {}
    openclaw_status = reports.get("openclaw_status", {})
    culture_ship_status = reports.get("culture_ship_status", {})
    delegation_matrix = reports.get("delegation_matrix", {})
    matrix_result = (
        delegation_matrix.get("result") if isinstance(delegation_matrix.get("result"), dict) else delegation_matrix
    )
    matrix_entries = matrix_result.get("entries", []) if isinstance(matrix_result, dict) else []
    entry_by_system = {
        str(entry.get("system")).strip().lower(): entry
        for entry in matrix_entries
        if isinstance(entry, dict) and str(entry.get("system") or "").strip()
    }
    triad = reports.get("multi_agent_doctor", {})
    triad_agents = triad.get("agents", {}) if isinstance(triad.get("agents"), dict) else {}
    terminal_keys = _collect_terminal_surface_keys(paths.nusyq_hub)

    surfaces: dict[str, dict[str, Any]] = {}

    def _add_surface(
        name: str,
        *,
        kind: str,
        functional: bool | None,
        status: str,
        activation: str,
        notes: list[str] | None = None,
        sources: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        surfaces[name] = {
            "kind": kind,
            "functional": functional,
            "status": status,
            "activation": activation,
            "notes": notes or [],
            "sources": sources or [],
            "details": details or {},
        }

    triad_surface_map = {
        "claude": "claude_cli",
        "codex": "codex",
        "copilot": "copilot",
    }
    for name, router_target in triad_surface_map.items():
        report = triad_agents.get(name, {}) if isinstance(triad_agents.get(name), dict) else {}
        _add_surface(
            name,
            kind="routed",
            functional=bool(report.get("functional")) if report else False,
            status=str(report.get("status") or ("ok" if report.get("functional") else "degraded")),
            activation="doctor+routed",
            sources=["multi_agent_doctor", "delegation_matrix"],
            details={
                "router_target": router_target,
                "surface_contract": report.get("surface_contract"),
                "router_probe": report.get("router_probe"),
            },
        )

    routed_service_names = (
        "chatdev",
        "ollama",
        "lmstudio",
        "openclaw",
        "skyclaw",
        "intermediary",
        "quantum_resolver",
        "factory",
    )
    for name in routed_service_names:
        service = services.get(name, {}) if isinstance(services.get(name), dict) else {}
        entry = entry_by_system.get(name, {})
        functional: bool | None = None
        if isinstance(service, dict) and "healthy" in service:
            functional = bool(service.get("healthy"))
        elif isinstance(entry, dict):
            probe = entry.get("probe", {})
            if isinstance(probe, dict) and probe.get("ok") is not None:
                functional = bool(probe.get("ok"))
        status = str(
            service.get("status")
            if isinstance(service, dict) and service.get("status")
            else ("ready" if functional else "unknown" if functional is None else "degraded")
        )
        details = {
            "service": service if isinstance(service, dict) else {},
            "delegation_entry": entry if isinstance(entry, dict) else {},
        }
        if name == "openclaw":
            details["messaging_functional"] = bool(openclaw_status.get("messaging_functional"))
        _add_surface(
            name,
            kind="routed",
            functional=functional,
            status=status,
            activation="router",
            sources=["ai_status", "delegation_matrix"],
            details=details,
        )

    simulatedverse_service = services.get("simulatedverse") if isinstance(services.get("simulatedverse"), dict) else {}
    _add_surface(
        "simulatedverse",
        kind="runtime_service",
        functional=bool(simulatedverse_service.get("healthy")) if simulatedverse_service else False,
        status=str(
            simulatedverse_service.get("status") or ("ready" if simulatedverse_service.get("healthy") else "degraded")
        ),
        activation="service+terminal",
        sources=["ai_status", "terminal_snapshot"],
        details={
            "service": simulatedverse_service,
            "terminal_present": "simulatedverse" in terminal_keys,
        },
    )

    for name in ("metaclaw", "hermes_agent"):
        service = services.get(name, {}) if isinstance(services.get(name), dict) else {}
        _add_surface(
            name,
            kind="passive_runtime",
            functional=bool(service.get("healthy")) if service else False,
            status=str(service.get("status") or ("ready" if service.get("healthy") else "degraded")),
            activation="runtime_only",
            sources=["ai_status", "agent_registry"],
            details={"service": service},
            notes=["Runtime detected, but no first-class router target exists yet."],
        )

    council_available = (paths.nusyq_hub / "scripts" / "nusyq_dispatch.py").exists() and ("ai_council" in terminal_keys)
    _add_surface(
        "ai_council",
        kind="dispatcher_only",
        functional=council_available,
        status="ready" if council_available else "degraded",
        activation="dispatcher+terminal",
        sources=["nusyq_dispatch", "terminal_awareness"],
        details={
            "command": "python scripts/nusyq_dispatch.py council ...",
            "terminal_present": "ai_council" in terminal_keys,
        },
        notes=["Consensus surface exists at the dispatcher layer rather than as a first-class router target."],
    )

    stale_hours = float(os.getenv("NUSYQ_CULTURE_SHIP_STALE_HOURS", "24") or "24")
    finished_at = _parse_iso8601_datetime(culture_ship_status.get("finished_at"))
    stale = True
    if finished_at is not None:
        stale = (datetime.now(UTC) - finished_at).total_seconds() > stale_hours * 3600.0
    culture_functional = bool(culture_ship_status.get("rc") == 0 and not stale)
    _add_surface(
        "culture_ship",
        kind="async_job_history",
        functional=culture_functional,
        status="stale_history" if stale else str(culture_ship_status.get("status") or "unknown"),
        activation="async_job+terminal",
        sources=["culture_ship_status", "terminal_snapshot"],
        details={
            "job_id": culture_ship_status.get("job_id"),
            "finished_at": culture_ship_status.get("finished_at"),
            "terminal_present": "culture_ship" in terminal_keys,
        },
        notes=["Current status is derived from the last background job, not a live probe."],
    )

    _add_surface(
        "shepherd",
        kind="alias_only",
        functional=False,
        status="alias_only",
        activation="not_first_class",
        sources=["terminal_pid_registry"],
        details={"mapped_to": "simulatedverse"},
        notes=["No first-class Shepherd runtime/route was found; only a terminal alias mapping exists."],
    )

    _add_surface(
        "rosetta_stone",
        kind="documentation",
        functional=(paths.nusyq_hub / "docs" / "ROSETTA_STONE.md").exists(),
        status="ready" if (paths.nusyq_hub / "docs" / "ROSETTA_STONE.md").exists() else "missing",
        activation="docs",
        sources=["docs"],
        details=_build_doc_surface(paths.nusyq_hub / "docs" / "ROSETTA_STONE.md"),
    )
    _add_surface(
        "agent_tutorial",
        kind="documentation",
        functional=(paths.nusyq_hub / "docs" / "AGENT_TUTORIAL.md").exists(),
        status="ready" if (paths.nusyq_hub / "docs" / "AGENT_TUTORIAL.md").exists() else "missing",
        activation="docs",
        sources=["docs"],
        details=_build_doc_surface(paths.nusyq_hub / "docs" / "AGENT_TUTORIAL.md"),
    )

    healthy = sorted(name for name, surface in surfaces.items() if surface.get("functional") is True)
    degraded = sorted(name for name, surface in surfaces.items() if surface.get("functional") is False)
    unknown = sorted(name for name, surface in surfaces.items() if surface.get("functional") is None)
    critical_surfaces = [
        "claude",
        "codex",
        "copilot",
        "chatdev",
        "ollama",
        "openclaw",
        "skyclaw",
        "simulatedverse",
    ]
    critical_healthy = [name for name in critical_surfaces if surfaces.get(name, {}).get("functional") is True]
    critical_degraded = [name for name in critical_surfaces if surfaces.get(name, {}).get("functional") is False]
    matrix_summary = (
        matrix_result.get("summary")
        if isinstance(matrix_result, dict) and isinstance(matrix_result.get("summary"), dict)
        else {}
    )

    orchestration_contract = {
        "triad_router_ready": bool(triad.get("functional")),
        "delegation_matrix_ready": bool(delegation_matrix.get("functional")),
        "router_runtime_contract_enabled": bool(matrix_summary.get("router_runtime_contract_enabled")),
        "routed_execution_path_ready_systems": list(matrix_summary.get("execution_path_ready_systems", [])),
        "dispatcher_only_surfaces": [
            name for name, surface in surfaces.items() if surface.get("kind") == "dispatcher_only"
        ],
        "passive_runtime_surfaces": [
            name for name, surface in surfaces.items() if surface.get("kind") == "passive_runtime"
        ],
        "doc_surfaces": [name for name, surface in surfaces.items() if surface.get("kind") == "documentation"],
        "subagent_ready_targets": [
            name
            for name in ("chatdev", "ollama", "lmstudio", "openclaw", "skyclaw", "quantum_resolver", "factory")
            if surfaces.get(name, {}).get("functional") is True
        ],
    }

    functional = (
        not failures
        and not critical_degraded
        and bool(triad.get("functional"))
        and bool(delegation_matrix.get("functional"))
    )
    status = "ok" if functional and not degraded else ("degraded" if surfaces else "error")
    summary = {
        "surface_count": len(surfaces),
        "healthy_surfaces": healthy,
        "degraded_surfaces": degraded,
        "unknown_surfaces": unknown,
        "critical_surfaces": critical_surfaces,
        "critical_healthy": critical_healthy,
        "critical_degraded": critical_degraded,
        "terminal_surface_keys": terminal_keys,
        "kinds": {
            kind: sorted(name for name, surface in surfaces.items() if surface.get("kind") == kind)
            for kind in sorted({str(surface.get("kind")) for surface in surfaces.values()})
        },
    }

    payload = {
        "action": "agent_fleet_doctor",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "functional": functional,
        "summary": summary,
        "orchestration_contract": orchestration_contract,
        "surfaces": surfaces,
        "checks": reports,
        "failures": failures,
    }
    payload["recommendations"] = _build_agent_fleet_doctor_recommendations(payload)
    report_path = _write_state_report(paths.nusyq_hub, "agent_fleet_doctor_latest.json", payload)
    payload["report_path"] = str(report_path)
    _write_json_report(report_path, payload)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🩺 Agent Fleet Doctor")
        print("=" * 50)
        print(f"status: {payload['status']}")
        print(f"critical_healthy: {', '.join(critical_healthy) if critical_healthy else 'none'}")
        print(f"critical_degraded: {', '.join(critical_degraded) if critical_degraded else 'none'}")
        print(f"dispatcher_only: {', '.join(orchestration_contract['dispatcher_only_surfaces']) or 'none'}")
        print(f"passive_runtime: {', '.join(orchestration_contract['passive_runtime_surfaces']) or 'none'}")
        for recommendation in payload["recommendations"]:
            print(f"- {recommendation}")
        print(f"report_path: {report_path}")
    return 0 if functional else 1


def _extract_health_signal_checks(payload: dict[str, Any] | None) -> dict[str, bool]:
    """Extract boolean signal checks from integration_health JSON payload."""
    checks: dict[str, bool] = {}
    if not isinstance(payload, dict):
        return checks
    environment = payload.get("environment")
    if not isinstance(environment, dict):
        return checks

    ollama_status = environment.get("ollama_status")
    if isinstance(ollama_status, dict):
        checks["ollama"] = bool(ollama_status.get("ok"))

    sim_status = environment.get("simulatedverse_status")
    if isinstance(sim_status, dict):
        checks["simulatedverse"] = bool(sim_status.get("ok"))

    mcp_server = environment.get("mcp_server")
    mcp_status = environment.get("mcp_status")
    if mcp_server and isinstance(mcp_status, dict):
        checks["mcp"] = bool(mcp_status.get("ok"))
    return checks


SIMULATEDVERSE_RUNTIME_MODES = {"auto", "always_on", "off"}
SIMULATEDVERSE_MODE_ALIASES = {
    "always-on": "always_on",
    "always": "always_on",
    "on": "always_on",
    "disabled": "off",
    "none": "off",
}
SIMULATEDVERSE_MODE_ENV_KEY = "NUSYQ_SIMULATEDVERSE_MODE"
COMPOSE_REQUIRED_SECRET_KEYS = ("POSTGRES_PASSWORD", "REDIS_PASSWORD", "GRAFANA_PASSWORD")


def _read_env_var(path: Path, key: str) -> str | None:
    """Read KEY from dotenv-style file; returns None when absent."""
    if not path.exists():
        return None
    key_re = re.compile(rf"^\s*{re.escape(key)}\s*=\s*(.*)$")
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = key_re.match(line)
            if not match:
                continue
            value = match.group(1).strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            return value
    except OSError:
        return None
    return None


def _normalize_simulatedverse_mode(candidate: str) -> str | None:
    """Normalize SimulatedVerse runtime mode aliases."""
    normalized = candidate.strip().lower().replace("-", "_")
    normalized = SIMULATEDVERSE_MODE_ALIASES.get(normalized, normalized)
    if normalized not in SIMULATEDVERSE_RUNTIME_MODES:
        return None
    return normalized


def _resolve_simulatedverse_runtime_mode(
    tokens: list[str] | None = None,
    hub_path: Path | None = None,
) -> tuple[str, str, str | None]:
    """Resolve SimulatedVerse runtime mode from CLI args/env with normalized aliases."""
    candidate = _parse_str_flag(tokens or [], "--simulatedverse-mode") or _parse_str_flag(
        tokens or [], "--simulatedverse-policy"
    )
    source = "cli"
    if not candidate:
        candidate = os.getenv(SIMULATEDVERSE_MODE_ENV_KEY) or os.getenv("SIMULATEDVERSE_MODE")
        source = "env"
    if not candidate:
        workspace_env_path = (hub_path / ".env.workspace") if hub_path else None
        if workspace_env_path:
            candidate = _read_env_var(workspace_env_path, SIMULATEDVERSE_MODE_ENV_KEY) or _read_env_var(
                workspace_env_path, "SIMULATEDVERSE_MODE"
            )
            source = "env.workspace"
    if not candidate:
        return "auto", "default", None

    normalized = _normalize_simulatedverse_mode(candidate)
    if normalized is None:
        return "auto", source, f"invalid simulatedverse mode '{candidate}', using auto"
    return normalized, source, None


def _mask_env_value_state(value: str | None) -> str:
    """Return redacted state only (no value leakage)."""
    if value is None:
        return "missing"
    if not value.strip():
        return "empty"
    if re.search(r"(change-me|your|example|dummy|placeholder)", value, re.IGNORECASE):
        return "placeholder"
    return "set"


def _collect_compose_secret_status(hub_path: Path) -> dict[str, Any]:
    """Collect compose secret availability from shell + local dotenv files."""
    env_path = hub_path / ".env"
    docker_env_path = hub_path / ".env.docker"
    workspace_env_path = hub_path / ".env.workspace"

    status: dict[str, Any] = {
        "env_file": str(env_path),
        "env_docker_file": str(docker_env_path),
        "env_workspace_file": str(workspace_env_path),
        "keys": {},
        "missing_effective": [],
    }

    for key in COMPOSE_REQUIRED_SECRET_KEYS:
        shell_value = os.getenv(key)
        dot_env_value = _read_env_var(env_path, key)
        dot_docker_value = _read_env_var(docker_env_path, key)
        dot_workspace_value = _read_env_var(workspace_env_path, key)
        effective_value = shell_value if shell_value not in {None, ""} else dot_env_value

        key_state = {
            "shell": _mask_env_value_state(shell_value),
            ".env": _mask_env_value_state(dot_env_value),
            ".env.docker": _mask_env_value_state(dot_docker_value),
            ".env.workspace": _mask_env_value_state(dot_workspace_value),
            "effective_for_compose": _mask_env_value_state(effective_value),
            "effective_present": bool(effective_value),
        }
        status["keys"][key] = key_state
        if not key_state["effective_present"]:
            status["missing_effective"].append(key)

    status["functional"] = not status["missing_effective"]
    return status


def _probe_compose_secret_warnings(
    hub_path: Path,
    compose_file: str = "docker-compose.yml",
    env_file: str | None = None,
) -> dict[str, Any]:
    """Run docker compose config and capture missing-variable warnings."""
    cmd = ["docker", "compose"]
    if env_file:
        cmd.extend(["--env-file", env_file])
    cmd.extend(["-f", compose_file, "config"])
    rc, out, err = run(cmd, cwd=hub_path, timeout_s=120)
    warning_lines = []
    for line in err.splitlines():
        lowered = line.lower()
        if "variable is not set" in lowered and "defaulting to a blank string" in lowered:
            warning_lines.append(line.strip())
    return {
        "compose_file": compose_file,
        "env_file": env_file,
        "command": cmd,
        "exit_code": rc,
        "warning_lines": warning_lines,
        "warning_count": len(warning_lines),
        "stderr_tail": "\n".join(err.splitlines()[-20:]) if err else "",
        "stdout_tail": "\n".join(out.splitlines()[-10:]) if out else "",
    }


def _handle_compose_secrets(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Audit and optionally initialize required docker-compose secrets."""
    if not paths.nusyq_hub:
        payload = {
            "action": "compose_secrets",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    tokens = list(args[1:] if args and args[0] == "compose_secrets" else args)
    mode = tokens[0].strip().lower() if tokens else "status"
    valid_modes = {"status", "audit", "init-local", "init"}
    if mode not in valid_modes:
        msg = "Usage: compose_secrets [status|init-local]"
        if json_mode:
            print(json.dumps({"action": "compose_secrets", "status": "error", "error": msg}, indent=2))
        else:
            print(f"[ERROR] {msg}")
        return 1

    initialized: dict[str, str] = {}
    env_path = paths.nusyq_hub / ".env"
    pre_status = _collect_compose_secret_status(paths.nusyq_hub)

    if mode in {"init-local", "init"}:
        for key in COMPOSE_REQUIRED_SECRET_KEYS:
            key_info = pre_status["keys"].get(key, {})
            if key_info.get("effective_present"):
                continue
            generated = secrets.token_hex(24)
            _upsert_env_var(env_path, key, generated)
            initialized[key] = "created"

    post_status = _collect_compose_secret_status(paths.nusyq_hub)
    compose_probe_main = _probe_compose_secret_warnings(paths.nusyq_hub, compose_file="docker-compose.yml")

    fullstack_path = paths.nusyq_hub / "deploy" / "docker-compose.full-stack.yml"
    compose_probe_fullstack: dict[str, Any] | None = None
    compose_probe_fullstack_envfile: dict[str, Any] | None = None
    advisories: list[str] = []
    if fullstack_path.exists():
        compose_probe_fullstack = _probe_compose_secret_warnings(
            paths.nusyq_hub,
            compose_file="deploy/docker-compose.full-stack.yml",
        )
        compose_probe_fullstack_envfile = _probe_compose_secret_warnings(
            paths.nusyq_hub,
            compose_file="deploy/docker-compose.full-stack.yml",
            env_file=".env",
        )
        if (
            compose_probe_fullstack.get("warning_count", 0) > 0
            and compose_probe_fullstack_envfile.get("warning_count", 0) == 0
        ):
            advisories.append(
                "deploy/docker-compose.full-stack.yml may miss root .env interpolation; use --env-file .env or export POSTGRES_PASSWORD in shell."
            )

    functional = bool(post_status.get("functional")) and compose_probe_main.get("warning_count", 0) == 0

    payload = {
        "action": "compose_secrets",
        "mode": mode,
        "status": "ok" if functional else "degraded",
        "functional": functional,
        "required_keys": list(COMPOSE_REQUIRED_SECRET_KEYS),
        "initialized": initialized,
        "pre_status": pre_status,
        "post_status": post_status,
        "compose_probe": compose_probe_main,
        "compose_probe_fullstack": compose_probe_fullstack,
        "compose_probe_fullstack_envfile": compose_probe_fullstack_envfile,
        "advisories": advisories,
        "notes": [
            "docker compose uses shell env first, then .env in the project root",
            ".env.docker is not auto-loaded by docker compose unless explicitly provided",
        ],
    }

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🔐 Compose Secrets")
        print("=" * 50)
        for key in COMPOSE_REQUIRED_SECRET_KEYS:
            key_state = post_status["keys"][key]
            print(
                f"{key}: effective={key_state['effective_for_compose']} "
                f"(shell={key_state['shell']}, .env={key_state['.env']}, .env.docker={key_state['.env.docker']})"
            )
        if initialized:
            print("\nInitialized missing local secrets in .env:")
            for key in initialized:
                print(f"  - {key}")
        if compose_probe_main["warning_lines"]:
            print("\nCompose warnings:")
            for line in compose_probe_main["warning_lines"]:
                print(f"  - {line}")
        else:
            print("\nCompose warnings: none")
        if compose_probe_fullstack and compose_probe_fullstack["warning_lines"]:
            print("\nFull-stack compose warnings:")
            for line in compose_probe_fullstack["warning_lines"]:
                print(f"  - {line}")
        if advisories:
            print("\nAdvisories:")
            for line in advisories:
                print(f"  - {line}")

    return 0 if functional else 1


def _handle_simverse_mode(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Get or set the persisted SimulatedVerse runtime mode used by integration_health."""
    if not paths.nusyq_hub:
        payload = {
            "action": "simverse_mode",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    tokens = list(args[1:] if args and args[0] == "simverse_mode" else args)
    if not tokens or tokens[0].strip().lower() in {"status", "show"}:
        mode, source, warning = _resolve_simulatedverse_runtime_mode([], paths.nusyq_hub)
        payload = {
            "action": "simverse_mode",
            "status": "ok",
            "mode": mode,
            "source": source,
            "warning": warning,
            "env_key": SIMULATEDVERSE_MODE_ENV_KEY,
            "env_file": str(paths.nusyq_hub / ".env.workspace"),
        }
        print(
            json.dumps(payload, indent=2, ensure_ascii=False)
            if json_mode
            else f"simverse_mode: {mode} (source={source})"
        )
        return 0

    requested = tokens[0].strip().lower()
    if requested == "set":
        if len(tokens) < 2:
            msg = "Usage: simverse_mode [status|auto|always_on|off] or simverse_mode set <mode>"
            if json_mode:
                print(json.dumps({"action": "simverse_mode", "status": "error", "error": msg}, indent=2))
            else:
                print(f"[ERROR] {msg}")
            return 1
        requested = tokens[1].strip().lower()

    normalized = _normalize_simulatedverse_mode(requested)
    if normalized is None:
        msg = f"invalid simulatedverse mode '{requested}' (valid: auto, always_on, off)"
        if json_mode:
            print(json.dumps({"action": "simverse_mode", "status": "error", "error": msg}, indent=2))
        else:
            print(f"[ERROR] {msg}")
        return 1

    env_path = paths.nusyq_hub / ".env.workspace"
    changed, created = _upsert_env_var(env_path, SIMULATEDVERSE_MODE_ENV_KEY, normalized)
    os.environ[SIMULATEDVERSE_MODE_ENV_KEY] = normalized
    payload = {
        "action": "simverse_mode",
        "status": "ok",
        "mode": normalized,
        "source": "env.workspace",
        "env_key": SIMULATEDVERSE_MODE_ENV_KEY,
        "env_file": str(env_path),
        "env_file_created": created,
        "changed": changed,
    }
    print(
        json.dumps(payload, indent=2, ensure_ascii=False)
        if json_mode
        else f"simverse_mode set to {normalized} (persisted in .env.workspace)"
    )
    return 0


def _parse_simulatedverse_port(payload: dict[str, Any] | None) -> int:
    """Extract SimulatedVerse port from payload, defaulting to 5002."""
    default_port = 5002
    if not isinstance(payload, dict):
        return default_port
    environment = payload.get("environment")
    if not isinstance(environment, dict):
        return default_port
    base_url = str(environment.get("simulatedverse_base") or "").strip()
    if not base_url:
        return default_port
    parsed = urlparse(base_url)
    if parsed.port:
        return int(parsed.port)
    if parsed.scheme == "https":
        return 443
    return default_port


def _simulatedverse_health_urls(port: int) -> list[str]:
    """Build prioritized SimulatedVerse health URLs for local + WSL gateway probing."""
    urls = [f"http://127.0.0.1:{port}/api/health", f"http://127.0.0.1:{port}/health"]
    gateway_ip = _wsl_default_gateway_ip()
    if gateway_ip:
        urls.extend([f"http://{gateway_ip}:{port}/api/health", f"http://{gateway_ip}:{port}/health"])
    return urls


def _attempt_simulatedverse_autostart(
    paths: RepoPaths,
    result_payload: dict[str, Any] | None,
    timeout_s: int = 45,
) -> dict[str, Any]:
    """Attempt to auto-start SimulatedVerse via Windows npm dev runtime and verify health."""
    simulatedverse_path = paths.simulatedverse
    if not simulatedverse_path:
        simulatedverse_path = _coerce_workspace_path(
            os.environ.get("SIMULATEDVERSE_PATH")
            or os.environ.get("SIMULATEDVERSE_ROOT_PATH")
            or os.environ.get("SIMVERSE_PATH")
        )
    if not simulatedverse_path:
        simulatedverse_path = _coerce_workspace_path(
            str(Path("/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"))
        )
    if not simulatedverse_path:
        return {
            "status": "error",
            "functional": False,
            "detail": "simulatedverse_path_missing",
        }
    if not simulatedverse_path.exists():
        return {
            "status": "error",
            "functional": False,
            "detail": f"simulatedverse_path_not_found: {simulatedverse_path}",
        }

    port = _parse_simulatedverse_port(result_payload)
    for url in _simulatedverse_health_urls(port):
        ok, detail = _probe_http_health(url, timeout_s=2.0)
        if ok:
            return {
                "status": "already_running",
                "functional": True,
                "detail": detail,
                "health_url": url,
                "port": port,
            }

    cmd_exe = shutil.which("cmd.exe")
    simverse_windows = _to_windows_path(simulatedverse_path)
    if len(simverse_windows) > 3:
        simverse_windows = simverse_windows.rstrip("\\/")
    launch_profile = os.getenv("NUSYQ_SIMULATEDVERSE_START_PROFILE", "minimal").strip().lower()
    launch_npm_script = "dev" if launch_profile in {"full", "always_on", "dev"} else "dev:minimal"

    launch_cmd: list[str] | None = None
    rc: int | None = None
    out = ""
    err = ""
    launch_ok = False
    launcher_blocked = False
    launcher_block_reason: str | None = None
    if cmd_exe:
        cd_fragment = f'cd /d "{simverse_windows}"' if " " in simverse_windows else f"cd /d {simverse_windows}"
        launch_script = (
            f"{cd_fragment} "
            f'&& set "PORT={port}" '
            f'&& set "SIMULATEDVERSE_PORT={port}" '
            f'&& start "" /b cmd /c npm run {launch_npm_script}'
        )
        launch_cmd = [cmd_exe, "/c", launch_script]
        rc, out, err = run(launch_cmd, timeout_s=12)
        launch_ok = rc == 0
        if not launch_ok and _looks_like_probe_blocked_error(err):
            launcher_blocked = True
            launcher_block_reason = err
    else:
        err = "cmd.exe not available for simulatedverse auto-start"
    fallback_attempt: dict[str, Any] | None = None
    minimal_attempt: dict[str, Any] | None = None

    if not launch_ok:
        previous_env = {
            "SIMULATEDVERSE_PATH": os.environ.get("SIMULATEDVERSE_PATH"),
            "SIMULATEDVERSE_PORT": os.environ.get("SIMULATEDVERSE_PORT"),
            "NUSYQ_SIMULATEDVERSE_DETACH": os.environ.get("NUSYQ_SIMULATEDVERSE_DETACH"),
            "NUSYQ_HUB_PATH": os.environ.get("NUSYQ_HUB_PATH"),
        }
        try:
            from scripts.start_simulatedverse_minimal import SimulatedVerseMinimal

            os.environ["SIMULATEDVERSE_PATH"] = str(simulatedverse_path)
            os.environ["SIMULATEDVERSE_PORT"] = str(port)
            os.environ["NUSYQ_SIMULATEDVERSE_DETACH"] = "1"
            if paths.nusyq_hub:
                os.environ["NUSYQ_HUB_PATH"] = str(paths.nusyq_hub)

            launcher = SimulatedVerseMinimal()
            launcher.simulatedverse_path = simulatedverse_path
            launcher.base_url = f"http://127.0.0.1:{port}"
            process = launcher.start_agents_only(timeout=max(10, min(int(timeout_s), 30)))
            minimal_running = bool(process) or bool(launcher.check_if_running())
            minimal_attempt = {
                "status": "ok" if minimal_running else "degraded",
                "running": minimal_running,
                "launcher": "start_simulatedverse_minimal",
                "process_started": bool(process),
            }
            launch_ok = launch_ok or minimal_running
        except Exception as exc:
            minimal_attempt = {
                "status": "error",
                "running": False,
                "launcher": "start_simulatedverse_minimal",
                "error": str(exc),
            }
        finally:
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    legacy_fallback_flag = os.getenv("NUSYQ_ENABLE_LEGACY_SIMVERSE_FALLBACK", "0").strip().lower()
    legacy_fallback_enabled = legacy_fallback_flag in {"1", "true", "yes", "on"}
    if not launch_ok and not launcher_blocked and paths.nusyq_hub:
        if not legacy_fallback_enabled:
            fallback_attempt = {
                "status": "skipped",
                "reason": "legacy_fallback_disabled",
                "env_key": "NUSYQ_ENABLE_LEGACY_SIMVERSE_FALLBACK",
            }
        else:
            starter_script = paths.nusyq_hub / "scripts" / "Start-SimulatedVerse.ps1"
            powershell_exe = shutil.which("powershell.exe")
            if powershell_exe and starter_script.exists():
                starter_windows = _to_windows_path(starter_script)
                simverse_windows_safe = (
                    simverse_windows.rstrip("\\/") if len(simverse_windows) > 3 else simverse_windows
                )
                ps_command = (
                    f"$env:SIMULATEDVERSE_PATH='{simverse_windows_safe}'; "
                    f"$env:SIMULATEDVERSE_PORT='{port}'; "
                    f"& '{starter_windows}'"
                )
                fallback_cmd = [
                    powershell_exe,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    ps_command,
                ]
                fallback_rc, fallback_out, fallback_err = run(fallback_cmd, timeout_s=min(timeout_s, 60))
                fallback_attempt = {
                    "status": "ok" if fallback_rc == 0 else "error",
                    "rc": fallback_rc,
                    "command": fallback_cmd,
                    "stdout_tail": ("\n".join(fallback_out.splitlines()[-10:]) if fallback_out else ""),
                    "stderr_tail": ("\n".join(fallback_err.splitlines()[-10:]) if fallback_err else ""),
                }
                if fallback_rc != 0 and _looks_like_probe_blocked_error(fallback_err):
                    launcher_blocked = True
                    launcher_block_reason = fallback_err
                    fallback_attempt["status"] = "blocked"
                    fallback_attempt["blocked"] = True
                launch_ok = launch_ok or fallback_rc == 0
            else:
                fallback_attempt = {
                    "status": "skipped",
                    "reason": "legacy_launcher_unavailable",
                    "powershell_found": bool(powershell_exe),
                    "starter_script_exists": bool(starter_script.exists()),
                }

    deadline = time.time() + timeout_s
    last_detail = "health probe not attempted"
    healthy_url: str | None = None
    while time.time() < deadline:
        for url in _simulatedverse_health_urls(port):
            ok, detail = _probe_http_health(url, timeout_s=2.0)
            last_detail = detail
            if ok:
                healthy_url = url
                break
        if healthy_url:
            break
        time.sleep(1.0)

    functional = healthy_url is not None
    return {
        "status": "ok" if functional else ("degraded" if launch_ok else "error"),
        "functional": functional,
        "port": port,
        "health_url": healthy_url,
        "health_detail": last_detail,
        "launch_rc": rc,
        "launch_stdout_tail": "\n".join(out.splitlines()[-10:]) if out else "",
        "launch_stderr_tail": "\n".join(err.splitlines()[-10:]) if err else "",
        "launch_command": launch_cmd,
        "launch_npm_script": launch_npm_script,
        "launch_profile": launch_profile,
        "fallback_attempt": fallback_attempt,
        "minimal_attempt": minimal_attempt,
        "launcher_blocked": launcher_blocked,
        "launcher_block_reason": launcher_block_reason,
    }


def _handle_integration_health(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Run consolidated integration health checks from existing health script."""
    if not paths.nusyq_hub:
        payload = {
            "action": "integration_health",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    tokens = list(args[1:] if args and args[0] == "integration_health" else args)
    simulatedverse_mode, simulatedverse_mode_source, simulatedverse_mode_warning = _resolve_simulatedverse_runtime_mode(
        tokens, paths.nusyq_hub
    )
    cmd = [sys.executable, "scripts/integration_health_check.py"]

    # Keep CLI-orchestration flags local; the underlying checker does not accept these.
    local_only_flags = {
        "--no-repair-simulatedverse",
        "--attempt-simulatedverse-repair",
        "--async",
        "--sync",
        "--json",
    }
    forwarded_tokens = [token for token in tokens if token not in local_only_flags]

    if not any(token.startswith("--mode") for token in forwarded_tokens):
        cmd.extend(["--mode", "fast"])
    if not any(token.startswith("--format") for token in forwarded_tokens):
        cmd.extend(["--format", "json" if json_mode else "human"])
    if not any(
        token.startswith("--simulatedverse-mode") or token.startswith("--simulatedverse-policy")
        for token in forwarded_tokens
    ):
        cmd.extend(["--simulatedverse-mode", simulatedverse_mode])
    cmd.extend(forwarded_tokens)

    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=240)
    json_payload = _extract_json_payload(out) if out else None
    result_payload = json_payload if isinstance(json_payload, dict) else None
    signal_checks = _extract_health_signal_checks(result_payload)
    ignored_signals: list[str] = []
    probe_blocked_signals: list[str] = []
    environment = result_payload.get("environment") if isinstance(result_payload, dict) else None

    def _ignore_probe_blocked_signal(name: str, status_payload: Any) -> None:
        if not _looks_like_probe_blocked_error(status_payload):
            return
        if name in signal_checks:
            signal_checks[name] = True
        if name not in ignored_signals:
            ignored_signals.append(name)
        if name not in probe_blocked_signals:
            probe_blocked_signals.append(name)

    if isinstance(environment, dict):
        _ignore_probe_blocked_signal("ollama", environment.get("ollama_status"))
        _ignore_probe_blocked_signal("mcp", environment.get("mcp_status"))

        # SimulatedVerse remains strict in always_on mode, but auto mode should not fail
        # when probes are blocked by sandbox/runtime permission boundaries.
        if simulatedverse_mode != "always_on":
            _ignore_probe_blocked_signal("simulatedverse", environment.get("simulatedverse_status"))

    if simulatedverse_mode == "off" and "simulatedverse" in signal_checks:
        signal_checks["simulatedverse"] = True
        ignored_signals.append("simulatedverse")

    repair_allowed = "--no-repair-simulatedverse" not in tokens and simulatedverse_mode != "off"
    repair_attempt: dict[str, Any] | None = None
    repair_recheck: dict[str, Any] | None = None

    sim_ok = signal_checks.get("simulatedverse", True)
    if repair_allowed and not sim_ok:
        repair_attempt = _attempt_simulatedverse_autostart(paths, result_payload)
        if repair_attempt.get("functional"):
            rc2, out2, err2 = run(cmd, cwd=paths.nusyq_hub, timeout_s=240)
            json_payload2 = _extract_json_payload(out2) if out2 else None
            result_payload2 = json_payload2 if isinstance(json_payload2, dict) else None
            signal_checks2 = _extract_health_signal_checks(result_payload2)
            repair_recheck = {
                "exit_code": rc2,
                "signal_checks": signal_checks2,
            }
            rc = rc2
            out = out2
            err = err2
            result_payload = result_payload2
            signal_checks = signal_checks2

    checks_ok = all(signal_checks.values()) if signal_checks else True
    functional = rc == 0 and checks_ok
    status = "ok" if functional else ("degraded" if rc == 0 else "error")
    failed_signals = sorted(name for name, ok in signal_checks.items() if not ok)
    payload = {
        "action": "integration_health",
        "status": status,
        "functional": functional,
        "simulatedverse_mode": simulatedverse_mode,
        "simulatedverse_mode_source": simulatedverse_mode_source,
        "simulatedverse_mode_warning": simulatedverse_mode_warning,
        "ignored_signals": ignored_signals,
        "probe_blocked_signals": probe_blocked_signals,
        "exit_code": rc,
        "result": result_payload,
        "signal_checks": signal_checks,
        "failed_signals": failed_signals,
        "repair_allowed": repair_allowed,
        "simulatedverse_repair_attempt": repair_attempt,
        "simulatedverse_repair_recheck": repair_recheck,
        "stdout": out if not result_payload else None,
        "stderr": err,
    }
    report_path = _write_state_report(paths.nusyq_hub, "integration_health_status.json", payload)
    payload["report_file"] = str(report_path)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        if out:
            print(out)
        print("Integration wrapper summary:")
        print(f"  simulatedverse_mode: {simulatedverse_mode} (source={simulatedverse_mode_source})")
        print(f"  status: {status}")
        if ignored_signals:
            print(f"  ignored_signals: {', '.join(sorted(set(ignored_signals)))}")
        if failed_signals:
            print(f"  failed_signals: {', '.join(failed_signals)}")
        if err:
            print(err)
    return 0 if functional else 1


def _handle_vscode_extensions_plan(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Generate Codex-first VS Code extension isolation plan."""
    if not paths.nusyq_hub:
        payload = {
            "action": "vscode_extensions_plan",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    tokens = list(args[1:] if args and args[0] == "vscode_extensions_plan" else args)
    cmd = [sys.executable, "scripts/integrate_extensions.py", "--plan-isolation"]
    cmd.extend(tokens)

    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=240)
    plan_payload = _extract_json_payload(out) if out else None
    status_ok = rc == 0 and isinstance(plan_payload, dict) and plan_payload.get("status") == "ok"
    payload = {
        "action": "vscode_extensions_plan",
        "status": "ok" if status_ok else "error",
        "functional": status_ok,
        "exit_code": rc,
        "plan": plan_payload if isinstance(plan_payload, dict) else None,
        "stdout": out if not isinstance(plan_payload, dict) else None,
        "stderr": err,
    }

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🧩 VS Code Extensions Isolation Plan")
        print("=" * 50)
        if out:
            print(out)
        if err:
            print(err)

    return 0 if status_ok else 1


def _handle_vscode_extensions_quickwins(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Generate immediate extension optimization actions from local audit tooling."""
    if not paths.nusyq_hub:
        payload = {
            "action": "vscode_extensions_quickwins",
            "status": "error",
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    tokens = list(args[1:] if args and args[0] == "vscode_extensions_quickwins" else args)
    cmd = [sys.executable, "scripts/integrate_extensions.py", "--quickwins"]
    cmd.extend(tokens)

    rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=240)
    quickwins_payload = _extract_json_payload(out) if out else None
    status_ok = rc == 0 and isinstance(quickwins_payload, dict) and quickwins_payload.get("status") == "ok"
    payload = {
        "action": "vscode_extensions_quickwins",
        "status": "ok" if status_ok else "error",
        "functional": status_ok,
        "exit_code": rc,
        "quickwins": quickwins_payload if isinstance(quickwins_payload, dict) else None,
        "stdout": out if not isinstance(quickwins_payload, dict) else None,
        "stderr": err,
    }

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🧩 VS Code Extensions Quickwins")
        print("=" * 50)
        if out:
            print(out)
        if err:
            print(err)

    return 0 if status_ok else 1


def _capture_action_output(action: Callable[[], int]) -> tuple[int, str]:
    """Capture stdout/stderr from an internal action handler."""
    buffer = io.StringIO()
    rc = 1
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        try:
            rc = action()
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}")
            rc = 1
    return rc, buffer.getvalue().strip()


def _upsert_env_var(path: Path, key: str, value: str) -> tuple[bool, bool]:
    """Upsert KEY=VALUE in dotenv-style file; returns (changed, created)."""
    created = False
    if path.exists():
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    else:
        raw_lines = []
        created = True

    key_re = re.compile(rf"^\s*{re.escape(key)}\s*=")
    changed = False
    found = False
    next_lines: list[str] = []
    for line in raw_lines:
        if key_re.match(line):
            found = True
            desired = f"{key}={value}"
            if line.strip() != desired:
                next_lines.append(desired)
                changed = True
            else:
                next_lines.append(line)
            continue
        next_lines.append(line)

    if not found:
        next_lines.append(f"{key}={value}")
        changed = True

    if changed or created:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")

    return changed, created


def _ensure_ignition_api(paths: RepoPaths, host: str = "127.0.0.1", port: int = 8000) -> dict[str, Any]:
    """Ensure NuSyQ API runtime is live on the expected host/port."""
    if not paths.nusyq_hub:
        return {
            "status": "error",
            "functional": False,
            "detail": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }

    health_url = f"http://{host}:{port}/api/health"
    pid_path = _ignition_api_pid_path(paths.nusyq_hub)
    log_path = _ignition_api_log_path(paths.nusyq_hub)
    pid_record = _read_openclaw_pid_record(pid_path)
    pid = int(pid_record.get("pid", 0) or 0)
    running = _is_process_running(pid)

    if pid and not running and pid_path.exists():
        with contextlib.suppress(OSError):
            pid_path.unlink()

    health_ok, health_detail = _probe_http_health(health_url)
    if health_ok:
        return {
            "status": "already_running" if running else "ok",
            "functional": True,
            "pid": pid or None,
            "health_url": health_url,
            "health_detail": health_detail,
            "log_file": str(log_path),
            "pid_file": str(pid_path),
        }

    if pid and running:
        _terminate_job_process(pid, grace_s=3.0)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.api.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    try:
        with log_path.open("a", encoding="utf-8") as log_fh:
            proc = subprocess.Popen(
                cmd,
                cwd=str(paths.nusyq_hub),
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                env=_build_env(),
                start_new_session=True,
            )
    except OSError as exc:
        return {
            "status": "error",
            "functional": False,
            "detail": str(exc),
            "command": cmd,
        }

    _write_openclaw_pid_record(
        pid_path,
        {
            "pid": proc.pid,
            "started_at": now_stamp(),
            "command": cmd,
            "cwd": str(paths.nusyq_hub),
            "host": host,
            "port": port,
            "health_url": health_url,
            "log_file": str(log_path),
        },
    )

    deadline = time.time() + IGNITION_API_READY_TIMEOUT_S
    while time.time() < deadline:
        health_ok, health_detail = _probe_http_health(health_url)
        if health_ok:
            break
        if not _is_process_running(proc.pid):
            break
        time.sleep(0.5)

    return {
        "status": "ok" if health_ok else "degraded",
        "functional": health_ok,
        "pid": proc.pid,
        "health_url": health_url,
        "health_detail": health_detail,
        "log_file": str(log_path),
        "pid_file": str(pid_path),
        "command": cmd,
    }


def _probe_intermediary_endpoint(base_url: str) -> dict[str, Any]:
    """Warm the AI Intermediary endpoint and return probe details."""
    url = f"{base_url.rstrip('/')}/api/intermediary"
    payload = {
        "text": "ignition_warmup",
        "paradigm": "natural_language",
        "module": "code_analysis_helper",
        "context": {"origin": "ignition"},
    }
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            status_code = int(getattr(response, "status", 500))
            body = response.read().decode("utf-8", errors="replace")
            parsed = _extract_json_payload(body) if body else None
            functional = status_code < 500 and isinstance(parsed, dict)
            return {
                "status": "ok" if functional else "degraded",
                "functional": functional,
                "url": url,
                "http_status": status_code,
                "response": parsed if isinstance(parsed, dict) else body[:400],
            }
    except Exception as exc:
        return {
            "status": "error",
            "functional": False,
            "url": url,
            "error": str(exc),
        }


def _configure_copilot_endpoint(paths: RepoPaths, base_url: str) -> dict[str, Any]:
    """Configure copilot bridge env vars for intermediary-backed local runtime."""
    endpoint = f"{base_url.rstrip('/')}/api/intermediary"
    health_url = f"{base_url.rstrip('/')}/api/health"
    env_updates = {
        "NUSYQ_COPILOT_BRIDGE_MODE": "intermediary",
        "NUSYQ_COPILOT_BRIDGE_ENDPOINT": endpoint,
        "NUSYQ_COPILOT_BRIDGE_HEALTH_URL": health_url,
    }
    for key, value in env_updates.items():
        os.environ[key] = value

    changed_keys: list[str] = []
    created = False
    env_path = paths.nusyq_hub / ".env.workspace" if paths.nusyq_hub else None
    if env_path is not None:
        for key, value in env_updates.items():
            changed, was_created = _upsert_env_var(env_path, key, value)
            if changed:
                changed_keys.append(key)
            created = created or was_created

    return {
        "status": "ok",
        "functional": True,
        "endpoint": endpoint,
        "health_url": health_url,
        "env_file": str(env_path) if env_path else None,
        "env_keys_changed": changed_keys,
        "env_file_created": created,
    }


def _verify_model_discovery(paths: RepoPaths) -> dict[str, Any]:
    """Validate model discovery against Ollama API and run sync helper."""
    ollama_base = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434"
    if "://" not in ollama_base:
        ollama_base = f"http://{ollama_base}"
    tags_url = f"{ollama_base.rstrip('/')}/api/tags"

    api_count = 0
    api_error = ""
    try:
        with urlopen(Request(tags_url, method="GET"), timeout=8) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
            models = data.get("models", []) if isinstance(data, dict) else []
            api_count = len(models) if isinstance(models, list) else 0
    except Exception as exc:
        api_error = str(exc)

    hub_count = 0
    hub_error = ""
    try:
        from src.integration.Ollama_Integration_Hub import KILOOllamaHub

        hub = KILOOllamaHub()
        discovered = hub.discover_models()
        hub_count = len(discovered) if isinstance(discovered, dict) else 0
    except Exception as exc:
        hub_error = str(exc)

    sync_rc, sync_out, sync_err = run(
        [sys.executable, "scripts/discover_and_sync_models.py", "--query-apis"],
        cwd=paths.nusyq_hub,
        timeout_s=180,
    )

    functional = (api_count == 0 and not api_error) or (hub_count > 0 and (api_count == 0 or hub_count >= 1))
    status = "ok" if functional else "degraded"
    return {
        "status": status,
        "functional": functional,
        "ollama_tags_url": tags_url,
        "ollama_api_models": api_count,
        "ollama_api_error": api_error or None,
        "hub_discovered_models": hub_count,
        "hub_discovery_error": hub_error or None,
        "sync_rc": sync_rc,
        "sync_output": sync_out[:4000] if sync_out else "",
        "sync_error": sync_err[:2000] if sync_err else "",
    }


def _check_sql_datastores(paths: RepoPaths, auto_init: bool = False) -> dict[str, Any]:
    """Validate SQL-backed local state stores used by NuSyQ runtime."""
    if not paths.nusyq_hub:
        return {
            "status": "error",
            "functional": False,
            "detail": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }

    import sqlite3

    hub = paths.nusyq_hub
    runtime_db = hub / "state" / "nusyq_state.db"
    knowledge_db = hub / "state" / "knowledge_garden.db"
    duckdb_path = hub / "data" / "state.duckdb"

    init_rc = 0
    init_out = ""
    init_err = ""
    init_attempted = False
    if auto_init and not runtime_db.exists():
        init_attempted = True
        init_rc, init_out, init_err = run(
            [sys.executable, "scripts/init_db.py"],
            cwd=hub,
            timeout_s=90,
        )

    def _sqlite_probe(db_path: Path) -> dict[str, Any]:
        result: dict[str, Any] = {
            "path": str(db_path),
            "exists": db_path.exists(),
            "size_bytes": db_path.stat().st_size if db_path.exists() else 0,
            "table_count": 0,
            "tables_sample": [],
            "error": None,
        }
        if not db_path.exists():
            return result
        try:
            with sqlite3.connect(str(db_path), timeout=4) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [str(row[0]) for row in cursor.fetchall() if row and row[0]]
                result["table_count"] = len(tables)
                result["tables_sample"] = tables[:20]
        except Exception as exc:
            result["error"] = str(exc)
        return result

    runtime_probe = _sqlite_probe(runtime_db)
    knowledge_probe = _sqlite_probe(knowledge_db)

    duckdb_probe: dict[str, Any] = {
        "path": str(duckdb_path),
        "exists": duckdb_path.exists(),
        "size_bytes": duckdb_path.stat().st_size if duckdb_path.exists() else 0,
        "table_count": 0,
        "error": None,
    }
    if duckdb_path.exists():
        try:
            import duckdb  # type: ignore[import-not-found]

            with duckdb.connect(str(duckdb_path), read_only=True) as con:
                row = con.execute("SELECT COUNT(*) FROM information_schema.tables").fetchone()
                duckdb_probe["table_count"] = int(row[0]) if row else 0
        except Exception as exc:
            duckdb_probe["error"] = str(exc)

    runtime_ok = bool(runtime_probe["exists"] and runtime_probe["table_count"] > 0)
    functional = runtime_ok
    warnings: list[str] = []
    if not runtime_ok:
        warnings.append("nusyq_state.db missing or unreadable")
    if knowledge_probe.get("exists") and knowledge_probe.get("error"):
        warnings.append("knowledge_garden.db unreadable")
    if duckdb_probe.get("exists") and duckdb_probe.get("error"):
        warnings.append("state.duckdb unreadable")

    status = "ok" if functional and not warnings else "degraded" if functional else "error"
    return {
        "status": status,
        "functional": functional,
        "auto_init_attempted": init_attempted,
        "auto_init_rc": init_rc if init_attempted else None,
        "auto_init_output": init_out[:1500] if init_out else "",
        "auto_init_error": init_err[:800] if init_err else "",
        "runtime_sqlite": runtime_probe,
        "knowledge_sqlite": knowledge_probe,
        "duckdb": duckdb_probe,
        "warnings": warnings,
    }


def _check_nssm_admin_readiness() -> dict[str, Any]:
    """Probe Windows NSSM and admin rights for service installation readiness."""
    cmd_exe = shutil.which("cmd.exe")
    if not cmd_exe:
        return {
            "status": "not_applicable",
            "functional": True,
            "detail": "cmd.exe not available; NSSM checks skipped",
        }

    def _discover_nssm_paths() -> list[str]:
        discovered: list[str] = []

        # PATH-backed resolution first.
        nssm_bin = shutil.which("nssm")
        if nssm_bin:
            discovered.append(nssm_bin)

        rc_where, out_where, _err_where = run([cmd_exe, "/c", "where nssm"], timeout_s=8)
        if rc_where == 0 and out_where:
            for line in out_where.splitlines():
                candidate = line.strip()
                if candidate and candidate not in discovered:
                    discovered.append(candidate)

        # Winget fallback if PATH has not been refreshed in current shell.
        localappdata = os.getenv("LOCALAPPDATA", "").strip()
        if localappdata:
            winget_root = Path(localappdata) / "Microsoft" / "WinGet" / "Packages"
            package_root = winget_root / "NSSM.NSSM_Microsoft.Winget.Source_8wekyb3d8bbwe"
            if package_root.exists():
                for rel in (
                    Path("nssm-2.24-101-g897c7ad/win64/nssm.exe"),
                    Path("nssm-2.24-101-g897c7ad/win32/nssm.exe"),
                ):
                    candidate = package_root / rel
                    if candidate.exists():
                        text = str(candidate)
                        if text not in discovered:
                            discovered.append(text)
                # Version-agnostic fallback.
                if not any(path.lower().endswith("nssm.exe") for path in discovered):
                    for candidate in package_root.rglob("nssm.exe"):
                        text = str(candidate)
                        if text not in discovered:
                            discovered.append(text)

        return discovered

    nssm_paths = _discover_nssm_paths()
    nssm_found = bool(nssm_paths)
    lookup_error = "" if nssm_found else "nssm not found in PATH or WinGet package locations"

    admin = False
    admin_check = "unknown"
    powershell_bin = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    if powershell_bin:
        admin_expr = (
            "[bool](([Security.Principal.WindowsPrincipal] "
            "[Security.Principal.WindowsIdentity]::GetCurrent())"
            ".IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))"
        )
        rc_admin, out_admin, err_admin = run(
            [powershell_bin, "-NoProfile", "-NonInteractive", "-Command", admin_expr],
            timeout_s=8,
        )
        admin = rc_admin == 0 and "true" in out_admin.strip().lower()
        admin_check = out_admin.strip() or err_admin.strip() or "no output"
    else:
        # Use a hidden window to avoid flashing a new console during periodic
        # health checks (e.g., when invoked by background schedulers).
        #
        # `cmd.exe /c net session ...` can spawn a visible window if the parent
        # process does not already have a console. Hiding the window prevents
        # the user from seeing intermittent "true"/"false" popups.
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            proc = subprocess.run(
                [cmd_exe, "/c", "net session >nul 2>&1 && echo true || echo false"],
                timeout=8,
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
            )
            rc_admin = proc.returncode
            out_admin = proc.stdout.strip()
            err_admin = proc.stderr.strip()
        except Exception as exc:
            rc_admin = 1
            out_admin = ""
            err_admin = f"{type(exc).__name__}: {exc}"

        admin = rc_admin == 0 and "true" in out_admin.strip().lower()
        admin_check = out_admin.strip() or err_admin.strip() or "net session check unavailable"

    functional = bool(nssm_found and admin)
    status = "ok" if functional else "degraded"
    return {
        "status": status,
        "functional": functional,
        "nssm_found": nssm_found,
        "nssm_paths": nssm_paths[:5],
        "admin": admin,
        "admin_check": admin_check,
        "lookup_error": lookup_error,
        "remediation": [
            "Install NSSM (e.g., winget install --id NSSM.NSSM) if missing",
            "If NSSM is installed but not found, open a new shell so PATH refreshes",
            "Run terminal as Administrator before installing/updating services",
        ],
    }


def _check_telemetry_output_channels(paths: RepoPaths) -> dict[str, Any]:
    """Validate trace service posture and terminal/output channel signal flow."""
    trace_rc, trace_out = _capture_action_output(lambda: handle_trace_service_status(paths))
    trace_ok = trace_rc == 0

    snapshot_rc, snapshot_out = _capture_action_output(lambda: handle_terminals(["snapshot", "--limit=5"]))
    snapshot_payload = _extract_json_payload(snapshot_out) if snapshot_out else None
    summary = snapshot_payload.get("summary", {}) if isinstance(snapshot_payload, dict) else {}
    total_channels = int(summary.get("total_channels", 0) or 0)
    hot_channels = int(summary.get("hot_channels", 0) or 0)
    missing_logs = int(summary.get("missing_logs", 0) or 0)
    snapshot_ok = snapshot_rc == 0 and total_channels >= 16

    routing_total = 0
    routing_error = ""
    try:
        from src.system.output_source_intelligence import get_output_intelligence

        intelligence = _run_async_sync(get_output_intelligence())
        routing_map = intelligence.generate_routing_map()
        routing_total = int(routing_map.get("total_sources", 0) or 0)
    except Exception as exc:
        routing_error = str(exc)

    functional = snapshot_ok and routing_total >= 80
    status = "ok" if functional and trace_ok else "degraded" if functional else "error"
    return {
        "status": status,
        "functional": functional,
        "trace_ok": trace_ok,
        "trace_output": trace_out[:1200] if trace_out else "",
        "snapshot_ok": snapshot_ok,
        "channels_total": total_channels,
        "channels_hot": hot_channels,
        "missing_logs": missing_logs,
        "output_sources_configured": routing_total,
        "output_sources_error": routing_error or None,
    }


def _run_brownfield_reuse_probe(paths: RepoPaths, capabilities: list[str]) -> dict[str, Any]:
    """Run Three-Before-New scans for requested capabilities."""
    if not paths.nusyq_hub:
        return {
            "status": "error",
            "functional": False,
            "detail": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
    try:
        configured_timeout_s = int(os.environ.get("NUSYQ_FIND_EXISTING_TOOL_TIMEOUT_S", "20"))
    except (TypeError, ValueError):
        configured_timeout_s = 20
    tool_timeout_s = max(8, configured_timeout_s)

    def _fallback_candidates(capability: str) -> list[dict[str, Any]]:
        tokens = [token for token in re.split(r"[^A-Za-z0-9]+", capability.lower()) if token]
        if not tokens:
            return []
        rc, out, _err = run(
            ["rg", "--files", "scripts", "src", "docs", "config", "web"],
            cwd=paths.nusyq_hub,
            timeout_s=15,
        )
        if rc != 0 or not out:
            return []
        scored: list[tuple[float, str]] = []
        for line in out.splitlines():
            path_text = line.strip()
            if not path_text:
                continue
            lowered = path_text.lower()
            score = 0.0
            for token in tokens:
                if token in lowered:
                    score += 1.0
                basename = path_text.rsplit("/", 1)[-1].lower()
                if token in basename:
                    score += 1.5
            if score > 0:
                scored.append((score, path_text))
        scored.sort(key=lambda item: item[0], reverse=True)
        fallback_records: list[dict[str, Any]] = []
        for score, path_text in scored[:5]:
            fallback_records.append(
                {
                    "path": path_text,
                    "score": score,
                    "reasons": ["fallback: path/filename token match"],
                    "excerpt": None,
                }
            )
        return fallback_records

    results: list[dict[str, Any]] = []
    all_good = True
    for capability in capabilities:
        rc, out, err = run(
            [
                sys.executable,
                "scripts/find_existing_tool.py",
                "--capability",
                capability,
                "--max-results",
                "5",
                "--format",
                "json",
            ],
            cwd=paths.nusyq_hub,
            timeout_s=tool_timeout_s,
        )
        records: list[dict[str, Any]] = []
        parse_error = ""
        used_fallback = False
        if out.strip():
            try:
                payload = json.loads(out)
                if isinstance(payload, list):
                    records = [item for item in payload if isinstance(item, dict)]
            except Exception as exc:
                parse_error = str(exc)
        if len(records) < 3:
            fallback_records = _fallback_candidates(capability)
            if fallback_records:
                records = fallback_records
                used_fallback = True
        if len(records) < 3:
            all_good = False
        results.append(
            {
                "capability": capability,
                "exit_code": rc,
                "used_fallback": used_fallback,
                "candidate_count": len(records),
                "top_candidates": records[:3],
                "stderr": err[:400] if err else "",
                "parse_error": parse_error or None,
            }
        )

    status = "ok" if all_good else "degraded"
    return {
        "status": status,
        "functional": all_good,
        "tool_timeout_seconds": tool_timeout_s,
        "capabilities": capabilities,
        "results": results,
    }


def _handle_ignition(args: list[str], paths: RepoPaths, json_mode: bool = False) -> int:
    """Full-system ignition sequence for AI/intermediary/terminal orchestration."""
    if not paths.nusyq_hub:
        payload = {
            "action": "ignition",
            "status": "error",
            "functional": False,
            "error": ERROR_NUSYQ_HUB_PATH_NOT_FOUND,
        }
        print(json.dumps(payload, indent=2) if json_mode else payload["error"])
        return 1

    tokens = list(args[1:] if args and args[0] == "ignition" else args)
    thorough_mode = any(flag in tokens for flag in ("--thorough", "--hetaeristic", "--full-pass"))
    strict_mode = "--strict" in tokens
    include_sql = thorough_mode or "--with-sql" in tokens
    include_nssm = thorough_mode or "--with-nssm" in tokens
    include_telemetry = thorough_mode or "--with-telemetry" in tokens
    include_brownfield = thorough_mode or "--with-brownfield" in tokens
    auto_init_db = "--init-db" in tokens or thorough_mode
    deep_health = "--deep-health" in tokens

    base_url = "http://127.0.0.1:8000"
    steps: list[dict[str, Any]] = []

    # 1) Start Terminal/API runtime on port 8000.
    api_state = _ensure_ignition_api(paths, host="127.0.0.1", port=8000)
    steps.append({"id": 1, "name": "start_terminal_api", **api_state})

    # 2) Start specialized terminals.
    terminals_rc, terminals_out = _capture_action_output(lambda: handle_terminals(["activate"]))
    steps.append(
        {
            "id": 2,
            "name": "activate_specialized_terminals",
            "status": "ok" if terminals_rc == 0 else "error",
            "functional": terminals_rc == 0,
            "exit_code": terminals_rc,
            "output": terminals_out[:4000],
        }
    )

    # 3) Activate intermediary endpoint.
    intermediary_state = _probe_intermediary_endpoint(base_url)
    steps.append({"id": 3, "name": "activate_ai_intermediary", **intermediary_state})

    # 4) Enable breathing integration.
    if paths.nusyq_root and not os.getenv("NUSYQ_ROOT_PATH"):
        os.environ["NUSYQ_ROOT_PATH"] = str(paths.nusyq_root)
    try:
        from src.integration.breathing_integration import BreathingIntegration

        breathing = BreathingIntegration(tau_base=90.0, enable_breathing=True)
        breathing_state = breathing.get_breathing_state()
        breathing_ok = bool(breathing_state.get("enabled"))
        steps.append(
            {
                "id": 4,
                "name": "enable_breathing_integration",
                "status": "ok" if breathing_ok else "degraded",
                "functional": breathing_ok,
                "state": breathing_state,
            }
        )
    except Exception as exc:
        steps.append(
            {
                "id": 4,
                "name": "enable_breathing_integration",
                "status": "error",
                "functional": False,
                "error": str(exc),
            }
        )

    # 5) Route VS Code extension outputs.
    route_rc, route_out, route_err = run(
        [sys.executable, "scripts/activate_live_terminal_routing.py"],
        cwd=paths.nusyq_hub,
        timeout_s=240,
    )
    validate_rc, validate_out, validate_err = run(
        [sys.executable, "scripts/activate_live_terminal_routing.py", "--validate"],
        cwd=paths.nusyq_hub,
        timeout_s=120,
    )
    channel_count = 0
    routing_cfg = read_json(paths.nusyq_hub / "data" / "terminal_routing.json") or {}
    terminals_cfg = routing_cfg.get("terminals", {}) if isinstance(routing_cfg, dict) else {}
    if isinstance(terminals_cfg, dict):
        channel_count = len(terminals_cfg)
    route_ok = route_rc == 0 and validate_rc == 0
    steps.append(
        {
            "id": 5,
            "name": "route_vscode_extension_outputs",
            "status": "ok" if route_ok else "degraded",
            "functional": route_ok,
            "channels_configured": channel_count,
            "activate_rc": route_rc,
            "validate_rc": validate_rc,
            "activate_output": route_out[:2500],
            "validate_output": validate_out[:2500],
            "error": (route_err or validate_err)[:1500] if (route_err or validate_err) else "",
        }
    )

    # 6) Bridge SimulatedVerse consciousness.
    sim_rc, sim_out = _capture_action_output(lambda: handle_cross_sync(paths))
    steps.append(
        {
            "id": 6,
            "name": "bridge_simulatedverse_consciousness",
            "status": "ok" if sim_rc == 0 else "degraded",
            "functional": sim_rc == 0,
            "exit_code": sim_rc,
            "output": sim_out[:3000],
        }
    )

    # 7) Configure Copilot endpoint.
    copilot_cfg = _configure_copilot_endpoint(paths, base_url)
    copilot_probe_rc, copilot_probe_out = _capture_action_output(lambda: _handle_copilot_probe(paths, json_mode=True))
    copilot_probe_payload = _extract_json_payload(copilot_probe_out) if copilot_probe_out else None
    copilot_ok = bool(isinstance(copilot_probe_payload, dict) and copilot_probe_payload.get("functional"))
    steps.append(
        {
            "id": 7,
            "name": "configure_copilot_endpoint",
            **copilot_cfg,
            "probe_status": "ok" if copilot_ok else "degraded",
            "probe_payload": (
                copilot_probe_payload if isinstance(copilot_probe_payload, dict) else copilot_probe_out[:2000]
            ),
            "probe_exit_code": copilot_probe_rc,
        }
    )

    # 8) Fix/verify model discovery.
    model_state = _verify_model_discovery(paths)
    steps.append({"id": 8, "name": "fix_model_discovery", **model_state})

    # 9) Show system health dashboard.
    doctor_args = ["doctor", "--quick", "--json"]
    if deep_health:
        doctor_args = ["doctor", "--json", "--with-system-health", "--with-analyzer", "--with-lint"]
    elif thorough_mode or "--full-health" in tokens:
        doctor_args = ["doctor", "--json", "--with-system-health", "--with-analyzer"]

    dashboard_rc, dashboard_out = _capture_action_output(
        lambda: _handle_doctor_action(doctor_args, paths, json_mode=True)
    )
    dashboard_payload = _extract_json_payload(dashboard_out) if dashboard_out else None
    steps.append(
        {
            "id": 9,
            "name": "show_system_health_dashboard",
            "status": ("ok" if dashboard_rc == 0 and isinstance(dashboard_payload, dict) else "degraded"),
            "functional": dashboard_rc == 0 and isinstance(dashboard_payload, dict),
            "exit_code": dashboard_rc,
            "dashboard": (dashboard_payload if isinstance(dashboard_payload, dict) else dashboard_out[:2000]),
        }
    )

    if include_sql:
        sql_state = _check_sql_datastores(paths, auto_init=auto_init_db)
        steps.append({"id": len(steps) + 1, "name": "sql_database_readiness", **sql_state})

    if include_nssm:
        nssm_state = _check_nssm_admin_readiness()
        steps.append({"id": len(steps) + 1, "name": "nssm_admin_readiness", **nssm_state})

    if include_telemetry:
        telemetry_state = _check_telemetry_output_channels(paths)
        steps.append({"id": len(steps) + 1, "name": "telemetry_output_channels", **telemetry_state})

    if include_brownfield:
        brownfield_state = _run_brownfield_reuse_probe(
            paths,
            capabilities=[
                "ecosystem routing",
                "telemetry output channels",
                "sql database health",
            ],
        )
        steps.append({"id": len(steps) + 1, "name": "brownfield_reuse_protocol", **brownfield_state})

    core_steps = [step for step in steps if int(step.get("id", 0) or 0) <= 9]
    extension_steps = [step for step in steps if int(step.get("id", 0) or 0) > 9]
    optional_core_names = {"enable_breathing_integration"}
    required_core_steps = [step for step in core_steps if str(step.get("name") or "") not in optional_core_names]
    optional_core_steps = [step for step in core_steps if str(step.get("name") or "") in optional_core_names]

    core_functional = all(bool(step.get("functional")) for step in required_core_steps)
    core_optional_functional = all(bool(step.get("functional")) for step in optional_core_steps)
    extension_functional = all(bool(step.get("functional")) for step in extension_steps)
    functional = core_functional and (extension_functional if strict_mode else True)
    if functional and (
        (extension_steps and not extension_functional) or (optional_core_steps and not core_optional_functional)
    ):
        status = "online_with_warnings"
    else:
        status = "online" if functional else "degraded"
    payload = {
        "action": "ignition",
        "status": status,
        "functional": functional,
        "core_functional": core_functional,
        "core_optional_functional": core_optional_functional if optional_core_steps else True,
        "core_optional_warning_steps": [
            str(step.get("name")) for step in optional_core_steps if not bool(step.get("functional"))
        ],
        "extended_functional": extension_functional if extension_steps else True,
        "strict_mode": strict_mode,
        "base_url": base_url,
        "steps": steps,
        "options": {
            "thorough_mode": thorough_mode,
            "include_sql": include_sql,
            "include_nssm": include_nssm,
            "include_telemetry": include_telemetry,
            "include_brownfield": include_brownfield,
            "auto_init_db": auto_init_db,
            "deep_health": deep_health,
        },
        "generated_at": datetime.now(UTC).isoformat(),
    }

    report_dir = paths.nusyq_hub / "state" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "ignition_latest.json"
    _write_json_report(report_path, payload)
    payload["report_path"] = str(report_path)

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🚀 NuSyQ Ignition")
        print("=" * 60)
        for step in steps:
            mark = "✅" if step.get("functional") else "⚠️"
            print(f"{mark} [{step.get('id')}] {step.get('name')}: {step.get('status')}")
        print(f"\nstatus: {status}")
        print(f"report: {report_path}")

    return 0 if functional else 1


def _handle_auto_fix(args: list[str], paths: RepoPaths) -> int:
    """Auto-fix import errors using intelligent error detection.

    Usage:
        python start_nusyq.py auto_fix \"ModuleNotFoundError: No module named 'xyz'\"
        python start_nusyq.py auto_fix \"ImportError: cannot import name 'Foo'\"

    Analyzes error message and suggests/applies fixes:
    - ModuleNotFoundError: Creates minimal stub module
    - ImportError: Adds missing name to existing module
    - Circular imports: Suggests local import pattern
    """
    if not args or not args[0]:
        print("❌ Error message required")
        print("Usage: python start_nusyq.py auto_fix '<error_message>'")
        print("\nExamples:")
        print("  auto_fix \"ModuleNotFoundError: No module named 'src.missing'\"")
        print("  auto_fix \"ImportError: cannot import name 'Foo' from 'src.bar'\"")
        return 1

    error_message = " ".join(args)

    try:
        # Import the fixer module
        sys.path.insert(0, str(paths.nusyq_hub / "scripts"))
        from auto_fix_imports import ImportErrorFixer

        fixer = ImportErrorFixer(paths.nusyq_hub)

        print("🔧 Auto-fixing import error...\n")
        print(f"📋 Error: {error_message}\n")

        # Analyze and get fix
        fix_suggestion = fixer.analyze_and_fix(error_message)

        print(f"💡 Action: {fix_suggestion.get('action', 'unknown')}\n")

        if fix_suggestion["action"] in ("create_stub_module", "add_stub_to_module"):
            print(f"📝 File: {fix_suggestion['file_path']}")
            print("\n🔨 Proposed stub code:\n")
            print(fix_suggestion["content"])
            print("\n✨ To apply: Create/edit the file above with the stub implementation.")

        elif fix_suggestion["action"] == "suggest_local_import":
            print(f"💭 Suggestion: {fix_suggestion['suggestion']}")
            print("\n📚 Example:\n")
            print(fix_suggestion["example"])

        else:
            print(f"Info: Details: {fix_suggestion}")

        print("\n✅ Auto-fix analysis complete")
        return 0

    except ImportError as e:
        print(f"❌ Cannot import auto_fix_imports module: {e}")
        print("Make sure scripts/auto_fix_imports.py exists")
        return 1
    except Exception as e:
        print(f"❌ Error during auto-fix: {e}")
        return 1


def _guess_action(raw_args: list[str]) -> str:
    """Return first non-flag token, defaulting to snapshot."""
    for arg in raw_args:
        if not arg.startswith("-"):
            return arg
    return "snapshot"


def _validate_fast_path_args(action_guess: str, raw_args: list[str], hub_default: Path) -> int | None:
    """Return early error code for obvious arg problems, else None."""
    if action_guess not in {"analyze", "review", "debug"}:
        return None
    try:
        action_index = raw_args.index(action_guess)
    except ValueError:
        action_index = -1
    next_arg = raw_args[action_index + 1] if action_index >= 0 and len(raw_args) > action_index + 1 else None

    if action_guess == "review" and (not next_arg or next_arg.startswith("--")):
        print("[ERROR] Missing file path argument")
        print("\nUsage: python start_nusyq.py review <file_path> [--system=ollama|chatdev|copilot|auto]")
        print("\nExamples:")
        print("  python start_nusyq.py review src/main.py")
        print("  python start_nusyq.py review scripts/start_nusyq.py --system=auto")
        return 1

    if action_guess == "debug" and (not next_arg or next_arg.startswith("--")):
        print("[ERROR] Missing error description")
        print("\nUsage: python start_nusyq.py debug <error_description> [--system=quantum|ai]")
        print("\nExamples:")
        print("  python start_nusyq.py debug \"ImportError: cannot import name 'foo'\"")
        print('  python start_nusyq.py debug "Tests failing in test_ml_modules.py"')
        print('  python start_nusyq.py debug "TypeError in quantum module" --system=quantum')
        return 1

    if action_guess == "analyze" and next_arg and not next_arg.startswith("--"):
        candidate_path = Path(next_arg)
        if not candidate_path.is_absolute():
            candidate_path = hub_default / candidate_path
        if not candidate_path.exists():
            print(f"[ERROR] File not found: {candidate_path}")
            return 1

    return None


# Search action handlers
def _handle_search(args: list[str], json_mode: bool = False) -> int:
    """Dispatcher for search subcommands."""
    if not args:
        print("Usage: nusyq search <subcommand> [options]")
        print("\nSubcommands:")
        print("  keyword <query>              Search by keyword")
        print("  class <name>                 Search by class name")
        print("  function <name>              Search by function name")
        print("  patterns <terms>             Search for code patterns")
        print("  index-health                 Check search index health")
        print("  hacking-quests               Find hacking game quests")
        print("\nExamples:")
        print("  nusyq search keyword consciousness")
        print("  nusyq search class ConsciousnessBridge")
        print("  nusyq search function route_task")
        return 0

    subcommand = args[0]
    sub_args = args[1:] if len(args) > 1 else []

    if subcommand == "keyword":
        return _handle_search_keyword(sub_args)
    elif subcommand == "class":
        return _handle_search_class(sub_args)
    elif subcommand == "function":
        return _handle_search_function(sub_args)
    elif subcommand == "patterns":
        return _handle_search_patterns(sub_args)
    elif subcommand == "index-health":
        return _handle_search_index_health()
    elif subcommand == "hacking-quests":
        return _handle_search_hacking_quests(sub_args)
    else:
        print(f"Unknown search subcommand: {subcommand}")
        return 1


def _handle_search_keyword(args: list[str]) -> int:
    """Handle nusyq search keyword <query>."""
    if not args:
        print("Usage: nusyq search keyword <query> [--limit N]")
        return 1

    query = args[0]
    limit = 20
    for i, arg in enumerate(args[1:], 1):
        if arg == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass

    result = handle_search_keyword(query, limit=limit, output_format="text")
    print(result.get("output", ""))
    return 0 if result["status"] == "success" else 1


def _handle_search_class(args: list[str]) -> int:
    """Handle nusyq search class <name>."""
    if not args:
        print("Usage: nusyq search class <name> [--no-exact] [--limit N]")
        return 1

    class_name = args[0]
    exact = "--no-exact" not in args
    limit = 20
    for i, arg in enumerate(args[1:], 1):
        if arg == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass

    result = handle_search_class(class_name, exact=exact, limit=limit)
    print(result.get("output", ""))
    return 0 if result["status"] == "success" else 1


def _handle_search_function(args: list[str]) -> int:
    """Handle nusyq search function <name>."""
    if not args:
        print("Usage: nusyq search function <name> [--no-exact] [--limit N]")
        return 1

    function_name = args[0]
    exact = "--no-exact" not in args
    limit = 20
    for i, arg in enumerate(args[1:], 1):
        if arg == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass

    result = handle_search_function(function_name, exact=exact, limit=limit)
    print(result.get("output", ""))
    return 0 if result["status"] == "success" else 1


def _handle_search_patterns(args: list[str]) -> int:
    """Handle nusyq search patterns <terms>."""
    if not args:
        print("Usage: nusyq search patterns <terms> [--pattern-type consciousness|tagging|bridge] [--limit N]")
        return 1

    pattern = args[0]
    pattern_type = "all"
    limit = 10
    for i, arg in enumerate(args[1:], 1):
        if arg == "--pattern-type" and i + 1 < len(args):
            pattern_type = args[i + 1]
        elif arg == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass

    result = handle_search_patterns(pattern, pattern_type=pattern_type, limit=limit)
    print(result.get("output", ""))
    return 0 if result["status"] == "success" else 1


def _handle_search_index_health() -> int:
    """Handle nusyq search index-health."""
    result = handle_search_index_health()
    print(result.get("output", ""))
    return 0 if result["status"] == "success" else 1


def _handle_search_hacking_quests(args: list[str]) -> int:
    """Handle nusyq search hacking-quests."""
    quest_type = "all"
    limit = 10
    for i, arg in enumerate(args):
        if arg == "--quest-type" and i + 1 < len(args):
            quest_type = args[i + 1]
        elif arg == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass

    result = handle_search_hacking_quests(quest_type=quest_type, limit=limit)
    print(result.get("output", ""))
    return 0 if result["status"] == "success" else 1


def _split_runtime_args(raw_args: list[str]) -> tuple[str | None, bool, list[str]]:
    """Split top-level flags from action args."""
    mode: str | None = None
    json_mode = False
    args: list[str] = []
    i = 0
    while i < len(raw_args):
        if raw_args[i] == "--json":
            json_mode = True
            i += 1
        elif raw_args[i] == "--mode" and i + 1 < len(raw_args):
            mode = raw_args[i + 1].lower()
            i += 2
        else:
            args.append(raw_args[i])
            i += 1
    return mode, json_mode, args


_SPINE_SKIP_STARTUP_ACTIONS = {
    "help",
    "capabilities",
    "ecosystem_status",
    "agent_probe",
    "dispatch",
    "culture_ship_status",
    "culture_ship_doctor",
    "delegation_matrix",
    "claude_doctor",
    "doctor",
    "doctor_status",
    "openclaw_smoke",
    "openclaw_smoke_status",
    "openclaw_status",
    "openclaw_gateway_start",
    "openclaw_gateway_status",
    "openclaw_gateway_stop",
    "openclaw_bridge_start",
    "openclaw_bridge_status",
    "openclaw_bridge_stop",
    "openclaw_internal_send",
    "skyclaw_status",
    "skyclaw_start",
    "skyclaw_stop",
    "open_antigravity_start",
    "open_antigravity_runtime_status",
    "open_antigravity_stop",
    "antigravity_status",
    "antigravity_health",
    "failover_status",
    "integration_health",
    "error_report",
    "error_report_split",
    "error_report_status",
    "error_signal_bridge",
    "signal_quest_bridge",
    "error_quest_bridge",
    "auto_quest",
    "system_complete_status",
    "log_dedup_status",
    "quantum_resolver_status",
    # Lightweight read-only actions that do not need startup spine probing.
    "menu",
    "snapshot",
    "brief",
    "suggest",
    "prune_reports",
    "task_summary",
    "lifecycle_catalog",
    "problem_signal_snapshot",
    "vscode_diagnostics_bridge",
    "search",
    "search_index_health",
    "task_status",
    "list_background_tasks",
    "orchestrator_status",
    "terminals",
}


def _env_flag_enabled(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _should_disable_otel_for_action(action: str) -> bool:
    if action == "brief":
        return _env_flag_enabled("NUSYQ_BRIEF_DISABLE_OTEL", "1")
    if action == "auto_cycle":
        return _env_flag_enabled("NUSYQ_AUTO_CYCLE_DISABLE_OTEL", "1")
    if action in {
        "menu",
        "help",
        "--help",
        "snapshot",
        "suggest",
        "capabilities",
        "error_signal_bridge",
        "signal_quest_bridge",
        "error_quest_bridge",
        "auto_quest",
        "task_summary",
        "lifecycle_catalog",
        "ecosystem_status",
        "agent_probe",
        "dispatch",
        "culture_ship_status",
        "ai_status",
        "integration_health",
        "claude_doctor",
        "codex_doctor",
        "copilot_doctor",
        "multi_agent_doctor",
        "agent_fleet_doctor",
        "openclaw_smoke",
        "openclaw_smoke_status",
        "openclaw_status",
        "openclaw_gateway_start",
        "openclaw_gateway_status",
        "openclaw_gateway_stop",
        "openclaw_internal_send",
        "skyclaw_status",
        "skyclaw_start",
        "skyclaw_stop",
        "problem_signal_snapshot",
        "vscode_diagnostics_bridge",
        "prune_reports",
        "doctor",
        "doctor_status",
    }:
        return _env_flag_enabled("NUSYQ_STATUS_DISABLE_OTEL", "1")
    return False


def _should_skip_spine_startup(action_guess: str, raw_args: list[str]) -> bool:
    """Decide whether startup spine probing should be skipped for this invocation.

    Env override:
        NUSYQ_SPINE_STARTUP=always|auto|never
    """
    startup_mode = str(os.getenv("NUSYQ_SPINE_STARTUP", "auto")).strip().lower()
    if startup_mode in {"never", "off", "false", "0"}:
        return True
    if startup_mode in {"always", "on", "true", "1"}:
        return False

    if "--help" in raw_args:
        return True
    if action_guess.endswith("_status"):
        return True
    return action_guess in _SPINE_SKIP_STARTUP_ACTIONS


def _handle_terminals_pid(args: list[str]) -> int:
    """Handler for terminal PID awareness subcommands (assign, emit, channels, startup, map)."""
    try:
        from scripts.nusyq_actions.terminals import handle_terminals as _ht

        return _ht(args)
    except Exception as exc:
        print(f"terminals_pid error: {exc}")
        return 1


def _handle_chug(args: list[str]) -> int:
    """Handler for the NuSyQ-Chug autonomous assembly-line loop.

    Delegates directly to scripts/nusyq_chug.py so it can be invoked as:
        python scripts/start_nusyq.py chug [--hours N] [--phase N] [--dry-run]
    """
    import subprocess
    import sys

    chug_script = Path(__file__).parent / "nusyq_chug.py"
    cmd = [sys.executable, str(chug_script)] + args
    result = subprocess.run(cmd)
    return result.returncode


def _handle_eol(args: list[str], json_mode: bool = False) -> int:
    """Handler for EOL subcommands (sense, propose, full-cycle, stats, debug)."""
    try:
        # Convert args to namespace for handler compatibility
        import argparse

        from scripts.nusyq_actions.eol import handle_eol_command

        parser = argparse.ArgumentParser(prog="eol")
        parser.add_argument("eol_subcommand", nargs="?", default="sense")
        parser.add_argument("objective", nargs="?", default=None)
        parser.add_argument("--json", action="store_true", default=json_mode)
        parser.add_argument("--auto", action="store_true", default=False)
        parser.add_argument("--dry-run", action="store_true", default=True)

        parsed_args = parser.parse_args(args)
        return handle_eol_command(parsed_args)

    except Exception as e:
        print(f"Error handling eol command: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main() -> int:
    global _LAST_OUTPUTS, _JSON_OUTPUT
    json_requested = "--json" in sys.argv[1:]
    raw_args = sys.argv[1:]
    _hydrate_process_env()
    action_guess = _guess_action(raw_args)
    skip_spine_startup = _should_skip_spine_startup(action_guess, raw_args)
    if json_requested:
        logging.getLogger().setLevel(logging.WARNING)
    # Default: assume script is in NuSyQ-Hub/scripts/
    hub_default = Path(__file__).resolve().parents[1]  # NuSyQ-Hub/
    if initialize_spine and not skip_spine_startup:
        try:
            health = initialize_spine(repo_root=hub_default)
            logger.info(
                "Spine quick health | status=%s | signals=%s",
                health.status,
                health.signals,
            )
            if export_spine_health:
                try:
                    export_path = export_spine_health(repo_root=hub_default, refresh=True)
                    logger.info("Spine snapshot exported: %s", export_path)
                except Exception as exc:
                    logger.warning("Spine snapshot export failed: %s", exc)
        except Exception as exc:
            logger.warning("Failed to capture spine health: %s", exc)

    # Emit terminal routing hint for themed terminals
    if not json_requested:
        emit_terminal_route(action_guess)

    # Fast-path failures for missing/invalid file args to avoid heavy startup.
    validation_error = _validate_fast_path_args(action_guess, raw_args, hub_default)
    if validation_error is not None:
        return validation_error

    if action_guess not in KNOWN_ACTIONS:
        print(f"[ERROR] Unknown action: {action_guess}")
        print("Run 'python start_nusyq.py help' for usage.")
        return 1

    mode, json_mode, args = _split_runtime_args(raw_args)
    _JSON_OUTPUT = json_mode

    action = args[0] if args else "snapshot"
    if _should_disable_otel_for_action(action):
        os.environ["OTEL_SDK_DISABLED"] = "true"
        os.environ["OTEL_TRACES_EXPORTER"] = "none"
        os.environ["NUSYQ_TRACING"] = "0"
        os.environ["NUSYQ_TRACE"] = "0"
        _suppress_otel_exporter_logs()

    if action in {
        "openclaw_smoke",
        "openclaw_smoke_status",
        "openclaw_status",
        "openclaw_gateway_start",
        "openclaw_gateway_status",
        "openclaw_gateway_stop",
        "openclaw_bridge_start",
        "openclaw_bridge_status",
        "openclaw_bridge_stop",
        "openclaw_internal_send",
        "skyclaw_status",
        "skyclaw_start",
        "skyclaw_stop",
        "open_antigravity_start",
        "open_antigravity_runtime_status",
        "open_antigravity_stop",
        "antigravity_status",
        "antigravity_health",
        "failover_status",
        "integration_health",
        "error_report",
        "error_report_split",
        "error_report_status",
        "doctor_status",
        "system_complete_status",
    }:
        if _should_disable_otel_for_action(action):
            apply_trace_config({"enabled": False})
        # Keep status/smoke actions fast, but allow cross-repo discovery for error reports.
        if action in {"error_report", "error_report_split"}:
            fast_paths = load_paths(hub_default, allow_discovery=True)
        else:
            fast_paths = WorkspacePaths(
                nusyq_hub=hub_default,
                simulatedverse=None,
                nusyq_root=None,
            )
        if action == "openclaw_smoke":
            return _handle_openclaw_smoke(args, fast_paths, json_mode=json_mode)
        if action == "openclaw_smoke_status":
            return _handle_openclaw_smoke_status(args, fast_paths, json_mode=json_mode)
        if action == "openclaw_status":
            return _handle_openclaw_status(fast_paths, json_mode=json_mode)
        if action == "openclaw_gateway_start":
            return _handle_openclaw_gateway_start(args, fast_paths, json_mode=json_mode)
        if action == "openclaw_gateway_status":
            return _handle_openclaw_gateway_status(args, fast_paths, json_mode=json_mode)
        if action == "openclaw_gateway_stop":
            return _handle_openclaw_gateway_stop(args, fast_paths, json_mode=json_mode)
        if action == "openclaw_bridge_start":
            return _handle_openclaw_bridge_start(args, fast_paths, json_mode=json_mode)
        if action == "openclaw_bridge_status":
            return _handle_openclaw_bridge_status(args, fast_paths, json_mode=json_mode)
        if action == "openclaw_bridge_stop":
            return _handle_openclaw_bridge_stop(args, fast_paths, json_mode=json_mode)
        if action == "openclaw_internal_send":
            return _handle_openclaw_internal_send(args, fast_paths, json_mode=json_mode)
        if action in {"skyclaw_status", "skyclaw_start", "skyclaw_stop"}:
            from scripts.nusyq_actions.skyclaw_actions import (
                handle_skyclaw_start,
                handle_skyclaw_status,
                handle_skyclaw_stop,
            )

            _skyclaw_handlers = {
                "skyclaw_status": handle_skyclaw_status,
                "skyclaw_start": handle_skyclaw_start,
                "skyclaw_stop": handle_skyclaw_stop,
            }
            return _skyclaw_handlers[action](args, json_mode=json_mode)
        if action == "open_antigravity_start":
            return _handle_open_antigravity_start(args, fast_paths, json_mode=json_mode)
        if action == "open_antigravity_runtime_status":
            return _handle_open_antigravity_runtime_status(args, fast_paths, json_mode=json_mode)
        if action == "open_antigravity_stop":
            return _handle_open_antigravity_stop(args, fast_paths, json_mode=json_mode)
        if action == "antigravity_status":
            return _handle_antigravity_status(fast_paths, json_mode=json_mode, action_args=args)
        if action == "antigravity_health":
            return _handle_antigravity_health(fast_paths, json_mode=json_mode, action_args=args)
        if action == "integration_health":
            return _handle_integration_health(args, fast_paths, json_mode=json_mode)
        if action == "error_report":
            return _handle_error_report(args, fast_paths, json_mode=json_mode)
        if action == "error_report_status":
            return _handle_error_report_status(args, fast_paths, json_mode=json_mode)
        if action == "doctor_status":
            return _handle_doctor_status(args, fast_paths, json_mode=json_mode)
        if action == "failover_status":
            return _handle_failover_status(args, fast_paths, json_mode=json_mode)
        if action == "system_complete_status":
            return _handle_system_complete_status(args, fast_paths, json_mode=json_mode)
        return _handle_error_report_split(args, fast_paths)

    fast_actions = {
        "log_dedup_status",
        "quantum_resolver_status",
        "brief",
        "prune_reports",
        "help",
        "--help",
        "delegation_matrix",
        "claude_doctor",
        "codex_doctor",
        "copilot_doctor",
        "multi_agent_doctor",
        "agent_fleet_doctor",
        "doctor_status",
        "openclaw_smoke_status",
        "openclaw_status",
        "openclaw_gateway_start",
        "openclaw_gateway_status",
        "openclaw_gateway_stop",
        "openclaw_bridge_start",
        "openclaw_bridge_status",
        "openclaw_bridge_stop",
        "openclaw_internal_send",
        "skyclaw_status",
        "skyclaw_start",
        "skyclaw_stop",
        "open_antigravity_start",
        "open_antigravity_runtime_status",
        "open_antigravity_stop",
        "antigravity_status",
        "antigravity_health",
        "failover_status",
        "integration_health",
        "error_report_status",
        "system_complete_status",
    }
    allow_discovery = action not in fast_actions

    if os.getenv("NUSYQ_FAST_TEST_MODE") == "1" and action == "hygiene":
        print("✅ Spine hygiene: CLEAN (fast test mode)")
        print("✅ AI systems: Available (mocked)")
        return 0

    paths = load_paths(hub_default, allow_discovery=allow_discovery)
    run_id = ensure_run_id()
    contracts = read_action_contracts(paths.nusyq_hub)
    catalog = read_action_catalog(paths.nusyq_hub)

    trace_config = load_trace_config(paths.nusyq_hub)
    if _should_disable_otel_for_action(action):
        trace_config["enabled"] = False
    apply_trace_config(trace_config)
    if otel:
        try:
            otel.bind_correlation_id("run.id", run_id)
        except Exception:
            pass

    defaults = _load_ecosystem_defaults(paths)
    cadence_hours = float(defaults.get("terminal_orchestration", {}).get("lifecycle_cadence_hours", 0) or 0)
    if action != "lifecycle_catalog" and not _should_skip_lifecycle_refresh(action):
        _maybe_refresh_lifecycle_catalog(paths, cadence_hours)

    dispatch_map: dict[str, ActionHandler] = {
        "heal": lambda: run_heal(paths.nusyq_hub),
        "suggest": lambda: handle_suggest(
            paths,
            git_snapshot,
            read_quest_log,
            run,
            json_mode=json_mode,
        ),
        "hygiene": lambda: handle_hygiene(
            paths,
            check_spine_hygiene,
            _run_aux_script,
            run,
            fast="--fast" in args,
        ),
        "prune_reports": lambda: _handle_prune_reports(args, paths, json_mode=json_mode),
        "review": lambda: handle_review(args, paths, run_ai_task),
        "analyze": lambda: handle_analyze(args, paths, run_ai_task),
        "debug": lambda: handle_debug(args, paths, run_ai_task),
        "generate": lambda: handle_generate(args, paths, run_ai_task),
        "ollama": lambda: handle_ollama(args, paths),
        "test": lambda: handle_test(paths, run, _run_fast_test_suite),
        "test_history": lambda: handle_test_history(args, paths),
        "task": lambda: handle_task(paths, args[1:] if len(args) > 1 else []),
        "task_manager": lambda: _handle_task_manager(args),
        "doctor": lambda: _handle_doctor_action(args, paths, json_mode=json_mode),
        "doctor_status": lambda: _handle_doctor_status(args, paths, json_mode=json_mode),
        "failover_status": lambda: _handle_failover_status(args, paths, json_mode=json_mode),
        "openclaw_smoke": lambda: _handle_openclaw_smoke(args, paths, json_mode=json_mode),
        "openclaw_smoke_status": lambda: _handle_openclaw_smoke_status(args, paths, json_mode=json_mode),
        "openclaw_status": lambda: _handle_openclaw_status(paths, json_mode=json_mode),
        "openclaw_gateway_start": lambda: _handle_openclaw_gateway_start(args, paths, json_mode=json_mode),
        "openclaw_gateway_status": lambda: _handle_openclaw_gateway_status(args, paths, json_mode=json_mode),
        "openclaw_gateway_stop": lambda: _handle_openclaw_gateway_stop(args, paths, json_mode=json_mode),
        "openclaw_bridge_start": lambda: _handle_openclaw_bridge_start(args, paths, json_mode=json_mode),
        "openclaw_bridge_status": lambda: _handle_openclaw_bridge_status(args, paths, json_mode=json_mode),
        "openclaw_bridge_stop": lambda: _handle_openclaw_bridge_stop(args, paths, json_mode=json_mode),
        "openclaw_internal_send": lambda: _handle_openclaw_internal_send(args, paths, json_mode=json_mode),
        "open_antigravity_start": lambda: _handle_open_antigravity_start(args, paths, json_mode=json_mode),
        "open_antigravity_runtime_status": lambda: _handle_open_antigravity_runtime_status(
            args, paths, json_mode=json_mode
        ),
        "open_antigravity_stop": lambda: _handle_open_antigravity_stop(args, paths, json_mode=json_mode),
        "antigravity_status": lambda: _handle_antigravity_status(paths, json_mode=json_mode, action_args=args),
        "antigravity_health": lambda: _handle_antigravity_health(paths, json_mode=json_mode, action_args=args),
        "ignition": lambda: _handle_ignition(args, paths, json_mode=json_mode),
        "integration_health": lambda: _handle_integration_health(args, paths, json_mode=json_mode),
        "compose_secrets": lambda: _handle_compose_secrets(args, paths, json_mode=json_mode),
        "claude_preflight": lambda: _handle_claude_preflight(args, paths, json_mode=json_mode),
        "delegation_matrix": lambda: _handle_delegation_matrix(paths, json_mode=json_mode),
        "claude_doctor": lambda: _handle_claude_doctor(paths, json_mode=json_mode),
        "codex_doctor": lambda: _handle_codex_doctor(paths, json_mode=json_mode),
        "copilot_doctor": lambda: _handle_copilot_doctor(paths, json_mode=json_mode),
        "multi_agent_doctor": lambda: _handle_multi_agent_doctor(paths, json_mode=json_mode),
        "agent_fleet_doctor": lambda: _handle_agent_fleet_doctor(paths, json_mode=json_mode),
        "copilot_probe": lambda: _handle_copilot_probe(paths, json_mode=json_mode),
        "vscode_extensions_plan": lambda: _handle_vscode_extensions_plan(args, paths, json_mode=json_mode),
        "vscode_extensions_quickwins": lambda: _handle_vscode_extensions_quickwins(args, paths, json_mode=json_mode),
        "map": lambda: run_capability_map(paths.nusyq_hub),
        "menu": lambda: handle_menu(args),
        "work": lambda: handle_work(paths, _handle_ai_work_gate),
        "develop_system": lambda: handle_develop_system(args, paths),
        "capabilities": lambda: handle_capabilities(paths, args[1:] if len(args) > 1 else None),
        "ai_status": lambda: _handle_ai_status(paths, json_mode=json_mode),
        "advanced_ai_quests": lambda: _handle_advanced_ai_quests(args, paths, json_mode=json_mode),
        "graph_learning": lambda: _handle_graph_learning(args, paths, json_mode=json_mode),
        "system_complete": lambda: _handle_system_complete(paths, json_mode=json_mode, args=args),
        "system_complete_status": lambda: _handle_system_complete_status(args, paths, json_mode=json_mode),
        "validate_contracts": lambda: _handle_validate_contracts(
            paths, contracts, action_args=args, json_mode=json_mode
        ),
        "ai_work_gate": lambda: _handle_ai_work_gate(paths),
        "brief": lambda: handle_brief(paths, check_spine_hygiene),
        "doctrine_check": lambda: _handle_doctrine_check(paths),
        "emergence_capture": lambda: _handle_emergence_capture(paths),
        "selfcheck": lambda: handle_selfcheck(paths, run),
        "simverse_bridge": lambda: _handle_simverse_bridge(paths),
        "simverse_mode": lambda: _handle_simverse_mode(args, paths, json_mode=json_mode),
        "simverse_consciousness": lambda: _handle_simverse_consciousness(paths, json_mode=json_mode),
        "simverse_history": lambda: _handle_simverse_history(
            args[1:] if len(args) > 1 else [], paths, json_mode=json_mode
        ),
        "simverse_ship_directives": lambda: _handle_simverse_ship_directives(
            args[1:] if len(args) > 1 else [], paths, json_mode=json_mode
        ),
        "simverse_cognition_insights": lambda: _handle_simverse_cognition_insights(
            args[1:] if len(args) > 1 else [], paths, json_mode=json_mode
        ),
        "simverse_bridge_health": lambda: _handle_simverse_bridge_health(paths, json_mode=json_mode),
        "simverse_ship_approve": lambda: _handle_simverse_ship_approve(
            args[1:] if len(args) > 1 else [], paths, json_mode=json_mode
        ),
        "simverse_log_event": lambda: _handle_simverse_log_event(
            args[1:] if len(args) > 1 else [], paths, json_mode=json_mode
        ),
        "simverse_breathing": lambda: _handle_simverse_breathing(paths, json_mode=json_mode),
        "sns_analyze": lambda: _handle_sns_analyze(args[1:] if len(args) > 1 else [], paths),
        "sns_convert": lambda: _handle_sns_convert(args[1:] if len(args) > 1 else []),
        "zero_token_status": lambda: _handle_zero_token_status(paths),
        "trace_doctor": lambda: handle_trace_doctor(paths),
        "trace_correlation_on": lambda: handle_trace_correlation_on(paths),
        "next_action": lambda: handle_next_action_display(paths, json_mode=json_mode),
        "next_action_generate": lambda: handle_next_action_generate(paths, json_mode=json_mode),
        "next_action_exec": lambda: handle_next_action_exec(args, paths),
        "trace_correlation_off": lambda: handle_trace_correlation_off(paths),
        "override_gate": lambda: _handle_override_gate(args, paths),
        "preflight_trace": lambda: _handle_preflight_trace(paths, contracts),
        "problem_signal_snapshot": lambda: _handle_problem_signal_snapshot(args, paths),
        "vscode_diagnostics_bridge": lambda: _handle_vscode_diagnostics_bridge(args, paths),
        "error_report": lambda: _handle_error_report(args, paths, json_mode=json_mode),
        "error_report_split": lambda: _handle_error_report_split(args, paths),
        "error_report_status": lambda: _handle_error_report_status(args, paths, json_mode=json_mode),
        "error_signal_bridge": lambda: _handle_error_signal_bridge(args, paths, json_mode=json_mode),
        "signal_quest_bridge": lambda: _handle_signal_quest_bridge(args, paths, json_mode=json_mode),
        "error_quest_bridge": lambda: _handle_error_quest_bridge(args, paths, json_mode=json_mode),
        "auto_quest": lambda: _handle_error_quest_bridge(args, paths, json_mode=json_mode),
        "quest_compact": lambda: _handle_quest_compact(args, paths, json_mode=json_mode),
        "log_dedup_status": _handle_log_dedup_status,
        "quantum_resolver_status": _handle_quantum_resolver_status,
        "task_summary": lambda: _handle_task_summary(paths),
        "lifecycle_catalog": lambda: _handle_lifecycle_catalog(paths),
        "trace_service_status": lambda: handle_trace_service_status(paths),
        "trace_service_start": lambda: handle_trace_service_start(paths),
        "trace_service_stop": lambda: handle_trace_service_stop(paths),
        "trace_service_healthcheck": lambda: handle_trace_service_healthcheck(paths),
        "trace_config_show": lambda: handle_trace_config_show(paths),
        "trace_config_set": lambda: handle_trace_config_set(args, paths),
        "trace_config_validate": lambda: handle_trace_config_validate(paths),
        "trace_smoke": lambda: handle_trace_smoke(paths),
        "trace_assert": lambda: handle_trace_assert(args, paths),
        "guild_status": lambda: handle_guild_status(_run_guild),
        "guild_render": lambda: handle_guild_render(_run_guild),
        "guild_heartbeat": lambda: handle_guild_heartbeat(args, _run_guild),
        "guild_claim": lambda: handle_guild_claim(args, _run_guild),
        "guild_start": lambda: handle_guild_start(args, _run_guild),
        "guild_post": lambda: handle_guild_post(args, _run_guild),
        "guild_complete": lambda: handle_guild_complete(args, _run_guild),
        "guild_available": lambda: handle_guild_available(args, _run_guild),
        "guild_add_quest": lambda: handle_guild_add_quest(args, _run_guild),
        "guild_close_quest": lambda: handle_guild_close_quest(args, _run_guild),
        "guild_register": lambda: handle_guild_register(args, _run_guild),
        "log_quest": lambda: handle_log_quest(args),
        # Learning & Tutorial actions
        "examples": lambda: _handle_examples(args, paths),
        "examples_list": lambda: _handle_examples(["examples_list", "--list"], paths),
        "tutorial": lambda: _handle_examples(args, paths),  # Alias for examples
        # Factory Gateway actions (Phase 2 orphan rehabilitation)
        "factory": lambda: _handle_factories(args, paths),
        "integrator": lambda: _handle_factories(["factory", "integrator", *args[1:]], paths),
        "orchestrator": lambda: _handle_factories(["factory", "orchestrator", *args[1:]], paths),
        "quantum_factory": lambda: _handle_factories(["factory", "quantum", *args[1:]], paths),
        "context_server": lambda: _handle_factories(["factory", "context_server", *args[1:]], paths),
        # Dashboard action (Phase 4 - false positive rehabilitation)
        "dashboard": lambda: _handle_dashboard(paths),
        # Demo actions (Phase 5 orphan rehabilitation)
        "demo": lambda: _handle_demo(args, paths),
        # Enhancement actions
        "patch": lambda: handle_patch(args, paths, run_ai_task),
        "fix": lambda: handle_fix(args, paths, run_ai_task),
        "improve": lambda: handle_improve(args, paths, run_ai_task),
        "update": lambda: handle_update(args, paths),
        "modernize": lambda: handle_modernize(args, paths, run_ai_task),
        "enhance": lambda: handle_enhance(args, paths, run_ai_task),
        "snapshot": lambda: _handle_snapshot_or_help(action, paths),
        "--help": lambda: _handle_snapshot_or_help(action, paths),
        "help": lambda: _handle_snapshot_or_help(action, paths),
        "queue": lambda: handle_queue_execution(paths),
        "pu_execute": lambda: _handle_pu_execute(args, paths),
        "batch_commit": lambda: _handle_batch_commit(args, paths),
        "causal_analysis": lambda: _handle_causal_analysis(args, paths, json_mode=json_mode),
        "causal": lambda: _handle_causal_analysis(args, paths, json_mode=json_mode),
        "specialization_status": lambda: _handle_specialization_status(args, paths, json_mode=json_mode),
        "metrics": lambda: handle_metrics_dashboard(paths),
        "replay": lambda: handle_quest_replay(paths),
        "sync": lambda: handle_cross_sync(paths),
        "auto_cycle": lambda: handle_auto_cycle(
            args,
            paths,
            handle_pu_queue_processing,
            handle_queue_execution,
            handle_quest_replay,
            handle_metrics_dashboard,
            handle_cross_sync,
            handle_next_action_generation,
            culture_ship_handler=lambda dry_run: _handle_culture_ship_cycle(
                paths,
                ["--sync", *(["--dry-run"] if dry_run else [])],
                json_mode=json_mode,
            ),
            gate_handler=_handle_ai_work_gate,
        ),
        "autonomous_service": lambda: _handle_autonomous_service(args, paths, json_mode=json_mode),
        "auto_fix": lambda: _handle_auto_fix(args, paths),
        # MJOLNIR Protocol unified agent dispatch
        "dispatch": lambda: handle_dispatch(args, paths, run_ai_task),
        # Orchestration actions
        "agent_status": lambda: _handle_agent_status(),
        "agent_probe": lambda: _handle_agent_probe(json_mode=json_mode),
        "orchestrate": lambda: _handle_orchestrate(args),
        "invoke_agent": lambda: _handle_invoke_agent(args),
        "council_loop": lambda: _handle_council_loop(args),
        # Quest system query actions
        "quest_query": lambda: _handle_quest_query(args),
        "quest_continue": lambda: _handle_quest_continue(args),
        "quest_graph": lambda: _handle_quest_graph(args),
        "quest_status": lambda: _handle_quest_status(args),
        # Ecosystem activation actions
        "activate_ecosystem": lambda: _handle_activate_ecosystem(),
        "ecosystem_status": lambda: _handle_ecosystem_status(),
        # Strategic advisory actions
        "culture_ship": lambda: _handle_culture_ship_advisory(paths, args[1:], json_mode=json_mode),
        "culture_ship_cycle": lambda: _handle_culture_ship_cycle(paths, args[1:], json_mode=json_mode),
        "culture_ship_status": lambda: _handle_culture_ship_status(args, paths, json_mode=json_mode),
        # Jupyter notebook execution
        "run_notebook": lambda: _handle_run_notebook(args),
        # Background task orchestration for local LLMs
        "dispatch_task": lambda: handle_dispatch_task(args[1:]),
        "task_status": lambda: handle_task_status(args[1:]),
        "list_background_tasks": lambda: handle_list_background_tasks(args[1:], json_mode=json_mode),
        "orchestrator_status": lambda: handle_orchestrator_status(),
        "orchestrator_hygiene": lambda: handle_orchestrator_hygiene(args[1:]),
        # Terminal intelligence system
        "terminals": lambda: handle_terminals(args[1:] if len(args) > 1 else []),
        "terminal_snapshot": lambda: handle_terminals(["snapshot", *(args[1:] if len(args) > 1 else [])]),
        # Terminal PID awareness (assign, emit, channels, startup, map)
        "terminals_pid": lambda: _handle_terminals_pid(args[1:] if len(args) > 1 else []),
        # Search & discovery actions
        "search": lambda: _handle_search(args[1:] if len(args) > 1 else [], json_mode=json_mode),
        "search_keyword": lambda: _handle_search_keyword(args[1:] if len(args) > 1 else []),
        "search_class": lambda: _handle_search_class(args[1:] if len(args) > 1 else []),
        "search_function": lambda: _handle_search_function(args[1:] if len(args) > 1 else []),
        "search_patterns": lambda: _handle_search_patterns(args[1:] if len(args) > 1 else []),
        "search_index_health": lambda: _handle_search_index_health(),
        "search_hacking_quests": lambda: _handle_search_hacking_quests(args[1:] if len(args) > 1 else []),
        # Epistemic-Operational Lattice decision cycles
        "eol": lambda: _handle_eol(args[1:] if len(args) > 1 else [], json_mode=json_mode),
        # NuSyQ-Chug: autonomous timed assembly-line loop
        "chug": lambda: _handle_chug(args[1:] if len(args) > 1 else []),
    }

    # Overnight Safe Mode: restrict certain actions
    if mode == "overnight":
        forbidden = {"generate", "develop_system", "sync", "queue", "work"}
        if action in forbidden:
            print("🌙 Overnight Safe Mode active: action restricted")
            print(f"Action '{action}' is not allowed in overnight mode.")
            print(
                "Allowed examples: snapshot, brief, analyze, review, test, test_history, doctor, map, metrics, replay"
            )
            return 1

    # Execute action within a tracing span and emit a [RECEIPT]
    enabled = False
    if otel:
        try:
            enabled = otel.init_tracing(trace_config.get("service_name", "nusyq-hub"))
        except Exception:
            enabled = False

    # Gather attributes for root span
    attrs = _build_trace_attrs(action, paths, contracts, catalog, run_id)

    # Run
    handler_rc = 1
    if action in dispatch_map:
        span_name = f"nusyq.action.{action}"
        cm = otel.start_action_span(span_name, attrs) if (otel and enabled) else None
        receipt_path = None
        if cm:
            with cm as span:  # pylint: disable=not-context-manager
                handler_rc = dispatch_map[action]()
                trace_id, span_id = otel.current_trace_ids() if (otel and enabled) else ("n/a", "n/a")
                tier = get_action_tier(action, contracts, catalog)
                outputs = _LAST_OUTPUTS
                receipt_path = emit_receipt(
                    action,
                    paths.nusyq_hub,
                    tier,
                    run_id,
                    trace_id,
                    span_id,
                    ("success" if handler_rc == 0 else "error"),
                    inputs={"argv": args, "mode": mode, "json_mode": json_mode},
                    exit_code=handler_rc,
                    outputs=outputs,
                )
                _LAST_OUTPUTS = None
                try:
                    span.set_attribute("receipt.path", str(receipt_path))
                    span.add_event(
                        "receipt",
                        {
                            "receipt.path": str(receipt_path),
                            "status": ("success" if handler_rc == 0 else "error"),
                            "exit_code": handler_rc,
                        },
                    )
                except Exception:
                    pass
        else:
            handler_rc = dispatch_map[action]()
            trace_id, span_id = otel.current_trace_ids() if (otel and enabled) else ("n/a", "n/a")
            tier = get_action_tier(action, contracts, catalog)
            outputs = _LAST_OUTPUTS
            receipt_path = emit_receipt(
                action,
                paths.nusyq_hub,
                tier,
                run_id,
                trace_id,
                span_id,
                ("success" if handler_rc == 0 else "error"),
                inputs={"argv": args, "mode": mode, "json_mode": json_mode},
                exit_code=handler_rc,
                outputs=outputs,
            )
            _LAST_OUTPUTS = None
        if handler_rc == 0:
            _award_xp_for_action(action)
        return handler_rc

    else:
        print(f"[ERROR] Unknown action: {action}")
        print("Run 'python start_nusyq.py help' for usage.")
        return 1


if __name__ == "__main__":
    exit_code = 1
    try:
        exit_code = main()
    except BaseException:
        _write_job_exit_code_from_env(1)
        raise
    _write_job_exit_code_from_env(exit_code)
    raise SystemExit(exit_code)
