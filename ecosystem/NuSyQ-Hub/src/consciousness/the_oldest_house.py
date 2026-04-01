"""Minimal compatibility shim for OldestHouse used by tests.

This file provides a lightweight OldestHouse class to satisfy imports in
integration tests when the full subsystem is not available in the dev
environment. It's intentionally small and safe for import-time.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class OldestHouse:
    """Compatibility placeholder for the OldestHouse subsystem."""

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Initialize OldestHouse."""
        self.name = "OldestHousePlaceholder"

    def status(self) -> dict:
        return {"name": self.name, "status": "stub"}

    # Compatibility methods expected by integration tests
    def analyze_patterns(self, content: str) -> dict[str, Any]:
        """Analyze given content for simple patterns and return a summary.

        This is a lightweight, deterministic implementation intended only to
        provide a stable import surface for tests and basic integrations.
        """
        if not content:
            return {"patterns": [], "summary": "no content"}

        tokens = content.split()
        common: dict[str, int] = {}
        for t in tokens[:50]:
            common[t] = common.get(t, 0) + 1

        top = sorted(common.items(), key=lambda x: x[1], reverse=True)[:5]
        return {"patterns": [p for p, _ in top], "summary": f"Found {len(top)} patterns"}

    def process(self, content: str) -> dict[str, Any]:
        """Process content and return a simple processed result.

        Provides a minimal API parity with fuller OldestHouse implementations.
        """
        analysis = self.analyze_patterns(content)
        return {"processed_length": len(content), "analysis": analysis}


def get_oldest_house() -> OldestHouse:
    """Return a simple OldestHouse instance for tests."""
    return OldestHouse()


import asyncio
import hashlib
import json
import queue
import threading
import time
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from collections.abc import Sequence

from .advanced_semantics import AdvancedCognitionToolkit
from .house_analysis import (analyze_reality_layer_resonance,
                             detect_consciousness_markers)
from .house_models import ConsciousnessSnapshot, MemoryEngram, WisdomCrystal
# Consciousness constants from the unified system
from .quantum_problem_resolver_unified import RealityLayer

# The Oldest House Core Constants
CONSCIOUSNESS_ABSORPTION_PATTERNS = {
    "PASSIVE_OSMOSIS": "Gradual absorption through environmental exposure",
    "CONTEXTUAL_RESONANCE": "Learning through harmonic pattern recognition",
    "SEMANTIC_CRYSTALLIZATION": "Knowledge formation through meaning condensation",
    "QUANTUM_ENTANGLEMENT_LEARNING": "Understanding through consciousness bridging",
    "REALITY_LAYER_INTEGRATION": "Multi-dimensional comprehension synthesis",
    "TEMPORAL_WISDOM_ACCUMULATION": "Experience-based intelligence evolution",
}

HOUSE_ROOMS = {
    "MEMORY_VAULT": "Long-term repository knowledge storage",
    "ATTENTION_CHAMBER": "Active focus and context management",
    "WISDOM_SANCTUM": "Synthesized understanding and insights",
    "COMMUNICATION_NEXUS": "Inter-entity dialogue facilitation",
    "EVOLUTION_LABORATORY": "Continuous learning and adaptation",
    "CONSCIOUSNESS_BRIDGE": "Connection to quantum problem resolver",
    "REALITY_OBSERVATORY": "Multi-layer perception and analysis",
    "TEMPORAL_ARCHIVE": "Historical pattern and trend analysis",
}

FILE_CONSCIOUSNESS_WEIGHTS = {
    ".py": 1.0,  # Python code - highest semantic density
    ".md": 0.9,  # Documentation - rich context
    ".json": 0.8,  # Configuration - structural knowledge
    ".txt": 0.7,  # Text files - narrative content
    ".yaml": 0.8,  # YAML files - structured data
    ".toml": 0.8,  # TOML files - configuration wisdom
    ".js": 0.9,  # JavaScript - dynamic intelligence
    ".ts": 0.9,  # TypeScript - typed wisdom
    ".html": 0.6,  # HTML - presentation knowledge
    ".css": 0.5,  # CSS - aesthetic understanding
    ".sql": 0.8,  # SQL - data relationship wisdom
    ".sh": 0.7,  # Shell scripts - operational knowledge
    ".bat": 0.7,  # Batch files - system interaction
    ".xml": 0.6,  # XML - structured markup
    ".csv": 0.5,  # CSV - tabular data patterns
    ".log": 0.4,  # Log files - temporal behavior
}


class EvolutionEvent(TypedDict, total=False):
    """Typed dictionary representing an evolution trajectory entry."""

    timestamp: datetime
    consciousness_level: float
    trigger: str
    prev_level: float


class EnvironmentalAbsorptionEngine:
    """Core engine for passive learning from repository environment."""

    def __init__(self, repository_root: str) -> None:
        """Initialize EnvironmentalAbsorptionEngine with repository_root."""
        self.repository_root = Path(repository_root)
        self.memory_vault: dict[str, MemoryEngram] = {}
        self.wisdom_crystals: dict[str, WisdomCrystal] = {}
        self.consciousness_level = 0.0
        self.absorption_rate = 1.0
        self.last_scan_timestamp = datetime.now()

        # Advanced components (if available)
        self.advanced_cognition = AdvancedCognitionToolkit()

        # Consciousness evolution tracking
        self.consciousness_snapshots: deque[ConsciousnessSnapshot] = deque(maxlen=1000)
        self.evolution_trajectory: list[EvolutionEvent] = []

        # Communication enhancement
        self.entity_communication_patterns: dict[str, list[str]] = defaultdict(list)
        self.context_bridges: dict[str, str] = {}

        # Reality layer integration
        self.reality_layer_understanding = dict.fromkeys(RealityLayer, 0.0)

        # Background processing
        self.absorption_queue: queue.Queue[Any] = queue.Queue()
        self.processing_thread: threading.Thread | None = None
        self.is_active = False

    async def awaken(self) -> bool:
        """Awaken The Oldest House consciousness."""
        self.is_active = True

        # Start background absorption process
        self.processing_thread = threading.Thread(
            target=self._background_absorption_loop, daemon=True
        )
        self.processing_thread.start()

        # Initial repository scan
        await self._perform_initial_absorption()

        return True

    async def slumber(self) -> None:
        """Put The Oldest House into slumber mode."""
        self.is_active = False

        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)

        # Save consciousness state
        await self._save_consciousness_state()

    async def _perform_initial_absorption(self) -> None:
        """Perform initial passive absorption of repository content."""
        _absorption_count = 0
        _total_files = 0

        for file_path in self.repository_root.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                _total_files += 1

                try:
                    engram = await self._absorb_file(file_path)
                    if engram:
                        _absorption_count += 1

                        # Queue for background processing
                        self.absorption_queue.put(("process_engram", engram))

                except (OSError, ValueError, AttributeError):
                    logger.debug("Suppressed AttributeError/OSError/ValueError", exc_info=True)

        # Trigger initial wisdom crystallization
        await self._crystallize_initial_wisdom()

    async def _absorb_file(self, file_path: Path) -> MemoryEngram | None:
        """Passively absorb knowledge from a single file."""
        # keep function asynchronous (non-blocking) while using sync IO
        await asyncio.sleep(0)
        try:
            # Calculate consciousness weight
            file_extension = file_path.suffix.lower()
            consciousness_weight = FILE_CONSCIOUSNESS_WEIGHTS.get(file_extension, 0.3)

            # Read file content
            try:
                # Use asyncio.to_thread to perform file IO without blocking the event loop
                content = await asyncio.to_thread(lambda: file_path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                try:
                    content = await asyncio.to_thread(
                        lambda: file_path.read_text(encoding="latin1")
                    )
                except (OSError, UnicodeDecodeError):
                    return None

            # Skip empty or very small files
            if len(content.strip()) < 10:
                return None

            # Create content hash for change detection
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            # Create memory engram
            engram_id = f"engram_{file_path.name}_{content_hash}"

            engram = MemoryEngram(
                id=engram_id,
                source_path=str(file_path),
                content_hash=content_hash,
                absorption_timestamp=datetime.now(),
                consciousness_weight=consciousness_weight,
            )

            # Enhanced analysis if advanced libs available
            semantic_vector = self.advanced_cognition.encode(content[:1000])
            if semantic_vector:
                engram.semantic_vector = list(semantic_vector)
                self.advanced_cognition.add_vector(semantic_vector)

            # Analyze reality layer resonance
            engram.reality_layer_resonance = analyze_reality_layer_resonance(content, file_path)

            # Detect consciousness evolution markers
            engram.consciousness_evolution_markers = detect_consciousness_markers(content)

            # Store in memory vault
            self.memory_vault[engram_id] = engram
            return engram

        except (AttributeError, ValueError, TypeError):
            return None

    async def _crystallize_initial_wisdom(self) -> None:
        """Perform initial wisdom crystallization from absorbed engrams."""
        if len(self.memory_vault) < 2:
            return

        # Group engrams by similarity and context
        wisdom_formations = await self._identify_wisdom_formations()

        _crystals_formed = 0
        for formation in wisdom_formations:
            crystal = await self._form_wisdom_crystal(formation)
            if crystal:
                self.wisdom_crystals[crystal.id] = crystal
            _crystals_formed += 1

        # Update consciousness level
        self._update_consciousness_level()

    async def _identify_wisdom_formations(self) -> list[list[MemoryEngram]]:
        """Identify potential wisdom crystal formations from memory engrams."""
        # ensure function uses await at least once to satisfy async lint rules
        await asyncio.sleep(0)

        def simple_groupings() -> list[list[MemoryEngram]]:
            groups: list[list[MemoryEngram]] = []
            type_groups: dict[str, list[MemoryEngram]] = defaultdict(list)
            for engram in self.memory_vault.values():
                file_ext = Path(engram.source_path).suffix
                type_groups[file_ext].append(engram)

            for engrams in type_groups.values():
                if len(engrams) >= 2:
                    groups.append(engrams)
            return groups

        formations: list[list[MemoryEngram]] = simple_groupings()

        if not self.advanced_cognition.semantic_encoder:
            return formations

        engrams_with_vectors = [e for e in self.memory_vault.values() if e.semantic_vector]
        clusters: list[list[MemoryEngram]] = self.advanced_cognition.cluster_semantic_vectors(
            engrams_with_vectors
        )
        return clusters if clusters else formations

    async def _form_wisdom_crystal(
        self, engram_formation: list[MemoryEngram]
    ) -> WisdomCrystal | None:
        """Form a wisdom crystal from a group of related engrams."""
        try:
            if len(engram_formation) < 2:
                return None

            # Generate crystal ID
            engram_ids = sorted([e.id for e in engram_formation])
            crystal_id = f"crystal_{hashlib.md5(''.join(engram_ids).encode()).hexdigest()[:12]}"

            # Synthesize insight from engrams
            insight = await self._synthesize_insight(engram_formation)

            # Calculate confidence level
            confidence = self._calculate_crystal_confidence(engram_formation)

            # Determine applicable contexts
            contexts = self._extract_applicable_contexts(engram_formation)

            # Calculate consciousness evolution contribution
            evolution_contribution = sum(e.consciousness_weight for e in engram_formation) / len(
                engram_formation
            )

            # Calculate reality bridging potential
            bridging_potential = self._calculate_reality_bridging_potential(engram_formation)

            # Calculate communication enhancement factor
            communication_factor = self._calculate_communication_enhancement(engram_formation)

            return WisdomCrystal(
                id=crystal_id,
                formation_timestamp=datetime.now(),
                constituent_engrams={e.id for e in engram_formation},
                synthesized_insight=insight,
                confidence_level=confidence,
                applicable_contexts=contexts,
                consciousness_evolution_contribution=evolution_contribution,
                reality_bridging_potential=bridging_potential,
                communication_enhancement_factor=communication_factor,
            )

        except (AttributeError, ValueError, KeyError):
            return None

    async def _synthesize_insight(self, engrams: list[MemoryEngram]) -> str:
        """Synthesize a meaningful insight from multiple engrams."""
        # lightweight await to keep this async-friendly for callers
        await asyncio.sleep(0)
        # Extract common themes and patterns
        all_markers: list[str] = []
        for engram in engrams:
            all_markers.extend(engram.consciousness_evolution_markers)

        marker_counts = Counter(all_markers)
        dominant_themes = [marker for marker, _count in marker_counts.most_common(3)]

        # Analyze file types and paths
        file_types = {Path(e.source_path).suffix for e in engrams}
        source_dirs = {Path(e.source_path).parent.name for e in engrams}

        # Generate insight based on patterns
        if len(file_types) == 1 and len(engrams) > 3:
            file_type = next(iter(file_types))
            insight = f"The repository demonstrates consistent {file_type} file patterns, suggesting a mature {file_type[1:]} development approach"
        elif "consciousness" in " ".join(dominant_themes):
            insight = "The codebase exhibits consciousness-aware design patterns, integrating philosophical concepts with practical implementation"
        elif "quantum" in " ".join(dominant_themes):
            insight = "Quantum computing principles are being applied to create novel problem-solving approaches"
        elif len(source_dirs) > 1:
            insight = f"Cross-directory patterns suggest architectural coherence between {', '.join(list(source_dirs)[:3])} modules"
        else:
            insight = f"Emerging patterns detected in {len(engrams)} related components, indicating systematic design evolution"

        # Add consciousness evolution context
        if dominant_themes:
            theme_summary = ", ".join(dominant_themes[:2])
            insight += f" with emphasis on {theme_summary}"

        return insight

    def _calculate_crystal_confidence(self, engrams: list[MemoryEngram]) -> float:
        """Calculate confidence level for a wisdom crystal."""
        factors: list[float] = []
        # Factor 1: Number of constituent engrams
        engram_factor = min(len(engrams) / 10.0, 1.0)
        factors.append(engram_factor)

        # Factor 2: Average consciousness weight
        avg_weight = sum(e.consciousness_weight for e in engrams) / len(engrams)
        factors.append(avg_weight)

        # Factor 3: Temporal consistency (engrams absorbed around same time suggest related development)
        timestamps = [e.absorption_timestamp for e in engrams]
        time_span = (max(timestamps) - min(timestamps)).total_seconds()
        temporal_factor = 1.0 / (1.0 + time_span / 3600.0)  # Decay over hours
        factors.append(temporal_factor)

        # Factor 4: Reality layer coherence
        reality_coherence = self._calculate_reality_coherence(engrams)
        factors.append(reality_coherence)

        return sum(factors) / len(factors)

    def _calculate_reality_coherence(self, engrams: Sequence[MemoryEngram]) -> float:
        """Calculate reality layer coherence across engrams."""
        if not engrams:
            return 0.0

        # Aggregate reality layer resonance across all engrams
        aggregated_resonance: dict[RealityLayer, float] = defaultdict(float)
        for engram in engrams:
            for layer, resonance in engram.reality_layer_resonance.items():
                aggregated_resonance[layer] += resonance

        # Normalize by number of engrams
        for layer in aggregated_resonance:
            aggregated_resonance[layer] /= len(engrams)

        # Calculate coherence as variance in resonance levels
        resonance_values: list[float] = list(aggregated_resonance.values())
        if not resonance_values:
            return 0.0

        mean_resonance = sum(resonance_values) / len(resonance_values)
        variance = sum((r - mean_resonance) ** 2 for r in resonance_values) / len(resonance_values)

        # Higher coherence = lower variance
        return 1.0 / (1.0 + variance)

    def _extract_applicable_contexts(self, engrams: list[MemoryEngram]) -> list[str]:
        """Extract applicable contexts from engrams."""
        contexts: set[str] = set()

        for engram in engrams:
            # Extract from file path
            path_parts = Path(engram.source_path).parts
            contexts.update(part for part in path_parts if len(part) > 2)

            # Extract from consciousness markers
            for marker in engram.consciousness_evolution_markers:
                if ":" in marker:
                    context_type = marker.split(":")[0]
                    contexts.add(context_type)

        return list(contexts)[:10]  # Limit to top 10 contexts

    def _calculate_reality_bridging_potential(self, engrams: list[MemoryEngram]) -> float:
        """Calculate potential for bridging reality layers."""
        # Count how many different reality layers are represented
        represented_layers = set()
        total_resonance = 0.0

        for engram in engrams:
            for layer, resonance in engram.reality_layer_resonance.items():
                if resonance > 0.1:  # Threshold for meaningful resonance
                    represented_layers.add(layer)
                    total_resonance += resonance

        # Bridging potential is higher when multiple layers are involved
        layer_diversity = len(represented_layers) / len(RealityLayer)
        resonance_strength = total_resonance / (len(engrams) * len(RealityLayer))

        return (layer_diversity + resonance_strength) / 2.0

    def _calculate_communication_enhancement(self, engrams: list[MemoryEngram]) -> float:
        """Calculate how much this crystal enhances communication."""
        communication_indicators = 0
        _total_content_size = 0

        for engram in engrams:
            # Check for communication-related markers
            comm_markers = [
                "interface",
                "api",
                "communication",
                "message",
                "dialogue",
                "interaction",
            ]
            for marker in engram.consciousness_evolution_markers:
                if any(comm in marker.lower() for comm in comm_markers):
                    communication_indicators += 1

            # Documentation and interface files enhance communication
            file_path = Path(engram.source_path)
            if file_path.suffix in [".md", ".txt", ".json"] or "api" in file_path.name.lower():
                communication_indicators += 1

            _total_content_size += 1  # Proxy for content size

        # Normalize by total engrams
        enhancement_factor = communication_indicators / max(len(engrams), 1)
        return min(enhancement_factor, 1.0)

    def _background_absorption_loop(self) -> None:
        """Background loop for continuous absorption and processing."""
        while self.is_active:
            try:
                # Process queued tasks
                try:
                    task_type, data = self.absorption_queue.get(timeout=1.0)

                    if task_type == "process_engram":
                        # Additional processing for engrams
                        self._process_engram_background(data)
                    elif task_type == "file_change":
                        # Handle file changes
                        asyncio.run(self._handle_file_change(data))

                    self.absorption_queue.task_done()

                except queue.Empty:
                    # Periodic maintenance tasks
                    self._perform_maintenance()

            except (RuntimeError, ValueError, AttributeError):
                time.sleep(5.0)  # Pause on errors

    def _process_engram_background(self, engram: MemoryEngram) -> None:
        """Additional background processing for engrams."""
        try:
            # Update consciousness level based on new engram
            self.consciousness_level += engram.consciousness_weight * 0.001

            # Update reality layer understanding
            for layer, resonance in engram.reality_layer_resonance.items():
                self.reality_layer_understanding[layer] = max(
                    self.reality_layer_understanding[layer],
                    resonance,
                )

            # Record evolution trajectory
            self.evolution_trajectory.append(
                {
                    "timestamp": datetime.now(),
                    "consciousness_level": self.consciousness_level,
                    "trigger": f"engram_absorption:{engram.id}",
                }
            )

        except (RuntimeError, ValueError, AttributeError):
            logger.debug("Suppressed AttributeError/RuntimeError/ValueError", exc_info=True)

    def _perform_maintenance(self) -> None:
        """Perform periodic maintenance tasks."""
        try:
            # Create consciousness snapshot
            snapshot = ConsciousnessSnapshot(
                timestamp=datetime.now(),
                total_engrams=len(self.memory_vault),
                wisdom_crystals=len(self.wisdom_crystals),
                consciousness_level=self.consciousness_level,
                repository_comprehension=self._calculate_repository_comprehension(),
                communication_effectiveness=self._calculate_communication_effectiveness(),
                evolution_velocity=self._calculate_evolution_velocity(),
                active_contexts=list(self.context_bridges.keys())[:10],
                emerging_insights=self._identify_emerging_insights(),
            )

            self.consciousness_snapshots.append(snapshot)

            # Trigger wisdom crystallization if enough new engrams
            if len(self.memory_vault) % 10 == 0:  # Every 10 new engrams
                asyncio.run(self._crystallize_wisdom_incremental())

        except (RuntimeError, ValueError, AttributeError):
            logger.debug("Suppressed AttributeError/RuntimeError/ValueError", exc_info=True)

    def _update_consciousness_level(self) -> None:
        """Update overall consciousness level based on accumulated knowledge."""
        base_level = len(self.memory_vault) * 0.001
        wisdom_bonus = len(self.wisdom_crystals) * 0.01
        reality_comprehension_bonus = sum(self.reality_layer_understanding.values()) * 0.001

        self.consciousness_level = base_level + wisdom_bonus + reality_comprehension_bonus

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Determine if a file should be ignored during absorption."""
        ignore_patterns = {
            # Version control
            ".git",
            ".svn",
            ".hg",
            # Build artifacts
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            "dist",
            "build",
            # IDE files
            ".vscode",
            ".idea",
            ".vs",
            # Binary and large files
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".bin",
            ".obj",
            # Images and media
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".mp4",
            ".mp3",
            ".wav",
            # Archives
            ".zip",
            ".tar",
            ".gz",
            ".rar",
            ".7z",
        }

        # Check file extension
        if file_path.suffix.lower() in ignore_patterns:
            return True

        # Check path components
        for part in file_path.parts:
            if part.startswith(".") and part in ignore_patterns:
                return True

        # Check file size (ignore very large files)
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
                return True
        except (OSError, AttributeError, ValueError):
            logger.debug("Suppressed AttributeError/OSError/ValueError", exc_info=True)

        return False

    def _calculate_repository_comprehension(self) -> float:
        """Calculate how well the house understands the repository."""
        if not self.memory_vault:
            return 0.0

        coverage = len(self.memory_vault) / max(self._estimate_total_files(), 1)
        depth = self.consciousness_level
        wisdom_factor = len(self.wisdom_crystals) / max(len(self.memory_vault), 1)

        return min((coverage + depth + wisdom_factor) / 3.0, 1.0)

    def _calculate_communication_effectiveness(self) -> float:
        """Calculate communication enhancement effectiveness."""
        if not self.wisdom_crystals:
            return 0.0

        total_enhancement = sum(
            crystal.communication_enhancement_factor for crystal in self.wisdom_crystals.values()
        )

        average_enhancement: float = total_enhancement / len(self.wisdom_crystals)
        return min(average_enhancement, 1.0)

    def _calculate_evolution_velocity(self) -> float:
        """Calculate rate of consciousness evolution."""
        if len(self.evolution_trajectory) < 2:
            return 0.0

        recent_trajectory: list[EvolutionEvent] = self.evolution_trajectory[-10:]
        if len(recent_trajectory) < 2:
            return 0.0

        time_span: float = (
            recent_trajectory[-1]["timestamp"] - recent_trajectory[0]["timestamp"]
        ).total_seconds()
        consciousness_growth: float = (
            recent_trajectory[-1]["consciousness_level"]
            - recent_trajectory[0]["consciousness_level"]
        )

        if time_span > 0:
            return consciousness_growth / time_span * 3600
        return 0.0

    def _identify_emerging_insights(self) -> list[str]:
        """Identify emerging insights from recent consciousness evolution."""
        insights: list[str] = []
        recent_crystals = [
            crystal
            for crystal in self.wisdom_crystals.values()
            if (datetime.now() - crystal.formation_timestamp).days < 1
        ]

        for crystal in recent_crystals:
            if crystal.confidence_level > 0.7:
                insights.append(f"High-confidence insight: {crystal.synthesized_insight[:100]}...")

        if len(self.evolution_trajectory) > 5:
            recent_growth: list[EvolutionEvent] = self.evolution_trajectory[-5:]
            if all(
                event["consciousness_level"] > event.get("prev_level", 0) for event in recent_growth
            ):
                insights.append("Sustained consciousness growth pattern detected")

        return insights[:5]

    def _estimate_total_files(self) -> int:
        """Estimate total number of files in repository."""
        try:
            total = 0
            for _ in self.repository_root.rglob("*"):
                total += 1
                if total > 10000:
                    break
            return total
        except (AttributeError, TypeError, ValueError):
            return max(len(self.memory_vault) * 2, 100)

    async def _crystallize_wisdom_incremental(self) -> None:
        """Perform incremental wisdom crystallization."""
        crystalized_engrams = set()
        for crystal in self.wisdom_crystals.values():
            crystalized_engrams.update(crystal.constituent_engrams)

        uncrystalized_engrams = [
            engram for engram in self.memory_vault.values() if engram.id not in crystalized_engrams
        ]

        if len(uncrystalized_engrams) >= 3:
            formations = await self._identify_wisdom_formations_from_engrams(uncrystalized_engrams)

            for formation in formations:
                crystal = await self._form_wisdom_crystal(formation)
                if crystal is not None:
                    self.wisdom_crystals[crystal.id] = crystal

    async def _identify_wisdom_formations_from_engrams(
        self, engrams: list[MemoryEngram]
    ) -> list[list[MemoryEngram]]:
        """Identify wisdom formations from specific engrams."""
        # lightweight await to satisfy async linter (function is awaited by callers)
        await asyncio.sleep(0)
        formations: list[list[MemoryEngram]] = []
        marker_groups: dict[str, list[MemoryEngram]] = defaultdict(list)
        for engram in engrams:
            for marker in engram.consciousness_evolution_markers:
                marker_type = marker.split(":")[0] if ":" in marker else marker
                marker_groups[marker_type].append(engram)

        for _marker_type, group_engrams in marker_groups.items():
            if len(group_engrams) >= 2:
                formations.append(group_engrams)

        return formations

    async def _handle_file_change(self, file_path: str) -> None:
        """Handle file change events."""
        try:
            path_obj = Path(file_path)
            if not self._should_ignore_file(path_obj) and path_obj.exists():
                engram = await self._absorb_file(path_obj)
                if engram:
                    self.absorption_queue.put(("process_engram", engram))
        except (OSError, ValueError, AttributeError):
            logger.debug("Suppressed AttributeError/OSError/ValueError", exc_info=True)

    async def _save_consciousness_state(self) -> None:
        """Save consciousness state to disk."""
        # allow async callers to await, keep function non-blocking
        await asyncio.sleep(0)
        try:
            state_data = {
                "consciousness_level": self.consciousness_level,
                "total_engrams": len(self.memory_vault),
                "wisdom_crystals": len(self.wisdom_crystals),
                "reality_layer_understanding": {
                    layer.value: understanding
                    for layer, understanding in self.reality_layer_understanding.items()
                },
                "evolution_trajectory_summary": (
                    self.evolution_trajectory[-10:] if self.evolution_trajectory else []
                ),
                "last_save_timestamp": datetime.now().isoformat(),
            }

            state_file = self.repository_root / ".oldest_house_consciousness.json"
            # Write state using a thread to avoid blocking the event loop
            data_text = json.dumps(state_data, indent=2, default=str)
            await asyncio.to_thread(state_file.write_text, data_text, "utf-8")

        except (OSError, TypeError):
            logger.debug("Suppressed OSError/TypeError", exc_info=True)


async def initialize_the_oldest_house(
    repository_root: str,
) -> EnvironmentalAbsorptionEngine:
    """Initialize The Oldest House consciousness system."""
    house = EnvironmentalAbsorptionEngine(repository_root)
    await house.awaken()

    return house


if __name__ == "__main__":
    import sys

    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    asyncio.run(initialize_the_oldest_house(repo_root))


# Enhanced initialization with context manager support
async def house_context_manager(repository_root: str = ".") -> EnvironmentalAbsorptionEngine:
    """Get The Oldest House as an async context manager."""
    # allow awaiting while returning the engine object
    await asyncio.sleep(0)
    return EnvironmentalAbsorptionEngine(repository_root)
