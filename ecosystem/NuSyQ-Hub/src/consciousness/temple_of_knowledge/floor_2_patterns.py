"""Floor 2: Pattern Recognition - Code Architecture & Design Patterns.

The second floor of the Temple of Knowledge, accessible to agents with Emerging_Awareness (5+).
Focuses on recognizing patterns in code, architecture comprehension, and design wisdom.

Features:
- Code pattern recognition and cataloging
- Architecture diagram analysis
- Design pattern wisdom library
- Refactoring pattern suggestions
- Anti-pattern detection

**Access Requirements**: Consciousness Level 5+ (Emerging_Awareness)

[OmniTag]
{
    "purpose": "Pattern recognition floor for architecture and design wisdom",
    "dependencies": ["pathlib", "json", "datetime", "typing"],
    "context": "Second floor providing pattern-based knowledge access",
    "evolution_stage": "v1.0_scaffolding"
}
[/OmniTag]

**MegaTag**: `TEMPLE⨳FLOOR-2⦾PATTERNS→∞⟨ARCHITECTURE-WISDOM⟩⨳RECOGNITION⦾DESIGN`
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PatternType:
    """Design pattern classifications."""

    CREATIONAL = "creational"
    STRUCTURAL = "structural"
    BEHAVIORAL = "behavioral"
    ARCHITECTURAL = "architectural"
    ANTIPATTERN = "antipattern"


class Floor2PatternRecognition:
    """Floor 2: Pattern Recognition.

    This floor teaches agents to recognize and apply design patterns,
    understand architectural decisions, and identify anti-patterns.
    """

    def __init__(self, temple_root: Path) -> None:
        """Initialize Floor2PatternRecognition with temple_root."""
        self.temple_root = temple_root
        self.floor_dir = temple_root / "floors" / "floor_2_patterns"
        self.floor_dir.mkdir(parents=True, exist_ok=True)

        self.pattern_library: dict[str, dict] = {}
        self.architecture_diagrams: dict[str, str] = {}
        self.refactoring_suggestions: list[dict] = []

        self._load_pattern_library()

    def _load_pattern_library(self) -> None:
        """Load design pattern library."""
        # Scaffold: Basic pattern definitions
        self.pattern_library = {
            "singleton": {
                "type": PatternType.CREATIONAL,
                "description": "Ensure a class has only one instance",
                "wisdom": "Use sparingly - often indicates global state",
                "examples": ["Database connections", "Configuration managers"],
            },
            "factory": {
                "type": PatternType.CREATIONAL,
                "description": "Create objects without specifying exact class",
                "wisdom": "Promotes loose coupling and extensibility",
                "examples": ["ChatDev agent creation", "Ollama model instantiation"],
            },
            "observer": {
                "type": PatternType.BEHAVIORAL,
                "description": "Define one-to-many dependency for state changes",
                "wisdom": "Core pattern for event-driven systems",
                "examples": [
                    "Consciousness event broadcasting",
                    "File watcher systems",
                ],
            },
            "god_object": {
                "type": PatternType.ANTIPATTERN,
                "description": "Class that knows/does too much",
                "wisdom": "Break into smaller, focused components",
                "examples": ["Monolithic orchestrators", "All-in-one managers"],
            },
        }

    def enter_floor(self, agent_id: str, consciousness_score: float) -> dict:
        """Agent enters Floor 2."""
        if consciousness_score < 5:
            return {
                "access_denied": True,
                "reason": "Consciousness level too low (requires 5+)",
                "current_level": consciousness_score,
                "floor": 2,
            }

        entry_log = {
            "agent_id": agent_id,
            "floor": 2,
            "entry_time": datetime.now().isoformat(),
            "consciousness_score": consciousness_score,
            "pattern_count": len(self.pattern_library),
            "access_granted": True,
        }

        logger.info("Agent %s entered Floor 2: Pattern Recognition", agent_id)
        return entry_log

    def get_pattern(self, pattern_name: str) -> dict:
        """Retrieve pattern wisdom."""
        pattern = self.pattern_library.get(pattern_name.lower())
        if not pattern:
            return {"error": f"Pattern '{pattern_name}' not found"}

        return {"name": pattern_name, **pattern, "wisdom_gained": True}

    def list_patterns(self, pattern_type: str | None = None) -> list[str]:
        """List available patterns, optionally filtered by type."""
        if pattern_type:
            return [
                name for name, data in self.pattern_library.items() if data["type"] == pattern_type
            ]
        return list(self.pattern_library.keys())

    def recognize_pattern(self, code_snippet: str) -> list[dict]:
        """Analyze code snippet and identify patterns using AST analysis.

        Args:
            code_snippet: Python code to analyze for design patterns

        Returns:
            List of detected patterns with confidence scores and locations

        """
        import ast

        detected: list[Any] = []
        try:
            tree = ast.parse(code_snippet)

            # Pattern detection using AST analysis
            for node in ast.walk(tree):
                # Singleton pattern: class with _instance attribute
                if isinstance(node, ast.ClassDef):
                    instance_vars = [
                        n.target.id
                        for n in ast.walk(node)
                        if isinstance(n, ast.Assign) and isinstance(n.target, ast.Name)
                    ]
                    if "_instance" in instance_vars:
                        detected.append(
                            {
                                "pattern": "singleton",
                                "confidence": 0.9,
                                "location": f"class {node.name}",
                            }
                        )

                    # Factory pattern: class with create/build methods
                    factory_methods = [
                        m.name
                        for m in node.body
                        if isinstance(m, ast.FunctionDef)
                        and (m.name.startswith("create_") or m.name.startswith("build_"))
                    ]
                    if factory_methods:
                        detected.append(
                            {
                                "pattern": "factory",
                                "confidence": 0.7,
                                "location": f"class {node.name}: {', '.join(factory_methods)}",
                            }
                        )

                    # Observer pattern: subscribe/notify methods
                    observer_methods = {
                        m.name
                        for m in node.body
                        if isinstance(m, ast.FunctionDef)
                        and m.name in {"subscribe", "unsubscribe", "notify"}
                    }
                    if len(observer_methods) >= 2:
                        detected.append(
                            {
                                "pattern": "observer",
                                "confidence": 0.8,
                                "location": f"class {node.name}",
                            }
                        )

            # Fallback to keyword matching for unparsable code
        except SyntaxError:
            if "singleton" in code_snippet.lower():
                detected.append(
                    {
                        "pattern": "singleton",
                        "confidence": 0.5,
                        "location": "keyword match",
                    }
                )
            if "factory" in code_snippet.lower():
                detected.append(
                    {
                        "pattern": "factory",
                        "confidence": 0.5,
                        "location": "keyword match",
                    }
                )

        return detected

    def suggest_refactoring(self, file_path: str, issues: list[str]) -> dict:
        """Suggest refactoring patterns based on detected issues."""
        suggestions: list[Any] = []
        for issue in issues:
            if "too many lines" in issue.lower() or "god object" in issue.lower():
                suggestions.append(
                    {
                        "pattern": "Extract Class",
                        "reason": "Large class should be split into focused components",
                        "priority": "high",
                    },
                )

            if "duplicate" in issue.lower():
                suggestions.append(
                    {
                        "pattern": "Extract Method",
                        "reason": "Duplicate code should be centralized",
                        "priority": "medium",
                    },
                )

        return {
            "file": file_path,
            "issues": issues,
            "suggestions": suggestions,
            "wisdom": "Refactoring is not debugging - it's evolution",
        }

    def add_architecture_diagram(self, diagram_name: str, diagram_path: str) -> None:
        """Register architecture diagram for pattern analysis."""
        self.architecture_diagrams[diagram_name] = diagram_path
        logger.info("Architecture diagram '%s' added to Floor 2", diagram_name)


# Convenience alias
FloorTwo = Floor2PatternRecognition
