"""Tests for src/tagging/ — OmniTagSystem and Validator."""

import pytest


class TestOmniTagSystem:
    """Tests for OmniTagSystem CRUD lifecycle."""

    @pytest.fixture
    def ots(self):
        from src.tagging.omnitag_system import OmniTagSystem
        return OmniTagSystem()

    def test_instantiation(self, ots):
        assert ots is not None

    def test_empty_on_init(self, ots):
        assert ots.list_omni_tags() == {}

    def test_initialize_is_noop(self, ots):
        result = ots.initialize()
        assert result is None

    def test_create_and_retrieve(self, ots):
        ots.create_omni_tag("python", "Python programming")
        ctx = ots.retrieve_omni_tag("python")
        assert ctx == "Python programming"

    def test_create_no_context(self, ots):
        ots.create_omni_tag("bare")
        assert ots.retrieve_omni_tag("bare") == ""

    def test_create_duplicate_raises(self, ots):
        ots.create_omni_tag("tag1", "first")
        with pytest.raises(ValueError, match="already exists"):
            ots.create_omni_tag("tag1", "second")

    def test_retrieve_missing_raises(self, ots):
        with pytest.raises(KeyError):
            ots.retrieve_omni_tag("nonexistent")

    def test_update_tag(self, ots):
        ots.create_omni_tag("upd", "original")
        ots.update_omni_tag("upd", "updated")
        assert ots.retrieve_omni_tag("upd") == "updated"

    def test_update_missing_raises(self, ots):
        with pytest.raises(KeyError):
            ots.update_omni_tag("missing", "new")

    def test_delete_tag(self, ots):
        ots.create_omni_tag("del_me", "context")
        ots.delete_omni_tag("del_me")
        with pytest.raises(KeyError):
            ots.retrieve_omni_tag("del_me")

    def test_delete_missing_raises(self, ots):
        with pytest.raises(KeyError):
            ots.delete_omni_tag("nope")

    def test_list_returns_copy(self, ots):
        ots.create_omni_tag("x", "ctx")
        listed = ots.list_omni_tags()
        listed["y"] = "extra"  # mutate copy
        assert "y" not in ots.list_omni_tags()

    def test_create_dict_tag_no_error(self, ots):
        # Dict-form create_omni_tag is pass-through (no copilot backend)
        ots.create_omni_tag({"purpose": "test"})  # Should not raise


class TestOmniTagSystemCreateTags:
    """Tests for OmniTagSystem.create_tags content tagging."""

    @pytest.fixture
    def ots(self):
        from src.tagging.omnitag_system import OmniTagSystem
        return OmniTagSystem()

    def test_empty_input_returns_empty(self, ots):
        assert ots.create_tags("") == []
        assert ots.create_tags(None) == []

    def test_length_tag_always_present(self, ots):
        tags = ots.create_tags("hello world")
        tag_names = [t["tag"] for t in tags]
        assert "length" in tag_names

    def test_length_tag_value(self, ots):
        text = "hello"
        tags = ots.create_tags(text)
        length_tag = next(t for t in tags if t["tag"] == "length")
        assert length_tag["value"] == 5

    def test_bug_keyword_creates_debugging_category(self, ots):
        tags = ots.create_tags("fix the bug")
        categories = [t["value"] for t in tags if t["tag"] == "category"]
        assert "debugging" in categories

    def test_optimize_keyword_creates_optimization_category(self, ots):
        tags = ots.create_tags("refactor and optimize code")
        categories = [t["value"] for t in tags if t["tag"] == "category"]
        assert "optimization" in categories

    def test_neutral_text_no_category(self, ots):
        tags = ots.create_tags("hello world greeting")
        categories = [t["tag"] for t in tags]
        assert "category" not in categories


class TestTaggingValidator:
    """Tests for Validator — OmniTag, MegaTag, RSHTS validation."""

    @pytest.fixture
    def v(self):
        from src.tagging.validator import Validator
        return Validator()

    @pytest.fixture
    def v_lenient(self):
        from src.tagging.validator import Validator
        return Validator(strict=False)

    # OmniTag tests
    def test_valid_omnitag_minimal(self, v):
        data = [{"OmniTag": {"purpose": "testing module"}}]
        assert v.validate(data) is True
        assert v.get_errors() == []

    def test_valid_omnitag_no_dependencies_key(self, v):
        # Fixed bug: absent 'dependencies' key must not crash (None is not iterable)
        data = [{"OmniTag": {"purpose": "no deps"}}]
        assert v.validate(data) is True

    def test_omnitag_missing_purpose_fails(self, v):
        data = [{"OmniTag": {"context": "something"}}]
        assert v.validate(data) is False
        assert any("purpose" in e for e in v.get_errors())

    def test_omnitag_not_dict_fails(self, v):
        data = [{"OmniTag": "not_a_dict"}]
        assert v.validate(data) is False

    def test_omnitag_with_optional_fields(self, v):
        data = [{"OmniTag": {
            "purpose": "testing",
            "dependencies": ["dep1", "dep2"],
            "context": "some context",
            "evolution_stage": "v1.0",
        }}]
        assert v.validate(data) is True

    def test_omnitag_bad_dependencies_type_fails(self, v):
        data = [{"OmniTag": {"purpose": "test", "dependencies": "not_a_list"}}]
        assert v.validate(data) is False

    # MegaTag tests
    def test_valid_megatag_string(self, v):
        data = [{"MegaTag": "TYPE⨳INTEGRATION⦾[core]→∞"}]
        assert v.validate(data) is True

    def test_megatag_string_missing_markers_fails(self, v):
        data = [{"MegaTag": "plain string without markers"}]
        assert v.validate(data) is False

    def test_valid_megatag_dict(self, v):
        data = [{"MegaTag": {"type": "orchestration", "integration_points": ["api", "db"]}}]
        assert v.validate(data) is True

    def test_megatag_dict_missing_type_fails(self, v):
        data = [{"MegaTag": {"integration_points": ["api"]}}]
        assert v.validate(data) is False

    # RSHTS tests
    def test_valid_rshts(self, v):
        data = [{"RSHTS": "CONSCIOUSNESS⨳TRANSCENDENT◊AWARE"}]
        assert v.validate(data) is True

    def test_rshts_missing_markers_fails(self, v):
        data = [{"RSHTS": "plain string without symbols"}]
        assert v.validate(data) is False

    def test_rshts_empty_fails(self, v):
        data = [{"RSHTS": ""}]
        assert v.validate(data) is False

    # Strict vs lenient
    def test_strict_rejects_unknown_tags(self, v):
        data = [{"SomeUnknownTag": "value"}]
        assert v.validate(data) is False

    def test_lenient_accepts_unknown_tags(self, v_lenient):
        data = [{"SomeUnknownTag": "value"}]
        # Lenient mode: no known tags = no failures (item just ignored)
        assert v_lenient.validate(data) is True

    def test_errors_cleared_between_validate_calls(self, v):
        v.validate([{"OmniTag": {"bad": True}}])
        assert len(v.get_errors()) > 0
        v.validate([{"OmniTag": {"purpose": "good"}}])
        assert v.get_errors() == []

    def test_validate_item_standalone(self, v):
        result = v.validate_item({"OmniTag": {"purpose": "standalone test"}})
        assert result is True
