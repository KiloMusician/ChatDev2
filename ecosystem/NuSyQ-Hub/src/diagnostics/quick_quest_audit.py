#!/usr/bin/env python3
"""🔍 KILO-FOOLISH Quick Quest Audit - Simplified Version.

Immediate systematic file analysis with quest progression.
"""

import ast
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def main() -> None:
    """Execute simplified quest-based audit."""
    repo_root = Path.cwd()

    results: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "repository": str(repo_root),
        "quests": {},
    }

    # QUEST 1: File Discovery

    file_counts = {
        "python": 0,
        "markdown": 0,
        "json": 0,
        "powershell": 0,
        "src_python": 0,
    }

    python_files: list[Any] = []
    src_files: list[Any] = []
    for root, dirs, files in os.walk(repo_root):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".vscode", "node_modules"}]

        for file in files:
            file_path = Path(root) / file
            relative_path = file_path.relative_to(repo_root)

            if file.endswith(".py"):
                file_counts["python"] += 1
                python_files.append(str(relative_path))
                if "src" in relative_path.parts:
                    file_counts["src_python"] += 1
                    src_files.append(str(relative_path))
            elif file.endswith(".md"):
                file_counts["markdown"] += 1
            elif file.endswith(".json"):
                file_counts["json"] += 1
            elif file.endswith(".ps1"):
                file_counts["powershell"] += 1

    results["quests"]["file_discovery"] = {
        "status": "completed",
        "results": file_counts,
        "python_files": python_files[:20],  # First 20 for brevity
        "src_files": src_files,
    }

    # QUEST 2: Python Syntax Validation

    syntax_results: dict[str, Any] = {
        "valid_files": 0,
        "syntax_errors": 0,
        "import_errors": 0,
        "error_files": [],
    }

    # Test first 30 Python files for performance
    test_files = python_files[:30]
    for _i, file_path in enumerate(test_files):
        full_path = repo_root / file_path

        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(full_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                syntax_results["valid_files"] += 1
            else:
                error_type = "syntax_error"
                if (
                    "importerror" in result.stderr.lower()
                    or "modulenotfounderror" in result.stderr.lower()
                ):
                    syntax_results["import_errors"] += 1
                    error_type = "import_error"
                else:
                    syntax_results["syntax_errors"] += 1

                syntax_results["error_files"].append(
                    {
                        "file": file_path,
                        "type": error_type,
                        "error": result.stderr[:200],  # Truncate long errors
                    }
                )

        except Exception as e:
            syntax_results["error_files"].append(
                {
                    "file": file_path,
                    "type": "exception",
                    "error": str(e),
                }
            )

    success_rate = (syntax_results["valid_files"] / len(test_files)) * 100 if test_files else 0

    results["quests"]["syntax_validation"] = {
        "status": "completed",
        "results": syntax_results,
        "success_rate": success_rate,
        "files_tested": len(test_files),
    }

    # QUEST 3: Src Directory Analysis

    src_analysis: dict[str, Any] = {
        "subdirectories": {},
        "total_lines": 0,
        "total_functions": 0,
        "total_classes": 0,
    }

    src_path = repo_root / "src"
    if src_path.exists():
        for subdir in src_path.iterdir():
            if subdir.is_dir():
                subdir_info: dict[str, Any] = {
                    "python_files": 0,
                    "lines": 0,
                    "functions": 0,
                    "classes": 0,
                }

                for py_file in subdir.rglob("*.py"):
                    subdir_info["python_files"] += 1

                    try:
                        with open(py_file, encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            lines = content.count("\n") + 1
                            subdir_info["lines"] += lines
                            src_analysis["total_lines"] += lines

                        # Count functions and classes
                        try:
                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    subdir_info["functions"] += 1
                                    src_analysis["total_functions"] += 1
                                elif isinstance(node, ast.ClassDef):
                                    subdir_info["classes"] += 1
                                    src_analysis["total_classes"] += 1
                        except SyntaxError:
                            logger.debug("Suppressed SyntaxError", exc_info=True)

                    except (PermissionError, FileNotFoundError, UnicodeDecodeError):
                        logger.debug(
                            "Suppressed FileNotFoundError/PermissionError/UnicodeDecodeError",
                            exc_info=True,
                        )

                src_analysis["subdirectories"][subdir.name] = subdir_info

    results["quests"]["src_analysis"] = {
        "status": "completed",
        "results": src_analysis,
    }

    # QUEST 4: Integration System Check

    integration_files = {
        "ollama": [
            "src/integration/ollama_integration.py",
            "src/ai/ollama_chatdev_integrator.py",
        ],
        "chatdev": [
            "src/integration/chatdev_llm_adapter.py",
            "src/integration/chatdev_launcher.py",
        ],
        "copilot": [
            ".copilot/copilot_enhancement_bridge.py",
            ".github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md",
        ],
    }

    integration_status: dict[str, Any] = {}
    for system, files in integration_files.items():
        system_status: dict[str, Any] = {"present": 0, "total": len(files), "files": []}

        for file_path_str in files:
            full_path = repo_root / file_path_str
            if full_path.exists():
                system_status["present"] += 1
                system_status["files"].append({"path": file_path_str, "status": "present"})
            else:
                system_status["files"].append({"path": file_path_str, "status": "missing"})

        system_status["operational"] = system_status["present"] >= (system_status["total"] // 2)
        integration_status[system] = system_status

    results["quests"]["integration_check"] = {
        "status": "completed",
        "results": integration_status,
    }

    # QUEST 5: Generate Summary Report

    # Calculate overall health score
    health_factors = [
        success_rate / 100,  # Syntax success rate
        file_counts["src_python"] / max(1, file_counts["python"]),  # Src organization
        sum(s["operational"] for s in integration_status.values())
        / len(integration_status),  # Integration health
    ]

    overall_health = sum(health_factors) / len(health_factors) * 100

    # Generate recommendations
    recommendations: list[Any] = []
    if success_rate < 90:
        recommendations.append("🔧 Fix Python syntax and import errors")

    if file_counts["src_python"] < file_counts["python"] * 0.5:
        recommendations.append("📁 Consider organizing more Python files into src/ structure")

    for system, status in integration_status.items():
        if not status["operational"]:
            recommendations.append(f"🔗 Review {system} integration setup")

    if not recommendations:
        recommendations.append("🎉 Repository is in excellent condition!")

    # Save results
    results_path = repo_root / "data" / "logs" / "quick_quest_audit.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    # Generate summary report
    report_lines = [
        "# 🔍 KILO-FOOLISH Quick Quest Audit Report",
        f"**Generated:** {results['timestamp']}",
        f"**Repository Health:** {overall_health:.1f}%",
        "",
        "## 📊 Summary Statistics",
        f"- **Python Files:** {file_counts['python']} ({file_counts['src_python']} in src/)",
        f"- **Syntax Success Rate:** {success_rate:.1f}%",
        f"- **Total Lines in src/:** {src_analysis['total_lines']:,}",
        f"- **Functions:** {src_analysis['total_functions']}",
        f"- **Classes:** {src_analysis['total_classes']}",
        "",
        "## 🔗 Integration Status",
    ]

    for system, status in integration_status.items():
        status_icon = "✅" if status["operational"] else "❌"
        report_lines.append(
            f"- **{system.title()}:** {status_icon} {status['present']}/{status['total']} files present"
        )

    report_lines.extend(
        [
            "",
            "## 💡 Recommendations",
        ]
    )

    for rec in recommendations:
        report_lines.append(f"- {rec}")

    report_lines.extend(
        [
            "",
            f"**Detailed Results:** `{results_path}`",
            "",
            "*Generated by KILO-FOOLISH Quest-Based Auditor*",
        ]
    )

    report_content = "\n".join(report_lines)

    report_path = repo_root / "docs" / "reports" / "quick_quest_audit_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        f.write(report_content)

    # Final Summary
    for _i, _rec in enumerate(recommendations[:3], 1):
        pass


if __name__ == "__main__":
    main()
