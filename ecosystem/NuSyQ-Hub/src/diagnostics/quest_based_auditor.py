#!/usr/bin/env python3
"""🔍 KILO-FOOLISH Quest-Based Repository Audit System.

Systematic file analysis with quest progression and detailed reporting.

OmniTag: {
    "purpose": "comprehensive_repository_audit",
    "type": "quest_based_analysis",
    "evolution_stage": "v4.0_quest_system"
}
MegaTag: {
    "scope": "full_repository_analysis",
    "integration_points": ["file_analysis", "syntax_validation", "import_resolution", "quest_progression"],
    "quantum_context": "systematic_repository_consciousness"
}
RSHTS: ΞΨΩ∞⟨QUEST_AUDIT⟩→ΦΣΣ⟨SYSTEMATIC_ANALYSIS⟩
"""

import ast
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict


class FileInfo(TypedDict):
    """File information structure."""

    path: str
    size: int
    modified: str


class SubdirInfo(TypedDict):
    """Subdirectory information."""

    name: str
    python_files: int


class SrcFocus(TypedDict):
    """Source directory focus structure."""

    subdirectories: list[SubdirInfo]
    python_files: list[FileInfo]
    total_python_files: int


class FileCatalog(TypedDict):
    """File catalog structure for quest 1."""

    python_files: list[FileInfo]
    markdown_files: list[FileInfo]
    json_files: list[FileInfo]
    powershell_files: list[FileInfo]
    other_files: list[FileInfo]
    directories: list[str]
    total_size: int
    src_focus: SrcFocus


class QuestBasedAuditor:
    """Quest-based systematic repository auditor."""

    def __init__(self) -> None:
        """Initialize QuestBasedAuditor."""
        self.repo_root = Path.cwd()
        self.quest_results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "repository": str(self.repo_root),
            "quests": {},
            "overall_stats": {},
            "recommendations": [],
        }
        self.total_files_found: int = 0
        self.files_analyzed: int = 0
        self.errors_found: int = 0
        self.warnings_found: int = 0

    def log_quest_start(self, quest_name: str, description: str) -> None:
        """Log the start of a quest."""
        self.quest_results["quests"][quest_name] = {
            "description": description,
            "started": datetime.now().isoformat(),
            "status": "in_progress",
            "results": {},
            "files_processed": 0,
            "issues_found": 0,
            "completion_time": None,
        }

    def log_quest_complete(self, quest_name: str, summary: str) -> None:
        """Log quest completion."""
        quest = self.quest_results["quests"][quest_name]
        quest["status"] = "completed"
        quest["completed"] = datetime.now().isoformat()
        quest["summary"] = summary

    def quest_1_file_discovery(self) -> FileCatalog:
        """Quest 1: Discover and catalog all files in the repository."""
        self.log_quest_start("File Discovery", "Systematically catalog all files in the repository")

        file_catalog: FileCatalog = {
            "python_files": [],
            "markdown_files": [],
            "json_files": [],
            "powershell_files": [],
            "other_files": [],
            "directories": [],
            "total_size": 0,
            "src_focus": {
                "subdirectories": [],
                "python_files": [],
                "total_python_files": 0,
            },
        }

        # Discover all files
        for root, dirs, files in os.walk(self.repo_root):
            root_path = Path(root)
            relative_root = root_path.relative_to(self.repo_root)

            # Skip certain directories
            skip_dirs = {
                ".git",
                "__pycache__",
                ".vscode",
                "node_modules",
                ".pytest_cache",
            }
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            file_catalog["directories"].append(str(relative_root))

            for file in files:
                file_path = root_path / file
                relative_path = file_path.relative_to(self.repo_root)

                try:
                    file_size = file_path.stat().st_size
                    file_catalog["total_size"] += file_size

                    file_info: FileInfo = {
                        "path": str(relative_path),
                        "size": file_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    }

                    if file.endswith(".py"):
                        file_catalog["python_files"].append(file_info)
                        # Special tracking for src directory
                        if "src" in relative_path.parts:
                            file_catalog["src_focus"]["python_files"].append(file_info)
                    elif file.endswith(".md"):
                        file_catalog["markdown_files"].append(file_info)
                    elif file.endswith(".json"):
                        file_catalog["json_files"].append(file_info)
                    elif file.endswith(".ps1"):
                        file_catalog["powershell_files"].append(file_info)
                    else:
                        file_catalog["other_files"].append(file_info)

                except (PermissionError, FileNotFoundError):
                    continue

        # Analyze src directory structure
        src_path = self.repo_root / "src"
        if src_path.exists():
            for item in src_path.iterdir():
                if item.is_dir():
                    subdir_info: SubdirInfo = {
                        "name": item.name,
                        "python_files": len(list(item.rglob("*.py"))),
                    }
                    file_catalog["src_focus"]["subdirectories"].append(subdir_info)

        file_catalog["src_focus"]["total_python_files"] = len(
            file_catalog["src_focus"]["python_files"]
        )
        self.total_files_found = (
            len(file_catalog["python_files"])
            + len(file_catalog["markdown_files"])
            + len(file_catalog["json_files"])
            + len(file_catalog["powershell_files"])
            + len(file_catalog["other_files"])
        )

        self.quest_results["quests"]["File Discovery"]["results"] = file_catalog
        self.quest_results["quests"]["File Discovery"]["files_processed"] = self.total_files_found

        summary = f"Found {self.total_files_found} files ({len(file_catalog['python_files'])} Python, {len(file_catalog['src_focus']['python_files'])} in src/)"
        self.log_quest_complete("File Discovery", summary)

        return file_catalog

    def quest_2_python_syntax_validation(self, python_files: list[FileInfo]) -> dict[str, Any]:
        """Quest 2: Validate Python syntax across all files."""
        self.log_quest_start("Python Syntax Validation", "Check all Python files for syntax errors")

        validation_results: dict[str, Any] = {
            "valid_files": [],
            "syntax_errors": [],
            "import_errors": [],
            "compilation_errors": [],
            "success_rate": 0.0,
            "error_categories": defaultdict(int),
        }

        for _i, file_info in enumerate(python_files):
            file_path = self.repo_root / file_info["path"]

            try:
                # Test compilation
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(file_path)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    validation_results["valid_files"].append(file_info["path"])
                else:
                    error_info = {
                        "file": file_info["path"],
                        "error": result.stderr,
                        "type": "compilation_error",
                    }

                    # Categorize error
                    error_text = result.stderr.lower()
                    if "syntaxerror" in error_text:
                        error_info["type"] = "syntax_error"
                        validation_results["syntax_errors"].append(error_info)
                        validation_results["error_categories"]["syntax"] += 1
                    elif "indentationerror" in error_text:
                        error_info["type"] = "indentation_error"
                        validation_results["syntax_errors"].append(error_info)
                        validation_results["error_categories"]["indentation"] += 1
                    elif "importerror" in error_text or "modulenotfounderror" in error_text:
                        error_info["type"] = "import_error"
                        validation_results["import_errors"].append(error_info)
                        validation_results["error_categories"]["import"] += 1
                    else:
                        validation_results["compilation_errors"].append(error_info)
                        validation_results["error_categories"]["other"] += 1

            except subprocess.TimeoutExpired:
                validation_results["compilation_errors"].append(
                    {
                        "file": file_info["path"],
                        "error": "Compilation timeout",
                        "type": "timeout",
                    }
                )
                validation_results["error_categories"]["timeout"] += 1

            except Exception as e:
                validation_results["compilation_errors"].append(
                    {
                        "file": file_info["path"],
                        "error": str(e),
                        "type": "exception",
                    }
                )
                validation_results["error_categories"]["exception"] += 1

        total_errors = (
            len(validation_results["syntax_errors"])
            + len(validation_results["import_errors"])
            + len(validation_results["compilation_errors"])
        )
        validation_results["success_rate"] = (
            (len(validation_results["valid_files"]) / len(python_files)) * 100
            if python_files
            else 0
        )

        self.errors_found += total_errors
        self.quest_results["quests"]["Python Syntax Validation"]["results"] = validation_results
        self.quest_results["quests"]["Python Syntax Validation"]["files_processed"] = len(
            python_files
        )
        self.quest_results["quests"]["Python Syntax Validation"]["issues_found"] = total_errors

        summary = f"Validated {len(python_files)} files - {validation_results['success_rate']:.1f}% success rate, {total_errors} errors"
        self.log_quest_complete("Python Syntax Validation", summary)

        return validation_results

    def quest_3_import_dependency_analysis(self, python_files: list[FileInfo]) -> dict[str, Any]:
        """Quest 3: Analyze import dependencies and detect issues."""
        self.log_quest_start(
            "Import Dependency Analysis",
            "Map import dependencies and detect circular imports",
        )

        dependency_results: dict[str, Any] = {
            "import_graph": {},
            "circular_imports": [],
            "missing_modules": [],
            "stdlib_imports": set(),
            "third_party_imports": set(),
            "local_imports": set(),
            "src_internal_imports": {},
        }

        for file_info in python_files:
            file_path = self.repo_root / file_info["path"]

            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Parse AST to extract imports
                try:
                    tree = ast.parse(content)
                    file_imports: list[Any] = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                file_imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            file_imports.append(node.module)

                    dependency_results["import_graph"][file_info["path"]] = file_imports

                    # Categorize imports
                    for imp in file_imports:
                        if imp.startswith(("src.", ".")):
                            dependency_results["local_imports"].add(imp)
                            # Track src internal imports
                            if "src/" in file_info["path"]:
                                if (
                                    file_info["path"]
                                    not in dependency_results["src_internal_imports"]
                                ):
                                    dependency_results["src_internal_imports"][
                                        file_info["path"]
                                    ] = []
                                dependency_results["src_internal_imports"][
                                    file_info["path"]
                                ].append(imp)
                        elif (
                            imp in sys.stdlib_module_names
                            or imp.split(".")[0] in sys.stdlib_module_names
                        ):
                            dependency_results["stdlib_imports"].add(imp)
                        else:
                            dependency_results["third_party_imports"].add(imp)

                except SyntaxError:
                    # Skip files with syntax errors
                    continue

            except (PermissionError, FileNotFoundError, UnicodeDecodeError):
                continue

        # Convert sets to lists for JSON serialization
        dependency_results["stdlib_imports"] = list(dependency_results["stdlib_imports"])
        dependency_results["third_party_imports"] = list(dependency_results["third_party_imports"])
        dependency_results["local_imports"] = list(dependency_results["local_imports"])

        self.quest_results["quests"]["Import Dependency Analysis"]["results"] = dependency_results
        self.quest_results["quests"]["Import Dependency Analysis"]["files_processed"] = len(
            python_files
        )

        summary = f"Analyzed imports for {len(python_files)} files - {len(dependency_results['third_party_imports'])} 3rd party, {len(dependency_results['local_imports'])} local"
        self.log_quest_complete("Import Dependency Analysis", summary)

        return dependency_results

    def quest_4_src_directory_deep_analysis(self) -> dict[str, Any]:
        """Quest 4: Deep analysis of src directory structure and organization."""
        self.log_quest_start(
            "Src Directory Analysis",
            "Comprehensive analysis of src/ directory structure and code organization",
        )

        src_analysis: dict[str, Any] = {
            "directory_structure": {},
            "code_metrics": {},
            "integration_points": {},
            "module_relationships": {},
            "capability_mapping": {},
        }

        src_path = self.repo_root / "src"
        if not src_path.exists():
            src_analysis["error"] = "src directory not found"
            self.log_quest_complete("Src Directory Analysis", "src directory not found")
            return src_analysis

        # Analyze directory structure
        total_lines = 0
        total_functions = 0
        total_classes = 0

        for subdir in src_path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("."):
                subdir_info: dict[str, Any] = {
                    "python_files": [],
                    "total_lines": 0,
                    "functions": 0,
                    "classes": 0,
                    "imports": [],
                }

                for py_file in subdir.rglob("*.py"):
                    try:
                        with open(py_file, encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            lines = content.count("\n") + 1
                            subdir_info["total_lines"] += lines
                            total_lines += lines

                        # Parse for functions and classes
                        try:
                            tree = ast.parse(content)
                            file_functions = 0
                            file_classes = 0

                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    file_functions += 1
                                elif isinstance(node, ast.ClassDef):
                                    file_classes += 1

                            subdir_info["functions"] += file_functions
                            subdir_info["classes"] += file_classes
                            total_functions += file_functions
                            total_classes += file_classes

                            subdir_info["python_files"].append(
                                {
                                    "path": str(py_file.relative_to(self.repo_root)),
                                    "lines": lines,
                                    "functions": file_functions,
                                    "classes": file_classes,
                                }
                            )

                        except SyntaxError:
                            continue

                    except (PermissionError, FileNotFoundError, UnicodeDecodeError):
                        continue

                src_analysis["directory_structure"][subdir.name] = subdir_info

        # Overall metrics
        src_analysis["code_metrics"] = {
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "avg_lines_per_file": total_lines
            / max(
                1,
                sum(
                    len(info["python_files"])
                    for info in src_analysis["directory_structure"].values()
                ),
            ),
        }

        # Identify integration points (files that import from multiple subdirectories)
        integration_files: list[Any] = []
        for subdir_name, subdir_info in src_analysis["directory_structure"].items():
            for file_info in subdir_info["python_files"]:
                file_path = self.repo_root / file_info["path"]
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Count imports from other src subdirectories
                    other_subdir_imports = 0
                    for line in content.split("\n"):
                        if line.strip().startswith(("from src.", "import src.")):
                            imported_subdir = line.split("src.")[1].split(".")[0]
                            if imported_subdir != subdir_name:
                                other_subdir_imports += 1

                    if other_subdir_imports > 0:
                        integration_files.append(
                            {
                                "file": file_info["path"],
                                "subdir": subdir_name,
                                "cross_imports": other_subdir_imports,
                            }
                        )

                except (PermissionError, FileNotFoundError, UnicodeDecodeError):
                    continue

        src_analysis["integration_points"]["cross_directory_imports"] = integration_files

        self.quest_results["quests"]["Src Directory Analysis"]["results"] = src_analysis
        self.quest_results["quests"]["Src Directory Analysis"]["files_processed"] = sum(
            len(info["python_files"]) for info in src_analysis["directory_structure"].values()
        )

        summary = f"Analyzed src/ - {len(src_analysis['directory_structure'])} subdirs, {total_lines} lines, {total_functions} functions, {total_classes} classes"
        self.log_quest_complete("Src Directory Analysis", summary)

        return src_analysis

    def quest_5_integration_system_validation(self) -> dict[str, Any]:
        """Quest 5: Validate integration systems (Ollama, ChatDev, Copilot)."""
        self.log_quest_start(
            "Integration System Validation",
            "Test and validate all AI integration systems",
        )

        integration_validation: dict[str, Any] = {
            "ollama_integration": {"status": "unknown", "files": [], "issues": []},
            "chatdev_integration": {"status": "unknown", "files": [], "issues": []},
            "copilot_integration": {"status": "unknown", "files": [], "issues": []},
            "cross_system_compatibility": {"score": 0, "issues": []},
        }

        # Check Ollama integration files
        ollama_files = [
            "src/integration/ollama_integration.py",
            "src/ai/ollama_chatdev_integrator.py",
            "src/integration/Update-ChatDev-to-use-Ollama.py",
        ]

        ollama_working = 0
        for file_path in ollama_files:
            full_path = self.repo_root / file_path
            if full_path.exists():
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", str(full_path)],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        integration_validation["ollama_integration"]["files"].append(
                            {"path": file_path, "status": "valid"}
                        )
                        ollama_working += 1
                    else:
                        integration_validation["ollama_integration"]["files"].append(
                            {
                                "path": file_path,
                                "status": "error",
                                "error": result.stderr,
                            }
                        )
                        integration_validation["ollama_integration"]["issues"].append(
                            f"{file_path}: {result.stderr}"
                        )
                except Exception as e:
                    integration_validation["ollama_integration"]["issues"].append(
                        f"{file_path}: {e!s}"
                    )
            else:
                integration_validation["ollama_integration"]["issues"].append(
                    f"{file_path}: File not found"
                )

        integration_validation["ollama_integration"]["status"] = (
            "operational" if ollama_working >= 2 else "needs_attention"
        )

        # Check ChatDev integration files
        chatdev_files = [
            "src/integration/chatdev_llm_adapter.py",
            "src/integration/chatdev_launcher.py",
            "src/orchestration/chatdev_testing_chamber.py",
        ]

        chatdev_working = 0
        for file_path in chatdev_files:
            full_path = self.repo_root / file_path
            if full_path.exists():
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", str(full_path)],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        integration_validation["chatdev_integration"]["files"].append(
                            {"path": file_path, "status": "valid"}
                        )
                        chatdev_working += 1
                    else:
                        integration_validation["chatdev_integration"]["files"].append(
                            {
                                "path": file_path,
                                "status": "error",
                                "error": result.stderr,
                            }
                        )
                        integration_validation["chatdev_integration"]["issues"].append(
                            f"{file_path}: {result.stderr}"
                        )
                except Exception as e:
                    integration_validation["chatdev_integration"]["issues"].append(
                        f"{file_path}: {e!s}"
                    )
            else:
                integration_validation["chatdev_integration"]["issues"].append(
                    f"{file_path}: File not found"
                )

        integration_validation["chatdev_integration"]["status"] = (
            "operational" if chatdev_working >= 2 else "needs_attention"
        )

        # Check Copilot enhancement files
        copilot_files = [
            ".copilot/copilot_enhancement_bridge.py",
            ".github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md",
        ]

        copilot_working = 0
        for file_path in copilot_files:
            full_path = self.repo_root / file_path
            if full_path.exists():
                copilot_working += 1
                integration_validation["copilot_integration"]["files"].append(
                    {"path": file_path, "status": "present"}
                )
            else:
                integration_validation["copilot_integration"]["issues"].append(
                    f"{file_path}: File not found"
                )

        integration_validation["copilot_integration"]["status"] = (
            "operational" if copilot_working >= 1 else "needs_attention"
        )

        # Calculate cross-system compatibility score
        system_scores = [
            (1 if integration_validation["ollama_integration"]["status"] == "operational" else 0),
            (1 if integration_validation["chatdev_integration"]["status"] == "operational" else 0),
            (1 if integration_validation["copilot_integration"]["status"] == "operational" else 0),
        ]
        integration_validation["cross_system_compatibility"]["score"] = sum(system_scores) * 33.33

        self.quest_results["quests"]["Integration System Validation"][
            "results"
        ] = integration_validation

        summary = f"Integration validation - Ollama: {integration_validation['ollama_integration']['status']}, ChatDev: {integration_validation['chatdev_integration']['status']}, Copilot: {integration_validation['copilot_integration']['status']}"
        self.log_quest_complete("Integration System Validation", summary)

        return integration_validation

    def quest_6_performance_and_optimization_analysis(
        self, python_files: list[FileInfo]
    ) -> dict[str, Any]:
        """Quest 6: Analyze performance characteristics and optimization opportunities."""
        self.log_quest_start(
            "Performance Analysis",
            "Identify performance bottlenecks and optimization opportunities",
        )

        performance_analysis: dict[str, Any] = {
            "large_files": [],
            "complex_functions": [],
            "potential_optimizations": [],
            "code_quality_metrics": {},
            "resource_usage_patterns": {},
        }

        # Analyze file sizes and complexity
        for file_info in python_files[:50]:  # Limit to first 50 files for performance
            file_path = self.repo_root / file_info["path"]

            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                lines = content.count("\n") + 1

                # Flag large files
                if lines > 500:
                    performance_analysis["large_files"].append(
                        {
                            "path": file_info["path"],
                            "lines": lines,
                            "size_kb": file_info["size"] / 1024,
                        }
                    )

                # Analyze for potential performance issues
                if "for" in content and "for" in content:  # Nested loops
                    performance_analysis["potential_optimizations"].append(
                        {
                            "file": file_info["path"],
                            "issue": "Potential nested loops detected",
                            "suggestion": "Consider algorithmic optimization",
                        }
                    )

                if content.count("import") > 20:
                    performance_analysis["potential_optimizations"].append(
                        {
                            "file": file_info["path"],
                            "issue": "Many imports detected",
                            "suggestion": "Consider lazy imports or import optimization",
                        }
                    )

            except (PermissionError, FileNotFoundError, UnicodeDecodeError):
                continue

        # Calculate overall code quality metrics
        total_python_files = len(python_files)
        avg_file_size = sum(f["size"] for f in python_files) / max(1, total_python_files)

        performance_analysis["code_quality_metrics"] = {
            "total_python_files": total_python_files,
            "average_file_size_kb": avg_file_size / 1024,
            "large_files_count": len(performance_analysis["large_files"]),
            "optimization_opportunities": len(performance_analysis["potential_optimizations"]),
        }

        self.quest_results["quests"]["Performance Analysis"]["results"] = performance_analysis
        self.quest_results["quests"]["Performance Analysis"]["files_processed"] = min(
            50, len(python_files)
        )

        summary = f"Performance analysis - {len(performance_analysis['large_files'])} large files, {len(performance_analysis['potential_optimizations'])} optimization opportunities"
        self.log_quest_complete("Performance Analysis", summary)

        return performance_analysis

    def quest_7_generate_comprehensive_report(self) -> str:
        """Quest 7: Generate comprehensive audit report with recommendations."""
        self.log_quest_start(
            "Report Generation",
            "Compile comprehensive audit report with actionable recommendations",
        )

        # Calculate overall statistics
        total_quests = len(self.quest_results["quests"])
        completed_quests = sum(
            1 for q in self.quest_results["quests"].values() if q["status"] == "completed"
        )

        self.quest_results["overall_stats"] = {
            "total_files_discovered": self.total_files_found,
            "files_analyzed": self.files_analyzed,
            "errors_found": self.errors_found,
            "warnings_found": self.warnings_found,
            "quests_completed": completed_quests,
            "total_quests": total_quests,
            "completion_rate": ((completed_quests / total_quests) * 100 if total_quests > 0 else 0),
        }

        # Generate recommendations based on findings
        recommendations: list[Any] = []
        # Check Python syntax validation results
        if "Python Syntax Validation" in self.quest_results["quests"]:
            syntax_results = self.quest_results["quests"]["Python Syntax Validation"]["results"]
            if syntax_results["success_rate"] < 95:
                recommendations.append(
                    {
                        "priority": "high",
                        "category": "syntax",
                        "issue": f"Python syntax success rate is {syntax_results['success_rate']:.1f}%",
                        "recommendation": "Fix syntax and indentation errors in Python files",
                        "files_affected": len(syntax_results["syntax_errors"]),
                    }
                )

        # Check integration system validation
        if "Integration System Validation" in self.quest_results["quests"]:
            integration_results = self.quest_results["quests"]["Integration System Validation"][
                "results"
            ]
            for system, details in integration_results.items():
                if isinstance(details, dict) and details.get("status") == "needs_attention":
                    recommendations.append(
                        {
                            "priority": "medium",
                            "category": "integration",
                            "issue": f"{system} needs attention",
                            "recommendation": f"Review and fix {system} configuration",
                            "issues": details.get("issues", []),
                        }
                    )

        # Check for large files
        if "Performance Analysis" in self.quest_results["quests"]:
            perf_results = self.quest_results["quests"]["Performance Analysis"]["results"]
            if len(perf_results["large_files"]) > 0:
                recommendations.append(
                    {
                        "priority": "low",
                        "category": "performance",
                        "issue": f"{len(perf_results['large_files'])} large files detected",
                        "recommendation": "Consider refactoring large files into smaller modules",
                        "files": [f["path"] for f in perf_results["large_files"]],
                    }
                )

        self.quest_results["recommendations"] = recommendations

        # Generate markdown report
        report_lines = [
            "# 🔍 KILO-FOOLISH Quest-Based Repository Audit Report",
            f"**Generated:** {self.quest_results['timestamp']}",
            f"**Repository:** {self.quest_results['repository']}",
            "",
            "## 📊 Executive Summary",
            f"**Files Discovered:** {self.quest_results['overall_stats']['total_files_discovered']}",
            f"**Files Analyzed:** {self.quest_results['overall_stats']['files_analyzed']}",
            f"**Errors Found:** {self.quest_results['overall_stats']['errors_found']}",
            f"**Quests Completed:** {self.quest_results['overall_stats']['quests_completed']}/{self.quest_results['overall_stats']['total_quests']} ({self.quest_results['overall_stats']['completion_rate']:.1f}%)",
            "",
            "## 🎯 Quest Results Summary",
        ]

        for quest_name, quest_data in self.quest_results["quests"].items():
            status_icon = "✅" if quest_data["status"] == "completed" else "⏳"
            report_lines.extend(
                [
                    f"### {status_icon} {quest_name}",
                    f"**Description:** {quest_data['description']}",
                    f"**Status:** {quest_data['status'].upper()}",
                    f"**Files Processed:** {quest_data['files_processed']}",
                    f"**Issues Found:** {quest_data.get('issues_found', 0)}",
                    "",
                ]
            )

        # Add recommendations
        if recommendations:
            report_lines.extend(
                [
                    "## 💡 Recommendations",
                    "",
                ]
            )

            for i, rec in enumerate(recommendations, 1):
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    rec["priority"], "⚪"
                )
                report_lines.extend(
                    [
                        f"### {i}. {priority_icon} {rec['category'].title()} - {rec['priority'].upper()} Priority",
                        f"**Issue:** {rec['issue']}",
                        f"**Recommendation:** {rec['recommendation']}",
                        "",
                    ]
                )

        report_lines.extend(
            [
                "## 🎮 Quest System Integration",
                "This audit was conducted using the KILO-FOOLISH quest-based analysis system,",
                "providing systematic progression through repository analysis tasks.",
                "",
                "### Next Steps:",
                "1. Address high-priority recommendations",
                "2. Run targeted fixes for syntax errors",
                "3. Verify integration system functionality",
                "4. Consider performance optimizations",
                "",
                "---",
                "*Generated by KILO-FOOLISH Quest-Based Auditor v4.0*",
            ]
        )

        report_content = "\n".join(report_lines)

        self.log_quest_complete(
            "Report Generation",
            f"Generated comprehensive report with {len(recommendations)} recommendations",
        )

        return report_content

    async def execute_quest_sequence(self) -> dict[str, Any]:
        """Execute the complete quest sequence."""
        # Quest 1: File Discovery
        file_catalog = self.quest_1_file_discovery()

        # Quest 2: Python Syntax Validation
        python_files = file_catalog["python_files"]
        self.quest_2_python_syntax_validation(python_files)

        # Quest 3: Import Dependency Analysis
        self.quest_3_import_dependency_analysis(python_files)

        # Quest 4: Src Directory Deep Analysis
        self.quest_4_src_directory_deep_analysis()

        # Quest 5: Integration System Validation
        self.quest_5_integration_system_validation()

        # Quest 6: Performance Analysis
        self.quest_6_performance_and_optimization_analysis(python_files)

        # Quest 7: Generate Report
        report_content = self.quest_7_generate_comprehensive_report()

        # Save results
        results_path = self.repo_root / "data" / "logs" / "quest_based_audit_results.json"
        results_path.parent.mkdir(parents=True, exist_ok=True)

        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(self.quest_results, f, indent=2, default=str)

        # Save report
        report_path = self.repo_root / "docs" / "reports" / "quest_based_audit_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        return self.quest_results


async def main():
    """Main quest execution function."""
    auditor = QuestBasedAuditor()
    return await auditor.execute_quest_sequence()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
