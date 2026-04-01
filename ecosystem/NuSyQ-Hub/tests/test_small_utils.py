"""Tests for small utility modules:
- src/utils/helpers.py
- src/utils/validators.py
- src/system/resilience.py
- src/system/attestation.py
"""

from pathlib import Path
from unittest.mock import patch


# ── helpers ────────────────────────────────────────────────────────────────

from src.utils.helpers import join_path


def test_join_path_two_parts():
    result = join_path("a", "b")
    assert result == Path("a/b")


def test_join_path_single_part():
    result = join_path("hello")
    assert result == Path("hello")


def test_join_path_returns_path_object():
    result = join_path("x", "y", "z")
    assert isinstance(result, Path)


# ── validators ─────────────────────────────────────────────────────────────

from src.utils.validators import is_nonempty_string, is_positive_int, is_dict_with_keys


def test_is_nonempty_string_true():
    assert is_nonempty_string("hello") is True


def test_is_nonempty_string_false_empty():
    assert is_nonempty_string("") is False
    assert is_nonempty_string("   ") is False


def test_is_nonempty_string_false_non_string():
    assert is_nonempty_string(42) is False
    assert is_nonempty_string(None) is False


def test_is_positive_int_true():
    assert is_positive_int(1) is True
    assert is_positive_int(100) is True


def test_is_positive_int_false_zero_and_negative():
    assert is_positive_int(0) is False
    assert is_positive_int(-1) is False


def test_is_positive_int_false_non_int():
    assert is_positive_int(1.5) is False
    assert is_positive_int("1") is False


def test_is_dict_with_keys_true():
    assert is_dict_with_keys({"a": 1, "b": 2}, ["a", "b"]) is True


def test_is_dict_with_keys_false_missing():
    assert is_dict_with_keys({"a": 1}, ["a", "b"]) is False


def test_is_dict_with_keys_false_not_dict():
    assert is_dict_with_keys([1, 2], ["a"]) is False


# ── resilience ─────────────────────────────────────────────────────────────

from src.system.resilience import checkpoint, retry_if_failed, degraded_mode


def test_checkpoint_appends_copy():
    store: list = []
    state = {"step": 1}
    checkpoint(state, store)
    assert len(store) == 1
    assert store[0] == {"step": 1}
    # Modifying original doesn't affect stored copy
    state["step"] = 99
    assert store[0]["step"] == 1


def test_retry_if_failed_true():
    assert retry_if_failed({"error": "oops"}, attempts=1) is True


def test_retry_if_failed_false_no_error():
    assert retry_if_failed({"error": None}, attempts=1) is False
    assert retry_if_failed({}, attempts=1) is False


def test_retry_if_failed_false_no_attempts():
    assert retry_if_failed({"error": "oops"}, attempts=0) is False


def test_degraded_mode_enabled():
    result = degraded_mode(True)
    assert result["degraded"] is True
    assert "note" in result


def test_degraded_mode_disabled():
    result = degraded_mode(False)
    assert result["degraded"] is False


# ── attestation ────────────────────────────────────────────────────────────

from src.system.attestation import attest_manifest


def test_attest_manifest_when_disabled():
    """When attestation_enabled=False, manifest is returned unchanged."""
    with patch("src.system.attestation.is_feature_enabled", return_value=False):
        manifest = {"version": "1.0"}
        result = attest_manifest(manifest)
        assert "attestation" not in result


def test_attest_manifest_when_enabled():
    """When attestation_enabled=True, manifest gets sha256 attestation."""
    with patch("src.system.attestation.is_feature_enabled", return_value=True):
        manifest = {"version": "1.0", "name": "test"}
        result = attest_manifest(manifest)
        assert "attestation" in result
        assert "sha256" in result["attestation"]
        assert len(result["attestation"]["sha256"]) == 64  # SHA-256 hex
