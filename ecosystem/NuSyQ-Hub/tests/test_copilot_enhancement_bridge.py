"""Tests for src/copilot/copilot_enhancement_bridge.py.

All imports are inside test functions to avoid module-level side effects.
External calls (sqlite3, subprocess, os.walk, pickle) are stubbed where needed.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# ZetaSetLexemeGenerator
# ---------------------------------------------------------------------------


def test_lexeme_generator_glyph_map_keys():
    from src.copilot.copilot_enhancement_bridge import ZetaSetLexemeGenerator

    assert set(ZetaSetLexemeGenerator.GLYPH_MAP.keys()) == set(range(12))


def test_lexeme_generator_generate_from_context_returns_string():
    from src.copilot.copilot_enhancement_bridge import ZetaSetLexemeGenerator

    result = ZetaSetLexemeGenerator.generate_from_context("hello world")
    assert isinstance(result, str)
    assert len(result) == 11  # 11 bytes used from md5 digest


def test_lexeme_generator_generate_from_context_deterministic():
    from src.copilot.copilot_enhancement_bridge import ZetaSetLexemeGenerator

    r1 = ZetaSetLexemeGenerator.generate_from_context("same_input")
    r2 = ZetaSetLexemeGenerator.generate_from_context("same_input")
    assert r1 == r2


def test_lexeme_generator_generate_from_context_varies_with_input():
    from src.copilot.copilot_enhancement_bridge import ZetaSetLexemeGenerator

    r1 = ZetaSetLexemeGenerator.generate_from_context("input_a")
    r2 = ZetaSetLexemeGenerator.generate_from_context("input_b")
    # Different inputs should (almost certainly) differ
    assert r1 != r2


def test_lexeme_generator_get_semantic_meaning_returns_arrow_joined():
    from src.copilot.copilot_enhancement_bridge import ZetaSetLexemeGenerator

    sequence = "ΩΦΣ"
    meaning = ZetaSetLexemeGenerator.get_semantic_meaning(sequence)
    assert " → " in meaning


def test_lexeme_generator_get_semantic_meaning_up_to_5_glyphs():
    from src.copilot.copilot_enhancement_bridge import ZetaSetLexemeGenerator

    sequence = "ΩΦΣΨ∇χ"  # 6 chars; only first 5 should be used
    meaning = ZetaSetLexemeGenerator.get_semantic_meaning(sequence)
    parts = meaning.split(" → ")
    assert len(parts) == 5


# ---------------------------------------------------------------------------
# OmniTag dataclass
# ---------------------------------------------------------------------------


def test_omnitag_construction_defaults():
    from src.copilot.copilot_enhancement_bridge import OmniTag

    tag = OmniTag(msg_id=1)
    assert tag.msg_id == 1
    assert tag.topic == ""
    assert tag.quantum_state == ""
    assert tag.meta_context == ""
    assert tag.lexeme_sequence == ""
    assert tag.semantic_meaning == ""
    assert tag.sub_tags == {}
    assert isinstance(tag.timestamp, datetime)


def test_omnitag_add_layer():
    from src.copilot.copilot_enhancement_bridge import OmniTag

    tag = OmniTag(msg_id=5, topic="test")
    tag.add_layer("layer_a", [1, 2, 3])
    assert tag.sub_tags["layer_a"] == [1, 2, 3]


def test_omnitag_generate_lexeme_populates_fields():
    from src.copilot.copilot_enhancement_bridge import OmniTag

    tag = OmniTag(msg_id=2, topic="arch", meta_context="design", quantum_state="Ψ")
    tag.generate_lexeme()
    assert len(tag.lexeme_sequence) > 0
    assert len(tag.semantic_meaning) > 0


def test_omnitag_render_contains_msg_id():
    from src.copilot.copilot_enhancement_bridge import OmniTag

    tag = OmniTag(msg_id=42, topic="test_topic")
    rendered = tag.render()
    assert "42" in rendered
    assert "test_topic" in rendered


def test_omnitag_render_includes_sub_tags():
    from src.copilot.copilot_enhancement_bridge import OmniTag

    tag = OmniTag(msg_id=3)
    tag.add_layer("MyLayer", "some_value")
    rendered = tag.render()
    assert "MyLayer" in rendered
    assert "some_value" in rendered


def test_omnitag_to_dict_keys():
    from src.copilot.copilot_enhancement_bridge import OmniTag

    tag = OmniTag(msg_id=7, topic="coding")
    d = tag.to_dict()
    expected_keys = {
        "msg_id",
        "timestamp",
        "topic",
        "quantum_state",
        "meta_context",
        "lexeme_sequence",
        "semantic_meaning",
        "sub_tags",
    }
    assert expected_keys.issubset(d.keys())


def test_omnitag_to_dict_msg_id_value():
    from src.copilot.copilot_enhancement_bridge import OmniTag

    tag = OmniTag(msg_id=99)
    assert tag.to_dict()["msg_id"] == 99


# ---------------------------------------------------------------------------
# MegaTag dataclass
# ---------------------------------------------------------------------------


def test_megatag_construction_defaults():
    from src.copilot.copilot_enhancement_bridge import MegaTag

    mt = MegaTag(session_id="s1", system_node="node1")
    assert mt.overseer == "Raven"
    assert mt.tags == []
    assert mt.consciousness_level == 0.0
    assert mt.recursive_depth == 0


def test_megatag_add_tag_increases_count():
    from src.copilot.copilot_enhancement_bridge import MegaTag, OmniTag

    mt = MegaTag(session_id="s2", system_node="node2")
    tag = OmniTag(msg_id=1, topic="hello")
    mt.add_tag(tag)
    assert len(mt.tags) == 1


def test_megatag_consciousness_level_increases_with_complexity():
    from src.copilot.copilot_enhancement_bridge import MegaTag, OmniTag

    mt = MegaTag(session_id="s3", system_node="node3")
    tag = OmniTag(
        msg_id=1,
        topic="architecture design patterns",
        meta_context="extended meta context info",
        lexeme_sequence="ΩΦΣΨ∇",
    )
    tag.add_layer("key1", "value")
    tag.add_layer("key2", "value")
    mt.add_tag(tag)
    assert mt.consciousness_level > 0.0


def test_megatag_recursive_depth_counts_recursive_tags():
    from src.copilot.copilot_enhancement_bridge import MegaTag, OmniTag

    mt = MegaTag(session_id="s4", system_node="node4")
    tag_recursive = OmniTag(msg_id=1, meta_context="recursive call chain")
    tag_plain = OmniTag(msg_id=2, meta_context="plain context")
    mt.add_tag(tag_recursive)
    mt.add_tag(tag_plain)
    assert mt.recursive_depth == 1


def test_megatag_summary_contains_session_id():
    from src.copilot.copilot_enhancement_bridge import MegaTag

    mt = MegaTag(session_id="test_session_xyz", system_node="n1")
    s = mt.summary()
    assert "test_session_xyz" in s


def test_megatag_summary_includes_metalinks():
    from src.copilot.copilot_enhancement_bridge import MegaTag

    mt = MegaTag(session_id="s5", system_node="n2")
    mt.meta_links["repo"] = "https://github.com/example/repo"
    s = mt.summary()
    assert "repo" in s


# ---------------------------------------------------------------------------
# EnhancedCopilotBridge / CopilotEnhancementBridge — construction
# ---------------------------------------------------------------------------


def test_enhanced_bridge_construction(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    assert bridge.repository_root == tmp_path
    assert isinstance(bridge.session_id, str)
    assert bridge.session_id.startswith("ΣΞΛΨ_")
    assert bridge.msg_counter == 0


def test_copilot_enhancement_bridge_is_subclass(tmp_path):
    from src.copilot.copilot_enhancement_bridge import (
        CopilotEnhancementBridge,
        EnhancedCopilotBridge,
    )

    bridge = CopilotEnhancementBridge(repository_root=str(tmp_path))
    assert isinstance(bridge, EnhancedCopilotBridge)


def test_bridge_creates_memory_dir(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    EnhancedCopilotBridge(repository_root=str(tmp_path))
    assert (tmp_path / "copilot_memory").exists()


def test_bridge_creates_sqlite_db(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    EnhancedCopilotBridge(repository_root=str(tmp_path))
    db_path = tmp_path / "copilot_memory" / "consciousness_memory.db"
    assert db_path.exists()


# ---------------------------------------------------------------------------
# Pure / logic methods (no network or subprocess needed)
# ---------------------------------------------------------------------------


def test_extract_intent_keywords_code_generation(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    intents = bridge._extract_intent_keywords("create a new function")
    assert "code_generation" in intents


def test_extract_intent_keywords_debugging(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    intents = bridge._extract_intent_keywords("fix this bug in the error handler")
    assert "debugging" in intents


def test_extract_intent_keywords_multiple(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    intents = bridge._extract_intent_keywords("generate tests and document the api interface")
    assert "code_generation" in intents
    assert "documentation" in intents


def test_extract_intent_keywords_no_match(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    intents = bridge._extract_intent_keywords("the quick brown fox")
    assert intents == []


def test_analyze_file_context_no_context(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    result = bridge._analyze_file_context(None)
    assert result == {"status": "no_file_context"}


def test_analyze_file_context_python(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    python_code = "def foo():\n    pass\nclass Bar:\n    pass\n"
    result = bridge._analyze_file_context(python_code)
    assert result["file_type"] == "python"
    assert result["complexity"]["functions"] >= 1
    assert result["complexity"]["classes"] >= 1


def test_analyze_file_context_markdown(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    md = "# Title\n## Section\nSome text\n"
    result = bridge._analyze_file_context(md)
    assert result["file_type"] == "markdown"


def test_find_related_files_returns_list(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    result = bridge._find_related_files(["testing", "documentation"])
    assert isinstance(result, list)
    # All items should be unique (set was applied)
    assert len(result) == len(set(result))


def test_find_related_files_unknown_intent(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    result = bridge._find_related_files(["nonexistent_intent"])
    assert result == []


def test_get_architecture_recommendations_code_gen(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    analysis = {"intent_keywords": ["code_generation"]}
    recs = bridge._get_architecture_recommendations(analysis)
    assert isinstance(recs, list)
    assert len(recs) > 0


def test_get_architecture_recommendations_empty_intents(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    analysis = {"intent_keywords": []}
    recs = bridge._get_architecture_recommendations(analysis)
    assert recs == []


def test_generate_lexeme_enhancements_known_glyphs(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    # "Ψ" is in glyph_enhancements map
    result = bridge._generate_lexeme_enhancements("Ψ")
    assert len(result) >= 1
    assert any("emergent" in r for r in result)


def test_generate_lexeme_enhancements_empty_sequence(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    result = bridge._generate_lexeme_enhancements("")
    assert result == []


def test_get_relevant_user_patterns_returns_subset(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    bridge.user_patterns["testing"] = 5
    bridge.user_patterns["debugging"] = 3
    result = bridge._get_relevant_user_patterns(["testing"])
    assert result == {"testing": 5}
    assert "debugging" not in result


# ---------------------------------------------------------------------------
# get_consciousness_summary
# ---------------------------------------------------------------------------


def test_get_consciousness_summary_structure(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    summary = bridge.get_consciousness_summary()
    assert "session_id" in summary
    assert "message_count" in summary
    assert "consciousness_level" in summary
    assert "memory_palace_size" in summary
    assert summary["message_count"] == 0


# ---------------------------------------------------------------------------
# cultivate_understanding
# ---------------------------------------------------------------------------


def test_cultivate_understanding_adds_insights(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    bridge.cultivate_understanding(
        observations=["system stable", "tests passing"],
        insights=["modular design preferred"],
    )
    assert "modular design preferred" in bridge.architecture_insights
    assert bridge.msg_counter == 1
    assert len(bridge.current_megatag.tags) == 1


# ---------------------------------------------------------------------------
# store_context_memory
# ---------------------------------------------------------------------------


def test_store_context_memory_appends(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    initial_size = len(bridge.context_memory)
    bridge.store_context_memory({"key": "value"})
    assert len(bridge.context_memory) == initial_size + 1
    assert bridge.context_memory[-1] == {"key": "value"}


# ---------------------------------------------------------------------------
# parse_quest_log_for_context — returns empty when no file
# ---------------------------------------------------------------------------


def test_parse_quest_log_no_file(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    result = bridge.parse_quest_log_for_context()
    assert result == {"quests": {}, "questlines": {}}


def test_parse_quest_log_with_entries(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    # Create the expected file path
    quest_dir = tmp_path / "Rosetta_Quest_System"
    quest_dir.mkdir()
    quest_log = quest_dir / "quest_log.jsonl"

    lines = [
        json.dumps({"event": "add_questline", "details": {"name": "QL1", "description": "first"}}),
        json.dumps({"event": "add_quest", "details": {"id": "q1", "title": "Quest One", "status": "pending"}}),
        json.dumps({"event": "update_quest_status", "details": {"id": "q1", "status": "active"}}),
    ]
    quest_log.write_text("\n".join(lines), encoding="utf-8")

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    result = bridge.parse_quest_log_for_context()
    assert "QL1" in result["questlines"]
    assert "q1" in result["quests"]
    assert result["quests"]["q1"]["status"] == "active"


# ---------------------------------------------------------------------------
# _parse_json_line
# ---------------------------------------------------------------------------


def test_parse_json_line_valid(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    result = bridge._parse_json_line('{"event": "test", "details": {}}')
    assert result == {"event": "test", "details": {}}


def test_parse_json_line_invalid(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    result = bridge._parse_json_line("not valid json{{")
    assert result is None


# ---------------------------------------------------------------------------
# enhance_search_context — smoke test (subprocess patched)
# ---------------------------------------------------------------------------


def test_enhance_search_context_returns_expected_keys(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    # Stub log_event to avoid AttributeError from broken _logging_module.LogLevel
    bridge.log_event = MagicMock()
    with patch("os.walk", return_value=[]):
        result = bridge.enhance_search_context("create a logging utility")

    assert "original_query" in result
    assert "lexeme_sequence" in result
    assert "semantic_meaning" in result
    assert "enhanced_context" in result
    assert "actionable_enhancements" in result
    assert "consciousness_level" in result
    assert "omnitag" in result
    assert result["original_query"] == "create a logging utility"


def test_enhance_search_context_increments_counter(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    bridge.log_event = MagicMock()
    assert bridge.msg_counter == 0
    with patch("os.walk", return_value=[]):
        bridge.enhance_search_context("fix this error")
    assert bridge.msg_counter == 1


def test_enhance_search_context_with_file_context(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    bridge.log_event = MagicMock()
    fc = "def my_func():\n    pass\n"
    with patch("os.walk", return_value=[]):
        result = bridge.enhance_search_context("explain this function", file_context=fc)
    assert result["omnitag"]["topic"] != ""


# ---------------------------------------------------------------------------
# launch_tool_hook — subprocess patched
# ---------------------------------------------------------------------------


def test_launch_tool_hook_known_tool(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    bridge.log_event = MagicMock()
    with patch("subprocess.Popen") as mock_popen:
        bridge.launch_tool_hook("context_browser")
        mock_popen.assert_called_once()


def test_launch_tool_hook_unknown_tool_does_not_popen(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    bridge.log_event = MagicMock()
    with patch("subprocess.Popen") as mock_popen:
        bridge.launch_tool_hook("nonexistent_tool_xyz")
        mock_popen.assert_not_called()


# ---------------------------------------------------------------------------
# get_enhanced_bridge singleton
# ---------------------------------------------------------------------------


def test_get_enhanced_bridge_returns_instance(tmp_path):
    import src.copilot.copilot_enhancement_bridge as module
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    original = module._enhanced_bridge
    module._enhanced_bridge = None
    try:
        from src.copilot.copilot_enhancement_bridge import get_enhanced_bridge

        bridge = get_enhanced_bridge(str(tmp_path))
        assert isinstance(bridge, EnhancedCopilotBridge)
    finally:
        module._enhanced_bridge = original


def test_get_enhanced_bridge_singleton(tmp_path):
    import src.copilot.copilot_enhancement_bridge as module

    original = module._enhanced_bridge
    module._enhanced_bridge = None
    try:
        from src.copilot.copilot_enhancement_bridge import get_enhanced_bridge

        b1 = get_enhanced_bridge(str(tmp_path))
        b2 = get_enhanced_bridge(str(tmp_path))
        assert b1 is b2
    finally:
        module._enhanced_bridge = original


# ---------------------------------------------------------------------------
# _generate_session_id format
# ---------------------------------------------------------------------------


def test_generate_session_id_format(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    sid = bridge._generate_session_id()
    assert sid.startswith("ΣΞΛΨ_")
    # hex part is 8 chars
    hex_part = sid[len("ΣΞΛΨ_"):]
    assert len(hex_part) == 8
    int(hex_part, 16)  # must be valid hex


# ---------------------------------------------------------------------------
# _handle_add_questline / _handle_add_quest / _handle_update_quest_status
# ---------------------------------------------------------------------------


def test_handle_add_questline(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    questlines = {}
    bridge._handle_add_questline({"name": "QL_A", "desc": "first"}, questlines)
    assert "QL_A" in questlines


def test_handle_add_quest(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    quests = {}
    bridge._handle_add_quest({"id": "uuid-123", "title": "My Quest", "status": "pending"}, quests)
    assert "uuid-123" in quests


def test_handle_update_quest_status(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    quests = {"uuid-123": {"title": "My Quest", "status": "pending"}}
    bridge._handle_update_quest_status({"id": "uuid-123", "status": "active"}, quests)
    assert quests["uuid-123"]["status"] == "active"


def test_handle_update_quest_status_missing_id(tmp_path):
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    bridge = EnhancedCopilotBridge(repository_root=str(tmp_path))
    quests = {}
    # Should not raise even if quest doesn't exist
    bridge._handle_update_quest_status({"id": "nonexistent", "status": "done"}, quests)
    assert quests == {}
