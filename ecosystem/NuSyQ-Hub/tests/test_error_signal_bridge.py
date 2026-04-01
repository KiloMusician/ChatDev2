"""Regression tests for error_signal_bridge schema/path compatibility."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from src.orchestration import error_signal_bridge


def test_parse_error_report_falls_back_to_unified_report(monkeypatch, tmp_path: Path) -> None:
    """Bridge parser should accept unified_error_report_latest when ground truth file is absent."""
    monkeypatch.setattr(error_signal_bridge, "ROOT", tmp_path)
    diagnostics = tmp_path / "docs" / "Reports" / "diagnostics"
    diagnostics.mkdir(parents=True, exist_ok=True)
    (diagnostics / "unified_error_report_latest.json").write_text(
        json.dumps(
            {
                "diagnostic_details": [
                    {
                        "source": "ruff",
                        "severity": "warning",
                        "file_path": "src/main.py",
                        "message": "F401 imported but unused",
                    },
                    {
                        "source": "ruff",
                        "severity": "warning",
                        "file_path": "src/utils.py",
                        "message": "Potential issue",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    groups = error_signal_bridge.parse_error_report(tmp_path / "state" / "ground_truth_errors.json")
    assert len(groups) == 1
    assert groups[0].category == "ruff"
    assert groups[0].count == 2
    assert groups[0].severity.value == "medium"


def test_run_error_scan_returns_unified_report_when_scanner_missing(
    monkeypatch, tmp_path: Path
) -> None:
    """Scanner fallback should use unified_error_report_latest when scanner script is unavailable."""
    monkeypatch.setattr(error_signal_bridge, "ROOT", tmp_path)
    diagnostics = tmp_path / "docs" / "Reports" / "diagnostics"
    diagnostics.mkdir(parents=True, exist_ok=True)
    fallback = diagnostics / "unified_error_report_latest.json"
    fallback.write_text("{}", encoding="utf-8")

    report_path = asyncio.run(error_signal_bridge.run_error_scan())
    assert report_path == fallback


def test_post_signals_uses_save_board_fallback(monkeypatch) -> None:
    """Posting should succeed when GuildBoard only exposes _save_board()."""
    import src.guild.guild_board as guild_board_module

    saved = {"value": False}

    class FakeBoard:
        async def add_signal(
            self, signal_type: str, severity: str, message: str, context: dict
        ) -> None:
            return None

        async def _save_board(self) -> None:
            saved["value"] = True

    monkeypatch.setattr(guild_board_module, "GuildBoard", FakeBoard)
    signals = [
        error_signal_bridge.SignalToPost(
            signal_type="error",
            severity="high",
            message="Found 10 ruff errors",
            context={"error_category": "ruff", "error_count": 10},
        )
    ]

    result = asyncio.run(error_signal_bridge.post_signals_to_guild_board(signals))
    assert result["success"] is True
    assert result["status"] == "success"
    assert result["signals_posted"] == 1
    assert saved["value"] is True


def test_post_signals_test_mode_contract() -> None:
    """Test mode should emit a successful test response envelope."""
    signals = [
        error_signal_bridge.SignalToPost(
            signal_type="error",
            severity="low",
            message="Dry run signal",
            context={"error_category": "dryrun", "error_count": 1},
        )
    ]
    result = asyncio.run(error_signal_bridge.post_signals_to_guild_board(signals, test_mode=True))
    assert result["success"] is True
    assert result["status"] == "test"
    assert result["signals_posted"] == 1


def test_post_signals_partial_contract(monkeypatch) -> None:
    """Partial posting should return status=partial with success=False."""
    import src.guild.guild_board as guild_board_module

    class FakeBoard:
        async def add_signal(
            self, signal_type: str, severity: str, message: str, context: dict
        ) -> None:
            if message == "fail me":
                raise RuntimeError("simulated failure")

        async def save_state(self) -> None:
            return None

    monkeypatch.setattr(guild_board_module, "GuildBoard", FakeBoard)
    signals = [
        error_signal_bridge.SignalToPost(
            signal_type="error",
            severity="high",
            message="ok",
            context={"error_category": "ruff", "error_count": 10},
        ),
        error_signal_bridge.SignalToPost(
            signal_type="error",
            severity="high",
            message="fail me",
            context={"error_category": "mypy", "error_count": 5},
        ),
    ]

    result = asyncio.run(error_signal_bridge.post_signals_to_guild_board(signals))
    assert result["success"] is False
    assert result["status"] == "partial"
    assert result["signals_posted"] == 1
    assert result["signals_total"] == 2
