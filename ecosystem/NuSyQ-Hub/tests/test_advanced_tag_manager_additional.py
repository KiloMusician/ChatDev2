"""Tests for AdvancedTagManager (rule-based multi-system tagger)."""

import asyncio
from src.tagging.advanced_tag_manager import AdvancedTagManager


def test_advanced_tag_manager_instantiation(tmp_path):
    """AdvancedTagManager can be instantiated with a custom config path."""
    mgr = AdvancedTagManager(config_path=tmp_path / "rules.json")
    assert mgr is not None


def test_extract_all_tags_returns_expected_keys(tmp_path):
    """extract_all_tags returns dict with all tagger keys."""
    mgr = AdvancedTagManager(config_path=tmp_path / "rules.json")
    result = asyncio.run(mgr.extract_all_tags("test content"))
    assert isinstance(result, dict)
    for key in ("omni_tags", "mega_tags", "nusyq_tags", "rsev_tags", "rule_tags"):
        assert key in result, f"Missing key: {key}"


def test_extract_all_tags_values_are_lists(tmp_path):
    """All values in extract_all_tags result are lists."""
    mgr = AdvancedTagManager(config_path=tmp_path / "rules.json")
    result = asyncio.run(mgr.extract_all_tags("analysis task"))
    for key, value in result.items():
        assert isinstance(value, list), f"Key {key!r} should be a list"


def test_apply_rules_no_rules_returns_empty(tmp_path):
    """_apply_rules returns empty list when rule list is cleared."""
    mgr = AdvancedTagManager(config_path=tmp_path / "rules.json")
    mgr.tag_rules = []
    result = mgr._apply_rules("some random text xyz123", {})
    assert result == []


def test_extract_all_tags_with_context(tmp_path):
    """extract_all_tags accepts and propagates context dict."""
    mgr = AdvancedTagManager(config_path=tmp_path / "rules.json")
    context = {"file_type": "python", "priority": "high"}
    result = asyncio.run(mgr.extract_all_tags("code review task", context=context))
    assert isinstance(result, dict)
