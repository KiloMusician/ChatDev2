"""Agent Awareness — single import for any agent to understand the live ecosystem.

Every agent (Culture Ship, Codex, Claude, Copilot, LM Studio, Ollama, ChatDev,
OpenClaw, SkyClaw, MetaClaw, Hermes, HuggingFace, Intermediary, AI Council,
Shepherd, etc.) can call::

    from src.system.agent_awareness import get_snapshot, emit

    snap = get_snapshot()          # What's alive right now?
    emit("claude", "Starting analysis...", level="INFO")   # Write to terminal
    emit.broadcast("Build complete", level="INFO")         # All terminals

The snapshot is a lightweight dict; no heavy imports, no blocking calls.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_AWARENESS_CACHE = _REPO_ROOT / "state" / "agent_awareness_snapshot.json"
_REGISTRY_PATH = _REPO_ROOT / "state" / "terminal_pid_registry.json"
_LOG_DIR = _REPO_ROOT / "data" / "terminal_logs"


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


def get_snapshot(refresh: bool = False) -> dict[str, Any]:
    """Return a dict describing the live ecosystem state.

    Fields
    ------
    terminals : dict[role, {pid, status, log_file, write_count}]
    output_channels : dict[name, {type, url_or_path, status}]
    agents : dict[name, {role, terminal_role, available}]
    timestamp : str ISO
    """
    if not refresh and _AWARENESS_CACHE.exists():
        try:
            data = json.loads(_AWARENESS_CACHE.read_text(encoding="utf-8"))
            # Return cached if < 60s old
            ts = datetime.fromisoformat(data.get("timestamp", "2000-01-01"))
            if (datetime.now() - ts).total_seconds() < 60:
                return data
        except (json.JSONDecodeError, ValueError):
            pass

    snap = _build_snapshot()
    try:
        _AWARENESS_CACHE.parent.mkdir(parents=True, exist_ok=True)
        _AWARENESS_CACHE.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    except OSError:
        pass
    return snap


def _build_snapshot() -> dict[str, Any]:
    from src.system.terminal_pid_registry import (AGENT_TO_ROLE,
                                                  TERMINAL_ROLES, get_registry)

    registry = get_registry()
    registry._refresh_status()

    # Terminal section
    terminals: dict[str, Any] = {}
    for role in TERMINAL_ROLES:
        entry = registry.entries.get(role)
        log_path = _LOG_DIR / f"{role}.log"
        terminals[role] = {
            "pid": entry.pid if entry else None,
            "status": entry.status if entry else "unregistered",
            "log_file": str(log_path),
            "write_count": entry.write_count if entry else 0,
            "last_write": entry.last_write if entry else None,
            "watcher_script": entry.watcher_script if entry else None,
        }

    # Output channels
    output_channels = _probe_output_channels()

    # Agent → terminal mapping
    agents: dict[str, Any] = {}
    for agent_name, role in AGENT_TO_ROLE.items():
        entry = registry.entries.get(role)
        agents[agent_name] = {
            "terminal_role": role,
            "terminal_pid": entry.pid if entry else None,
            "terminal_status": entry.status if entry else "unregistered",
            "log_file": str(_LOG_DIR / f"{role}.log"),
        }

    return {
        "timestamp": datetime.now().isoformat(),
        "terminals": terminals,
        "output_channels": output_channels,
        "agents": agents,
        "active_terminal_count": sum(1 for t in terminals.values() if t["status"] == "active"),
        "active_channel_count": sum(
            1 for c in output_channels.values() if c.get("status") == "online"
        ),
    }


def _probe_output_channels() -> dict[str, Any]:
    """Quick non-blocking probe of known output channels."""
    channels: dict[str, Any] = {}

    # OpenClaw WebSocket gateway
    openclaw_url = os.environ.get("OPENCLAW_GATEWAY_URL", "ws://127.0.0.1:18789")
    channels["openclaw"] = {
        "type": "websocket",
        "url": openclaw_url,
        "status": _http_check("http://127.0.0.1:18789/"),
        "description": "12+ messaging platforms (Slack, Discord, Telegram, Teams, …)",
    }

    # SkyClaw HTTP gateway
    skyclaw_url = os.environ.get("SKYCLAW_GATEWAY_URL", "http://127.0.0.1:8080")
    channels["skyclaw"] = {
        "type": "http",
        "url": skyclaw_url,
        "status": _http_check(f"{skyclaw_url}/health"),
        "description": "Rust AI sidecar — persistent memory, multi-provider chat",
    }

    # Guild board event bus
    guild_events = _REPO_ROOT / "state" / "guild" / "guild_events.jsonl"
    channels["guild_events"] = {
        "type": "jsonl",
        "path": str(guild_events),
        "status": "online" if guild_events.exists() else "offline",
        "description": "Quest/agent event bus (JSONL + DuckDB dual-write)",
    }

    # Terminal log files
    channels["terminal_logs"] = {
        "type": "file",
        "path": str(_LOG_DIR),
        "status": "online" if _LOG_DIR.exists() else "offline",
        "description": "NDJSON per-agent log files watched by PowerShell terminals",
    }

    # SimulatedVerse consciousness state
    sv_state = _REPO_ROOT.parent.parent / "SimulatedVerse" / "SimulatedVerse" / "mind-state.json"
    channels["simulatedverse"] = {
        "type": "file",
        "path": str(sv_state),
        "status": "online" if sv_state.exists() else "offline",
        "description": "Consciousness level, breathing factor, stage",
    }

    # OpenTelemetry / Jaeger tracing
    channels["jaeger"] = {
        "type": "http",
        "url": "http://localhost:16686",
        "status": _http_check("http://localhost:16686/"),
        "description": "Distributed tracing UI",
    }

    return channels


def _http_check(url: str, timeout: float = 0.5) -> str:
    """Return 'online' | 'offline' without raising."""
    try:
        import urllib.request

        req = urllib.request.Request(url, method="GET")  # type: ignore[call-overload]
        with urllib.request.urlopen(req, timeout=timeout):
            return "online"
    except Exception:
        return "offline"


# ---------------------------------------------------------------------------
# Emit (write to terminal log files)
# ---------------------------------------------------------------------------


class _Emitter:
    """Callable emit object — supports both `emit(agent, msg)` and `emit.broadcast(msg)`."""

    def __call__(
        self,
        agent_or_role: str,
        message: str,
        level: str = "INFO",
        source: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        """Write *message* to the terminal log file for *agent_or_role*."""
        from src.system.terminal_pid_registry import get_registry

        return get_registry().write(agent_or_role, message, level, source, extra)

    def broadcast(
        self,
        message: str,
        level: str = "INFO",
        source: str = "system",
        roles: list[str] | None = None,
    ) -> int:
        """Write *message* to multiple terminal log files. Returns count written."""
        from src.system.terminal_pid_registry import get_registry

        return get_registry().broadcast(message, level, source, roles)

    def event(
        self,
        agent_or_role: str,
        event_type: str,
        payload: dict[str, Any],
        level: str = "INFO",
    ) -> bool:
        """Write a structured event (with type field) to an agent's terminal."""
        message = f"[{event_type}] {payload.get('message', json.dumps(payload))}"
        extra = {"event_type": event_type, **{k: v for k, v in payload.items() if k != "message"}}
        return self(agent_or_role, message, level=level, source=agent_or_role, extra=extra)

    def task_started(self, agent: str, task_id: str, description: str) -> None:
        self.event(agent, "task_started", {"task_id": task_id, "message": description}, "INFO")
        self.event(
            "tasks",
            "task_started",
            {"task_id": task_id, "agent": agent, "message": description},
            "INFO",
        )

    def task_completed(self, agent: str, task_id: str, summary: str) -> None:
        self.event(agent, "task_completed", {"task_id": task_id, "message": summary}, "INFO")
        self.event(
            "tasks",
            "task_completed",
            {"task_id": task_id, "agent": agent, "message": summary},
            "INFO",
        )
        self.event(
            "metrics",
            "task_completed",
            {"task_id": task_id, "agent": agent, "message": summary},
            "INFO",
        )

    def task_failed(self, agent: str, task_id: str, error: str) -> None:
        self.event(agent, "task_failed", {"task_id": task_id, "message": error}, "ERROR")
        self.event(
            "errors", "task_failed", {"task_id": task_id, "agent": agent, "message": error}, "ERROR"
        )

    def agent_online(self, agent: str, detail: str = "") -> None:
        self.event(
            "agents",
            "agent_online",
            {"agent": agent, "message": detail or f"{agent} is online"},
            "INFO",
        )
        self(agent, f"Online — {detail}" if detail else "Online", level="INFO", source=agent)

    def inter_agent(self, source: str, target: str, message: str) -> None:
        """Route inter-agent message to both agents and the intermediary terminal."""
        self("intermediary", f"{source} → {target}: {message}", level="INFO", source=source)
        self(source, f"[To {target}] {message}", level="INFO", source=source)
        self(target, f"[From {source}] {message}", level="INFO", source=source)


emit = _Emitter()


# ---------------------------------------------------------------------------
# Terminal awareness report (human-readable)
# ---------------------------------------------------------------------------


def awareness_report() -> str:
    """Return a colorful ASCII report of the current ecosystem state."""
    snap = get_snapshot(refresh=True)
    lines = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║         NuSyQ-Hub  —  Agent Awareness Snapshot              ║",
        f"║  {snap['timestamp'][:19]}  —  Terminals: {snap['active_terminal_count']}/23 active         ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  TERMINALS                                                   ║",
    ]
    for role, info in snap["terminals"].items():
        pid_str = str(info["pid"]) if info["pid"] else "  ——"
        status_icon = "●" if info["status"] == "active" else "○"
        writes = info["write_count"]
        lines.append(f"║  {status_icon} {role:<20} pid={pid_str:<7} writes={writes:>5}  ║")

    lines += [
        "╠══════════════════════════════════════════════════════════════╣",
        "║  OUTPUT CHANNELS                                             ║",
    ]
    for name, info in snap["output_channels"].items():
        status_icon = "●" if info.get("status") == "online" else "○"
        lines.append(
            f"║  {status_icon} {name:<20} {info['type']:<12} {info.get('status', '?'):<8}  ║"
        )

    lines.append("╚══════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


def broadcast_awareness_snapshot() -> None:
    """Emit the current awareness snapshot to the metrics terminal.

    Call this periodically (e.g., every 60s) to give the metrics terminal
    a living pulse of the ecosystem state.  Safe to call from any thread.
    """
    try:
        snap = get_snapshot(refresh=True)
        active = snap["active_terminal_count"]
        total = len(snap["terminals"])
        channels_online = sum(
            1 for c in snap["output_channels"].values() if c.get("status") == "online"
        )
        channels_total = len(snap["output_channels"])
        report_line = (
            f"NuSyQ ecosystem: {active}/{total} terminals active | "
            f"{channels_online}/{channels_total} channels online | "
            f"snapshot={snap['timestamp'][:19]}"
        )
        emit("metrics", report_line, level="INFO", source="awareness")
    except Exception:
        pass
