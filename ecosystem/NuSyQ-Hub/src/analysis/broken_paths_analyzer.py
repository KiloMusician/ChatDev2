#!/usr/bin/env python3
"""Broken Paths Analyzer - Repository Path Validation System.

Identifies and reports broken file paths, imports, and references.

This module provides comprehensive analysis of repository structure to identify:
- Broken file path references
- Invalid import statements
- Orphaned files with no references
- Missing dependencies

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Analysis", "Task"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import ast
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class BrokenPathsAnalyzer:
    """Comprehensive repository path validation and broken reference detection."""

    def __init__(self, repository_root: Path) -> None:
        """Initialize analyzer with repository root path."""
        self.repository_root = Path(repository_root).resolve()
        self.broken_paths: list[dict[str, Any]] = []
        self.broken_imports: list[dict[str, Any]] = []
        self.orphaned_files: list[dict[str, Any]] = []
        self.missing_files: list[dict[str, Any]] = []
        self.import_map: dict[str, list[str]] = {}
        self.file_references: dict[str, list[str]] = {}

    def analyze_repository(self) -> dict:
        """Comprehensive repository path analysis.

        Returns:
            dict containing analysis results with broken paths, imports, orphaned files

        """
        logger.info(f"Starting repository analysis for: {self.repository_root}")

        # Build file inventory
        all_files = self._get_all_files()
        python_files = [f for f in all_files if f.suffix == ".py"]

        # Analyze different types of issues
        self.broken_paths = self._find_broken_paths(all_files)
        self.broken_imports = self._find_broken_imports(python_files)
        self.orphaned_files = self._find_orphaned_files(all_files)
        self.missing_files = self._find_missing_referenced_files(all_files)

        # Generate summary
        summary = self._generate_summary()

        return {
            "repository_root": str(self.repository_root),
            "analysis_timestamp": str(datetime.now()),
            "broken_paths": self.broken_paths,
            "broken_imports": self.broken_imports,
            "orphaned_files": self.orphaned_files,
            "missing_files": self.missing_files,
            "summary": summary,
            "recommendations": self._generate_recommendations(),
        }

    def _get_all_files(self) -> list[Path]:
        """Get all files in repository, excluding common ignore patterns."""
        ignore_patterns = {
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            ".pytest_cache",
            "node_modules",
            ".mypy_cache",
            ".tox",
            "dist",
            "build",
        }

        all_files: list[Any] = []
        for root, dirs, files in os.walk(self.repository_root):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_patterns]

            for file in files:
                file_path = Path(root) / file
                all_files.append(file_path)

        return all_files

    def _find_broken_paths(self, all_files: list[Path]) -> list[dict]:
        """Find references to non-existent file paths."""
        broken_paths: list[Any] = []
        for file_path in all_files:
            if file_path.suffix in [".py", ".md", ".txt", ".yml", ".yaml", ".json"]:
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Look for file path patterns
                    path_patterns = [
                        r'["\']([^"\']+\.py)["\']',  # Python files in quotes
                        r'["\']([^"\']+\.md)["\']',  # Markdown files in quotes
                        r'["\']([^"\']+\.txt)["\']',  # Text files in quotes
                        r'["\']([^"\']+\.json)["\']',  # JSON files in quotes
                        r'["\']([^"\']+\.yml)["\']',  # YAML files in quotes
                        r'["\']([^"\']+\.yaml)["\']',  # YAML files in quotes
                    ]

                    for pattern in path_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            referenced_path = self._resolve_path_reference(file_path, match)
                            if referenced_path and not referenced_path.exists():
                                broken_paths.append(
                                    {
                                        "source_file": str(
                                            file_path.relative_to(self.repository_root)
                                        ),
                                        "broken_reference": match,
                                        "resolved_path": str(referenced_path),
                                        "type": "file_reference",
                                    }
                                )

                except Exception as e:
                    logger.warning(f"Error reading {file_path}: {e}")

        return broken_paths

    def _find_broken_imports(self, python_files: list[Path]) -> list[dict]:
        """Find broken import statements in Python files."""
        broken_imports: list[Any] = []
        for file_path in python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Parse AST to find imports
                try:
                    tree = ast.parse(content)
                    imports = self._extract_imports(tree)

                    for import_info in imports:
                        if not self._validate_import(import_info, file_path):
                            broken_imports.append(
                                {
                                    "source_file": str(file_path.relative_to(self.repository_root)),
                                    "import_statement": import_info["statement"],
                                    "module": import_info["module"],
                                    "line": import_info.get("line", "unknown"),
                                    "type": "import_error",
                                }
                            )

                except SyntaxError as e:
                    broken_imports.append(
                        {
                            "source_file": str(file_path.relative_to(self.repository_root)),
                            "import_statement": "SYNTAX_ERROR",
                            "module": "N/A",
                            "line": e.lineno if hasattr(e, "lineno") else "unknown",
                            "type": "syntax_error",
                            "error": str(e),
                        }
                    )

            except Exception as e:
                logger.warning(f"Error analyzing imports in {file_path}: {e}")

        return broken_imports

    def _find_orphaned_files(self, all_files: list[Path]) -> list[dict]:
        """Find files that appear to be orphaned (no references found)."""
        orphaned_files: list[Any] = []
        # Build reference map
        reference_map: dict[str, Any] = {}
        for file_path in all_files:
            if file_path.suffix in [".py", ".md", ".txt", ".yml", ".yaml", ".json"]:
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Look for references to other files
                    for other_file in all_files:
                        if other_file != file_path:
                            referenced_relative_path = other_file.relative_to(self.repository_root)
                            referenced_relative_path_str = str(referenced_relative_path)
                            if (
                                referenced_relative_path_str in content
                                or other_file.name in content
                            ):
                                if referenced_relative_path_str not in reference_map:
                                    reference_map[referenced_relative_path_str] = []
                                reference_map[referenced_relative_path_str].append(
                                    str(file_path.relative_to(self.repository_root))
                                )

                except (OSError, ValueError, AttributeError):
                    continue

        # Find files with no references and potential for being orphaned
        for file_path in all_files:
            relative_path = str(file_path.relative_to(self.repository_root))

            # Skip certain types that are commonly standalone
            if any(
                pattern in relative_path
                for pattern in [
                    "README",
                    "__init__",
                    "setup",
                    "requirements",
                    "LICENSE",
                    ".git",
                    "test_",
                    "_test",
                    ".venv",
                    "__pycache__",
                ]
            ):
                continue

            if relative_path not in reference_map:
                # Check if file is empty or very small (potentially incomplete)
                try:
                    file_size = file_path.stat().st_size
                    is_empty = file_size == 0
                    is_small = file_size < 100  # Less than 100 bytes

                    orphaned_files.append(
                        {
                            "file_path": relative_path,
                            "size_bytes": file_size,
                            "is_empty": is_empty,
                            "is_small": is_small,
                            "type": "potentially_orphaned",
                            "recommendation": (
                                "empty" if is_empty else "small" if is_small else "review"
                            ),
                        }
                    )
                except (OSError, ValueError, AttributeError):
                    continue

        return orphaned_files

    def _find_missing_referenced_files(self, all_files: list[Path]) -> list[dict]:
        """Find files that are referenced but don't exist."""
        missing_files: list[Any] = []
        existing_files = {str(f.relative_to(self.repository_root)) for f in all_files}

        for file_path in all_files:
            if file_path.suffix in [".py", ".md", ".txt"]:
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Look for file references that might be missing
                    patterns = [
                        r"(?:src/|docs/|tests?/|scripts?/)[\w/]+\.py",
                        r"[\w/]+\.md",
                        r"[\w/]+\.json",
                        r"[\w/]+\.yaml?",
                    ]

                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if match not in existing_files and self._looks_like_file_reference(
                                content, match
                            ):
                                # Check if it's a real reference (not just a string)
                                missing_files.append(
                                    {
                                        "source_file": str(
                                            file_path.relative_to(self.repository_root)
                                        ),
                                        "missing_file": match,
                                        "type": "missing_reference",
                                    }
                                )

                except (OSError, ValueError, AttributeError):
                    continue

        return missing_files

    def _resolve_path_reference(self, source_file: Path, reference: str) -> Path | None:
        """Resolve a path reference relative to source file or repository root."""
        # Try relative to source file directory
        relative_path = source_file.parent / reference
        if relative_path.exists():
            return relative_path

        # Try relative to repository root
        root_path = self.repository_root / reference
        if root_path.exists():
            return root_path

        # Try common variations
        variations = [
            self.repository_root / "src" / reference,
            self.repository_root / "docs" / reference,
            self.repository_root / "tests" / reference,
        ]

        for variation in variations:
            if variation.exists():
                return variation

        return self.repository_root / reference  # Return expected path even if it doesn't exist

    def _extract_imports(self, tree: ast.AST) -> list[dict]:
        """Extract import information from AST."""
        imports: list[Any] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "type": "import",
                            "module": alias.name,
                            "statement": f"import {alias.name}",
                            "line": node.lineno,
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(
                        {
                            "type": "from_import",
                            "module": module,
                            "name": alias.name,
                            "statement": f"from {module} import {alias.name}",
                            "line": node.lineno,
                        }
                    )

        return imports

    def _validate_import(self, import_info: dict, source_file: Path) -> bool:
        """Validate if an import can be resolved."""
        try:
            module = import_info["module"]

            # Skip standard library and known external packages
            if self._is_standard_or_external(module):
                return True

            # Try to resolve local imports
            if import_info["type"] == "from_import":
                return self._resolve_local_import(module, source_file)
            return self._resolve_module_import(module, source_file)

        except (KeyError, ValueError, AttributeError):
            return False

    def _is_standard_or_external(self, module: str) -> bool:
        """Check if module is standard library or known external package."""
        standard_libs = {
            "os",
            "sys",
            "json",
            "pathlib",
            "typing",
            "logging",
            "ast",
            "re",
            "datetime",
            "time",
            "collections",
            "itertools",
            "functools",
            "pandas",
            "numpy",
            "matplotlib",
            "requests",
            "yaml",
            "pydantic",
        }

        return any(module.startswith(lib) for lib in standard_libs)

    def _resolve_local_import(self, module: str, source_file: Path) -> bool:
        """Try to resolve a local module import."""
        if not module:
            return True

        # Convert module path to file path
        module_parts = module.split(".")

        # Try relative to source file
        current_dir = source_file.parent
        for part in module_parts:
            current_dir = current_dir / part

        if (current_dir / "__init__.py").exists() or (current_dir.with_suffix(".py")).exists():
            return True

        # Try relative to repository root
        current_dir = self.repository_root
        for part in module_parts:
            current_dir = current_dir / part

        return (current_dir / "__init__.py").exists() or (current_dir.with_suffix(".py")).exists()

    def _resolve_module_import(self, module: str, source_file: Path) -> bool:
        """Try to resolve a direct module import."""
        return self._resolve_local_import(module, source_file)

    def _looks_like_file_reference(self, content: str, reference: str) -> bool:
        """Heuristic to determine if a string looks like a file reference."""
        # Look for context clues that suggest it's a file reference
        reference_contexts = [
            f'"{reference}"',
            f"'{reference}'",
            f"load({reference}",
            f"open({reference}",
            f"read({reference}",
            f"import {reference}",
            f"include {reference}",
            f"path={reference}",
        ]

        return any(context in content for context in reference_contexts)

    def _generate_summary(self) -> dict:
        """Generate analysis summary statistics."""
        return {
            "total_broken_paths": len(self.broken_paths),
            "total_broken_imports": len(self.broken_imports),
            "total_orphaned_files": len(self.orphaned_files),
            "total_missing_files": len(self.missing_files),
            "empty_files": len([f for f in self.orphaned_files if f.get("is_empty", False)]),
            "small_files": len([f for f in self.orphaned_files if f.get("is_small", False)]),
            "syntax_errors": len(
                [i for i in self.broken_imports if i.get("type") == "syntax_error"]
            ),
            "health_score": self._calculate_health_score(),
        }

    def _calculate_health_score(self) -> float:
        """Calculate repository health score based on issues found."""
        total_issues = (
            len(self.broken_paths)
            + len(self.broken_imports)
            + len([f for f in self.orphaned_files if f.get("is_empty", False)])
            + len(self.missing_files)
        )

        # Rough scoring - could be refined
        max_score = 100
        deduction_per_issue = 2
        score = max(0, max_score - (total_issues * deduction_per_issue))

        return round(score, 1)

    def _generate_recommendations(self) -> list[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations: list[Any] = []
        if self.broken_paths:
            recommendations.append(f"Fix {len(self.broken_paths)} broken file path references")

        if self.broken_imports:
            recommendations.append(f"Resolve {len(self.broken_imports)} import issues")

        empty_files = [f for f in self.orphaned_files if f.get("is_empty", False)]
        if empty_files:
            recommendations.append(f"Implement or remove {len(empty_files)} empty files")

        if self.missing_files:
            recommendations.append(
                f"Create or fix references to {len(self.missing_files)} missing files"
            )

        syntax_errors = [i for i in self.broken_imports if i.get("type") == "syntax_error"]
        if syntax_errors:
            recommendations.append(f"Fix {len(syntax_errors)} syntax errors")

        if not recommendations:
            recommendations.append("Repository structure looks healthy!")

        return recommendations

    def save_analysis(self, output_path: Path) -> None:
        """Save analysis results to JSON file."""
        results = self.analyze_repository()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Analysis results saved to: {output_path}")


def main() -> None:
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze repository for broken paths and references"
    )
    parser.add_argument(
        "--repository",
        "-r",
        type=Path,
        default=Path.cwd(),
        help="Repository root path (default: current directory)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default="broken_paths_analysis.json",
        help="Output file path (default: broken_paths_analysis.json)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    analyzer = BrokenPathsAnalyzer(args.repository)
    results = analyzer.analyze_repository()

    # Print summary

    for _rec in results["recommendations"]:
        pass

    # Save results
    analyzer.save_analysis(args.output)


if __name__ == "__main__":
    main()
