#!/usr/bin/env python3
"""Validate placeholders (plugin registry, Copilot prompts, health assessor wiring).

Uses the existing registry, quest log, and diagnostics to publish traceable reports and close the remaining placeholders.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.diagnostics.system_health_assessor import SystemHealthAssessment

REGISTRY_PATH = Path("data/plugin_registry.json")
QUEST_LOG_PATH = Path("src/Rosetta_Quest_System/quest_log.jsonl")
GUILD_EVENTS_PATH = Path("state/guild/guild_events.jsonl")
REPORTS_DIR = Path("reports")


def ensure_registry() -> list[dict[str, Any]]:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError("Plugin registry data missing. Restore data/plugin_registry.json first.")
    with REGISTRY_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def refresh_registry(registry: list[dict[str, Any]]) -> None:
    now_iso = datetime.utcnow().isoformat()
    for plugin in registry:
        entry = Path(plugin.get("entrypoint", ""))
        available = entry.exists()
        plugin["available"] = available
        plugin["status"] = "wired" if available else "missing"
        plugin["last_checked"] = now_iso
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(registry, handle, indent=2, ensure_ascii=False)


def summarize_registry(registry: list[dict[str, Any]]) -> str:
    lines: list[str] = [
        "# Plugin Registry Report",
        "",
        f"Generated: {datetime.utcnow().isoformat()}",
        "",
    ]
    for plugin in registry:
        status = plugin.get("status", "unknown")
        lines.append(f"## {plugin['name']} ({status})")
        lines.append(f"- Description: {plugin.get('description')}")
        lines.append(f"- Entrypoint: `{plugin.get('entrypoint')}`")
        lines.append(f"- Command: `{plugin.get('command')}`")
        tags = plugin.get("tags", [])
        lines.append(f"- Tags: {', '.join(tags) if tags else '(none)'}")
        lines.append("")
    return "\n".join(lines)


def write_report(filename: str, content: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path


def build_copilot_prompts(registry: list[dict[str, Any]]) -> str:
    lines: list[str] = [
        "# Copilot Prompt Matrix",
        "",
        "Use these prompts when guiding Copilot/LLM assistants:",
        "",
    ]
    for plugin in registry:
        status = plugin.get("status", "unknown")
        cmd = plugin.get("command", "<command missing>")
        lines.append(f"## {plugin['name']} ({status})")
        lines.append(f"Prompt: `Execute {cmd}` to leverage the {plugin['name']} plugin")
        lines.append(f"Context: {plugin.get('description')}")
        lines.append("")
    return "\n".join(lines)


def run_health_assessor() -> tuple[str, Path]:
    assessor = SystemHealthAssessment()
    collected = assessor.collect()
    if not collected:
        message = (
            "No quick_system_analysis JSON artifacts were found. ``scripts/quick_system_analyzer.py`` "
            "must be run to gather diagnostics before re-running this playbook."
        )
        path = write_report("health_assessor_report.md", message)
        return message, path

    report_text = assessor.render_report(collected["health_metrics"], collected["roadmap"])
    path = write_report("health_assessor_report.md", report_text)
    return report_text, path


def append_quest_record() -> None:
    timestamp = datetime.utcnow().isoformat()
    quest_id = f"placeholder_fix_{int(datetime.utcnow().timestamp())}"
    details = {
        "id": quest_id,
        "title": "Close placeholders: plugin registry, Copilot prompts, health assessor",
        "description": (
            "Generated registry + Copilot prompt reports, posted a health assessor summary, and logged the wiring."
        ),
        "questline": "System Maintenance",
        "status": "completed",
        "dependencies": [],
        "tags": ["placeholder", "plugin_registry", "copilot", "health"],
        "proof": [
            "reports/plugin_registry_report.md",
            "reports/copilot_prompt_matrix.md",
            "reports/health_assessor_report.md",
        ],
    }
    entry = {"timestamp": timestamp, "event": "add_quest", "details": details}
    QUEST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with QUEST_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def append_guild_event(report_path: Path, health_path: Path) -> None:
    GUILD_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "placeholder_playbook",
        "data": {
            "message": "Plugin registry, Copilot prompts, and health assessor wiring refreshed.",
            "report": str(report_path),
            "health_report": str(health_path),
        },
    }
    with GUILD_EVENTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        registry = ensure_registry()
    except FileNotFoundError as exc:
        print(exc)
        return 1

    refresh_registry(registry)
    report_content = summarize_registry(registry)
    report_path = write_report("plugin_registry_report.md", report_content)

    prompts = build_copilot_prompts(registry)
    prompt_path = write_report("copilot_prompt_matrix.md", prompts)

    _health_summary, health_path = run_health_assessor()

    append_quest_record()
    append_guild_event(report_path, health_path)

    placeholder_lines = [
        "Placeholder playbook executed successfully.",
        "",
        f"- Plugin registry report: {report_path}",
        f"- Copilot prompt matrix: {prompt_path}",
        f"- Health assessor report: {health_path}",
    ]
    write_report("placeholder_playbook_report.md", "\n".join(placeholder_lines))

    print("Placeholder playbook complete; see reports/ for trace files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
