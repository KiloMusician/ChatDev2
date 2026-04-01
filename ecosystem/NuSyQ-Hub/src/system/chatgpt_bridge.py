"""ChatGPT CLI Bridge.

Lightweight HTTP bridge to accept CLI-style commands from external GPT apps
oracles (ChatGPT CLI, Hugging Face, Replit webhooks). Commands are forwarded
into the TerminalManager as structured events and — if available — routed to
the UnifiedAIOrchestrator for execution.

This module is intentionally best-effort: it will run even if FastAPI or the
orchestrator dependencies are missing. Run with:

  uvicorn src.system.chatgpt_bridge:app --host 127.0.0.1 --port 8765

"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import re
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Module-level set keeps strong references to fire-and-forget async tasks so
# they are not garbage-collected before completing (RUF006 guard).
_background_tasks: set[asyncio.Task[Any]] = set()

# Initialize terminal logging (best-effort)
try:
    from src.system.init_terminal import init_terminal_logging

    init_terminal_logging(channel="ChatGPT-Bridge")
except Exception:
    logger.debug("Suppressed Exception", exc_info=True)


try:
    from fastapi import FastAPI, HTTPException, Request, WebSocket
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
except Exception:  # pragma: no cover - optional dependency
    FastAPI = None  # type: ignore
    HTTPException = Exception  # type: ignore
    BaseModel = object  # type: ignore


class CommandRequest(BaseModel):  # type: ignore
    command: str
    args: dict[str, Any] | None = None
    source: str | None = None


class TerminalSendRequest(BaseModel):
    channel: str
    level: str
    message: str
    meta: dict[str, Any] | None = None


class PURequest(BaseModel):
    title: str
    payload: dict[str, Any] | None = None
    priority: str | None = "normal"


app = FastAPI(title="NuSyQ ChatGPT Bridge") if FastAPI else None

SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
ROUTER_TASK_TYPES = {
    "analyze",
    "generate",
    "review",
    "debug",
    "plan",
    "test",
    "document",
}
ROUTER_COMMAND_ALIASES = {
    "analyze_with_ai": "analyze",
    "generate_with_ai": "generate",
    "review_with_ai": "review",
    "debug_with_ai": "debug",
}
KEY_STATUS = "status"
KEY_ERROR = "error"
KEY_REASON = "reason"
KEY_RESULT = "result"
KEY_EXECUTOR = "executor"
STATUS_OK = "ok"
STATUS_FAILED = "failed"
STATUS_UNHANDLED = "unhandled"

START_NUSYQ_COMMON_ACTIONS = {
    "ai_status",
    "brief",
    "capabilities",
    "doctor",
    "error_report",
    "hygiene",
    "orchestrator_status",
    "queue",
    "selfcheck",
    "snapshot",
    "suggest",
    "terminal_snapshot",
    "task_summary",
    "terminals",
    "work",
}


def _status_implies_success(status: str | None) -> bool:
    """Map mixed adapter statuses to canonical success semantics."""
    if not status:
        return False
    return str(status).strip().lower() in {
        STATUS_OK,
        "success",
        "accepted",
        "completed",
        "queued",
        "running",
        "healthy",
        "operational",
    }


def _normalize_bridge_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Ensure bridge command responses consistently expose status + success."""
    normalized = dict(payload)
    status = normalized.get(KEY_STATUS)
    if not isinstance(status, str) or not status.strip():
        status = "success" if bool(normalized.get("success")) else KEY_ERROR
        normalized[KEY_STATUS] = status
    if "success" not in normalized:
        normalized["success"] = _status_implies_success(str(normalized[KEY_STATUS]))
    return normalized


def _require_token(request: Request | None) -> None:
    """If NUSYQ_BRIDGE_TOKEN is set in env, require that header 'x-bridge-token' matches."""
    token = os.environ.get("NUSYQ_BRIDGE_TOKEN")
    if not token:
        return
    if request is None:
        raise HTTPException(status_code=401, detail="missing auth header")
    header = request.headers.get("x-bridge-token")
    if header != token:
        raise HTTPException(status_code=401, detail="invalid bridge token")


def _build_plugin_manifest(base_url: str) -> dict[str, Any]:
    """Build OpenAI/ChatGPT plugin metadata for bridge discovery."""
    token_required = bool(os.environ.get("NUSYQ_BRIDGE_TOKEN"))
    auth: dict[str, Any]
    auth = (
        {"type": "service_http", "authorization_type": "bearer"}
        if token_required
        else {"type": "none"}
    )

    return {
        "schema_version": "v1",
        "name_for_human": "NuSyQ ChatGPT Bridge",
        "name_for_model": "nusyq_bridge",
        "description_for_human": (
            "Bridge for running NuSyQ actions, routing AI tasks, and reading quest/terminal state."
        ),
        "description_for_model": (
            "Use this bridge to execute routed tasks (analyze/generate/review/debug), "
            "trigger start_nusyq actions, submit processing units, and inspect quest or mailbox status."
        ),
        "auth": auth,
        "api": {
            "type": "openapi",
            "url": f"{base_url}/openapi.json",
            "is_user_authenticated": token_required,
        },
        "logo_url": f"{base_url}/health",
        "contact_email": "ops@nusyq.local",
        "legal_info_url": f"{base_url}/api/commands",
    }


def _emit_event_to_terminal(
    command: str, args: dict[str, Any] | None, source: str | None
) -> dict[str, Any]:
    from src.system.enhanced_terminal_ecosystem import TerminalManager

    tm = TerminalManager.get_instance()
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    payload = {
        "id": job_id,
        "ts": datetime.utcnow().isoformat() + "Z",
        "command": command,
        "args": args or {},
        "source": source or "chatgpt-cli",
    }
    # Send a structured event into the ChatDev/Agents channel
    try:
        tm.send("ChatDev", "info", f"chatgpt_bridge: {command}", meta=payload)
    except Exception:
        logger.exception("Failed to send to TerminalManager")
    # notify any websocket subscribers via bridge pubsub
    with contextlib.suppress(Exception):
        _broadcast_to_subscribers(payload)
    return {"job_id": job_id, "payload": payload}


def _try_orchestrator_execute(command: str, args: dict[str, Any] | None) -> dict[str, Any]:
    # Best-effort orchestrator adapter. Prefer explicit command mapping before
    # attempting legacy execute_command/handle_command hooks.
    payload = args or {}
    try:
        from src.orchestration.unified_ai_orchestrator import (
            OrchestrationTask, TaskPriority, UnifiedAIOrchestrator)

        orchestrator = UnifiedAIOrchestrator()
        command_name = str(command or "").strip().lower()

        if command_name in {"orchestrator_status", "system_status"}:
            return _normalize_bridge_response(
                {
                    KEY_STATUS: STATUS_OK,
                    "adapter": "get_system_status",
                    KEY_RESULT: orchestrator.get_system_status(),
                }
            )

        if command_name in {"orchestrator_capabilities", "capabilities"}:
            return _normalize_bridge_response(
                {
                    KEY_STATUS: STATUS_OK,
                    "adapter": "get_capabilities",
                    KEY_RESULT: orchestrator.get_capabilities(),
                }
            )

        if command_name in {"orchestrator_health", "health_check"}:
            return _normalize_bridge_response(
                {
                    KEY_STATUS: STATUS_OK,
                    "adapter": "health_check",
                    KEY_RESULT: orchestrator.health_check(),
                }
            )

        if command_name == "route_request":
            request_type = str(
                payload.get("request_type") or payload.get("task_type") or ""
            ).strip()
            if not request_type:
                return _normalize_bridge_response(
                    {KEY_STATUS: STATUS_UNHANDLED, KEY_REASON: "missing_request_type"}
                )
            target = orchestrator.route_request(request_type)
            return _normalize_bridge_response(
                {
                    KEY_STATUS: STATUS_OK,
                    "adapter": "route_request",
                    KEY_RESULT: {"request_type": request_type, "target": target},
                }
            )

        if command_name == "submit_task":
            task_type = str(payload.get("task_type") or "analysis").strip() or "analysis"
            content = _extract_description(command_name, "", payload)
            context = payload.get("context")
            if not isinstance(context, dict):
                context = {}
            preferred_systems = None
            target_system = str(payload.get("target_system") or "").strip().lower()
            if target_system and target_system != "auto":
                preferred_systems = [target_system]
            priority_name = _normalize_priority(payload.get("priority"))
            priority = getattr(TaskPriority, priority_name, TaskPriority.NORMAL)
            task = OrchestrationTask(
                task_id=str(payload.get("task_id") or ""),
                task_type=task_type,
                content=content,
                context=context,
                priority=priority,
                preferred_systems=orchestrator._normalize_services(preferred_systems),
            )
            task_id = orchestrator.submit_task(task)
            return _normalize_bridge_response(
                {
                    KEY_STATUS: STATUS_OK,
                    "adapter": "submit_task",
                    KEY_RESULT: {
                        "task_id": task_id,
                        "task_type": task_type,
                        "priority": priority_name,
                        "preferred_systems": preferred_systems or [],
                        KEY_STATUS: "queued",
                    },
                }
            )

        if command_name == "task_status":
            task_id = str(payload.get("task_id") or "").strip()
            if not task_id:
                return _normalize_bridge_response(
                    {KEY_STATUS: STATUS_UNHANDLED, KEY_REASON: "missing_task_id"}
                )
            task = orchestrator.active_tasks.get(task_id)
            if not task:
                return _normalize_bridge_response(
                    {KEY_STATUS: STATUS_OK, "adapter": "task_status", KEY_RESULT: {"found": False}}
                )
            return _normalize_bridge_response(
                {
                    KEY_STATUS: STATUS_OK,
                    "adapter": "task_status",
                    KEY_RESULT: {
                        "found": True,
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        KEY_STATUS: (
                            task.status.value if hasattr(task.status, "value") else str(task.status)
                        ),
                        "assigned_system": task.assigned_system,
                        "created_at": task.created_at.isoformat(),
                    },
                }
            )

        # Preferred method name: `execute_command` or `handle_command` — try both
        if hasattr(orchestrator, "execute_command"):
            result = orchestrator.execute_command(command, payload)
            return _normalize_bridge_response({KEY_STATUS: STATUS_OK, KEY_RESULT: result})
        if hasattr(orchestrator, "handle_command"):
            result = orchestrator.handle_command(command, payload)
            return _normalize_bridge_response({KEY_STATUS: STATUS_OK, KEY_RESULT: result})
        return _normalize_bridge_response(
            {KEY_STATUS: STATUS_UNHANDLED, KEY_REASON: "orchestrator_missing_handler"}
        )
    except Exception as exc:  # pragma: no cover - runtime behavior
        logger.debug("Orchestrator not available or failed: %s", exc)
        return _normalize_bridge_response(
            {KEY_STATUS: "orchestrator_unavailable", KEY_ERROR: str(exc)}
        )


async def _try_orchestrator_execute_async(
    command: str,
    args: dict[str, Any] | None,
) -> dict[str, Any]:
    """Async orchestrator adapter for direct task execution paths."""
    payload = args or {}
    command_name = str(command or "").strip().lower()
    if command_name not in {
        "orchestrate_task",
        "orchestrate_task_async",
        "execute_task",
        "execute_orchestration_task",
    }:
        return _normalize_bridge_response(
            {KEY_STATUS: STATUS_UNHANDLED, KEY_REASON: "unsupported_async_orchestrator_command"}
        )

    try:
        from src.orchestration.unified_ai_orchestrator import (
            TaskPriority, UnifiedAIOrchestrator)

        orchestrator = UnifiedAIOrchestrator()
        task_type = str(payload.get("task_type") or "analysis").strip() or "analysis"
        content = _extract_description(command_name, "", payload)
        context = payload.get("context")
        if not isinstance(context, dict):
            context = {}

        preferred_systems: list[str] = []
        raw_preferred = payload.get("preferred_systems")
        if isinstance(raw_preferred, list):
            for item in raw_preferred:
                token = str(item).strip().lower()
                if token:
                    preferred_systems.append(token)
        target_system = str(payload.get("target_system") or "").strip().lower()
        if target_system and target_system != "auto" and target_system not in preferred_systems:
            preferred_systems.append(target_system)

        required_capabilities: list[str] = []
        raw_capabilities = payload.get("required_capabilities")
        if isinstance(raw_capabilities, list):
            required_capabilities = [
                str(item).strip() for item in raw_capabilities if str(item).strip()
            ]

        priority_name = _normalize_priority(payload.get("priority"))
        priority = getattr(TaskPriority, priority_name, TaskPriority.NORMAL)

        result = await orchestrator.orchestrate_task_async(
            task_type=task_type,
            content=content,
            context=context,
            priority=priority,
            required_capabilities=required_capabilities or None,
            preferred_systems=preferred_systems or None,
        )
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_OK,
                "adapter": "orchestrate_task_async",
                KEY_RESULT: result,
            }
        )
    except Exception as exc:  # pragma: no cover - runtime behavior
        logger.debug("Async orchestrator adapter failed: %s", exc)
        return _normalize_bridge_response(
            {KEY_STATUS: STATUS_FAILED, "adapter": "orchestrate_task_async", KEY_ERROR: str(exc)}
        )


def _parse_command_name(raw_command: str) -> tuple[str, str]:
    command_text = str(raw_command or "").strip()
    if not command_text:
        return "", ""
    parts = command_text.split(maxsplit=1)
    name = parts[0].lower()
    inline_tail = parts[1].strip() if len(parts) > 1 else ""
    return name, inline_tail


def _safe_cli_tokens(values: Any) -> list[str]:
    tokens: list[str] = []
    if not isinstance(values, list):
        return tokens
    for value in values:
        token = str(value).strip()
        if not token:
            continue
        if not SAFE_TOKEN_RE.match(token):
            continue
        tokens.append(token)
    return tokens


def _terminal_channels() -> dict[str, Any]:
    """Return available terminal channels from TerminalManager."""
    try:
        from src.system.enhanced_terminal_ecosystem import TerminalManager

        tm = TerminalManager.get_instance()
        channels = tm.list_channels()
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_OK,
                KEY_EXECUTOR: "terminal_manager",
                "channels": channels,
                "count": len(channels),
            }
        )
    except Exception as exc:
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_FAILED,
                KEY_EXECUTOR: "terminal_manager",
                KEY_ERROR: str(exc),
            }
        )


def _terminal_recent(channel: str | None, limit: int = 50) -> dict[str, Any]:
    """Return recent terminal entries for one or all channels."""
    bounded_limit = max(1, min(int(limit), 200))
    try:
        from src.system.enhanced_terminal_ecosystem import TerminalManager

        tm = TerminalManager.get_instance()
        if channel:
            entries = tm.recent(channel, n=bounded_limit)
            return _normalize_bridge_response(
                {
                    KEY_STATUS: STATUS_OK,
                    KEY_EXECUTOR: "terminal_manager",
                    "channel": channel,
                    "count": len(entries),
                    "entries": entries,
                }
            )

        payload: dict[str, list[dict[str, Any]]] = {}
        total = 0
        for ch in tm.list_channels():
            recent_entries = tm.recent(ch, n=bounded_limit)
            payload[ch] = recent_entries
            total += len(recent_entries)
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_OK,
                KEY_EXECUTOR: "terminal_manager",
                "channel": None,
                "count": total,
                "entries_by_channel": payload,
            }
        )
    except Exception as exc:
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_FAILED,
                KEY_EXECUTOR: "terminal_manager",
                KEY_ERROR: str(exc),
            }
        )


def _terminal_snapshot(limit_per_channel: int = 20) -> dict[str, Any]:
    """Return a machine-readable snapshot of terminal freshness and activity."""
    bounded_limit = max(1, min(int(limit_per_channel), 200))

    def _freshness_label(age_seconds: float) -> str:
        if age_seconds < 300:
            return "HOT"
        if age_seconds < 3600:
            return "WARM"
        return "COLD"

    def _normalize_channel_name(name: str) -> str:
        tokens = re.findall(r"[A-Za-z0-9]+", name)
        if not tokens:
            return "terminal"
        return "_".join(token.lower() for token in tokens)

    try:
        from src.system.enhanced_terminal_ecosystem import TerminalManager
        from src.system.terminal_intelligence_orchestrator import \
            get_orchestrator

        root = Path(__file__).resolve().parents[2]
        tm = TerminalManager.get_instance()
        orchestrator = get_orchestrator()
        now = datetime.now(UTC)
        configured_channels = set(orchestrator.terminals.keys())
        runtime_channels = set(tm.list_channels())
        channels = sorted(configured_channels | runtime_channels)

        entries: list[dict[str, Any]] = []
        hot = warm = cold = missing = 0
        for channel in channels:
            log_path = root / "data" / "terminal_logs" / f"{_normalize_channel_name(channel)}.log"
            exists = log_path.exists()
            age_seconds = None
            freshness = "MISSING"
            if exists:
                age_seconds = max(
                    (now - datetime.fromtimestamp(log_path.stat().st_mtime, UTC)).total_seconds(),
                    0.0,
                )
                freshness = _freshness_label(age_seconds)
                if freshness == "HOT":
                    hot += 1
                elif freshness == "WARM":
                    warm += 1
                else:
                    cold += 1
            else:
                missing += 1

            recent_entries = tm.recent(channel, n=bounded_limit)
            last_entry = recent_entries[-1] if recent_entries else {}
            entries.append(
                {
                    "channel": channel,
                    "log_path": str(log_path),
                    "exists": exists,
                    "freshness": freshness,
                    "age_seconds": round(age_seconds, 3) if age_seconds is not None else None,
                    "recent_count": len(recent_entries),
                    "last_ts": last_entry.get("ts"),
                    "last_level": last_entry.get("level"),
                    "last_message_preview": str(last_entry.get("msg", ""))[:200],
                }
            )

        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_OK,
                KEY_EXECUTOR: "terminal_manager",
                "schema_version": "1.0",
                "timestamp": now.isoformat(),
                "summary": {
                    "total_channels": len(channels),
                    "hot_channels": hot,
                    "warm_channels": warm,
                    "cold_channels": cold,
                    "missing_logs": missing,
                },
                "channels": entries,
            }
        )
    except Exception as exc:
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_FAILED,
                KEY_EXECUTOR: "terminal_manager",
                KEY_ERROR: str(exc),
            }
        )


def _background_task_status(limit: int = 10, status: str | None = None) -> dict[str, Any]:
    """Summarize background task orchestrator state in a stable schema."""
    try:
        from src.orchestration.background_task_orchestrator import (
            TaskStatus, get_orchestrator)

        orchestrator = get_orchestrator()
        task_status = None
        if status:
            with contextlib.suppress(Exception):
                task_status = TaskStatus(status)
        tasks = orchestrator.list_tasks(status=task_status, limit=max(1, min(limit, 100)))
        status_summary = orchestrator.get_orchestrator_status()
        recent = [
            {
                "task_id": task.task_id,
                KEY_STATUS: task.status.value,
                "target": task.target.value,
                "requesting_agent": task.requesting_agent,
                "created_at": task.created_at.isoformat(),
            }
            for task in tasks
        ]
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_OK,
                KEY_EXECUTOR: "background_task_orchestrator",
                "schema_version": "1.0",
                "summary": {
                    "total_tasks": status_summary.get("total_tasks", 0),
                    "status_counts": status_summary.get("status_counts", {}),
                    "worker_running": status_summary.get("worker_running", False),
                },
                "recent_tasks": recent,
                "count": len(recent),
            }
        )
    except Exception as exc:
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_FAILED,
                KEY_EXECUTOR: "background_task_orchestrator",
                KEY_ERROR: str(exc),
            }
        )


def _pu_queue_status(limit: int = 10, status: str | None = None) -> dict[str, Any]:
    """Summarize unified PU queue state in a stable schema."""
    try:
        from src.automation.unified_pu_queue import UnifiedPUQueue

        queue = UnifiedPUQueue()
        stats = queue.get_statistics()
        pu_items = queue.get_status(filter_status=status) if status else queue.get_status()
        recent = [
            {
                "id": pu.id,
                "type": pu.type,
                "title": pu.title,
                KEY_STATUS: pu.status,
                "priority": pu.priority,
                "source_repo": pu.source_repo,
                "created_at": pu.created_at,
                "background_task_id": pu.background_task_id,
            }
            for pu in list(reversed(pu_items))[: max(1, min(limit, 100))]
        ]
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_OK,
                KEY_EXECUTOR: "unified_pu_queue",
                "schema_version": "1.0",
                "summary": stats,
                "recent_pus": recent,
                "count": len(recent),
            }
        )
    except Exception as exc:
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_FAILED,
                KEY_EXECUTOR: "unified_pu_queue",
                KEY_ERROR: str(exc),
            }
        )


def _normalize_priority(value: Any) -> str:
    priority = str(value or "NORMAL").upper()
    if priority not in {"CRITICAL", "HIGH", "NORMAL", "LOW", "BACKGROUND"}:
        return "NORMAL"
    return priority


def _extract_description(
    command_name: str,
    inline_tail: str,
    args: dict[str, Any],
) -> str:
    description = args.get("description") or args.get("prompt") or args.get("query")
    if isinstance(description, str) and description.strip():
        return description.strip()
    if inline_tail:
        return inline_tail
    return command_name


def _run_start_nusyq(
    args: dict[str, Any] | None, inferred_action: str | None = None
) -> dict[str, Any]:
    payload = args or {}
    action = str(payload.get("action") or inferred_action or "").strip()
    if not action:
        return _normalize_bridge_response(
            {KEY_STATUS: STATUS_UNHANDLED, KEY_REASON: "missing_action"}
        )
    if not SAFE_TOKEN_RE.match(action):
        return _normalize_bridge_response(
            {KEY_STATUS: STATUS_FAILED, KEY_REASON: "invalid_action", "action": action}
        )

    extra_args = _safe_cli_tokens(payload.get("extra_args", []))
    try:
        timeout = int(payload.get("timeout_seconds", 120))
    except Exception:
        timeout = 120
    timeout = max(5, min(timeout, 900))

    repo_root = Path(__file__).resolve().parents[2]
    cmd = [sys.executable, "scripts/start_nusyq.py", action, *extra_args]
    try:
        completed = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        output = "\n".join(filter(None, [completed.stdout, completed.stderr])).strip()
        return _normalize_bridge_response(
            {
                KEY_STATUS: "success" if completed.returncode == 0 else STATUS_FAILED,
                KEY_EXECUTOR: "start_nusyq",
                "action": action,
                "returncode": completed.returncode,
                "command": cmd,
                "output_preview": output[-2500:],
            }
        )
    except subprocess.TimeoutExpired:
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_FAILED,
                KEY_EXECUTOR: "start_nusyq",
                "action": action,
                KEY_REASON: "timeout",
                "timeout_seconds": timeout,
                "command": cmd,
            }
        )
    except Exception as exc:  # pragma: no cover - runtime behavior
        return _normalize_bridge_response(
            {
                KEY_STATUS: STATUS_FAILED,
                KEY_EXECUTOR: "start_nusyq",
                "action": action,
                KEY_ERROR: str(exc),
                "command": cmd,
            }
        )


async def _try_router_execute(
    command_name: str,
    inline_tail: str,
    args: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = args or {}
    routed_command = ROUTER_COMMAND_ALIASES.get(command_name, command_name)

    try:
        from src.tools.agent_task_router import AgentTaskRouter
    except Exception as exc:
        return _normalize_bridge_response({KEY_STATUS: "router_unavailable", KEY_ERROR: str(exc)})

    try:
        router = AgentTaskRouter()
    except Exception as exc:
        return _normalize_bridge_response({KEY_STATUS: "router_unavailable", KEY_ERROR: str(exc)})

    if routed_command == "route_task":
        task_type = str(payload.get("task_type", "")).strip()
        if not task_type:
            return _normalize_bridge_response(
                {KEY_STATUS: STATUS_UNHANDLED, KEY_REASON: "missing_task_type"}
            )
        target_system = str(payload.get("target_system", "auto"))
        context = payload.get("context")
        if not isinstance(context, dict):
            context = {}
        description = _extract_description(task_type, inline_tail, payload)
        priority = _normalize_priority(payload.get("priority"))
        try:
            result = await router.route_task(
                task_type=task_type,  # type: ignore[arg-type]
                description=description,
                context=context,
                target_system=target_system,  # type: ignore[arg-type]
                priority=priority,
            )
            return _normalize_bridge_response(
                {KEY_STATUS: STATUS_OK, KEY_EXECUTOR: "agent_task_router", KEY_RESULT: result}
            )
        except Exception as exc:
            return _normalize_bridge_response(
                {KEY_STATUS: STATUS_FAILED, KEY_EXECUTOR: "agent_task_router", KEY_ERROR: str(exc)}
            )

    if routed_command == "health_check":
        try:
            result = await router.health_check()
            return _normalize_bridge_response(
                {KEY_STATUS: STATUS_OK, KEY_EXECUTOR: "agent_task_router", KEY_RESULT: result}
            )
        except Exception as exc:
            return _normalize_bridge_response(
                {KEY_STATUS: STATUS_FAILED, KEY_EXECUTOR: "agent_task_router", KEY_ERROR: str(exc)}
            )

    if routed_command in ROUTER_TASK_TYPES:
        target_system = str(payload.get("target_system", "auto"))
        context = payload.get("context")
        if not isinstance(context, dict):
            context = {}
        description = _extract_description(routed_command, inline_tail, payload)
        priority = _normalize_priority(payload.get("priority"))
        try:
            result = await router.route_task(
                task_type=routed_command,  # type: ignore[arg-type]
                description=description,
                context=context,
                target_system=target_system,  # type: ignore[arg-type]
                priority=priority,
            )
            return _normalize_bridge_response(
                {KEY_STATUS: STATUS_OK, KEY_EXECUTOR: "agent_task_router", KEY_RESULT: result}
            )
        except Exception as exc:
            return _normalize_bridge_response(
                {KEY_STATUS: STATUS_FAILED, KEY_EXECUTOR: "agent_task_router", KEY_ERROR: str(exc)}
            )

    return _normalize_bridge_response(
        {KEY_STATUS: STATUS_UNHANDLED, KEY_REASON: "unsupported_router_command"}
    )


async def _execute_bridge_command(command: str, args: dict[str, Any] | None) -> dict[str, Any]:
    command_name, inline_tail = _parse_command_name(command)
    if not command_name:
        return _normalize_bridge_response({KEY_STATUS: STATUS_FAILED, KEY_REASON: "empty_command"})

    payload = args or {}
    if command_name in {"terminals_channels", "terminals_list"}:
        return _normalize_bridge_response(_terminal_channels())

    if command_name in {"terminals_recent", "terminal_recent"}:
        channel = payload.get("channel")
        channel_name = str(channel).strip() if channel else ""
        try:
            limit = int(payload.get("limit", 50))
        except Exception:
            limit = 50
        return _normalize_bridge_response(_terminal_recent(channel_name or None, limit=limit))

    if command_name in {"terminals_snapshot", "terminal_snapshot"}:
        limit = payload.get("limit", 20)
        try:
            bounded_limit = int(limit)
        except Exception:
            bounded_limit = 20
        if isinstance(payload.get("extra_args"), list):
            for token in payload.get("extra_args", []):
                tok = str(token).strip()
                if tok.startswith("--limit="):
                    with contextlib.suppress(Exception):
                        bounded_limit = int(tok.split("=", 1)[1].strip())
        return _normalize_bridge_response(_terminal_snapshot(limit_per_channel=bounded_limit))

    if command_name in {"background_task_status", "background_tasks_status"}:
        try:
            limit = int(payload.get("limit", 10))
        except Exception:
            limit = 10
        status = payload.get(KEY_STATUS)
        status_filter = str(status).strip() if status else None
        return _normalize_bridge_response(
            _background_task_status(limit=limit, status=status_filter)
        )

    if command_name in {"pu_queue_status", "pu_status"}:
        try:
            limit = int(payload.get("limit", 10))
        except Exception:
            limit = 10
        status = payload.get(KEY_STATUS)
        status_filter = str(status).strip() if status else None
        return _normalize_bridge_response(_pu_queue_status(limit=limit, status=status_filter))

    if command_name == "start_nusyq":
        return _normalize_bridge_response(_run_start_nusyq(args))

    if command_name in START_NUSYQ_COMMON_ACTIONS:
        return _normalize_bridge_response(_run_start_nusyq(args, inferred_action=command_name))

    router_result = await _try_router_execute(command_name, inline_tail, args)
    if router_result.get(KEY_STATUS) in {STATUS_OK, STATUS_FAILED}:
        return _normalize_bridge_response(router_result)

    async_orchestration = await _try_orchestrator_execute_async(command_name, args)
    if async_orchestration.get(KEY_STATUS) in {STATUS_OK, STATUS_FAILED}:
        status = STATUS_OK if async_orchestration.get(KEY_STATUS) == STATUS_OK else STATUS_FAILED
        return _normalize_bridge_response(
            {
                KEY_STATUS: status,
                KEY_EXECUTOR: "unified_orchestrator",
                KEY_RESULT: async_orchestration,
            }
        )

    orchestration = _try_orchestrator_execute(command_name, args)
    if orchestration.get(KEY_STATUS) == STATUS_OK:
        return _normalize_bridge_response(
            {KEY_STATUS: STATUS_OK, KEY_EXECUTOR: "unified_orchestrator", KEY_RESULT: orchestration}
        )

    return _normalize_bridge_response(
        {
            KEY_STATUS: STATUS_UNHANDLED,
            "command": command_name,
            "router": router_result,
            "orchestrator": orchestration,
            "hint": "Use /api/commands for supported command contracts.",
        }
    )


# --- Simple in-process pubsub for broadcasting terminal events to WebSocket/SSE ---
_subscriber_lock = asyncio.Lock()
_websocket_subscribers: set[WebSocket] = set()
_last_seen: dict[str, str | None] = {}


async def _register_websocket(ws: WebSocket) -> None:
    await ws.accept()
    async with _subscriber_lock:
        _websocket_subscribers.add(ws)


async def _unregister_websocket(ws: WebSocket) -> None:
    async with _subscriber_lock:
        _websocket_subscribers.discard(ws)


def _broadcast_to_subscribers(message: dict[str, Any]) -> None:
    # schedule broadcast without blocking sync flow
    _t = asyncio.create_task(_async_broadcast(message))
    _background_tasks.add(_t)
    _t.add_done_callback(_background_tasks.discard)


async def _async_broadcast(message: dict[str, Any]) -> None:
    async with _subscriber_lock:
        to_remove = []
        for ws in list(_websocket_subscribers):
            try:
                await ws.send_json({"type": "terminal_event", "data": message})
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            _websocket_subscribers.discard(ws)


async def _poll_terminal_manager_and_broadcast(interval: float = 1.0) -> None:
    # Periodically poll TerminalManager channels for new entries and broadcast
    try:
        from src.system.enhanced_terminal_ecosystem import TerminalManager
    except Exception:
        return
    tm = TerminalManager.get_instance()
    while True:
        try:
            for ch in list(tm.list_channels()):
                try:
                    recent = tm.recent(ch, n=50)
                except Exception:
                    recent = []
                last_ts = _last_seen.get(ch)
                new_items = []
                for item in recent:
                    its = item.get("ts")
                    if not its:
                        continue
                    if last_ts is None or its > last_ts:
                        new_items.append(item)
                if new_items:
                    ts_val = new_items[-1].get("ts")
                    if isinstance(ts_val, str):
                        _last_seen[ch] = ts_val
                    else:
                        _last_seen[ch] = str(ts_val) if ts_val is not None else None
                    for item in new_items:
                        _broadcast_to_subscribers({"channel": ch, "entry": item})
        except Exception:
            logger.debug("polling loop encountered an error", exc_info=True)
        await asyncio.sleep(interval)


if app:

    @app.get("/health", tags=["bridge"])
    async def health() -> dict[str, Any]:
        return {
            STATUS_OK: True,
            "service": "nusyq-chatgpt-bridge",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    @app.get("/.well-known/ai-plugin.json", tags=["bridge"])
    async def ai_plugin_manifest(request: Request) -> dict[str, Any]:
        base_url = str(request.base_url).rstrip("/")
        return _build_plugin_manifest(base_url)

    @app.get("/api/discovery", tags=["bridge"])
    async def discovery(request: Request) -> dict[str, Any]:
        _require_token(request)
        base_url = str(request.base_url).rstrip("/")
        return {
            STATUS_OK: True,
            "links": {
                "plugin_manifest": f"{base_url}/.well-known/ai-plugin.json",
                "openapi": f"{base_url}/openapi.json",
                "commands": f"{base_url}/api/commands",
                "execute": f"{base_url}/api/execute",
                "terminals_channels": f"{base_url}/api/terminals/channels",
                "terminals_recent": f"{base_url}/api/terminals/recent",
                "terminals_snapshot": f"{base_url}/api/terminals/snapshot",
                "status_background_tasks": f"{base_url}/api/status/background_tasks",
                "status_pu_queue": f"{base_url}/api/status/pu_queue",
                "stream": f"{base_url}/api/stream",
                "websocket": f"{base_url}/ws",
            },
        }

    @app.get("/api/commands", tags=["bridge"])
    async def command_contracts(request: Request) -> dict[str, Any]:
        _require_token(request)
        return {
            STATUS_OK: True,
            "commands": [
                {
                    "command": "analyze|generate|review|debug|plan|test|document",
                    "args": {
                        "description": "natural-language task",
                        "target_system": "auto|ollama|chatdev|copilot|consciousness|quantum_resolver",
                        "context": {"file": "optional"},
                        "priority": "CRITICAL|HIGH|NORMAL|LOW|BACKGROUND",
                    },
                },
                {
                    "command": "route_task",
                    "args": {
                        "task_type": "analyze|generate|review|debug|...",
                        "description": "task description",
                        "target_system": "auto|ollama|chatdev|copilot|consciousness|quantum_resolver",
                        "context": {},
                        "priority": "NORMAL",
                    },
                },
                {
                    "command": "start_nusyq",
                    "args": {
                        "action": "queue|work|suggest|error_report|...",
                        "extra_args": ["--optional-token-safe-args"],
                        "timeout_seconds": 120,
                    },
                },
                {
                    "command": "terminals_channels",
                    "args": {},
                },
                {
                    "command": "terminals_recent",
                    "args": {
                        "channel": "optional channel name; omit for all channels",
                        "limit": "optional max entries (default 50, max 200)",
                    },
                },
                {
                    "command": "background_task_status",
                    "args": {
                        KEY_STATUS: "optional queued|running|completed|failed|cancelled",
                        "limit": "optional max rows (default 10, max 100)",
                    },
                },
                {
                    "command": "pu_queue_status",
                    "args": {
                        KEY_STATUS: "optional queued|approved|executing|completed|failed",
                        "limit": "optional max rows (default 10, max 100)",
                    },
                },
                {
                    "command": "terminal_snapshot",
                    "args": {
                        "limit": "optional max entries per channel (default 20, max 200)",
                        "extra_args": ["--limit=50 (optional; backward compatible)"],
                    },
                },
                {
                    "command": "orchestrate_task",
                    "args": {
                        "task_type": "analysis|generation|review|...",
                        "description": "task description",
                        "target_system": "auto|ollama|chatdev|copilot|consciousness|quantum_resolver",
                        "context": {},
                        "priority": "NORMAL",
                        "preferred_systems": ["optional preferred systems"],
                        "required_capabilities": ["optional capability tags"],
                    },
                },
                {"command": "health_check", "args": {}},
            ],
        }

    @app.post("/api/execute", tags=["bridge"])
    async def execute(req: CommandRequest, request: Request) -> dict[str, Any]:
        _require_token(request)
        try:
            info = _emit_event_to_terminal(req.command, req.args, req.source)
            execution = await _execute_bridge_command(req.command, req.args)
            return {STATUS_OK: True, "job": info, "execution": execution}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/terminals/send", tags=["terminals"])
    async def terminals_send(req: TerminalSendRequest, request: Request) -> dict[str, Any]:
        _require_token(request)
        try:
            from src.system.enhanced_terminal_ecosystem import TerminalManager

            tm = TerminalManager.get_instance()
            tm.send(req.channel, req.level, req.message, meta=req.meta)
            return {STATUS_OK: True, "sent": True, "channel": req.channel}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/terminals/channels", tags=["terminals"])
    async def terminals_channels(request: Request) -> dict[str, Any]:
        _require_token(request)
        result = _terminal_channels()
        if result.get(KEY_STATUS) == STATUS_FAILED:
            raise HTTPException(status_code=500, detail=result.get(KEY_ERROR))
        return {STATUS_OK: True, **result}

    @app.get("/api/terminals/recent", tags=["terminals"])
    async def terminals_recent(
        request: Request,
        channel: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        _require_token(request)
        result = _terminal_recent(channel, limit=limit)
        if result.get(KEY_STATUS) == STATUS_FAILED:
            raise HTTPException(status_code=500, detail=result.get(KEY_ERROR))
        return {STATUS_OK: True, **result}

    @app.get("/api/terminals/snapshot", tags=["terminals"])
    async def terminals_snapshot(
        request: Request,
        limit: int = 20,
    ) -> dict[str, Any]:
        _require_token(request)
        result = _terminal_snapshot(limit_per_channel=limit)
        if result.get(KEY_STATUS) == STATUS_FAILED:
            raise HTTPException(status_code=500, detail=result.get(KEY_ERROR))
        return {STATUS_OK: True, **result}

    @app.get("/api/status/background_tasks", tags=[KEY_STATUS])
    async def background_tasks_status(
        request: Request,
        status: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        _require_token(request)
        result = _background_task_status(limit=limit, status=status)
        if result.get(KEY_STATUS) == STATUS_FAILED:
            raise HTTPException(status_code=500, detail=result.get(KEY_ERROR))
        return {STATUS_OK: True, **result}

    @app.get("/api/status/pu_queue", tags=[KEY_STATUS])
    async def pu_queue_status(
        request: Request,
        status: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        _require_token(request)
        result = _pu_queue_status(limit=limit, status=status)
        if result.get(KEY_STATUS) == STATUS_FAILED:
            raise HTTPException(status_code=500, detail=result.get(KEY_ERROR))
        return {STATUS_OK: True, **result}

    @app.post("/api/pu/submit", tags=["pu"])
    async def pu_submit(req: PURequest, request: Request) -> dict[str, Any]:
        _require_token(request)

        try:
            # Best-effort: try to import a UnifiedPUQueue or similar interface
            try:
                from src.automation.unified_pu_queue import PU, UnifiedPUQueue

                payload = req.payload or {}
                queue = UnifiedPUQueue()
                pu = PU(
                    id="",
                    type=str(payload.get("type", "AnalysisPU")),
                    title=req.title,
                    description=str(payload.get("description", req.title)),
                    source_repo=str(payload.get("source_repo", "nusyq-hub")),
                    priority=str(req.priority or "normal").lower(),
                    proof_criteria=payload.get("proof_criteria", ["diagnose", "resolve", "verify"]),
                    metadata=payload,
                    status="queued",
                )
                pu_id = queue.submit_pu(pu)
                return {STATUS_OK: True, "pu_id": pu_id, KEY_STATUS: "queued"}
            except Exception:
                # Fallback: send to TerminalManager for human inspection
                from src.system.enhanced_terminal_ecosystem import \
                    TerminalManager

                tm = TerminalManager.get_instance()
                tm.send(
                    "Tasks",
                    "info",
                    f"PU submit (fallback): {req.title}",
                    meta={"payload": req.payload},
                )
                return {STATUS_OK: True, "fallback": True}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/quests/status", tags=["quests"])
    async def quests_status(request: Request) -> dict[str, Any]:
        _require_token(request)

        try:
            hub = os.environ.get("NUSYQ_HUB_PATH")
            if not hub:
                hub = str(Path(__file__).resolve().parents[2])
            quest_file = Path(hub) / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
            if not quest_file.exists():
                return {STATUS_OK: True, "quests": []}
            items = []
            with open(quest_file, encoding="utf-8") as f:
                for line in f:
                    try:
                        items.append(json.loads(line))
                    except Exception:
                        continue
            return {STATUS_OK: True, "quests": items[-50:]}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/mailbox/send", tags=["mailbox"])
    async def mailbox_send(body: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_token(request)

        """Append a command to the file-based mailbox (commands.ndjson).

        This endpoint supports offline CLI patterns where the CLI cannot
        reach the HTTP bridge but can write to a shared volume. The mailbox
        is checked by NuSyQ processes that can pick up and execute commands.
        """
        try:
            try:
                from src.system.mailbox_queue import Mailbox

                mb = Mailbox()
                mb.append_command(body)
                return {STATUS_OK: True, "written": True}
            except Exception:
                # fallback to TerminalManager for human inspection
                from src.system.enhanced_terminal_ecosystem import \
                    TerminalManager

                tm = TerminalManager.get_instance()
                tm.send("Tasks", "warning", "mailbox_send fallback", meta={"body": body})
                return {STATUS_OK: True, "fallback": True}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/mailbox/results", tags=["mailbox"])
    async def mailbox_results(request: Request) -> dict[str, Any]:
        _require_token(request)

        try:
            from src.system.mailbox_queue import Mailbox

            mb = Mailbox()
            return {STATUS_OK: True, "results": mb.read_results()}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await _register_websocket(ws)
        try:
            while True:
                data = await ws.receive_text()
                # Simple protocol: receive JSON command or ping
                try:
                    obj = json.loads(data)
                except Exception:
                    obj = {"raw": data}
                # If it's a command, route through execute
                if isinstance(obj, dict) and obj.get("command"):
                    cmd = obj.get("command")
                    try:
                        cmd_str = str(cmd)
                        info = _emit_event_to_terminal(cmd_str, obj.get("args"), obj.get("source"))
                        execution = await _execute_bridge_command(cmd_str, obj.get("args"))
                        await ws.send_json({STATUS_OK: True, "job": info, "execution": execution})
                    except Exception:
                        await ws.send_json({STATUS_OK: False, KEY_ERROR: "invalid command"})
                else:
                    await ws.send_json({"echo": obj})
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)
        finally:
            await _unregister_websocket(ws)

    @app.get("/api/stream", tags=["stream"])
    async def stream(request: Request, channel: str | None = None):
        _require_token(request)
        """Server-Sent Events endpoint streaming new terminal entries for a channel.

        Example: /api/stream?channel=Errors
        """

        async def event_generator(ch: str | None):
            try:
                from src.system.enhanced_terminal_ecosystem import \
                    TerminalManager
            except Exception:
                yield (
                    'event: error\nretry: 1000\ndata: {KEY_ERROR: "TerminalManager not available"}\n\n'
                )
                return
            tm = TerminalManager.get_instance()
            last = None
            while True:
                if await request.is_disconnected():
                    break
                try:
                    if ch:
                        recent = tm.recent(ch, n=50)
                    else:
                        # if no channel specified, aggregate latest from all channels
                        recent = []
                        for c in tm.list_channels():
                            recent.extend(tm.recent(c, n=5))
                        recent = sorted(recent, key=lambda x: x.get("ts", ""))[-50:]
                    new_items = []
                    for item in recent:
                        its = item.get("ts")
                        if not its:
                            continue
                        if last is None or its > last:
                            new_items.append(item)
                    if new_items:
                        last = new_items[-1].get("ts")
                        for it in new_items:
                            payload = json.dumps(it, ensure_ascii=False)
                            yield f"data: {payload}\n\n"
                except Exception:
                    yield "event: error\ndata: {}\n\n"
                await asyncio.sleep(1.0)

        return StreamingResponse(event_generator(channel), media_type="text/event-stream")

    @app.on_event("startup")
    async def _startup_tasks():
        # start background poller that broadcasts terminal updates to websockets
        loop = asyncio.get_event_loop()
        _poll_task = loop.create_task(_poll_terminal_manager_and_broadcast())
        _background_tasks.add(_poll_task)
        _poll_task.add_done_callback(_background_tasks.discard)


def run_standalone(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run using uvicorn when available."""
    try:
        import uvicorn

        uvicorn.run("src.system.chatgpt_bridge:app", host=host, port=port, log_level="info")
    except Exception as exc:
        logger.error("Failed to start uvicorn: %s", exc)


if __name__ == "__main__":
    run_standalone()
