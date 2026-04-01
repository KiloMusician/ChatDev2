"""Tests for xi_nusyq/typestates.py, system/safety.py, and nusyq_spine/state.py."""

import json
from pathlib import Path
from unittest.mock import patch

# ── xi_nusyq.typestates ────────────────────────────────────────────────────

from src.xi_nusyq.typestates import Frame, Bound, Walked, Closed, bind, walk, seal, reopen


def test_bind_frame_to_bound():
    f = Frame(value=42)
    b = bind(f)
    assert isinstance(b, Bound)
    assert b.value == 42


def test_walk_bound_to_walked():
    b = Bound(value="hello")
    w = walk(b)
    assert isinstance(w, Walked)
    assert w.value == "hello"


def test_seal_walked_to_closed():
    w = Walked(value=[1, 2, 3])
    c = seal(w)
    assert isinstance(c, Closed)
    assert c.value == [1, 2, 3]


def test_reopen_closed_to_bound():
    c = Closed(value={"key": "val"})
    b = reopen(c)
    assert isinstance(b, Bound)
    assert b.value == {"key": "val"}


def test_full_typestate_chain():
    f = Frame(value=99)
    result = reopen(seal(walk(bind(f))))
    assert result.value == 99


# ── system.safety ──────────────────────────────────────────────────────────

from src.system.safety import vote_responses, diff_responses


def test_vote_responses_picks_first_non_error():
    responses = [
        {"error": "failed"},
        {"result": "ok", "score": 0.9},
        {"result": "also ok"},
    ]
    voted = vote_responses(responses)
    assert voted["winner"]["result"] == "ok"
    assert len(voted["votes"]) == 3


def test_vote_responses_empty_list():
    result = vote_responses([])
    assert result["winner"] == {}


def test_vote_responses_all_errors():
    responses = [{"error": "a"}, {"error": "b"}]
    voted = vote_responses(responses)
    # Falls back to first element
    assert voted["winner"]["error"] == "a"


def test_diff_responses_same():
    d = diff_responses("hello", "hello")
    assert d["same"] is True


def test_diff_responses_different():
    d = diff_responses("abc", "xyz")
    assert d["same"] is False
    assert d["len_a"] == 3
    assert d["len_b"] == 3


def test_diff_responses_strips_whitespace():
    d = diff_responses("  hi  ", "hi")
    assert d["same"] is True


# ── nusyq_spine.state ──────────────────────────────────────────────────────

import src.nusyq_spine.state as _state_mod


def test_snapshot_state_returns_dict(tmp_path):
    with patch.object(_state_mod, "STATE_PATH", tmp_path / "state.json"):
        result = _state_mod.snapshot_state()
    assert isinstance(result, dict)
    assert result["status"] == "ok"
    assert "timestamp" in result


def test_snapshot_state_with_extra(tmp_path):
    with patch.object(_state_mod, "STATE_PATH", tmp_path / "state.json"):
        result = _state_mod.snapshot_state(extra={"mode": "test"})
    assert result["mode"] == "test"


def test_read_state_after_snapshot(tmp_path):
    with patch.object(_state_mod, "STATE_PATH", tmp_path / "state.json"):
        _state_mod.snapshot_state(extra={"foo": "bar"})
        data = _state_mod.read_state()
    assert data["foo"] == "bar"


def test_read_state_missing_file(tmp_path):
    with patch.object(_state_mod, "STATE_PATH", tmp_path / "nonexistent.json"):
        result = _state_mod.read_state()
    assert result == {}
