"""Comprehensive Repository Context Analyzer using Pandas.

Creates structured datasets for easy "Add Context" interactions.
"""

import ast
import hashlib
import json
import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import git
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class RepositoryCompendium:
    """Comprehensive repository analysis and context generation system with QoL enhancements."""

    def __init__(self, repo_path: str = ".") -> None:
        """Initialize RepositoryCompendium with repo_path."""
        self.repo_path = Path(repo_path).resolve()
        self.repo_name = self.repo_path.name

        # Initialize dataframes
        self.files_df = pd.DataFrame()
        self.functions_df = pd.DataFrame()
        self.classes_df = pd.DataFrame()
        self.imports_df = pd.DataFrame()
        self.dependencies_df = pd.DataFrame()
        self.structure_df = pd.DataFrame()
        self.metrics_df = pd.DataFrame()
        self.git_history_df = pd.DataFrame()

        # Analysis cache
        self._analysis_cache: dict[str, Any] = {}

        # Add output deduplication for QoL
        self.last_output: str | None = None

    def _dedupe_print(self, message: str) -> None:
        """Prevent duplicate console output."""
        if message != self.last_output:
            self.last_output = message

    def analyze_repository(self) -> dict[str, pd.DataFrame]:
        """Complete repository analysis returning all dataframes."""
        self._dedupe_print(f"🔍 Analyzing repository: {self.repo_name}")

        # Core analyses
        self._analyze_file_structure()
        self._analyze_code_elements()
        self._analyze_dependencies()
        self._analyze_git_history()
        self._calculate_metrics()
        self._create_summary_views()

        return self.get_all_dataframes()

    def _analyze_file_structure(self) -> None:
        """Analyze file structure and create files DataFrame."""
        self._dedupe_print("📁 Analyzing file structure...")

        file_data: list[Any] = []
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common ignore directories
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d not in ["__pycache__", "node_modules", ".venv"]
            ]

            for file in files:
                if file.startswith("."):
                    continue

                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.repo_path)

                try:
                    stat = file_path.stat()
                    size_bytes = stat.st_size
                    modified_time = datetime.fromtimestamp(stat.st_mtime)

                    # File categorization
                    extension = file_path.suffix.lower()
                    file_type = self._categorize_file_type(extension)

                    # Calculate file hash for change detection
                    file_hash = self._calculate_file_hash(file_path)

                    # Count lines for text files
                    line_count = (
                        self._count_lines(file_path)
                        if file_type in ["code", "config", "docs"]
                        else 0
                    )

                    file_data.append(
                        {
                            "file_path": str(rel_path),
                            "file_name": file,
                            "directory": str(rel_path.parent),
                            "extension": extension,
                            "file_type": file_type,
                            "size_bytes": size_bytes,
                            "size_kb": round(size_bytes / 1024, 2),
                            "line_count": line_count,
                            "modified_time": modified_time,
                            "file_hash": file_hash,
                            "depth_level": len(rel_path.parts) - 1,
                        }
                    )

                except (FileNotFoundError, UnicodeDecodeError, OSError):
                    logger.debug(
                        "Suppressed FileNotFoundError/OSError/UnicodeDecodeError", exc_info=True
                    )

        self.files_df = pd.DataFrame(file_data)

        if not self.files_df.empty:
            # Add derived columns
            self.files_df["is_main_file"] = self.files_df["file_name"].isin(
                ["main.py", "app.py", "index.js", "index.html"]
            )
            self.files_df["is_config"] = self.files_df["file_type"] == "config"
            self.files_df["is_test"] = self.files_df["file_name"].str.contains(
                "test", case=False, na=False
            )

    def _analyze_code_elements(self) -> None:
        """Extract functions, classes, and imports from Python files."""
        python_files = self.files_df[self.files_df["extension"] == ".py"]["file_path"].tolist()

        functions_data: list[Any] = []
        classes_data: list[Any] = []
        imports_data: list[Any] = []
        for file_path in python_files:
            full_path = self.repo_path / file_path

            try:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                # Parse AST
                tree = ast.parse(content)

                # Extract elements
                file_functions = self._extract_functions(tree, file_path)
                file_classes = self._extract_classes(tree, file_path)
                file_imports = self._extract_imports(tree, file_path)

                functions_data.extend(file_functions)
                classes_data.extend(file_classes)
                imports_data.extend(file_imports)

            except (SyntaxError, ValueError, AttributeError):
                logger.debug("Suppressed AttributeError/SyntaxError/ValueError", exc_info=True)

        self.functions_df = pd.DataFrame(functions_data)
        self.classes_df = pd.DataFrame(classes_data)
        self.imports_df = pd.DataFrame(imports_data)

    def _extract_functions(self, tree: ast.AST, file_path: str) -> list[dict]:
        """Extract function information from AST."""
        functions: list[Any] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate complexity (simplified)
                complexity = len(
                    [
                        n
                        for n in ast.walk(node)
                        if isinstance(n, (ast.If, ast.For, ast.While, ast.With))
                    ]
                )

                # Extract docstring
                docstring = ast.get_docstring(node)

                # Extract parameters
                params = [arg.arg for arg in node.args.args]

                functions.append(
                    {
                        "file_path": file_path,
                        "function_name": node.name,
                        "line_start": node.lineno,
                        "line_end": getattr(node, "end_lineno", node.lineno),
                        "parameters": params,
                        "parameter_count": len(params),
                        "complexity": complexity,
                        "has_docstring": docstring is not None,
                        "docstring_length": len(docstring) if docstring else 0,
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "is_private": node.name.startswith("_"),
                        "is_magic": node.name.startswith("__") and node.name.endswith("__"),
                    }
                )

        return functions

    def _extract_classes(self, tree: ast.AST, file_path: str) -> list[dict]:
        """Extract class information from AST."""
        classes: list[Any] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count methods
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]

                # Extract base classes
                bases = [
                    base.id if isinstance(base, ast.Name) else str(base) for base in node.bases
                ]

                # Extract docstring
                docstring = ast.get_docstring(node)

                classes.append(
                    {
                        "file_path": file_path,
                        "class_name": node.name,
                        "line_start": node.lineno,
                        "line_end": getattr(node, "end_lineno", node.lineno),
                        "base_classes": bases,
                        "base_class_count": len(bases),
                        "method_count": len(methods),
                        "has_docstring": docstring is not None,
                        "docstring_length": len(docstring) if docstring else 0,
                        "is_private": node.name.startswith("_"),
                    }
                )

        return classes

    def _extract_imports(self, tree: ast.AST, file_path: str) -> list[dict]:
        """Extract import information from AST."""
        imports: list[Any] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "file_path": file_path,
                            "import_type": "import",
                            "module": alias.name,
                            "alias": alias.asname,
                            "line_number": node.lineno,
                            "is_standard_library": self._is_standard_library(alias.name),
                            "is_relative": False,
                        }
                    )

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(
                        {
                            "file_path": file_path,
                            "import_type": "from_import",
                            "module": (f"{module}.{alias.name}" if module else alias.name),
                            "base_module": module,
                            "imported_name": alias.name,
                            "alias": alias.asname,
                            "line_number": node.lineno,
                            "is_standard_library": self._is_standard_library(module),
                            "is_relative": node.level > 0,
                            "relative_level": node.level,
                        }
                    )

        return imports

    def _analyze_dependencies(self) -> None:
        """Analyze project dependencies."""
        deps_data: list[Any] = []
        # Check common dependency files
        dep_files = {
            "requirements.txt": "pip",
            "pyproject.toml": "poetry/pip",
            "package.json": "npm",
            "Pipfile": "pipenv",
            "environment.yml": "conda",
        }

        for file_name, package_manager in dep_files.items():
            dep_path = self.repo_path / file_name
            if dep_path.exists():
                deps = self._parse_dependency_file(dep_path, package_manager)
                deps_data.extend(deps)

        self.dependencies_df = pd.DataFrame(deps_data)

    def _analyze_git_history(self) -> None:
        """Analyze Git history if available."""
        try:
            repo = git.Repo(self.repo_path)
            commits_data: list[Any] = []
            # Get last 100 commits
            for commit in list(repo.iter_commits())[:100]:
                commits_data.append(
                    {
                        "commit_hash": commit.hexsha,
                        "short_hash": commit.hexsha[:7],
                        "author": commit.author.name,
                        "author_email": commit.author.email,
                        "date": commit.committed_datetime,
                        "message": commit.message.strip(),
                        "files_changed": len(commit.stats.files),
                        "insertions": commit.stats.total["insertions"],
                        "deletions": commit.stats.total["deletions"],
                        "lines_changed": commit.stats.total["lines"],
                    }
                )

            self.git_history_df = pd.DataFrame(commits_data)

        except (subprocess.CalledProcessError, OSError, ValueError):
            self.git_history_df = pd.DataFrame()

    def _calculate_metrics(self) -> None:
        """Calculate repository metrics."""
        metrics = {
            "timestamp": datetime.now(),
            "total_files": len(self.files_df),
            "total_lines": self.files_df["line_count"].sum(),
            "total_size_kb": self.files_df["size_kb"].sum(),
            "python_files": len(self.files_df[self.files_df["extension"] == ".py"]),
            "total_functions": len(self.functions_df),
            "total_classes": len(self.classes_df),
            "total_imports": len(self.imports_df),
            "avg_function_complexity": (
                self.functions_df["complexity"].mean() if not self.functions_df.empty else 0
            ),
            "max_file_size_kb": (self.files_df["size_kb"].max() if not self.files_df.empty else 0),
            "deepest_directory_level": (
                self.files_df["depth_level"].max() if not self.files_df.empty else 0
            ),
        }

        # File type distribution
        if not self.files_df.empty:
            file_type_counts = self.files_df["file_type"].value_counts().to_dict()
            metrics.update({f"files_{k}": v for k, v in file_type_counts.items()})

        self.metrics_df = pd.DataFrame([metrics])

    def _create_summary_views(self) -> None:
        """Create summary views for easy analysis."""
        if self.files_df.empty:
            return

        # Directory structure summary
        dir_summary = (
            self.files_df.groupby("directory")
            .agg(
                {
                    "file_path": "count",
                    "size_kb": "sum",
                    "line_count": "sum",
                }
            )
            .rename(columns={"file_path": "file_count"})
            .reset_index()
        )

        self.structure_df = dir_summary.sort_values("file_count", ascending=False)

    def get_context_summary(self) -> dict[str, Any]:
        """Generate a comprehensive context summary."""
        summary = {
            "repository": {
                "name": self.repo_name,
                "path": str(self.repo_path),
                "analysis_date": datetime.now().isoformat(),
            },
            "overview": {},
            "top_files": [],
            "key_components": {},
            "dependencies": [],
            "recommendations": [],
        }

        if not self.metrics_df.empty:
            metrics = self.metrics_df.iloc[0].to_dict()
            summary["overview"] = {
                "total_files": metrics.get("total_files", 0),
                "lines_of_code": metrics.get("total_lines", 0),
                "size_mb": round(metrics.get("total_size_kb", 0) / 1024, 2),
                "python_files": metrics.get("python_files", 0),
                "functions": metrics.get("total_functions", 0),
                "classes": metrics.get("total_classes", 0),
            }

        # Top files by size and complexity
        if not self.files_df.empty:
            top_files = self.files_df.nlargest(5, "size_kb")[
                ["file_path", "size_kb", "line_count"]
            ].to_dict("records")
            summary["top_files"] = top_files

        # Key components (main files, configs, etc.)
        key_mask = (
            self.files_df["is_main_file"]
            | self.files_df["is_config"]
            | self.files_df["file_name"].str.contains("README", case=False, na=False)
        )
        key_files = self.files_df[key_mask]["file_path"].tolist()

        summary["key_components"] = {
            "entry_points": [f for f in key_files if "main" in f or "app" in f],
            "configuration": [
                f for f in key_files if any(ext in f for ext in [".json", ".yaml", ".toml", ".ini"])
            ],
            "documentation": [f for f in key_files if "README" in f.upper()],
        }

        return summary

    def export_context_package(self, output_dir: str = "context_export") -> str:
        """Export all analysis data as a context package."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Export all dataframes
        dataframes = self.get_all_dataframes()
        for name, df in dataframes.items():
            if not df.empty:
                df.to_csv(output_path / f"{name}.csv", index=False)
                df.to_json(output_path / f"{name}.json", orient="records", default_handler=str)

        # Export summary
        summary = self.get_context_summary()
        with open(output_path / "context_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        # Create markdown report
        self._create_markdown_report(output_path)

        return str(output_path)

    def _create_markdown_report(self, output_path: Path) -> None:
        """Create a comprehensive markdown report."""
        summary = self.get_context_summary()

        report = f"""# Repository Analysis Report: {self.repo_name}

## Overview
- **Total Files**: {summary["overview"].get("total_files", 0)}
- **Lines of Code**: {summary["overview"].get("lines_of_code", 0):,}
- **Size**: {summary["overview"].get("size_mb", 0)} MB
- **Python Files**: {summary["overview"].get("python_files", 0)}
- **Functions**: {summary["overview"].get("functions", 0)}
- **Classes**: {summary["overview"].get("classes", 0)}

## File Structure
"""

        if not self.structure_df.empty:
            report += "\n### Directory Breakdown\n"
            for _, row in self.structure_df.head(10).iterrows():
                report += f"- **{row['directory']}**: {row['file_count']} files, {row['size_kb']:.1f} KB\n"

        if summary["top_files"]:
            report += "\n### Largest Files\n"
            for file_info in summary["top_files"]:
                report += f"- **{file_info['file_path']}**: {file_info['size_kb']:.1f} KB, {file_info['line_count']} lines\n"

        if not self.functions_df.empty:
            complex_functions = self.functions_df.nlargest(5, "complexity")
            if not complex_functions.empty:
                report += "\n### Most Complex Functions\n"
                for _, func in complex_functions.iterrows():
                    report += f"- **{func['function_name']}** in {func['file_path']}: Complexity {func['complexity']}\n"

        if not self.dependencies_df.empty:
            report += "\n### Dependencies\n"
            report += f"Total dependencies: {len(self.dependencies_df)}\n"

            top_deps = self.dependencies_df.head(10)
            for _, dep in top_deps.iterrows():
                report += f"- {dep.get('package', 'unknown')}\n"

        report += f"\n---\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        with open(output_path / "ANALYSIS_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report)

    def get_all_dataframes(self) -> dict[str, pd.DataFrame]:
        """Return all analysis dataframes."""
        return {
            "files": self.files_df,
            "functions": self.functions_df,
            "classes": self.classes_df,
            "imports": self.imports_df,
            "dependencies": self.dependencies_df,
            "structure": self.structure_df,
            "metrics": self.metrics_df,
            "git_history": self.git_history_df,
        }

    # Utility methods
    def _categorize_file_type(self, extension: str) -> str:
        """Categorize file type based on extension."""
        categories = {
            "code": [
                ".py",
                ".js",
                ".ts",
                ".java",
                ".cpp",
                ".c",
                ".cs",
                ".go",
                ".rs",
                ".php",
            ],
            "config": [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"],
            "docs": [".md", ".rst", ".txt", ".pdf", ".doc", ".docx"],
            "web": [".html", ".css", ".scss", ".less"],
            "data": [".csv", ".xlsx", ".json", ".xml", ".sql"],
            "image": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"],
            "archive": [".zip", ".tar", ".gz", ".rar"],
        }

        for category, extensions in categories.items():
            if extension in extensions:
                return category
        return "other"

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()[:8]
        except (FileNotFoundError, OSError):
            return "unknown"

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in text file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return sum(1 for _ in f)
        except (FileNotFoundError, UnicodeDecodeError, OSError):
            return 0

    def _is_standard_library(self, module_name: str) -> bool:
        """Check if module is part of Python standard library."""
        if not module_name:
            return False

        stdlib_modules = {
            "os",
            "sys",
            "json",
            "csv",
            "math",
            "random",
            "datetime",
            "time",
            "pathlib",
            "collections",
            "itertools",
            "functools",
            "operator",
            "re",
            "ast",
            "hashlib",
            "urllib",
            "http",
            "subprocess",
            "threading",
        }

        base_module = module_name.split(".")[0]
        return base_module in stdlib_modules

    def _parse_dependency_file(self, file_path: Path, package_manager: str) -> list[dict]:
        """Parse dependency file."""
        deps: list[Any] = []
        try:
            if file_path.name == "requirements.txt":
                with open(file_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Parse requirement
                            package = re.split(r"[<>=!]", line)[0].strip()
                            deps.append(
                                {
                                    "package": package,
                                    "version_spec": line,
                                    "package_manager": package_manager,
                                    "file_source": str(file_path.name),
                                }
                            )
            # Add other dependency file parsers as needed
        except (FileNotFoundError, UnicodeDecodeError, OSError):
            logger.debug("Suppressed FileNotFoundError/OSError/UnicodeDecodeError", exc_info=True)

        return deps


# Quick analysis function
def quick_analyze(repo_path: str = ".") -> dict[str, pd.DataFrame]:
    """Quick repository analysis function."""
    analyzer = RepositoryCompendium(repo_path)
    return analyzer.analyze_repository()


# Context export function
def export_repository_context(repo_path: str = ".", output_dir: str = "context_export") -> str:
    """Export complete repository context for AI interactions."""
    analyzer = RepositoryCompendium(repo_path)
    analyzer.analyze_repository()
    return analyzer.export_context_package(output_dir)
