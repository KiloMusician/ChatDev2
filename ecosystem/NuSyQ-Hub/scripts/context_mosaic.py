"""Context Mosaic Helper - fuses diagnostics, guild/quest state, and fallbacks."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = REPO_ROOT / "state" / "reports" / "context_mosaic.json"
REPORT_MD = REPO_ROOT / "state" / "reports" / "context_mosaic.md"


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _tail_json_lines(path: Path, limit: int = 10) -> list[dict]:
    if not path.exists():
        return []
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    entries = []
    for raw in lines[-limit:]:
        try:
            entries.append(json.loads(raw))
        except Exception:
            continue
    return entries


def _simulate_services() -> dict:
    simverse_path = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
    return {
        "github_cli": bool(shutil.which("gh")),
        "simulatedverse_fs": simverse_path.exists(),
        "simulatedverse_http": False,
    }


def _summarize_guild() -> dict[str, dict | int | str]:
    path = REPO_ROOT / "state" / "guild" / "guild_board.json"
    data = _read_json(path)
    return {
        "total_agents": len(data.get("agents", {})),
        "active_quests": data.get("quest_summary", {}).get("in_progress", 0),
        "pending_quests": data.get("quest_summary", {}).get("pending", 0),
    }


def _summarize_errors() -> dict[str, int]:
    path = REPO_ROOT / "docs" / "Reports" / "diagnostics" / "unified_error_report_latest.json"
    data = _read_json(path)
    by_severity = data.get("by_severity", {})
    return {
        "errors": by_severity.get("errors", 0),
        "warnings": by_severity.get("warnings", 0),
        "infos": by_severity.get("infos_hints", 0),
        "total": data.get("total_diagnostics", 0),
    }


def _summarize_quests() -> dict:
    path = REPO_ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    entries = _tail_json_lines(path, limit=8)
    status_counts: dict[str, int] = {}
    for entry in entries:
        status = entry.get("details", {}).get("status") or entry.get("status")
        if status:
            status_counts[status] = status_counts.get(status, 0) + 1
    return {"recent": entries, "status_counts": status_counts}


def _summarize_tasks() -> dict:
    path = REPO_ROOT / "state" / "tasks.jsonl"
    entries = _tail_json_lines(path, limit=15)
    fallback = [e for e in entries if e.get("source") == "todo_to_issue"]
    return {"recent": entries, "fallback_tasks": len(fallback)}


def _summarize_zeta() -> dict:
    path = REPO_ROOT / "config" / "ZETA_PROGRESS_TRACKER.json"
    data = _read_json(path)
    current = data.get("current_progress", {})
    return {
        "phase": list(data.get("phases", {}).keys()),
        "completion": current.get("completion_percentage"),
    }


def build_mosaic() -> dict:
    mosaic = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": _simulate_services(),
        "guild": _summarize_guild(),
        "quests": _summarize_quests(),
        "tasks": _summarize_tasks(),
        "errors": _summarize_errors(),
        "zeta": _summarize_zeta(),
    }
    return mosaic


def write_reports(mosaic: dict) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(mosaic, indent=2), encoding="utf-8")
    text_lines = [
        "# Context Mosaic",
        f"**Generated**: {mosaic['timestamp']}",
        "",
        "## Services",
        *[f"- {name}: {status}" for name, status in mosaic["services"].items()],
        "",
        "## Guild Summary",
        f"- Agents: {mosaic['guild']['total_agents']}",
        f"- Pending quests: {mosaic['guild']['pending_quests']}",
        f"- Active quests: {mosaic['guild']['active_quests']}",
        "",
        "## Latest Quests",
        *[
            f"- {entry.get('details', {}).get('title', entry.get('description', ''))} ({entry.get('status')})"
            for entry in mosaic["quests"]["recent"]
        ],
        "",
        "## Fallback Tasks",
        f"- Fallback TODOs recorded: {mosaic['tasks']['fallback_tasks']}",
        "",
        "## Diagnostics",
        f"- Errors: {mosaic['errors']['errors']} | Warnings: {mosaic['errors']['warnings']} | Infos: {mosaic['errors']['infos']}",
    ]
    REPORT_MD.write_text("\n".join(text_lines), encoding="utf-8")


def main() -> int:
    mosaic = build_mosaic()
    write_reports(mosaic)
    print("Context mosaic generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
