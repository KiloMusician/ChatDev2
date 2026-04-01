"""Regression tests for guild action handlers."""

from __future__ import annotations

from scripts.nusyq_actions import guild_actions


def test_handle_log_quest_success_with_json_details(monkeypatch, capsys) -> None:
    logged: list[tuple[str, dict]] = []
    receipts: list[dict] = []

    def fake_log_event(event: str, details: dict) -> None:
        logged.append((event, details))

    def fake_receipt(action_name: str, exit_code: int, metadata: dict | None = None) -> dict:
        payload = {"action": action_name, "exit_code": exit_code, "metadata": metadata or {}}
        receipts.append(payload)
        return payload

    monkeypatch.setattr("src.Rosetta_Quest_System.quest_engine.log_event", fake_log_event)
    monkeypatch.setattr(guild_actions, "emit_action_receipt", fake_receipt)

    rc = guild_actions.handle_log_quest(
        ["log_quest", "quest_started", '{"quest_id":"q-123","status":"active"}']
    )

    assert rc == 0
    assert logged == [("quest_started", {"quest_id": "q-123", "status": "active"})]
    assert receipts[-1]["action"] == "log_quest"
    assert receipts[-1]["exit_code"] == 0
    assert receipts[-1]["metadata"]["event"] == "quest_started"
    assert "Logged quest event" in capsys.readouterr().out


def test_handle_log_quest_non_json_falls_back_to_message(monkeypatch) -> None:
    logged: list[tuple[str, dict]] = []
    receipts: list[dict] = []

    def fake_log_event(event: str, details: dict) -> None:
        logged.append((event, details))

    def fake_receipt(action_name: str, exit_code: int, metadata: dict | None = None) -> dict:
        payload = {"action": action_name, "exit_code": exit_code, "metadata": metadata or {}}
        receipts.append(payload)
        return payload

    monkeypatch.setattr("src.Rosetta_Quest_System.quest_engine.log_event", fake_log_event)
    monkeypatch.setattr(guild_actions, "emit_action_receipt", fake_receipt)

    rc = guild_actions.handle_log_quest(["log_quest", "note", "plain text details"])

    assert rc == 0
    assert logged == [("note", {"message": "plain text details"})]
    assert receipts[-1]["exit_code"] == 0


def test_handle_log_quest_missing_args_emits_error_receipt(monkeypatch, capsys) -> None:
    receipts: list[dict] = []

    def fake_receipt(action_name: str, exit_code: int, metadata: dict | None = None) -> dict:
        payload = {"action": action_name, "exit_code": exit_code, "metadata": metadata or {}}
        receipts.append(payload)
        return payload

    monkeypatch.setattr(guild_actions, "emit_action_receipt", fake_receipt)

    rc = guild_actions.handle_log_quest(["log_quest"])

    assert rc == 1
    assert receipts[-1]["action"] == "log_quest"
    assert receipts[-1]["exit_code"] == 1
    assert receipts[-1]["metadata"]["error"] == "missing_args"
    assert "Usage: python start_nusyq.py log_quest" in capsys.readouterr().out


def test_handle_log_quest_import_error_emits_error_receipt(monkeypatch, capsys) -> None:
    receipts: list[dict] = []

    def fake_log_event(event: str, details: dict) -> None:
        raise RuntimeError("boom")

    def fake_receipt(action_name: str, exit_code: int, metadata: dict | None = None) -> dict:
        payload = {"action": action_name, "exit_code": exit_code, "metadata": metadata or {}}
        receipts.append(payload)
        return payload

    monkeypatch.setattr("src.Rosetta_Quest_System.quest_engine.log_event", fake_log_event)
    monkeypatch.setattr(guild_actions, "emit_action_receipt", fake_receipt)

    rc = guild_actions.handle_log_quest(["log_quest", "quest_failed", '{"quest_id":"q-404"}'])

    assert rc == 1
    assert receipts[-1]["action"] == "log_quest"
    assert receipts[-1]["exit_code"] == 1
    assert "boom" in receipts[-1]["metadata"]["error"]
    assert "Log quest failed" in capsys.readouterr().out
