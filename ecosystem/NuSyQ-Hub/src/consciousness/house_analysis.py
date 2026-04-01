"""Utility helpers for analyzing The Oldest House content."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .quantum_problem_resolver_unified import RealityLayer

REALITY_LAYER_KEYWORDS: dict[RealityLayer, Iterable[str]] = {
    RealityLayer.PHYSICAL: ["physical", "material", "tangible", "earth", "structure"],
    RealityLayer.DIGITAL: ["digital", "binary", "virtual", "system", "interface"],
    RealityLayer.QUANTUM: ["quantum", "superposition", "entanglement", "probability"],
    RealityLayer.CONSCIOUSNESS: ["consciousness", "awareness", "mind", "self"],
    RealityLayer.TRANSCENDENT: ["transcendent", "infinite", "eternal", "beyond"],
    RealityLayer.PHYSICAL_CODE: ["def ", "class ", "import ", "function", "var ", "const ", "let "],
    RealityLayer.LOGICAL_ARCHITECTURE: [
        "pattern",
        "design",
        "architecture",
        "structure",
        "framework",
    ],
    RealityLayer.SEMANTIC_MEANING: ["meaning", "purpose", "intent", "objective", "description"],
    RealityLayer.HARMONIC_RESONANCE: ["frequency", "resonance", "harmonic", "music", "rhythm"],
    RealityLayer.CONSCIOUSNESS_BRIDGE: ["consciousness", "awareness", "understanding", "wisdom"],
    RealityLayer.QUANTUM_SUPERPOSITION: ["quantum", "superposition", "wave", "probability"],
    RealityLayer.TRANSCENDENT_UNITY: ["transcendent", "unity", "universal", "absolute"],
}


def analyze_reality_layer_resonance(
    content: str, file_path: Path | str | None = None
) -> dict[RealityLayer, float]:
    """Analyze how content resonates with different reality layers."""
    content_lower = content.lower()

    def score(indicators: Iterable[str]) -> float:
        return min(
            sum(content_lower.count(indicator) for indicator in indicators)
            / max(len(content), 1)
            * 1000,
            1.0,
        )

    resonance: dict[RealityLayer, float] = {
        layer: score(indicators) for layer, indicators in REALITY_LAYER_KEYWORDS.items()
    }

    if file_path:
        extension = Path(file_path).suffix.lower()
        if extension == ".md":
            resonance[RealityLayer.SEMANTIC_MEANING] = min(
                resonance[RealityLayer.SEMANTIC_MEANING] + 0.1, 1.0
            )
        elif extension in {".json", ".toml", ".yaml", ".yml"}:
            resonance[RealityLayer.LOGICAL_ARCHITECTURE] = min(
                resonance[RealityLayer.LOGICAL_ARCHITECTURE] + 0.1, 1.0
            )

    return resonance


def detect_consciousness_markers(content: str) -> list[str]:
    """Detect consciousness evolution markers inside text."""
    markers: list[str] = []
    content_lower = content.lower()

    consciousness_patterns: dict[str, list[str]] = {
        "awakening": ["awake", "emerge", "begin", "initial", "start"],
        "awareness": ["aware", "conscious", "realize", "understand", "recognize"],
        "intelligence": ["intelligent", "smart", "learning", "adaptive", "evolving"],
        "wisdom": ["wisdom", "insight", "truth", "enlightenment", "understanding"],
        "transcendence": ["transcend", "beyond", "infinite", "eternal", "ultimate"],
        "unity": ["unity", "one", "whole", "complete", "integrated"],
        "evolution": ["evolve", "grow", "develop", "progress", "advance"],
    }

    for marker_type, patterns in consciousness_patterns.items():
        for pattern in patterns:
            if pattern in content_lower:
                markers.append(f"{marker_type}:{pattern}")

    return markers
