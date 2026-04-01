#!/usr/bin/env python3
"""Tests for Culture Ship strategic quest bridge triage and proof wiring."""

from __future__ import annotations

import json

from src.orchestration.culture_ship_quest_bridge import (
    journal_strategic_decision_as_quest,
    triage_latest_culture_ship_cycle,
)


def test_journal_adds_owner_and_proof_checks(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".github").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".github" / "CODEOWNERS").write_text(
        "* @DefaultOwner\n/src/main.py @MainOwner\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "Rosetta_Quest_System").mkdir(parents=True, exist_ok=True)

    quest_id = journal_strategic_decision_as_quest(
        {
            "decision": "Address correctness: timeout mismatch in async wrapper",
            "category": "correctness",
            "severity": "high",
            "priority": 8,
            "rationale": "High-severity typing inconsistency",
            "affected_files": ["src/main.py"],
            "action_plan": ["Fix timeout parameter type mismatch"],
        }
    )

    quests = json.loads(
        (tmp_path / "src" / "Rosetta_Quest_System" / "quests.json").read_text(encoding="utf-8")
    )
    quest = next(q for q in quests if q["id"] == quest_id)
    assert quest["owner"] == "@MainOwner"
    assert isinstance(quest.get("proof_of_fix_checks"), list)
    assert any("mypy" in check["command"] for check in quest["proof_of_fix_checks"])


def test_triage_prioritizes_architecture_then_correctness(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".github").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".github" / "CODEOWNERS").write_text("* @KiloMusician\n", encoding="utf-8")
    (tmp_path / "src" / "Rosetta_Quest_System").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "Rosetta_Quest_System" / "quests.json").write_text("[]", encoding="utf-8")
    (tmp_path / "state").mkdir(parents=True, exist_ok=True)

    history = {
        "cycles": [
            {
                "timestamp": "2026-02-17T13:08:48",
                "strategic_decisions": [
                    {
                        "decision": "Address quality: lint backlog",
                        "category": "quality",
                        "severity": "medium",
                        "priority": 5,
                        "action_plan": ["Run ruff --fix"],
                    },
                    {
                        "decision": "Address correctness: timeout/type mismatches",
                        "category": "correctness",
                        "severity": "high",
                        "priority": 8,
                        "action_plan": ["Fix timeout annotations"],
                    },
                    {
                        "decision": "Address architecture: integrate culture ship",
                        "category": "architecture",
                        "severity": "critical",
                        "priority": 10,
                        "action_plan": ["Wire orchestrator integration"],
                    },
                    {
                        "decision": "Address efficiency: optimize scans",
                        "category": "efficiency",
                        "severity": "low",
                        "priority": 2,
                        "action_plan": ["Reduce redundant scans"],
                    },
                ],
            }
        ]
    }
    (tmp_path / "state" / "culture_ship_healing_history.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8"
    )

    payload = triage_latest_culture_ship_cycle()
    assert payload["ticket_count"] == 4
    categories = [ticket["category"] for ticket in payload["tickets"]]
    assert categories[:2] == ["architecture", "correctness"]

    quest_log = tmp_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    entries = [
        json.loads(line) for line in quest_log.read_text(encoding="utf-8").splitlines() if line
    ]
    triage_events = [e for e in entries if e.get("event") == "culture_ship_ticket_triaged"]
    assert len(triage_events) == 4
    assert all(event["details"].get("proof_of_fix_checks") for event in triage_events)
