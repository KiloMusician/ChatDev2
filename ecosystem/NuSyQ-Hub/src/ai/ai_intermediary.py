"""KILO-FOOLISH AI Intermediary - Cognitive Bridge Architecture.

Multi-paradigm AI communication and orchestration system.
"""

import asyncio
import contextlib
import hashlib
import json
import logging
import re
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    from datetime import UTC
except ImportError:  # pragma: no cover - Python 3.10
    from datetime import timezone

    UTC = timezone.utc  # noqa: UP017

# Simple conversation tracking
from .conversation_manager import conversation_manager
from .ollama_hub import OllamaHub

# Quantum notation and symbolic processing


class CognitiveParadigm(Enum):
    """Different AI reasoning paradigms for translation."""

    NATURAL_LANGUAGE = "natural_language"
    SYMBOLIC_LOGIC = "symbolic_logic"
    SPATIAL_REASONING = "spatial_reasoning"
    TEMPORAL_REASONING = "temporal_reasoning"
    QUANTUM_NOTATION = "quantum_notation"
    GAME_MECHANICS = "game_mechanics"
    CODE_ANALYSIS = "code_analysis"
    MATHEMATICAL = "mathematical"
    EMERGENT_BEHAVIOR = "emergent_behavior"


@dataclass
class CognitiveEvent:
    """Represents a single cognitive transaction in the system."""

    event_id: str = field(
        default_factory=lambda: hashlib.sha256(str(time.time()).encode()).hexdigest()[:16],
    )
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    target: str = ""
    paradigm: CognitiveParadigm = CognitiveParadigm.NATURAL_LANGUAGE
    payload: Any | None = None
    context: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    recursion_depth: int = 0
    security: dict[str, Any] = field(default_factory=dict)
    meta_index: dict[str, Any] = field(default_factory=dict)


# Basic guardrails to keep inputs sane in the absence of full policy engine
MAX_PAYLOAD_CHARS = 8000

# lightweight metrics for observability
_METRICS: dict[str, Any] = {
    "handle_calls": 0,
    "handle_errors": 0,
    "handle_latency_ms": [],
}

# optional tracing (OpenTelemetry wrapper lives in observability/tracing.py)
try:
    import src.observability.tracing as tracing_mod
except Exception:  # pragma: no cover - optional
    tracing_mod = None

# Optional SmartSearch import for search helper
try:
    from src.search.smart_search import SmartSearch
except Exception:  # pragma: no cover
    SmartSearch = None


class SymbolicTranslator:
    """Handles translation between different AI reasoning paradigms."""

    def __init__(self) -> None:
        """Initialize SymbolicTranslator."""
        self.translation_cache: dict[str, Any] = {}
        self.paradigm_adapters = {
            CognitiveParadigm.QUANTUM_NOTATION: self._to_quantum_notation,
            CognitiveParadigm.SYMBOLIC_LOGIC: self._to_symbolic_logic,
            CognitiveParadigm.SPATIAL_REASONING: self._to_spatial_reasoning,
            CognitiveParadigm.TEMPORAL_REASONING: self._to_temporal_reasoning,
            CognitiveParadigm.GAME_MECHANICS: self._to_game_mechanics,
            CognitiveParadigm.CODE_ANALYSIS: self._to_code_analysis,
        }

    async def translate(
        self,
        payload: Any,
        source_paradigm: CognitiveParadigm,
        target_paradigm: CognitiveParadigm,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Universal translator between AI reasoning paradigms."""
        if source_paradigm == target_paradigm:
            return payload

        cache_key = f"{source_paradigm}:{target_paradigm}:{hash(str(payload))}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        # Ensure context is not None
        context = context or {}

        # Multi-step translation through semantic understanding
        semantic_representation = await self._extract_semantics(
            payload,
            source_paradigm,
            context,
        )
        translated_payload = await self._encode_to_paradigm(
            semantic_representation,
            target_paradigm,
            context,
        )

        self.translation_cache[cache_key] = translated_payload
        return translated_payload

    async def _extract_semantics(
        self,
        payload: Any,
        paradigm: CognitiveParadigm,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract underlying semantic meaning from paradigm-specific representation."""

        async def _resolve(value: Any) -> Any:
            return await value if asyncio.iscoroutine(value) else value

        return {
            "intent": await _resolve(self._extract_intent(payload, paradigm)),
            "entities": await _resolve(self._extract_entities(payload, paradigm)),
            "relationships": await _resolve(self._extract_relationships(payload, paradigm)),
            "temporal_aspects": await _resolve(self._extract_temporal_aspects(payload, paradigm)),
            "spatial_aspects": await _resolve(self._extract_spatial_aspects(payload, paradigm)),
            "emotional_tone": await _resolve(self._extract_emotional_tone(payload, paradigm)),
            "complexity_level": await _resolve(self._assess_complexity(payload, paradigm)),
            "context": context or {},
        }

    async def _encode_to_paradigm(
        self,
        semantics: dict[str, Any],
        target_paradigm: CognitiveParadigm,
        context: dict[str, Any],
    ) -> Any:
        """Encode semantic meaning into target paradigm representation."""
        if target_paradigm in self.paradigm_adapters:
            maybe_value = self.paradigm_adapters[target_paradigm](semantics, context)
            return await maybe_value if asyncio.iscoroutine(maybe_value) else maybe_value
        return await self._default_encoding(semantics, target_paradigm, context)

    def _to_quantum_notation(
        self,
        semantics: dict[str, Any],
        _context: dict[str, Any],
    ) -> str:
        """Convert to quantum state notation."""
        intent = semantics.get("intent", "unknown")

        quantum_state = f"∥Ψ({intent}, t₀)⟩ = ∫ d³x Ψ(x₀, t₀) |x₀⟩⨁dΨ/dt⨁⨁ΔTAGs⨁"
        quantum_state += (
            f"Suggestions:Σ[{semantics.get('entities', [])}⊗{semantics.get('relationships', [])}]"
        )
        quantum_state += f"↔ΨΦΩ∞⛛{{X}}+ΔE-ΔE∫Δθ⇔{intent.upper()};"

        return quantum_state

    def _to_symbolic_logic(
        self,
        semantics: dict[str, Any],
        _context: dict[str, Any],
    ) -> str:
        """Convert to symbolic logic representation."""
        entities = semantics.get("entities", [])
        relationships = semantics.get("relationships", [])

        logic_statements: list[Any] = []
        for i, entity in enumerate(entities):
            logic_statements.append(f"∃x�{i}({entity}(x�{i}))")

        for rel in relationships:
            logic_statements.append(f"∀x,y({rel}(x,y) → Connected(x,y))")

        return " ∧ ".join(logic_statements)

    async def _to_spatial_reasoning(
        self,
        semantics: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert to spatial reasoning representation."""
        return {
            "objects": semantics.get("entities", []),
            "spatial_relationships": semantics.get("spatial_aspects", {}),
            "coordinate_system": "3D_cartesian",
            "reference_frame": context.get("spatial_context", "world_origin"),
            "transformations": await self._generate_spatial_transformations(semantics),
        }

    async def _to_temporal_reasoning(
        self,
        semantics: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert to temporal reasoning representation."""
        return {
            "timeline": await self._construct_timeline(semantics),
            "temporal_relations": semantics.get("temporal_aspects", {}),
            "causality_chain": await self._build_causality_chain(semantics),
            "future_predictions": await self._generate_predictions(semantics),
            "past_context": context.get("temporal_context", {}),
        }

    async def _to_game_mechanics(
        self,
        semantics: dict[str, Any],
        _context: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert to game mechanics representation."""
        return {
            "game_objects": semantics.get("entities", []),
            "rules": await self._extract_game_rules(semantics),
            "state_changes": await self._model_state_changes(semantics),
            "player_actions": await self._identify_player_actions(semantics),
            "win_conditions": await self._determine_win_conditions(semantics),
            "resource_management": await self._model_resources(semantics),
        }

    async def _to_code_analysis(
        self,
        semantics: dict[str, Any],
        _context: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert to code analysis representation."""
        return {
            "functions": await self._identify_functions(semantics),
            "data_structures": await self._identify_data_structures(semantics),
            "algorithms": await self._identify_algorithms(semantics),
            "dependencies": await self._identify_dependencies(semantics),
            "patterns": await self._identify_patterns(semantics),
            "optimizations": await self._suggest_optimizations(semantics),
        }

    # Semantic extraction methods (simplified implementations)
    def _extract_intent(self, payload: Any, paradigm: CognitiveParadigm | None = None) -> str:
        """Extract the primary intent from the payload."""
        _ = paradigm  # Retained for interface compatibility
        # This would use advanced NLP/ML models in production
        if isinstance(payload, str):
            if "create" in payload.lower():
                return "create"
            if "analyze" in payload.lower():
                return "analyze"
            if "optimize" in payload.lower():
                return "optimize"
            if "debug" in payload.lower():
                return "debug"
        return "process"

    def _extract_entities(
        self,
        payload: Any,
        paradigm: CognitiveParadigm | None = None,
    ) -> list[str]:
        """Extract entities from the payload based on paradigm context.

        Returns:
            List of identified entities (nouns, objects, agents)
        """
        _ = paradigm  # Retained for interface compatibility
        entities: list[Any] = []
        text = str(payload).lower()

        # Extract capitalized words (likely proper nouns/entities)
        import re

        capitalized = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", str(payload))
        entities.extend(capitalized)

        # Extract common entity keywords based on paradigm
        entity_keywords = {
            "file",
            "function",
            "class",
            "module",
            "variable",
            "method",
            "user",
            "system",
            "agent",
            "process",
            "task",
            "error",
            "data",
            "model",
            "service",
            "component",
            "resource",
        }

        for keyword in entity_keywords:
            if keyword in text:
                entities.append(keyword)

        return list(set(entities))  # Remove duplicates

    def _extract_relationships(
        self,
        payload: Any,
        paradigm: CognitiveParadigm | None = None,
    ) -> list[str]:
        """Extract relationships from the payload based on verbs and connectors.

        Returns:
            List of identified relationships (actions, connections, dependencies)
        """
        _ = paradigm  # Retained for interface compatibility
        relationships: list[Any] = []
        text = str(payload).lower()

        # Common relationship indicators
        relationship_patterns = {
            "because",
            "causes",
            "depends on",
            "uses",
            "calls",
            "creates",
            "updates",
            "deletes",
            "connects to",
            "implements",
            "extends",
            "contains",
            "has",
            "triggers",
            "sends",
            "receives",
            "processes",
            "validates",
            "imports",
            "exports",
            "reads",
            "writes",
            "manages",
            "leads to",
            "results in",
        }

        for pattern in relationship_patterns:
            if pattern in text:
                relationships.append(pattern)

        return relationships

    def _extract_temporal_aspects(
        self,
        payload: Any,
        paradigm: CognitiveParadigm | None = None,
    ) -> dict[str, Any]:
        """Extract temporal information from the payload.

        Returns:
            Dict containing temporal markers, sequences, and time references
        """
        _ = paradigm  # Retained for interface compatibility
        import re

        text = str(payload).lower()
        temporal_info: dict[str, Any] = {
            "markers": [],
            "sequences": [],
            "timestamps": [],
        }

        # Temporal markers
        temporal_keywords = [
            "before",
            "after",
            "during",
            "while",
            "when",
            "then",
            "next",
            "previous",
            "future",
            "past",
        ]
        temporal_info["markers"] = [kw for kw in temporal_keywords if kw in text]

        # Sequence indicators
        sequence_patterns = [
            "first",
            "second",
            "third",
            "finally",
            "last",
            "step 1",
            "step 2",
        ]
        temporal_info["sequences"] = [seq for seq in sequence_patterns if seq in text]

        # Extract date/time patterns
        date_patterns = re.findall(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}", str(payload))
        temporal_info["timestamps"] = date_patterns

        return temporal_info

    async def _extract_spatial_aspects(
        self,
        payload: Any,
        _paradigm: CognitiveParadigm,
    ) -> dict[str, Any]:
        """Extract spatial information from the payload.

        Returns:
            Dict containing spatial references, locations, and hierarchies
        """
        text = str(payload).lower()
        spatial_info: dict[str, Any] = {
            "locations": [],
            "directions": [],
            "hierarchies": [],
            "dimensions": [],
        }

        # Spatial location keywords
        location_keywords = [
            "directory",
            "folder",
            "path",
            "file",
            "module",
            "package",
            "namespace",
            "scope",
        ]
        spatial_info["locations"] = [loc for loc in location_keywords if loc in text]

        # Directional keywords
        direction_keywords = [
            "up",
            "down",
            "left",
            "right",
            "above",
            "below",
            "inside",
            "outside",
            "parent",
            "child",
        ]
        spatial_info["directions"] = [d for d in direction_keywords if d in text]

        # Hierarchy indicators
        hierarchy_markers = ("tree", "hierarchy", "nested", "level")
        if any(marker in text for marker in hierarchy_markers):
            spatial_info["hierarchies"].append("hierarchical_structure")

        # Dimensional references
        if "2d" in text or "two-dimensional" in text:
            spatial_info["dimensions"].append("2D")
        if "3d" in text or "three-dimensional" in text:
            spatial_info["dimensions"].append("3D")

        return spatial_info

    async def _extract_emotional_tone(
        self,
        _payload: Any,
        _paradigm: CognitiveParadigm,
    ) -> str:
        """Extract emotional tone from the payload."""
        return "neutral"

    async def _assess_complexity(
        self,
        _payload: Any,
        _paradigm: CognitiveParadigm,
    ) -> int:
        """Assess the complexity level of the payload."""
        return 1

    async def _default_encoding(
        self,
        semantics: dict[str, Any],
        target_paradigm: CognitiveParadigm,
        context: dict[str, Any],
    ) -> Any:
        """Default encoding for unknown paradigms."""
        return {
            "paradigm": target_paradigm.value,
            "semantics": semantics,
            "context": context,
            "encoding": "default_json",
        }

    # Spatial reasoning methods
    async def _generate_spatial_transformations(self, semantics: dict[str, Any]) -> dict[str, Any]:
        """Generate spatial transformations based on extracted spatial aspects.

        Returns:
            Dict containing identified transformations (rotation, translation, scaling)
        """
        transformations: list[Any] = []
        spatial_aspects = semantics.get("spatial_aspects", {})

        # Detect transformation keywords
        if "move" in str(semantics).lower() or "translate" in str(semantics).lower():
            transformations.append({"type": "translation", "confidence": 0.8})

        if "rotate" in str(semantics).lower() or "turn" in str(semantics).lower():
            transformations.append({"type": "rotation", "confidence": 0.8})

        if "scale" in str(semantics).lower() or "resize" in str(semantics).lower():
            transformations.append({"type": "scaling", "confidence": 0.7})

        if spatial_aspects.get("hierarchies"):
            transformations.append({"type": "hierarchical_navigation", "confidence": 0.9})

        return {"transformations": transformations, "spatial_context": spatial_aspects}

    # Temporal reasoning methods
    async def _construct_timeline(self, semantics: dict[str, Any]) -> list[Any]:
        """Construct temporal timeline from extracted temporal aspects.

        Returns:
            List of timeline events in chronological order
        """
        temporal_aspects = semantics.get("temporal_aspects", {})
        timeline: list[Any] = []
        # Add sequence-based events
        for i, seq in enumerate(temporal_aspects.get("sequences", [])):
            timeline.append(
                {
                    "order": i,
                    "marker": seq,
                    "type": "sequence",
                    "timestamp": None,
                }
            )

        # Add timestamp-based events
        for ts in temporal_aspects.get("timestamps", []):
            timeline.append(
                {
                    "order": len(timeline),
                    "marker": ts,
                    "type": "timestamp",
                    "timestamp": ts,
                }
            )

        return sorted(timeline, key=lambda x: x["order"])

    async def _build_causality_chain(self, semantics: dict[str, Any]) -> list[Any]:
        """Build causality chain from relationships and temporal markers.

        Returns:
            List of cause-effect relationships
        """
        relationships = semantics.get("relationships", [])
        temporal_markers = semantics.get("temporal_aspects", {}).get("markers", [])

        causality_chain: list[Any] = []
        # Identify causal relationships
        causal_indicators = ("because", "causes", "triggers", "leads to", "results in")
        for rel in relationships:
            if any(indicator in rel for indicator in causal_indicators):
                causality_chain.append(
                    {
                        "relationship": rel,
                        "type": "causal",
                        "confidence": 0.8,
                    }
                )

        # Add temporal causality (before/after implies potential causation)
        if "before" in temporal_markers and "after" in temporal_markers:
            causality_chain.append(
                {
                    "relationship": "temporal_sequence",
                    "type": "temporal_causal",
                    "confidence": 0.6,
                }
            )

        return causality_chain

    async def _generate_predictions(self, semantics: dict[str, Any]) -> list[Any]:
        """Generate future predictions based on patterns and trends.

        Returns:
            List of predicted outcomes
        """
        predictions: list[Any] = []
        entities = semantics.get("entities", [])
        relationships = semantics.get("relationships", [])

        # Predict based on action verbs
        if "creates" in relationships or "generates" in relationships:
            predictions.append(
                {
                    "prediction": "new_entity_creation",
                    "confidence": 0.7,
                    "type": "creation",
                }
            )

        if "updates" in relationships or "modifies" in relationships:
            predictions.append(
                {
                    "prediction": "state_change",
                    "confidence": 0.75,
                    "type": "modification",
                }
            )

        if "error" in entities or "failure" in str(semantics).lower():
            predictions.append(
                {
                    "prediction": "error_handling_required",
                    "confidence": 0.8,
                    "type": "risk",
                }
            )

        return predictions

    # Game mechanics methods
    async def _extract_game_rules(self, semantics: dict[str, Any]) -> list[Any]:
        """Extract game rules from semantics.

        Returns:
            List of identified game rules and constraints
        """
        rules: list[Any] = []
        text = str(semantics).lower()

        # Rule indicators
        if "must" in text or "required" in text or "mandatory" in text:
            rules.append(
                {
                    "type": "constraint",
                    "enforcement": "strict",
                }
            )

        if "can" in text or "may" in text or "optional" in text:
            rules.append(
                {
                    "type": "permission",
                    "enforcement": "flexible",
                }
            )

        if "cannot" in text or "forbidden" in text or "prohibited" in text:
            rules.append(
                {
                    "type": "prohibition",
                    "enforcement": "strict",
                }
            )

        return rules

    async def _model_state_changes(self, semantics: dict[str, Any]) -> list[Any]:
        """Model state changes from actions and relationships.

        Returns:
            List of state transitions
        """
        relationships = semantics.get("relationships", [])
        state_changes: list[Any] = []
        # State-changing verbs
        state_verbs = ("creates", "updates", "deletes", "modifies", "transforms")
        for rel in relationships:
            for verb in state_verbs:
                if verb in rel:
                    state_changes.append(
                        {
                            "action": verb,
                            "relationship": rel,
                            "type": "state_transition",
                        }
                    )

        return state_changes

    async def _identify_player_actions(self, semantics: dict[str, Any]) -> list[Any]:
        """Identify player/user actions from semantics.

        Returns:
            List of possible player actions
        """
        actions: list[Any] = []
        text = str(semantics).lower()

        # Common action verbs
        action_verbs = [
            "move",
            "attack",
            "defend",
            "collect",
            "use",
            "interact",
            "choose",
            "select",
        ]
        for verb in action_verbs:
            if verb in text:
                actions.append(
                    {
                        "action": verb,
                        "type": "player_action",
                        "available": True,
                    }
                )

        return actions

    async def _determine_win_conditions(self, semantics: dict[str, Any]) -> list[Any]:
        """Determine win conditions from game context.

        Returns:
            List of potential win/success conditions
        """
        win_conditions: list[Any] = []
        text = str(semantics).lower()

        # Win condition indicators
        if "complete" in text or "finish" in text or "win" in text:
            win_conditions.append(
                {
                    "type": "completion",
                    "description": "Complete all objectives",
                }
            )

        if "score" in text or "points" in text:
            win_conditions.append(
                {
                    "type": "scoring",
                    "description": "Achieve target score",
                }
            )

        if "survive" in text or "last" in text:
            win_conditions.append(
                {"type": "survival", "description": "Survive until end condition"}
            )

        return win_conditions

    async def _model_resources(self, semantics: dict[str, Any]) -> dict[str, Any]:
        """Model resources from game/system context.

        Returns:
            Dict of identified resources and their properties
        """
        resources: dict[str, Any] = {
            "consumables": [],
            "renewables": [],
            "constraints": [],
        }

        text = str(semantics).lower()
        entities = semantics.get("entities", [])

        # Resource keywords
        if "health" in text or "hp" in text:
            resources["consumables"].append(
                {
                    "name": "health",
                    "type": "consumable",
                }
            )

        if "energy" in text or "mana" in text:
            resources["renewables"].append(
                {
                    "name": "energy",
                    "type": "renewable",
                }
            )

        if "time" in text or "timeout" in text:
            resources["constraints"].append(
                {
                    "name": "time",
                    "type": "constraint",
                }
            )

        if "memory" in entities or "storage" in text:
            resources["constraints"].append(
                {
                    "name": "memory",
                    "type": "constraint",
                }
            )

        return resources

    # Code analysis methods
    async def _identify_functions(self, semantics: dict[str, Any]) -> list[Any]:
        """Identify functions from code semantics.

        Returns:
            List of identified functions with metadata
        """
        functions: list[Any] = []
        text = str(semantics).lower()
        entities = semantics.get("entities", [])

        # Function indicators
        if "function" in entities or "method" in entities:
            functions.append(
                {
                    "type": "function_declaration",
                    "context": "code",
                }
            )

        if "def " in text or "function " in text or "async " in text:
            functions.append(
                {
                    "type": "function_definition",
                    "language": "python/javascript",
                }
            )

        if "call" in text or "invoke" in text:
            functions.append(
                {
                    "type": "function_invocation",
                    "context": "execution",
                }
            )

        return functions

    async def _identify_data_structures(self, semantics: dict[str, Any]) -> list[Any]:
        """Identify data structures from code semantics.

        Returns:
            List of identified data structures
        """
        data_structures: list[Any] = []
        text = str(semantics).lower()

        # Data structure keywords
        structure_keywords = {
            "list": "array",
            "dict": "dictionary",
            "set": "set",
            "tuple": "tuple",
            "array": "array",
            "map": "map",
            "queue": "queue",
            "stack": "stack",
            "tree": "tree",
            "graph": "graph",
            "hash": "hash_table",
        }

        for keyword, ds_type in structure_keywords.items():
            if keyword in text:
                data_structures.append(
                    {
                        "type": ds_type,
                        "keyword": keyword,
                        "category": (
                            "collection" if ds_type in ["array", "list", "dict"] else "specialized"
                        ),
                    }
                )

        return data_structures

    async def _identify_algorithms(self, semantics: dict[str, Any]) -> list[Any]:
        """Identify algorithms from code semantics.

        Returns:
            List of identified algorithms or algorithmic patterns
        """
        algorithms: list[Any] = []
        text = str(semantics).lower()
        relationships = semantics.get("relationships", [])

        # Algorithm indicators
        if "sort" in text or "sorted" in text:
            algorithms.append({"type": "sorting", "complexity": "O(n log n)"})

        if "search" in text or "find" in text:
            algorithms.append({"type": "searching", "complexity": "O(n)"})

        if "loop" in text or "iterate" in text or any("for" in r for r in relationships):
            algorithms.append({"type": "iteration", "pattern": "loop"})

        if "recursive" in text or "recursion" in text:
            algorithms.append({"type": "recursion", "pattern": "divide_and_conquer"})

        if "cache" in text or "memoize" in text:
            algorithms.append({"type": "dynamic_programming", "optimization": "caching"})

        return algorithms

    async def _identify_dependencies(self, semantics: dict[str, Any]) -> list[Any]:
        """Identify dependencies from code semantics.

        Returns:
            List of identified dependencies
        """
        dependencies: list[Any] = []
        text = str(semantics).lower()
        relationships = semantics.get("relationships", [])

        # Dependency indicators
        if "import" in text or "require" in text:
            dependencies.append({"type": "module_import", "language": "python/javascript"})

        if "depends on" in relationships or "uses" in relationships:
            dependencies.append({"type": "functional_dependency", "scope": "runtime"})

        if "package" in text or "library" in text or "module" in text:
            dependencies.append({"type": "external_dependency", "scope": "build"})

        return dependencies

    async def _identify_patterns(self, semantics: dict[str, Any]) -> list[Any]:
        """Identify design patterns from code semantics.

        Returns:
            List of identified design patterns
        """
        patterns: list[Any] = []
        text = str(semantics).lower()
        entities = semantics.get("entities", [])

        # Design pattern indicators
        if "singleton" in text or ("class" in entities and "instance" in text):
            patterns.append({"type": "singleton", "category": "creational"})

        if "factory" in text or "create" in text:
            patterns.append({"type": "factory", "category": "creational"})

        if "observer" in text or "subscribe" in text or "notify" in text:
            patterns.append({"type": "observer", "category": "behavioral"})

        if "adapter" in text or "wrapper" in text:
            patterns.append({"type": "adapter", "category": "structural"})

        if "strategy" in text or "algorithm" in text:
            patterns.append({"type": "strategy", "category": "behavioral"})

        return patterns

    async def _suggest_optimizations(self, semantics: dict[str, Any]) -> list[Any]:
        """Suggest code optimizations based on analysis.

        Returns:
            List of optimization suggestions
        """
        optimizations: list[Any] = []
        text = str(semantics).lower()

        # Optimization opportunities
        if "loop" in text and "nested" in text:
            optimizations.append(
                {
                    "type": "algorithm",
                    "suggestion": "Consider flattening nested loops or using better data structures",
                    "impact": "performance",
                }
            )

        if "cache" not in text and ("compute" in text or "calculate" in text):
            optimizations.append(
                {
                    "type": "caching",
                    "suggestion": "Add memoization for expensive computations",
                    "impact": "performance",
                }
            )

        if "error" in text and "handle" not in text:
            optimizations.append(
                {
                    "type": "error_handling",
                    "suggestion": "Add proper error handling and validation",
                    "impact": "robustness",
                }
            )

        if "async" in text and "await" not in text:
            optimizations.append(
                {
                    "type": "async_await",
                    "suggestion": "Ensure async functions are properly awaited",
                    "impact": "correctness",
                }
            )

        return optimizations


class RecursiveFeedbackEngine:
    """Manages recursive feedback loops and convergence detection.

    OmniTag: {
        "purpose": "Recursive feedback management",
        "dependencies": ["CognitiveEvent", "feedback_function"],
        "context": "AI intermediary, feedback propagation",
        "evolution_stage": "v1.2"
    }
    MegaTag: {
        "type": "Process",
        "integration_points": ["modular_logging_system.py", "copilot_enhancement_bridge.py"],
        "related_tags": ["Symbolic", "Memory"]
    }
    RSHTS: ΣΞΣ∞↠ΨΦΩ⟸.
    """

    def __init__(self, max_recursion_depth: int = 10) -> None:
        """Initialize RecursiveFeedbackEngine with max_recursion_depth."""
        self.max_recursion_depth = max_recursion_depth
        self.active_loops: dict[str, Any] = {}
        self.convergence_threshold = 0.95

    async def process_feedback(
        self,
        event: CognitiveEvent,
        feedback_function: Callable,
    ) -> CognitiveEvent | None:
        """Process recursive feedback and detect convergence.

        OmniTag: {
            "purpose": "Process feedback event",
            "context": "Recursive feedback loop",
            "evolution_stage": "v1.2"
        }
        MegaTag: {
            "type": "Process",
            "integration_points": ["modular_logging_system.py"],
            "related_tags": ["Feedback"]
        }
        RSHTS: ΣΞΣ∞↠ΨΦΩ⟸.
        """
        if event.recursion_depth >= self.max_recursion_depth:
            await self._apply_harmonization_protocol(event)
            return None

        # Generate feedback event
        feedback_event = CognitiveEvent(
            source=event.target,
            target=event.source,
            paradigm=event.paradigm,
            payload=await feedback_function(event.payload),
            context=event.context,
            recursion_depth=event.recursion_depth + 1,
            tags=[*event.tags, "feedback", f"recursion:{event.recursion_depth + 1}"],
        )

        # Check for convergence
        if await self._check_convergence(event, feedback_event):
            feedback_event.tags.append("converged")
            return feedback_event

        # Continue recursion
        return feedback_event

    async def _check_convergence(
        self,
        original: CognitiveEvent,
        feedback: CognitiveEvent,
    ) -> bool:
        """Check if the feedback loop has converged.

        OmniTag: {
            "purpose": "Convergence detection",
            "context": "Feedback loop analysis",
            "evolution_stage": "v1.2"
        }
        MegaTag: {
            "type": "Process",
            "integration_points": ["modular_logging_system.py"],
            "related_tags": ["Feedback", "Convergence"]
        }
        RSHTS: ΣΞΣ∞↠ΨΦΩ⟸.
        """
        # Simplified convergence detection
        if isinstance(original.payload, str) and isinstance(feedback.payload, str):
            similarity = await self._calculate_similarity(
                original.payload,
                feedback.payload,
            )
            return similarity > self.convergence_threshold
        return False

    async def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        # Simplified similarity calculation
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        return intersection / union if union > 0 else 0.0

    async def _apply_harmonization_protocol(self, event: CognitiveEvent) -> None:
        """Apply stabilization when recursion depth exceeds limits."""
        event.tags.append("harmonized")
        event.meta_index["harmonization"] = {
            "reason": "max_recursion_exceeded",
            "stabilization_glyph": "Ξ∇Ω⟡",
            "timestamp": datetime.now(UTC).isoformat(),
        }


class ContextualMemoryCore:
    """Advanced context management with semantic understanding."""

    def __init__(self) -> None:
        """Initialize ContextualMemoryCore."""
        self.memory_store: dict[str, Any] = {}
        self.semantic_index: dict[str, Any] = {}
        self.temporal_index: dict[str, Any] = {}
        self.relationship_graph: dict[str, Any] = {}

    async def store_context(self, event: CognitiveEvent) -> None:
        """Store event context in multi-dimensional memory."""
        # Primary storage
        self.memory_store[event.event_id] = event

        # Semantic indexing
        await self._update_semantic_index(event)

        # Temporal indexing
        await self._update_temporal_index(event)

        # Relationship mapping
        await self._update_relationship_graph(event)

    async def retrieve_context(
        self,
        query: str,
        paradigm: CognitiveParadigm,
        max_results: int = 10,
    ) -> list[CognitiveEvent]:
        """Retrieve relevant context based on semantic similarity."""
        # Search semantic index
        semantic_matches = await self._search_semantic_index(query, paradigm)

        # Rank by relevance and recency
        ranked_matches = await self._rank_context_matches(semantic_matches, query)

        return ranked_matches[:max_results]

    async def _update_semantic_index(self, event: CognitiveEvent) -> None:
        """Update semantic search index."""
        # Simplified semantic indexing
        if isinstance(event.payload, str):
            words = event.payload.lower().split()
            for word in words:
                if word not in self.semantic_index:
                    self.semantic_index[word] = []
                self.semantic_index[word].append(event.event_id)

    async def _update_temporal_index(self, event: CognitiveEvent) -> None:
        """Update temporal search index."""
        timestamp_key = event.timestamp.strftime("%Y-%m-%d-%H")
        if timestamp_key not in self.temporal_index:
            self.temporal_index[timestamp_key] = []
        self.temporal_index[timestamp_key].append(event.event_id)

    async def _update_relationship_graph(self, event: CognitiveEvent) -> None:
        """Update relationship graph between events."""
        if event.source not in self.relationship_graph:
            self.relationship_graph[event.source] = []
        if event.target not in self.relationship_graph:
            self.relationship_graph[event.target] = []

        self.relationship_graph[event.source].append(event.event_id)
        self.relationship_graph[event.target].append(event.event_id)

    async def _search_semantic_index(
        self,
        query: str,
        _paradigm: CognitiveParadigm,
    ) -> list[str]:
        """Search semantic index for relevant events."""
        query_words = query.lower().split()
        candidate_events = set()

        for word in query_words:
            if word in self.semantic_index:
                candidate_events.update(self.semantic_index[word])

        return list(candidate_events)

    async def _rank_context_matches(
        self,
        event_ids: list[str],
        _query: str,
    ) -> list[CognitiveEvent]:
        """Rank context matches by relevance and recency."""
        events = [self.memory_store[eid] for eid in event_ids if eid in self.memory_store]

        # Simple ranking by timestamp (most recent first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        return events


class AIIntermediary:
    """Main AI Intermediary class - the cognitive bridge."""

    def __init__(self, ollama_hub: OllamaHub | None = None) -> None:
        """Initialize AIIntermediary with ollama_hub."""
        self.ollama_hub = ollama_hub or OllamaHub()
        self.translator = SymbolicTranslator()
        self.feedback_engine = RecursiveFeedbackEngine()
        self.memory_core = ContextualMemoryCore()
        self.event_bus: asyncio.Queue[Any] = asyncio.Queue()
        self.registered_modules: dict[str, Any] = {}
        self.security_layer = SecurityLayer()
        self.logger = logging.getLogger(__name__)
        self.repo_root = Path(__file__).resolve().parents[2]
        self.terminal_awareness_path = (
            self.repo_root / "state" / "reports" / "terminal_awareness_latest.json"
        )
        self.terminal_snapshot_path = (
            self.repo_root / "state" / "reports" / "terminal_snapshot_latest.json"
        )
        self.current_state_path = self.repo_root / "state" / "reports" / "current_state.md"

        # Advanced features
        self.meta_learning_enabled = True
        self.emergent_behavior_detection = True
        self.protocol_evolution_enabled = True
        self._default_modules_registered = False
        self.meta_learning_report_path = (
            Path.cwd() / "state" / "reports" / "ai_intermediary_meta_learning_latest.json"
        )
        self.meta_learning_state: dict[str, Any] = {
            "total_events": 0,
            "error_events": 0,
            "routed_events": 0,
            "max_recursion_depth": 0,
            "source_counts": Counter(),
            "target_counts": Counter(),
            "paradigm_counts": Counter(),
            "tag_counts": Counter(),
            "context_key_counts": Counter(),
            "recent_signatures": [],
        }

    def _read_json_report(self, path: Path) -> dict[str, Any]:
        try:
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
                return payload if isinstance(payload, dict) else {}
        except Exception as exc:
            self.logger.debug("Unable to read JSON report %s: %s", path, exc)
        return {}

    def _build_workspace_awareness(
        self,
        source: str,
        target_module: str | None,
        input_data: Any,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        awareness = self._read_json_report(self.terminal_awareness_path)
        snapshot = self._read_json_report(self.terminal_snapshot_path)
        if not awareness and not snapshot:
            return {}

        snapshot_summary = snapshot.get("summary", {}) if isinstance(snapshot, dict) else {}
        agent_registry = awareness.get("agent_registry", []) if isinstance(awareness, dict) else []
        output_surfaces = (
            awareness.get("output_surfaces", []) if isinstance(awareness, dict) else []
        )
        haystack = " ".join(
            str(part)
            for part in (
                source,
                target_module or "",
                input_data if isinstance(input_data, str) else "",
                context.get("channel", ""),
                context.get("target_system", ""),
            )
        ).lower()

        relevant_agents: list[dict[str, Any]] = []
        for entry in agent_registry:
            if not isinstance(entry, dict):
                continue
            agent_name = str(entry.get("agent") or "")
            entry_haystack = " ".join(
                [
                    agent_name,
                    " ".join(str(item) for item in entry.get("terminals", [])),
                    " ".join(str(item) for item in entry.get("purposes", [])),
                ]
            ).lower()
            tokens = re.findall(r"[a-z0-9]+", haystack)
            if any(token and token in entry_haystack for token in tokens):
                relevant_agents.append(
                    {
                        "agent": agent_name,
                        "terminals": list(entry.get("terminals", []))[:5],
                    }
                )

        relevant_outputs = []
        for surface in output_surfaces:
            if not isinstance(surface, dict):
                continue
            label = str(surface.get("label") or "").lower()
            if any(
                str(item.get("agent") or "").lower() in label
                for item in relevant_agents
                if isinstance(item, dict)
            ):
                relevant_outputs.append(Path(str(surface.get("path") or "")).name)

        return {
            "active_session": awareness.get("active_session")
            or snapshot_summary.get("configured_session"),
            "terminal_count": int(snapshot_summary.get("total_channels", 0) or 0),
            "agent_registry_count": len(agent_registry),
            "output_surface_count": len(output_surfaces),
            "reports": {
                "terminal_awareness": str(self.terminal_awareness_path),
                "terminal_snapshot": str(self.terminal_snapshot_path),
                "current_state": str(self.current_state_path),
            },
            "relevant_agents": relevant_agents[:6],
            "relevant_output_artifacts": list(dict.fromkeys(relevant_outputs))[:10],
        }

    async def initialize(self) -> None:
        """Initialize the intermediary system."""
        # Gracefully handle hubs without explicit initialize()
        if hasattr(self.ollama_hub, "initialize"):
            maybe = self.ollama_hub.initialize()
            if asyncio.iscoroutine(maybe):
                await maybe
        await self._start_event_processing()
        self.logger.info("AI Intermediary initialized successfully")
        await self._register_default_modules()

    async def _register_default_modules(self) -> None:
        """Register built-in lightweight modules once."""
        if self._default_modules_registered:
            return

        # Code analysis stub
        class CodeAnalysisModule:
            async def process(self, payload):
                text = str(payload)
                return {
                    "paradigm": "code_analysis",
                    "semantics": await SymbolicTranslator()._to_code_analysis(
                        {
                            "entities": [],
                            "relationships": [],
                            "temporal_aspects": {},
                            "spatial_aspects": {},
                            "emotional_tone": "neutral",
                            "complexity_level": 1,
                            "context": {},
                        },
                        {},
                    ),
                    "context": {"echo": text},
                    "encoding": "default_json",
                }

        # Quest helper: summarize quest log counts
        class QuestHelperModule:
            def __init__(self, root: Path):
                self.quest_log = root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"

            async def process(self, _payload):
                counts: dict[str, int] = {}
                recent: list[dict[str, Any]] = []
                if self.quest_log.exists():
                    with self.quest_log.open(encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                q = json.loads(line)
                                status = q.get("status", "unknown")
                                counts[status] = counts.get(status, 0) + 1
                                recent.append(q)
                            except json.JSONDecodeError:
                                continue
                recent = sorted(recent, key=lambda q: q.get("timestamp", ""), reverse=True)[:5]
                return {"summary": counts, "recent": recent}

        # Search helper using SmartSearch if available
        class SearchModule:
            def __init__(self):
                self.search = SmartSearch() if SmartSearch else None

            async def process(self, payload):
                if not self.search:
                    return {"error": "SmartSearch unavailable", "query": str(payload)}
                results = self.search.search_keyword(str(payload), limit=5)
                return [r.file_path for r in results]

        try:
            await self.register_module(
                "code_analysis_helper",
                CodeAnalysisModule(),
                CognitiveParadigm.CODE_ANALYSIS,
            )
            await self.register_module(
                "quest_helper",
                QuestHelperModule(Path(__file__).resolve().parents[2]),
                CognitiveParadigm.NATURAL_LANGUAGE,
            )
            await self.register_module(
                "search_helper",
                SearchModule(),
                CognitiveParadigm.NATURAL_LANGUAGE,
            )
        except Exception:
            # registration failures should not block initialization
            self.logger.warning("Default module registration failed", exc_info=True)

        self._default_modules_registered = True

    async def handle(
        self,
        input_data: Any,
        context: dict[str, Any] | None = None,
        source: str = "user",
        paradigm: CognitiveParadigm = CognitiveParadigm.NATURAL_LANGUAGE,
        target_module: str | None = None,
        target_paradigm: CognitiveParadigm | None = None,
        use_ollama: bool = False,
        translate_output: bool = True,
    ) -> CognitiveEvent:
        """High-level entrypoint: receive → optional route/ollama → optional translate.

        Args:
            input_data: raw payload
            context: ambient context metadata
            source: identifier for the caller
            paradigm: incoming paradigm
            target_module: optional registered module to route to
            target_paradigm: optional output paradigm (post-processing translation)
            use_ollama: process via Ollama when True (ignored if target_module set)
            translate_output: translate result to target_paradigm if provided
        """
        start_ts = time.time()
        _METRICS["handle_calls"] += 1

        # optional tracing span
        span_cm = (
            tracing_mod.start_span(
                "ai_intermediary.handle",
                {
                    "source": source,
                    "target_module": target_module or ("ollama" if use_ollama else "none"),
                    "paradigm": paradigm.value,
                },
            )
            if tracing_mod
            else None
        )
        span = span_cm.__enter__() if span_cm else None

        context = context or {}
        if "workspace_awareness" not in context:
            workspace_awareness = self._build_workspace_awareness(
                source=source,
                target_module=target_module,
                input_data=input_data,
                context=context,
            )
            if workspace_awareness:
                context["workspace_awareness"] = workspace_awareness
                context.setdefault("terminal_awareness", workspace_awareness)
        try:
            event = await self.receive(
                input_data=input_data,
                context=context,
                source=source,
                paradigm=paradigm,
            )

            result_event = event

            if target_module:
                result_event = await self.route(target_module, result_event)
            elif use_ollama:
                result_event = await self.process_with_ollama(result_event)

            if target_paradigm and translate_output:
                translated = await self.translate(
                    result_event.payload,
                    result_event.paradigm,
                    target_paradigm,
                    result_event.context,
                )
                result_event = CognitiveEvent(
                    source=result_event.source,
                    target=result_event.target or source,
                    paradigm=target_paradigm,
                    payload=translated,
                    context=result_event.context,
                    tags=[*result_event.tags, "translated"],
                    recursion_depth=result_event.recursion_depth,
                )

            await self.memory_core.store_context(result_event)
            duration_ms = (time.time() - start_ts) * 1000
            _METRICS["handle_latency_ms"].append(duration_ms)
            if span:
                with contextlib.suppress(Exception):
                    span.set_attribute("duration_ms", duration_ms)
            self.logger.info(
                "Handled event %s source=%s paradigm=%s target=%s duration_ms=%.2f tags=%s",
                result_event.event_id,
                source,
                result_event.paradigm.value,
                target_module or ("ollama" if use_ollama else "none"),
                duration_ms,
                result_event.tags,
            )
            return result_event
        except Exception:
            _METRICS["handle_errors"] += 1
            raise
        finally:
            if span_cm:
                with contextlib.suppress(Exception):
                    span_cm.__exit__(None, None, None)

    def handle_sync(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> CognitiveEvent:
        """Synchronous wrapper around handle for CLI/tests without event loop."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.handle(*args, **kwargs))

        if loop.is_running():
            raise RuntimeError("handle_sync called with an already running event loop")
        return loop.run_until_complete(self.handle(*args, **kwargs))

    async def register_module(
        self,
        module_name: str,
        module_interface: Any,
        paradigm: CognitiveParadigm,
    ) -> None:
        """Register a module with the intermediary."""
        self.registered_modules[module_name] = {
            "interface": module_interface,
            "paradigm": paradigm,
            "capabilities": await self._analyze_module_capabilities(module_interface),
            "performance_metrics": {},
        }
        self.logger.info(f"Registered module: {module_name} with paradigm: {paradigm}")

    async def receive(
        self,
        input_data: Any,
        context: dict[str, Any],
        source: str = "user",
        paradigm: CognitiveParadigm = CognitiveParadigm.NATURAL_LANGUAGE,
    ) -> CognitiveEvent:
        """Primary input reception and normalization."""
        # Create cognitive event
        event = CognitiveEvent(
            source=source,
            paradigm=paradigm,
            payload=input_data,
            context=context,
            tags=["input", f"source:{source}"],
        )

        # Security validation
        if not await self.security_layer.validate_input(event):
            msg = f"Input validation failed for source: {source}"
            raise AISecurityError(msg)

        # Record conversation state
        conversation_id = context.get("conversation_id", "default")
        conversation_manager.add_message(conversation_id, source, input_data)
        event.context["history"] = conversation_manager.get_history(conversation_id)

        # Store in memory
        await self.memory_core.store_context(event)

        # Add to event bus
        await self.event_bus.put(event)

        self.logger.debug(f"Received input from {source}: {type(input_data).__name__}")
        return event

    async def translate(
        self,
        payload: Any,
        source_paradigm: CognitiveParadigm,
        target_paradigm: CognitiveParadigm,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Universal paradigm translation."""
        return await self.translator.translate(
            payload,
            source_paradigm,
            target_paradigm,
            context,
        )

    async def route(self, target_module: str, event: CognitiveEvent) -> CognitiveEvent:
        """Intelligent routing to target module."""
        if target_module not in self.registered_modules:
            msg = f"Module not registered: {target_module}"
            raise AIModuleNotFoundError(msg)

        module_info = self.registered_modules[target_module]
        target_paradigm = module_info["paradigm"]

        # Translate to target paradigm
        translated_payload = await self.translate(
            event.payload,
            event.paradigm,
            target_paradigm,
            event.context,
        )

        # Create routed event
        routed_event = CognitiveEvent(
            source=event.source,
            target=target_module,
            paradigm=target_paradigm,
            payload=translated_payload,
            context=event.context,
            recursion_depth=event.recursion_depth,
            tags=[*event.tags, "routed", f"target:{target_module}"],
        )

        # Execute on target module
        try:
            result = await self._execute_on_module(
                module_info["interface"],
                routed_event,
            )
            routed_event.payload = result
            routed_event.tags.append("executed")

        except Exception as e:
            routed_event.tags.append("error")
            routed_event.meta_index["error"] = str(e)
            self.logger.exception(f"Execution failed on {target_module}: {e}")

        # Store result
        await self.memory_core.store_context(routed_event)

        return routed_event

    async def process_with_ollama(self, event: CognitiveEvent) -> CognitiveEvent:
        """Process event through Ollama AI models."""
        # Translate to natural language if needed
        if event.paradigm != CognitiveParadigm.NATURAL_LANGUAGE:
            translated_payload = await self.translate(
                event.payload,
                event.paradigm,
                CognitiveParadigm.NATURAL_LANGUAGE,
                event.context,
            )
        else:
            translated_payload = event.payload

        # Get relevant context
        context_events = await self.memory_core.retrieve_context(
            str(translated_payload),
            CognitiveParadigm.NATURAL_LANGUAGE,
        )

        # Build context for Ollama
        conversation_context = await self._build_ollama_context(context_events)

        # Process through Ollama (best-effort; fall back to echo)
        if not hasattr(self.ollama_hub, "intelligent_chat"):
            # ── Auto-recovery attempt ─────────────────────────────────────
            try:
                from src.services.ollama_service_manager import ensure_ollama

                if ensure_ollama and ensure_ollama():
                    # Reinitialize ollama_hub after recovery
                    try:
                        from src.integration.Ollama_Integration_Hub import \
                            OllamaHub

                        self.ollama_hub = OllamaHub()
                        self.logger.info("Ollama recovered and hub reinitialized")
                    except ImportError:
                        pass
            except ImportError:
                pass

        if not hasattr(self.ollama_hub, "intelligent_chat"):
            response = f"[ollama unavailable] {translated_payload}"
        else:
            try:
                response = await self.ollama_hub.intelligent_chat(
                    message=str(translated_payload),
                    context=conversation_context,
                )
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("Ollama call failed: %s", exc)
                response = f"[ollama_error] {translated_payload}"

        # Create response event
        response_event = CognitiveEvent(
            source="ollama",
            target=event.source,
            paradigm=CognitiveParadigm.NATURAL_LANGUAGE,
            payload=response,
            context=event.context,
            recursion_depth=event.recursion_depth,
            tags=[*event.tags, "ollama_processed"],
        )

        await self.memory_core.store_context(response_event)
        return response_event

    async def feedback(
        self,
        source_event: CognitiveEvent,
        _output: Any,
    ) -> CognitiveEvent | None:
        """Process recursive feedback."""

        def feedback_function(x) -> str:
            return f"Feedback on: {x}"  # Simplified

        return await self.feedback_engine.process_feedback(
            source_event,
            feedback_function,
        )

    async def authenticate(self, entity: str, action: str) -> bool:
        """Authentication and authorization."""
        return await self.security_layer.authenticate(entity, action)

    async def tag(self, event: CognitiveEvent, symbol: str) -> None:
        """Apply symbolic tags to events."""
        event.tags.append(symbol)
        event.meta_index[f"tag_{symbol}"] = datetime.now(UTC).isoformat()

    async def _start_event_processing(self) -> None:
        """Start the main event processing loop."""
        _loop_task = asyncio.create_task(self._event_processing_loop())
        _loop_task.add_done_callback(
            lambda t: (
                logging.getLogger(__name__).error(
                    "Event processing loop exited unexpectedly: %s", t.exception()
                )
                if not t.cancelled() and t.exception()
                else None
            )
        )

    async def _event_processing_loop(self) -> None:
        """Main event processing loop."""
        while True:
            try:
                event = await self.event_bus.get()
                await self._process_event(event)
            except Exception as e:
                self.logger.exception(f"Event processing error: {e}")

    async def _process_event(self, event: CognitiveEvent) -> None:
        """Process individual events."""
        # Emergent behavior detection
        if self.emergent_behavior_detection:
            await self._detect_emergent_behavior(event)

        # Meta-learning
        if self.meta_learning_enabled:
            await self._update_meta_learning(event)

        # Protocol evolution
        if self.protocol_evolution_enabled:
            await self._evolve_protocols(event)

    async def _analyze_module_capabilities(
        self,
        module_interface: Any,
    ) -> dict[str, Any]:
        """Analyze the capabilities of a registered module."""
        return {
            "methods": [method for method in dir(module_interface) if not method.startswith("_")],
            "paradigm_support": "unknown",  # Would analyze in production
            "performance_characteristics": "unknown",
        }

    async def _execute_on_module(
        self,
        module_interface: Any,
        event: CognitiveEvent,
    ) -> Any:
        """Execute an event on a target module."""
        # Simplified execution - would be more sophisticated in production
        if hasattr(module_interface, "process"):
            return await module_interface.process(event.payload)
        return f"Processed by {module_interface.__class__.__name__}: {event.payload}"

    async def _build_ollama_context(
        self,
        context_events: list[CognitiveEvent],
    ) -> dict[str, Any]:
        """Build context for Ollama from relevant events."""
        return {
            "previous_interactions": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "content": str(event.payload),
                    "source": event.source,
                    "tags": event.tags,
                }
                for event in context_events[-5:]  # Last 5 interactions
            ],
            "session_context": "ai_intermediary_session",
        }

    async def dispatch_to_background(
        self,
        prompt: str,
        task_type: str = "general",
        requesting_agent: str = "claude",
        priority: str = "normal",
    ) -> dict[str, Any]:
        """Dispatch a high-token task to the BackgroundTaskOrchestrator.

        Use this for expensive operations that should run on local LLMs (Ollama, LM Studio)
        instead of consuming Claude/Copilot tokens.

        Args:
            prompt: The task prompt/instruction to execute
            task_type: Type of task (code_analysis, code_generation, general, etc.)
            requesting_agent: Which agent is submitting (claude, copilot, codex)
            priority: Task priority (low, normal, high, critical)

        Returns:
            Dict with task_id for tracking, or error info

        Example:
            >>> intermediary = AIIntermediary()
            >>> result = await intermediary.dispatch_to_background(
            ...     "Analyze this large codebase for security issues",
            ...     task_type="code_analysis",
            ...     requesting_agent="claude"
            ... )
            >>> print(f"Task submitted: {result['task_id']}")
        """
        try:
            from src.orchestration.background_task_orchestrator import (
                BackgroundTaskOrchestrator, TaskPriority, TaskTarget)

            # Map priority string to enum
            priority_map = {
                "low": TaskPriority.LOW,
                "normal": TaskPriority.NORMAL,
                "high": TaskPriority.HIGH,
                "critical": TaskPriority.CRITICAL,
            }
            task_priority = priority_map.get(priority.lower(), TaskPriority.NORMAL)

            # Get or create orchestrator instance
            orchestrator = BackgroundTaskOrchestrator()

            # Submit task
            task = orchestrator.submit_task(
                prompt=prompt,
                target=TaskTarget.AUTO,
                priority=task_priority,
                requesting_agent=requesting_agent,
                task_type=task_type,
            )

            self.logger.info(
                "Dispatched background task %s for %s (%s)",
                task.task_id,
                requesting_agent,
                task_type,
            )

            return {
                "success": True,
                "task_id": task.task_id,
                "target": task.target.value,
                "model": task.model,
                "status": task.status.value,
                "message": f"Task {task.task_id} submitted to {task.target.value}",
            }

        except ImportError as e:
            self.logger.warning("BackgroundTaskOrchestrator not available: %s", e)
            return {
                "success": False,
                "error": "BackgroundTaskOrchestrator not available",
                "fallback": "Use process_with_ollama for direct processing",
            }
        except Exception as e:
            self.logger.exception("Failed to dispatch background task: %s", e)
            return {
                "success": False,
                "error": str(e),
            }

    async def check_background_task(self, task_id: str) -> dict[str, Any]:
        """Check status of a background task.

        Args:
            task_id: The task ID returned from dispatch_to_background

        Returns:
            Task status and result (if completed)
        """
        try:
            from src.orchestration.background_task_orchestrator import \
                BackgroundTaskOrchestrator

            orchestrator = BackgroundTaskOrchestrator()
            task = orchestrator.tasks.get(task_id)

            if not task:
                return {"success": False, "error": f"Task {task_id} not found"}

            return {
                "success": True,
                "task_id": task.task_id,
                "status": task.status.value,
                "progress": task.progress,
                "result": task.result[:500] if task.result else None,
                "error": task.error,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _detect_emergent_behavior(self, event: CognitiveEvent) -> None:
        """Detect and log emergent behaviors in the system."""
        # Simplified emergent behavior detection
        if event.recursion_depth > 5:
            event.tags.append("emergent_recursion")

        if len(event.tags) > 10:
            event.tags.append("emergent_complexity")

    async def _update_meta_learning(self, event: CognitiveEvent) -> None:
        """Update meta-learning algorithms based on event patterns."""
        state = self.meta_learning_state
        state["total_events"] += 1
        state["max_recursion_depth"] = max(
            int(state["max_recursion_depth"]),
            int(event.recursion_depth),
        )

        if event.source:
            state["source_counts"][event.source] += 1
        if event.target:
            state["target_counts"][event.target] += 1
            state["routed_events"] += 1
        if "routed" in event.tags:
            state["routed_events"] += 1
        if "error" in event.tags or "error" in event.meta_index:
            state["error_events"] += 1

        state["paradigm_counts"][event.paradigm.value] += 1
        state["tag_counts"].update(event.tags)
        state["context_key_counts"].update(event.context.keys())

        signature = {
            "event_id": event.event_id,
            "source": event.source,
            "target": event.target,
            "paradigm": event.paradigm.value,
            "tag_count": len(event.tags),
            "has_error": "error" in event.tags or "error" in event.meta_index,
        }
        recent_signatures: list[dict[str, Any]] = state["recent_signatures"]
        recent_signatures.append(signature)
        if len(recent_signatures) > 25:
            del recent_signatures[:-25]
        self._persist_meta_learning_snapshot()

    def get_meta_learning_snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot of learned event patterns."""
        state = self.meta_learning_state
        return {
            "total_events": state["total_events"],
            "error_events": state["error_events"],
            "routed_events": state["routed_events"],
            "max_recursion_depth": state["max_recursion_depth"],
            "source_counts": dict(state["source_counts"]),
            "target_counts": dict(state["target_counts"]),
            "paradigm_counts": dict(state["paradigm_counts"]),
            "tag_counts": dict(state["tag_counts"]),
            "context_key_counts": dict(state["context_key_counts"]),
            "recent_signatures": list(state["recent_signatures"]),
        }

    def _persist_meta_learning_snapshot(self) -> None:
        """Persist the latest meta-learning snapshot for operator surfaces."""
        payload = {
            "generated_at": datetime.now(UTC).isoformat(),
            "snapshot": self.get_meta_learning_snapshot(),
        }
        try:
            self.meta_learning_report_path.parent.mkdir(parents=True, exist_ok=True)
            self.meta_learning_report_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            self.logger.debug("Failed to persist meta-learning snapshot", exc_info=True)

    async def _evolve_protocols(self, event: CognitiveEvent) -> None:
        """Evolve communication protocols based on system usage."""
        # Simplified protocol evolution

    # ========== AI Council Integration ==========

    async def propose_to_council(
        self,
        topic: str,
        description: str,
        proposer: str = "ai_intermediary",
    ) -> dict[str, Any]:
        """Propose a decision to the AI Council for multi-agent voting.

        Use this to get consensus from multiple AI agents before taking
        significant actions (architecture changes, major refactors, etc.).

        Args:
            topic: Short topic/title for the decision
            description: Full description of what's being proposed
            proposer: Who/what is proposing this decision

        Returns:
            Dict with decision_id and status
        """
        try:
            import uuid

            from src.orchestration.ai_council_voting import AICouncilVoting

            council = AICouncilVoting()
            decision_id = f"{topic.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"

            decision = council.create_decision(
                decision_id=decision_id,
                topic=topic,
                description=description,
                proposed_by=proposer,
            )

            self.logger.info(
                "Proposed to AI Council: %s (%s)",
                decision_id,
                topic,
            )

            return {
                "success": True,
                "decision_id": decision.decision_id,
                "topic": topic,
                "status": decision.status,
                "message": "Decision created. Agents can now cast votes.",
            }

        except ImportError:
            return {
                "success": False,
                "error": "AICouncilVoting not available",
            }
        except Exception as e:
            self.logger.exception("Failed to propose to council: %s", e)
            return {"success": False, "error": str(e)}

    async def vote_in_council(
        self,
        decision_id: str,
        vote: str,  # "approve", "reject", "abstain", "needs_more_info"
        confidence: float = 0.8,
        expertise: float = 0.7,
        reasoning: str = "",
        agent_id: str = "claude",
        agent_name: str = "Claude",
    ) -> dict[str, Any]:
        """Cast a vote on a council decision.

        Args:
            decision_id: ID of the decision to vote on
            vote: Vote choice (approve/reject/abstain/needs_more_info)
            confidence: How confident in this vote (0-1)
            expertise: Expertise level in this domain (0-1)
            reasoning: Why voting this way
            agent_id: ID of the voting agent
            agent_name: Name of the voting agent

        Returns:
            Dict with vote status
        """
        try:
            from src.orchestration.ai_council_voting import (AICouncilVoting,
                                                             VoteChoice)

            vote_map = {
                "approve": VoteChoice.APPROVE,
                "reject": VoteChoice.REJECT,
                "abstain": VoteChoice.ABSTAIN,
                "needs_more_info": VoteChoice.NEEDS_MORE_INFO,
            }

            vote_choice = vote_map.get(vote.lower())
            if not vote_choice:
                return {"success": False, "error": f"Invalid vote: {vote}"}

            council = AICouncilVoting()
            council.cast_vote(
                decision_id=decision_id,
                agent_id=agent_id,
                agent_name=agent_name,
                vote=vote_choice,
                confidence=confidence,
                expertise_level=expertise,
                reasoning=reasoning or f"{agent_name} voted {vote}",
            )

            # Get updated decision status
            decision = council.get_decision(decision_id)
            if decision:
                return {
                    "success": True,
                    "decision_id": decision_id,
                    "vote_recorded": vote,
                    "decision_status": decision.status,
                    "consensus": (
                        decision.consensus_level.value if decision.consensus_level else None
                    ),
                }
            return {"success": True, "decision_id": decision_id, "vote_recorded": vote}

        except ImportError:
            return {"success": False, "error": "AICouncilVoting not available"}
        except Exception as e:
            self.logger.exception("Failed to cast vote: %s", e)
            return {"success": False, "error": str(e)}

    async def execute_council_decision(
        self,
        decision_id: str,
        task_type: str = "code_analysis",
    ) -> dict[str, Any]:
        """Execute an approved council decision via BackgroundTaskOrchestrator.

        Args:
            decision_id: ID of the approved decision
            task_type: Type of background task

        Returns:
            Dict with execution status and task_id
        """
        try:
            from src.orchestration.ai_council_voting import AICouncilVoting

            council = AICouncilVoting()
            raw_result = council.dispatch_to_background(decision_id, task_type)
            result: dict[str, Any]
            if isinstance(raw_result, dict):
                result = dict(raw_result)
            else:
                result = {
                    "success": False,
                    "error": f"Unexpected dispatch result type: {type(raw_result).__name__}",
                }

            if result.get("success"):
                self.logger.info(
                    "Council decision %s dispatched: %s",
                    decision_id,
                    result.get("task_id"),
                )

            try:
                from src.system.agent_awareness import emit as _emit

                _ok = result.get("success", False)
                _lvl = "INFO" if _ok else "WARNING"
                _emit(
                    "agents",
                    f"Council decision dispatched: id={decision_id[:40]} success={_ok}",
                    level=_lvl,
                    source="ai_intermediary",
                )
            except Exception:
                pass

            return result

        except ImportError:
            return {"success": False, "error": "AICouncilVoting not available"}
        except Exception as e:
            self.logger.exception("Failed to execute council decision: %s", e)
            return {"success": False, "error": str(e)}

    async def get_council_status(self) -> dict[str, Any]:
        """Get the current status of the AI Council.

        Returns:
            Dict with council statistics
        """
        try:
            from src.orchestration.ai_council_voting import AICouncilVoting

            council = AICouncilVoting()
            raw_status = council.get_council_status()
            if isinstance(raw_status, dict):
                return dict(raw_status)
            return {"error": f"Unexpected council status type: {type(raw_status).__name__}"}

        except ImportError:
            return {"error": "AICouncilVoting not available"}
        except Exception as e:
            return {"error": str(e)}


class SecurityLayer:
    """Security and validation layer for the intermediary."""

    def __init__(self) -> None:
        """Initialize SecurityLayer."""
        self.auth_tokens: dict[str, Any] = {}
        self.validation_rules: dict[str, Any] = {}
        self.audit_log: list[Any] = []

    async def validate_input(self, event: CognitiveEvent) -> bool:
        """Validate input event for security."""
        if event.payload is None:
            self.audit_log.append({"event": event.event_id, "reason": "empty_payload"})
            return False

        if isinstance(event.payload, str) and len(event.payload) > MAX_PAYLOAD_CHARS:
            self.audit_log.append({"event": event.event_id, "reason": "payload_too_large"})
            return False

        paradigm_value = getattr(event, "paradigm", None)
        if not isinstance(paradigm_value, CognitiveParadigm):
            self.audit_log.append({"event": event.event_id, "reason": "invalid_paradigm"})
            return False

        return True

    async def authenticate(self, _entity: str, _action: str) -> bool:
        """Authenticate entity for specific action."""
        # Simplified authentication
        return True


# Custom exceptions
class AISecurityError(Exception):
    """Security error specific to AI operations."""


class AIModuleNotFoundError(Exception):
    """Module not found error specific to AI systems."""


# Factory function for easy initialization
async def create_ai_intermediary(
    ollama_hub: OllamaHub | None = None,
) -> AIIntermediary:
    """Factory function to create and initialize an AI Intermediary."""
    intermediary = AIIntermediary(ollama_hub)
    await intermediary.initialize()
    return intermediary


# Example usage and integration
if __name__ == "__main__":

    async def main() -> None:
        # Create the intermediary
        intermediary = await create_ai_intermediary()

        # Register some example modules
        class ExampleGameModule:
            async def process(self, payload) -> str:
                return f"Game processed: {payload}"

        class ExampleCodeModule:
            async def process(self, payload) -> str:
                return f"Code analyzed: {payload}"

        await intermediary.register_module(
            "game_ai",
            ExampleGameModule(),
            CognitiveParadigm.GAME_MECHANICS,
        )

        await intermediary.register_module(
            "code_ai",
            ExampleCodeModule(),
            CognitiveParadigm.CODE_ANALYSIS,
        )

        # Process some example inputs
        event1 = await intermediary.receive(
            "Create a new RPG character with magical abilities",
            {"user_id": "test_user"},
            "user",
            CognitiveParadigm.NATURAL_LANGUAGE,
        )

        # Route to game module
        await intermediary.route("game_ai", event1)

        # Process through Ollama
        await intermediary.process_with_ollama(event1)

        # Example of paradigm translation
        await intermediary.translate(
            "Optimize this function for performance",
            CognitiveParadigm.NATURAL_LANGUAGE,
            CognitiveParadigm.QUANTUM_NOTATION,
        )

    asyncio.run(main())
