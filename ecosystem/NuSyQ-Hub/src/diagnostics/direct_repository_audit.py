#!/usr/bin/env python3
"""🔍 KILO-FOOLISH Direct Repository Audit.

Direct examination of repository structure and file health.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import ast
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def analyze_python_file(file_path):
    """Analyze a single Python file."""
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Basic metrics
        lines = content.count("\n") + 1
        size_kb = os.path.getsize(file_path) / 1024

        # AST analysis
        functions = 0
        classes = 0
        imports: list[Any] = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions += 1
                elif isinstance(node, ast.ClassDef):
                    classes += 1
                elif isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)

        except SyntaxError as e:
            return {
                "status": "syntax_error",
                "error": str(e),
                "lines": lines,
                "size_kb": size_kb,
            }

        return {
            "status": "valid",
            "lines": lines,
            "size_kb": size_kb,
            "functions": functions,
            "classes": classes,
            "imports": len(imports),
            "import_list": imports[:10],  # First 10 imports
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "lines": 0,
            "size_kb": 0,
        }


def main():
    """Execute direct repository audit."""
    repo_root = Path.cwd()
    audit_results: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "repository": str(repo_root),
        "src_analysis": {},
        "file_summary": {},
        "integration_check": {},
        "overall_health": {},
    }

    # Analyze src directory

    src_path = repo_root / "src"
    src_stats: dict[str, Any] = {
        "subdirectories": {},
        "total_python_files": 0,
        "total_lines": 0,
        "total_functions": 0,
        "total_classes": 0,
    }

    if src_path.exists():
        for subdir in src_path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("_"):
                subdir_stats: dict[str, Any] = {
                    "python_files": [],
                    "file_count": 0,
                    "total_lines": 0,
                    "total_functions": 0,
                    "total_classes": 0,
                    "syntax_errors": 0,
                    "valid_files": 0,
                }

                for py_file in subdir.rglob("*.py"):
                    if py_file.name == "__init__.py":
                        continue

                    relative_path = py_file.relative_to(repo_root)

                    analysis = analyze_python_file(py_file)
                    analysis["path"] = str(relative_path)

                    subdir_stats["python_files"].append(analysis)
                    subdir_stats["file_count"] += 1

                    if analysis["status"] == "valid":
                        subdir_stats["valid_files"] += 1
                        subdir_stats["total_lines"] += analysis["lines"]
                        subdir_stats["total_functions"] += analysis["functions"]
                        subdir_stats["total_classes"] += analysis["classes"]
                    elif analysis["status"] == "syntax_error":
                        subdir_stats["syntax_errors"] += 1

                src_stats["subdirectories"][subdir.name] = subdir_stats
                src_stats["total_python_files"] += subdir_stats["file_count"]
                src_stats["total_lines"] += subdir_stats["total_lines"]
                src_stats["total_functions"] += subdir_stats["total_functions"]
                src_stats["total_classes"] += subdir_stats["total_classes"]

    audit_results["src_analysis"] = src_stats

    # Check key integration files

    integration_files = {
        "ollama": [
            "src/integration/ollama_integration.py",
            "src/ai/ollama_chatdev_integrator.py",
            "src/integration/Update-ChatDev-to-use-Ollama.py",
        ],
        "chatdev": [
            "src/integration/chatdev_llm_adapter.py",
            "src/integration/chatdev_launcher.py",
            "src/orchestration/chatdev_testing_chamber.py",
        ],
        "copilot": [
            ".copilot/copilot_enhancement_bridge.py",
            ".github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md",
        ],
        "core": [
            "src/core/ai_coordinator.py",
            "src/core/ArchitectureScanner.py",
            "src/consciousness/consciousness_bridge.py",
        ],
    }

    integration_status: dict[str, Any] = {}
    for system, files in integration_files.items():
        system_status: dict[str, Any] = {
            "files_present": 0,
            "files_total": len(files),
            "file_details": [],
        }

        for file_path in files:
            full_path = repo_root / file_path
            if full_path.exists():
                analysis = (
                    analyze_python_file(full_path)
                    if file_path.endswith(".py")
                    else {
                        "status": "present",
                        "lines": 0,
                        "size_kb": full_path.stat().st_size / 1024,
                    }
                )
                system_status["files_present"] += 1
                system_status["file_details"].append(
                    {
                        "path": file_path,
                        "status": "present",
                        "analysis": analysis,
                    }
                )
                "✅" if analysis["status"] in ["valid", "present"] else "⚠️"
            else:
                system_status["file_details"].append(
                    {
                        "path": file_path,
                        "status": "missing",
                        "analysis": None,
                    }
                )

        system_status["operational"] = system_status["files_present"] >= (
            system_status["files_total"] // 2
        )
        integration_status[system] = system_status

    audit_results["integration_check"] = integration_status

    # Generate summary

    # Calculate health metrics
    total_src_files = src_stats["total_python_files"]
    valid_src_files = sum(subdir["valid_files"] for subdir in src_stats["subdirectories"].values())
    src_health = (valid_src_files / total_src_files) * 100 if total_src_files > 0 else 0

    operational_integrations = sum(
        1 for status in integration_status.values() if status["operational"]
    )
    integration_health = (operational_integrations / len(integration_status)) * 100

    overall_health = (src_health + integration_health) / 2

    audit_results["overall_health"] = {
        "src_health": src_health,
        "integration_health": integration_health,
        "overall_score": overall_health,
        "total_python_files": total_src_files,
        "valid_python_files": valid_src_files,
        "operational_integrations": operational_integrations,
    }

    # Detailed breakdown
    for subdir_stats in src_stats["subdirectories"].values():
        subdir_stats["valid_percent"] = (
            subdir_stats["valid_files"] / max(1, subdir_stats["file_count"])
        ) * 100

    for _system, status in integration_status.items():
        status["status_emoji"] = "✅" if status["operational"] else "❌"

    # Save results
    results_path = repo_root / "data" / "logs" / "direct_repository_audit.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2, default=str)

    # Generate recommendations
    recommendations: list[Any] = []
    if src_health < 90:
        recommendations.append("🔧 Fix Python syntax errors in src/ directory")

    if integration_health < 75:
        recommendations.append("🔗 Review integration system setup")

    if src_stats["total_python_files"] > 50:
        recommendations.append("📁 Consider code organization review for large codebase")

    if overall_health > 80:
        recommendations.append("🎉 Repository is in excellent condition!")

    for _rec in recommendations:
        pass

    return audit_results


if __name__ == "__main__":
    main()
