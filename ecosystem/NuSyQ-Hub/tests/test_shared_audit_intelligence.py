"""Tests for audit-intelligence helpers used by status surfaces."""

from __future__ import annotations

from scripts.nusyq_actions.shared import collect_audit_intelligence, format_audit_intelligence_lines


def test_collect_audit_intelligence_reads_docs_metadata(tmp_path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "SYSTEM_AUDIT_2026-02-25.md").write_text("# audit\n", encoding="utf-8")
    (docs / "ROSETTA_STONE.md").write_text("# rosetta\n", encoding="utf-8")
    (docs / "AGENT_TUTORIAL.md").write_text("# tutorial\n", encoding="utf-8")
    (docs / "custom_audit.md").write_text("# custom\n", encoding="utf-8")

    payload = collect_audit_intelligence(tmp_path, include_sessions=False, max_audits=3)

    assert payload["status"] == "ok"
    assert isinstance(payload.get("canonical"), list)
    assert any(
        isinstance(item, dict) and item.get("path") == "docs/ROSETTA_STONE.md"
        for item in payload["canonical"]
    )
    lines = format_audit_intelligence_lines(payload, max_lines=3)
    assert lines


def test_collect_audit_intelligence_handles_missing_docs(tmp_path) -> None:
    payload = collect_audit_intelligence(tmp_path)
    assert payload["status"] == "unavailable"
