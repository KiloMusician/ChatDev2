#!/usr/bin/env python3
"""Build the canonical control-plane snapshot for the Rosetta bundle."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.repo_path_resolver import get_repo_path  # noqa: E402

GENERATOR_VERSION = "control-plane-snapshot-v1"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def sha256_path(path: Path) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


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


def read_commands(package_json_path: Path) -> list[str]:
    payload = read_json(package_json_path) or {}
    commands = payload.get("contributes", {}).get("commands", [])
    return [
        command.get("command")
        for command in commands
        if isinstance(command, dict) and command.get("command")
    ]


def read_settings(package_json_path: Path) -> list[str]:
    payload = read_json(package_json_path) or {}
    properties = payload.get("contributes", {}).get("configuration", {}).get("properties", {})
    if not isinstance(properties, dict):
        return []
    return sorted(key for key in properties.keys() if isinstance(key, str))


def read_tasks(tasks_path: Path) -> list[str]:
    payload = read_jsonc(tasks_path) or {}
    tasks = payload.get("tasks", [])
    return [
        task.get("label")
        for task in tasks
        if isinstance(task, dict) and isinstance(task.get("label"), str)
    ]


def stat_mtime_iso(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")


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


def probe_json(url: str, timeout: float = 2.0) -> tuple[bool, dict[str, Any] | None, str]:
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            payload = json.loads(body) if body else {}
            return 200 <= response.status < 300, payload if isinstance(payload, dict) else {}, f"HTTP {response.status}"
    except (TimeoutError, URLError, ValueError, OSError) as exc:
        return False, None, str(exc)


def build_service_entry(name: str, url: str) -> dict[str, Any]:
    ok, payload, detail = probe_json(url)
    return {"name": name, "url": url, "ok": ok, "detail": detail, "payload": payload}


def probe_windows_localhost_via_powershell(port: str, request_path: str) -> dict[str, Any]:
    target = f"http://127.0.0.1:{port}{request_path}"
    command = [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-Command",
        (
            "$ProgressPreference='SilentlyContinue';"
            f"$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 '{target}';"
            "Write-Output (@{ ok = $true; status = $r.StatusCode; target = '"
            + target
            + "' } | ConvertTo-Json -Compress)"
        ),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "error": str(exc), "target": target}

    if result.returncode != 0:
        return {
            "ok": False,
            "error": (result.stderr or result.stdout or f"powershell exit {result.returncode}").strip(),
            "target": target,
        }

    try:
        payload = json.loads((result.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        payload = {"ok": True, "target": target}
    return payload if isinstance(payload, dict) else {"ok": True, "target": target}


def probe_gitnexus_local_cli() -> dict[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "src.orchestration.gitnexus", "--json"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            cwd=normalize_path(REPO_ROOT),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "error": str(exc)}

    if result.returncode != 0:
        return {
            "ok": False,
            "error": (result.stderr or result.stdout or f"gitnexus exit {result.returncode}").strip(),
        }

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid gitnexus json: {exc}"}

    if isinstance(payload, dict) and "repos" in payload:
        repo_count = len(payload.get("repos") or {})
    elif isinstance(payload, dict) and "matrix" in payload:
        repo_count = len(payload.get("matrix") or {})
    else:
        repo_count = 0

    return {"ok": True, "probe": "local_cli", "repo_count": repo_count}


def main() -> int:
    nusyq_root = Path(get_repo_path("NUSYQ_ROOT"))
    sim_root = Path(get_repo_path("SIMULATEDVERSE_ROOT"))
    dev_mentor_root = nusyq_root.parent / "Dev-Mentor"

    output_path = nusyq_root / "state" / "reports" / "control_plane_snapshot.json"
    runtime_descriptor_path = sim_root / "state" / "culture_ship_runtime_descriptor.json"
    registry_path = nusyq_root / "state" / "registry.json"
    bootstrap_path = nusyq_root / "state" / "boot" / "rosetta_bootstrap.json"
    deprecation_path = nusyq_root / "state" / "deprecation_registry.json"
    archive_index_path = REPO_ROOT / "state" / "reports" / "obsolete_current_state_archive_index.json"
    archive_summary_path = REPO_ROOT / "state" / "reports" / "obsolete_current_state_archive_summary.md"
    quest_rotation_status_path = sim_root / "shared_cultivation" / "quest_log_rotation_status.json"
    quest_rotation_policy_path = sim_root / "shared_cultivation" / "QUEST_LOG_ROTATION_POLICY.md"
    mediator_pkg = REPO_ROOT / "src" / "vscode_mediator_extension" / "package.json"
    legacy_dashboard_pkg = REPO_ROOT / "extensions" / "agent-dashboard" / "package.json"
    chatdev_extension_pkg = REPO_ROOT / "src" / "integration" / "vscode_extension" / "package.json"
    dev_mentor_tasks_path = dev_mentor_root / ".vscode" / "tasks.json"

    services = {
        "dev_mentor": build_service_entry("dev_mentor", "http://127.0.0.1:7337/api/health"),
        "simulatedverse": build_service_entry("simulatedverse", "http://127.0.0.1:5002/api/health"),
        "chatdev_adapter": build_service_entry("chatdev_adapter", "http://127.0.0.1:4466/chatdev/agents"),
        "ollama": build_service_entry("ollama", "http://127.0.0.1:11434/api/tags"),
        "lm_studio": build_service_entry("lm_studio", "http://127.0.0.1:1234/v1/models"),
        "gitnexus": build_service_entry("gitnexus", "http://127.0.0.1:8000/api/gitnexus/health"),
    }
    if not services["lm_studio"]["ok"]:
        lm_fallback = probe_windows_localhost_via_powershell("1234", "/v1/models")
        if lm_fallback.get("ok"):
            services["lm_studio"] = {
                "name": "lm_studio",
                "url": str(lm_fallback.get("target", "http://127.0.0.1:1234/v1/models")),
                "ok": True,
                "detail": "Windows localhost fallback",
                "payload": lm_fallback,
            }
    if not services["gitnexus"]["ok"]:
        gitnexus_fallback = probe_gitnexus_local_cli()
        if gitnexus_fallback.get("ok"):
            services["gitnexus"] = {
                "name": "gitnexus",
                "url": "local_cli",
                "ok": True,
                "detail": "local CLI fallback",
                "payload": gitnexus_fallback,
            }

    runtime_descriptor = read_json(runtime_descriptor_path)
    registry = read_json(registry_path)
    bootstrap = read_json(bootstrap_path)
    deprecations = read_json(deprecation_path)
    archive_index = read_json(archive_index_path)
    quest_rotation_status = read_json(quest_rotation_status_path)
    mediator_commands = read_commands(mediator_pkg)
    mediator_settings = read_settings(mediator_pkg)
    dashboard_commands = read_commands(legacy_dashboard_pkg)
    chatdev_commands = read_commands(chatdev_extension_pkg)
    dev_mentor_tasks = read_tasks(dev_mentor_tasks_path)
    storage_surfaces = {
        "rosetta_quest_log": describe_storage_surface(
            owner="nusyq",
            label="Rosetta Quest Ledger",
            path=nusyq_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl",
            kind="jsonl_ledger",
            authority="append-only canonical memory",
            note="Primary continuity ledger for cross-session discoveries and task breadcrumbs.",
        ),
        "event_ledgers": describe_storage_surface(
            owner="nusyq",
            label="NuSyQ Event Ledgers",
            path=nusyq_root / "Reports" / "events",
            kind="jsonl_event_directory",
            authority="supporting event archive",
            note="Historical event streams and operational traces.",
        ),
        "hub_ecosystem_status": describe_storage_surface(
            owner="nusyq_hub",
            label="Hub Ecosystem Status",
            path=REPO_ROOT / "ecosystem_status.json",
            kind="json_status",
            authority="supporting status artifact",
            note="Legacy-supporting ecosystem status surface still referenced by operator flows.",
        ),
        "hub_startup_log": describe_storage_surface(
            owner="nusyq_hub",
            label="Hub Startup Log",
            path=REPO_ROOT / "config" / "startup_log.jsonl",
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
            path=dev_mentor_root / "var" / "memory.db",
            kind="sqlite_db",
            authority="repo-local runtime memory",
            note="Dev-Mentor local memory/state database.",
        ),
        "simulatedverse_cache_db": describe_storage_surface(
            owner="simulatedverse",
            label="SimulatedVerse ZTP Cache",
            path=sim_root / "ztp_cache.sqlite3",
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
            path=sim_root / "shared_cultivation" / "quest_log.jsonl",
            kind="jsonl_ledger",
            authority="supporting runtime ledger",
            note="Runtime-adjacent shared cultivation quest trail.",
        ),
    }
    legacy_current_state_archives = sorted((REPO_ROOT / "archive" / "obsolete").glob("current_state_*.md"))
    archive_count = archive_index.get("file_count", len(legacy_current_state_archives)) if archive_index else len(legacy_current_state_archives)
    archive_sample = (
        [entry.get("name") for entry in archive_index.get("latest_entries", [])[:5] if entry.get("name")]
        if archive_index
        else [item.name for item in legacy_current_state_archives[:5]]
    )
    advisories = []
    if archive_count >= 50:
        advisories.append(
            f"legacy current_state archive pressure: {archive_count} files under NuSyQ-Hub/archive/obsolete"
        )
    shared_quest_log_size = storage_surfaces["simulatedverse_shared_quest_log"].get("size_bytes") or 0
    if quest_rotation_status and quest_rotation_status.get("needs_rotation"):
        advisories.append(
            "simulatedverse shared quest log needs rotation; run the canonical quest-log rotation tool"
        )
    elif shared_quest_log_size >= 10_000_000:
        advisories.append(
            "simulatedverse shared quest log is large; consider rotation or archival to reduce scan friction"
        )
    warnings = [
        f"{name} unavailable: {entry['detail']}" for name, entry in services.items() if not entry["ok"]
    ]
    status = "ready" if not warnings else "degraded"

    snapshot = {
        "generated_at": iso_now(),
        "source_hashes": {
            normalize_path(runtime_descriptor_path): sha256_path(runtime_descriptor_path),
            normalize_path(registry_path): sha256_path(registry_path),
            normalize_path(bootstrap_path): sha256_path(bootstrap_path),
            normalize_path(deprecation_path): sha256_path(deprecation_path),
            normalize_path(archive_index_path): sha256_path(archive_index_path),
            normalize_path(quest_rotation_status_path): sha256_path(quest_rotation_status_path),
            normalize_path(Path(__file__).resolve()): sha256_path(Path(__file__).resolve()),
            normalize_path(mediator_pkg): sha256_path(mediator_pkg),
            normalize_path(legacy_dashboard_pkg): sha256_path(legacy_dashboard_pkg),
            normalize_path(chatdev_extension_pkg): sha256_path(chatdev_extension_pkg),
            normalize_path(dev_mentor_tasks_path): sha256_path(dev_mentor_tasks_path),
        },
        "source_paths": [
            normalize_path(runtime_descriptor_path),
            normalize_path(registry_path),
            normalize_path(bootstrap_path),
            normalize_path(deprecation_path),
            normalize_path(archive_index_path),
            normalize_path(quest_rotation_status_path),
            normalize_path(Path(__file__).resolve()),
            normalize_path(mediator_pkg),
            normalize_path(legacy_dashboard_pkg),
            normalize_path(chatdev_extension_pkg),
            normalize_path(dev_mentor_tasks_path),
        ],
        "stale_after_seconds": 300,
        "generator_version": GENERATOR_VERSION,
        "summary": {
            "status": status,
            "healthy_services": sum(1 for entry in services.values() if entry["ok"]),
            "total_services": len(services),
        },
        "control_plane": {
            "runtime_owner": "simulatedverse",
            "control_owner": "nusyq_hub",
            "bootstrap_present": bool(bootstrap),
            "registry_present": bool(registry),
            "deprecations_present": bool(deprecations),
        },
        "culture_ship": {
            "runtime_descriptor_status": runtime_descriptor.get("status", "missing")
            if runtime_descriptor
            else "missing",
            "runtime_owner": (runtime_descriptor or {}).get("runtime_owner", "simulatedverse"),
            "control_owner": (runtime_descriptor or {}).get("control_owner", "nusyq_hub"),
        },
        "ide_surfaces": {
            "canonical_cockpit": "powershellMediator.openCapabilityCockpit",
            "mediator_command_count": len(mediator_commands),
            "mediator_commands": mediator_commands,
            "mediator_setting_count": len(mediator_settings),
            "legacy_dashboard_command_count": len(dashboard_commands),
            "legacy_dashboard_commands": dashboard_commands,
            "chatdev_extension_command_count": len(chatdev_commands),
            "chatdev_extension_commands": chatdev_commands,
            "dev_mentor_task_count": len(dev_mentor_tasks),
            "dev_mentor_task_sample": dev_mentor_tasks[:12],
        },
        "storage_surfaces": {
            "tracked_surface_count": len(storage_surfaces),
            "existing_surface_count": sum(1 for surface in storage_surfaces.values() if surface["exists"]),
            "sqlite_db_count": sum(1 for surface in storage_surfaces.values() if surface["kind"] == "sqlite_db"),
            "legacy_current_state_archive_count": len(legacy_current_state_archives),
            "surfaces": storage_surfaces,
            "legacy_current_state_archives": {
                "path": normalize_path(REPO_ROOT / "archive" / "obsolete"),
                "sample": archive_sample,
            },
        },
        "services": {
            name: {
                "ok": entry["ok"],
                "detail": entry["detail"],
                "summary": entry["payload"] if isinstance(entry["payload"], dict) else {},
            }
            for name, entry in services.items()
        },
        "warnings": warnings,
        "advisories": advisories,
        "errors": [],
        "resource_pressure": {
            "note": "See CONCEPT / Keeper for machine-authoritative pressure state."
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"snapshot": normalize_path(output_path), "status": status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
