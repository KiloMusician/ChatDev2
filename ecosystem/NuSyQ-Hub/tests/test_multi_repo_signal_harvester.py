import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest
import scripts.multi_repo_signal_harvester as harvester


def test_collect_repo_signals_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent"
    signals = harvester._collect_repo_signals(missing)
    assert signals["error"] == "path missing"
    assert signals["path"] == str(missing)


def test_collect_repo_signals_uses_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    recorded_calls: list[tuple[Iterable[str], Path]] = []

    def fake_run(cmd: Iterable[str], cwd: Path) -> tuple[int, str, str]:
        recorded_calls.append((tuple(cmd), cwd))
        if "ruff" in cmd:
            return 0, "", ""
        return 0, "ok", ""

    monkeypatch.setattr(harvester, "_run", fake_run)

    signals = harvester._collect_repo_signals(repo)

    assert signals["lint_command"].startswith("ruff")
    assert signals["lint_failed"] is False
    assert any("git" in call[0][0] for call in recorded_calls)


def test_main_writes_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()

    def fake_default_repos():
        return [("fake", fake_repo)]

    def fake_collect(path: Path) -> dict[str, Any]:
        return {"path": str(path), "git_head": "deadbeef", "lint_errors_count": 0}

    monkeypatch.setattr(harvester, "_default_repos", fake_default_repos)
    monkeypatch.setattr(harvester, "_collect_repo_signals", fake_collect)

    argv_backup = sys.argv[:]
    sys.argv = [
        "harvest",
        "--quiet",
        "--output",
        str(tmp_path / "out.json"),
    ]

    try:
        exit_code = harvester.main()
    finally:
        sys.argv = argv_backup

    assert exit_code == 0
    out_file = tmp_path / "out.json"
    assert out_file.exists()
    report = json.loads(out_file.read_text())
    assert report["summary"]["total_repos"] == 1
    assert "fake" in report["repos"]
