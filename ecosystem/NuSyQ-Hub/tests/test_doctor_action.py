"""Regression tests for doctor action artifacts and trend history."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone, UTC
from pathlib import Path
from types import SimpleNamespace

from scripts.nusyq_actions.doctor import handle_doctor


def _write_quest_log(hub_path: Path, rows: list[dict]) -> None:
    quest_log = hub_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    quest_log.parent.mkdir(parents=True, exist_ok=True)
    quest_log.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_doctor_writes_artifacts_and_history(tmp_path, capsys) -> None:
    paths = SimpleNamespace(nusyq_hub=tmp_path)

    def fake_run(cmd, cwd=None, timeout_s=None):
        script = cmd[1] if len(cmd) > 1 else ""
        if script.endswith("quick_system_analyzer.py"):
            return 0, "quick analyzer ok", ""
        if script.endswith("lint_test_check.py"):
            return 1, "", "ruff failed"
        return 0, "", ""

    rc = handle_doctor(paths, fake_run, "health_report.json", json_mode=True)
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "doctor"
    assert payload["status"] == "degraded"
    assert payload["passed_steps"] < payload["total_steps"]
    assert "quest_signal" in payload

    history_file = tmp_path / "state" / "reports" / "doctor_history.jsonl"
    latest_report = tmp_path / "state" / "reports" / "doctor_report_latest.json"
    dashboard_latest = tmp_path / "state" / "reports" / "doctor_dashboard_latest.json"
    assert history_file.exists()
    assert latest_report.exists()
    assert dashboard_latest.exists()

    history_lines = history_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(history_lines) == 1
    history_entry = json.loads(history_lines[0])
    assert history_entry["status"] == "degraded"

    dashboard = json.loads(dashboard_latest.read_text(encoding="utf-8"))
    assert dashboard["history_runs"] == 1
    assert any(item["name"] == "lint_test_diagnostic" for item in dashboard["per_step_trends"])


def test_doctor_dashboard_tracks_trends_across_runs(tmp_path, capsys) -> None:
    paths = SimpleNamespace(nusyq_hub=tmp_path)
    run_count = {"value": 0}

    def fake_run(cmd, cwd=None, timeout_s=None):
        script = cmd[1] if len(cmd) > 1 else ""
        if script.endswith("quick_system_analyzer.py"):
            return 0, "quick analyzer ok", ""
        if script.endswith("lint_test_check.py"):
            run_count["value"] += 1
            if run_count["value"] == 1:
                return 1, "", "ruff failed"
            return 0, "ruff clean", ""
        return 0, "", ""

    handle_doctor(paths, fake_run, "health_report.json", json_mode=True)
    capsys.readouterr()
    handle_doctor(paths, fake_run, "health_report.json", json_mode=True)
    capsys.readouterr()

    dashboard_latest = tmp_path / "state" / "reports" / "doctor_dashboard_latest.json"
    dashboard = json.loads(dashboard_latest.read_text(encoding="utf-8"))
    assert dashboard["history_runs"] == 2

    lint_trend = next(
        item for item in dashboard["per_step_trends"] if item["name"] == "lint_test_diagnostic"
    )
    assert lint_trend["runs"] == 2
    assert lint_trend["last_status"] == "PASS"
    assert lint_trend["recent"][-2:] == ["FAIL", "PASS"]


def test_doctor_json_includes_quest_signal_counts(tmp_path, capsys, monkeypatch) -> None:
    now = datetime.now(UTC)
    _write_quest_log(
        tmp_path,
        [
            {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-recent", "title": "Recent Active", "status": "active"},
            },
            {
                "timestamp": (now - timedelta(days=40)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-stale", "title": "Stale Pending", "status": "pending"},
            },
        ],
    )
    monkeypatch.setenv("NUSYQ_SUGGEST_QUEST_WINDOW_DAYS", "14")

    paths = SimpleNamespace(nusyq_hub=tmp_path)

    def fake_run(cmd, cwd=None, timeout_s=None):
        return 0, "ok", ""

    rc = handle_doctor(paths, fake_run, "health_report.json", json_mode=True)
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    signal = payload["quest_signal"]
    assert signal["actionable_recent_count"] == 1
    assert signal["stale_backlog_count"] == 1


def test_doctor_quick_mode_skips_slow_checks_and_reports_progress(tmp_path, capsys) -> None:
    paths = SimpleNamespace(nusyq_hub=tmp_path)
    invoked_scripts: list[str] = []

    def fake_run(cmd, cwd=None, timeout_s=None):
        script = cmd[1] if len(cmd) > 1 else ""
        invoked_scripts.append(script)
        return 0, "ok", ""

    rc = handle_doctor(
        paths,
        fake_run,
        "health_report.json",
        json_mode=True,
        action_args=["doctor", "--quick"],
    )
    assert rc == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["mode"] == "quick"
    assert payload["options"]["include_system_health"] is False
    assert payload["options"]["include_lint"] is False
    assert payload["options"]["include_analyzer"] is False
    assert any(step["name"] == "system_health" and step.get("skipped") for step in payload["steps"])
    assert any(
        step["name"] == "lint_test_diagnostic" and step.get("skipped") for step in payload["steps"]
    )
    assert any(
        step["name"] == "quick_system_analyzer" and step.get("skipped") for step in payload["steps"]
    )
    assert not any(script.endswith("quick_system_analyzer.py") for script in invoked_scripts)
    assert not any(script.endswith("lint_test_check.py") for script in invoked_scripts)
    assert "[doctor] Mode=quick" in captured.err


def test_doctor_quick_mode_with_analyzer_runs_analyzer(tmp_path, capsys) -> None:
    paths = SimpleNamespace(nusyq_hub=tmp_path)
    invoked_scripts: list[str] = []

    def fake_run(cmd, cwd=None, timeout_s=None):
        script = cmd[1] if len(cmd) > 1 else ""
        invoked_scripts.append(script)
        return 0, "ok", ""

    rc = handle_doctor(
        paths,
        fake_run,
        "health_report.json",
        json_mode=True,
        action_args=["doctor", "--quick", "--with-analyzer"],
    )
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "quick"
    assert payload["options"]["include_analyzer"] is True
    assert any(script.endswith("quick_system_analyzer.py") for script in invoked_scripts)


def test_doctor_budget_enforces_step_skips_and_checkpoint(tmp_path, capsys) -> None:
    paths = SimpleNamespace(nusyq_hub=tmp_path)

    def fake_run(cmd, cwd=None, timeout_s=None):
        script = cmd[1] if len(cmd) > 1 else ""
        if script.endswith("quick_system_analyzer.py"):
            time.sleep(1.1)
            return 0, "quick analyzer ok", ""
        if script.endswith("lint_test_check.py"):
            return 0, "lint ok", ""
        return 0, "", ""

    rc = handle_doctor(
        paths,
        fake_run,
        "health_report.json",
        json_mode=True,
        action_args=["doctor", "--with-analyzer", "--with-lint", "--budget-s=1"],
    )
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "doctor"
    assert payload["options"]["budget_s"] == 1
    assert payload["status"] == "degraded"
    assert payload.get("checkpoint_file", "").endswith("doctor_checkpoint_latest.json")

    lint_step = next(step for step in payload["steps"] if step["name"] == "lint_test_diagnostic")
    assert lint_step.get("skipped") is True
    assert lint_step.get("reason") == "budget_exceeded"

    checkpoint_path = tmp_path / "state" / "reports" / "doctor_checkpoint_latest.json"
    assert checkpoint_path.exists()
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["status"] == "degraded"
    assert checkpoint["completed_checks"] >= 2
