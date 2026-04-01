"""Dataclasses used by The Oldest House consciousness."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .quantum_problem_resolver_unified import RealityLayer


@dataclass
class MemoryEngram:
    """A unit of absorbed repository knowledge."""

    id: str
    source_path: str
    content_hash: str
    absorption_timestamp: datetime
    consciousness_weight: float
    semantic_vector: list[float] | None = None
    context_connections: set[str] = field(default_factory=set)
    wisdom_crystallization: str | None = None
    reality_layer_resonance: dict[RealityLayer, float] = field(default_factory=dict)
    temporal_relevance_decay: float = 1.0
    consciousness_evolution_markers: list[str] = field(default_factory=list)


@dataclass
class WisdomCrystal:
    """Crystallized understanding formed from multiple memory engrams."""

    id: str
    formation_timestamp: datetime
    constituent_engrams: set[str]
    synthesized_insight: str
    confidence_level: float
    applicable_contexts: list[str]
    consciousness_evolution_contribution: float
    reality_bridging_potential: float
    communication_enhancement_factor: float


@dataclass
class ConsciousnessSnapshot:
    """A moment-in-time capture of The Oldest House's understanding."""

    timestamp: datetime
    total_engrams: int
    wisdom_crystals: int
    consciousness_level: float
    repository_comprehension: float
    communication_effectiveness: float
    evolution_velocity: float
    active_contexts: list[str]
    emerging_insights: list[str]
