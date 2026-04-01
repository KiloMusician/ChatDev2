"""Action module: work/task/suggest operations."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.nusyq_actions.shared import emit_action_receipt

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    UTC = timezone.utc  # noqa: UP017

ACTIVE_QUEST_STATUSES = {"active", "pending", "in_progress", "todo", "open"}
ACTION_TYPE_TO_COMMAND = {
    "fix_error": "python scripts/start_nusyq.py doctor --quick --async --json",
    "resolve_quest": "python scripts/start_nusyq.py work",
    "expand_coverage": "python scripts/quality_orchestrator.py --skip-analysis",
    "heal_repository": "python scripts/start_nusyq.py heal",
    "validate_module": "python scripts/start_nusyq.py doctor --quick --json",
    "scale_orchestration": "python -m pytest tests/test_orchestration_comprehensive.py -q",
    "integrate_cross_repo": "python scripts/start_nusyq.py cross_sync",
    "improve_architecture": "python scripts/start_nusyq.py lifecycle_catalog",
}


def _extract_quest_fields(entry: dict[str, Any]) -> tuple[str, str, str, str]:
    """Extract canonical (id, title, status, timestamp) across mixed event schemas."""
    details = entry.get("details") if isinstance(entry.get("details"), dict) else {}
    quest_id = str(
        details.get("id") or details.get("quest_id") or entry.get("id") or entry.get("quest_id") or ""
    ).strip()
    title = str(
        details.get("title")
        or details.get("quest")
        or details.get("name")
        or entry.get("title")
        or entry.get("quest")
        or entry.get("name")
        or ""
    ).strip()
    status = (
        str(details.get("status") or details.get("new_status") or entry.get("status") or entry.get("state") or "")
        .strip()
        .lower()
    )
    timestamp = str(entry.get("timestamp") or details.get("updated_at") or "").strip()
    return quest_id, title, status, timestamp


def _normalize_title(title: str) -> str:
    return " ".join(title.strip().lower().split())


def _parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _is_newer(candidate: dict[str, str], existing: dict[str, str]) -> bool:
    candidate_ts = _parse_timestamp(candidate.get("timestamp", ""))
    existing_ts = _parse_timestamp(existing.get("timestamp", ""))
    if candidate_ts is not None and existing_ts is not None:
        return candidate_ts >= existing_ts
    if candidate_ts is not None:
        return True
    if existing_ts is not None:
        return False
    return candidate.get("timestamp", "") >= existing.get("timestamp", "")


def _get_quest_window_days() -> int:
    raw_value = os.getenv(
        "NUSYQ_SUGGEST_QUEST_WINDOW_DAYS",
        os.getenv("NUSYQ_NEXT_ACTION_QUEST_WINDOW_DAYS", "21"),
    )
    try:
        days = int(raw_value)
    except (TypeError, ValueError):
        return 21
    return max(1, days)


def _load_compacted_quest_state(hub_path: Path, limit: int = 5000) -> dict[str, dict[str, str]]:
    """Read quest_log.jsonl and keep only the latest state per quest identity."""
    quest_log = hub_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    if not quest_log.exists():
        return {}

    latest_by_key: dict[str, dict[str, str]] = {}
    try:
        lines = quest_log.read_text(encoding="utf-8", errors="replace").splitlines()
        for raw in lines[-limit:]:
            if not raw.strip():
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            quest_id, title, status, timestamp = _extract_quest_fields(entry)
            key = quest_id or _normalize_title(title)
            if not key:
                continue
            latest_by_key[key] = {
                "id": quest_id,
                "title": title,
                "status": status,
                "timestamp": timestamp,
            }
    except Exception:
        return {}

    # Collapse duplicate IDs that refer to the same quest title.
    collapsed_by_title: dict[str, dict[str, str]] = {}
    untitled: dict[str, dict[str, str]] = {}
    for key, quest in latest_by_key.items():
        title = quest.get("title", "").strip()
        if not title:
            untitled[key] = quest
            continue
        normalized = _normalize_title(title)
        existing = collapsed_by_title.get(normalized)
        if existing is None or _is_newer(quest, existing):
            collapsed_by_title[normalized] = quest

    merged: dict[str, dict[str, str]] = {}
    for normalized, quest in collapsed_by_title.items():
        merged[quest.get("id", "") or normalized] = quest
    merged.update(untitled)
    return merged


def collect_quest_signal(hub_path: Path | None, limit: int = 5000) -> dict[str, Any]:
    """Build recent-vs-stale quest signal for recommendation quality."""
    window_days = _get_quest_window_days()
    cutoff = datetime.now(UTC) - timedelta(days=window_days)
    payload: dict[str, Any] = {
        "available": False,
        "window_days": window_days,
        "deduped_count": 0,
        "active_recent_count": 0,
        "pending_recent_count": 0,
        "active_total_count": 0,
        "pending_total_count": 0,
        "actionable_recent_count": 0,
        "stale_backlog_count": 0,
        "active_sample": [],
        "pending_sample": [],
        "stale_sample": [],
    }

    if not hub_path:
        return payload

    compacted = _load_compacted_quest_state(hub_path, limit=limit)
    if not compacted:
        return payload

    payload["available"] = True
    payload["deduped_count"] = len(compacted)

    active_recent: list[dict[str, str]] = []
    pending_recent: list[dict[str, str]] = []
    stale_items: list[dict[str, str]] = []

    for quest in compacted.values():
        status = quest.get("status", "")
        title = quest.get("title", "")
        if status not in ACTIVE_QUEST_STATUSES or not title:
            continue

        parsed_ts = _parse_timestamp(quest.get("timestamp", ""))
        is_recent = parsed_ts is not None and parsed_ts >= cutoff
        if status == "pending":
            payload["pending_total_count"] += 1
            if is_recent:
                pending_recent.append(quest)
                payload["pending_recent_count"] += 1
            else:
                stale_items.append(quest)
        else:
            payload["active_total_count"] += 1
            if is_recent:
                active_recent.append(quest)
                payload["active_recent_count"] += 1
            else:
                stale_items.append(quest)

    active_recent.sort(key=lambda q: q.get("timestamp", ""), reverse=True)
    pending_recent.sort(key=lambda q: q.get("timestamp", ""), reverse=True)
    stale_items.sort(key=lambda q: q.get("timestamp", ""), reverse=True)

    payload["active_sample"] = [q.get("title", "") for q in active_recent[:3] if q.get("title")]
    payload["pending_sample"] = [q.get("title", "") for q in pending_recent[:3] if q.get("title")]
    payload["stale_sample"] = [q.get("title", "") for q in stale_items[:3] if q.get("title")]
    payload["stale_backlog_count"] = len(stale_items)
    payload["actionable_recent_count"] = int(payload["active_recent_count"]) + int(payload["pending_recent_count"])
    return payload


def _safe_read_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _format_cmd(cmd: Any) -> str:
    if not isinstance(cmd, list) or not cmd:
        return ""
    tokens = [str(token) for token in cmd if isinstance(token, (str, int, float))]
    if not tokens:
        return ""
    head = Path(tokens[0]).name.lower()
    if "python" in head:
        tokens[0] = "python"
    return " ".join(tokens)


def _load_system_complete_signal(hub_path: Path | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "available": False,
        "status": "missing",
        "overall_pass": None,
        "failed_count": 0,
        "skipped_count": 0,
        "blockers": [],
    }
    if not hub_path:
        return payload

    report_path = hub_path / "state" / "reports" / "system_complete_gate_latest.json"
    if not report_path.exists():
        return payload

    report = _safe_read_json(report_path)
    checks = report.get("checks", [])
    if not isinstance(checks, list):
        checks = []

    blockers: list[dict[str, Any]] = []
    failed_count = 0
    skipped_count = 0
    for raw in checks:
        if not isinstance(raw, dict):
            continue
        if raw.get("passed") is True:
            continue
        name = str(raw.get("name") or "unknown")
        skipped = bool(raw.get("skipped", False))
        status = "skipped" if skipped else "failed"
        if skipped:
            skipped_count += 1
        else:
            failed_count += 1
        blockers.append(
            {
                "name": name,
                "status": status,
                "reason": str(raw.get("reason") or ""),
                "cmd": _format_cmd(raw.get("cmd")),
                "stderr_tail": str(raw.get("stderr_tail") or ""),
            }
        )

    payload.update(
        {
            "available": True,
            "status": str(report.get("status") or "unknown"),
            "overall_pass": report.get("overall_pass"),
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "blockers": blockers,
            "report_file": str(report_path),
        }
    )
    return payload


def _load_error_signal(hub_path: Path | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "available": False,
        "errors": 0,
        "warnings": 0,
        "infos": 0,
        "ruff_count": 0,
        "import_like_count": 0,
        "f401_count": 0,
    }
    if not hub_path:
        return payload

    report_path = _select_latest_error_report(hub_path)
    if not report_path.exists():
        return payload

    report = _safe_read_json(report_path)
    ground = report.get("ground_truth", {})
    if not isinstance(ground, dict):
        ground = {}

    by_repo = report.get("by_repo", {})
    ruff_count = 0
    if isinstance(by_repo, dict):
        for repo_summary in by_repo.values():
            if not isinstance(repo_summary, dict):
                continue
            by_source = repo_summary.get("by_source", {})
            if isinstance(by_source, dict):
                ruff_count += int(by_source.get("ruff", 0) or 0)

    import_like_count = 0
    f401_count = 0
    details = report.get("diagnostic_details", [])
    if isinstance(details, list):
        for row in details:
            if not isinstance(row, dict):
                continue
            error_id = str(row.get("error_id") or "").lower()
            message = str(row.get("message") or "").lower()
            if "f401" in error_id:
                f401_count += 1
            if "import" in message or "module not found" in message or "cannot import" in message:
                import_like_count += 1

    payload.update(
        {
            "available": True,
            "errors": int(ground.get("errors", 0) or 0),
            "warnings": int(ground.get("warnings", 0) or 0),
            "infos": int(ground.get("infos", 0) or 0),
            "ruff_count": ruff_count,
            "import_like_count": import_like_count,
            "f401_count": f401_count,
            "report_file": str(report_path),
        }
    )
    return payload


def _select_latest_error_report(hub_path: Path) -> Path:
    """Select the freshest unified error report file for suggest signal quality.

    `unified_error_report_latest.json` may intentionally stay pinned to a canonical
    full-scan report while newer quick-scan reports are generated with timestamps.
    Suggestions should reflect freshest known diagnostics.
    """
    report_dir = hub_path / "docs" / "Reports" / "diagnostics"
    canonical = report_dir / "unified_error_report_latest.json"
    newest: Path | None = None
    newest_mtime = -1.0

    try:
        for candidate in report_dir.glob("unified_error_report_*.json"):
            try:
                mtime = candidate.stat().st_mtime
            except OSError:
                continue
            if mtime > newest_mtime:
                newest = candidate
                newest_mtime = mtime
    except OSError:
        return canonical

    return newest if newest is not None else canonical


def _load_next_action_signal(hub_path: Path | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "available": False,
        "total_actions": 0,
        "top_title": "",
        "top_type": "",
        "top_command": "",
    }
    if not hub_path:
        return payload

    queue_path = hub_path / "state" / "next_action_queue.json"
    if not queue_path.exists():
        return payload

    queue = _safe_read_json(queue_path)
    actions = queue.get("actions", [])
    if not isinstance(actions, list):
        actions = []
    top = actions[0] if actions and isinstance(actions[0], dict) else {}
    top_type = str(top.get("type") or "")
    top_context = top.get("context", {})
    context_command = ""
    if isinstance(top_context, dict):
        raw_command = top_context.get("recommended_command")
        if isinstance(raw_command, str):
            context_command = raw_command.strip()

    payload.update(
        {
            "available": True,
            "total_actions": int(queue.get("total_actions", len(actions)) or 0),
            "top_title": str(top.get("title") or ""),
            "top_type": top_type,
            "top_command": context_command or ACTION_TYPE_TO_COMMAND.get(top_type, ""),
            "queue_file": str(queue_path),
        }
    )
    return payload


def _build_quest_metrics(
    hub_path: Path | None,
    quest_signal: dict[str, Any],
    limit: int = 5000,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "available": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "window_days": int(quest_signal.get("window_days", 21) or 21),
        "deduped_count": int(quest_signal.get("deduped_count", 0) or 0),
        "active_total_count": int(quest_signal.get("active_total_count", 0) or 0),
        "pending_total_count": int(quest_signal.get("pending_total_count", 0) or 0),
        "active_recent_count": int(quest_signal.get("active_recent_count", 0) or 0),
        "pending_recent_count": int(quest_signal.get("pending_recent_count", 0) or 0),
        "actionable_recent_count": int(quest_signal.get("actionable_recent_count", 0) or 0),
        "stale_backlog_count": int(quest_signal.get("stale_backlog_count", 0) or 0),
        "status_breakdown": {},
        "last_updated": "",
        "sample_titles": {
            "active": list(quest_signal.get("active_sample", []) or [])[:3],
            "pending": list(quest_signal.get("pending_sample", []) or [])[:3],
            "stale": list(quest_signal.get("stale_sample", []) or [])[:3],
        },
    }

    if not hub_path:
        return payload

    compacted = _load_compacted_quest_state(hub_path, limit=limit)
    if not compacted:
        return payload

    status_breakdown: dict[str, int] = {}
    latest_timestamp: datetime | None = None
    for quest in compacted.values():
        status = str(quest.get("status") or "unknown").strip().lower() or "unknown"
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
        parsed_ts = _parse_timestamp(quest.get("timestamp", ""))
        if parsed_ts is not None and (latest_timestamp is None or parsed_ts > latest_timestamp):
            latest_timestamp = parsed_ts

    total_actionable = payload["active_total_count"] + payload["pending_total_count"]
    payload.update(
        {
            "available": True,
            "status_breakdown": status_breakdown,
            "last_updated": latest_timestamp.isoformat() if latest_timestamp else "",
            "stale_ratio": ((payload["stale_backlog_count"] / total_actionable) if total_actionable else 0.0),
        }
    )
    return payload


def _persist_quest_metrics(hub_path: Path | None, payload: dict[str, Any]) -> tuple[str, str]:
    if not hub_path:
        return "", ""
    report_dir = hub_path / "state" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    latest_path = report_dir / "quest_metrics.json"
    history_path = report_dir / "quest_metrics_history.jsonl"
    try:
        latest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        with history_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        return "", ""
    return str(latest_path), str(history_path)


def _persist_suggest_payload(hub_path: Path | None, payload: dict[str, Any]) -> tuple[str, str]:
    if not hub_path:
        return "", ""
    report_dir = hub_path / "state" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    latest_path = report_dir / "suggest_latest.json"
    history_path = report_dir / "suggest_history.jsonl"
    try:
        latest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        with history_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        return "", ""
    return str(latest_path), str(history_path)


def handle_work(paths, handle_ai_work_gate: Callable) -> int:
    """Execute next safe quest in queue."""
    print("🎯 Quest-driven execution mode")
    if not paths.nusyq_hub:
        print("[ERROR] NuSyQ-Hub path not found")
        emit_action_receipt(
            "work",
            exit_code=1,
            metadata={"error": "missing_hub_path"},
        )
        return 1

    # Gate work on AI system availability (can be bypassed with --force)
    import sys as sys_module

    force_mode = "--force" in sys_module.argv

    if not force_mode:
        gate_result = handle_ai_work_gate(paths)
        if gate_result != 0:
            print("\n💡 Tip: Use 'python start_nusyq.py work --force' to bypass work gate")
            emit_action_receipt(
                "work",
                exit_code=gate_result,
                metadata={"error": "work_gate_failed"},
            )
            return gate_result

    if str(paths.nusyq_hub) not in sys.path:
        sys.path.insert(0, str(paths.nusyq_hub))

    try:
        from src.quest import QuestExecutor

        executor = QuestExecutor(paths.nusyq_hub)
        result = executor.execute_next_safe_quest()

        if result["status"] == "executed":
            print(f"\n✅ Quest executed: {result['quest'][:60]}")
            print(f"   Action: {result['action']}")
            emit_action_receipt(
                "work",
                exit_code=0,
                metadata={"status": "executed", "quest": result.get("quest")},
            )
            return 0
        if result["status"] == "no_quests":
            print("\n📭 No active quests found")
            emit_action_receipt(
                "work",
                exit_code=0,
                metadata={"status": "no_quests"},
            )
            return 0
        if result["status"] == "no_safe_quests":
            print(f"\n⚠️ {result['message']}")
            emit_action_receipt(
                "work",
                exit_code=1,
                metadata={"status": "no_safe_quests", "message": result.get("message")},
            )
            return 1

        print(f"\n❌ {result.get('message', 'Unknown error')}")
        emit_action_receipt(
            "work",
            exit_code=1,
            metadata={"status": result.get("status"), "message": result.get("message")},
        )
        return 1

    except ImportError as exc:
        print(f"[ERROR] Failed to import quest executor: {exc}")
        emit_action_receipt(
            "work",
            exit_code=1,
            metadata={"error": str(exc)},
        )
        return 1
    except Exception as exc:
        print(f"[ERROR] Quest execution failed: {exc}")
        import traceback

        traceback.print_exc()
        emit_action_receipt(
            "work",
            exit_code=1,
            metadata={"error": str(exc)},
        )
        return 1


def handle_task(paths, args: list[str]) -> int:
    """Minimal task tracker: add/list/complete/stats for work items."""
    base = paths.nusyq_hub if paths.nusyq_hub else Path.cwd()
    tasks_file = base / "data" / "tasks.json"
    tasks_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        tasks = json.loads(tasks_file.read_text(encoding="utf-8")) if tasks_file.exists() else []
    except json.JSONDecodeError:
        tasks = []

    command = args[0] if args else "list"

    def _save() -> None:
        tasks_file.write_text(json.dumps(tasks, indent=2), encoding="utf-8")

    if command == "list":
        open_tasks = [t for t in tasks if t.get("status") == "open"]
        if not open_tasks:
            print("✅ No open work items")
            emit_action_receipt(
                "task",
                exit_code=0,
                metadata={"command": "list", "open_count": 0},
            )
            return 0
        print(f"📝 Open tasks ({len(open_tasks)}):")
        for task in open_tasks:
            print(f"  {task['id']}: {task['title']}")
        emit_action_receipt(
            "task",
            exit_code=0,
            metadata={"command": "list", "open_count": len(open_tasks)},
        )
        return 0

    if command == "add" and len(args) > 1:
        title = " ".join(args[1:])
        task_id = f"task_{len(tasks) + 1}"
        entry = {
            "id": task_id,
            "title": title,
            "status": "open",
            "created": datetime.now(UTC).isoformat(),
        }
        tasks.append(entry)
        _save()
        print(f"✅ Task added: {task_id} - {title}")
        emit_action_receipt(
            "task",
            exit_code=0,
            metadata={"command": "add", "task_id": task_id},
        )
        return 0

    if command == "done" and len(args) > 1:
        task_id = args[1]
        for task in tasks:
            if task.get("id") == task_id:
                task["status"] = "completed"
                task["completed"] = datetime.now(UTC).isoformat()
                _save()
                print(f"✅ Task completed: {task_id}")
                emit_action_receipt(
                    "task",
                    exit_code=0,
                    metadata={"command": "done", "task_id": task_id},
                )
                return 0
        print(f"❌ Task not found: {task_id}")
        emit_action_receipt(
            "task",
            exit_code=1,
            metadata={"command": "done", "task_id": task_id, "error": "not_found"},
        )
        return 1

    if command == "stats":
        total = len(tasks)
        open_count = sum(1 for task in tasks if task.get("status") == "open")
        completed_count = sum(1 for task in tasks if task.get("status") == "completed")
        print(f"📊 Task stats - total: {total}, open: {open_count}, completed: {completed_count}")
        emit_action_receipt(
            "task",
            exit_code=0,
            metadata={
                "command": "stats",
                "total": total,
                "open": open_count,
                "completed": completed_count,
            },
        )
        return 0

    print("Usage: task <add|list|done> [description|id]")
    emit_action_receipt(
        "task",
        exit_code=1,
        metadata={"error": "usage", "argv": args},
    )
    return 1


def handle_suggest(
    paths,
    git_snapshot: Callable,
    read_quest_log: Callable,
    run: Callable,
    json_mode: bool = False,
) -> int:
    """Provide specific, actionable suggestions based on system state."""
    suggestions = []
    blockers: list[dict[str, Any]] = []
    hub_path = paths.nusyq_hub if paths.nusyq_hub else None
    system_complete_signal = _load_system_complete_signal(hub_path)
    error_signal = _load_error_signal(hub_path)
    next_action_signal = _load_next_action_signal(hub_path)

    # 1. Check for blocking issues first
    try:
        from src.guild.guild_board import GuildBoard

        gb = GuildBoard()
        gb.post_message("system", "suggest_check")
    except Exception as e:
        suggestions.append(f"🚨 FIX BLOCKING: GuildBoard broken - {str(e)[:60]}")

    if system_complete_signal.get("available"):
        failed_count = int(system_complete_signal.get("failed_count", 0))
        skipped_count = int(system_complete_signal.get("skipped_count", 0))
        for blocker in system_complete_signal.get("blockers", [])[:3]:
            if not isinstance(blocker, dict):
                continue
            if blocker.get("status") != "failed":
                continue
            cmd = str(blocker.get("cmd") or "").strip()
            if cmd:
                suggestions.append(f"🚨 UNBLOCK {str(blocker.get('name', 'check')).upper()}: run `{cmd}`")
            else:
                suggestions.append(
                    f"🚨 UNBLOCK {str(blocker.get('name', 'check')).upper()}: investigate latest gate report"
                )
            blockers.append(
                {
                    "name": str(blocker.get("name") or ""),
                    "status": "failed",
                    "reason": str(blocker.get("reason") or ""),
                    "command": cmd,
                }
            )

        if failed_count > 0:
            suggestions.append(
                f"🧭 SYSTEM_COMPLETE has {failed_count} failing checks - use `python scripts/start_nusyq.py system_complete --async --budget-s=1200 --json`"
            )
        if skipped_count > 0:
            suggestions.append(
                f"⏱️ {skipped_count} heavy checks were skipped by budget - rerun gate with higher budget or poll status actions"
            )

    if next_action_signal.get("available"):
        top_title = str(next_action_signal.get("top_title", "")).strip()
        top_command = str(next_action_signal.get("top_command", "")).strip()
        failed_gate_names = {
            str(item.get("name") or "").strip().lower()
            for item in system_complete_signal.get("blockers", [])
            if isinstance(item, dict) and str(item.get("status") or "") == "failed"
        }
        top_title_lower = top_title.lower()
        gate_name = ""
        if top_title_lower.startswith("unblock gate failure:"):
            gate_name = top_title_lower.split(":", 1)[1].strip().split(" ", 1)[0]

        stale_gate_action = bool(gate_name and gate_name not in failed_gate_names)
        if stale_gate_action:
            suggestions.append(
                "🔄 REFRESH NEXT ACTIONS: run `python scripts/start_nusyq.py next_action_generate --json` "
                "(suppressed stale gate-failure action)"
            )
        elif top_title and top_command:
            suggestions.append(f"🎯 NEXT ACTION: {top_title} → `{top_command}`")
        elif top_title:
            suggestions.append(f"🎯 NEXT ACTION: {top_title}")
    else:
        suggestions.append("🎯 GENERATE QUEUE: run `python scripts/start_nusyq.py next_action_generate --json`")

    # 2. Check git state
    hub_snap = git_snapshot("NuSyQ-Hub", hub_path)
    if hub_snap.dirty == "DIRTY":
        status_result = run(["git", "status", "--short"], cwd=hub_path)
        if status_result[0] == 0:
            file_count = len(status_result[1].strip().split("\n"))
            if file_count > 15:
                suggestions.append(f"📦 CLEANUP: {file_count} uncommitted changes - run cleanup script")
            elif file_count > 0:
                suggestions.append(f"💾 COMMIT: {file_count} file(s) changed - run 'git status' to review")

    # 3. Diagnostics signals
    if error_signal.get("available"):
        errors = int(error_signal.get("errors", 0))
        warnings = int(error_signal.get("warnings", 0))
        infos = int(error_signal.get("infos", 0))
        if errors > 0 or warnings > 0:
            suggestions.append(
                f"🧪 ERROR SCAN: {errors} errors / {warnings} warnings detected - run `python scripts/start_nusyq.py error_report --quick --json`"
            )
        elif infos > 0:
            suggestions.append(
                f"📋 DIAGNOSTICS: {infos} informational findings available - prioritize by source and impact"
            )
        if int(error_signal.get("ruff_count", 0)) > 0:
            suggestions.append("⚡ LINT ANTI-HANG: run `python scripts/quality_orchestrator.py --skip-analysis`")
        if int(error_signal.get("f401_count", 0)) > 0:
            suggestions.append(
                f"🧹 F401 WAVE: {int(error_signal.get('f401_count', 0))} unused-import findings - burn down via quality orchestrator batches"
            )
        if int(error_signal.get("import_like_count", 0)) > 0:
            suggestions.append(
                "🔗 IMPORT HOTSPOTS: run `python scripts/start_nusyq.py doctor --quick --json` and target import/module errors first"
            )

    quest_signal = collect_quest_signal(paths.nusyq_hub if paths.nusyq_hub else None)
    quest_metrics = _build_quest_metrics(hub_path, quest_signal)
    quest_metrics_file, quest_metrics_history = _persist_quest_metrics(hub_path, quest_metrics)
    if quest_metrics_file:
        quest_metrics["report_file"] = quest_metrics_file
    if quest_metrics_history:
        quest_metrics["history_file"] = quest_metrics_history

    # 4. Check quest system with compaction/dedup + recency signal.
    if paths.nusyq_hub:
        recent_count = int(quest_signal.get("actionable_recent_count", 0))
        stale_count = int(quest_signal.get("stale_backlog_count", 0))
        window_days = int(quest_signal.get("window_days", 21))
        active_sample = quest_signal.get("active_sample", [])
        pending_sample = quest_signal.get("pending_sample", [])

        top_recent_title = ""
        if isinstance(active_sample, list) and active_sample:
            top_recent_title = str(active_sample[0])[:50]
        elif isinstance(pending_sample, list) and pending_sample:
            top_recent_title = str(pending_sample[0])[:50]

        if recent_count > 0 and top_recent_title:
            suggestions.append(f"🎯 CONTINUE QUEST: {top_recent_title}")

        if stale_count > 0:
            suggestions.append(f"🧹 TRIAGE QUEST BACKLOG: {stale_count} stale quests older than {window_days}d")

        if recent_count == 0 and stale_count == 0:
            # Fallback to tail-only parse for unusual log schema edge-cases.
            before_fallback = len(suggestions)
            quest = read_quest_log(paths.nusyq_hub)
            if quest.last_nonempty_line:
                try:
                    obj = json.loads(quest.last_nonempty_line)
                    if isinstance(obj, dict):
                        details = obj.get("details", {})
                        status = details.get("status", "")
                        if status in ["active", "pending"]:
                            title = details.get("title", "")[:50]
                            suggestions.append(f"🎯 CONTINUE QUEST: {title}")
                except Exception:
                    pass
            if len(suggestions) == before_fallback:
                suggestions.append("📭 No actionable quest signal detected")
        elif recent_count == 0:
            suggestions.append("📭 No actionable quest signal detected")

    # Optional active probes for deeper checks (off by default to keep suggest fast).
    if os.getenv("NUSYQ_SUGGEST_ACTIVE_PROBES", "0") == "1":
        test_result = run(["python", "-m", "pytest", "tests/", "-q", "--tb=no"], cwd=hub_path)
        if test_result[0] != 0 and "failed" in test_result[1].lower():
            suggestions.append("🧪 FIX TESTS: Run `pytest tests/ -v` to inspect failures")

    # 4. Deduplicate suggestion lines while preserving order.
    deduped_suggestions: list[str] = []
    seen: set[str] = set()
    for item in suggestions:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped_suggestions.append(normalized)
    suggestions = deduped_suggestions

    # 5. Default suggestions if none generated
    if not suggestions:
        suggestions.append("✨ System is healthy! Consider:")
        suggestions.append("  • Run tests: pytest tests/ -v")
        suggestions.append("  • Review recent commits: git log -5")
        suggestions.append("  • Check next quest: python scripts/start_nusyq.py guild_available")
        suggestions.append("  • Start new development: python scripts/start_nusyq.py task add")

    top_suggestions = suggestions[:5]
    payload = {
        "action": "suggest",
        "status": "ok",
        "generated_at": datetime.now().isoformat(),
        "suggestions": top_suggestions,
        "total_suggestions": len(suggestions),
        "quest_signal": quest_signal,
        "quest_metrics": quest_metrics,
        "blockers": blockers,
        "signals": {
            "system_complete": {
                "available": bool(system_complete_signal.get("available")),
                "status": str(system_complete_signal.get("status", "missing")),
                "failed_count": int(system_complete_signal.get("failed_count", 0)),
                "skipped_count": int(system_complete_signal.get("skipped_count", 0)),
            },
            "diagnostics": {
                "available": bool(error_signal.get("available")),
                "errors": int(error_signal.get("errors", 0)),
                "warnings": int(error_signal.get("warnings", 0)),
                "infos": int(error_signal.get("infos", 0)),
                "ruff_count": int(error_signal.get("ruff_count", 0)),
            },
            "next_action": {
                "available": bool(next_action_signal.get("available")),
                "total_actions": int(next_action_signal.get("total_actions", 0)),
                "top_title": str(next_action_signal.get("top_title", "")),
                "top_type": str(next_action_signal.get("top_type", "")),
            },
        },
    }
    report_file, history_file = _persist_suggest_payload(hub_path, payload)
    if report_file:
        payload["report_file"] = report_file
    if history_file:
        payload["history_file"] = history_file

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        emit_action_receipt(
            "suggest",
            exit_code=0,
            metadata={"total_suggestions": len(suggestions), "json_mode": True},
        )
        return 0

    # Output actionable suggestions
    print("💡 Actionable Suggestions (prioritized):")
    for i, suggestion in enumerate(top_suggestions, 1):
        print(f"  {i}. {suggestion}")
    recent_count = int(quest_signal.get("actionable_recent_count", 0))
    stale_count = int(quest_signal.get("stale_backlog_count", 0))
    window_days = int(quest_signal.get("window_days", 21))
    print(f"  Quest signal: recent={recent_count} stale={stale_count} (window={window_days}d)")
    emit_action_receipt(
        "suggest",
        exit_code=0,
        metadata={"total_suggestions": len(suggestions), "json_mode": False},
    )
    return 0
