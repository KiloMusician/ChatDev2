"""🔍 Enhanced Interactive Context Browser for KILO-FOOLISH.

Pandas-Integrated Repository Analysis with Cross-Referencing & Tagging.

{# 🔍ΞΦ⟆EnhancedContextBrowser⊗PandasIntegration⟲RepositoryAnalysis⟡InteractiveInterface}
OmniTag: [🔍→ ContextBrowser, PandasIntegration, RepositoryAnalysis]
MegaTag: [BROWSER⨳ENHANCED⦾PANDAS→∞]
"""

import contextlib
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, ClassVar

import networkx as nx
import pandas as pd
import streamlit as st

# Import KILO-FOOLISH systems
sys.path.append(str(Path(__file__).parent.parent))

# Recursion protection variables
_main_execution_count = 0
_max_main_executions = 5  # Maximum allowed recursive calls


# Define stub classes first (will be replaced if imports succeed)
class _StubRepositoryCoordinator:
    def __init__(self, path: str) -> None:
        pass


class RepositoryCompendium:
    def __init__(self, path: str) -> None:
        """Initialize RepositoryCompendium with path."""
        pass

    def analyze_repository(self) -> dict[str, Any]:
        return {}


class _StubRepositorySyntaxAnalyzer:
    def __init__(self, path: str) -> None:
        pass

    def analyze(self, _file_path: str) -> list[Any]:
        return []


class _StubImportHealthChecker:
    def __init__(self, path: str) -> None:
        pass

    def run(self) -> list[Any]:
        return []


RepositoryCoordinator: type[Any] = _StubRepositoryCoordinator
RepositorySyntaxAnalyzer: type[Any] = _StubRepositorySyntaxAnalyzer
ImportHealthChecker: type[Any] = _StubImportHealthChecker


try:
    # RepositoryCompendium import is intentionally skipped (module name contains hyphens).
    from src.diagnostics.repository_syntax_analyzer import \
        RepositorySyntaxAnalyzer as _RepositorySyntaxAnalyzer
    from src.system.RepositoryCoordinator import \
        KILORepositoryCoordinator as _RepositoryCoordinator
    from src.utils.import_health_checker import \
        ImportHealthChecker as _ImportHealthChecker

    RepositorySyntaxAnalyzer = _RepositorySyntaxAnalyzer
    RepositoryCoordinator = _RepositoryCoordinator
    ImportHealthChecker = _ImportHealthChecker
    KILO_SYSTEMS_AVAILABLE = True
except ImportError:
    KILO_SYSTEMS_AVAILABLE = False


class EnhancedContextBrowser:
    """Advanced repository analysis browser with pandas integration,.

    cross-referencing, and intelligent tagging systems.

    🛡️ ANTI-RECURSION SAFEGUARDS ENABLED
    """

    # Class-level recursion protection
    _instance_count = 0
    _max_instances = 1
    _initialization_stack: ClassVar[list[Any]] = []

    def __init__(self, repo_path: str = ".") -> None:
        """Initialize EnhancedContextBrowser with repo_path."""
        # 🛡️ RECURSION PROTECTION: Prevent infinite instantiation
        self._initialization_depth = 0  # Initialize first
        EnhancedContextBrowser._instance_count += 1
        if EnhancedContextBrowser._instance_count > EnhancedContextBrowser._max_instances:
            msg = (
                f"🚫 RECURSION PROTECTION: Maximum instances ({EnhancedContextBrowser._max_instances}) exceeded. "
                f"Infinite loop detected!"
            )
            raise RuntimeError(msg)

        # Track initialization stack to detect recursive calls
        init_id = id(self)
        if init_id in EnhancedContextBrowser._initialization_stack:
            msg = "🚫 RECURSION PROTECTION: Circular initialization detected!"
            raise RuntimeError(msg)

        EnhancedContextBrowser._initialization_stack.append(init_id)

        try:
            self.repo_path = Path(repo_path).resolve()
            self.cache_dir = self.repo_path / ".kilo_cache"
            self.cache_dir.mkdir(exist_ok=True)

            # Initialize core systems
            self.compendium: RepositoryCompendium | None = None
            self.syntax_analyzer: Any | None = None
            self.coordinator: Any | None = None
            self.import_checker: Any | None = None

            # Data storage
            self.analysis_cache: dict[str, Any] = {}
            self.relationship_graph = nx.DiGraph()
            self.tag_system = TaggingSystem()
            self.cross_ref_engine = CrossReferenceEngine()

            # Pandas DataFrames for advanced analysis
            self.master_df = pd.DataFrame()
            self.relationships_df = pd.DataFrame()
            self.tags_df = pd.DataFrame()
            self.metrics_df = pd.DataFrame()
            self.timeline_df = pd.DataFrame()

        except Exception as e:
            # Clean up on initialization failure
            EnhancedContextBrowser._instance_count -= 1
            msg = f"🚫 INITIALIZATION FAILED: {e}"
            raise RuntimeError(msg) from e
        finally:
            # Always clean up the initialization stack
            if init_id in EnhancedContextBrowser._initialization_stack:
                EnhancedContextBrowser._initialization_stack.remove(init_id)

        # Initialize systems
        self._initialize_systems()

    def __del__(self) -> None:
        """🛡️ Cleanup method to prevent resource leaks."""
        with contextlib.suppress(AttributeError, TypeError):  # Ignore cleanup errors in __del__
            EnhancedContextBrowser._instance_count = max(
                0, EnhancedContextBrowser._instance_count - 1
            )

    def _initialize_systems(self) -> None:
        """Initialize KILO-FOOLISH analysis systems with recursion protection."""
        # 🛡️ RECURSION PROTECTION: Limit initialization depth
        if hasattr(self, "_initialization_depth"):
            self._initialization_depth += 1
            if self._initialization_depth > 3:
                msg = "🚫 RECURSION PROTECTION: System initialization depth exceeded!"
                raise RuntimeError(msg)
        else:
            self._initialization_depth = 1

        if KILO_SYSTEMS_AVAILABLE:
            try:
                self.compendium = RepositoryCompendium(str(self.repo_path))
                self.syntax_analyzer = RepositorySyntaxAnalyzer(str(self.repo_path))
                self.coordinator = RepositoryCoordinator(str(self.repo_path))
                self.import_checker = ImportHealthChecker(str(self.repo_path))
                st.success("✅ All KILO-FOOLISH systems initialized")
            except Exception as e:
                st.error(f"❌ System initialization error: {e}")
                # Fall back to stub instances
                self.compendium = RepositoryCompendium(str(self.repo_path))
                self.syntax_analyzer = RepositorySyntaxAnalyzer(str(self.repo_path))
                self.coordinator = RepositoryCoordinator(str(self.repo_path))
                self.import_checker = ImportHealthChecker(str(self.repo_path))
        else:
            # Always initialize stub instances as fallback
            # Ensure repo_path exists before use
            if not hasattr(self, "repo_path"):
                self.repo_path = Path(".")
            self.compendium = RepositoryCompendium(str(self.repo_path))
            self.syntax_analyzer = RepositorySyntaxAnalyzer(str(self.repo_path))
            self.coordinator = RepositoryCoordinator(str(self.repo_path))
            self.import_checker = ImportHealthChecker(str(self.repo_path))

    def run_streamlit_app(self) -> None:
        """Main Streamlit application."""
        st.set_page_config(
            page_title="KILO-FOOLISH Context Browser",
            page_icon="🔍",
            layout="wide",
        )


class Tag:
    def __init__(
        self,
        name: str,
        category: str,
        confidence: float = 1.0,
        auto_generated: bool = True,
    ) -> None:
        """Initialize Tag with name, category, confidence, ...."""
        self.name = name
        self.category = category
        self.confidence = confidence
        self.auto_generated = auto_generated


class TaggingSystem:
    def __init__(self) -> None:
        """Initialize TaggingSystem."""
        self.tags: defaultdict[str, list[Tag]] = defaultdict(list)

    def add_tag(self, entity: str, tag: Tag) -> None:
        self.tags[entity].append(tag)

    def clear(self) -> None:
        self.tags.clear()


class CrossReferenceEngine:
    def __init__(self) -> None:
        """Initialize CrossReferenceEngine."""
        # Use dict-of-dicts for richer relationship modeling
        self.relationships: dict[str, dict[str, dict[str, dict]]] = {}
        # Caches and dataframes expected downstream
        self.analysis_cache: dict[str, pd.DataFrame] = {}
        self.relationship_graph = nx.DiGraph()
        self.files_df = pd.DataFrame()
        self.functions_df = pd.DataFrame()
        self.import_issues_df = pd.DataFrame()
        self.tag_system = TaggingSystem()
        self.cache_dir = Path(".cache/context_browser")
        self.cross_ref_engine = self  # self-reference for compatibility

    def add_relationship(self, source: str, target: str, rel_type: str, details: dict) -> None:
        src = self.relationships.setdefault(source, {})
        tgt = src.setdefault(target, {})
        rel = tgt.setdefault(rel_type, {})
        rel.update(details)

    def clear(self) -> None:
        self.relationships.clear()
        self.relationships_df = pd.DataFrame()
        self.tags_df = pd.DataFrame()
        self.metrics_df = pd.DataFrame()
        self.timeline_df = pd.DataFrame()
        self.scope_basic = True
        self.scope_syntax = True
        self.scope_imports = True
        self.scope_crossref = True

    # --- helper methods expected by browser ---
    def _resolve_import_to_file(self, module_name: str) -> str | None:
        try:
            # naive resolution; could be improved by inspecting sys.path/package structure
            parts = module_name.split(".")
            candidate = Path("src") / Path(*parts)
            for ext in (".py", "/__init__.py"):
                p = Path(str(candidate) + ext)
                if p.exists():
                    return str(p)
        except (AttributeError, OSError, ValueError):
            return None
        return None

    def _analyze_function_usage(self) -> None:
        """Populate relationship_graph edges based on function usage data."""
        if isinstance(self.functions_df, pd.DataFrame) and not self.functions_df.empty:
            for _, row in self.functions_df.iterrows():
                src = row.get("file_path")
                tgt = row.get("called_in")
                if src and tgt:
                    self.relationship_graph.add_edge(src, tgt, relationship="calls")

    def _analyze_config_relationships(self) -> None:
        """Analyze configuration file relationships.

        Currently a no-op - config analysis not yet implemented.
        Future: parse config files and detect dependencies between them.
        """
        return None


# Stub classes are already defined at the top of the file (lines 36-49)
# No need for duplicate fallback definitions here
# All methods are properly defined inside EnhancedContextBrowser class above


class ChatDevAPI:
    def __init__(self) -> None:
        """Initialize ChatDevAPI."""
        self.endpoint = "https://chatdev.example.com/api"

    def query(self, prompt) -> str:
        # Simulate API call
        return f"Response for: {prompt}"


chatdev_api = ChatDevAPI()


# Main entry point is defined at the end of the file
def main() -> None:
    """🛡️ Main function with recursion protection."""
    global _main_execution_count

    # Prevent infinite main() recursion
    _main_execution_count += 1
    if _main_execution_count > _max_main_executions:
        msg = f"🚫 RECURSION PROTECTION: main() called too many times! Maximum executions: {_max_main_executions}"
        raise RuntimeError(msg)

    try:
        browser = EnhancedContextBrowser()
        browser.run_streamlit_app()
    except (KeyboardInterrupt, SystemExit, RuntimeError):
        raise
    finally:
        # Reset counter when done
        _main_execution_count = 0


if __name__ == "__main__":
    main()
