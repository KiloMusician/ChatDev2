#!/usr/bin/env python3
"""Terminal management actions for NuSyQ orchestration.

Handles activation, monitoring, and intelligence routing for 23 specialized terminals.
"""

import asyncio
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - Python 3.10 compatibility
    UTC = timezone.utc  # noqa: UP017

# Add repository root to sys.path for src imports
repo_root = str(Path(__file__).resolve().parents[2])
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from scripts.nusyq_actions.shared import emit_action_receipt
from src.system.output_source_intelligence import get_output_intelligence
from src.system.terminal_intelligence_orchestrator import get_orchestrator

logger = logging.getLogger(__name__)


def _normalize_channel_name(name: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", name)
    if not tokens:
        return "terminal"
    return "_".join(token.lower() for token in tokens)


def _channel_log_path(channel: str) -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "data" / "terminal_logs" / f"{_normalize_channel_name(channel)}.log"


def _freshness_label(age_seconds: float) -> str:
    if age_seconds < 300:
        return "HOT"
    if age_seconds < 3600:
        return "WARM"
    return "COLD"


def _channel_watcher_slug(channel: str) -> str:
    overrides = {
        "AI Council": "ai_council",
        "ChatGPT Bridge": "chatgpt_bridge",
        "LM Studio": "lmstudio",
        "PowerShell Extension": "powershell_extension",
        "SimulatedVerse": "simulatedverse",
    }
    return overrides.get(channel, _normalize_channel_name(channel))


def _infer_channel_agents(name: str, command_text: str = "") -> list[str]:
    haystack = f"{name} {command_text}".lower()
    agents: set[str] = set()

    def _maybe_add(token: str, label: str) -> None:
        if token in haystack:
            agents.add(label)

    _maybe_add("claude", "Claude")
    _maybe_add("copilot", "Copilot")
    _maybe_add("codex", "Codex")
    _maybe_add("chatdev", "ChatDev")
    _maybe_add("council", "AI Council")
    _maybe_add("intermediary", "Intermediary")
    _maybe_add("ollama", "Ollama")
    _maybe_add("lm studio", "LM Studio")
    _maybe_add("lmstudio", "LM Studio")
    _maybe_add("culture ship", "Culture Ship")
    _maybe_add("moderator", "Moderator")
    _maybe_add("chatgpt", "ChatGPT Bridge")
    _maybe_add("simulated verse", "SimulatedVerse")
    _maybe_add("simulatedverse", "SimulatedVerse")
    _maybe_add("future", "Future")
    if "agents" in haystack:
        for agent in ("OpenClaw", "SkyClaw", "MetaClaw", "Hermes-Agent", "Shepherd", "Hugging Face"):
            agents.add(agent)
    if "system" in haystack:
        for agent in ("OpenClaw", "SkyClaw", "MetaClaw"):
            agents.add(agent)
    return sorted(agents)


def _infer_channel_purpose(name: str, command_text: str = "") -> str:
    key = _normalize_channel_name(name)
    if "errors" in key:
        return "error monitoring"
    if "suggestions" in key:
        return "suggestion stream"
    if "tasks" in key:
        return "task queue"
    if "tests" in key:
        return "test telemetry"
    if "metrics" in key:
        return "metrics and health"
    if "anomalies" in key:
        return "anomaly detection"
    if "future" in key:
        return "future prediction stream"
    if "council" in key:
        return "multi-agent council"
    if "intermediary" in key:
        return "AI routing bridge"
    if "culture_ship" in key:
        return "culture ship interface"
    if "chatdev" in key:
        return "multi-agent development"
    if "ollama" in key:
        return "local model runtime"
    if key in {"lm_studio", "lmstudio"}:
        return "OpenAI-compatible model runtime"
    if "system" in key:
        return "system status"
    if "agents" in key:
        return "agent coordination hub"
    if "main" in key:
        return "main operational console"
    if "codex" in key or "copilot" in key or "claude" in key:
        return "agent log watcher"
    if "watch_" in command_text.lower():
        return "terminal watcher"
    return "specialized terminal"


def _read_sessions_payload(root: Path) -> tuple[str | None, list[dict[str, Any]], Path]:
    sessions_path = root / ".vscode" / "sessions.json"
    if not sessions_path.exists():
        return None, [], sessions_path
    try:
        payload = json.loads(sessions_path.read_text(encoding="utf-8"))
    except Exception:
        return None, [], sessions_path

    sessions = payload.get("sessions", {}) if isinstance(payload, dict) else {}
    active_session = None
    if isinstance(payload, dict):
        active_session = payload.get("active") or payload.get("activeSession")
    active_entries = []
    if isinstance(sessions, dict) and active_session in sessions and isinstance(sessions[active_session], list):
        active_entries = sessions[active_session]
    return str(active_session) if active_session else None, active_entries, sessions_path


def _resolve_workspace_script_path(command_text: str, root: Path) -> Path | None:
    if not command_text:
        return None
    match = re.search(r'-File\s+("?)([^"\n]+?\.ps1)\1(?:\s|$)', command_text, re.IGNORECASE)
    if not match:
        return None
    raw = match.group(2).replace("\\", "/")
    basename = Path(raw).name
    candidates = [
        root / "data" / "terminal_watchers" / basename,
        root / "scripts" / "terminals" / basename,
        root / ".vscode" / basename,
    ]
    raw_path = Path(raw)
    if raw_path.is_absolute() and raw_path.exists():
        return raw_path
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _infer_log_paths_from_script(script_path: Path | None, root: Path, fallback_key: str) -> list[str]:
    results: set[str] = set()
    if script_path and script_path.exists():
        text = script_path.read_text(encoding="utf-8", errors="ignore")
        patterns = [
            r"data[\\/]+terminal_logs[\\/]+([A-Za-z0-9_.-]+\.log)",
            r"state[\\/]+logs[\\/]+([A-Za-z0-9_.-]+\.log)",
            r"state[\\/]+reports[\\/]+([A-Za-z0-9_.-]+\.(?:log|md|json))",
            r"docs[\\/]+Reports[\\/]+diagnostics[\\/]+([A-Za-z0-9_.-]+\.(?:log|md|json))",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                relative = match.group(0).replace("\\", "/")
                results.add(str(root / Path(relative)))
    if script_path and script_path.name.startswith("watch_") and fallback_key:
        results.add(str(root / "data" / "terminal_logs" / f"{fallback_key}.log"))
    return sorted(results)


def _build_terminal_awareness(root: Path) -> dict[str, Any]:
    active_session, active_entries, sessions_path = _read_sessions_payload(root)
    session_entries_by_key: dict[str, dict[str, Any]] = {}
    for entry in active_entries:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "unknown")
        session_entries_by_key[_normalize_channel_name(name)] = entry

    orchestrator = get_orchestrator()
    from src.system.enhanced_terminal_ecosystem import TerminalManager

    tm = TerminalManager.get_instance()
    configured_channels = set(orchestrator.terminals.keys())
    runtime_channels = set(tm.list_channels())
    known_channels = sorted(configured_channels | runtime_channels | set(session_entries_by_key))

    terminal_entries: list[dict[str, Any]] = []
    agent_index: dict[str, dict[str, Any]] = {}
    output_surfaces: dict[str, dict[str, Any]] = {}

    def _push_surface(label: str, file_path: Path, category: str) -> None:
        key = str(file_path)
        if key not in output_surfaces:
            output_surfaces[key] = {
                "label": label,
                "path": key,
                "category": category,
                "exists": file_path.exists(),
            }

    for channel in known_channels:
        key = _normalize_channel_name(channel)
        session_entry = session_entries_by_key.get(key, {})
        display_name = str(session_entry.get("name") or channel)
        commands = session_entry.get("commands") if isinstance(session_entry, dict) else []
        commands = commands if isinstance(commands, list) else []
        command_text = " && ".join(str(command) for command in commands)
        watcher_slug = _channel_watcher_slug(display_name)
        watcher_path = root / "data" / "terminal_watchers" / f"watch_{watcher_slug}_terminal.ps1"
        script_path = _resolve_workspace_script_path(command_text, root)
        log_path = _channel_log_path(display_name)
        agents = _infer_channel_agents(display_name, command_text)
        purpose = _infer_channel_purpose(display_name, command_text)
        surfaces = _infer_log_paths_from_script(script_path, root, key)
        surfaces.append(str(log_path))
        unique_surfaces = sorted({surface for surface in surfaces if surface})

        _push_surface(f"{display_name} Log", log_path, "terminal-log")
        for surface in unique_surfaces:
            surface_path = Path(surface)
            category = "terminal-log" if "terminal_logs" in surface else "report"
            _push_surface(f"{display_name} Surface", surface_path, category)

        terminal_entries.append(
            {
                "channel": channel,
                "display_name": display_name,
                "key": key,
                "purpose": purpose,
                "agents": agents,
                "watcher_path": str(watcher_path),
                "watcher_exists": watcher_path.exists(),
                "script_path": str(script_path) if script_path else None,
                "script_exists": bool(script_path and script_path.exists()),
                "command_text": command_text or None,
                "log_path": str(log_path),
                "log_exists": log_path.exists(),
                "output_surfaces": unique_surfaces,
                "configured_in_session": bool(session_entry),
                "configured_in_orchestrator": channel in configured_channels,
                "observed_in_runtime": channel in runtime_channels,
            }
        )

        for agent in agents:
            bucket = agent_index.setdefault(
                agent,
                {
                    "agent": agent,
                    "terminals": set(),
                    "purposes": set(),
                    "output_surfaces": set(),
                },
            )
            bucket["terminals"].add(display_name)
            bucket["purposes"].add(purpose)
            bucket["output_surfaces"].update(unique_surfaces)

    _push_surface("Agent Bus", root / "state" / "logs" / "agent_bus.log", "coordination")
    _push_surface("Current State", root / "state" / "reports" / "current_state.md", "state")
    _push_surface(
        "Unified Error Report",
        root / "state" / "reports" / "unified_error_report_latest.md",
        "diagnostics",
    )
    _push_surface(
        "Quest Log",
        root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl",
        "quest",
    )

    agent_registry = [
        {
            "agent": payload["agent"],
            "terminals": sorted(payload["terminals"]),
            "purposes": sorted(payload["purposes"]),
            "output_surfaces": sorted(payload["output_surfaces"]),
        }
        for payload in sorted(agent_index.values(), key=lambda item: item["agent"].lower())
    ]

    return {
        "active_session": active_session,
        "sessions_path": str(sessions_path),
        "terminals": terminal_entries,
        "agent_registry": agent_registry,
        "output_surfaces": list(output_surfaces.values()),
    }


def _build_terminal_snapshot(limit_per_channel: int = 20) -> dict[str, Any]:
    """Build a stable, machine-readable terminal snapshot payload."""
    from src.system.enhanced_terminal_ecosystem import TerminalManager

    orchestrator = get_orchestrator()
    tm = TerminalManager.get_instance()
    now = datetime.now(UTC)
    root = Path(__file__).resolve().parents[2]

    configured_channels = set(orchestrator.terminals.keys())
    runtime_channels = set(tm.list_channels())
    channels = sorted(configured_channels | runtime_channels)

    entries: list[dict[str, Any]] = []
    hot = warm = cold = missing = 0

    for channel in channels:
        log_path = _channel_log_path(channel)
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

        recent_entries = tm.recent(channel, n=max(1, min(limit_per_channel, 200)))
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

    awareness = _build_terminal_awareness(root)
    routing_summary: dict[str, Any] = {"total_sources": 0, "terminal_load": {}, "by_category": {}}
    try:
        intelligence = asyncio.run(get_output_intelligence())
        routing_summary = intelligence.generate_routing_map()
    except Exception as exc:
        routing_summary = {
            "total_sources": 0,
            "terminal_load": {},
            "by_category": {},
            "error": str(exc),
        }

    return {
        "schema_version": "1.0",
        "timestamp": now.isoformat(),
        "summary": {
            "total_channels": len(channels),
            "hot_channels": hot,
            "warm_channels": warm,
            "cold_channels": cold,
            "missing_logs": missing,
            "agent_registry_count": len(awareness.get("agent_registry", [])),
            "output_surface_count": len(awareness.get("output_surfaces", [])),
            "configured_session": awareness.get("active_session"),
            "output_sources_configured": int(routing_summary.get("total_sources", 0) or 0),
        },
        "channels": entries,
        "awareness": awareness,
        "output_routing": routing_summary,
    }


def _parse_stream_options(args: list[str] | None = None) -> dict[str, Any]:
    args = args or []
    options: dict[str, Any] = {
        "focus": "all",
        "follow": False,
        "lines": 40,
        "interval_s": 2.0,
    }
    for arg in args:
        token = str(arg).strip()
        if token in {"--follow", "-f"}:
            options["follow"] = True
        elif token.startswith("--focus="):
            options["focus"] = token.split("=", 1)[1].strip().lower() or "all"
        elif token.startswith("--lines="):
            try:
                options["lines"] = int(token.split("=", 1)[1].strip())
            except Exception:
                options["lines"] = 40
        elif token.startswith("--interval="):
            try:
                options["interval_s"] = float(token.split("=", 1)[1].strip())
            except Exception:
                options["interval_s"] = 2.0

    options["lines"] = max(1, min(int(options["lines"]), 400))
    options["interval_s"] = max(0.2, min(float(options["interval_s"]), 30.0))
    allowed_focus = {"all", "chatdev", "system", "autonomous", "council"}
    if options["focus"] not in allowed_focus:
        options["focus"] = "all"
    return options


def _iter_stream_sources(root: Path, focus: str) -> list[tuple[str, Path]]:
    """Return ordered stream sources for selected focus area."""
    focus_filters: dict[str, tuple[str, ...]] = {
        "all": (),
        "chatdev": ("chatdev", "council_chatdev"),
        "system": ("system", "autonomous_service", "task", "receipt"),
        "autonomous": ("autonomous_service", "auto_cycle", "zeta"),
        "council": ("council", "chatdev"),
    }

    explicit_sources: list[tuple[str, Path]] = [
        ("channel.system", root / "data" / "terminal_logs" / "system.log"),
        ("channel.chatdev", root / "data" / "terminal_logs" / "chatdev.log"),
        ("channel.tasks", root / "data" / "terminal_logs" / "tasks.log"),
        ("channel.zeta", root / "data" / "terminal_logs" / "zeta.log"),
        ("state.chatdev_latest", root / "state" / "logs" / "chatdev_latest.log"),
        (
            "state.council_chatdev_execution",
            root / "state" / "council_chatdev_loop" / "execution_log.jsonl",
        ),
        (
            "state.autonomous_checkpoint",
            root / "state" / "reports" / "autonomous_service_latest.json",
        ),
    ]

    glob_sources: list[tuple[str, str]] = [
        ("jobs.autonomous_service", "state/jobs/*autonomous_service*.*.log"),
        ("jobs.chatdev", "state/jobs/*chatdev*.*.log"),
        ("jobs.all", "state/jobs/*.*.log"),
        ("receipts.tracing", "docs/tracing/RECEIPTS/*.txt"),
    ]

    sources: list[tuple[str, Path]] = []
    for label, path in explicit_sources:
        sources.append((label, path))
    for label, pattern in glob_sources:
        matched = list(root.glob(pattern))
        matched.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        cap = 40
        if label == "receipts.tracing":
            cap = 12
        elif label in {"jobs.all", "jobs.chatdev", "jobs.autonomous_service"}:
            cap = 20
        for path in matched[:cap]:
            sources.append((label, path))

    filter_tokens = focus_filters.get(focus, ())
    if filter_tokens:
        filtered: list[tuple[str, Path]] = []
        for label, path in sources:
            haystack = f"{label} {path}".lower()
            if any(token in haystack for token in filter_tokens):
                filtered.append((label, path))
        sources = filtered

    # Deduplicate while preserving order
    deduped: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for label, path in sources:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((label, path))

    max_by_focus = {
        "all": 30,
        "system": 35,
        "autonomous": 25,
        "chatdev": 20,
        "council": 20,
    }
    max_total = max_by_focus.get(focus)
    if max_total is not None and len(deduped) > max_total:

        def _source_sort_key(item: tuple[str, Path]) -> tuple[int, float]:
            label, path = item
            priority = 1
            if label.startswith("channel.") or label.startswith("state."):
                priority = 0
            mtime = path.stat().st_mtime if path.exists() else 0.0
            return (priority, -mtime)

        deduped = sorted(deduped, key=_source_sort_key)[:max_total]

    return deduped


def _tail_lines(path: Path, line_count: int) -> list[str]:
    if not path.exists():
        return []
    if line_count <= 0:
        return []
    with path.open("rb") as fh:
        fh.seek(0, 2)
        end_pos = fh.tell()
        if end_pos <= 0:
            return []
        block_size = 8192
        data = b""
        pos = end_pos
        while pos > 0 and data.count(b"\n") <= line_count:
            read_size = min(block_size, pos)
            pos -= read_size
            fh.seek(pos)
            data = fh.read(read_size) + data
            if pos == 0:
                break
    text = data.decode("utf-8", errors="ignore")
    lines = text.splitlines()
    return lines[-line_count:] if lines else []


def _format_stream_line(label: str, line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    max_len = 500
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            obj = json.loads(stripped)
            ts = obj.get("timestamp") or obj.get("ts") or datetime.now(UTC).isoformat()
            level = (obj.get("level") or "INFO").upper()
            message = obj.get("message") or obj.get("msg") or str(obj)
            message = str(message)
            if len(message) > max_len:
                message = f"{message[:max_len]}... [truncated]"
            return f"[{ts}] [{label}] [{level}] {message}"
        except Exception:
            pass
    if len(stripped) > max_len:
        stripped = f"{stripped[:max_len]}... [truncated]"
    return f"[{label}] {stripped}"


def handle_terminals_stream(args: list[str] | None = None) -> int:
    """Unified live stream for terminal logs, job logs, and receipt traces."""
    root = Path(__file__).resolve().parents[2]
    opts = _parse_stream_options(args)
    focus = str(opts["focus"])
    follow = bool(opts["follow"])
    lines = int(opts["lines"])
    interval_s = float(opts["interval_s"])

    sources = _iter_stream_sources(root, focus)
    existing_sources = [(label, path) for label, path in sources if path.exists()]
    print("📡 NuSyQ Live Stream")
    print("=" * 80)
    print(f"focus={focus} | follow={follow} | lines={lines} | interval={interval_s:.1f}s")
    print(f"sources={len(existing_sources)}/{len(sources)} existing")
    for label, path in existing_sources[:15]:
        print(f"  - {label:28} {path}")
    if len(existing_sources) > 15:
        print(f"  ... +{len(existing_sources) - 15} additional sources")
    print("=" * 80)

    if not existing_sources:
        print("⚠️  No stream sources found for this focus.")
        print("Try: python scripts/start_nusyq.py terminals stream --focus=all --follow")
        emit_action_receipt(
            "terminals_stream",
            exit_code=1,
            metadata={"focus": focus, "sources": 0},
        )
        return 1

    cursor: dict[str, int] = {}

    # Initial tail snapshot
    printed = 0
    for label, path in existing_sources:
        tail = _tail_lines(path, lines)
        if not tail:
            continue
        print(f"\n--- {label} :: {path.name} ---")
        for raw_line in tail:
            out_line = _format_stream_line(label, raw_line)
            if out_line:
                print(out_line)
                printed += 1
        try:
            cursor[str(path)] = path.stat().st_size
        except Exception:
            cursor[str(path)] = 0

    if not follow:
        emit_action_receipt(
            "terminals_stream",
            exit_code=0,
            metadata={"focus": focus, "sources": len(existing_sources), "printed": printed},
        )
        return 0

    print("\n🔁 Following updates (Ctrl+C to stop)...")
    try:
        while True:
            # Re-resolve sources so newly created logs are picked up automatically.
            dynamic_sources = _iter_stream_sources(root, focus)
            for label, path in dynamic_sources:
                key = str(path)
                if not path.exists():
                    continue

                try:
                    size = path.stat().st_size
                except Exception:
                    continue

                old = cursor.get(key)
                if old is None:
                    # New source discovered while following.
                    cursor[key] = size
                    print(f"\n[stream] source discovered: {label} -> {path}")
                    continue

                if size < old:
                    # File rotated/truncated; restart at beginning.
                    old = 0

                if size == old:
                    continue

                try:
                    with path.open("r", encoding="utf-8", errors="ignore") as fh:
                        fh.seek(old)
                        chunk = fh.read()
                except Exception:
                    continue

                for raw_line in chunk.splitlines():
                    out_line = _format_stream_line(label, raw_line)
                    if out_line:
                        print(out_line)

                cursor[key] = size
            time.sleep(interval_s)
    except KeyboardInterrupt:
        print("\n⏹️  Stream stopped.")
        emit_action_receipt(
            "terminals_stream",
            exit_code=0,
            metadata={
                "focus": focus,
                "sources": len(existing_sources),
                "stopped": "keyboard_interrupt",
            },
        )
        return 0


async def _activate_terminals_async() -> int:
    """Async helper to activate terminal ecosystem."""
    try:
        orchestrator = get_orchestrator()
        orchestrator.activate_all_terminals()

        # Display dashboard
        dashboard = orchestrator.generate_terminal_dashboard()
        print(dashboard)

        # Show output source routing
        intelligence = await get_output_intelligence()
        routing_map = intelligence.generate_routing_map()

        print("\n" + "=" * 80)
        print(f"🎯 Output Source Intelligence: {routing_map['total_sources']} sources configured")
        print("\n📊 Terminal Load Distribution:")
        for terminal, count in sorted(routing_map["terminal_load"].items(), key=lambda x: -x[1]):
            print(f"  {terminal:20} ← {count:3} output sources")

        print("\n✅ Terminal ecosystem activated successfully!")
        return 0

    except Exception as e:
        logger.error(f"Failed to activate terminals: {e}", exc_info=True)
        print(f"❌ Error activating terminals: {e}")
        return 1


def handle_terminals_activate(_args: list[str] | None = None) -> int:
    """Activate the 23-terminal intelligence ecosystem."""
    rc = asyncio.run(_activate_terminals_async())
    emit_action_receipt("terminals_activate", exit_code=rc)
    return rc


def _terminals_status_async() -> int:
    """Helper to show terminal status."""
    try:
        orchestrator = get_orchestrator()
        dashboard = orchestrator.generate_terminal_dashboard()
        print(dashboard)

        # Count active terminals in-process
        active = sum(1 for state in orchestrator.terminals.values() if state.active)
        total = len(orchestrator.terminals)

        # Count recently active terminals by log freshness (cross-process signal)
        now = datetime.now(UTC)
        recent_active = 0
        print("\n📡 Recent Log Activity (cross-process):")
        for name in sorted(orchestrator.terminals.keys()):
            log_path = _channel_log_path(name)
            if not log_path.exists():
                print(f"  {name:20} MISSING   (no log)")
                continue
            age_s = (now - datetime.fromtimestamp(log_path.stat().st_mtime, UTC)).total_seconds()
            age_s = max(age_s, 0.0)
            freshness = _freshness_label(age_s)
            if freshness == "HOT":
                recent_active += 1
            print(f"  {name:20} {freshness:7} age={age_s:7.1f}s")

        print(f"\n📊 In-Process Status: {active}/{total} terminals active")
        print(f"📊 Recent Activity: {recent_active}/{total} terminals HOT (<5m)")
        return 0

    except Exception as e:
        logger.error(f"Failed to get terminal status: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return 1


def handle_terminals_status(_args: list[str] | None = None) -> int:
    """Show terminal ecosystem status."""
    rc = _terminals_status_async()
    emit_action_receipt("terminals_status", exit_code=rc)
    return rc


def _terminals_probe_async() -> int:
    """Emit probe events to all terminal channels and verify log ingestion."""
    try:
        from src.system.enhanced_terminal_ecosystem import TerminalManager

        orchestrator = get_orchestrator()
        tm = TerminalManager.get_instance()

        probe_id = datetime.now(UTC).strftime("probe_%Y%m%d_%H%M%S")
        print(f"🛰️ Emitting terminal probes ({probe_id})...\n")

        channels = sorted(orchestrator.terminals.keys())
        # Include supplemental operational channels that have dedicated watcher scripts.
        channels.extend(["PowerShell Extension", "pwsh"])

        sent = 0
        verified = 0
        for channel in channels:
            message = f"terminal_probe {probe_id} channel={channel}"
            tm.send(channel, "INFO", message, meta={"probe_id": probe_id, "channel": channel})
            sent += 1

            log_path = _channel_log_path(channel)
            if log_path.exists():
                try:
                    tail = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-25:]
                    if any(probe_id in line for line in tail):
                        verified += 1
                        print(f"  ✅ {channel:20} -> {log_path.name}")
                    else:
                        print(f"  ⚠️  {channel:20} -> {log_path.name} (probe not in tail yet)")
                except Exception:
                    print(f"  ⚠️  {channel:20} -> {log_path.name} (read error)")
            else:
                print(f"  ❌ {channel:20} -> missing log file")

        print(f"\n✅ Probe dispatch complete: sent={sent}, verified={verified}")
        return 0
    except Exception as e:
        logger.error(f"Probe failed: {e}", exc_info=True)
        print(f"❌ Probe error: {e}")
        return 1


def handle_terminals_probe(_args: list[str] | None = None) -> int:
    """Probe all terminal channels and verify logs."""
    rc = _terminals_probe_async()
    emit_action_receipt("terminals_probe", exit_code=rc)
    return rc


def _terminals_doctor_async() -> int:
    """Diagnose terminal ecosystem health and print remediation guidance."""
    try:
        orchestrator = get_orchestrator()
        root = Path(__file__).resolve().parents[2]
        watchers_dir = root / "data" / "terminal_watchers"
        sessions_path = root / ".vscode" / "sessions.json"
        now = datetime.now(UTC)

        channels = [*sorted(orchestrator.terminals.keys()), "PowerShell Extension", "pwsh"]

        # Channel slug overrides for watcher file names.
        slug_overrides = {
            "AI Council": "ai_council",
            "ChatGPT Bridge": "chatgpt_bridge",
            "LM Studio": "lmstudio",
            "PowerShell Extension": "powershell_extension",
            "SimulatedVerse": "simulatedverse",
        }

        print("🩺 Terminal Doctor Report")
        print("=" * 80)

        total = 0
        healthy = 0
        warnings = 0
        critical = 0
        stale_channels: list[str] = []
        missing_logs: list[str] = []
        bad_json_channels: list[str] = []

        print("\n📡 Channel Health:")
        for channel in channels:
            total += 1
            log_path = _channel_log_path(channel)
            if not log_path.exists():
                critical += 1
                missing_logs.append(channel)
                print(f"  ❌ {channel:20} MISSING log={log_path.name}")
                continue

            size = log_path.stat().st_size
            age_s = max(
                (now - datetime.fromtimestamp(log_path.stat().st_mtime, UTC)).total_seconds(),
                0.0,
            )
            freshness = _freshness_label(age_s)

            lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if size == 0 or not lines:
                warnings += 1
                stale_channels.append(channel)
                print(f"  ⚠️  {channel:20} EMPTY   age={age_s:7.1f}s")
                continue

            last = lines[-1].strip()
            if not (last.startswith("{") and last.endswith("}")):
                warnings += 1
                bad_json_channels.append(channel)
                print(f"  ⚠️  {channel:20} NONJSON age={age_s:7.1f}s")
                continue

            try:
                json.loads(last)
            except Exception:
                warnings += 1
                bad_json_channels.append(channel)
                print(f"  ⚠️  {channel:20} BADJSON age={age_s:7.1f}s")
                continue

            if freshness == "COLD":
                warnings += 1
                stale_channels.append(channel)
                print(f"  ⚠️  {channel:20} {freshness:6} age={age_s:7.1f}s")
            else:
                healthy += 1
                print(f"  ✅ {channel:20} {freshness:6} age={age_s:7.1f}s")

        print("\n🧩 Watcher Coverage:")
        missing_watchers: list[str] = []
        for channel in channels:
            slug = slug_overrides.get(channel, _normalize_channel_name(channel))
            watcher = watchers_dir / f"watch_{slug}_terminal.ps1"
            if watcher.exists():
                print(f"  ✅ {channel:20} {watcher.name}")
            else:
                missing_watchers.append(channel)
                print(f"  ❌ {channel:20} watch_{slug}_terminal.ps1 missing")

        print("\n🗂️ Session Wiring:")
        sessions_ok = True
        if not sessions_path.exists():
            sessions_ok = False
            critical += 1
            print("  ❌ .vscode/sessions.json missing")
        else:
            content = sessions_path.read_text(encoding="utf-8", errors="ignore")
            rel_refs = content.count("-File data/") + content.count("-File scripts/")
            if rel_refs > 0:
                sessions_ok = False
                warnings += 1
                print(f"  ⚠️  Found {rel_refs} relative -File references in sessions.json")
            else:
                print("  ✅ sessions.json uses non-relative script paths")

        print("\n📋 Summary:")
        print(f"  healthy={healthy}/{total}")
        print(f"  warnings={warnings}")
        print(f"  critical={critical}")

        print("\n🛠️ Remediation:")
        if not stale_channels and not missing_logs and not bad_json_channels and not missing_watchers and sessions_ok:
            print("  ✅ No action required. Terminal ecosystem is healthy.")
        else:
            print("  1. Re-prime channels: python scripts/start_nusyq.py terminals probe")
            print("  2. Rebuild watcher scripts/tasks: python scripts/activate_live_terminal_routing.py")
            print("  3. Re-check health: python scripts/start_nusyq.py terminals doctor")
            if stale_channels:
                print(f"  stale/empty channels: {', '.join(sorted(set(stale_channels)))}")
            if missing_logs:
                print(f"  missing logs: {', '.join(sorted(set(missing_logs)))}")
            if missing_watchers:
                print(f"  missing watchers: {', '.join(sorted(set(missing_watchers)))}")
            if bad_json_channels:
                print(f"  non-json tails: {', '.join(sorted(set(bad_json_channels)))}")

        return 0 if critical == 0 else 1
    except Exception as e:
        logger.error(f"Doctor failed: {e}", exc_info=True)
        print(f"❌ Doctor error: {e}")
        return 1


def handle_terminals_doctor(_args: list[str] | None = None) -> int:
    """Run terminal ecosystem health diagnostics."""
    rc = _terminals_doctor_async()
    emit_action_receipt("terminals_doctor", exit_code=rc)
    return rc


def handle_terminals_snapshot(args: list[str] | None = None) -> int:
    """Write and print a stable JSON terminal snapshot."""
    args = args or []
    limit = 20
    for arg in args:
        if arg.startswith("--limit="):
            with_value = arg.split("=", 1)[1].strip()
            try:
                limit = int(with_value)
            except Exception:
                limit = 20
    limit = max(1, min(limit, 200))

    try:
        payload = _build_terminal_snapshot(limit_per_channel=limit)
        root = Path(__file__).resolve().parents[2]
        report_dir = root / "state" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"terminal_snapshot_{stamp}.json"
        latest_path = report_dir / "terminal_snapshot_latest.json"
        awareness_path = report_dir / "terminal_awareness_latest.json"
        json_payload = json.dumps(payload, indent=2)
        report_path.write_text(json_payload, encoding="utf-8")
        latest_path.write_text(json_payload, encoding="utf-8")
        awareness_path.write_text(json.dumps(payload.get("awareness", {}), indent=2), encoding="utf-8")

        print(json_payload)
        print(f"\nSaved: {report_path}")
        emit_action_receipt(
            "terminals_snapshot",
            exit_code=0,
            metadata={
                "report_path": str(report_path),
                "awareness_path": str(awareness_path),
            },
        )
        return 0
    except Exception as e:
        logger.error(f"Terminal snapshot failed: {e}", exc_info=True)
        print(f"❌ Terminal snapshot error: {e}")
        emit_action_receipt(
            "terminals_snapshot",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return 1


async def _test_routing_async() -> int:
    """Async helper to test terminal routing."""
    try:
        orchestrator = get_orchestrator()
        intelligence = await get_output_intelligence()

        print("🧪 Testing Terminal Routing...\n")

        # Test terminal routing
        test_messages = [
            ("ERROR: Import failed in module.py", "ERROR"),
            ("SUGGESTION: Refactor this function", "INFO"),
            ("TASK: Implement feature XYZ", "INFO"),
            ("TEST: pytest passed 50/50 tests", "INFO"),
            ("METRIC: System health: 95%", "INFO"),
        ]

        print("📨 Terminal Message Routing:")
        for msg, level in test_messages:
            orchestrator.route_message(msg, level=level)
            print(f"  {msg[:50]:52} → routed")

        # Test output source routing
        print("\n📡 Output Source Routing:")
        test_outputs = [
            ("Ruff", "Found 42 errors in module.py", "ERROR"),
            ("GitHub Copilot chat", "Suggestion: Use list comprehension", "INFO"),
            ("Python Test Adapter Log", "pytest passed 100 tests", "INFO"),
            ("SonarQube for IDE", "Code smell detected", "WARNING"),
            ("Git", "Changes not staged for commit", "INFO"),
        ]

        for source, message, level in test_outputs:
            terminal = await intelligence.route_output(source, message, level)
            print(f"  [{source:30}] → {terminal or 'FILTERED'}")

        print("\n✅ Routing tests completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Routing test failed: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return 1


def handle_terminals_test(_args: list[str] | None = None) -> int:
    """Test terminal routing with sample messages."""
    rc = asyncio.run(_test_routing_async())
    emit_action_receipt("terminals_test", exit_code=rc)
    return rc


def handle_terminals(args: list[str] | None = None) -> int:
    """Main terminal management dispatcher.

    Usage:
        python start_nusyq.py terminals [activate|status|test|probe|doctor|snapshot|stream]

    Actions:
        activate - Activate all 23 terminals and display dashboard
        status   - Show current terminal ecosystem status
        test     - Run routing tests with sample messages
        probe    - Emit probe events to all channels and verify log ingestion
        doctor   - Diagnose terminal health and print concrete fixes
        snapshot - Emit stable JSON snapshot for agents/integrations
        stream   - Unified live stream (channels + jobs + receipts)
    """
    if not args or len(args) == 0:
        # Default: activate + status
        rc = handle_terminals_activate()
        emit_action_receipt("terminals", exit_code=rc, metadata={"subcommand": "activate"})
        return rc

    subcommand = args[0]

    if subcommand == "activate":
        rc = handle_terminals_activate(args[1:] if len(args) > 1 else None)
        emit_action_receipt("terminals", exit_code=rc, metadata={"subcommand": "activate"})
        return rc
    elif subcommand == "status":
        rc = handle_terminals_status(args[1:] if len(args) > 1 else None)
        emit_action_receipt("terminals", exit_code=rc, metadata={"subcommand": "status"})
        return rc
    elif subcommand == "test":
        rc = handle_terminals_test(args[1:] if len(args) > 1 else None)
        emit_action_receipt("terminals", exit_code=rc, metadata={"subcommand": "test"})
        return rc
    elif subcommand == "probe":
        rc = handle_terminals_probe(args[1:] if len(args) > 1 else None)
        emit_action_receipt("terminals", exit_code=rc, metadata={"subcommand": "probe"})
        return rc
    elif subcommand == "doctor":
        rc = handle_terminals_doctor(args[1:] if len(args) > 1 else None)
        emit_action_receipt("terminals", exit_code=rc, metadata={"subcommand": "doctor"})
        return rc
    elif subcommand == "snapshot":
        rc = handle_terminals_snapshot(args[1:] if len(args) > 1 else None)
        emit_action_receipt("terminals", exit_code=rc, metadata={"subcommand": "snapshot"})
        return rc
    elif subcommand == "stream":
        rc = handle_terminals_stream(args[1:] if len(args) > 1 else None)
        emit_action_receipt("terminals", exit_code=rc, metadata={"subcommand": "stream"})
        return rc
    else:
        print(f"❌ Unknown subcommand: {subcommand}")
        print("\nUsage: terminals [activate|status|test|probe|doctor|snapshot|stream]")
        emit_action_receipt(
            "terminals",
            exit_code=1,
            metadata={"error": "unknown_subcommand", "subcommand": subcommand},
        )
        return 1
