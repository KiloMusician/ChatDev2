"""Tests for startup spine probe gating in start_nusyq."""

from __future__ import annotations

import scripts.start_nusyq as start_nusyq


def test_should_skip_spine_startup_for_lightweight_search(monkeypatch) -> None:
    monkeypatch.delenv("NUSYQ_SPINE_STARTUP", raising=False)
    assert start_nusyq._should_skip_spine_startup("search", ["search", "index-health"]) is True


def test_should_not_skip_spine_startup_for_heavy_action_by_default(monkeypatch) -> None:
    monkeypatch.delenv("NUSYQ_SPINE_STARTUP", raising=False)
    assert start_nusyq._should_skip_spine_startup("generate", ["generate", "x"]) is False


def test_spine_startup_mode_env_override(monkeypatch) -> None:
    monkeypatch.setenv("NUSYQ_SPINE_STARTUP", "never")
    assert start_nusyq._should_skip_spine_startup("generate", ["generate", "x"]) is True

    monkeypatch.setenv("NUSYQ_SPINE_STARTUP", "always")
    assert start_nusyq._should_skip_spine_startup("search", ["search", "index-health"]) is False
