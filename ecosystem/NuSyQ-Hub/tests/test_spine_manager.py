from __future__ import annotations

import json
from pathlib import Path

from src.spine.spine_manager import export_spine_health, initialize_spine


def _prepare_state_dir(base: Path) -> Path:
    reports = base / "state" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    return reports


def _write_current_state(reports: Path, lines: list[str]) -> None:
    current = reports / "current_state.md"
    current.write_text("\n".join(lines), encoding="utf-8")


def _write_lifecycle(reports: Path, payload: list[dict[str, str]]) -> None:
    lifecycle_file = reports / "lifecycle_catalog_latest.json"
    lifecycle_file.write_text(json.dumps(payload), encoding="utf-8")


def test_initialize_spine_reads_signals(tmp_path: Path) -> None:
    repo_root = tmp_path / "hub"
    reports = _prepare_state_dir(repo_root)
    _write_current_state(reports, ["line1", "line2", "line3", "line4", "line5"])
    _write_lifecycle(
        reports,
        [
            {"name": "Task Alpha", "summary": "first task"},
            {"name": "Task Beta", "summary": "second task"},
        ],
    )

    health = initialize_spine(repo_root=repo_root, refresh=True)

    assert health.status == "GREEN"
    assert health.signals["current_state_lines"] == 4
    assert health.signals["lifecycle_entries"] == 2
    assert health.current_state_excerpt[0] == "line1"
    assert "Task Alpha" in health.lifecycle_entries[0]


def test_initialize_spine_refresh_rebuilds_snapshot(tmp_path: Path) -> None:
    repo_root = tmp_path / "hub"
    reports = _prepare_state_dir(repo_root)
    _write_current_state(reports, ["first"])
    health_first = initialize_spine(repo_root=repo_root, refresh=True)

    _write_current_state(reports, ["second", "line"])
    health_second = initialize_spine(repo_root=repo_root, refresh=True)

    assert health_first.current_state_excerpt != health_second.current_state_excerpt
    assert health_second.signals["current_state_lines"] == 2


def test_export_spine_health_produces_snapshot(tmp_path: Path) -> None:
    repo_root = tmp_path / "hub"
    reports = _prepare_state_dir(repo_root)
    _write_current_state(reports, ["alpha", "beta"])
    _write_lifecycle(reports, [{"name": "Pulse", "summary": "ready"}])
    snapshot_path = export_spine_health(repo_root=repo_root, refresh=True)

    assert snapshot_path.exists()
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert payload["status"] in {"GREEN", "YELLOW", "RED"}
    assert "current_state_excerpt" in payload
    assert "lifecycle_entries" in payload
    assert "signals" in payload
