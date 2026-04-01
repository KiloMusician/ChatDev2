"""
Bridge inventory for IDE agents, local tools, and claw-family surfaces.

This is the shared source of truth for diagnostics, API manifests, and
workspace-level bridge awareness.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "state" / "bridge_inventory.json"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _windows_home() -> Path:
    candidates = [
        Path("/mnt/c/Users/keath"),
        Path.home(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("/mnt/c/Users/keath")


def _vscode_extensions_root() -> Path:
    return _windows_home() / ".vscode" / "extensions"


def _pick_latest(pattern: str) -> Path | None:
    root = _vscode_extensions_root()
    if not root.exists():
        return None
    matches = sorted(root.glob(pattern))
    return matches[-1] if matches else None


def _entry(
    *,
    bridge_id: str,
    name: str,
    family: str,
    tier: str,
    surface_type: str,
    integration_mode: str,
    installed: bool,
    path: Path | None = None,
    command_surface: str | None = None,
    local_capability: str = "",
    remote_dependency: str = "",
    recommended_role: str = "",
    autonomous_default: bool = False,
    trust_notes: str = "",
    proven_live: bool = False,
) -> dict[str, Any]:
    return {
        "id": bridge_id,
        "name": name,
        "family": family,
        "tier": tier,
        "type": surface_type,
        "integration_mode": integration_mode,
        "installed": installed,
        "proven_live": proven_live,
        "path": str(path.resolve()) if path and path.exists() else (str(path) if path else ""),
        "command_surface": command_surface or "",
        "local_capability": local_capability,
        "remote_dependency": remote_dependency,
        "recommended_role": recommended_role,
        "autonomous_default": autonomous_default,
        "trust_notes": trust_notes,
    }


def build_bridge_inventory() -> dict[str, Any]:
    codex = _pick_latest("openai.chatgpt-*")
    claude = _pick_latest("anthropic.claude-code-*")
    copilot = _pick_latest("github.copilot-chat-*")
    continue_ext = _pick_latest("continue.continue-*")
    kilo = _pick_latest("kilocode.kilo-code-*")
    soulclaw = _pick_latest("clawsouls.soulclaw-vscode-*")
    openclaw_ext = _pick_latest("openknot.openclaw-extension-*")
    openclaw_luna = _pick_latest("lunaticlegacy.openclaw-vscode-luna-*")
    terminal_keeper_ext = _pick_latest("nguyenngoclong.terminal-keeper-*")

    serena_agent = ROOT / "agents" / "serena" / "serena_agent.py"
    skyclaw_scanner = ROOT / "scripts" / "skyclaw_scanner.py"
    terminal_keeper_mod = ROOT / "mods" / "TerminalKeeper"

    bridges = [
        _entry(
            bridge_id="serena",
            name="Serena",
            family="core",
            tier="first_class",
            surface_type="native_service",
            integration_mode="workspace+api+cli",
            installed=serena_agent.exists(),
            path=serena_agent,
            command_surface="python scripts/serena_cli.py",
            local_capability="Local-first semantic code search, drift detection, YAML-aware explain.",
            remote_dependency="Optional Redis/HTTP surfaces; core analysis works locally.",
            recommended_role="Primary local code intelligence and repo memory bridge.",
            autonomous_default=True,
            trust_notes="Repo-native and local-first.",
            proven_live=serena_agent.exists(),
        ),
        _entry(
            bridge_id="codex_vscode",
            name="Codex for VS Code",
            family="ide_agent",
            tier="first_class",
            surface_type="webview_agent",
            integration_mode="vscode_extension+cli",
            installed=codex is not None,
            path=codex,
            command_surface=str((codex / "bin" / "linux-x86_64" / "codex") if codex else ""),
            local_capability="Native VS Code agent surface with shipped Codex binary.",
            remote_dependency="OpenAI service for model execution.",
            recommended_role="Primary IDE-native agent bridge.",
            autonomous_default=True,
            trust_notes="Cloud-backed coding agent; treat as explicit outbound AI surface.",
            proven_live=codex is not None,
        ),
        _entry(
            bridge_id="claude_vscode",
            name="Claude Code for VS Code",
            family="ide_agent",
            tier="first_class",
            surface_type="webview_agent",
            integration_mode="vscode_extension+native_binary",
            installed=claude is not None,
            path=claude,
            command_surface=str((claude / "resources" / "native-binary" / "claude.exe") if claude else ""),
            local_capability="VS Code agent surface with native Claude launcher.",
            remote_dependency="Anthropic service for model execution.",
            recommended_role="Primary IDE-native reasoning and coding bridge.",
            autonomous_default=True,
            trust_notes="Cloud-backed coding agent; respect explicit context boundaries.",
            proven_live=claude is not None,
        ),
        _entry(
            bridge_id="copilot_chat",
            name="GitHub Copilot Chat",
            family="ide_agent",
            tier="first_class",
            surface_type="webview_agent",
            integration_mode="vscode_builtin_extension",
            installed=copilot is not None,
            path=copilot,
            command_surface="VS Code integrated Copilot Chat tools",
            local_capability="Editor-integrated codebase search, read/edit tools, subagents.",
            remote_dependency="GitHub Copilot service.",
            recommended_role="Primary editor-native bridge inside VS Code.",
            autonomous_default=True,
            trust_notes="First-party editor-integrated cloud AI surface.",
            proven_live=copilot is not None,
        ),
        _entry(
            bridge_id="continue",
            name="Continue",
            family="ide_agent",
            tier="second_wave",
            surface_type="webview_agent",
            integration_mode="vscode_extension+workspace",
            installed=continue_ext is not None,
            path=continue_ext,
            command_surface=str(ROOT / ".vscode" / "continue" / "config.json"),
            local_capability="Configurable local-model and remote-model IDE agent.",
            remote_dependency="Optional; can run via local Ollama/LM Studio or remote providers.",
            recommended_role="Second-wave customizable local-model bridge.",
            autonomous_default=False,
            trust_notes="Useful when intentionally configured; telemetry is on by default upstream.",
            proven_live=continue_ext is not None,
        ),
        _entry(
            bridge_id="kilo_code",
            name="Kilo Code",
            family="ide_agent",
            tier="second_wave",
            surface_type="webview_agent",
            integration_mode="vscode_extension",
            installed=kilo is not None,
            path=kilo,
            command_surface="VS Code Kilo Code sidebar",
            local_capability="Autonomous IDE agent and prompt/task surface.",
            remote_dependency="Provider-dependent; may use remote and local backends.",
            recommended_role="Second-wave experimental IDE agent surface.",
            autonomous_default=False,
            trust_notes="Installed but not yet proven in your current workflow.",
            proven_live=kilo is not None,
        ),
        _entry(
            bridge_id="skyclaw",
            name="SkyClaw",
            family="claw",
            tier="first_party",
            surface_type="native_service",
            integration_mode="script+service",
            installed=skyclaw_scanner.exists(),
            path=skyclaw_scanner,
            command_surface="python scripts/skyclaw_scanner.py --daemon",
            local_capability="Local-first filesystem, process, and alert scanning.",
            remote_dependency="Optional Redis event bus.",
            recommended_role="Native scanner and anomaly detection surface.",
            autonomous_default=True,
            trust_notes="Repo-native and local-first.",
            proven_live=skyclaw_scanner.exists(),
        ),
        _entry(
            bridge_id="terminal_keeper_mod",
            name="Terminal Keeper",
            family="claw",
            tier="first_party",
            surface_type="workspace_mod",
            integration_mode="workspace+rimworld_mod",
            installed=terminal_keeper_mod.exists(),
            path=terminal_keeper_mod,
            command_surface="mods/TerminalKeeper/",
            local_capability="RimWorld bridge and mod-first terminal/game integration.",
            remote_dependency="Calls Terminal Depths HTTP bridge when active.",
            recommended_role="Game/mod bridge rather than autonomous coding agent.",
            autonomous_default=False,
            trust_notes="First-party mod surface; game-first, not AI-first.",
            proven_live=terminal_keeper_mod.exists(),
        ),
        _entry(
            bridge_id="soulclaw_vscode",
            name="SoulClaw",
            family="claw",
            tier="third_party_opt_in",
            surface_type="webview_agent",
            integration_mode="vscode_extension+workspace_sync",
            installed=soulclaw is not None,
            path=soulclaw,
            command_surface="SoulClaw sidebar / swarm memory / checkpoints",
            local_capability="Persona, swarm-memory, and workspace sync workflows.",
            remote_dependency="Outbound-capable; supports remote publish and messaging flows.",
            recommended_role="Visible and auditable, but never silently promoted into autonomous flows.",
            autonomous_default=False,
            trust_notes="Third-party and outbound-capable.",
            proven_live=soulclaw is not None,
        ),
        _entry(
            bridge_id="openclaw_extension",
            name="OpenClaw Extension",
            family="claw",
            tier="third_party_opt_in",
            surface_type="cli_bridge",
            integration_mode="vscode_extension+external_cli",
            installed=openclaw_ext is not None,
            path=openclaw_ext,
            command_surface="openclaw status / openclaw chat",
            local_capability="Thin status/chat connector around an external OpenClaw CLI.",
            remote_dependency="Depends on whatever the external CLI is configured to use.",
            recommended_role="CLI bridge candidate if an OpenClaw runtime is intentionally adopted.",
            autonomous_default=False,
            trust_notes="Thin bridge, but not part of your native stack.",
            proven_live=openclaw_ext is not None,
        ),
        _entry(
            bridge_id="openclaw_luna",
            name="OpenClaw Luna",
            family="claw",
            tier="third_party_opt_in",
            surface_type="webview_agent",
            integration_mode="vscode_extension",
            installed=openclaw_luna is not None,
            path=openclaw_luna,
            command_surface="OpenClaw sidebar / tasks / clusters",
            local_capability="Fuller third-party agent workbench with task and cluster UX.",
            remote_dependency="Provider-dependent; broader agent/workbench surface.",
            recommended_role="Exploratory third-party workbench, not default infrastructure.",
            autonomous_default=False,
            trust_notes="Webview-agent workbench, not a thin local bridge.",
            proven_live=openclaw_luna is not None,
        ),
        _entry(
            bridge_id="openclaw_manifest",
            name="OpenClaw (manifest-level)",
            family="claw",
            tier="conceptual",
            surface_type="manifest_only",
            integration_mode="workspace_manifest",
            installed=True,
            path=ROOT / "scripts" / "workspace_bridge.py",
            command_surface="workspace manifest only",
            local_capability="Known in Dev-Mentor manifests as a sibling/game-engine concept.",
            remote_dependency="None currently.",
            recommended_role="Concept tracked in manifests until a real runtime is proven.",
            autonomous_default=False,
            trust_notes="Manifest-only; not a proven live bridge.",
            proven_live=False,
        ),
        _entry(
            bridge_id="metaclaw_manifest",
            name="MetaClaw",
            family="claw",
            tier="conceptual",
            surface_type="manifest_only",
            integration_mode="workspace_manifest",
            installed=True,
            path=ROOT / "scripts" / "workspace_bridge.py",
            command_surface="workspace manifest only",
            local_capability="Meta-progression concept tracked in workspace manifests.",
            remote_dependency="None currently.",
            recommended_role="Concept tracked in manifests until a real runtime is proven.",
            autonomous_default=False,
            trust_notes="Manifest-only; not a proven live bridge.",
            proven_live=False,
        ),
        _entry(
            bridge_id="terminal_keeper_extension",
            name="Terminal Keeper VS Code Extension",
            family="claw",
            tier="third_party_optional",
            surface_type="workspace_tool",
            integration_mode="vscode_extension",
            installed=terminal_keeper_ext is not None,
            path=terminal_keeper_ext,
            command_surface="terminal-keeper.* commands",
            local_capability="Terminal session orchestration and restoration.",
            remote_dependency="None required.",
            recommended_role="Workflow utility, not an AI bridge.",
            autonomous_default=False,
            trust_notes="Useful terminal utility; distinct from your RimWorld Terminal Keeper mod.",
            proven_live=terminal_keeper_ext is not None,
        ),
    ]

    first_class_ids = [b["id"] for b in bridges if b["tier"] == "first_class"]
    claw_ids = [b["id"] for b in bridges if b["family"] == "claw"]

    return {
        "generated_at": _iso_now(),
        "inventory_version": "1.0",
        "repo_root": str(ROOT),
        "bridges": bridges,
        "summary": {
            "total": len(bridges),
            "installed": sum(1 for b in bridges if b["installed"]),
            "first_class": first_class_ids,
            "second_wave": [b["id"] for b in bridges if b["tier"] == "second_wave"],
            "claw_family": claw_ids,
        },
    }


def save_bridge_inventory(inventory: dict[str, Any] | None = None) -> Path:
    if inventory is None:
        inventory = build_bridge_inventory()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    return STATE_PATH


def load_bridge_inventory(generate_if_missing: bool = True) -> dict[str, Any]:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    if not generate_if_missing:
        return {
            "generated_at": "",
            "inventory_version": "1.0",
            "repo_root": str(ROOT),
            "bridges": [],
            "summary": {"total": 0, "installed": 0, "first_class": [], "second_wave": [], "claw_family": []},
        }
    inventory = build_bridge_inventory()
    save_bridge_inventory(inventory)
    return inventory
