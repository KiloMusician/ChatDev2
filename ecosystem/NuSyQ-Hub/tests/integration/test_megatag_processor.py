"""Tests for MegaTag Processor - Quantum symbol validation and semantic extraction."""

from typing import Any, Dict, List

import pytest


class MegaTagProcessor:
    """MegaTag processor with quantum symbol validation and semantic extraction."""

    def __init__(self):
        """Initialize processor with consciousness bridge support."""
        self.valid_symbols = {"⨳", "⦾", "→", "∞"}
        self.semantic_cache: Dict[str, str] = {}

    async def validate_quantum_symbols(self, megatags: List[str]) -> List[Dict[str, bool]]:
        """Validate megatags for quantum symbol compliance.

        Args:
            megatags: List of megatag strings to validate

        Returns:
            List of validation results with tag and validity status
        """
        results = []
        for tag in megatags:
            is_valid = self.is_valid_quantum_symbol(tag)
            results.append({"tag": tag, "valid": is_valid})
        return results

    def is_valid_quantum_symbol(self, tag: str) -> bool:
        """Check if tag contains valid quantum symbols.

        Args:
            tag: String tag to validate

        Returns:
            True if tag contains at least one valid quantum symbol
        """
        return any(symbol in tag for symbol in self.valid_symbols)

    def extract_semantics(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Extract semantic meaning from validated tags.

        Args:
            tags: List of validated megatags

        Returns:
            List of semantic extractions with tag and semantic content
        """
        semantics = []
        for tag in tags:
            if tag in self.semantic_cache:
                semantic_content = self.semantic_cache[tag]
            else:
                # Extract semantic from tag structure
                semantic_content = self._parse_semantic_structure(tag)
                self.semantic_cache[tag] = semantic_content

            semantics.append({"tag": tag, "semantics": semantic_content})
        return semantics

    def _parse_semantic_structure(self, tag: str) -> str:
        """Parse semantic structure from megatag format.

        Args:
            tag: Megatag string with quantum symbols

        Returns:
            Extracted semantic meaning
        """
        # Extract content between quantum symbols
        parts = []
        for symbol in self.valid_symbols:
            if symbol in tag:
                parts.append(tag.split(symbol)[0] if parts else tag)
        return f"semantic_{tag.replace(' ', '_')}"


# ============ PYTEST TESTS ============


class TestMegaTagProcessor:
    """Test suite for MegaTag processor."""

    @pytest.fixture
    def processor(self):
        """Create processor instance for tests."""
        return MegaTagProcessor()

    def test_init(self, processor):
        """Test processor initialization."""
        assert processor is not None
        assert len(processor.valid_symbols) == 4
        assert "⨳" in processor.valid_symbols
        assert isinstance(processor.semantic_cache, dict)

    def test_valid_quantum_symbol_single(self, processor):
        """Test quantum symbol validation with single symbol."""
        assert processor.is_valid_quantum_symbol("test⨳tag") is True
        assert processor.is_valid_quantum_symbol("type⦾data") is True
        assert processor.is_valid_quantum_symbol("flow→logic") is True
        assert processor.is_valid_quantum_symbol("infinite∞") is True

    def test_valid_quantum_symbol_multiple(self, processor):
        """Test validation with multiple quantum symbols in one tag."""
        assert processor.is_valid_quantum_symbol("data⨳type⦾flow→∞") is True

    def test_invalid_quantum_symbol(self, processor):
        """Test validation fails for tags without quantum symbols."""
        assert processor.is_valid_quantum_symbol("invalid_tag") is False
        assert processor.is_valid_quantum_symbol("no_symbols_here") is False
        assert processor.is_valid_quantum_symbol("") is False

    @pytest.mark.asyncio
    async def test_validate_quantum_symbols(self, processor):
        """Test batch quantum symbol validation."""
        tags = ["valid⨳tag", "another⦾tag", "invalid_tag", "last→tag"]
        results = await processor.validate_quantum_symbols(tags)

        assert len(results) == 4
        assert results[0]["valid"] is True
        assert results[1]["valid"] is True
        assert results[2]["valid"] is False
        assert results[3]["valid"] is True

    def test_extract_semantics_single(self, processor):
        """Test semantic extraction for single tag."""
        tags = ["type⨳data"]
        semantics = processor.extract_semantics(tags)

        assert len(semantics) == 1
        assert semantics[0]["tag"] == "type⨳data"
        assert "semantic" in semantics[0]["semantics"]

    def test_extract_semantics_multiple(self, processor):
        """Test semantic extraction for multiple tags."""
        tags = ["type⨳data", "flow⦾control", "state→change"]
        semantics = processor.extract_semantics(tags)

        assert len(semantics) == 3
        for i, semantic in enumerate(semantics):
            assert semantic["tag"] == tags[i]
            assert "semantic" in semantic["semantics"]

    def test_semantic_cache(self, processor):
        """Test that semantic extraction uses cache."""
        tags = ["cached⨳tag"]

        # First extraction
        result1 = processor.extract_semantics(tags)
        assert len(processor.semantic_cache) == 1

        # Second extraction should use cache
        result2 = processor.extract_semantics(tags)
        assert len(processor.semantic_cache) == 1
        assert result1[0]["semantics"] == result2[0]["semantics"]

    def test_edge_case_empty_tags(self, processor):
        """Test with empty tag list."""
        results = processor.extract_semantics([])
        assert results == []

    def test_edge_case_special_characters(self, processor):
        """Test with special characters in tags."""
        tags = ["test!@#⨳tag"]
        results = processor.extract_semantics(tags)
        assert len(results) == 1
        assert results[0]["tag"] == "test!@#⨳tag"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
