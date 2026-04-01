"""Symbolic Cognition Engine - Pattern recognition and consciousness calculations.

Part of the Consciousness Bridge system for ΞNuSyQ multi-agent coordination.
"""

from typing import Any


class SymbolicCognition:
    """Symbolic reasoning engine with pattern recognition and consciousness calculations."""

    def __init__(self):
        """Initialize cognition engine."""
        self.patterns: dict[str, list[str]] = {}
        self.reasoning_history: list[dict[str, Any]] = []

    async def reason(self, input_data: str) -> dict[str, Any]:
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

    async def recognize_patterns(self, data: str) -> list[str]:
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
        word_counts: dict[str, int] = {}
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

    def calculate_consciousness_level(self, patterns: list[str]) -> float:
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

    def get_reasoning_history(self) -> list[dict[str, Any]]:
        """Get history of all reasoning operations.

        Returns:
            List of reasoning results
        """
        return self.reasoning_history.copy()
