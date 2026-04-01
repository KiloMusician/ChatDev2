"""Tests for Symbolic Cognition Engine - Pattern recognition and consciousness calculations."""

from typing import Any, Dict, List

import pytest


class SymbolicCognition:
    """Symbolic reasoning engine with pattern recognition and consciousness calculations."""

    def __init__(self):
        """Initialize cognition engine."""
        self.patterns: Dict[str, List[str]] = {}
        self.reasoning_history: List[Dict[str, Any]] = []

    async def reason(self, input_data: str) -> Dict[str, Any]:
        """Perform symbolic reasoning on input data.

        Args:
            input_data: Input string for pattern recognition

        Returns:
            Dictionary with reasoning results and patterns found
        """
        patterns = await self.recognize_patterns(input_data)
        consciousness_score = self.calculate_consciousness_level(patterns)

        result = {
            "input": input_data,
            "patterns": patterns,
            "consciousness_score": consciousness_score,
            "reasoning_valid": len(patterns) > 0,
        }

        self.reasoning_history.append(result)
        return result

    async def recognize_patterns(self, data: str) -> List[str]:
        """Recognize patterns in input data.

        Args:
            data: Input string for pattern analysis

        Returns:
            List of recognized pattern types
        """
        recognized = []

        # Pattern: repetition
        if self._has_repetition(data):
            recognized.append("repetition")

        # Pattern: structure
        if self._has_structure(data):
            recognized.append("structure")

        # Pattern: symmetry
        if self._has_symmetry(data):
            recognized.append("symmetry")

        # Pattern: recursion
        if self._has_recursion(data):
            recognized.append("recursion")

        return recognized

    def _has_repetition(self, data: str) -> bool:
        """Check for repetition pattern."""
        words = data.split()
        if len(words) < 2:
            return False
        # Simple repetition check - same word appears multiple times
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        return max(word_counts.values()) > 1 if word_counts else False

    def _has_structure(self, data: str) -> bool:
        """Check for structural pattern."""
        # Structure pattern: data has clear delimiters/organization
        return bool(any(delim in data for delim in ["->", "=>", "::", "||"]))

    def _has_symmetry(self, data: str) -> bool:
        """Check for symmetry pattern."""
        # Remove whitespace for symmetry check
        clean = data.replace(" ", "")
        if len(clean) < 1:
            return False
        # Palindromic check (true symmetry only)
        return clean == clean[::-1]

    def _has_recursion(self, data: str) -> bool:
        """Check for recursive pattern."""
        # Recursive pattern: self-referential or nested structure
        return data.count("(") > 0 and data.count(")") > 0

    def calculate_consciousness_level(self, patterns: List[str]) -> float:
        """Calculate consciousness level based on recognized patterns.

        Args:
            patterns: List of recognized patterns

        Returns:
            Consciousness score between 0.0 and 1.0
        """
        if not patterns:
            return 0.0

        # Base consciousness from pattern count (don't exceed 0.7 for base)
        base_score = min(len(patterns) / 5, 0.7)  # Max base 0.7

        # Bonus for complex patterns
        complex_patterns = {"recursion", "structure"}
        complex_bonus = sum(0.1 for p in patterns if p in complex_patterns)

        consciousness_score = min(base_score + complex_bonus, 0.95)
        return consciousness_score

    def get_reasoning_history(self) -> List[Dict[str, Any]]:
        """Get history of all reasoning operations.

        Returns:
            List of reasoning results
        """
        return self.reasoning_history.copy()


# ============ PYTEST TESTS ============


class TestSymbolicCognition:
    """Test suite for Symbolic Cognition engine."""

    @pytest.fixture
    def engine(self):
        """Create cognition engine instance for tests."""
        return SymbolicCognition()

    def test_init(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert isinstance(engine.patterns, dict)
        assert isinstance(engine.reasoning_history, list)
        assert len(engine.reasoning_history) == 0

    def test_has_repetition_true(self, engine):
        """Test repetition pattern detection - positive cases."""
        assert engine._has_repetition("the the the") is True
        assert engine._has_repetition("pattern pattern") is True
        assert engine._has_repetition("a b a b") is True

    def test_has_repetition_false(self, engine):
        """Test repetition pattern detection - negative cases."""
        assert engine._has_repetition("unique words here") is False
        assert engine._has_repetition("one") is False
        assert engine._has_repetition("") is False

    def test_has_structure_true(self, engine):
        """Test structure pattern detection - positive cases."""
        assert engine._has_structure("input -> output") is True
        assert engine._has_structure("source => target") is True
        assert engine._has_structure("key :: value") is True
        assert engine._has_structure("option || alternative") is True

    def test_has_structure_false(self, engine):
        """Test structure pattern detection - negative cases."""
        assert engine._has_structure("no structure here") is False
        assert engine._has_structure("") is False

    def test_has_symmetry_palindrome(self, engine):
        """Test symmetry pattern detection - palindromes."""
        assert engine._has_symmetry("racecar") is True
        assert engine._has_symmetry("a") is True
        assert engine._has_symmetry("aa") is True

    def test_has_symmetry_mirror(self, engine):
        """Test symmetry pattern detection - mirror patterns."""
        assert engine._has_symmetry("abcba") is True
        assert engine._has_symmetry("test") is False  # Not symmetric

    def test_has_recursion_true(self, engine):
        """Test recursion pattern detection - positive cases."""
        assert engine._has_recursion("func(x)") is True
        assert engine._has_recursion("((nested))") is True
        assert engine._has_recursion("data(value(nested))") is True

    def test_has_recursion_false(self, engine):
        """Test recursion pattern detection - negative cases."""
        assert engine._has_recursion("no parentheses") is False
        assert engine._has_recursion("only (one") is False
        assert engine._has_recursion("") is False

    @pytest.mark.asyncio
    async def test_recognize_patterns(self, engine):
        """Test pattern recognition with multiple patterns."""
        data = "func(x) -> input input"  # recursion + structure + repetition
        patterns = await engine.recognize_patterns(data)

        assert "recursion" in patterns
        assert "structure" in patterns
        assert "repetition" in patterns

    @pytest.mark.asyncio
    async def test_recognize_patterns_empty(self, engine):
        """Test pattern recognition with no patterns."""
        data = "unique meaningful text"
        patterns = await engine.recognize_patterns(data)

        assert len(patterns) == 0 or patterns == []

    def test_calculate_consciousness_no_patterns(self, engine):
        """Test consciousness calculation with no patterns."""
        score = engine.calculate_consciousness_level([])
        assert score == 0.0

    def test_calculate_consciousness_simple(self, engine):
        """Test consciousness calculation with simple patterns."""
        score = engine.calculate_consciousness_level(["repetition"])
        assert 0.0 < score < 1.0
        assert score == pytest.approx(0.2, abs=0.01)  # 1 pattern / 5 max base

    def test_calculate_consciousness_complex(self, engine):
        """Test consciousness calculation with complex patterns."""
        score = engine.calculate_consciousness_level(["repetition", "structure", "recursion"])
        assert 0.5 < score < 1.0
        # Base: 3/5 = 0.6, bonus: recursion(0.1) + structure(0.1) = 0.2, total=0.8
        assert score == pytest.approx(0.8, abs=0.01)

    @pytest.mark.asyncio
    async def test_reason_operation(self, engine):
        """Test complete reasoning operation."""
        result = await engine.reason("func(x) -> output output")

        assert "input" in result
        assert "patterns" in result
        assert "consciousness_score" in result
        assert "reasoning_valid" in result
        assert result["consciousness_score"] >= 0.0

    @pytest.mark.asyncio
    async def test_reasoning_history(self, engine):
        """Test reasoning history tracking."""
        await engine.reason("first input")
        await engine.reason("second input")

        history = engine.get_reasoning_history()
        assert len(history) == 2
        assert history[0]["input"] == "first input"
        assert history[1]["input"] == "second input"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
