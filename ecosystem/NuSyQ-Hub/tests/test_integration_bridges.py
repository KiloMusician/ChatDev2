"""Tests for src/integration/consciousness_bridge.py and src/integration/oldest_house_interface.py."""

from unittest.mock import MagicMock, patch


class TestOldestHouseInterface:
    """Tests for OldestHouseInterface — no external dependencies."""

    def _make(self):
        from src.integration.oldest_house_interface import OldestHouseInterface
        return OldestHouseInterface()

    def test_instantiation(self):
        iface = self._make()
        assert iface is not None

    def test_omni_tags_starts_empty(self):
        assert self._make().omni_tags == []

    def test_mega_tags_starts_empty(self):
        assert self._make().mega_tags == []

    def test_create_omni_tag_appends(self):
        iface = self._make()
        iface.create_omni_tag({"id": "t1", "context": "test"})
        assert len(iface.omni_tags) == 1

    def test_create_multiple_omni_tags(self):
        iface = self._make()
        iface.create_omni_tag({"id": "t1"})
        iface.create_omni_tag({"id": "t2"})
        assert len(iface.omni_tags) == 2

    def test_create_omni_tag_transforms_data(self):
        iface = self._make()
        iface.create_omni_tag({"id": "abc", "context": "ctx", "metadata": {"key": "val"}})
        tag = iface.omni_tags[0]
        assert tag["id"] == "abc"
        assert tag["context"] == "ctx"
        assert tag["metadata"] == {"key": "val"}

    def test_omni_tag_missing_fields_default_none(self):
        iface = self._make()
        iface.create_omni_tag({})
        tag = iface.omni_tags[0]
        assert tag["id"] is None
        assert tag["context"] is None
        assert tag["metadata"] == {}

    def test_process_mega_tag_appends(self):
        iface = self._make()
        iface.process_mega_tag({"id": "m1", "attributes": {"x": 1}})
        assert len(iface.mega_tags) == 1

    def test_process_mega_tag_transforms_data(self):
        iface = self._make()
        iface.process_mega_tag({"id": "m1", "attributes": {"a": 1}, "related_tags": ["t1"]})
        tag = iface.mega_tags[0]
        assert tag["id"] == "m1"
        assert tag["attributes"] == {"a": 1}
        assert tag["related_tags"] == ["t1"]

    def test_mega_tag_missing_related_tags_defaults_empty(self):
        iface = self._make()
        iface.process_mega_tag({"id": "m2"})
        assert iface.mega_tags[0]["related_tags"] == []

    def test_get_omni_tags_returns_list(self):
        iface = self._make()
        iface.create_omni_tag({"id": "x"})
        result = iface.get_omni_tags()
        assert isinstance(result, list)
        assert len(result) == 1

    def test_get_mega_tags_returns_list(self):
        iface = self._make()
        iface.process_mega_tag({"id": "y"})
        result = iface.get_mega_tags()
        assert isinstance(result, list)
        assert len(result) == 1

    def test_clear_tags_empties_both(self):
        iface = self._make()
        iface.create_omni_tag({"id": "a"})
        iface.process_mega_tag({"id": "b"})
        iface.clear_tags()
        assert iface.omni_tags == []
        assert iface.mega_tags == []

    def test_clear_then_add_still_works(self):
        iface = self._make()
        iface.create_omni_tag({"id": "a"})
        iface.clear_tags()
        iface.create_omni_tag({"id": "b"})
        assert len(iface.omni_tags) == 1
        assert iface.omni_tags[0]["id"] == "b"


class TestConsciousnessBridge:
    """Tests for ConsciousnessBridge with mocked subsystems."""

    def _make_with_mocks(self):
        with (
            patch("src.integration.consciousness_bridge.OmniTagSystem") as MockOTS,
            patch("src.integration.consciousness_bridge.MegaTagProcessor") as MockMTP,
            patch("src.integration.consciousness_bridge.SymbolicCognition") as MockSC,
        ):
            from src.integration.consciousness_bridge import ConsciousnessBridge
            bridge = ConsciousnessBridge()
            return bridge, MockOTS.return_value, MockMTP.return_value, MockSC.return_value

    def test_instantiation(self):
        bridge, _, _, _ = self._make_with_mocks()
        assert bridge is not None

    def test_contextual_memory_starts_empty(self):
        bridge, _, _, _ = self._make_with_mocks()
        assert bridge.contextual_memory == {}

    def test_has_initialized_at(self):
        from datetime import datetime
        bridge, _, _, _ = self._make_with_mocks()
        assert isinstance(bridge.initialized_at, datetime)

    def test_get_initialization_time_returns_string(self):
        bridge, _, _, _ = self._make_with_mocks()
        t = bridge.get_initialization_time()
        assert isinstance(t, str)
        assert len(t) > 0

    def test_get_initialization_time_format(self):
        import re
        bridge, _, _, _ = self._make_with_mocks()
        t = bridge.get_initialization_time()
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", t)

    def test_initialize_calls_subsystems(self):
        bridge, mock_ots, mock_mtp, mock_sc = self._make_with_mocks()
        bridge.initialize()
        mock_ots.initialize.assert_called_once()
        mock_mtp.initialize.assert_called_once()
        mock_sc.initialize.assert_called_once()

    def test_enhance_contextual_memory_uses_subsystems(self):
        bridge, mock_ots, mock_mtp, _mock_sc = self._make_with_mocks()
        mock_ots.create_tags.return_value = ["tag1"]
        mock_mtp.process_tags.return_value = {"key": "val"}
        bridge.enhance_contextual_memory("some input")
        mock_ots.create_tags.assert_called_once_with("some input")
        mock_mtp.process_tags.assert_called_once_with(["tag1"])

    def test_enhance_contextual_memory_updates_memory(self):
        bridge, mock_ots, mock_mtp, _mock_sc = self._make_with_mocks()
        mock_ots.create_tags.return_value = []
        mock_mtp.process_tags.return_value = {"concept": "memory_entry"}
        bridge.enhance_contextual_memory("data")
        assert bridge.contextual_memory.get("concept") == "memory_entry"

    def test_retrieve_contextual_memory_delegates(self):
        bridge, _mock_ots, _mock_mtp, mock_sc = self._make_with_mocks()
        mock_sc.query_memory.return_value = "result_value"
        result = bridge.retrieve_contextual_memory("my query")
        mock_sc.query_memory.assert_called_once_with({}, "my query")
        assert result == "result_value"
