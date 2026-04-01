#!/usr/bin/env python3
"""DevMentor Workspace Bridge
══════════════════════════════════════════════════════════════════════════════
Scans the parent filesystem for known adjacent repos (NuSyQ-Hub, SimulatedVerse,
ChatDev, prime_anchor, rimworld, skyclaw, openclaw, serena, etc.) and builds
a manifest of detected integrations.

The manifest is:
  - Saved to state/workspace_manifest.json (consumed by /api/workspace/manifest)
  - Loaded into the game VFS at /opt/workspace/<repo>
  - Displayed by the `workspace` in-game command

Run:
  python scripts/workspace_bridge.py
  python scripts/workspace_bridge.py --watch   # re-scan every 60s
  python scripts/workspace_bridge.py --json    # print manifest to stdout
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# ── Known repos and their integration profiles ────────────────────────────────
KNOWN_REPOS: dict[str, dict] = {
    "NuSyQ-Hub": {
        "description": "NuSyQ coordination hub — agent manifest publisher",
        "role": "orchestrator",
        "capabilities": ["agent_manifest", "chronicle", "event_bus"],
        "entry_point": "python nusyq/serve.py",
        "td_integration": "native",  # NuSyQ bridge already built in
    },
    "SimulatedVerse": {
        "description": "Simulated reality environment for agent training",
        "role": "simulation_substrate",
        "capabilities": ["world_sim", "agent_env", "scenario_runner"],
        "entry_point": "python main.py",
        "td_integration": "workspace_mount",
    },
    "ChatDev": {
        "description": "LLM-driven software development team simulation",
        "role": "agent_team",
        "capabilities": ["code_generation", "agent_roles", "project_planning"],
        "entry_point": "python run.py",
        "td_integration": "api_bridge",
    },
    "prime_anchor": {
        "description": "Prime Anchor — foundational agent infrastructure",
        "role": "infrastructure",
        "capabilities": ["agent_bootstrap", "state_sync", "auth"],
        "entry_point": "python anchor.py",
        "td_integration": "state_sync",
    },
    "rimworld": {
        "description": "RimWorld-inspired colony simulation",
        "role": "game_sibling",
        "capabilities": ["colony_sim", "npc_ai", "event_system"],
        "entry_point": "python main.py",
        "td_integration": "cross_save",
    },
    "skyclaw": {
        "description": "Skyclaw — aerial tactical game engine",
        "role": "game_sibling",
        "capabilities": ["aerial_combat", "territory_control"],
        "entry_point": "python skyclaw.py",
        "td_integration": "agent_import",
    },
    "openclaw": {
        "description": "OpenClaw — open-source game mechanics platform",
        "role": "game_engine",
        "capabilities": ["physics", "rendering", "input_handling"],
        "entry_point": None,
        "td_integration": "passive",
    },
    "serena": {
        "description": "Serena convergence layer — ΨΞΦΩ attractor",
        "role": "focal_agent",
        "capabilities": ["agent_orchestration", "trust_matrix", "narrative_engine"],
        "entry_point": "python serena.py serve",
        "td_integration": "native",
    },
    "metaclaw": {
        "description": "MetaClaw — meta-game layer and progression system",
        "role": "meta_progression",
        "capabilities": ["cross_game_xp", "achievement_sync", "player_identity"],
        "entry_point": None,
        "td_integration": "xp_sync",
    },
    "Dev-Mentor": {
        "description": "DevMentor — this repo (self-reference)",
        "role": "self",
        "capabilities": ["terminal_depths", "agent_api", "learning_engine"],
        "entry_point": "python -m cli.devmentor serve",
        "td_integration": "self",
    },
    ".cursor": {
        "description": "Cursor AI IDE configuration",
        "role": "ide_config",
        "capabilities": ["ai_completion", "code_generation"],
        "entry_point": None,
        "td_integration": "ide_surface",
    },
    ".copilot": {
        "description": "GitHub Copilot configuration",
        "role": "ide_config",
        "capabilities": ["ai_completion", "agent_mode"],
        "entry_point": None,
        "td_integration": "ide_surface",
    },
    "obsidian": {
        "description": "Obsidian knowledge base / note system",
        "role": "knowledge_surface",
        "capabilities": ["note_taking", "knowledge_graph", "plugin_system"],
        "entry_point": None,
        "td_integration": "lore_export",
    },
}


# Search paths (parent dirs, sibling dirs, common workspace locations)
def _search_paths(start: Path) -> list[Path]:
    paths = []
    # Parent directory siblings
    parent = start.parent
    if parent != start:
        paths.append(parent)
    # Grandparent (VS Code workspace often has projects side by side)
    grandparent = parent.parent
    if grandparent != parent:
        paths.append(grandparent)
    # Common workspace roots
    for env_key in ("VSCODE_WORKSPACE", "WORKSPACE_ROOT", "GITHUB_WORKSPACE", "HOME"):
        val = os.environ.get(env_key)
        if val:
            paths.append(Path(val))
    return paths


def scan(repo_root: Path | None = None) -> dict:
    """Scan for adjacent repos and return the manifest."""
    if repo_root is None:
        repo_root = Path(__file__).parent.parent

    found: list[dict] = []
    not_found: list[str] = []
    search_dirs = _search_paths(repo_root)

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for repo_name, profile in KNOWN_REPOS.items():
            if profile["role"] == "self":
                continue
            candidate = search_dir / repo_name
            if candidate.exists() and candidate.is_dir():
                # Check if it looks like a real repo
                is_git = (candidate / ".git").exists()
                has_python = any(candidate.glob("*.py"))
                has_js = any(candidate.glob("*.js")) or any(candidate.glob("*.ts"))
                has_readme = (candidate / "README.md").exists()

                found.append(
                    {
                        "name": repo_name,
                        "path": str(candidate.resolve()),
                        "relative_path": str(candidate.relative_to(search_dir)),
                        "description": profile["description"],
                        "role": profile["role"],
                        "capabilities": profile["capabilities"],
                        "entry_point": profile["entry_point"],
                        "td_integration": profile["td_integration"],
                        "is_git_repo": is_git,
                        "has_python": has_python,
                        "has_js": has_js,
                        "has_readme": has_readme,
                        "detected_at": datetime.now(UTC).isoformat(),
                    }
                )
                break  # Don't double-count

    # Collect not-found
    found_names = {r["name"] for r in found}
    not_found = [
        n
        for n in KNOWN_REPOS
        if n not in found_names and KNOWN_REPOS[n]["role"] != "self"
    ]

    # Also scan for unknown repos (any sibling dir with a .git folder)
    unknown = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        try:
            for item in search_dir.iterdir():
                if (
                    item.is_dir()
                    and (item / ".git").exists()
                    and item.name not in KNOWN_REPOS
                    and item.resolve() != repo_root.resolve()
                ):
                    unknown.append(
                        {
                            "name": item.name,
                            "path": str(item.resolve()),
                            "role": "unknown",
                            "td_integration": "none",
                            "detected_at": datetime.now(UTC).isoformat(),
                        }
                    )
        except PermissionError:
            pass

    manifest = {
        "scan_time": datetime.now(UTC).isoformat(),
        "repo_root": str(repo_root.resolve()),
        "found": found,
        "not_found": not_found,
        "unknown_repos": unknown[:10],  # cap to avoid noise
        "integration_summary": {
            "native": [r["name"] for r in found if r.get("td_integration") == "native"],
            "api_bridge": [
                r["name"] for r in found if r.get("td_integration") == "api_bridge"
            ],
            "workspace_mount": [
                r["name"] for r in found if r.get("td_integration") == "workspace_mount"
            ],
            "ide_surface": [
                r["name"] for r in found if r.get("td_integration") == "ide_surface"
            ],
            "passive": [
                r["name"] for r in found if r.get("td_integration") == "passive"
            ],
        },
    }
    return manifest


def save_manifest(manifest: dict, repo_root: Path | None = None):
    if repo_root is None:
        repo_root = Path(__file__).parent.parent
    state_dir = repo_root / "state"
    state_dir.mkdir(exist_ok=True)
    manifest_path = state_dir / "workspace_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path


def main():
    parser = argparse.ArgumentParser(description="DevMentor Workspace Bridge")
    parser.add_argument("--json", action="store_true", help="Print manifest to stdout")
    parser.add_argument("--watch", action="store_true", help="Re-scan every 60s")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent

    def run_scan():
        manifest = scan(repo_root)
        path = save_manifest(manifest, repo_root)
        found_count = len(manifest["found"])
        unknown_count = len(manifest["unknown_repos"])
        print(
            f"[workspace-bridge] Scan complete: {found_count} known repos, {unknown_count} unknown repos"
        )
        for r in manifest["found"]:
            print(f"  ✓ {r['name']:<20} [{r['td_integration']}]  {r['path']}")
        if args.json:
            print(json.dumps(manifest, indent=2))
        return manifest

    if args.watch:
        print("[workspace-bridge] Watch mode — scanning every 60s (Ctrl+C to stop)")
        while True:
            run_scan()
            time.sleep(60)
    else:
        run_scan()


if __name__ == "__main__":
    main()
