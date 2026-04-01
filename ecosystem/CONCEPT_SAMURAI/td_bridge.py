"""
td_bridge.py — drop this in any repo root for zero-setup TerminalDepths access.

Usage (from any repo):
    from td_bridge import td_command, td_ping, td_manifest, td_task, hub

    td_ping()
    td_manifest()
    td_command("boot")
    td_command("repo list")
    td_command("nusyq status")
    td_command("agents")
    td_task("scan_repo", repo="nusyq_hub")

    # Full hub client (orchestrator API)
    print(hub.status())
    print(hub.agents())
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# ── Auto-resolve workspace root ─────────────────────────────────────────────
# This file may live at: workspace/ecosystem/<repo>/td_bridge.py
#                     or: workspace/ecosystem/td_bridge.py
# Either way we need workspace/ in sys.path so `ecosystem.` imports work.

_THIS_FILE = Path(__file__).resolve()
_THIS_DIR  = _THIS_FILE.parent

# Walk up until we find the directory containing the 'ecosystem' folder
def _find_workspace(start: Path) -> Path:
    p = start
    for _ in range(6):
        if (p / "ecosystem").is_dir():
            return p
        p = p.parent
    return start

_WORKSPACE = _find_workspace(_THIS_DIR)
if str(_WORKSPACE) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE))

# ── Import nusyq_surface via workspace path ────────────────────────────────
from ecosystem.nusyq_surface.bridge_client import BridgeClient
from ecosystem.nusyq_surface.hub_client import HubClient
from ecosystem.nusyq_surface.registry import list_repos, get_repo

# Singletons
_bridge = BridgeClient()
hub = HubClient()


def td_ping() -> dict:
    return _bridge.ping()


def td_manifest() -> dict:
    return _bridge.manifest()


def td_command(cmd: str, context: dict = None) -> dict:
    return _bridge.command(cmd, context)


def td_task(action: str, repo: str = "ecosystem", payload: dict = None, priority: int = 5) -> str:
    r = _bridge.task_add(action, repo=repo, payload=payload, priority=priority)
    return r.get("task_id", "")


def td_repo_list() -> list:
    return list_repos()


def td_repo_status(name: str = None) -> dict:
    return _bridge.repo_status(name)


def td_dispatch(agent: str, task: str, payload: dict = None) -> dict:
    return _bridge.agent_dispatch(agent, task, payload)


def td_session(session_id: str = None) -> dict:
    return _bridge.session_open(session_id)


if __name__ == "__main__":
    import json
    print("=== td_bridge smoke test ===")
    print("workspace:", str(_WORKSPACE))
    print("ping:", td_ping())
    print("repos:", [r["id"] for r in td_repo_list()])
    print("boot:", json.dumps(td_command("boot"), indent=2))
    print("nusyq status:", json.dumps(td_command("nusyq status"), indent=2))
