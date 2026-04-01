#!/usr/bin/env python3
"""🔍 KILO-FOOLISH Comprehensive Integration Validator.

Validates all system integrations and generates detailed reports.

This script runs all validation tests and creates comprehensive documentation
of the current system state.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Async"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def run_all_validations() -> dict[str, Any]:
    """Run all validation tests and generate reports."""
    repo_root = Path.cwd()

    validation_results: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "repository": str(repo_root),
        "validations": {},
        "summary": {},
    }

    # 1. Run quick integration check

    try:
        sys.path.append(str(repo_root / "src"))
        from diagnostics.quick_integration_check import quick_system_check

        quick_results = quick_system_check()
        validation_results["validations"]["quick_check"] = quick_results

    except Exception as e:
        validation_results["validations"]["quick_check"] = {"error": str(e)}

    # 2. Run ChatDev capabilities test

    try:
        from diagnostics.chatdev_capabilities_test import \
            ChatDevDevelopmentTester

        async def run_chatdev_test():
            tester = ChatDevDevelopmentTester()
            return await tester.run_comprehensive_test()

        chatdev_results = asyncio.run(run_chatdev_test())
        validation_results["validations"]["chatdev_test"] = chatdev_results

    except Exception as e:
        validation_results["validations"]["chatdev_test"] = {"error": str(e)}

    # 3. Run process manager check

    try:
        from system.process_manager import ProcessManager

        manager = ProcessManager()
        process_status = manager.get_terminal_status()
        processes = manager.scan_existing_processes()

        validation_results["validations"]["process_management"] = {
            "status": process_status,
            "processes": processes,
        }

    except Exception as e:
        validation_results["validations"]["process_management"] = {"error": str(e)}

    # 4. Generate comprehensive summary

    # Calculate overall health scores
    health_metrics: dict[str, Any] = {
        "ollama_status": "unknown",
        "chatdev_status": "unknown",
        "copilot_status": "unknown",
        "process_status": "unknown",
        "overall_score": 0,
    }

    # Extract Ollama status
    if (
        "quick_check" in validation_results["validations"]
        and "checks" in validation_results["validations"]["quick_check"]
    ):
        ollama_check = validation_results["validations"]["quick_check"]["checks"].get("ollama", {})
        if ollama_check.get("status") == "RUNNING":
            health_metrics["ollama_status"] = "operational"
            health_metrics["overall_score"] += 25
        elif ollama_check.get("status") in ["NOT_RUNNING", "API_ERROR"]:
            health_metrics["ollama_status"] = "needs_attention"
        else:
            health_metrics["ollama_status"] = "error"

    # Extract ChatDev status
    if (
        "chatdev_test" in validation_results["validations"]
        and "overall" in validation_results["validations"]["chatdev_test"]
    ):
        chatdev_score = validation_results["validations"]["chatdev_test"]["overall"].get("score", 0)
        if chatdev_score >= 80:
            health_metrics["chatdev_status"] = "excellent"
            health_metrics["overall_score"] += 25
        elif chatdev_score >= 60:
            health_metrics["chatdev_status"] = "good"
            health_metrics["overall_score"] += 20
        elif chatdev_score >= 40:
            health_metrics["chatdev_status"] = "fair"
            health_metrics["overall_score"] += 15
        else:
            health_metrics["chatdev_status"] = "needs_setup"
            health_metrics["overall_score"] += 5

    # Extract Copilot status
    if (
        "quick_check" in validation_results["validations"]
        and "checks" in validation_results["validations"]["quick_check"]
    ):
        copilot_files = validation_results["validations"]["quick_check"]["checks"].get(
            "copilot_files", {}
        )
        copilot_count = sum(1 for f in copilot_files.values() if f.get("exists", False))
        if copilot_count >= 2:
            health_metrics["copilot_status"] = "operational"
            health_metrics["overall_score"] += 25
        elif copilot_count >= 1:
            health_metrics["copilot_status"] = "partial"
            health_metrics["overall_score"] += 15
        else:
            health_metrics["copilot_status"] = "missing"

    # Extract Process status
    if (
        "process_management" in validation_results["validations"]
        and "status" in validation_results["validations"]["process_management"]
    ):
        process_data = validation_results["validations"]["process_management"]["status"]
        if (
            process_data.get("total_terminals", 0) > 0
            or process_data.get("total_background", 0) > 0
        ):
            health_metrics["process_status"] = "active"
            health_metrics["overall_score"] += 25
        else:
            health_metrics["process_status"] = "inactive"
            health_metrics["overall_score"] += 10

    validation_results["summary"] = health_metrics

    # Generate final status
    overall_score = health_metrics["overall_score"]
    if overall_score >= 80:
        overall_status = "🟢 EXCELLENT - All systems operational"
    elif overall_score >= 60:
        overall_status = "🟡 GOOD - Most systems functional"
    elif overall_score >= 40:
        overall_status = "🟠 FAIR - Some systems need attention"
    else:
        overall_status = "🔴 NEEDS WORK - Multiple systems require setup"

    # 5. Save comprehensive results

    # Save JSON results
    results_path = repo_root / "data" / "logs" / "comprehensive_validation_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(validation_results, f, indent=2, default=str)

    # Generate executive summary
    summary_lines = [
        "# 🔍 KILO-FOOLISH System Integration Executive Summary",
        f"**Generated:** {validation_results['timestamp']}",
        f"**Overall Status:** {overall_status}",
        "",
        "## 📊 System Health Overview",
        f"**🦙 Ollama LLMs:** {health_metrics['ollama_status'].upper()}",
        f"**🤖 ChatDev Integration:** {health_metrics['chatdev_status'].upper()}",
        f"**🤖 Copilot Enhancements:** {health_metrics['copilot_status'].upper()}",
        f"**⚙️ Process Management:** {health_metrics['process_status'].upper()}",
        "",
        "## 🎯 Key Findings",
    ]

    # Add key findings based on results
    if health_metrics["ollama_status"] == "operational":
        summary_lines.append("✅ **Ollama is running** - Local LLMs are available for development")
    else:
        summary_lines.append(
            "❌ **Ollama needs attention** - Start with `ollama serve` and install models"
        )

    if health_metrics["chatdev_status"] in ["excellent", "good"]:
        summary_lines.append(
            "✅ **ChatDev is functional** - Multi-agent development capabilities available"
        )
    else:
        summary_lines.append(
            "❌ **ChatDev needs setup** - Install ChatDev and configure integration"
        )

    if health_metrics["copilot_status"] == "operational":
        summary_lines.append(
            "✅ **Copilot enhancements active** - Enhanced development workflow available"
        )
    else:
        summary_lines.append(
            "❌ **Copilot enhancements incomplete** - Review enhancement bridge setup"
        )

    summary_lines.extend(
        [
            "",
            "## 💡 Immediate Action Items",
        ]
    )

    action_items: list[Any] = []
    if health_metrics["ollama_status"] != "operational":
        action_items.append("Start Ollama service and install recommended models")
    if health_metrics["chatdev_status"] not in ["excellent", "good"]:
        action_items.append("Install and configure ChatDev integration")
    if health_metrics["copilot_status"] != "operational":
        action_items.append("Complete Copilot enhancement bridge setup")

    if not action_items:
        summary_lines.append("🎉 **No immediate actions needed** - All systems are operational!")
    else:
        for i, item in enumerate(action_items, 1):
            summary_lines.append(f"{i}. {item}")

    summary_lines.extend(
        [
            "",
            "## 🔗 Integration Capabilities Available",
            "",
            "### 🦙 Ollama Local LLMs",
            "- Privacy-first local AI models",
            "- Multiple model support (phi, mistral, codellama)",
            "- Direct API integration",
            "",
            "### 🤖 ChatDev Multi-Agent Development",
            "- Collaborative AI development teams",
            "- Structured development lifecycle",
            "- Code review and quality assurance",
            "- Project generation and management",
            "",
            "### 🤖 Enhanced Copilot Integration",
            "- Context-aware development assistance",
            "- Repository consciousness integration",
            "- Enhanced prompt engineering",
            "- Workflow optimization",
            "",
            "## 📈 Development Workflow Recommendations",
            "",
            "1. **Use Ollama for privacy-sensitive development**",
            "2. **Leverage ChatDev for new project initialization**",
            "3. **Combine Copilot with ChatDev for optimal results**",
            "4. **Utilize multi-agent approaches for complex problems**",
            "5. **Take advantage of local AI for faster iteration**",
            "",
            "---",
            f"*Detailed results: `{results_path}`*",
            "*Integration reports available in: `docs/reports/`*",
        ]
    )

    summary_path = repo_root / "docs" / "reports" / "integration_executive_summary.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    return validation_results


if __name__ == "__main__":
    results = run_all_validations()
