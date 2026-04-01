"""Tests for src/core/megatag_processor.py - MegaTag Processing System.

Coverage targets:
- MegaTagProcessor class:
  - __init__() - initialization with/without copilot processor
  - initialize() - consciousness bridge setup
  - process_tags() - tag processing with different input types
  - process_mega_tag() - mega tag payload processing
  - process_megatags() - async megatag pipeline
  - validate_quantum_symbols() - quantum symbol validation
  - is_valid_quantum_symbol() - individual symbol checking
  - extract_semantics() - semantic extraction
  - integrate_with_consciousness_bridge() - consciousness integration
"""

import pytest
from unittest.mock import MagicMock, patch

from src.core.megatag_processor import MegaTagProcessor


class TestMegaTagProcessorInit:
    """Tests for MegaTagProcessor initialization."""

    def test_init_without_copilot(self):
        """Initialize without copilot processor available."""
        with patch("src.core.megatag_processor.CopilotMegaTagProcessor", None):
            processor = MegaTagProcessor()

        assert processor._copilot is None
        assert processor.consciousness_bridge is None

    def test_init_with_copilot_mock(self):
        """Initialize with copilot processor available."""
        mock_copilot = MagicMock()

        with patch("src.core.megatag_processor.CopilotMegaTagProcessor", mock_copilot):
            processor = MegaTagProcessor("arg1", key="value")

        mock_copilot.assert_called_once_with("arg1", key="value")
        assert processor._copilot is not None


class TestMegaTagProcessorInitialize:
    """Tests for MegaTagProcessor.initialize() method."""

    def test_initialize_with_copilot(self):
        """Initialize with copilot processor - no-op."""
        processor = MegaTagProcessor()
        processor._copilot = MagicMock()

        # Should not raise
        processor.initialize()

    def test_initialize_without_copilot_bridge_available(self):
        """Initialize without copilot but with bridge available."""
        processor = MegaTagProcessor()
        processor._copilot = None

        mock_bridge = MagicMock()
        with patch.dict(
            "sys.modules",
            {
                "src.system.dictionary.consciousness_bridge": MagicMock(
                    ConsciousnessBridge=mock_bridge
                )
            },
        ):
            with patch(
                "src.core.megatag_processor.MegaTagProcessor.initialize",
                lambda self: setattr(self, "consciousness_bridge", mock_bridge()),
            ):
                processor.initialize()

    def test_initialize_without_copilot_bridge_unavailable(self):
        """Initialize without copilot and without bridge."""
        processor = MegaTagProcessor()
        processor._copilot = None

        # Real initialize with ImportError
        processor.initialize()
        # consciousness_bridge should be None due to ImportError


class TestMegaTagProcessorProcessTags:
    """Tests for MegaTagProcessor.process_tags() method."""

    def test_process_tags_list_input(self):
        """Process list of tags."""
        processor = MegaTagProcessor()
        processor._copilot = None

        result = processor.process_tags(["tag1", "tag2", "tag3"])

        assert result == {"processed_tags": ["tag1", "tag2", "tag3"]}

    def test_process_tags_dict_input_no_copilot(self):
        """Process dict tags without copilot processor."""
        processor = MegaTagProcessor()
        processor._copilot = None

        input_dict = {"type": "test", "value": 42}
        result = processor.process_tags(input_dict)

        assert result == input_dict

    def test_process_tags_dict_input_with_copilot(self):
        """Process dict tags with copilot processor."""
        processor = MegaTagProcessor()
        processor._copilot = MagicMock()
        processor._copilot.process_mega_tag.return_value = {"processed": True}

        input_dict = {"type": "test", "value": 42}
        result = processor.process_tags(input_dict)

        assert result == {"processed": True}
        processor._copilot.process_mega_tag.assert_called_once_with(input_dict)

    def test_process_tags_dict_copilot_exception(self):
        """Process dict tags when copilot throws exception."""
        processor = MegaTagProcessor()
        processor._copilot = MagicMock()
        processor._copilot.process_mega_tag.side_effect = ValueError("Test error")

        input_dict = {"type": "test"}
        result = processor.process_tags(input_dict)

        assert result == {"processed_tags": input_dict}


class TestMegaTagProcessorProcessMegaTag:
    """Tests for MegaTagProcessor.process_mega_tag() method."""

    def test_process_mega_tag_no_copilot(self):
        """Process mega tag without copilot."""
        processor = MegaTagProcessor()
        processor._copilot = None

        tag_data = {"type": "Symbol", "value": "⨳test"}
        result = processor.process_mega_tag(tag_data)

        assert result == {"processed_tags": tag_data}

    def test_process_mega_tag_with_copilot(self):
        """Process mega tag with copilot processor."""
        processor = MegaTagProcessor()
        processor._copilot = MagicMock()
        processor._copilot.process_mega_tag.return_value = {"enhanced": True}

        tag_data = {"type": "Symbol", "value": "⨳test"}
        result = processor.process_mega_tag(tag_data)

        assert result == {"enhanced": True}

    def test_process_mega_tag_copilot_exception(self):
        """Process mega tag when copilot throws exception."""
        processor = MegaTagProcessor()
        processor._copilot = MagicMock()
        processor._copilot.process_mega_tag.side_effect = RuntimeError("Failed")

        tag_data = {"type": "Error"}
        result = processor.process_mega_tag(tag_data)

        assert result == {"processed_tags": tag_data}


class TestQuantumSymbolValidation:
    """Tests for quantum symbol validation methods."""

    def test_is_valid_quantum_symbol_true(self):
        """Valid quantum symbols."""
        processor = MegaTagProcessor()

        assert processor.is_valid_quantum_symbol("TYPE⨳INTEGRATION") is True
        assert processor.is_valid_quantum_symbol("data⦾points") is True
        assert processor.is_valid_quantum_symbol("flow→result") is True
        assert processor.is_valid_quantum_symbol("infinite∞loop") is True
        assert processor.is_valid_quantum_symbol("state⟨ket⟩") is True

    def test_is_valid_quantum_symbol_false(self):
        """Invalid/missing quantum symbols."""
        processor = MegaTagProcessor()

        assert processor.is_valid_quantum_symbol("plain-tag") is False
        assert processor.is_valid_quantum_symbol("no_symbols_here") is False
        assert processor.is_valid_quantum_symbol("") is False
        assert processor.is_valid_quantum_symbol("123") is False

    @pytest.mark.asyncio
    async def test_validate_quantum_symbols(self):
        """Validate filters valid symbols."""
        processor = MegaTagProcessor()

        megatags = [
            "TYPE⨳VALID",
            "invalid-tag",
            "another⦾valid",
            "no_symbol",
            "flow→infinity∞",
        ]

        result = await processor.validate_quantum_symbols(megatags)

        assert len(result) == 3
        assert "TYPE⨳VALID" in result
        assert "another⦾valid" in result
        assert "flow→infinity∞" in result
        assert "invalid-tag" not in result
        assert "no_symbol" not in result


class TestSemanticExtraction:
    """Tests for MegaTagProcessor.extract_semantics() method."""

    def test_extract_semantics_basic(self):
        """Extract semantics from single tag."""
        processor = MegaTagProcessor()

        tags = ["TYPE⨳INTEGRATION"]
        result = processor.extract_semantics(tags)

        assert len(result) == 1
        assert result[0]["raw_tag"] == "TYPE⨳INTEGRATION"
        assert result[0]["type"] == "TYPE"
        assert result[0]["quantum_state"] == "TYPE⨳INTEGRATION"

    def test_extract_semantics_with_integration_points(self):
        """Extract semantics with integration points."""
        processor = MegaTagProcessor()

        tags = ["TYPE⨳DATA⦾point1⦾point2"]
        result = processor.extract_semantics(tags)

        assert len(result) == 1
        assert result[0]["type"] == "TYPE"
        # Integration points are split by ⦾
        assert "point1" in result[0]["integration_points"]
        assert "point2" in result[0]["integration_points"]

    def test_extract_semantics_empty_list(self):
        """Extract semantics from empty list."""
        processor = MegaTagProcessor()

        result = processor.extract_semantics([])

        assert result == []

    def test_extract_semantics_multiple_tags(self):
        """Extract semantics from multiple tags."""
        processor = MegaTagProcessor()

        tags = ["TAG1⨳DATA", "TAG2⨳OTHER", "PLAIN"]
        result = processor.extract_semantics(tags)

        assert len(result) == 3
        assert result[0]["type"] == "TAG1"
        assert result[1]["type"] == "TAG2"
        assert result[2]["type"] == "PLAIN"  # No ⨳, whole tag is type


class TestConsciousnessIntegration:
    """Tests for MegaTagProcessor.integrate_with_consciousness_bridge() method."""

    @pytest.mark.asyncio
    async def test_integrate_with_bridge(self):
        """Integrate when consciousness bridge available."""
        processor = MegaTagProcessor()
        processor.consciousness_bridge = MagicMock()

        semantics = [{"type": "TYPE1"}, {"type": "TYPE2"}]
        result = await processor.integrate_with_consciousness_bridge(semantics)

        assert len(result) == 2
        assert result[0]["semantic"] == {"type": "TYPE1"}
        assert result[0]["integrated"] is True
        assert result[1]["semantic"] == {"type": "TYPE2"}
        assert result[1]["integrated"] is True

    @pytest.mark.asyncio
    async def test_integrate_without_bridge(self):
        """Pass-through when no consciousness bridge."""
        processor = MegaTagProcessor()
        processor.consciousness_bridge = None

        semantics = [{"type": "TYPE1"}, {"type": "TYPE2"}]
        result = await processor.integrate_with_consciousness_bridge(semantics)

        assert result == semantics

    @pytest.mark.asyncio
    async def test_integrate_empty_semantics(self):
        """Integrate empty semantics list."""
        processor = MegaTagProcessor()
        processor.consciousness_bridge = MagicMock()

        result = await processor.integrate_with_consciousness_bridge([])

        assert result == []


class TestProcessMegatagsAsync:
    """Tests for MegaTagProcessor.process_megatags() async pipeline."""

    @pytest.mark.asyncio
    async def test_process_megatags_full_pipeline(self):
        """Full pipeline: validate → extract → integrate."""
        processor = MegaTagProcessor()
        processor.consciousness_bridge = MagicMock()

        megatags = ["TYPE⨳DATA⦾point1", "invalid", "OTHER⨳VALUE"]
        result = await processor.process_megatags(megatags)

        # 2 valid tags after validation
        assert len(result) == 2
        # Both should be integrated
        assert all(r.get("integrated") is True for r in result)

    @pytest.mark.asyncio
    async def test_process_megatags_no_valid_tags(self):
        """Pipeline with no valid quantum symbols."""
        processor = MegaTagProcessor()

        megatags = ["plain", "no_symbols", "regular-tag"]
        result = await processor.process_megatags(megatags)

        assert result == []

    @pytest.mark.asyncio
    async def test_process_megatags_without_bridge(self):
        """Pipeline without consciousness bridge."""
        processor = MegaTagProcessor()
        processor.consciousness_bridge = None

        megatags = ["TYPE⨳DATA", "OTHER⨳VALUE"]
        result = await processor.process_megatags(megatags)

        # Should return extracted semantics directly (not wrapped)
        assert len(result) == 2
        assert result[0]["type"] == "TYPE"
        assert result[1]["type"] == "OTHER"
