"""Regression tests for suggest action quest signal transparency."""

from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timedelta, timezone, UTC
from pathlib import Path
from types import SimpleNamespace

from scripts.nusyq_actions.work_task_actions import collect_quest_signal, handle_suggest


def _write_quest_log(hub_path: Path, rows: list[dict]) -> None:
    quest_log = hub_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    quest_log.parent.mkdir(parents=True, exist_ok=True)
    quest_log.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _install_fake_guild_board(monkeypatch) -> None:
    fake_module = types.ModuleType("src.guild.guild_board")

    class DummyGuildBoard:
        def post_message(self, *_args, **_kwargs) -> None:
            return None

    fake_module.GuildBoard = DummyGuildBoard
    monkeypatch.setitem(sys.modules, "src.guild.guild_board", fake_module)


def test_collect_quest_signal_tracks_recent_and_stale(monkeypatch, tmp_path: Path) -> None:
    now = datetime.now(UTC)
    _write_quest_log(
        tmp_path,
        [
            {
                "timestamp": (now - timedelta(days=35)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-old", "title": "Old Active", "status": "active"},
            },
            {
                "timestamp": (now - timedelta(days=2)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-new", "title": "Recent Active", "status": "active"},
            },
            {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-pending", "title": "Recent Pending", "status": "pending"},
            },
        ],
    )
    monkeypatch.setenv("NUSYQ_SUGGEST_QUEST_WINDOW_DAYS", "14")

    signal = collect_quest_signal(tmp_path)
    assert signal["available"] is True
    assert signal["actionable_recent_count"] == 2
    assert signal["stale_backlog_count"] == 1
    assert "Recent Active" in signal["active_sample"]
    assert "Recent Pending" in signal["pending_sample"]


def test_handle_suggest_json_includes_quest_signal(monkeypatch, tmp_path: Path, capsys) -> None:
    _install_fake_guild_board(monkeypatch)

    now = datetime.now(UTC)
    _write_quest_log(
        tmp_path,
        [
            {
                "timestamp": (now - timedelta(days=30)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-old", "title": "Stale Active Quest", "status": "active"},
            },
            {
                "timestamp": (now - timedelta(days=2)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-recent", "title": "Recent Active Quest", "status": "active"},
            },
            {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "event": "add_quest",
                "details": {
                    "id": "q-pending",
                    "title": "Recent Pending Quest",
                    "status": "pending",
                },
            },
        ],
    )
    monkeypatch.setenv("NUSYQ_SUGGEST_QUEST_WINDOW_DAYS", "14")

    paths = SimpleNamespace(nusyq_hub=tmp_path)

    def fake_git_snapshot(_repo_name: str, _repo_path: Path):
        return SimpleNamespace(dirty="CLEAN")

    def fake_read_quest_log(_hub_path: Path):
        return SimpleNamespace(last_nonempty_line="")

    def fake_run(cmd, cwd=None):
        if cmd[:3] == ["python", "-m", "pytest"]:
            return 0, "", ""
        return 0, "", ""

    rc = handle_suggest(
        paths,
        git_snapshot=fake_git_snapshot,
        read_quest_log=fake_read_quest_log,
        run=fake_run,
        json_mode=True,
    )
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "suggest"
    assert payload["quest_signal"]["actionable_recent_count"] == 2
    assert payload["quest_signal"]["stale_backlog_count"] == 1
    assert any("CONTINUE QUEST" in item for item in payload["suggestions"])
    assert any("TRIAGE QUEST BACKLOG" in item for item in payload["suggestions"])


def test_handle_suggest_does_not_emit_no_actionable_when_recent_exists(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    _install_fake_guild_board(monkeypatch)

    now = datetime.now(UTC)
    _write_quest_log(
        tmp_path,
        [
            {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-recent", "title": "Fresh Quest", "status": "active"},
            }
        ],
    )
    monkeypatch.setenv("NUSYQ_SUGGEST_QUEST_WINDOW_DAYS", "14")

    paths = SimpleNamespace(nusyq_hub=tmp_path)

    def fake_git_snapshot(_repo_name: str, _repo_path: Path):
        return SimpleNamespace(dirty="CLEAN")

    def fake_read_quest_log(_hub_path: Path):
        return SimpleNamespace(last_nonempty_line="")

    def fake_run(cmd, cwd=None):
        if cmd[:3] == ["python", "-m", "pytest"]:
            return 0, "", ""
        return 0, "", ""

    rc = handle_suggest(
        paths,
        git_snapshot=fake_git_snapshot,
        read_quest_log=fake_read_quest_log,
        run=fake_run,
        json_mode=True,
    )
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["quest_signal"]["actionable_recent_count"] == 1
    assert not any("No actionable quest signal" in item for item in payload["suggestions"])


def test_handle_suggest_surfaces_system_complete_blockers(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    _install_fake_guild_board(monkeypatch)
    now = datetime.now(UTC)
    _write_quest_log(
        tmp_path,
        [
            {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-recent", "title": "Fresh Quest", "status": "active"},
            }
        ],
    )

    reports_dir = tmp_path / "state" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "system_complete_gate_latest.json").write_text(
        json.dumps(
            {
                "action": "system_complete",
                "status": "failed",
                "overall_pass": False,
                "checks": [
                    {
                        "name": "chatdev_e2e",
                        "passed": False,
                        "cmd": ["python", "scripts/e2e_chatdev_mcp_test.py"],
                    },
                    {
                        "name": "lint_threshold",
                        "passed": False,
                        "skipped": True,
                        "reason": "budget_exceeded",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    paths = SimpleNamespace(nusyq_hub=tmp_path)

    def fake_git_snapshot(_repo_name: str, _repo_path: Path):
        return SimpleNamespace(dirty="CLEAN")

    def fake_read_quest_log(_hub_path: Path):
        return SimpleNamespace(last_nonempty_line="")

    def fake_run(cmd, cwd=None):
        return 0, "", ""

    rc = handle_suggest(
        paths,
        git_snapshot=fake_git_snapshot,
        read_quest_log=fake_read_quest_log,
        run=fake_run,
        json_mode=True,
    )
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["signals"]["system_complete"]["failed_count"] == 1
    assert payload["blockers"][0]["name"] == "chatdev_e2e"
    assert any("UNBLOCK CHATDEV_E2E" in item for item in payload["suggestions"])


def test_handle_suggest_writes_latest_and_history_artifacts(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    _install_fake_guild_board(monkeypatch)
    now = datetime.now(UTC)
    _write_quest_log(
        tmp_path,
        [
            {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-recent", "title": "Fresh Quest", "status": "active"},
            }
        ],
    )

    paths = SimpleNamespace(nusyq_hub=tmp_path)

    def fake_git_snapshot(_repo_name: str, _repo_path: Path):
        return SimpleNamespace(dirty="CLEAN")

    def fake_read_quest_log(_hub_path: Path):
        return SimpleNamespace(last_nonempty_line="")

    def fake_run(cmd, cwd=None):
        return 0, "", ""

    rc = handle_suggest(
        paths,
        git_snapshot=fake_git_snapshot,
        read_quest_log=fake_read_quest_log,
        run=fake_run,
        json_mode=True,
    )
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    report_file = Path(payload["report_file"])
    history_file = Path(payload["history_file"])
    assert report_file.exists()
    assert history_file.exists()


def test_handle_suggest_prefers_queue_recommended_command(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    _install_fake_guild_board(monkeypatch)

    now = datetime.now(UTC)
    _write_quest_log(
        tmp_path,
        [
            {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "event": "add_quest",
                "details": {"id": "q-recent", "title": "Fresh Quest", "status": "active"},
            }
        ],
    )

    queue_file = tmp_path / "state" / "next_action_queue.json"
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    queue_file.write_text(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "total_actions": 1,
                "actions": [
                    {
                        "title": "Unblock custom gate",
                        "type": "fix_error",
                        "context": {"recommended_command": "python scripts/custom_fix.py"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    paths = SimpleNamespace(nusyq_hub=tmp_path)

    def fake_git_snapshot(_repo_name: str, _repo_path: Path):
        return SimpleNamespace(dirty="CLEAN")

    def fake_read_quest_log(_hub_path: Path):
        return SimpleNamespace(last_nonempty_line="")

    def fake_run(cmd, cwd=None):
        return 0, "", ""

    rc = handle_suggest(
        paths,
        git_snapshot=fake_git_snapshot,
        read_quest_log=fake_read_quest_log,
        run=fake_run,
        json_mode=True,
    )
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["signals"]["next_action"]["available"] is True
    assert any("python scripts/custom_fix.py" in item for item in payload["suggestions"])
