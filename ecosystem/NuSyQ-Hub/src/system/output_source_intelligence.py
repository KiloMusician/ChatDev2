#!/usr/bin/env python3
"""Output Source Intelligence - VS Code Extension Output Router.

Maps 100+ VS Code extension output channels to appropriate NuSyQ terminals.
Provides intelligent routing, filtering, and aggregation of extension outputs.

🏷️ OmniTag: output_routing|vscode_extensions|intelligent_aggregation
🏷️ MegaTag: quantum_output_nexus|extension_intelligence|adaptive_routing
🏷️ RSHTS: ⟡ Master router for 100+ VS Code extension outputs → 23 terminals ⟡

Output Source Categories:
1. Language Servers (20+) - Python, C#, TypeScript, JSON, YAML, etc.
2. AI/ML Tools (15+) - Copilot, Claude, Cody, Windsurf, AI Toolkit, etc.
3. DevOps/Infra (15+) - Docker, Kubernetes, Helm, Git, GitHub Actions, etc.
4. Code Quality (12+) - Ruff, Pylint, Mypy, SonarQube, Semgrep, etc.
5. Database/Data (8+) - Database Client, SQLTools, rainbow_csv, coverage-gutters
6. Testing (6+) - Python Test Adapter, Test Explorer, ViTest, Jupyter
7. VS Code Core (10+) - Tasks, Terminal, Extension Host, Settings Sync, etc.
8. Utilities (20+) - Git Graph, GitLens, Peacock, VersionLens, etc.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.system.terminal_intelligence_orchestrator import get_orchestrator

logger = logging.getLogger(__name__)


class OutputSourceCategory(Enum):
    """Categories for VS Code extension outputs."""

    LANGUAGE_SERVER = "language_server"
    AI_ML_TOOL = "ai_ml_tool"
    DEVOPS_INFRA = "devops_infra"
    CODE_QUALITY = "code_quality"
    DATABASE_DATA = "database_data"
    TESTING = "testing"
    VSCODE_CORE = "vscode_core"
    UTILITY = "utility"
    AUTHENTICATION = "authentication"
    FORMATTING = "formatting"


@dataclass
class OutputSourceConfig:
    """Configuration for a single VS Code output source."""

    name: str
    category: OutputSourceCategory
    target_terminal: str  # Which NuSyQ terminal to route to
    description: str
    priority: int = 1  # 1-5: Low → Critical
    filter_patterns: list[str] = field(default_factory=list)
    aggregation_strategy: str = "append"  # append | summarize | alert_only


class OutputSourceIntelligence:
    """Routes 100+ VS Code extension outputs to appropriate terminals."""

    def __init__(self):
        """Initialize OutputSourceIntelligence."""
        self.logger = logging.getLogger(__name__)
        self.output_sources: dict[str, OutputSourceConfig] = {}
        self._initialize_output_sources()
        self.orchestrator: Any | None = None  # Type hint for orchestrator

    async def init(self):
        """Initialize connection to terminal orchestrator (async)."""
        if self.orchestrator is None:
            # get_orchestrator is synchronous; call directly
            self.orchestrator = get_orchestrator()

    def _build_output_sources(self) -> list[OutputSourceConfig]:
        """Define output source metadata used by routing."""
        # ========== AI/ML TOOLS ==========
        ai_ml_sources = [
            OutputSourceConfig(
                name="GitHub Copilot chat",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="Copilot",
                description="GitHub Copilot chat interface output",
                priority=4,
                filter_patterns=["suggestion", "completion", "chat"],
            ),
            OutputSourceConfig(
                name="GitHub Copilot Log (Code References)",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="Copilot",
                description="Copilot code reference logging",
                priority=3,
            ),
            OutputSourceConfig(
                name="Claude VSCode",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="Claude",
                description="Claude AI extension output",
                priority=5,
            ),
            OutputSourceConfig(
                name="Codex",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="Codex",
                description="OpenAI Codex extension output",
                priority=4,
            ),
            OutputSourceConfig(
                name="Cody by SourceGraph",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="AI Council",
                description="Cody AI assistant output",
                priority=4,
            ),
            OutputSourceConfig(
                name="Cody: Network",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="AI Council",
                description="Cody network activity",
                priority=2,
            ),
            OutputSourceConfig(
                name="AI Toolkit",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="Agents",
                description="Microsoft AI Toolkit output",
                priority=4,
            ),
            OutputSourceConfig(
                name="AI Toolkit Tracing",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="Agents",
                description="AI Toolkit trace output",
                priority=3,
            ),
            OutputSourceConfig(
                name="Windsurf",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="Agents",
                description="Windsurf AI coding assistant",
                priority=4,
            ),
            OutputSourceConfig(
                name="Roo-Code",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="Agents",
                description="Roo-Code AI assistant",
                priority=3,
            ),
            OutputSourceConfig(
                name="Kilo-Code",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="Agents",
                description="Kilo-Code AI features",
                priority=3,
            ),
            # ========== SIMULATEDVERSE ECOSYSTEM ==========
            OutputSourceConfig(
                name="SimulatedVerse",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="SimulatedVerse",
                description="SimulatedVerse consciousness simulation engine",
                priority=5,
                filter_patterns=["Temple", "PU Queue", "Agent", "Consciousness"],
            ),
            OutputSourceConfig(
                name="Culture Ship",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="Culture Ship",
                description="Culture Ship strategic advisor and guardian ethics",
                priority=5,
                filter_patterns=["Strategic", "Guardian", "Ethics", "Decision"],
            ),
            OutputSourceConfig(
                name="ChatDev",
                category=OutputSourceCategory.AI_ML_TOOL,
                target_terminal="ChatDev",
                description="ChatDev multi-agent software company (CEO→CTO→Programmer→Tester)",
                priority=5,
                filter_patterns=["CEO", "CTO", "Designer", "Programmer", "Tester", "Reviewer"],
            ),
            OutputSourceConfig(
                name="Node.js",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="System",
                description="Node.js runtime output",
                priority=3,
                filter_patterns=["listening", "server", "port"],
            ),
            OutputSourceConfig(
                name="Express",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="System",
                description="Express web framework output",
                priority=3,
                filter_patterns=["GET", "POST", "middleware", "route"],
            ),
        ]

        # ========== LANGUAGE SERVERS ==========
        language_server_sources = [
            OutputSourceConfig(
                name="Python",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="System",
                description="Python language server",
                priority=5,
                filter_patterns=["error", "warning"],
            ),
            OutputSourceConfig(
                name="Python Language Service",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="System",
                description="Python IntelliSense service",
                priority=4,
            ),
            OutputSourceConfig(
                name="C#",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="System",
                description="C# language server",
                priority=4,
            ),
            OutputSourceConfig(
                name="C# LSP Trace Logs",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="System",
                description="C# LSP trace logs",
                priority=2,
            ),
            OutputSourceConfig(
                name="TypeScript",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="System",
                description="TypeScript language server",
                priority=4,
            ),
            OutputSourceConfig(
                name="JSON Language Server",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="System",
                description="JSON IntelliSense",
                priority=3,
            ),
            OutputSourceConfig(
                name="YAML Support",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="System",
                description="YAML language support",
                priority=3,
            ),
            OutputSourceConfig(
                name="Even Better TOML",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="System",
                description="TOML language support",
                priority=3,
            ),
            OutputSourceConfig(
                name="Even Better TOML LSP",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="System",
                description="TOML LSP server",
                priority=2,
            ),
            OutputSourceConfig(
                name="Razor Log",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="System",
                description="Razor language server logs",
                priority=2,
            ),
            OutputSourceConfig(
                name="Markdown",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="System",
                description="Markdown language features",
                priority=3,
            ),
            OutputSourceConfig(
                name="Jupyter",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="Tests",
                description="Jupyter notebook support",
                priority=4,
            ),
            OutputSourceConfig(
                name="Jupyter Server Console",
                category=OutputSourceCategory.LANGUAGE_SERVER,
                target_terminal="Tests",
                description="Jupyter server output",
                priority=3,
            ),
        ]

        # ========== CODE QUALITY ==========
        code_quality_sources = [
            OutputSourceConfig(
                name="Ruff",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Ruff Python linter",
                priority=5,
                filter_patterns=["error", "warning"],
                aggregation_strategy="alert_only",
            ),
            OutputSourceConfig(
                name="Ruff Language Server",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Ruff LSP server",
                priority=4,
            ),
            OutputSourceConfig(
                name="Pylint",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Pylint Python linter",
                priority=4,
                filter_patterns=["error", "warning"],
            ),
            OutputSourceConfig(
                name="Mypy Type Checker",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Mypy static type checker",
                priority=4,
                filter_patterns=["error"],
            ),
            OutputSourceConfig(
                name="Flake8",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Flake8 Python linter",
                priority=3,
            ),
            OutputSourceConfig(
                name="SonarQube for IDE",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="SonarQube code quality analysis",
                priority=5,
                aggregation_strategy="summarize",
            ),
            OutputSourceConfig(
                name="Semgrep (Client)",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Semgrep security scanner client",
                priority=5,
            ),
            OutputSourceConfig(
                name="Semgrep (Server)",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Semgrep server output",
                priority=4,
            ),
            OutputSourceConfig(
                name="ESLint",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="ESLint JavaScript linter",
                priority=4,
            ),
            OutputSourceConfig(
                name="Biome",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Biome code formatter/linter",
                priority=3,
            ),
            OutputSourceConfig(
                name="Biome (NuSyQ-Hub)",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Biome for NuSyQ-Hub workspace",
                priority=3,
            ),
            OutputSourceConfig(
                name="Biome (NuSyQ)",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Biome for NuSyQ workspace",
                priority=3,
            ),
            OutputSourceConfig(
                name="Biome (SimulatedVerse)",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Biome for SimulatedVerse workspace",
                priority=3,
            ),
            OutputSourceConfig(
                name="Biome (Prime_anchor)",
                category=OutputSourceCategory.CODE_QUALITY,
                target_terminal="Errors",
                description="Biome for Prime_anchor workspace",
                priority=3,
            ),
        ]

        # ========== DEVOPS/INFRASTRUCTURE ==========
        devops_sources = [
            OutputSourceConfig(
                name="Docker Labs AI",
                category=OutputSourceCategory.DEVOPS_INFRA,
                target_terminal="System",
                description="Docker AI features",
                priority=3,
            ),
            OutputSourceConfig(
                name="Docker LSP (Markdown)",
                category=OutputSourceCategory.DEVOPS_INFRA,
                target_terminal="System",
                description="Docker LSP for markdown",
                priority=2,
            ),
            OutputSourceConfig(
                name="Kubernetes",
                category=OutputSourceCategory.DEVOPS_INFRA,
                target_terminal="System",
                description="Kubernetes extension output",
                priority=4,
            ),
            OutputSourceConfig(
                name="Helm",
                category=OutputSourceCategory.DEVOPS_INFRA,
                target_terminal="System",
                description="Helm chart support",
                priority=3,
            ),
            OutputSourceConfig(
                name="Git",
                category=OutputSourceCategory.DEVOPS_INFRA,
                target_terminal="Main",
                description="Git SCM output",
                priority=5,
            ),
            OutputSourceConfig(
                name="Git Graph",
                category=OutputSourceCategory.DEVOPS_INFRA,
                target_terminal="Main",
                description="Git Graph visualization",
                priority=3,
            ),
            OutputSourceConfig(
                name="GitHub",
                category=OutputSourceCategory.DEVOPS_INFRA,
                target_terminal="Main",
                description="GitHub integration",
                priority=4,
            ),
            OutputSourceConfig(
                name="GitHub Actions",
                category=OutputSourceCategory.DEVOPS_INFRA,
                target_terminal="Tasks",
                description="GitHub Actions workflow output",
                priority=4,
            ),
            OutputSourceConfig(
                name="GitLens",
                category=OutputSourceCategory.DEVOPS_INFRA,
                target_terminal="Main",
                description="GitLens Git supercharger",
                priority=4,
            ),
            OutputSourceConfig(
                name="GitLens (Git)",
                category=OutputSourceCategory.DEVOPS_INFRA,
                target_terminal="Main",
                description="GitLens Git operations",
                priority=3,
            ),
        ]

        # ========== TESTING ==========
        testing_sources = [
            OutputSourceConfig(
                name="Python Test Adapter Log",
                category=OutputSourceCategory.TESTING,
                target_terminal="Tests",
                description="Python test adapter logs",
                priority=4,
            ),
            OutputSourceConfig(
                name="Test Explorer",
                category=OutputSourceCategory.TESTING,
                target_terminal="Tests",
                description="Test Explorer UI output",
                priority=4,
            ),
            OutputSourceConfig(
                name="ViTest",
                category=OutputSourceCategory.TESTING,
                target_terminal="Tests",
                description="Vitest JavaScript testing",
                priority=3,
            ),
            OutputSourceConfig(
                name=".NET Test Log",
                category=OutputSourceCategory.TESTING,
                target_terminal="Tests",
                description=".NET test output",
                priority=4,
            ),
            OutputSourceConfig(
                name="Python Debugger",
                category=OutputSourceCategory.TESTING,
                target_terminal="Tests",
                description="Python debugger output",
                priority=5,
            ),
            OutputSourceConfig(
                name="coverage-gutters",
                category=OutputSourceCategory.TESTING,
                target_terminal="Tests",
                description="Code coverage visualization",
                priority=3,
            ),
        ]

        # ========== DATABASE/DATA ==========
        database_sources = [
            OutputSourceConfig(
                name="database Client",
                category=OutputSourceCategory.DATABASE_DATA,
                target_terminal="Metrics",
                description="Database client output",
                priority=3,
            ),
            OutputSourceConfig(
                name="SQLTools",
                category=OutputSourceCategory.DATABASE_DATA,
                target_terminal="Metrics",
                description="SQL query tool output",
                priority=4,
            ),
            OutputSourceConfig(
                name="rainbow_csv_debug+channel",
                category=OutputSourceCategory.DATABASE_DATA,
                target_terminal="Metrics",
                description="Rainbow CSV debug output",
                priority=2,
            ),
        ]

        # ========== FORMATTING ==========
        formatting_sources = [
            OutputSourceConfig(
                name="Black Formatter",
                category=OutputSourceCategory.FORMATTING,
                target_terminal="Suggestions",
                description="Black Python formatter",
                priority=3,
            ),
            OutputSourceConfig(
                name="Prettier",
                category=OutputSourceCategory.FORMATTING,
                target_terminal="Suggestions",
                description="Prettier code formatter",
                priority=3,
            ),
            OutputSourceConfig(
                name="isort",
                category=OutputSourceCategory.FORMATTING,
                target_terminal="Suggestions",
                description="Python import sorter",
                priority=2,
            ),
            OutputSourceConfig(
                name="autoDocstring",
                category=OutputSourceCategory.FORMATTING,
                target_terminal="Suggestions",
                description="Python docstring generator",
                priority=2,
            ),
            OutputSourceConfig(
                name="EditorConfig",
                category=OutputSourceCategory.FORMATTING,
                target_terminal="Suggestions",
                description="EditorConfig formatting",
                priority=2,
            ),
        ]

        # ========== AUTHENTICATION ==========
        auth_sources = [
            OutputSourceConfig(
                name="GitHub Authentication",
                category=OutputSourceCategory.AUTHENTICATION,
                target_terminal="System",
                description="GitHub auth provider",
                priority=4,
            ),
            OutputSourceConfig(
                name="Microsoft Authentication",
                category=OutputSourceCategory.AUTHENTICATION,
                target_terminal="System",
                description="Microsoft auth provider",
                priority=4,
            ),
        ]

        # ========== VS CODE CORE ==========
        vscode_core_sources = [
            OutputSourceConfig(
                name="Code",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="Main",
                description="VS Code core output",
                priority=5,
            ),
            OutputSourceConfig(
                name="Tasks",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="Tasks",
                description="VS Code task runner",
                priority=5,
            ),
            OutputSourceConfig(
                name="Terminal",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="Main",
                description="Integrated terminal output",
                priority=4,
            ),
            OutputSourceConfig(
                name="Extension Host",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="System",
                description="Extension host process",
                priority=3,
            ),
            OutputSourceConfig(
                name="Extension Host (Worker)",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="System",
                description="Extension worker process",
                priority=2,
            ),
            OutputSourceConfig(
                name="Main",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="Main",
                description="VS Code main process",
                priority=5,
            ),
            OutputSourceConfig(
                name="Pty Host",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="System",
                description="Pseudo-terminal host",
                priority=2,
            ),
            OutputSourceConfig(
                name="Settings Sync",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="System",
                description="Settings synchronization",
                priority=3,
            ),
            OutputSourceConfig(
                name="Shared",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="System",
                description="Shared VS Code services",
                priority=2,
            ),
            OutputSourceConfig(
                name="Window",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="Main",
                description="VS Code window management",
                priority=3,
            ),
            OutputSourceConfig(
                name="Text Model Changes Reason",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="System",
                description="Text model change tracking",
                priority=1,
            ),
            OutputSourceConfig(
                name="Remote Tunnel Service",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="System",
                description="Remote tunnel connections",
                priority=3,
            ),
            OutputSourceConfig(
                name="Agent Sessions",
                category=OutputSourceCategory.VSCODE_CORE,
                target_terminal="Agents",
                description="AI agent session management",
                priority=4,
            ),
        ]

        # ========== UTILITIES ==========
        utility_sources = [
            OutputSourceConfig(
                name="Auto Rename Tag",
                category=OutputSourceCategory.UTILITY,
                target_terminal="Suggestions",
                description="HTML/XML tag auto-renaming",
                priority=2,
            ),
            OutputSourceConfig(
                name="Code Spell Checker",
                category=OutputSourceCategory.UTILITY,
                target_terminal="Suggestions",
                description="Spell checker output",
                priority=2,
            ),
            OutputSourceConfig(
                name="Todohighlight",
                category=OutputSourceCategory.UTILITY,
                target_terminal="Tasks",
                description="TODO comment highlighter",
                priority=2,
            ),
            OutputSourceConfig(
                name="Peacock",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="Workspace color theming",
                priority=1,
            ),
            OutputSourceConfig(
                name="VersionLens",
                category=OutputSourceCategory.UTILITY,
                target_terminal="Suggestions",
                description="Package version lens",
                priority=3,
            ),
            OutputSourceConfig(
                name="Tailwind CSS IntelliSense",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="Tailwind CSS support",
                priority=3,
            ),
            OutputSourceConfig(
                name="OpenAPI Swagger Editor",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="OpenAPI/Swagger editor",
                priority=3,
            ),
            OutputSourceConfig(
                name="OpenCtx",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="OpenCtx context provider",
                priority=2,
            ),
            OutputSourceConfig(
                name="REST",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="REST client output",
                priority=3,
            ),
            OutputSourceConfig(
                name="Makefile Tools",
                category=OutputSourceCategory.UTILITY,
                target_terminal="Tasks",
                description="Makefile support",
                priority=3,
            ),
            OutputSourceConfig(
                name="MSBuild Project Tools",
                category=OutputSourceCategory.UTILITY,
                target_terminal="Tasks",
                description="MSBuild project tools",
                priority=3,
            ),
            OutputSourceConfig(
                name=".NET Install Tool",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description=".NET SDK installer",
                priority=2,
            ),
            OutputSourceConfig(
                name="ILSpy Backend",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="ILSpy decompiler backend",
                priority=2,
            ),
            OutputSourceConfig(
                name="ILSpy Extension",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="ILSpy extension output",
                priority=2,
            ),
            OutputSourceConfig(
                name="PyHover",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="Python hover documentation",
                priority=2,
            ),
            OutputSourceConfig(
                name="Python Locator",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="Python environment locator",
                priority=3,
            ),
            OutputSourceConfig(
                name="GritQL Token Provider",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="GritQL query token provider",
                priority=2,
            ),
            OutputSourceConfig(
                name="Sixth",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="Sixth extension output",
                priority=2,
            ),
            OutputSourceConfig(
                name="vscode-shiki-bridge",
                category=OutputSourceCategory.UTILITY,
                target_terminal="System",
                description="Shiki syntax highlighter bridge",
                priority=1,
            ),
            OutputSourceConfig(
                name="PowerShell",
                category=OutputSourceCategory.UTILITY,
                target_terminal="Main",
                description="PowerShell extension output",
                priority=4,
            ),
        ]

        # Combine all sources
        all_sources = (
            ai_ml_sources
            + language_server_sources
            + code_quality_sources
            + devops_sources
            + testing_sources
            + database_sources
            + formatting_sources
            + auth_sources
            + vscode_core_sources
            + utility_sources
        )

        return all_sources

    def _initialize_output_sources(self):
        """Map all 100+ output sources to terminal routing."""
        for source in self._build_output_sources():
            self.output_sources[source.name] = source

    async def route_output(self, source_name: str, message: str, level: str = "INFO") -> str | None:
        """Route an output message to the appropriate terminal."""
        await self.init()
        assert self.orchestrator is not None, "Orchestrator not initialized"

        if source_name not in self.output_sources:
            self.logger.warning(f"Unknown output source: {source_name}")
            # Route to Main as fallback
            self.orchestrator.route_message(f"[{source_name}] {message}", source=None, level=level)
            return "Main"

        config = self.output_sources[source_name]

        # Apply filter patterns
        if config.filter_patterns and not any(
            re.search(pattern, message, re.IGNORECASE) for pattern in config.filter_patterns
        ):
            return None  # Filtered out

        # Apply aggregation strategy
        if config.aggregation_strategy == "alert_only" and level not in ["ERROR", "WARNING"]:
            return None  # Only alert on errors/warnings

        # Route to target terminal
        self.orchestrator.route_message(
            f"[{source_name}] {message}", source=config.target_terminal, level=level
        )

        return config.target_terminal

    def get_sources_by_category(self, category: OutputSourceCategory) -> list[OutputSourceConfig]:
        """Get all output sources in a category."""
        return [source for source in self.output_sources.values() if source.category == category]

    def get_sources_by_terminal(self, terminal_name: str) -> list[OutputSourceConfig]:
        """Get all output sources routing to a specific terminal."""
        return [
            source
            for source in self.output_sources.values()
            if source.target_terminal == terminal_name
        ]

    def generate_routing_map(self) -> dict[str, Any]:
        """Generate comprehensive routing map."""
        by_terminal: dict[str, list[str]] = {}
        by_category: dict[str, list[str]] = {}

        for source in self.output_sources.values():
            # By terminal
            if source.target_terminal not in by_terminal:
                by_terminal[source.target_terminal] = []
            by_terminal[source.target_terminal].append(source.name)

            # By category
            cat_name = source.category.value
            if cat_name not in by_category:
                by_category[cat_name] = []
            by_category[cat_name].append(source.name)

        return {
            "total_sources": len(self.output_sources),
            "by_terminal": by_terminal,
            "by_category": by_category,
            "terminal_load": {terminal: len(sources) for terminal, sources in by_terminal.items()},
        }

    # ========== VS CODE LOG PARSING (Added for notification bootstrap) ==========

    def get_vscode_logs_dir(self) -> Path | None:
        """Get VS Code logs directory."""
        import os

        appdata = os.environ.get("APPDATA")
        if appdata:
            logs_dir = Path(appdata) / "Code" / "logs"
            if logs_dir.exists():
                return logs_dir
        return None

    def get_latest_log_session(self) -> Path | None:
        """Get the most recent VS Code log session directory."""
        logs_dir = self.get_vscode_logs_dir()
        if not logs_dir:
            return None
        # Session dirs are named like 20260228T171845
        sessions = sorted([d for d in logs_dir.iterdir() if d.is_dir()], reverse=True)
        return sessions[0] if sessions else None

    def parse_exthost_logs(self, max_entries: int = 100) -> list[dict[str, Any]]:
        """Parse VS Code extension host logs for errors/warnings.

        Returns list of parsed log entries with level, source, message, timestamp.
        """
        session = self.get_latest_log_session()
        if not session:
            return []

        entries: list[dict[str, Any]] = []
        exthost_log = session / "window1" / "exthost" / "exthost.log"

        if exthost_log.exists():
            try:
                content = exthost_log.read_text(encoding="utf-8", errors="replace")
                # Parse log lines: "2026-02-28 15:20:49.962 [warning] message..."
                log_pattern = re.compile(
                    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\s+\[(\w+)\]\s+(.+)"
                )
                for match in log_pattern.finditer(content):
                    timestamp, level, message = match.groups()
                    if level.lower() in ("error", "warning", "warn"):
                        entries.append(
                            {
                                "timestamp": timestamp,
                                "level": level.upper(),
                                "source": "exthost",
                                "message": message[:500],  # Truncate long messages
                            }
                        )
                        if len(entries) >= max_entries:
                            break
            except Exception as e:
                self.logger.warning(f"Failed to parse exthost.log: {e}")

        return entries

    def parse_output_channel_logs(
        self, channels: list[str] | None = None
    ) -> dict[str, list[dict[str, Any]]]:
        """Parse VS Code Output channel logs.

        Args:
            channels: Specific channels to parse. If None, parses key diagnostic channels.

        Returns dict mapping channel name to list of parsed entries.
        """
        session = self.get_latest_log_session()
        if not session:
            return {}

        # Default channels to parse for diagnostics
        if channels is None:
            channels = [
                "Ruff Language Server",
                "Python Language Server",
                "Python Test Adapter Log",
                "pytest",
                "Mypy",
                "Pylint",
            ]

        results: dict[str, list[dict[str, Any]]] = {}
        exthost_dir = session / "window1" / "exthost"

        # Find output_logging_* directories
        output_dirs = (
            sorted(
                [
                    d
                    for d in exthost_dir.iterdir()
                    if d.is_dir() and d.name.startswith("output_logging_")
                ],
                reverse=True,
            )
            if exthost_dir.exists()
            else []
        )

        if not output_dirs:
            return {}

        latest_output = output_dirs[0]

        for log_file in latest_output.iterdir():
            if not log_file.is_file() or not log_file.name.endswith(".log"):
                continue

            # Extract channel name (remove numeric prefix and .log suffix)
            channel_name = re.sub(r"^\d+-", "", log_file.stem)

            if channels and not any(c.lower() in channel_name.lower() for c in channels):
                continue

            entries: list[dict[str, Any]] = []
            try:
                content = log_file.read_text(encoding="utf-8", errors="replace")
                # Look for error/warning patterns
                for line in content.split("\n")[-200:]:  # Last 200 lines
                    line_lower = line.lower()
                    if any(kw in line_lower for kw in ("error", "warning", "failed", "exception")):
                        # Parse timestamp if present
                        ts_match = re.match(r"(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})", line)
                        entries.append(
                            {
                                "timestamp": ts_match.group(1) if ts_match else None,
                                "level": "ERROR" if "error" in line_lower else "WARNING",
                                "message": line[:500],
                            }
                        )
            except Exception as e:
                self.logger.debug(f"Failed to parse {log_file.name}: {e}")

            if entries:
                results[channel_name] = entries

        return results

    def parse_pytest_execution_log(self, max_failures: int = 50) -> list[dict[str, Any]]:
        """Parse pytest execution log for test failures.

        Returns list of test failure entries with test name, error, and file location.
        """
        session = self.get_latest_log_session()
        if not session:
            return []

        failures: list[dict[str, Any]] = []
        exthost_dir = session / "window1" / "exthost"

        # Find output_logging_* directories
        output_dirs = (
            sorted(
                [
                    d
                    for d in exthost_dir.iterdir()
                    if d.is_dir() and d.name.startswith("output_logging_")
                ],
                reverse=True,
            )
            if exthost_dir.exists()
            else []
        )

        for output_dir in output_dirs:
            # Find pytest execution log
            pytest_logs = list(output_dir.glob("*pytest*Execution*.log"))
            for pytest_log in pytest_logs:
                try:
                    content = pytest_log.read_text(encoding="utf-8", errors="replace")

                    # Parse FAILED test patterns
                    # Pattern: FAILED tests/test_foo.py::test_bar - AssertionError
                    fail_pattern = re.compile(r"FAILED\s+([\w/\\.:]+)\s*-?\s*(.*)")
                    for match in fail_pattern.finditer(content):
                        test_path, error = match.groups()
                        failures.append(
                            {
                                "test": test_path,
                                "error": error[:200] if error else "Unknown",
                                "source": pytest_log.name,
                            }
                        )
                        if len(failures) >= max_failures:
                            break

                    # Also capture ERROR lines
                    error_pattern = re.compile(r"^E\s+(.+)$", re.MULTILINE)
                    for i, match in enumerate(error_pattern.finditer(content)):
                        if i >= 20:  # Limit error lines
                            break
                        failures.append(
                            {
                                "test": "assertion",
                                "error": match.group(1)[:200],
                                "source": pytest_log.name,
                            }
                        )

                except Exception as e:
                    self.logger.debug(f"Failed to parse {pytest_log.name}: {e}")

                if len(failures) >= max_failures:
                    break

            if failures:
                break  # Found failures in this output dir

        return failures

    def aggregate_all_diagnostics(self) -> dict[str, Any]:
        """Aggregate all VS Code diagnostic sources into unified report.

        Returns comprehensive diagnostic summary for observability system.
        """
        session = self.get_latest_log_session()
        exthost = self.parse_exthost_logs(max_entries=50)
        channels = self.parse_output_channel_logs()
        pytest_failures = self.parse_pytest_execution_log(max_failures=30)

        return {
            "generated_at": datetime.now().isoformat(),
            "session": str(session) if session else None,
            "exthost_issues": exthost,
            "pytest_failures": pytest_failures,
            "output_channels": channels,
            "summary": {
                "exthost_count": len(exthost),
                "output_channel_count": sum(len(entries) for entries in channels.values()),
                "test_failure_count": len(pytest_failures),
            },
        }


# Singleton instance
_output_intelligence: OutputSourceIntelligence | None = None


async def get_output_intelligence() -> OutputSourceIntelligence:
    """Get or create singleton output intelligence."""
    global _output_intelligence
    if _output_intelligence is None:
        _output_intelligence = OutputSourceIntelligence()
        await _output_intelligence.init()
    return _output_intelligence


async def main():
    """Demo: Show routing map and test routing."""
    intelligence = await get_output_intelligence()

    logger.info("🎯 VS Code Output Source Intelligence")
    logger.info("=" * 80)

    routing_map = intelligence.generate_routing_map()

    logger.info(f"\n📊 Total Output Sources: {routing_map['total_sources']}")

    logger.info("\n📂 Sources by Terminal:")
    for terminal, count in sorted(routing_map["terminal_load"].items(), key=lambda x: -x[1]):
        sources = routing_map["by_terminal"][terminal]
        logger.info(f"  {terminal:20} → {count:3} sources")
        for source in sources[:3]:  # Show first 3
            logger.info(f"    • {source}")
        if len(sources) > 3:
            logger.info(f"    ... and {len(sources) - 3} more")

    logger.info("\n📂 Sources by Category:")
    for category, sources in routing_map["by_category"].items():
        logger.info(f"  {category:20} → {len(sources):3} sources")

    # Test routing
    logger.info("\n🧪 Testing Output Routing:")
    test_outputs = [
        ("Ruff", "Found 42 errors in module.py", "ERROR"),
        ("GitHub Copilot chat", "Suggestion: Use list comprehension", "INFO"),
        ("Python Test Adapter Log", "pytest passed 100 tests", "INFO"),
        ("SonarQube for IDE", "Code smell detected: complexity too high", "WARNING"),
        ("Git", "Changes not staged for commit", "INFO"),
    ]

    for source, message, level in test_outputs:
        terminal = await intelligence.route_output(source, message, level)
        logger.info(f"  [{source:30}] → {terminal or 'FILTERED'}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
