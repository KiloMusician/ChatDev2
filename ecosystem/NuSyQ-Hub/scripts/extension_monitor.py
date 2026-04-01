#!/usr/bin/env python3
"""Continuous VS Code extension monitoring utility.

- Summarizes active extension processes from `code --status`
- Logs daily audit snapshots to `state/audits/extensions/`
- Designed to run via VS Code task: "Daily Extension Audit"
"""

import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUTDIR = BASE / "state" / "audits" / "extensions"
OUTDIR.mkdir(parents=True, exist_ok=True)


def get_code_status() -> str:
    try:
        result = subprocess.run(["code", "--status"], capture_output=True, text=True, timeout=40, check=False)
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def normalize_extension_id(raw: str) -> str:
    """Normalize extension folder/process token to publisher.name form."""
    token = raw.strip().lower()
    if not token:
        return ""
    # Strip version/platform suffixes (publisher.name-1.2.3[-platform])
    token = re.sub(r"-\d[\w\.\-]*$", "", token)
    return token if re.match(r"^[a-z0-9][a-z0-9\-]*\.[a-z0-9][a-z0-9\-]*$", token) else ""


def parse_active_extensions(status_text: str) -> list[str]:
    """Parse active extension identifiers from `code --status` output."""
    active = []
    pattern = re.compile(r"\.vscode(?:-server)?[\\/]+extensions[\\/]+([^\\/]+)")
    for line in status_text.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        ext_id = normalize_extension_id(match.group(1))
        if ext_id and ext_id not in active:
            active.append(ext_id)
    return active


def list_installed_extensions() -> list[str]:
    """Discover installed extensions across common Windows/WSL paths."""
    candidates = []
    home = Path.home()
    userprofile = Path(os.environ.get("USERPROFILE", ""))
    if userprofile:
        candidates.append(userprofile / ".vscode" / "extensions")
    candidates.append(home / ".vscode" / "extensions")
    wsl_users = Path("/mnt/c/Users")
    if wsl_users.exists():
        candidates.extend(path for path in wsl_users.glob("*/.vscode/extensions"))

    values: set[str] = set()
    for ext_dir in candidates:
        if not ext_dir.exists():
            continue
        for child in ext_dir.iterdir():
            if not child.is_dir():
                continue
            ext_id = normalize_extension_id(child.name)
            if ext_id:
                values.add(ext_id)
    return sorted(values)


def main() -> None:
    status = get_code_status()
    active = parse_active_extensions(status)
    installed = list_installed_extensions()
    data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "total_installed": len(installed),
        "total_active_detected": len(active),
        "code_status_available": bool(status.strip()),
        "installed": installed,
        "active_detected": active,
    }
    (OUTDIR / f"monitor_snapshot_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json").write_text(
        json.dumps(data, indent=2)
    )
    print(json.dumps({"summary": data["total_installed"], "active": data["total_active_detected"]}))


if __name__ == "__main__":
    main()
