"""Shared utilities for nusyq action modules."""

from __future__ import annotations

import importlib
import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    UTC = timezone.utc  # noqa: UP017


def load_otel_bridge() -> tuple[Any | None, str, str | None]:
    """Load tracing bridge from legacy or canonical module paths.

    Returns:
        tuple[module|None, module_name, error]
        - module_name is ``unavailable`` when no bridge can be loaded.
    """
    errors: list[str] = []
    for module_name in ("otel", "src.observability.otel"):
        try:
            return importlib.import_module(module_name), module_name, None
        except Exception as exc:
            errors.append(f"{module_name}: {exc!s}")
    return None, "unavailable", "; ".join(errors) if errors else "otel bridge not found"


def parse_kv_args(args: Iterable[str]) -> dict[str, Any]:
    """Parse CLI-style --key=value args with simple type coercion."""
    updates: dict[str, Any] = {}
    for arg in args:
        if arg.startswith("--") and "=" in arg:
            key, value = arg[2:].split("=", 1)
            key_norm = key.replace("-", "_")
            low = value.lower()
            if low in {"true", "false"}:
                updates[key_norm] = low == "true"
                continue
            try:
                updates[key_norm] = float(value) if "." in value else int(value)
            except ValueError:
                updates[key_norm] = value
    return updates


def write_state_report(hub_path: Path, filename: str, payload: dict) -> Path:
    """Write a JSON report to state/reports using spine helper if available."""
    report_path = hub_path / "state" / "reports" / filename
    try:
        spine = importlib.import_module("scripts.start_nusyq")
        writer = getattr(spine, "_write_json_report", None)
        if callable(writer):
            writer(report_path, payload)
            return report_path
    except Exception:
        pass

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report_path


# Quest logging helpers — added 2026-02-25
# Enables all CLI actions to log to quest system automatically


def log_action_to_quest(action_name: str, status: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Log action execution to quest system with graceful degradation.

    Args:
        action_name: Name of action (e.g., "search_keyword", "heal_imports")
        status: Execution status ("started", "completed", "failed", "skipped")
        metadata: Dict with additional context (exit_code, result_count, error, etc.)

    Returns:
        dict: {"status": "success"} if logged, {"status": "degraded"} if quest unavailable

    Graceful Degradation:
        - Quest system unavailable → Logs to stderr, returns degraded status
        - No exception raised, action continues normally
        - Logged to console for debugging: "[QUEST LOGGING UNAVAILABLE]"
    """
    from datetime import datetime

    try:
        from src.Rosetta_Quest_System.quest_engine import log_event

        # Build event details from metadata + defaults
        event_details = {
            "action": action_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }

        if metadata:
            event_details.update(metadata)

        # Log to quest system
        log_event(
            event=f"action_{action_name}",
            details=event_details,
        )

        return {"success": True, "status": "success", "action": action_name}

    except ImportError as e:
        # Quest system unavailable (not installed in this context)
        print(f"[QUEST LOGGING UNAVAILABLE] {action_name}: {e!s}", file=__import__("sys").stderr)
        return {"success": False, "status": "degraded", "reason": "quest_unavailable"}

    except Exception as e:
        # Unexpected error in quest logging
        print(f"[QUEST LOGGING ERROR] {action_name}: {e!s}", file=__import__("sys").stderr)
        return {"success": False, "status": "degraded", "reason": "quest_error"}


def emit_action_receipt(action_name: str, exit_code: int, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Emit standardized action receipt to quest system.

    Every CLI action should call this at the point of completion/exit.

    Args:
        action_name: Name of action
        exit_code: 0 = success, non-zero = failure
        metadata: Dict with results (result_count, files_modified, duration_ms, etc.)

    Returns:
        dict: Receipt confirmation (status, action, logged)

    Usage Pattern (in every handler):
        ```python
        def handle_my_action(args):
            try:
                # ... do work ...
                result = {"status": "success", "files": 42}
                emit_action_receipt("my_action", exit_code=0, metadata=result)
                return result
            except Exception as e:
                emit_action_receipt("my_action", exit_code=1, metadata={"error": str(e)})
                raise
        ```
    """
    from datetime import datetime

    # Build receipt
    receipt = {
        "action": action_name,
        "exit_code": exit_code,
        "success": exit_code == 0,
        "timestamp": datetime.now().isoformat(),
    }

    if metadata:
        receipt.update(metadata)

    # Log to quest system
    status = "completed" if exit_code == 0 else "failed"
    log_action_to_quest(action_name, status=status, metadata=receipt)

    return {
        "success": True,
        "status": "receipt_emitted",
        "action": action_name,
        "logged": True,
    }


def collect_audit_intelligence(
    hub_path: Path,
    *,
    max_audits: int = 5,
    include_sessions: bool = False,
) -> dict[str, Any]:
    """Collect lightweight audit/tutorial doc signals for status surfaces.

    This is intentionally read-only and metadata-only (no full document parsing).
    """
    docs_root = hub_path / "docs"
    if not docs_root.exists():
        return {
            "status": "unavailable",
            "reason": "docs_not_found",
            "hub_path": str(hub_path),
            "generated_at": datetime.now(UTC).isoformat(),
        }

    canonical_paths = [
        docs_root / "SYSTEM_AUDIT_2026-02-25.md",
        docs_root / "SYSTEM_WIRING_MAP_2026-02-25.md",
        docs_root / "ROSETTA_STONE.md",
        docs_root / "AGENT_TUTORIAL.md",
        docs_root / "Analysis" / "extensions" / "EXTENSION_AUDIT_REPORT_20251227.md",
    ]

    def _meta(path: Path) -> dict[str, Any]:
        exists = path.exists()
        payload: dict[str, Any] = {
            "path": (path.relative_to(hub_path).as_posix() if path.is_absolute() else path.as_posix()),
            "exists": exists,
        }
        if exists:
            stat = path.stat()
            ts = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
            age_hours = max(
                0.0,
                round((datetime.now(UTC) - ts).total_seconds() / 3600.0, 2),
            )
            payload.update(
                {
                    "modified_at": ts.isoformat(),
                    "age_hours": age_hours,
                    "bytes": int(stat.st_size),
                }
            )
        return payload

    canonical = [_meta(path) for path in canonical_paths]

    audit_files = sorted(
        [p for p in docs_root.rglob("*audit*.md") if p.is_file()],
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
        reverse=True,
    )[: max(1, max_audits)]
    recent_audits = [_meta(path) for path in audit_files]

    latest_sessions: list[dict[str, Any]] = []
    if include_sessions:
        sessions_dir = docs_root / "Agent-Sessions"
        session_files = (
            sorted(
                [p for p in sessions_dir.glob("SESSION_*.md") if p.is_file()],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )[:3]
            if sessions_dir.exists()
            else []
        )
        latest_sessions = [_meta(path) for path in session_files]

    return {
        "status": "ok",
        "generated_at": datetime.now(UTC).isoformat(),
        "canonical": canonical,
        "recent_audits": recent_audits,
        "latest_sessions": latest_sessions,
        "recommended_commands": [
            "python scripts/start_nusyq.py search index-health",
            "python scripts/start_nusyq.py trace_service_status",
            "python scripts/start_nusyq.py culture_ship_status",
            "python scripts/start_nusyq.py ai_status --json",
        ],
    }


def format_audit_intelligence_lines(
    payload: dict[str, Any],
    *,
    max_lines: int = 5,
) -> list[str]:
    """Format compact human-readable lines for status output."""
    if payload.get("status") != "ok":
        reason = payload.get("reason", "unavailable")
        return [f"audit intelligence unavailable ({reason})"]

    lines: list[str] = []
    for item in payload.get("canonical", []):
        if not isinstance(item, dict) or not item.get("exists"):
            continue
        age = item.get("age_hours")
        age_display = f"{age}h" if isinstance(age, (int, float)) else "n/a"
        lines.append(f"{item.get('path')} (age={age_display})")
        if len(lines) >= max_lines:
            break

    if not lines:
        lines.append("no canonical audit/tutorial docs found")

    return lines
