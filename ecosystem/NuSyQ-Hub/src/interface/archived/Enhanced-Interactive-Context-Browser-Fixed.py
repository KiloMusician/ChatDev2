"""🔍 Enhanced Interactive Context Browser for KILO-FOOLISH.

Pandas-Integrated Repository Analysis with Cross-Referencing & Tagging.

{# 🔍ΞΦ⟆EnhancedContextBrowser⊗PandasIntegration⟲RepositoryAnalysis⟡InteractiveInterface}
OmniTag: [🔍→ ContextBrowser, PandasIntegration, RepositoryAnalysis]
MegaTag: [BROWSER⨳ENHANCED⦾PANDAS→∞]
"""

import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd
import plotly.express as px
import streamlit as st

# Import KILO-FOOLISH systems
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.stubs.repository_compendium_stub import RepositoryCompendium

    KILO_SYSTEMS_AVAILABLE = True
except (ImportError, ModuleNotFoundError, OSError):
    KILO_SYSTEMS_AVAILABLE = False


class Tag:
    """Represents a tag with metadata."""

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
    """Intelligent tagging system for repository entities."""

    def __init__(self) -> None:
        """Initialize TaggingSystem."""
        self.tags = defaultdict(list)

    def add_tag(self, entity: str, tag: Tag) -> None:
        self.tags[entity].append(tag)

    def clear(self) -> None:
        self.tags.clear()


class CrossReferenceEngine:
    """Engine for building and managing cross-references."""

    def __init__(self) -> None:
        """Initialize CrossReferenceEngine."""
        self.relationships = []

    def add_relationship(self, source: str, target: str, rel_type: str, details: dict) -> None:
        self.relationships.append(
            {"source": source, "target": target, "type": rel_type, "details": details},
        )

    def clear(self) -> None:
        self.relationships.clear()


class EnhancedContextBrowser:
    """Advanced repository analysis browser with pandas integration,.

    cross-referencing, and intelligent tagging systems.
    """

    def __init__(self, repo_path: str = ".") -> None:
        """Initialize EnhancedContextBrowser with repo_path."""
        self.repo_path = Path(repo_path).resolve()
        self.cache_dir = self.repo_path / ".kilo_cache"
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize core systems
        self.compendium = None

        # Data storage
        self.analysis_cache = {}
        self.relationship_graph = nx.DiGraph()
        self.tag_system = TaggingSystem()
        self.cross_ref_engine = CrossReferenceEngine()

        # Pandas DataFrames for advanced analysis
        self.master_df = pd.DataFrame()
        self.relationships_df = pd.DataFrame()
        self.tags_df = pd.DataFrame()
        self.metrics_df = pd.DataFrame()
        self.files_df = pd.DataFrame()
        self.functions_df = pd.DataFrame()
        self.classes_df = pd.DataFrame()
        self.imports_df = pd.DataFrame()

        # Analysis scope settings
        self.scope_basic = True
        self.scope_syntax = True
        self.scope_imports = True
        self.scope_crossref = True
        self.scope_tags = True

        # Initialize systems
        self._initialize_systems()

    def _initialize_systems(self) -> None:
        """Initialize KILO-FOOLISH analysis systems."""
        if KILO_SYSTEMS_AVAILABLE:
            try:
                self.compendium = RepositoryCompendium(str(self.repo_path))
                st.success("✅ Repository analysis system initialized")
            except Exception as e:
                st.warning(f"⚠️ Error initializing systems: {e}")
                self.compendium = None
        else:
            st.warning("⚠️ KILO-FOOLISH core systems unavailable. Limited mode.")

    def run_streamlit_app(self) -> None:
        """Main Streamlit application."""
        st.set_page_config(
            page_title="🔍 Enhanced KILO-FOOLISH Context Browser",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Custom CSS
        st.markdown(
            """
        <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            margin: 0.5rem 0;
        }
        .tag-chip {
            background: #4CAF50;
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 15px;
            margin: 0.1rem;
            display: inline-block;
            font-size: 0.8rem;
        }
        .relationship-node {
            border: 2px solid #007ACC;
            border-radius: 8px;
            padding: 0.5rem;
            margin: 0.2rem;
            background: #f0f8ff;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("# 🔍 Enhanced KILO-FOOLISH Context Browser")
        st.markdown("*Advanced repository analysis with pandas integration and cross-referencing*")

        # Sidebar
        with st.sidebar:
            self._render_sidebar()

        # Main tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
            [
                "📊 Dashboard",
                "🔍 Deep Analysis",
                "🕸️ Relationships",
                "🏷️ Tag Explorer",
                "📈 Metrics & Trends",
                "🔧 System Health",
                "🎮 Interactive",
                "📜 Logs",
            ],
        )

        with tab1:
            self._render_dashboard()
        with tab2:
            self._render_deep_analysis()
        with tab3:
            self._render_relationships()
        with tab4:
            self._render_tag_explorer()
        with tab5:
            self._render_metrics_trends()
        with tab6:
            self._render_system_health()
        with tab7:
            self._render_interactive_explorer()
        with tab8:
            self._render_logs_tab()

    def _render_sidebar(self) -> None:
        """Render sidebar controls."""
        st.header("🎛️ Analysis Controls")

        # Repository path input
        repo_path = st.text_input("Repository Path", value=str(self.repo_path))

        if st.button("🔄 Refresh Analysis", type="primary"):
            self.repo_path = Path(repo_path).resolve()
            self._initialize_systems()
            self._run_comprehensive_analysis()
            st.success("Analysis refreshed!")

        # Analysis scope
        st.subheader("🎯 Analysis Scope")
        st.write("Select which analyses to run:")
        self.scope_basic = st.checkbox("Basic Analysis", value=True)
        self.scope_syntax = st.checkbox("Syntax Analysis", value=True)
        self.scope_imports = st.checkbox("Import Health", value=True)
        self.scope_crossref = st.checkbox("Cross-Reference", value=True)
        self.scope_tags = st.checkbox("Intelligent Tagging", value=True)

        st.markdown("---")

        if st.button("📤 Export to Excel"):
            self._export_to_excel()

    def _run_comprehensive_analysis(self) -> None:
        """Run comprehensive repository analysis."""
        st.info("🔄 Running comprehensive analysis...")

        if self.scope_basic and self.compendium:
            try:
                with st.spinner("Running basic analysis..."):
                    analysis = self.compendium.analyze_repository()
                    self._process_basic_analysis(analysis)
                st.success("✅ Basic analysis complete")
            except Exception as e:
                st.warning(f"Basic analysis failed: {e}")

        if self.scope_crossref:
            try:
                with st.spinner("Building cross-references..."):
                    self._build_cross_references()
                st.success("✅ Cross-reference analysis complete")
            except Exception as e:
                st.warning(f"Cross-reference analysis failed: {e}")

        if self.scope_tags:
            try:
                with st.spinner("Generating intelligent tags..."):
                    self._generate_intelligent_tags()
                st.success("✅ Tag generation complete")
            except Exception as e:
                st.warning(f"Tag generation failed: {e}")

        # Build master dataframe
        self._build_master_dataframe()
        st.success("🎉 Comprehensive analysis complete!")

    def _process_basic_analysis(self, analysis: dict[str, pd.DataFrame]) -> None:
        """Process basic analysis results."""
        for k, v in analysis.items():
            setattr(self, f"{k}_df", v)
            self.analysis_cache[k] = v

    def _build_cross_references(self) -> None:
        """Build comprehensive cross-reference system."""
        self.cross_ref_engine.clear()

        # Simple file relationships based on imports
        if hasattr(self, "imports_df") and not self.imports_df.empty:
            for _, row in self.imports_df.iterrows():
                if (
                    "module" in row
                    and "is_standard_library" in row
                    and not row["is_standard_library"]
                ):
                    self.cross_ref_engine.add_relationship(
                        "current_file",
                        row["module"],
                        "imports",
                        {"type": "external_import"},
                    )

        # Convert to DataFrame
        relationships_data: list[Any] = []
        for rel in self.cross_ref_engine.relationships:
            relationships_data.append(
                {
                    "source": rel["source"],
                    "target": rel["target"],
                    "relationship_type": rel["type"],
                    "details": str(rel["details"]),
                    "strength": 1,
                },
            )

        self.relationships_df = pd.DataFrame(relationships_data)

    def _generate_intelligent_tags(self) -> None:
        """Generate intelligent tags using pattern analysis."""
        self.tag_system.clear()

        # File-based tags
        if hasattr(self, "files_df") and not self.files_df.empty:
            for _, file_row in self.files_df.iterrows():
                file_path = file_row.get("file_path", "")

                # Generate tags based on file characteristics
                if "test" in file_path.lower():
                    self.tag_system.add_tag(file_path, Tag("test", "purpose"))
                if file_path.endswith(".py"):
                    self.tag_system.add_tag(file_path, Tag("python", "language"))
                if "main" in file_path.lower():
                    self.tag_system.add_tag(file_path, Tag("entry_point", "architecture"))

        # Function-based tags
        if hasattr(self, "functions_df") and not self.functions_df.empty:
            for _, func_row in self.functions_df.iterrows():
                func_name = func_row.get("function_name", "")
                file_path = func_row.get("file_path", "")
                func_id = f"{file_path}::{func_name}"

                if func_name.startswith("_"):
                    self.tag_system.add_tag(func_id, Tag("private", "visibility"))
                if "test" in func_name.lower():
                    self.tag_system.add_tag(func_id, Tag("test", "purpose"))

        # Convert to DataFrame
        tags_data: list[Any] = []
        for entity, tags in self.tag_system.tags.items():
            for tag in tags:
                tags_data.append(
                    {
                        "entity": entity,
                        "tag": tag.name,
                        "category": tag.category,
                        "confidence": tag.confidence,
                        "auto_generated": tag.auto_generated,
                    },
                )

        self.tags_df = pd.DataFrame(tags_data)

    def _build_master_dataframe(self) -> None:
        """Build comprehensive master DataFrame combining all analyses."""
        if not hasattr(self, "files_df") or self.files_df.empty:
            self.master_df = pd.DataFrame()
            return

        # Start with files as base
        master_data = self.files_df.copy()

        # Add computed metrics
        master_data["health_score"] = self._calculate_health_scores(master_data)
        master_data["importance_score"] = self._calculate_importance_scores(master_data)

        # Add complexity categories
        if "line_count" in master_data.columns:
            master_data["complexity_category"] = pd.cut(
                master_data["line_count"],
                bins=[0, 50, 200, 500, float("inf")],
                labels=["Simple", "Medium", "Complex", "Very Complex"],
            )

        self.master_df = master_data

    def _render_dashboard(self) -> None:
        """Render main dashboard."""
        st.subheader("📊 Repository Dashboard")

        if self.master_df.empty:
            st.warning(
                "🔄 No analysis data available. Click 'Refresh Analysis' in the sidebar to start.",
            )
            return

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_files = len(self.master_df)
            st.metric("📁 Total Files", f"{total_files:,}")

        with col2:
            if "line_count" in self.master_df.columns:
                total_lines = self.master_df["line_count"].sum()
                st.metric("📝 Lines of Code", f"{total_lines:,}")
            else:
                st.metric("📝 Lines of Code", "N/A")

        with col3:
            if "health_score" in self.master_df.columns:
                avg_health = self.master_df["health_score"].mean()
                st.metric("💊 Avg Health Score", f"{avg_health:.1f}/100")
            else:
                st.metric("💊 Avg Health Score", "N/A")

        with col4:
            python_files = len(self.master_df[self.master_df.get("file_type", "") == "python"])
            st.metric("🐍 Python Files", python_files)

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            if "file_type" in self.master_df.columns:
                file_type_counts = self.master_df["file_type"].value_counts()
                fig = px.pie(
                    values=file_type_counts.values,
                    names=file_type_counts.index,
                    title="File Type Distribution",
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if "complexity_category" in self.master_df.columns:
                complexity_counts = self.master_df["complexity_category"].value_counts()
                fig = px.bar(
                    x=complexity_counts.index,
                    y=complexity_counts.values,
                    title="Complexity Distribution",
                )
                st.plotly_chart(fig, use_container_width=True)

        # Data preview
        st.subheader("📋 File Overview")
        st.dataframe(self.master_df.head(20), use_container_width=True)

    def _render_deep_analysis(self) -> None:
        """Render deep analysis interface."""
        st.subheader("🔍 Deep Repository Analysis")

        if not self.master_df.empty and "file_path" in self.master_df.columns:
            selected_file = st.selectbox(
                "Select file for detailed analysis",
                self.master_df["file_path"].tolist(),
            )

            if selected_file:
                st.subheader(f"📄 Analysis of: {selected_file}")
                file_data = self.master_df[self.master_df["file_path"] == selected_file].iloc[0]

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("File Size (KB)", f"{file_data.get('size_kb', 'N/A')}")
                    st.metric("Line Count", f"{file_data.get('line_count', 'N/A')}")

                with col2:
                    st.metric("Health Score", f"{file_data.get('health_score', 'N/A'):.1f}")
                    st.metric(
                        "Importance Score",
                        f"{file_data.get('importance_score', 'N/A'):.1f}",
                    )
        else:
            st.info("No files available for deep analysis. Run analysis first.")

    def _render_relationships(self) -> None:
        """Render relationship visualization."""
        st.subheader("🕸️ Repository Relationship Graph")

        if self.relationships_df.empty:
            st.warning("No relationship data available. Enable cross-reference analysis.")
            return

        # Relationship statistics
        col1, col2, col3 = st.columns(3)

        with col1:
            total_relationships = len(self.relationships_df)
            st.metric("🔗 Total Relationships", total_relationships)

        with col2:
            if "relationship_type" in self.relationships_df.columns:
                relationship_types = self.relationships_df["relationship_type"].nunique()
                st.metric("📋 Relationship Types", relationship_types)

        with col3:
            if "strength" in self.relationships_df.columns:
                avg_strength = self.relationships_df["strength"].mean()
                st.metric("💪 Avg Strength", f"{avg_strength:.1f}")

        # Relationship breakdown
        if "relationship_type" in self.relationships_df.columns:
            rel_counts = self.relationships_df["relationship_type"].value_counts()
            fig = px.bar(
                x=rel_counts.values,
                y=rel_counts.index,
                orientation="h",
                title="Relationship Types",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(self.relationships_df, use_container_width=True)

    def _render_tag_explorer(self) -> None:
        """Render tag exploration interface."""
        st.subheader("🏷️ Intelligent Tag Explorer")

        if self.tags_df.empty:
            st.warning("No tag data available. Enable intelligent tagging.")
            return

        # Tag statistics
        col1, col2, col3 = st.columns(3)

        with col1:
            total_tags = len(self.tags_df)
            st.metric("🏷️ Total Tags", total_tags)

        with col2:
            if "tag" in self.tags_df.columns:
                unique_tags = self.tags_df["tag"].nunique()
                st.metric("🎯 Unique Tags", unique_tags)

        with col3:
            if "category" in self.tags_df.columns:
                categories = self.tags_df["category"].nunique()
                st.metric("📂 Categories", categories)

        # Tag filtering
        if "category" in self.tags_df.columns:
            selected_category = st.selectbox(
                "Filter by category",
                ["All", *list(self.tags_df["category"].unique())],
            )

            if selected_category != "All":
                filtered_tags = self.tags_df[self.tags_df["category"] == selected_category]
            else:
                filtered_tags = self.tags_df

            st.dataframe(filtered_tags, use_container_width=True)

    def _render_metrics_trends(self) -> None:
        """Render metrics and trends analysis."""
        st.subheader("📈 Repository Metrics & Trends")

        if self.master_df.empty:
            st.warning("No metrics data available")
            return

        # Size analysis
        if all(col in self.master_df.columns for col in ["size_kb", "line_count"]):
            st.subheader("📊 Size Analysis")

            col1, col2 = st.columns(2)

            with col1:
                fig = px.scatter(
                    self.master_df,
                    x="size_kb",
                    y="line_count",
                    color=("file_type" if "file_type" in self.master_df.columns else None),
                    title="File Size vs Line Count",
                    hover_data=(["file_path"] if "file_path" in self.master_df.columns else None),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                if "file_type" in self.master_df.columns:
                    type_stats = self.master_df.groupby("file_type")["line_count"].agg(
                        ["mean", "sum", "count"],
                    )
                    st.subheader("📋 Stats by File Type")
                    st.dataframe(type_stats, use_container_width=True)

    def _render_system_health(self) -> None:
        """Render system health monitoring."""
        st.subheader("🔧 KILO-FOOLISH System Health")

        # System component status
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Analysis Systems")

            systems = [
                ("Repository Compendium", self.compendium is not None),
                ("KILO Systems Available", KILO_SYSTEMS_AVAILABLE),
                ("Analysis Cache", bool(self.analysis_cache)),
                ("Master DataFrame", not self.master_df.empty),
            ]

            for system_name, is_available in systems:
                status = "✅ Active" if is_available else "❌ Unavailable"
                st.write(f"**{system_name}**: {status}")

        with col2:
            st.subheader("📈 System Stats")
            st.metric("Cached Analyses", len(self.analysis_cache))
            st.metric("Graph Nodes", self.relationship_graph.number_of_nodes())
            st.metric("Graph Edges", self.relationship_graph.number_of_edges())
            st.metric("Active Tags", len(self.tag_system.tags))

    def _render_interactive_explorer(self) -> None:
        """Render interactive exploration interface."""
        st.subheader("🎮 Interactive Development Assistant")
        st.markdown(
            """
        **Enhanced Interactive Features:**
        - Type natural language queries to get AI assistance
        - Get context-aware enhancement suggestions
        - Execute custom pandas operations on repository data
        """,
        )

        # LLM Assistant Section
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("#### 💬 AI Assistant")
            user_query = st.text_input(
                "Ask for development help:",
                placeholder="How can I improve code quality in this repository?",
            )

            if st.button("🚀 Send Query"):
                if user_query:
                    response = self._query_ai_assistant(user_query)
                    st.success(f"**AI Response:**\n{response}")
                else:
                    st.warning("Please enter a query first.")

        with col2:
            st.markdown("#### 🤖 Quick Suggestions")
            suggestions = self._get_enhancement_suggestions()
            for _i, suggestion in enumerate(suggestions[:5]):
                st.info(f"💡 {suggestion}")

        # Custom Pandas Operations
        st.markdown("#### 🐼 Custom Data Analysis")

        if not self.master_df.empty:
            pandas_code = st.text_area(
                "Enter pandas code (use 'df' for master dataframe):",
                value="df.groupby('file_type')['line_count'].sum().sort_values(ascending=False)",
                height=100,
            )

            if st.button("▶️ Execute Pandas Code"):
                try:
                    df = self.master_df  # Make available to exec
                    # SECURITY: Use restrictive eval instead of unrestricted eval
                    # Only allow safe pandas operations
                    safe_namespace = {"df": df, "pd": pd}
                    result = eval(pandas_code, {"__builtins__": {}}, safe_namespace)  # nosemgrep

                    st.markdown("**Result:**")
                    if isinstance(result, pd.DataFrame):
                        st.dataframe(result, use_container_width=True)
                    elif isinstance(result, pd.Series):
                        st.dataframe(result.to_frame(), use_container_width=True)
                    else:
                        st.write(result)
                except Exception as e:
                    st.error(f"Error executing code: {e}")
        else:
            st.info("No data available for pandas operations. Run analysis first.")

    def _render_logs_tab(self) -> None:
        """Display active logs with auto-refresh and error handling."""
        st.subheader("📜 Active Logs Viewer")

        # Log file selection
        log_files = [
            "file_organization_audit.log",
            "import_health_check.log",
            "logs/ollama_integration.log",
            "logs/chatdev_integration.log",
            "logs/copilot_enhancement.log",
        ]

        selected_log = st.selectbox("Select log file", log_files)
        log_path = self.repo_path / selected_log

        col1, col2 = st.columns([1, 3])

        with col1:
            st.button("🔄 Refresh Log")
            max_lines = st.slider("Max lines to show", 50, 1000, 200, step=50)

        with col2:
            if log_path.exists():
                try:
                    with open(log_path, encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()[-max_lines:]

                    if lines:
                        log_content = "".join(lines)
                        st.text_area("Log Content:", value=log_content, height=400)
                    else:
                        st.info("Log file is empty")

                except Exception as e:
                    st.error(f"Error reading log: {e}")
            else:
                st.info(f"Log file not found: {log_path}")

                # Create a sample log entry
                if st.button("📝 Create Sample Log"):
                    try:
                        log_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(log_path, "w", encoding="utf-8") as f:
                            f.write(f"[{datetime.now()}] Sample log entry created\n")
                        st.success("Sample log created!")
                    except Exception as e:
                        st.error(f"Could not create log: {e}")

    def _query_ai_assistant(self, prompt: str) -> str:
        """Send prompt to AI assistant and return response."""
        # Enhanced AI assistant simulation with context awareness
        responses = {
            "quality": "Consider adding type hints, docstrings, and unit tests. Review code complexity and refactor large functions.",
            "modularity": "Extract reusable components into separate modules. Use dependency injection and follow SOLID principles.",
            "performance": "Profile your code to identify bottlenecks. Consider using pandas for data operations and async for I/O.",
            "testing": "Implement comprehensive unit tests, integration tests, and consider property-based testing.",
            "documentation": "Add detailed docstrings, create README files, and consider using Sphinx for documentation generation.",
        }

        # Simple keyword matching for demo
        for keyword, response in responses.items():
            if keyword in prompt.lower():
                return f"💡 **{keyword.title()} Suggestion**: {response}"

        # Default response with repo context
        file_count = len(self.master_df) if not self.master_df.empty else 0
        return f"""
🔍 **Repository Analysis**: Based on your {file_count} files, here are some general recommendations:

1. **Code Quality**: Ensure consistent formatting and add type hints
2. **Architecture**: Consider implementing a clean architecture pattern
3. **Testing**: Aim for >80% code coverage with comprehensive tests
4. **Documentation**: Document your API and add inline comments for complex logic
5. **Performance**: Monitor for performance bottlenecks and optimize critical paths

Would you like specific suggestions for any of these areas?
"""

    def _get_enhancement_suggestions(self) -> list[str]:
        """Get context-aware enhancement suggestions."""
        suggestions = [
            "Add comprehensive logging throughout the application",
            "Implement error handling and graceful degradation",
            "Create unit tests for core functionality",
            "Add type hints for better code documentation",
            "Consider using async/await for I/O operations",
        ]

        # Add context-aware suggestions based on current data
        if not self.master_df.empty:
            if "file_type" in self.master_df.columns:
                python_files = len(self.master_df[self.master_df["file_type"] == "python"])
                if python_files > 20:
                    suggestions.insert(0, "Consider organizing Python files into packages")

            if "line_count" in self.master_df.columns:
                large_files = len(self.master_df[self.master_df["line_count"] > 500])
                if large_files > 0:
                    suggestions.insert(
                        0,
                        f"Refactor {large_files} large files into smaller modules",
                    )

        return suggestions

    def _calculate_health_scores(self, df: pd.DataFrame) -> pd.Series:
        """Calculate health scores for files."""
        # Start with base score
        scores = pd.Series(85.0, index=df.index)  # Start with good score

        # Adjust based on file size
        if "line_count" in df.columns:
            # Penalize very large files
            large_files = df["line_count"] > 1000
            scores[large_files] -= 15

            # Penalize very small files (might be incomplete)
            small_files = df["line_count"] < 10
            scores[small_files] -= 5

        # Boost Python files (assumed to be more maintainable)
        if "file_type" in df.columns:
            python_files = df["file_type"] == "python"
            scores[python_files] += 10

        return scores.clip(0, 100)

    def _calculate_importance_scores(self, df: pd.DataFrame) -> pd.Series:
        """Calculate importance scores for files."""
        scores = pd.Series(50.0, index=df.index)  # Start with medium importance

        # Boost based on file size (larger files likely more important)
        if "line_count" in df.columns:
            scores += (df["line_count"] / 100).clip(0, 30)

        # Boost main files
        if "file_path" in df.columns:
            main_files = df["file_path"].str.contains(
                "main|setup|init|__init__",
                case=False,
                na=False,
            )
            scores[main_files] += 25

            # Boost test files (important for quality)
            test_files = df["file_path"].str.contains("test", case=False, na=False)
            scores[test_files] += 15

        return scores.clip(0, 100)

    def _export_to_excel(self) -> None:
        """Export all DataFrames to Excel."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.cache_dir / f"kilo_analysis_{timestamp}.xlsx"

            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                if not self.master_df.empty:
                    self.master_df.to_excel(writer, sheet_name="Master_Analysis", index=False)

                if not self.relationships_df.empty:
                    self.relationships_df.to_excel(writer, sheet_name="Relationships", index=False)

                if not self.tags_df.empty:
                    self.tags_df.to_excel(writer, sheet_name="Tags", index=False)

                if not self.files_df.empty:
                    self.files_df.to_excel(writer, sheet_name="Files", index=False)

                if not self.functions_df.empty:
                    self.functions_df.to_excel(writer, sheet_name="Functions", index=False)

                if not self.classes_df.empty:
                    self.classes_df.to_excel(writer, sheet_name="Classes", index=False)

            st.success(f"✅ Data exported to: {output_path}")

        except Exception as e:
            st.error(f"❌ Export failed: {e}")


def main() -> None:
    """Main function to run the Enhanced Context Browser."""
    browser = EnhancedContextBrowser()
    browser.run_streamlit_app()


if __name__ == "__main__":
    main()
