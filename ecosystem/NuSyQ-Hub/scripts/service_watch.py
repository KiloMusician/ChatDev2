#!/usr/bin/env python3
"""service_watch.py — console-based service observer that reports ports, duplicate guards,
latest ChatDev receipts/WareHouse artifacts, and dumps the status JSON to the state report.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "state" / "reports" / "ship_status.json"
LOG_PATH = ROOT / "data" / "terminal_logs" / "service_watch.log"
REGISTRY_DIR = ROOT / "state" / "registry"
PORT_CHECKS = {
    "mcp:8080": 8080,
    "critical:8081": 8081,
    "window:8090": 8090,
    "trace:4318": 4318,
    "ollama:11434": 11434,
}
DUPLICATE_TARGETS = {
    "cross_sync": "cross_ecosystem_sync",
    "guild_renderer": "render_guild_board",
    "pu_queue_runner": "pu_queue_runner",
}


def _process_list() -> str:
    cmd = ["tasklist"] if sys.platform == "win32" else ["ps", "-ef"]
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return ""


def _port_ok(port: int) -> bool:
    out = _process_list()
    return str(port) in out


def _duplicates(name: str) -> int:
    data = _process_list()
    return data.count(name)


def _parse_chatdev_entries() -> Iterable[tuple[Path, str, str]]:
    if not REGISTRY_DIR.exists():
        return []
    entries = []
    for pattern in ("*.yaml", "*.yml"):
        for path in REGISTRY_DIR.rglob(pattern):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            match = re.search(r"chatdev_warehouse_path:\s*['\"]?(.+?)['\"]?$", text, re.MULTILINE)
            if not match:
                continue
            entry_path = match.group(1).strip()
            entries.append((path, entry_path, text))
    return entries


def _latest_chatdev_receipt() -> tuple[str, str]:
    best = {
        "mtime": -1.0,
        "project": None,
        "version": None,
        "path": None,
    }
    for manifest, artifact, _ in _parse_chatdev_entries():
        try:
            rel = manifest.relative_to(REGISTRY_DIR)
        except Exception:
            continue
        parts = rel.parts
        project = parts[0] if parts else "unknown"
        version = parts[1] if len(parts) > 1 else None
        mtime = manifest.stat().st_mtime
        if mtime > best["mtime"]:
            best.update(
                {
                    "mtime": mtime,
                    "project": project,
                    "version": version,
                    "path": artifact,
                }
            )
    if best["path"]:
        suffix = f"/{best['version']}" if best["version"] else ""
        receipt = f"{best['project']}{suffix} @ {datetime.utcfromtimestamp(best['mtime']).isoformat()}Z"
        return receipt, best["path"]
    return "No ChatDev receipts yet", "No WareHouse artifact yet"


def _append_log(status: dict[str, object]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(status) + "\n")


def _print_summary(status: dict[str, object]) -> None:
    print("\n🛰️  Service Watch —", status["timestamp"])
    print("Ports:")
    for label, ok in status["ports"].items():
        state = "up" if ok else "down"
        emoji = "✅" if ok else "⚠️"
        print(f"  {emoji} {label:<15} {state}")

    print("\nDuplicates:")
    for label, count in status["duplicates"].items():
        symbol = "🟢" if count <= 1 else "🟡"
        print(f"  {symbol} {label:<18} {count} instance{'s' if count != 1 else ''}")

    print("\nChatDev:")
    print(f"  📜 Latest receipt: {status['chatdev_receipt']}")
    print(f"  🗂️  Latest WareHouse artifact: {status['warehouse_artifact']}")

    print("\nLog file:", LOG_PATH)


def _build_status() -> dict[str, object]:
    receipt, artifact = _latest_chatdev_receipt()
    ports = {label: _port_ok(port) for label, port in PORT_CHECKS.items()}
    duplicates = {label: _duplicates(target) for label, target in DUPLICATE_TARGETS.items()}
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ports": ports,
        "duplicates": duplicates,
        "chatdev_receipt": receipt,
        "warehouse_artifact": artifact,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Service watcher for NuSyQ-Hub.")
    parser.add_argument("--json", action="store_true", help="Emit machine-friendly JSON only (used by GUI).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status = _build_status()

    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")

    _append_log(status)

    if args.json:
        print(json.dumps(status))
    else:
        _print_summary(status)
        print(json.dumps(status))

    return 0


def interactive_status_dump() -> dict[str, object]:
    """Helper to run inside VS Code interactive window / Notebook cell."""
    status = _build_status()
    print(json.dumps(status, indent=2))
    return status


# %%
# Interactive cell: run `interactive_status_dump()` to view the current ports/receipts in the VS Code Python Interactive window.

if __name__ == "__main__":
    raise SystemExit(main())
