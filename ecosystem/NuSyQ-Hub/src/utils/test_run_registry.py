"""Track test runs to reduce duplicate spam and improve observability."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class TestRunSummary:
    run_id: str
    command: list[str]
    cwd: str
    status: str
    exit_code: int
    duration_seconds: float
    command_key: str
    run_count_window: int
    duplicate_of: str | None
    registry_path: str


def _normalize_command(cmd: list[str]) -> str:
    return " ".join(cmd).strip()


def _command_key(cmd: list[str]) -> str:
    normalized = _normalize_command(cmd).encode("utf-8", errors="ignore")
    return hashlib.sha256(normalized).hexdigest()


def _load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"runs": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
    except (OSError, json.JSONDecodeError):
        return {"runs": []}


def _save_registry(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_test_run(
    command: list[str],
    cwd: str,
    status: str,
    exit_code: int,
    duration_seconds: float,
    source: str,
    window_minutes: int = 30,
    max_entries: int = 200,
    registry_path: Path | None = None,
) -> TestRunSummary:
    """Record a test run and return a summary for logging."""
    now = datetime.now()
    run_id = f"test_run_{now.strftime('%Y%m%d_%H%M%S')}"
    command_key = _command_key(command)

    if registry_path is None:
        registry_path = Path("state") / "reports" / "test_runs.json"

    data = _load_registry(registry_path)
    runs = data.get("runs", [])

    window_start = now - timedelta(minutes=max(0, window_minutes))
    recent = []
    for entry in runs:
        ts = entry.get("timestamp")
        if not ts:
            continue
        try:
            parsed = datetime.fromisoformat(ts)
        except ValueError:
            continue
        if parsed >= window_start and entry.get("command_key") == command_key:
            recent.append(entry)

    duplicate_of = recent[-1]["run_id"] if recent else None
    run_count_window = len(recent) + 1

    new_entry = {
        "run_id": run_id,
        "timestamp": now.isoformat(),
        "command": command,
        "cwd": cwd,
        "status": status,
        "exit_code": exit_code,
        "duration_seconds": round(duration_seconds, 2),
        "command_key": command_key,
        "run_count_window": run_count_window,
        "duplicate_of": duplicate_of,
        "window_minutes": window_minutes,
        "source": source,
    }
    runs.append(new_entry)

    if max_entries > 0 and len(runs) > max_entries:
        runs = runs[-max_entries:]

    data["runs"] = runs
    _save_registry(registry_path, data)

    return TestRunSummary(
        run_id=run_id,
        command=command,
        cwd=cwd,
        status=status,
        exit_code=exit_code,
        duration_seconds=round(duration_seconds, 2),
        command_key=command_key,
        run_count_window=run_count_window,
        duplicate_of=duplicate_of,
        registry_path=str(registry_path),
    )
