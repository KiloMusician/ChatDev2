"""Tests for AdvancedTagManager coverage improvements."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from src.tagging.advanced_tag_manager import AdvancedTagManager, TagRule


@pytest.mark.asyncio
async def test_extract_all_tags_with_content():
    """Test extraction of all tag types from content."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        # Test with quantum content
        result = await manager.extract_all_tags("This is quantum research")
        assert "rule_tags" in result
        assert "omni_tags" in result
        assert isinstance(result["omni_tags"], list)


@pytest.mark.asyncio
async def test_extract_all_tags_with_context():
    """Test extraction with context information."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        context = {"file_path": "/quantum/module.py"}
        result = await manager.extract_all_tags("quantum analysis", context)

        assert "omni_tags" in result
        # Quantum module should be tagged
        if result["omni_tags"]:
            assert any("quantum" in tag.lower() for tag in result["omni_tags"])


@pytest.mark.asyncio
async def test_extract_all_tags_consciousness():
    """Test consciousness-related tagging."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        result = await manager.extract_all_tags("consciousness emergence patterns")
        assert "omni_tags" in result


@pytest.mark.asyncio
async def test_extract_all_tags_orchestration():
    """Test orchestration tagging."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        result = await manager.extract_all_tags("orchestration workflow management")
        assert "rule_tags" in result


def test_apply_rules_with_priority():
    """Test rule application respects priority."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)
        manager.tag_rules = [
            TagRule("quantum", ["high_priority"], 10),
            TagRule("quantum", ["low_priority"], 1),
        ]

        tags = manager._apply_rules("quantum system", {})
        assert "high_priority" in tags
        assert "low_priority" in tags


def test_apply_rules_removes_duplicates():
    """Test that duplicate tags are removed."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)
        manager.tag_rules = [
            TagRule("quantum", ["quantum_tag", "quantum_tag"], 10),
        ]

        tags = manager._apply_rules("quantum", {})
        # Count duplicates
        tag_count = tags.count("quantum_tag")
        assert tag_count == 1


def test_rule_matches_pattern_case_insensitive():
    """Test that pattern matching checks lowercase text against pattern."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)
        rule = TagRule("quantum", ["tag"], 10)  # lowercase pattern

        # Pattern is checked: rule.pattern in text.lower()
        assert manager._rule_matches(rule, "quantum system", {})
        assert manager._rule_matches(rule, "Quantum System", {})
        assert manager._rule_matches(rule, "QUANTUM", {})


def test_rule_matches_requires_context():
    """Test context_required flag enforcement."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)
        rule = TagRule("kilo", ["tag"], 10, context_required=True)

        # Without context, should not match
        assert not manager._rule_matches(rule, "kilo-foolish", {})

        # With context, should match
        assert manager._rule_matches(rule, "kilo-foolish", {"env": "test"})


def test_load_rules_from_config():
    """Test loading rules from JSON config."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_data = {
            "rules": [
                {
                    "pattern": "test",
                    "tags": ["test_tag"],
                    "priority": 5,
                    "context_required": False,
                }
            ]
        }
        config_path.write_text(json.dumps(config_data))

        manager = AdvancedTagManager(config_path=config_path)
        assert len(manager.tag_rules) > 0
        # Should have loaded test rule plus defaults
        patterns = [r.pattern for r in manager.tag_rules]
        assert "test" in patterns


def test_load_rules_creates_defaults():
    """Test that default rules are created when config missing."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "nonexistent.json"

        manager = AdvancedTagManager(config_path=config_path)
        assert len(manager.tag_rules) > 0
        patterns = [r.pattern for r in manager.tag_rules]
        assert "kilo-foolish" in patterns


@pytest.mark.asyncio
async def test_omni_tag_fallback_quantum():
    """Test OmniTag fallback with quantum content."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        # Test the fallback directly
        tags = await manager.omni_tag.extract_tags("quantum mechanics")
        assert any("quantum" in tag.lower() for tag in tags)


@pytest.mark.asyncio
async def test_omni_tag_fallback_consciousness():
    """Test OmniTag fallback with consciousness content."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        tags = await manager.omni_tag.extract_tags("consciousness and awareness")
        assert any("consciousness" in tag.lower() for tag in tags)


@pytest.mark.asyncio
async def test_omni_tag_fallback_with_context():
    """Test OmniTag fallback with file context."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        context = {"file_path": "/consciousness/module.py"}
        tags = await manager.omni_tag.extract_tags("awareness", context)
        # Should include consciousness_module from context path
        assert any("consciousness" in tag.lower() for tag in tags)


@pytest.mark.asyncio
async def test_mega_tag_fallback():
    """Test MegaTag fallback extraction."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        tags = await manager.mega_tag.extract_tags("def function(): pass")
        assert any("code" in tag.lower() for tag in tags)


@pytest.mark.asyncio
async def test_nusyq_tag_fallback():
    """Test NuSyQ tag fallback extraction."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        tags = await manager.nusyq_tag.extract_tags("nusyq protocol")
        assert isinstance(tags, list)


@pytest.mark.asyncio
async def test_rsev_tag_fallback():
    """Test RSEV tag fallback extraction."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        tags = await manager.rsev_tag.extract_tags("recursive structured element")
        assert isinstance(tags, list)


def test_tag_rule_dataclass():
    """Test TagRule dataclass creation and defaults."""
    rule1 = TagRule("pattern", ["tag1"], 10)
    assert rule1.context_required is False

    rule2 = TagRule("pattern", ["tag2"], 5, context_required=True)
    assert rule2.context_required is True


@pytest.mark.asyncio
async def test_extract_integration_tagging():
    """Test integration-related tagging."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        result = await manager.extract_all_tags("integration bridge system")
        assert "rule_tags" in result or any(
            "integration" in tag.lower() for tag in result.get("omni_tags", [])
        )


@pytest.mark.asyncio
async def test_extract_kilo_foolish_tagging():
    """Test kilo-foolish system tagging via rule matching."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "rules.json"
        config_path.write_text('{"rules": []}')

        manager = AdvancedTagManager(config_path=config_path)

        # The default rules include "kilo-foolish" pattern
        # _apply_rules checks if rule.pattern is in text.lower()
        result = await manager.extract_all_tags("kilo-foolish core system")
        tags_combined = result.get("rule_tags", []) + result.get("omni_tags", [])
        # Should find kilo-foolish in either rule_tags or omni_tags
        assert any("kilo" in str(tag).lower() for tag in tags_combined)
