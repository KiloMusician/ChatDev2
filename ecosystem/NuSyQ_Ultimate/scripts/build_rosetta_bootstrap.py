#!/usr/bin/env python3
"""Build the distributed Rosetta bundle and compact boot capsule."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "state"
BOOT_DIR = STATE_DIR / "boot"
REPORTS_DIR = STATE_DIR / "reports"
DOCS_PATH = ROOT / "docs" / "ROSETTA_STONE.md"
MANIFEST_PATH = ROOT / "config" / "control_plane_manifest.json"
REGISTRY_PATH = STATE_DIR / "registry.json"
DEPRECATION_PATH = STATE_DIR / "deprecation_registry.json"
SNAPSHOT_PATH = REPORTS_DIR / "control_plane_snapshot.json"
QUEST_LOG_PATH = ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
BOOTSTRAP_JSON_PATH = BOOT_DIR / "rosetta_bootstrap.json"
BOOTSTRAP_TXT_PATH = BOOT_DIR / "ROSETTA_BOOT.txt"
GENERATOR_VERSION = "rosetta-bootstrap-v1"
BOOT_JSON_MAX_BYTES = 32_768
BOOT_TXT_MAX_LINES = 60


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_text(path.read_text(encoding="utf-8")) if path.exists() else "missing"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def stat_mtime_iso(path: Path) -> str | None:
    if not path.exists():
        return None
    return (
        datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def describe_storage_surface(
    *,
    owner: str,
    label: str,
    path: Path,
    kind: str,
    authority: str,
    note: str,
) -> dict[str, Any]:
    return {
        "owner": owner,
        "label": label,
        "path": normalize_path(path),
        "kind": kind,
        "authority": authority,
        "note": note,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "updated_at": stat_mtime_iso(path),
    }


def strip_jsonc_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    stripped_lines: list[str] = []
    for line in text.splitlines():
        in_string = False
        escaped = False
        buffer: list[str] = []
        i = 0
        while i < len(line):
            char = line[i]
            if char == "\\" and in_string:
                escaped = not escaped
                buffer.append(char)
                i += 1
                continue
            if char == '"' and not escaped:
                in_string = not in_string
                buffer.append(char)
                i += 1
                continue
            escaped = False
            if not in_string and char == "/" and i + 1 < len(line) and line[i + 1] == "/":
                break
            buffer.append(char)
            i += 1
        stripped_lines.append("".join(buffer))
    return "\n".join(stripped_lines)


def read_jsonc(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(strip_jsonc_comments(text))


def read_package_commands(package_json_path: Path) -> list[str]:
    payload = read_json(package_json_path) or {}
    commands = payload.get("contributes", {}).get("commands", [])
    return [
        command.get("command")
        for command in commands
        if isinstance(command, dict) and command.get("command")
    ]


def read_package_settings(package_json_path: Path) -> list[str]:
    payload = read_json(package_json_path) or {}
    properties = payload.get("contributes", {}).get("configuration", {}).get("properties", {})
    if not isinstance(properties, dict):
        return []
    return sorted(key for key in properties.keys() if isinstance(key, str))


def read_vscode_tasks(tasks_path: Path) -> list[str]:
    payload = read_jsonc(tasks_path) or {}
    tasks = payload.get("tasks", [])
    return [
        task.get("label")
        for task in tasks
        if isinstance(task, dict) and isinstance(task.get("label"), str)
    ]


def discover_repo_roots() -> dict[str, Path]:
    user_root = ROOT.parent
    return {
        "concept": Path(os.getenv("CONCEPT_ROOT", "/mnt/c/CONCEPT")),
        "dev_mentor": Path(os.getenv("DEV_MENTOR_ROOT", normalize_path(user_root / "Dev-Mentor"))),
        "simulatedverse": Path(
            os.getenv(
                "SIMULATEDVERSE_ROOT",
                normalize_path(user_root / "Desktop" / "SimulatedVerse" / "SimulatedVerse"),
            )
        ),
        "nusyq": ROOT,
        "nusyq_hub": Path(
            os.getenv(
                "NUSYQ_HUB_ROOT",
                normalize_path(user_root / "Desktop" / "Legacy" / "NuSyQ-Hub"),
            )
        ),
    }


def build_deprecation_registry(repo_roots: dict[str, Path]) -> dict[str, Any]:
    generated_at = iso_now()
    entries = {
        "docs": [
            {
                "path": normalize_path(repo_roots["nusyq_hub"] / "CULTURE_SHIP_OPERATIONAL.md"),
                "reason": "Legacy single-owner Culture Ship framing; prefer structured dual-authority artifacts.",
                "replacement": normalize_path(DOCS_PATH),
            }
        ],
        "extensions": [
            {
                "path": normalize_path(repo_roots["nusyq_hub"] / "extensions" / "agent-dashboard"),
                "reason": "Legacy dashboard surface; behavior is folded into the mediator cockpit.",
                "replacement": normalize_path(
                    repo_roots["nusyq_hub"] / "src" / "vscode_mediator_extension"
                ),
            },
            {
                "path": normalize_path(
                    repo_roots["nusyq_hub"] / "src" / "integration" / "vscode_extension"
                ),
                "reason": "Supporting ChatDev extension, not the canonical control-plane cockpit.",
                "replacement": normalize_path(
                    repo_roots["nusyq_hub"] / "src" / "vscode_mediator_extension"
                ),
            },
        ],
        "bridges": [
            {
                "path": normalize_path(
                    repo_roots["simulatedverse"] / "server" / "router" / "culture-ship.ts"
                ),
                "reason": "Legacy bridge-style Culture Ship router; keep for compatibility, but prefer the runtime descriptor and active routes.",
                "replacement": normalize_path(
                    repo_roots["simulatedverse"] / "state" / "culture_ship_runtime_descriptor.json"
                ),
            }
        ],
        "commands": [
            {
                "command": "broad_repo_scan_before_bootstrap",
                "reason": "Superseded by structured control-plane read precedence.",
                "replacement": "state/boot/rosetta_bootstrap.json",
            }
        ],
    }
    source_paths = [
        normalize_path(DOCS_PATH),
        normalize_path(repo_roots["nusyq_hub"] / "ECOSYSTEM_CONTROL_PLANE.md"),
        normalize_path(repo_roots["simulatedverse"] / "README.md"),
    ]
    source_hashes = {path: sha256_path(Path(path)) for path in source_paths}
    registry = {
        "generated_at": generated_at,
        "generator_version": GENERATOR_VERSION,
        "stale_after_seconds": 86400,
        "source_paths": source_paths,
        "source_hashes": source_hashes,
        "deprecated": entries,
    }
    return registry


def build_registry(
    repo_roots: dict[str, Path],
    snapshot: dict[str, Any] | None,
    deprecations: dict[str, Any],
) -> dict[str, Any]:
    generated_at = iso_now()
    runtime_descriptor_path = (
        repo_roots["simulatedverse"] / "state" / "culture_ship_runtime_descriptor.json"
    )
    runtime_descriptor = read_json(runtime_descriptor_path)
    mediator_pkg = repo_roots["nusyq_hub"] / "src" / "vscode_mediator_extension" / "package.json"
    legacy_dashboard_pkg = (
        repo_roots["nusyq_hub"] / "extensions" / "agent-dashboard" / "package.json"
    )
    chatdev_extension_pkg = (
        repo_roots["nusyq_hub"] / "src" / "integration" / "vscode_extension" / "package.json"
    )
    dev_mentor_tasks_path = repo_roots["dev_mentor"] / ".vscode" / "tasks.json"
    archive_index_path = (
        repo_roots["nusyq_hub"] / "state" / "reports" / "obsolete_current_state_archive_index.json"
    )
    archive_summary_path = (
        repo_roots["nusyq_hub"] / "state" / "reports" / "obsolete_current_state_archive_summary.md"
    )
    quest_rotation_status_path = (
        repo_roots["simulatedverse"] / "shared_cultivation" / "quest_log_rotation_status.json"
    )
    quest_rotation_policy_path = (
        repo_roots["simulatedverse"] / "shared_cultivation" / "QUEST_LOG_ROTATION_POLICY.md"
    )
    mediator_commands = read_package_commands(mediator_pkg)
    mediator_settings = read_package_settings(mediator_pkg)
    legacy_dashboard_commands = read_package_commands(legacy_dashboard_pkg)
    chatdev_extension_commands = read_package_commands(chatdev_extension_pkg)
    dev_mentor_tasks = read_vscode_tasks(dev_mentor_tasks_path)
    storage_surfaces = {
        "rosetta_quest_log": describe_storage_surface(
            owner="nusyq",
            label="Rosetta Quest Ledger",
            path=QUEST_LOG_PATH,
            kind="jsonl_ledger",
            authority="append-only canonical memory",
            note="Primary continuity ledger for cross-session discoveries and task breadcrumbs.",
        ),
        "event_ledgers": describe_storage_surface(
            owner="nusyq",
            label="NuSyQ Event Ledgers",
            path=repo_roots["nusyq"] / "Reports" / "events",
            kind="jsonl_event_directory",
            authority="supporting event archive",
            note="Historical event streams and operational traces.",
        ),
        "hub_ecosystem_status": describe_storage_surface(
            owner="nusyq_hub",
            label="Hub Ecosystem Status",
            path=repo_roots["nusyq_hub"] / "ecosystem_status.json",
            kind="json_status",
            authority="supporting status artifact",
            note="Legacy-supporting ecosystem status surface still referenced by operator flows.",
        ),
        "hub_startup_log": describe_storage_surface(
            owner="nusyq_hub",
            label="Hub Startup Log",
            path=repo_roots["nusyq_hub"] / "config" / "startup_log.jsonl",
            kind="jsonl_log",
            authority="supporting startup trace",
            note="Startup/session trace for Hub-side activation and orchestration.",
        ),
        "hub_archive_index": describe_storage_surface(
            owner="nusyq_hub",
            label="Obsolete Current State Archive Index",
            path=archive_index_path,
            kind="json_index",
            authority="generated canonical archive summary",
            note="Canonical compact index for obsolete current_state archives.",
        ),
        "hub_archive_summary": describe_storage_surface(
            owner="nusyq_hub",
            label="Obsolete Current State Archive Summary",
            path=archive_summary_path,
            kind="markdown_summary",
            authority="generated canonical archive summary",
            note="Human-readable summary for obsolete current_state archives.",
        ),
        "dev_mentor_memory_db": describe_storage_surface(
            owner="dev_mentor",
            label="Dev-Mentor Memory DB",
            path=repo_roots["dev_mentor"] / "var" / "memory.db",
            kind="sqlite_db",
            authority="repo-local runtime memory",
            note="Dev-Mentor local memory/state database.",
        ),
        "simulatedverse_cache_db": describe_storage_surface(
            owner="simulatedverse",
            label="SimulatedVerse ZTP Cache",
            path=repo_roots["simulatedverse"] / "ztp_cache.sqlite3",
            kind="sqlite_db",
            authority="runtime cache",
            note="Simulation/runtime-side cache database.",
        ),
        "simulatedverse_quest_rotation_status": describe_storage_surface(
            owner="simulatedverse",
            label="Shared Quest Rotation Status",
            path=quest_rotation_status_path,
            kind="json_status",
            authority="generated maintenance status",
            note="Latest shared quest rotation recommendation or receipt.",
        ),
        "simulatedverse_quest_rotation_policy": describe_storage_surface(
            owner="simulatedverse",
            label="Shared Quest Rotation Policy",
            path=quest_rotation_policy_path,
            kind="markdown_policy",
            authority="hand-authored operational policy",
            note="Canonical policy for rotating the shared cultivation quest log.",
        ),
        "simulatedverse_shared_quest_log": describe_storage_surface(
            owner="simulatedverse",
            label="SimulatedVerse Shared Quest Log",
            path=repo_roots["simulatedverse"] / "shared_cultivation" / "quest_log.jsonl",
            kind="jsonl_ledger",
            authority="supporting runtime ledger",
            note="Runtime-adjacent shared cultivation quest trail.",
        ),
    }
    legacy_current_state_archives = sorted(
        (repo_roots["nusyq_hub"] / "archive" / "obsolete").glob("current_state_*.md")
    )
    repos = {
        "concept": {
            "path": normalize_path(repo_roots["concept"]),
            "role": "kernel",
            "priority": 1,
            "authority": "machine-governance",
        },
        "dev_mentor": {
            "path": normalize_path(repo_roots["dev_mentor"]),
            "role": "developer_intelligence",
            "priority": 2,
            "authority": "workflow_and_guidance",
        },
        "simulatedverse": {
            "path": normalize_path(repo_roots["simulatedverse"]),
            "role": "simulation_runtime",
            "priority": 3,
            "authority": "culture_ship_runtime_owner",
        },
        "nusyq_hub": {
            "path": normalize_path(repo_roots["nusyq_hub"]),
            "role": "control_plane",
            "priority": 4,
            "authority": "culture_ship_control_owner",
        },
        "nusyq": {
            "path": normalize_path(repo_roots["nusyq"]),
            "role": "rosetta_bundle",
            "priority": 5,
            "authority": "distributed_memory_and_bootstrap",
        },
    }
    services = {
        "dev_mentor": {"health_url": "http://127.0.0.1:7337/api/health", "port": 7337},
        "simulatedverse": {"health_url": "http://127.0.0.1:5002/api/health", "port": 5002},
        "chatdev_adapter": {
            "health_url": "http://127.0.0.1:4466/chatdev/agents",
            "port": 4466,
        },
        "ollama": {"health_url": "http://127.0.0.1:11434/api/tags", "port": 11434},
        "lm_studio": {"health_url": "http://127.0.0.1:1234/v1/models", "port": 1234},
        "gitnexus": {"health_url": "http://127.0.0.1:8000/api/gitnexus/health", "port": 8000},
    }
    registry = {
        "generated_at": generated_at,
        "updated_at": generated_at,
        "generator_version": GENERATOR_VERSION,
        "stale_after_seconds": 21600,
        "source_paths": [
            normalize_path(DOCS_PATH),
            normalize_path(MANIFEST_PATH),
            normalize_path(SNAPSHOT_PATH),
            normalize_path(runtime_descriptor_path),
            normalize_path(mediator_pkg),
            normalize_path(legacy_dashboard_pkg),
            normalize_path(chatdev_extension_pkg),
            normalize_path(dev_mentor_tasks_path),
        ],
        "source_hashes": {
            normalize_path(DOCS_PATH): sha256_path(DOCS_PATH),
            normalize_path(MANIFEST_PATH): sha256_path(MANIFEST_PATH),
            normalize_path(SNAPSHOT_PATH): sha256_path(SNAPSHOT_PATH),
            normalize_path(runtime_descriptor_path): sha256_path(runtime_descriptor_path),
            normalize_path(mediator_pkg): sha256_path(mediator_pkg),
            normalize_path(legacy_dashboard_pkg): sha256_path(legacy_dashboard_pkg),
            normalize_path(chatdev_extension_pkg): sha256_path(chatdev_extension_pkg),
            normalize_path(dev_mentor_tasks_path): sha256_path(dev_mentor_tasks_path),
        },
        "repos": repos,
        "roles": {name: meta["role"] for name, meta in repos.items()},
        "agents": {
            "serena": {"role": "refactor_and_structure"},
            "gordon": {"role": "execution_and_orchestration"},
            "chatdev": {"role": "multi_agent_generation"},
            "copilot": {"role": "inline_coding"},
            "ollama": {"role": "local_reasoning"},
            "lm_studio": {"role": "local_openai_compatible_models"},
        },
        "services": services,
        "bridges": {
            "keeper_mcp": "C:/CONCEPT/tools/keeper-mcp.ps1",
            "gitnexus": "/api/gitnexus/matrix",
            "nogic": "NuSyQ-Hub visualization surface",
            "chatdev_adapter": services["chatdev_adapter"]["health_url"],
        },
        "extensions": {
            "canonical": {
                "path": "NuSyQ-Hub/src/vscode_mediator_extension",
                "commands": mediator_commands,
                "settings": mediator_settings,
            },
            "supporting": {
                "agent_dashboard": legacy_dashboard_commands,
                "chatdev_vscode_extension": chatdev_extension_commands,
            },
            "legacy_dashboard_folded_in": True,
        },
        "commands": {
            "keeper_preflight": [
                "keeper_snapshot",
                "keeper_score",
                "keeper_advisor",
                "keeper_think",
            ],
            "bootstrap": ["python scripts/build_rosetta_bootstrap.py"],
            "snapshot": ["python scripts/build_control_plane_snapshot.py"],
            "culture_ship_runtime": ["python scripts/export_culture_ship_runtime_descriptor.py"],
            "quest_log_rotation": ["python ops/rotate_shared_quest_log.py"],
            "archive_index": ["python scripts/index_obsolete_current_state_archives.py"],
        },
        "tasks": {
            "boot": "load bootstrap, registry, snapshot, then focused feeds",
            "doctor": "refresh snapshot before broad diagnostics",
            "culture_ship": "use dual-authority model",
            "dev_mentor_vscode": {
                "path": normalize_path(dev_mentor_tasks_path),
                "count": len(dev_mentor_tasks),
                "sample": dev_mentor_tasks[:12],
            },
        },
        "dashboards": {
            "canonical_cockpit": "NuSyQ mediator capability cockpit",
            "supporting": ["NuSyQ diagnostics dashboard"],
        },
        "storage": {
            "surfaces": storage_surfaces,
            "legacy_current_state_archives": {
                "path": normalize_path(repo_roots["nusyq_hub"] / "archive" / "obsolete"),
                "count": len(legacy_current_state_archives),
                "sample": [item.name for item in legacy_current_state_archives[:5]],
            },
        },
        "ports": {name: info["port"] for name, info in services.items()},
        "artifacts": {
            "rosetta_contract": normalize_path(DOCS_PATH),
            "control_plane_manifest": normalize_path(MANIFEST_PATH),
            "control_plane_snapshot": normalize_path(SNAPSHOT_PATH),
            "culture_ship_runtime_descriptor": normalize_path(runtime_descriptor_path),
            "quest_log_rotation_status": normalize_path(quest_rotation_status_path),
            "quest_log_rotation_policy": normalize_path(quest_rotation_policy_path),
            "archive_index": normalize_path(archive_index_path),
            "archive_summary": normalize_path(archive_summary_path),
            "quest_log": normalize_path(QUEST_LOG_PATH),
            "deprecations": normalize_path(DEPRECATION_PATH),
        },
        "workflows": {
            "read_precedence": [
                "state/boot/rosetta_bootstrap.json",
                "state/registry.json",
                "state/reports/control_plane_snapshot.json",
                "focused feeds",
                "docs fallback",
            ],
            "culture_ship": {
                "runtime_owner": "simulatedverse",
                "control_owner": "nusyq_hub",
            },
        },
        "deprecated": deprecations["deprecated"],
        "control_plane": {
            "runtime_owner": "simulatedverse",
            "control_owner": "nusyq_hub",
            "snapshot_status": snapshot.get("summary", {}).get("status", "missing")
            if snapshot
            else "missing",
            "runtime_descriptor_status": runtime_descriptor.get("status", "missing")
            if runtime_descriptor
            else "missing",
            "ide_surface_summary": {
                "mediator_commands": len(mediator_commands),
                "mediator_settings": len(mediator_settings),
                "supporting_extension_commands": len(legacy_dashboard_commands)
                + len(chatdev_extension_commands),
                "dev_mentor_tasks": len(dev_mentor_tasks),
            },
            "storage_summary": {
                "tracked_surfaces": len(storage_surfaces),
                "existing_surfaces": sum(
                    1 for surface in storage_surfaces.values() if surface["exists"]
                ),
                "sqlite_dbs": sum(
                    1 for surface in storage_surfaces.values() if surface["kind"] == "sqlite_db"
                ),
                "legacy_current_state_archives": len(legacy_current_state_archives),
            },
        },
    }
    return registry


def build_bootstrap(
    registry: dict[str, Any],
    snapshot: dict[str, Any] | None,
) -> tuple[dict[str, Any], str]:
    generated_at = iso_now()
    services = registry["services"]
    focus = []
    if snapshot and snapshot.get("warnings"):
        focus.extend(snapshot["warnings"][:3])
    if not focus and snapshot and snapshot.get("advisories"):
        focus.extend(snapshot["advisories"][:3])
    if not focus:
        focus = [
            "Keeper preflight before heavy runtime activation",
            "Respect dual-authority Culture Ship contract",
            "Use mediator + structured bundle before broad scans",
        ]
    bootstrap = {
        "generated_at": generated_at,
        "generator_version": GENERATOR_VERSION,
        "stale_after_seconds": 3600,
        "source_paths": [
            normalize_path(REGISTRY_PATH),
            normalize_path(SNAPSHOT_PATH),
            normalize_path(DOCS_PATH),
            normalize_path(MANIFEST_PATH),
            normalize_path(DEPRECATION_PATH),
        ],
        "source_hashes": {
            normalize_path(REGISTRY_PATH): sha256_path(REGISTRY_PATH),
            normalize_path(SNAPSHOT_PATH): sha256_path(SNAPSHOT_PATH),
            normalize_path(DOCS_PATH): sha256_path(DOCS_PATH),
            normalize_path(MANIFEST_PATH): sha256_path(MANIFEST_PATH),
            normalize_path(DEPRECATION_PATH): sha256_path(DEPRECATION_PATH),
        },
        "read_precedence": registry["workflows"]["read_precedence"],
        "repo_roles": {
            name: {"role": meta["role"], "path": meta["path"], "priority": meta["priority"]}
            for name, meta in registry["repos"].items()
        },
        "control_plane": registry["control_plane"],
        "command_canon": registry["commands"],
        "canonical_paths": registry["artifacts"],
        "services": {
            name: {"port": meta["port"], "health_url": meta["health_url"]}
            for name, meta in services.items()
        },
        "top_focus": focus,
        "read_next": [
            "docs/ROSETTA_STONE.md",
            "config/control_plane_manifest.json",
            "state/reports/control_plane_snapshot.json",
        ],
        "deprecated_counts": {key: len(value) for key, value in registry["deprecated"].items()},
        "ide_surfaces": registry["control_plane"]["ide_surface_summary"],
        "storage_surfaces": registry["control_plane"]["storage_summary"],
    }
    boot_lines = [
        "ROSETTA BOOT",
        f"generated_at: {generated_at}",
        "read precedence:",
        "1. state/boot/rosetta_bootstrap.json",
        "2. state/registry.json",
        "3. state/reports/control_plane_snapshot.json",
        "4. focused feed artifacts",
        "5. docs fallback",
        "culture ship:",
        "runtime_owner: simulatedverse",
        "control_owner: nusyq_hub",
        "repo roles:",
    ]
    for name, meta in registry["repos"].items():
        boot_lines.append(f"- {name}: {meta['role']} @ {meta['path']}")
    boot_lines.extend(
        [
            "services:",
            f"- dev_mentor: {services['dev_mentor']['health_url']}",
            f"- simulatedverse: {services['simulatedverse']['health_url']}",
            f"- chatdev_adapter: {services['chatdev_adapter']['health_url']}",
            f"- ollama: {services['ollama']['health_url']}",
            f"- lm_studio: {services['lm_studio']['health_url']}",
            "ide surfaces:",
            f"- mediator commands: {registry['control_plane']['ide_surface_summary']['mediator_commands']}",
            f"- dev-mentor tasks: {registry['control_plane']['ide_surface_summary']['dev_mentor_tasks']}",
            "storage surfaces:",
            f"- tracked stores: {registry['control_plane']['storage_summary']['tracked_surfaces']}",
            f"- sqlite dbs: {registry['control_plane']['storage_summary']['sqlite_dbs']}",
            "top focus:",
        ]
    )
    for item in focus[:5]:
        boot_lines.append(f"- {item}")
    boot_lines.extend(
        [
            "read next:",
            "- docs/ROSETTA_STONE.md",
            "- state/registry.json",
            "- state/reports/control_plane_snapshot.json",
        ]
    )
    return bootstrap, "\n".join(boot_lines) + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    ensure_parent(path)
    path.write_text(payload, encoding="utf-8")


def main() -> int:
    repo_roots = discover_repo_roots()
    snapshot = read_json(SNAPSHOT_PATH)

    deprecations = build_deprecation_registry(repo_roots)
    write_json(DEPRECATION_PATH, deprecations)

    registry = build_registry(repo_roots, snapshot, deprecations)
    write_json(REGISTRY_PATH, registry)

    bootstrap, boot_text = build_bootstrap(registry, snapshot)
    bootstrap_bytes = len(json.dumps(bootstrap, separators=(",", ":")).encode("utf-8"))
    if bootstrap_bytes > BOOT_JSON_MAX_BYTES:
        raise SystemExit(
            f"Bootstrap JSON too large: {bootstrap_bytes} bytes > {BOOT_JSON_MAX_BYTES}"
        )
    if len(boot_text.splitlines()) > BOOT_TXT_MAX_LINES:
        raise SystemExit(
            f"Boot TXT too long: {len(boot_text.splitlines())} lines > {BOOT_TXT_MAX_LINES}"
        )
    write_json(BOOTSTRAP_JSON_PATH, bootstrap)
    write_text(BOOTSTRAP_TXT_PATH, boot_text)

    print(
        json.dumps(
            {
                "registry": normalize_path(REGISTRY_PATH),
                "deprecations": normalize_path(DEPRECATION_PATH),
                "bootstrap_json": normalize_path(BOOTSTRAP_JSON_PATH),
                "bootstrap_txt": normalize_path(BOOTSTRAP_TXT_PATH),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
