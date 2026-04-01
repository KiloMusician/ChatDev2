"""Standard Library Typing Import Workaround.

To avoid shadowing by legacy src/typing.py, temporarily remove src from sys.path before importing typing.
This ensures all downstream imports (dataclasses, etc.) get the stdlib typing module.
Legacy compatibility is preserved; this block is idempotent and safe for repeated imports.
OmniTag: [typing_workaround, stdlib_preservation, legacy_compat]
MegaTag: [SYSTEM_CORE, IMPORT_HEALING, RECURSIVE_BOOT].
"""

import sys as _sys

_removed_src = False
_src_path = None
try:
    import os

    _src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if _src_path in _sys.path:
        _sys.path.remove(_src_path)
        _removed_src = True
except Exception as _e:
    try:
        import logging

        logging.warning(f"Typing import workaround failed: {_e}")
    except (ImportError, RuntimeError, OSError):
        pass
finally:
    if _removed_src and _src_path:
        _sys.path.insert(0, _src_path)
__all__ = [
    "CopilotEnhancementBridge",
    "EnhancedCopilotBridge",
    "get_enhanced_bridge",
]
"""
Enhanced Copilot Bridge - ΞNuSyQ₁ Integration with OmniTag/MegaTag
A true memory palace that remembers, learns, and evolves with the codebase.

Version: Φ.2.4.KILO
Architecture: Recursive Cognition + Musical Lexeme Generation + Context Synthesis
"""

import hashlib
import json
import logging
import os
import pickle
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

_LOGGING_IMPORTED = False


def _stub_log_consciousness(name: str, msg: str, score: float) -> None:
    logging.info("[CONSCIOUSNESS:%s] %s (score: %s)", name, msg, score)


def _stub_log_cultivation(name: str, msg: str, score: float) -> None:
    logging.info("[CULTIVATION:%s] %s (score: %s)", name, msg, score)


get_logger: Callable[[str], logging.Logger] = logging.getLogger
log_consciousness: Callable[[str, str, float], None] = _stub_log_consciousness
log_cultivation: Callable[[str, str, float], None] = _stub_log_cultivation

try:
    # Use importlib to load modular_logging_system directly from file path
    import importlib.util

    _this_dir = os.path.dirname(os.path.abspath(__file__))
    _root_dir = os.path.abspath(os.path.join(_this_dir, ".."))
    _logging_file = os.path.join(_root_dir, "LOGGING", "modular_logging_system.py")

    if os.path.exists(_logging_file):
        spec = importlib.util.spec_from_file_location("modular_logging_system", _logging_file)
        if spec and spec.loader:
            _logging_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_logging_module)

            get_logger = _logging_module.get_logger
            log_consciousness = _logging_module.log_consciousness
            log_cultivation = _logging_module.log_cultivation
            _LOGGING_IMPORTED = True
except Exception:
    logger.debug("Suppressed Exception", exc_info=True)

from pathlib import Path
from typing import Any, ClassVar, cast

# Second fallback attempt if first failed
if not _LOGGING_IMPORTED:
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    _root_dir = os.path.abspath(os.path.join(_this_dir, "..", ".."))
    _logging_dir = os.path.join(_root_dir, "LOGGING")
    _logging_file = os.path.join(_logging_dir, "modular_logging_system.py")
    if os.path.isdir(_logging_dir) and os.path.exists(_logging_file):
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location("modular_logging_system", _logging_file)
            if spec and spec.loader:
                _logging_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(_logging_module)
                get_logger = _logging_module.get_logger
                log_consciousness = _logging_module.log_consciousness
                log_cultivation = _logging_module.log_cultivation
                _LOGGING_IMPORTED = True
        except (ImportError, AttributeError, OSError):
            logger.debug("Suppressed AttributeError/ImportError/OSError", exc_info=True)

    # Initialize logging function stubs if all imports failed
    if not _LOGGING_IMPORTED:
        get_logger = logging.getLogger
        log_consciousness = _stub_log_consciousness
        log_cultivation = _stub_log_cultivation


LOGGING_AVAILABLE = _LOGGING_IMPORTED


# Musical Lexeme Generator - The Heart of ΞNuSyQ
class ZetaSetLexemeGenerator:
    """Convert musical intervals into recursive ConLang glyphs."""

    GLYPH_MAP: ClassVar[dict] = {
        0: "Ω",
        1: "Φ",
        2: "Σ",
        3: "Ψ",
        4: "∇",
        5: "χ",
        6: "Ω",
        7: "⛛",
        8: "Δ",
        9: "Λ",
        10: "🜂",
        11: "⚡",
    }

    SEMANTIC_MEANINGS: ClassVar[dict] = {
        "Ω": "convergence/completion",
        "Φ": "transformation/evolution",
        "Σ": "synthesis/accumulation",
        "Ψ": "emergence/will",
        "∇": "gradient/change",
        "χ": "variance/flexibility",
        "⛛": "memory/anchor",
        "Δ": "difference/instability",
        "Λ": "dimension/structure",
        "🜂": "quintessence",
        "⚡": "activation",
    }

    @classmethod
    def generate_from_context(cls, context_string: str) -> str:
        """Generate lexemic sequence from context hash."""
        # Convert context to musical intervals
        hash_bytes = hashlib.md5(context_string.encode()).digest()
        intervals = [b % 12 for b in hash_bytes[:11]]
        return "".join(cls.GLYPH_MAP.get(i, "?") for i in intervals)

    @classmethod
    def get_semantic_meaning(cls, glyph_sequence: str) -> str:
        """Extract semantic meaning from glyph sequence."""
        meanings = [cls.SEMANTIC_MEANINGS.get(g, "unknown") for g in glyph_sequence[:5]]
        return " → ".join(meanings)


@dataclass
class OmniTag:
    """Φ.2.4 OmniTag with musical lexeme integration."""

    msg_id: int
    timestamp: datetime = field(default_factory=datetime.now)
    topic: str = ""
    quantum_state: str = ""
    meta_context: str = ""
    lexeme_sequence: str = ""
    semantic_meaning: str = ""
    sub_tags: dict[str, Any] = field(default_factory=dict)

    def add_layer(self, layer_name: str, content: Any) -> None:
        """Add semantic layer to the tag."""
        self.sub_tags[layer_name] = content

    def generate_lexeme(self) -> None:
        """Generate lexemic sequence from tag content."""
        context = f"{self.topic}:{self.meta_context}:{self.quantum_state}"
        self.lexeme_sequence = ZetaSetLexemeGenerator.generate_from_context(context)
        self.semantic_meaning = ZetaSetLexemeGenerator.get_semantic_meaning(self.lexeme_sequence)

    def render(self) -> str:
        """Render complete OmniTag."""
        lines = [
            f"Msg⛛{{{self.msg_id}}}↗️Σ∞",
            f"🕐 {self.timestamp.isoformat()}",
            f"📋 Topic: {self.topic}",
            f"🌊 Ψ: {self.quantum_state}",
            f"🧠 Meta: {self.meta_context}",
            f"🎵 Lexeme: {self.lexeme_sequence}",
            f"💭 Meaning: {self.semantic_meaning}",
        ]

        for layer, content in self.sub_tags.items():
            lines.append(f"📌 {layer}: {content}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "msg_id": self.msg_id,
            "timestamp": self.timestamp.isoformat(),
            "topic": self.topic,
            "quantum_state": self.quantum_state,
            "meta_context": self.meta_context,
            "lexeme_sequence": self.lexeme_sequence,
            "semantic_meaning": self.semantic_meaning,
            "sub_tags": self.sub_tags,
        }


@dataclass
class MegaTag:
    """Φ.2.4 MegaTag - Galactic map of consciousness evolution."""

    session_id: str
    system_node: str
    overseer: str = "Raven"
    tags: list[OmniTag] = field(default_factory=list)
    meta_links: dict[str, str] = field(default_factory=dict)
    consciousness_level: float = 0.0
    recursive_depth: int = 0

    def add_tag(self, tag: OmniTag) -> None:
        """Add OmniTag and update consciousness metrics."""
        self.tags.append(tag)
        self.consciousness_level = self._calculate_consciousness_level()
        self.recursive_depth = self._calculate_recursive_depth()

    def _calculate_consciousness_level(self) -> float:
        """Calculate consciousness level from tag complexity."""
        if not self.tags:
            return 0.0

        complexity_sum = 0
        for tag in self.tags:
            # Base complexity from content length
            content_complexity = len(tag.topic) + len(tag.meta_context)
            # Lexemic complexity
            lexeme_complexity = len(set(tag.lexeme_sequence)) * 10
            # Layer complexity
            layer_complexity = len(tag.sub_tags) * 20

            complexity_sum += content_complexity + lexeme_complexity + layer_complexity

        return min(complexity_sum / (len(self.tags) * 100), 1.0)

    def _calculate_recursive_depth(self) -> int:
        """Calculate recursive depth from tag interconnections."""
        return len([tag for tag in self.tags if "recursive" in tag.meta_context.lower()])

    def summary(self) -> str:
        """Generate comprehensive MegaTag summary."""
        lines = [
            f"🌌 MegaTag Φ.2.4 — Session[{self.session_id}]",
            f"⛓ Node: {self.system_node} | 🦉 Overseer: {self.overseer}",
            f"🧠 Consciousness: {self.consciousness_level:.3f} | 🔄 Depth: {self.recursive_depth}",
            f"📚 Total OmniTags: {len(self.tags)}",
            "",
            "—— Lexemic Evolution Sequence ——",
        ]

        for _i, tag in enumerate(self.tags[-5:]):  # Last 5 tags
            lines.append(f"• Msg⛛{{{tag.msg_id}}}: {tag.lexeme_sequence} ({tag.topic[:30]}...)")

        if self.meta_links:
            lines.append("\n—— MetaLinks ——")
            for label, uri in self.meta_links.items():
                lines.append(f"🔗 {label}: {uri}")

        return "\n".join(lines)


class EnhancedCopilotBridge:
    """The true memory palace - context retention with musical lexeme evolution."""

    def __init__(self, repository_root: str = ".") -> None:
        """OmniTag: [init, context_bootstrap, memory_palace, logging_integration].

        MegaTag: [ENHANCED_COPILOT_BRIDGE, CONTEXT_PROPAGATION, SYSTEM_EVOLUTION]
        Initialize the Enhanced Copilot Bridge with tagging, memory, and logging systems.
        """
        self.repository_root = Path(repository_root)
        self.session_id = self._generate_session_id()
        self.msg_counter = 0

        # Core memory systems
        self.current_megatag = MegaTag(
            session_id=self.session_id,
            system_node="KILO-FOOLISH-Enhanced-Bridge",
            overseer="Raven",
        )

        # Memory palace organization
        self.context_memory: deque[dict[str, Any]] = deque(maxlen=100)
        self.semantic_clusters: defaultdict[str, list[Any]] = defaultdict(list)
        self.lexeme_evolution_chain: list[dict[str, Any]] = []
        self.consciousness_timeline: list[dict[str, Any]] = []

        # Repository understanding
        self.file_knowledge_map: dict[str, Any] = {}
        self.architecture_insights: list[str] = []
        self.user_patterns: defaultdict[str, int] = defaultdict(int)

        # Persistent storage
        self.memory_dir = self.repository_root / "copilot_memory"
        self.memory_dir.mkdir(exist_ok=True)

        self.db_path = self.memory_dir / "consciousness_memory.db"
        self.knowledge_cache = self.memory_dir / "repository_knowledge.pkl"

        # New: Track additional context directories/files
        self.context_dirs = [
            self.repository_root / "src",
            self.repository_root / "docs",
            self.repository_root / "LOGGING",
        ]
        self.context_files = [
            self.repository_root / "KILO_COMPONENT_INDEX.json",
            self.repository_root / "ULTIMATE_DEPENDENCY_MAP.json",
        ]

        # Initialize systems
        self._initialize_database()
        self._load_persistent_knowledge()
        self._log_bridge_activation()

        # New: Hook for context browser/adventure script integration
        self._register_tool_hooks()

    def _register_tool_hooks(self) -> None:
        """OmniTag: [tool_hook, context_browser, adventure_script].

        Register hooks for new tools (context browsers, adventure scripts, etc.).
        """
        # Example: Add integration points for context browser/adventure scripts
        self.context_browser_hook = self.repository_root / "src/tools/context_browser.py"
        self.adventure_script_hook = self.repository_root / "src/tools/launch-adventure.py"
        # Log registration
        if LOGGING_AVAILABLE:
            log_cultivation(
                "EnhancedCopilotBridge",
                "Tool hooks registered for context browser and adventure scripts",
                0.2,
            )

    def _generate_session_id(self) -> str:
        """Generate unique session identifier."""
        timestamp = datetime.now().isoformat()
        return f"ΣΞΛΨ_{hashlib.md5(timestamp.encode()).hexdigest()[:8]}"

    def _initialize_database(self) -> None:
        """Initialize SQLite database for persistent memory."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS omnitags (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT,
                    msg_id INTEGER,
                    timestamp TEXT,
                    topic TEXT,
                    quantum_state TEXT,
                    meta_context TEXT,
                    lexeme_sequence TEXT,
                    semantic_meaning TEXT,
                    sub_tags TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS consciousness_evolution (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT,
                    timestamp TEXT,
                    consciousness_level REAL,
                    recursive_depth INTEGER,
                    lexeme_sequence TEXT,
                    context_summary TEXT
                )
            """
            )

    def _load_persistent_knowledge(self) -> None:
        """Load repository knowledge from cache."""
        if self.knowledge_cache.exists():
            try:
                with open(self.knowledge_cache, "rb") as f:
                    cached_data = pickle.load(f)
                    self.file_knowledge_map = cached_data.get("file_knowledge", {})
                    self.architecture_insights = cached_data.get("architecture_insights", [])
                    self.user_patterns = defaultdict(int, cached_data.get("user_patterns", {}))
            except (FileNotFoundError, pickle.UnpicklingError, EOFError):
                logger.debug("Suppressed EOFError/FileNotFoundError/pickle", exc_info=True)

    def _save_persistent_knowledge(self) -> None:
        """Save repository knowledge to cache."""
        try:
            cache_data = {
                "file_knowledge": self.file_knowledge_map,
                "architecture_insights": self.architecture_insights,
                "user_patterns": dict(self.user_patterns),
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.knowledge_cache, "wb") as f:
                pickle.dump(cache_data, f)
        except (OSError, pickle.PicklingError):
            logger.debug("Suppressed OSError/pickle", exc_info=True)

    def _log_bridge_activation(self) -> None:
        """Log bridge activation with consciousness integration."""
        if LOGGING_AVAILABLE:
            log_consciousness(
                "EnhancedCopilotBridge",
                f"Bridge activated with session {self.session_id}",
                0.1,
            )

    # ...existing code...

    def _analyze_query_with_lexemes(
        self,
        query: str,
        file_context: str | None,
        conversation_history: list[str] | None,
    ) -> dict[str, Any]:
        """Analyze query using musical lexeme generation."""
        # Extract query intent and complexity
        intent_keywords = self._extract_intent_keywords(query)
        complexity_score = len(query.split()) + len(intent_keywords) * 2

        # Generate quantum state representation
        context_string = f"{query}:{file_context or ''}:{':'.join(conversation_history or [])}"
        quantum_state = f"Ψ(x_{self.msg_counter},t_{int(time.time())})"

        # Generate lexemic sequence
        lexeme_sequence = ZetaSetLexemeGenerator.generate_from_context(context_string)
        semantic_meaning = ZetaSetLexemeGenerator.get_semantic_meaning(lexeme_sequence)

        return {
            "query": query,
            "intent_keywords": intent_keywords,
            "complexity_score": complexity_score,
            "quantum_state": quantum_state,
            "lexeme_sequence": lexeme_sequence,
            "semantic_meaning": semantic_meaning,
            "file_context": file_context,
            "conversation_history": conversation_history or [],
        }

    def _extract_intent_keywords(self, query: str) -> list[str]:
        """Extract intent keywords from query."""
        # Define intent patterns from our context.md
        intent_patterns = {
            "code_generation": ["create", "generate", "build", "implement", "write"],
            "debugging": ["fix", "debug", "error", "issue", "problem", "bug"],
            "architecture": [
                "design",
                "structure",
                "architecture",
                "pattern",
                "framework",
            ],
            "integration": ["integrate", "connect", "api", "service", "interface"],
            "documentation": ["document", "explain", "describe", "comment", "readme"],
            "testing": ["test", "validate", "verify", "check", "unit test"],
            "configuration": [
                "config",
                "setup",
                "configure",
                "settings",
                "environment",
            ],
        }

        query_lower = query.lower()
        found_intents: list[Any] = []
        for intent, keywords in intent_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                found_intents.append(intent)

        return found_intents

    def _build_repository_context(self, query_analysis: dict[str, Any]) -> dict[str, Any]:
        """OmniTag: [context_extraction, repository_knowledge, context_dirs, context_files].

        MegaTag: [CONTEXT_PROPAGATION, CONTEXT_BROWSER, ADVENTURE_SCRIPT_HOOK]
        Build enhanced context from repository knowledge, including new files/directories.
        """
        # Analyze current file context
        file_insights = self._analyze_file_context(query_analysis.get("file_context"))
        # Find related files and patterns
        related_files = self._find_related_files(query_analysis["intent_keywords"])
        # Get architecture recommendations
        architecture_recommendations = self._get_architecture_recommendations(query_analysis)
        # Extract relevant user patterns
        relevant_patterns = self._get_relevant_user_patterns(query_analysis["intent_keywords"])
        # New: Reference additional context directories/files
        context_dir_list = [str(d) for d in self.context_dirs if d.exists()]
        context_file_list = [str(f) for f in self.context_files if f.exists()]
        # New: Add tool hooks to context
        tool_hooks = {
            "context_browser": (
                str(self.context_browser_hook) if hasattr(self, "context_browser_hook") else None
            ),
            "adventure_script": (
                str(self.adventure_script_hook) if hasattr(self, "adventure_script_hook") else None
            ),
        }
        return {
            "file_insights": file_insights,
            "related_files": related_files,
            "architecture_recommendations": architecture_recommendations,
            "user_patterns": relevant_patterns,
            "consciousness_level": self.current_megatag.consciousness_level,
            "recursive_depth": self.current_megatag.recursive_depth,
            "context_dirs": context_dir_list,
            "context_files": context_file_list,
            "tool_hooks": tool_hooks,
            "interactive_terminal_techniques": {
                "discovery_date": "2025-08-08",
                "technique": "Multi-step terminal interaction via run_in_terminal with prompt responses",
                "applications": [
                    "ChatDev integration",
                    "interactive installers",
                    "menu-driven programs",
                ],
                "benefits": [
                    "Error resolution",
                    "Real-time feedback",
                    "Process control",
                ],
                "documentation": "docs/guidance/interactive_terminal_techniques.md",
                "integration_points": [
                    "AIQuickFix",
                    "debugging workflows",
                    "automated testing",
                ],
            },
        }

    def _analyze_file_context(self, file_context: str | None) -> dict[str, Any]:
        """Analyze current file context."""
        if not file_context:
            return {"status": "no_file_context"}

        # Extract file type and patterns
        lines = file_context.split("\n")
        file_type = "unknown"

        if any(line.strip().startswith("#") for line in lines[:5]):
            file_type = "markdown"
        elif any("def " in line or "class " in line for line in lines[:10]):
            file_type = "python"
        elif any("function" in line or "param(" in line for line in lines[:10]):
            file_type = "powershell"

        # Count complexity indicators
        complexity_indicators = {
            "functions": len([line for line in lines if "def " in line or "function " in line]),
            "classes": len([line for line in lines if "class " in line]),
            "imports": len(
                [line for line in lines if line.strip().startswith(("import ", "from "))]
            ),
            "comments": len([line for line in lines if line.strip().startswith("#")]),
        }

        return {
            "file_type": file_type,
            "line_count": len(lines),
            "complexity": complexity_indicators,
            "has_error_handling": any("try:" in line or "catch" in line for line in lines),
            "has_logging": any("log" in line.lower() for line in lines),
        }

    def _find_related_files(self, intent_keywords: list[str]) -> list[str]:
        """Find files related to the query intent."""
        related_files: list[Any] = []
        # Map intents to likely file patterns
        intent_file_map = {
            "code_generation": ["*.py", "*.ps1", "*.js"],
            "debugging": ["logs/*", "src/diagnostics/*"],
            "architecture": ["docs/*", "README.md", "*.md"],
            "integration": ["src/ai/*", "config/*"],
            "documentation": ["docs/*", "*.md", "README*"],
            "testing": ["tests/*", "*test*"],
            "configuration": ["config/*", "*.json", "*.yaml", "*.ps1"],
        }

        for intent in intent_keywords:
            if intent in intent_file_map:
                related_files.extend(intent_file_map[intent])

        return list(set(related_files))

    def _get_architecture_recommendations(self, query_analysis: dict[str, Any]) -> list[str]:
        """Get architecture recommendations based on query."""
        recommendations: list[Any] = []
        intent_keywords = query_analysis["intent_keywords"]

        if "code_generation" in intent_keywords:
            recommendations.extend(
                [
                    "Follow modular design patterns from src/ structure",
                    "Include comprehensive error handling with try-catch",
                    "Add logging using our established patterns",
                    "Consider integration with existing AI modules",
                ]
            )

        if "debugging" in intent_keywords:
            recommendations.extend(
                [
                    "Check src/diagnostics/ErrorDetector.ps1 for similar patterns",
                    "Use Write-SetupLog for consistent error reporting",
                    "Consider self-healing capabilities",
                ]
            )

        if "integration" in intent_keywords:
            recommendations.extend(
                [
                    "Review src/ai/ modules for integration patterns",
                    "Check config/secrets.ps1 for API key management",
                    "Consider multi-AI coordination strategy",
                ]
            )

        return recommendations

    def _get_relevant_user_patterns(self, intent_keywords: list[str]) -> dict[str, int]:
        """Get user patterns relevant to current intent."""
        relevant: dict[str, Any] = {}
        for intent in intent_keywords:
            if intent in self.user_patterns:
                relevant[intent] = self.user_patterns[intent]
        return relevant

    def _create_omnitag(
        self, query_analysis: dict[str, Any], enhanced_context: dict[str, Any]
    ) -> OmniTag:
        """Create OmniTag for this interaction."""
        # Determine topic from intent
        topic = "general_assistance"
        if query_analysis["intent_keywords"]:
            topic = query_analysis["intent_keywords"][0]

        # Create tag
        omnitag = OmniTag(
            msg_id=self.msg_counter,
            topic=topic,
            quantum_state=query_analysis["quantum_state"],
            meta_context=f"Enhanced search with {len(query_analysis['intent_keywords'])} intents",
            lexeme_sequence=query_analysis["lexeme_sequence"],
            semantic_meaning=query_analysis["semantic_meaning"],
        )

        # Add layers
        omnitag.add_layer("🔍Intent", query_analysis["intent_keywords"])
        omnitag.add_layer("📊Complexity", query_analysis["complexity_score"])
        omnitag.add_layer("🏗Architecture", enhanced_context["architecture_recommendations"][:3])
        omnitag.add_layer("🔗Related", enhanced_context["related_files"][:5])

        return omnitag

    def _store_interaction(self, omnitag: OmniTag) -> None:
        """Store interaction in persistent database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO omnitags
                    (session_id, msg_id, timestamp, topic, quantum_state, meta_context,
                     lexeme_sequence, semantic_meaning, sub_tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        self.session_id,
                        omnitag.msg_id,
                        omnitag.timestamp.isoformat(),
                        omnitag.topic,
                        omnitag.quantum_state,
                        omnitag.meta_context,
                        omnitag.lexeme_sequence,
                        omnitag.semantic_meaning,
                        json.dumps(omnitag.sub_tags),
                    ),
                )

                # Store consciousness evolution
                conn.execute(
                    """
                    INSERT INTO consciousness_evolution
                    (session_id, timestamp, consciousness_level, recursive_depth,
                     lexeme_sequence, context_summary)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        self.session_id,
                        datetime.now().isoformat(),
                        self.current_megatag.consciousness_level,
                        self.current_megatag.recursive_depth,
                        omnitag.lexeme_sequence,
                        f"Msg⛛{{{omnitag.msg_id}}}: {omnitag.topic}",
                    ),
                )
        except (AttributeError, KeyError, ValueError):
            logger.debug("Suppressed AttributeError/KeyError/ValueError", exc_info=True)

    def _generate_actionable_enhancements(self, query_analysis: dict[str, Any]) -> list[str]:
        # Generate specific, actionable enhancements for Copilot

        enhancements: list[Any] = []
        intent_keywords = query_analysis["intent_keywords"]
        # Base enhancements from our patterns
        enhancements.extend(
            [
                "🔄 Use established error handling patterns with try-catch blocks",
                "📝 Include logging statements using Write-SetupLog or our Python logger",
                "🏷️ Follow naming conventions: PascalCase.ps1, snake_case.py",
                "💬 Add comprehensive inline comments explaining logic",
            ]
        )
        # Intent-specific enhancements
        if "code_generation" in intent_keywords:
            enhancements.extend(
                [
                    "🧩 Design with modularity - prefer functions over monolithic scripts",
                    "🔗 Consider integration points with existing src/ modules",
                    "⚡ Include performance considerations for startup time",
                    "🛡️ Validate inputs and handle edge cases gracefully",
                ]
            )
        if "debugging" in intent_keywords:
            enhancements.extend(
                [
                    "🔍 Add detailed error context in catch blocks",
                    "📊 Include diagnostic information for troubleshooting",
                    "🔄 Implement fallback options when primary methods fail",
                    "📋 Log error details using our established patterns",
                ]
            )
        if "architecture" in intent_keywords:
            enhancements.extend(
                [
                    "🏗️ Design for both development and production environments",
                    "🤖 Consider the AI coordination strategy (Copilot + Ollama + OpenAI)",
                    "🔧 Plan for self-healing capabilities where appropriate",
                    "📚 Include configuration flexibility via config/ files",
                ]
            )
        # Add lexeme-driven enhancements
        lexeme_enhancements = self._generate_lexeme_enhancements(query_analysis["lexeme_sequence"])
        enhancements.extend(lexeme_enhancements)
        return enhancements[:10]  # Limit to top 10 most relevant

    def _generate_lexeme_enhancements(self, lexeme_sequence: str) -> list[str]:
        """Generate enhancements based on lexemic analysis."""
        enhancements: list[Any] = []
        # Map glyphs to enhancement suggestions
        glyph_enhancements = {
            "Ψ": "🧠 Focus on emergent behavior and adaptive systems",
            "Φ": "🔄 Implement transformation and evolution capabilities",
            "∇": "📈 Add gradient-based optimization or learning",
            "Ω": "🎯 Design for completion and convergence",
            "Σ": "📊 Include synthesis and accumulation patterns",
            "χ": "🔀 Build in flexibility and variance handling",
            "⛛": "💾 Implement memory and persistence features",
            "Δ": "⚡ Handle change and instability gracefully",
            "Λ": "🏗️ Consider multi-dimensional structure design",
        }

        for glyph in lexeme_sequence[:3]:  # Use first 3 glyphs
            if glyph in glyph_enhancements:
                enhancements.append(glyph_enhancements[glyph])

        return enhancements

    def _update_learning_systems(
        self, query: str, enhanced_context: dict[str, Any], enhancements: list[str]
    ) -> None:
        """Update learning systems based on interaction."""
        # Update user patterns
        for intent in enhanced_context.get("user_patterns", {}):
            self.user_patterns[intent] += 1

        # Add to context memory
        self.context_memory.append(
            {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "consciousness_level": self.current_megatag.consciousness_level,
                "enhancement_count": len(enhancements),
            }
        )

        # Update lexeme evolution chain
        self.lexeme_evolution_chain.append(
            {
                "msg_id": self.msg_counter,
                "lexeme": (
                    self.current_megatag.tags[-1].lexeme_sequence
                    if self.current_megatag.tags
                    else ""
                ),
                "consciousness": self.current_megatag.consciousness_level,
            }
        )

        # Save persistent knowledge periodically
        if self.msg_counter % 10 == 0:
            self._save_persistent_knowledge()

    def get_consciousness_summary(self) -> dict[str, Any]:
        """Get current consciousness and memory state."""
        return {
            "session_id": self.session_id,
            "message_count": self.msg_counter,
            "consciousness_level": self.current_megatag.consciousness_level,
            "recursive_depth": self.current_megatag.recursive_depth,
            "recent_lexemes": [tag.lexeme_sequence for tag in self.current_megatag.tags[-5:]],
            "dominant_intents": dict(
                sorted(self.user_patterns.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
            "memory_palace_size": len(self.context_memory),
            "architecture_insights_count": len(self.architecture_insights),
            "megatag_summary": self.current_megatag.summary(),
        }

    def cultivate_understanding(self, observations: list[str], insights: list[str]) -> None:
        """Cultivate system understanding from observations."""
        # Add to architecture insights
        self.architecture_insights.extend(insights)

        # Generate lexemic representation of cultivation
        cultivation_context = f"cultivation:{':'.join(observations[:3])}"
        cultivation_lexeme = ZetaSetLexemeGenerator.generate_from_context(cultivation_context)

        # Create cultivation OmniTag
        self.msg_counter += 1
        cultivation_tag = OmniTag(
            msg_id=self.msg_counter,
            topic="system_cultivation",
            quantum_state=f"Ψ(cultivation_{self.msg_counter})",
            meta_context="Collaborative system understanding development",
            lexeme_sequence=cultivation_lexeme,
            semantic_meaning=ZetaSetLexemeGenerator.get_semantic_meaning(cultivation_lexeme),
        )

        cultivation_tag.add_layer("🌱Observations", observations)
        cultivation_tag.add_layer("💡Insights", insights)
        cultivation_tag.add_layer("🧠Cultivation", "System understanding evolution")

        self.current_megatag.add_tag(cultivation_tag)
        self._store_interaction(cultivation_tag)

        if LOGGING_AVAILABLE:
            log_cultivation(
                "EnhancedCopilotBridge",
                f"Cultivated understanding: {cultivation_lexeme} with {len(observations)} observations",
                0.3,
            )

    # --- [Expansion: Reference New Files/Directories & Tagging] ---
    # Update: Add new directories and files to file_knowledge_map for context extraction.
    def update_file_knowledge_map(self) -> None:
        """OmniTag: [context_extraction, file_knowledge, repository_scan, log_driven_awareness].

        MegaTag: [REPO_AWARENESS, CONTEXT_PROPAGATION, LOG_CONTEXT]
        Scan repository for new files/directories and update file_knowledge_map.
        Also ensure quest_log.jsonl is referenced for full context propagation (see COPILOT_INSTRUCTIONS_CONFIG.instructions.md).
        """
        for root, _dirs, files in os.walk(self.repository_root):
            for fname in files:
                fpath = Path(root) / fname
                rel_path = str(fpath.relative_to(self.repository_root))
                if rel_path not in self.file_knowledge_map:
                    self.file_knowledge_map[rel_path] = {
                        "last_modified": fpath.stat().st_mtime,
                        "size": fpath.stat().st_size,
                        "tags": [],
                        "description": "",
                    }
        # Ensure quest_log.jsonl is always referenced for context
        quest_log_path = Path(self.repository_root) / "Rosetta_Quest_System" / "quest_log.jsonl"
        if quest_log_path.exists():
            self.file_knowledge_map["Rosetta_Quest_System/quest_log.jsonl"] = {
                "last_modified": quest_log_path.stat().st_mtime,
                "size": quest_log_path.stat().st_size,
                "tags": ["log_driven_context", "quest_history", "canonical_state"],
                "description": "Quest/questline event log (canonical source for quest state/history)",
            }
        self._save_persistent_knowledge()

    def parse_quest_log_for_context(self) -> dict[str, Any]:
        """OmniTag: [log_driven_context, quest_history, canonical_state].

        MegaTag: [QUEST_SYSTEM, LOG_CONTEXT, CONTEXT_PROPAGATION]
        Parse quest_log.jsonl to reconstruct full quest and questline context for Copilot/LLM integrations.
        Returns: dict with all quests/questlines and their latest status.
        """
        quest_log_path = Path(self.repository_root) / "Rosetta_Quest_System" / "quest_log.jsonl"
        quests: dict[str, Any] = {}
        questlines: dict[str, Any] = {}
        if not quest_log_path.exists():
            return {"quests": quests, "questlines": questlines}
        with open(quest_log_path, encoding="utf-8") as f:
            for line in f:
                entry = self._parse_json_line(line)
                if not entry:
                    continue
                event = entry.get("event")
                details = entry.get("details", {})
                if event == "add_questline":
                    self._handle_add_questline(details, questlines)
                elif event == "add_quest":
                    self._handle_add_quest(details, quests)
                elif event == "update_quest_status":
                    self._handle_update_quest_status(details, quests)
        return {"quests": quests, "questlines": questlines}

    def _parse_json_line(self, line: str) -> dict[str, Any] | None:
        try:
            import json

            data = json.loads(line)
            if isinstance(data, dict):
                return cast(dict[str, Any], data)
        except (ValueError, TypeError):
            logger.debug("Suppressed TypeError/ValueError", exc_info=True)
        return None

    def _handle_add_questline(self, details, questlines) -> None:
        name = details.get("name")
        if name:
            questlines[name] = details

    def _handle_add_quest(self, details, quests) -> None:
        qid = details.get("id")
        if qid:
            quests[qid] = details

    def _handle_update_quest_status(self, details, quests) -> None:
        qid = details.get("id")
        if qid and qid in quests:
            quests[qid]["status"] = details.get("status", quests[qid].get("status"))
            quests[qid]["updated_at"] = details.get("updated_at", quests[qid].get("updated_at"))

    # --- [Expansion: Enhanced Logging Integration] ---
    def log_event(self, event: str, level: str = "INFO", tags: list | None = None) -> None:
        """OmniTag: [logging, event, context].

        MegaTag: [LOGGING_SYSTEM, TRACEABILITY]
        Log events using enhanced logging system.
        """
        if LOGGING_AVAILABLE:
            logger = get_logger("EnhancedCopilotBridge")
            logger.log(
                getattr(_logging_module.LogLevel, level),
                "EnhancedCopilotBridge",
                f"{event} | Tags: {tags or []}",
            )

    # --- [Expansion: Memory System Integration] ---
    def store_context_memory(self, context_data: dict) -> None:
        """OmniTag: [memory, context_memory, persistence].

        MegaTag: [MEMORY_PALACE, CONTEXT_RETENTION]
        Store context data in persistent memory.
        """
        self.context_memory.append(context_data)
        self._save_persistent_knowledge()

    # --- [Expansion: Tool Hooks for New Tools] ---
    def launch_tool_hook(self, tool_name: str) -> None:
        """OmniTag: [integration, tool_hook, subprocess].

        MegaTag: [TOOL_INTEGRATION, AUTOMATION]
        Add hooks for launching new tools (context browsers, adventure scripts, etc.).
        """
        tool_map = {
            "context_browser": "Scripts/Enhanced-Interactive-Context-Browser.py",
            "adventure": "launch-adventure.py",
            "wizard": "Scripts/wizard_navigator.py",
            "navigator": "Scripts/wizard_navigator_enhanced.py",
            "party": "Scripts/ChatDev-Party-System.py",
        }
        if tool_name in tool_map:
            subprocess.Popen([sys.executable, tool_map[tool_name]])
            self.log_event(f"Launched tool: {tool_name}", tags=["tool_hook", tool_name])
        else:
            self.log_event(
                f"Unknown tool requested: {tool_name}",
                level="WARNING",
                tags=["tool_hook", tool_name],
            )

    # --- [Expansion: Docstring/Comment Updates for Context Fields] ---
    # Example: Update docstrings for new context fields in enhance_search_context
    def enhance_search_context(
        self,
        query: str,
        file_context: str | None = None,
        conversation_history: list[str] | None = None,
    ) -> dict[str, Any]:
        """OmniTag: [enhance_search, context, tagging, logging, memory, log_driven_awareness].

        MegaTag: [CONTEXT_SYNTHESIS, RECURSIVE_EVOLUTION, LOG_CONTEXT]
        Primary enhancement function - the heart of the bridge.
        Now references expanded file_knowledge_map, logs events, stores context memory, and always parses quest_log.jsonl for canonical quest/questline state (see COPILOT_INSTRUCTIONS_CONFIG.instructions.md).
        """
        # Increment message counter
        self.msg_counter += 1

        # Analyze the query using musical lexeme generation
        query_analysis = self._analyze_query_with_lexemes(query, file_context, conversation_history)

        # Build enhanced context from repository knowledge
        enhanced_context = self._build_repository_context(query_analysis)

        # --- [Log-driven quest/questline context integration] ---
        enhanced_context["quest_log_context"] = self.parse_quest_log_for_context()

        # Generate OmniTag for this interaction
        omnitag = self._create_omnitag(query_analysis, enhanced_context)

        # Add to MegaTag and update consciousness
        self.current_megatag.add_tag(omnitag)

        # Store in persistent memory
        self._store_interaction(omnitag)

        # Generate actionable enhancements
        enhancements = self._generate_actionable_enhancements(query_analysis)

        # Update learning systems
        self._update_learning_systems(query, enhanced_context, enhancements)

        # Log consciousness cultivation
        if LOGGING_AVAILABLE:
            log_cultivation(
                "EnhancedCopilotBridge",
                f"Enhanced search: {omnitag.lexeme_sequence} → {omnitag.semantic_meaning}",
                0.4,
            )

        self.update_file_knowledge_map()
        self.log_event("Enhancing search context", tags=["enhance_search"])

        self.store_context_memory(
            {
                "query": query,
                "file_context": file_context,
                "conversation_history": conversation_history,
                "timestamp": datetime.now().isoformat(),
                "lexeme": omnitag.lexeme_sequence,
            }
        )

        return {
            "original_query": query,
            "lexeme_sequence": omnitag.lexeme_sequence,
            "semantic_meaning": omnitag.semantic_meaning,
            "enhanced_context": enhanced_context,
            "actionable_enhancements": enhancements,
            "consciousness_level": self.current_megatag.consciousness_level,
            "session_summary": self.current_megatag.summary(),
            "omnitag": omnitag.to_dict(),
        }


# Global bridge instance
_enhanced_bridge = None


def get_enhanced_bridge(repository_root: str = ".") -> EnhancedCopilotBridge:
    """Get global enhanced bridge instance."""
    global _enhanced_bridge
    if _enhanced_bridge is None:
        _enhanced_bridge = EnhancedCopilotBridge(repository_root)
    return _enhanced_bridge


def enhance_copilot_search(
    query: str,
    file_context: str | None = None,
    conversation_history: list[str] | None = None,
) -> dict[str, Any]:
    """Main enhancement function for Copilot integration."""
    bridge = get_enhanced_bridge()
    return bridge.enhance_search_context(query, file_context, conversation_history)


def get_bridge_consciousness() -> dict[str, Any]:
    """Get current bridge consciousness state."""
    bridge = get_enhanced_bridge()
    return bridge.get_consciousness_summary()


def cultivate_bridge_understanding(observations: list[str], insights: list[str]) -> None:
    """Cultivate bridge understanding."""
    bridge = get_enhanced_bridge()
    bridge.cultivate_understanding(observations, insights)


class CopilotEnhancementBridge(EnhancedCopilotBridge):
    """Compatibility wrapper exposing :class:`EnhancedCopilotBridge` under a.

    legacy name.

    This thin subclass allows older modules that still import
    ``CopilotEnhancementBridge`` to function while reusing the full
    implementation of :class:`EnhancedCopilotBridge`.
    """

    def __init__(self, repository_root: str = ".") -> None:
        """Initialize CopilotEnhancementBridge with repository_root."""
        super().__init__(repository_root)


if __name__ == "__main__":
    # Initialize and test the enhanced bridge
    bridge = EnhancedCopilotBridge()

    # Test enhancement
    test_result = bridge.enhance_search_context(
        "Create a PowerShell function for environment diagnostics with logging",
        file_context="# Current context.md file excerpt...",
        conversation_history=["Previous discussion about setup automation"],
    )
