from __future__ import annotations

import csv
import io
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from app.backend import service_registry

ECOSYSTEM_KEYWORDS = (
    "python",
    "docker",
    "node",
    "bash",
    "git",
    "code",
    "ollama",
    "lm studio",
    "claude",
    "copilot",
    "chatgpt",
    "biome",
    "rimworld",
    "powershell",
    "pwsh",
    "cmd",
    "wsl",
    "steam",
    "unity",
    "terminal",
    "devmentor",
    "serena",
    "gordon",
    "skyclaw",
    "chatdev",
    "culture",
    "nusyq",
)


def is_ecosystem_process(name: str) -> bool:
    lowered = (name or "").strip().lower()
    return any(keyword in lowered for keyword in ECOSYSTEM_KEYWORDS)


def _is_wsl() -> bool:
    if os.getenv("WSL_DISTRO_NAME"):
        return True
    proc_version = Path("/proc/version")
    if not proc_version.exists():
        return False
    try:
        return "microsoft" in proc_version.read_text().lower()
    except Exception:
        return False


def _format_timestamp(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    text = str(value).strip()
    return text or None


def _normalize_process(
    pid: object,
    name: object,
    start_time: object,
    *,
    metadata: Dict | None = None,
) -> Dict | None:
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return None
    name_text = str(name or "").strip()
    if not name_text:
        return None
    return {
        "pid": pid_int,
        "name": name_text,
        "start_time": _format_timestamp(start_time),
        "is_ecosystem": is_ecosystem_process(name_text),
        "metadata": metadata or {},
    }


def _scan_windows_host_processes() -> List[Dict]:
    shell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not shell:
        raise RuntimeError("PowerShell is not available")

    script = r"""
$ErrorActionPreference = 'SilentlyContinue'
Get-Process | ForEach-Object {
  $start = ''
  $path = ''
  try { $start = $_.StartTime.ToString('o') } catch {}
  try { $path = $_.Path } catch {}
  [pscustomobject]@{
    Name = $_.ProcessName
    Id = $_.Id
    StartTime = $start
    Path = $path
  }
} | ConvertTo-Csv -NoTypeInformation
"""
    result = subprocess.run(
        [shell, "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "PowerShell process query failed")

    reader = csv.DictReader(io.StringIO(result.stdout))
    processes: List[Dict] = []
    for row in reader:
        metadata = {"source": "powershell"}
        if row.get("Path"):
            metadata["path"] = row["Path"].strip()
        normalized = _normalize_process(
            row.get("Id"),
            row.get("Name"),
            row.get("StartTime"),
            metadata=metadata,
        )
        if normalized:
            processes.append(normalized)
    return processes


def _scan_psutil_processes() -> List[Dict]:
    import psutil

    processes: List[Dict] = []
    for proc in psutil.process_iter(["pid", "name", "create_time", "exe", "username"]):
        try:
            metadata = {"source": "psutil"}
            if proc.info.get("exe"):
                metadata["path"] = proc.info["exe"]
            if proc.info.get("username"):
                metadata["username"] = proc.info["username"]
            normalized = _normalize_process(
                proc.info.get("pid"),
                proc.info.get("name"),
                proc.info.get("create_time"),
                metadata=metadata,
            )
            if normalized:
                processes.append(normalized)
        except Exception:
            continue
    return processes


def _scan_ps_processes() -> List[Dict]:
    result = subprocess.run(
        ["ps", "-eo", "pid=,comm=,lstart="],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ps process query failed")

    processes: List[Dict] = []
    for line in result.stdout.splitlines():
        parts = line.strip().split(maxsplit=6)
        if len(parts) < 7:
            continue
        normalized = _normalize_process(
            parts[0],
            parts[1],
            " ".join(parts[2:]),
            metadata={"source": "ps"},
        )
        if normalized:
            processes.append(normalized)
    return processes


def scan_processes() -> List[Dict]:
    scanners = []
    if _is_wsl():
        scanners.append(_scan_windows_host_processes)
    else:
        try:
            import psutil  # noqa: F401

            scanners.append(_scan_psutil_processes)
        except Exception:
            pass
        if sys.platform.startswith("win"):
            scanners.append(_scan_windows_host_processes)
        else:
            scanners.append(_scan_ps_processes)

    last_error = None
    for scanner in scanners:
        try:
            processes = scanner()
            if processes:
                return sorted(processes, key=lambda proc: (proc["name"].lower(), proc["pid"]))
        except Exception as exc:
            last_error = exc

    if last_error:
        raise RuntimeError(str(last_error))
    return []


def sync_processes_to_registry(
    processes: List[Dict],
    *,
    stale_seconds: int = 300,
) -> Dict:
    active_processes: List[Dict] = []
    normalized_processes: List[Dict] = []

    for process in processes:
        if process.get("pid") is None or not process.get("name"):
            continue
        normalized_processes.append(
            {
                "pid": int(process["pid"]),
                "name": str(process["name"]),
                "start_time": process.get("start_time"),
                "is_ecosystem": bool(process.get("is_ecosystem")),
                "metadata": process.get("metadata") or {},
            }
        )
        active_processes.append(
            {
                "pid": int(process["pid"]),
                "start_time": str(process.get("start_time") or ""),
            }
        )

    ecosystem_count = sum(1 for process in normalized_processes if process["is_ecosystem"])
    upserted = service_registry.upsert_processes(normalized_processes)

    pruned = service_registry.prune_stale_processes(
        age_seconds=stale_seconds,
        active_processes=active_processes,
    )
    return {
        "seen": upserted,
        "ecosystem": ecosystem_count,
        "pruned": pruned,
    }
