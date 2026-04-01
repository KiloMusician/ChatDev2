"""Ingest the latest maze_summary JSON and create a refactoring workflow via the bridge."""

from __future__ import annotations

import json
from pathlib import Path

from src.integration.copilot_chatdev_bridge import CopilotChatDevBridge
from src.tools.log_indexer import latest_maze_summaries


def ingest_latest_and_create_workflow(workspace_root: Path = Path()) -> str | None:
    latest = latest_maze_summaries(workspace_root / "logs", limit=1)
    if not latest:
        return None
    summary_path = latest[0]
    with summary_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    list(data.get("files", {}).keys())
    bridge = CopilotChatDevBridge(workspace_root=str(workspace_root))
    findings = {Path(p): v for p, v in data.get("files", {}).items()}
    workflow = bridge.create_workflow_from_treasures(findings)
    return workflow.get("id")


if __name__ == "__main__":
    ingest_latest_and_create_workflow()
