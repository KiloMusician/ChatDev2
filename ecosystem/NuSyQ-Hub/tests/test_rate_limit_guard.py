"""Tests for src/utils/rate_limit_guard.py."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone, UTC
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.rate_limit_guard import RateLimitGuard, get_rate_limit_guard


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def guard(tmp_path: Path) -> RateLimitGuard:
    """RateLimitGuard backed by a temp file so tests don't touch real state."""
    return RateLimitGuard(state_file=tmp_path / "test_rate_limits.json")


# ── TestIsRateLimited ────────────────────────────────────────────────────────


class TestIsRateLimited:
    def test_unknown_agent_not_limited(self, guard: RateLimitGuard) -> None:
        assert not guard.is_rate_limited("unknown_agent")

    def test_agent_within_window_is_limited(self, guard: RateLimitGuard) -> None:
        guard.mark_rate_limited("codex", duration_hours=72)
        assert guard.is_rate_limited("codex")

    def test_expired_entry_not_limited(self, guard: RateLimitGuard, tmp_path: Path) -> None:
        # Write an already-expired entry
        state_file = tmp_path / "test_rate_limits.json"
        past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        state_file.write_text(json.dumps({"codex": {"until": past}}), encoding="utf-8")
        assert not guard.is_rate_limited("codex")

    def test_lookup_is_case_insensitive(self, guard: RateLimitGuard) -> None:
        guard.mark_rate_limited("Codex", duration_hours=1)
        assert guard.is_rate_limited("CODEX")
        assert guard.is_rate_limited("codex")

    def test_malformed_entry_not_limited(self, guard: RateLimitGuard, tmp_path: Path) -> None:
        state_file = tmp_path / "test_rate_limits.json"
        state_file.write_text(json.dumps({"codex": {"until": "not-a-date"}}), encoding="utf-8")
        assert not guard.is_rate_limited("codex")

    def test_naive_datetime_treated_as_utc(self, guard: RateLimitGuard, tmp_path: Path) -> None:
        # Naive ISO string (no tz info) should be handled without raising
        state_file = tmp_path / "test_rate_limits.json"
        future_naive = (datetime.now(UTC) + timedelta(hours=2)).replace(tzinfo=None).isoformat()
        state_file.write_text(json.dumps({"codex": {"until": future_naive}}), encoding="utf-8")
        # Should detect as limited (naive treated as UTC)
        assert guard.is_rate_limited("codex")


# ── TestMarkRateLimited ──────────────────────────────────────────────────────


class TestMarkRateLimited:
    def test_mark_creates_entry(self, guard: RateLimitGuard) -> None:
        guard.mark_rate_limited("ollama", duration_hours=2)
        assert guard.is_rate_limited("ollama")

    def test_mark_stores_reason(self, guard: RateLimitGuard) -> None:
        guard.mark_rate_limited("ollama", duration_hours=1, reason="test_reason")
        agents = guard.get_limited_agents()
        entry = next(a for a in agents if a["agent"] == "ollama")
        assert entry["reason"] == "test_reason"

    def test_default_reason(self, guard: RateLimitGuard) -> None:
        guard.mark_rate_limited("ollama", duration_hours=1)
        agents = guard.get_limited_agents()
        entry = next(a for a in agents if a["agent"] == "ollama")
        assert entry["reason"] == "rate_limit_detected"

    def test_overwrite_existing_entry(self, guard: RateLimitGuard) -> None:
        guard.mark_rate_limited("ollama", duration_hours=1, reason="first")
        guard.mark_rate_limited("ollama", duration_hours=48, reason="second")
        agents = guard.get_limited_agents()
        entry = next(a for a in agents if a["agent"] == "ollama")
        assert entry["reason"] == "second"
        assert entry["duration_hours"] == 48


# ── TestClearRateLimited ─────────────────────────────────────────────────────


class TestClearRateLimited:
    def test_clear_removes_entry(self, guard: RateLimitGuard) -> None:
        guard.mark_rate_limited("codex", duration_hours=72)
        result = guard.clear_rate_limit("codex")
        assert result is True
        assert not guard.is_rate_limited("codex")

    def test_clear_nonexistent_returns_false(self, guard: RateLimitGuard) -> None:
        result = guard.clear_rate_limit("nonexistent")
        assert result is False

    def test_clear_case_insensitive(self, guard: RateLimitGuard) -> None:
        guard.mark_rate_limited("Codex", duration_hours=1)
        assert guard.clear_rate_limit("CODEX") is True
        assert not guard.is_rate_limited("codex")


# ── TestGetLimitedAgents ─────────────────────────────────────────────────────


class TestGetLimitedAgents:
    def test_returns_only_active(self, guard: RateLimitGuard) -> None:
        guard.mark_rate_limited("active_agent", duration_hours=2)
        guard.mark_rate_limited("soon_expired", duration_hours=0)  # 0h = already past
        # Overwrite the expired entry directly in the state file
        state = guard._load()
        past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        state["soon_expired"] = {**state.get("soon_expired", {}), "until": past}
        guard._save(state)
        active = guard.get_limited_agents()
        names = [e["agent"] for e in active]
        assert "active_agent" in names
        assert "soon_expired" not in names

    def test_prunes_expired_entries_from_file(self, guard: RateLimitGuard, tmp_path: Path) -> None:
        state_file = tmp_path / "test_rate_limits.json"
        now = datetime.now(UTC)
        state = {
            "expired_agent": {"until": (now - timedelta(hours=1)).isoformat()},
        }
        state_file.write_text(json.dumps(state), encoding="utf-8")
        guard.get_limited_agents()
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert "expired_agent" not in remaining

    def test_includes_remaining_hours(self, guard: RateLimitGuard) -> None:
        guard.mark_rate_limited("codex", duration_hours=10)
        agents = guard.get_limited_agents()
        entry = next(a for a in agents if a["agent"] == "codex")
        assert "remaining_hours" in entry
        assert entry["remaining_hours"] > 0

    def test_malformed_entry_pruned(self, guard: RateLimitGuard, tmp_path: Path) -> None:
        state_file = tmp_path / "test_rate_limits.json"
        state_file.write_text(json.dumps({"bad": {"until": "not-a-date"}}), encoding="utf-8")
        active = guard.get_limited_agents()
        assert active == []


# ── TestStatusSummary ────────────────────────────────────────────────────────


class TestStatusSummary:
    def test_summary_includes_agents_list(self, guard: RateLimitGuard) -> None:
        guard.mark_rate_limited("codex", duration_hours=72)
        summary = guard.status_summary()
        assert "rate_limited_agents" in summary
        assert "codex" in summary["rate_limited_agents"]
        assert "details" in summary
        assert "state_file" in summary

    def test_empty_when_no_limits(self, guard: RateLimitGuard) -> None:
        summary = guard.status_summary()
        assert summary["rate_limited_agents"] == []


# ── TestLoadSave ─────────────────────────────────────────────────────────────


class TestLoadSave:
    def test_load_missing_file_returns_empty(self, tmp_path: Path) -> None:
        g = RateLimitGuard(state_file=tmp_path / "nonexistent.json")
        assert g._load() == {}

    def test_load_corrupt_json_returns_empty(self, tmp_path: Path) -> None:
        state_file = tmp_path / "corrupt.json"
        state_file.write_text("not json {{", encoding="utf-8")
        g = RateLimitGuard(state_file=state_file)
        assert g._load() == {}

    def test_load_non_dict_returns_empty(self, tmp_path: Path) -> None:
        state_file = tmp_path / "list.json"
        state_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        g = RateLimitGuard(state_file=state_file)
        assert g._load() == {}

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c" / "limits.json"
        g = RateLimitGuard(state_file=nested)
        g.mark_rate_limited("x", duration_hours=1)
        assert nested.exists()

    def test_save_oserror_does_not_raise(self, tmp_path: Path) -> None:
        g = RateLimitGuard(state_file=tmp_path / "limits.json")
        with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
            g._save({"x": {}})  # should not raise


# ── TestEnvVarOverride ───────────────────────────────────────────────────────


class TestEnvVarOverride:
    def test_env_var_overrides_state_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        custom = tmp_path / "custom_limits.json"
        monkeypatch.setenv("NUSYQ_RATE_LIMIT_STATE_FILE", str(custom))
        g = RateLimitGuard()
        assert g._state_file == custom


# ── TestSingleton ────────────────────────────────────────────────────────────


class TestSingleton:
    def test_get_rate_limit_guard_returns_same_instance(self) -> None:
        import src.utils.rate_limit_guard as mod
        # Reset singleton so test is deterministic
        mod._guard = None
        g1 = get_rate_limit_guard()
        g2 = get_rate_limit_guard()
        assert g1 is g2
        mod._guard = None  # clean up
