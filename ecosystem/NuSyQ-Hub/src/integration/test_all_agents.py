"""Comprehensive Agent Test Suite - SimulatedVerse 9 Agent Validation.

Tests all agents using async file-based protocol with role-appropriate tasks.
Creates detailed test reports and validates proof-gated outputs.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AgentTestSuite:
    """Comprehensive testing for all SimulatedVerse agents."""

    def __init__(
        self,
        simulatedverse_root: str | None = None,
    ) -> None:
        if simulatedverse_root is None:
            simulatedverse_root = os.environ.get("SIMULATEDVERSE_PATH")
            if simulatedverse_root is None:
                simulatedverse_root = str(
                    Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
                )
        self.root = Path(simulatedverse_root)
        self.tasks_dir = self.root / "tasks"
        self.results_dir = self.root / "results"
        self.reports_dir = self.root / "test_reports"

        self.reports_dir.mkdir(exist_ok=True)

        # Define agent test scenarios
        self.test_scenarios = {
            "alchemist": {
                "content": "Transform CSV data to JSON format for analysis",
                "metadata": {
                    "input_format": "csv",
                    "output_format": "json",
                    "sample_data": "id,name,value\n1,test,100\n2,demo,200",
                },
            },
            "artificer": {
                "content": "Scaffold a new agent template structure",
                "metadata": {
                    "template_type": "agent",
                    "structure": ["manifest.yaml", "index.ts", "README.md"],
                },
            },
            "council": {
                "content": "Vote on priority of 3 cleanup tasks from theater audit",
                "metadata": {
                    "proposals": [
                        {"id": "console_cleanup", "priority": "medium"},
                        {"id": "progress_bars", "priority": "high"},
                        {"id": "todo_conversion", "priority": "medium"},
                    ],
                },
            },
            "culture-ship": {
                "content": "Review NuSyQ-Hub theater score: 0.082 (15962 hits in 194655 lines)",
                "metadata": {
                    "project": "NuSyQ-Hub",
                    "score": 0.082,
                    "hits": 15962,
                    "lines": 194655,
                    "patterns": {
                        "console_spam": 93,
                        "fake_progress": 219,
                        "todo_comments": 1847,
                    },
                },
            },
            "intermediary": {
                "content": "Route coordination request between Culture Ship and Librarian",
                "metadata": {
                    "source_agent": "culture-ship",
                    "target_agent": "librarian",
                    "message_type": "knowledge_request",
                },
            },
            "librarian": {
                "content": "Index all project documentation files",
                "metadata": {"task": "index", "scope": "all", "output": "summary"},
            },
            "party": {
                "content": "Orchestrate bundle of 3 small cleanup tasks",
                "metadata": {
                    "tasks": [
                        "Remove unused imports",
                        "Format code files",
                        "Update documentation",
                    ],
                    "parallel": True,
                },
            },
            "redstone": {
                "content": "Evaluate logic network for agent communication flow",
                "metadata": {
                    "network_type": "agent_communication",
                    "nodes": ["culture-ship", "librarian", "council"],
                },
            },
            "zod": {
                "content": "Validate schema compliance across data files",
                "metadata": {
                    "schemas": ["AgentManifest", "TaskInput", "PUSchema"],
                    "strict_mode": True,
                },
            },
        }

    def submit_test_task(self, agent_id: str, scenario: dict[str, Any]) -> str:
        """Submit a test task for an agent."""
        task_id = f"{agent_id}_test_{int(time.time() * 1000)}"

        task_data = {
            "task_id": task_id,
            "agent_id": agent_id,
            "content": scenario["content"],
            "metadata": scenario.get("metadata", {}),
            "ask": {"payload": scenario.get("metadata", {})},
            "t": int(time.time() * 1000),
            "utc": int(time.time() * 1000),
            "entropy": 0.5,
            "budget": 0.95,
            "submitted_at": datetime.now().isoformat(),
            "test_mode": True,
        }

        task_file = self.tasks_dir / f"{task_id}.json"
        task_file.write_text(json.dumps(task_data, indent=2))

        logger.info("  📤 Submitted test: %s", task_file.name)
        return task_id

    def wait_for_result(self, task_id: str, timeout: int = 30) -> dict[str, Any] | None:
        """Wait for task result with progress indicators."""
        result_file = self.results_dir / f"{task_id}_result.json"

        start_time = time.time()
        dots = 0

        while time.time() - start_time < timeout:
            if result_file.exists():
                result: dict[str, Any] = json.loads(result_file.read_text())
                logger.info("  ✅ Result received (%.1fs)", (time.time() - start_time))
                return result

            # Progress indicator
            if int(time.time() - start_time) > dots:
                logger.info("  ⏳" + "." * (dots + 1), end="\r")
                dots += 1

            time.sleep(0.5)

        logger.info("  ❌ Timeout after %ss", timeout)
        return None

    def validate_result(self, agent_id: str, result: dict[str, Any]) -> dict[str, Any]:
        """Validate agent result structure and content."""
        validation = {
            "agent_id": agent_id,
            "valid": False,
            "issues": [],
            "strengths": [],
        }

        # Check basic structure
        if not result.get("result", {}).get("ok"):
            validation["issues"].append("Result not marked as ok")
        else:
            validation["strengths"].append("Task completed successfully")

        # Check for effects
        effects = result.get("result", {}).get("effects", {})
        if not effects:
            validation["issues"].append("No effects reported")
        else:
            validation["strengths"].append(f"Effects present: {list(effects.keys())}")

        # Check for artifact path (if applicable)
        if "artifactPath" in effects:
            artifact_path = Path(effects["artifactPath"])
            if artifact_path.exists():
                validation["strengths"].append(f"Artifact created: {artifact_path.name}")
            else:
                validation["issues"].append(f"Artifact path doesn't exist: {artifact_path}")

        # Agent-specific validations
        if (
            agent_id == "culture-ship"
            and "stateDelta" in effects
            and "pusGenerated" in effects["stateDelta"]
        ):
            pus_count = effects["stateDelta"]["pusGenerated"]
            validation["strengths"].append(f"Generated {pus_count} PUs")

        if (
            agent_id == "librarian"
            and "stateDelta" in effects
            and "docsIndexed" in effects["stateDelta"]
        ):
            docs_count = effects["stateDelta"]["docsIndexed"]
            validation["strengths"].append(f"Indexed {docs_count} documents")

        validation["valid"] = len(validation["issues"]) == 0
        return validation

    def test_agent(self, agent_id: str) -> dict[str, Any]:
        """Test a single agent with its scenario."""
        logger.info("\n🧪 Testing Agent: %s", agent_id.upper())
        logger.info("  📋 Scenario: %s...", self.test_scenarios[agent_id]["content"][:60])

        test_report = {
            "agent_id": agent_id,
            "test_time": datetime.now().isoformat(),
            "status": "unknown",
            "duration_seconds": 0,
            "validation": None,
            "result": None,
        }

        start_time = time.time()

        try:
            # Submit test task
            task_id = self.submit_test_task(agent_id, self.test_scenarios[agent_id])

            # Wait for result
            result = self.wait_for_result(task_id)

            test_report["duration_seconds"] = time.time() - start_time

            if result:
                test_report["status"] = "completed"
                test_report["result"] = result

                # Validate result
                validation = self.validate_result(agent_id, result)
                test_report["validation"] = validation

                if validation["valid"]:
                    logger.info("  ✅ PASS - %s", ", ".join(validation["strengths"]))
                else:
                    logger.info("  ⚠️  ISSUES - %s", ", ".join(validation["issues"]))
                    for strength in validation["strengths"]:
                        logger.info("     ✓ %s", strength)
            else:
                test_report["status"] = "timeout"
                logger.info("  ❌ FAIL - No result received")

        except Exception as e:
            test_report["status"] = "error"
            test_report["error"] = str(e)
            logger.info("  ❌ ERROR - %s", str(e))

        return test_report

    def run_all_tests(self) -> dict[str, Any]:
        """Run comprehensive test suite for all agents."""
        logger.info("🚀 SimulatedVerse Agent Test Suite - Comprehensive Validation")
        logger.info("📂 Tasks Directory: %s", self.tasks_dir)
        logger.info("📂 Results Directory: %s", self.results_dir)
        logger.info("📊 Testing %s agents", len(self.test_scenarios))

        suite_start = time.time()
        all_reports: dict[str, Any] = {}

        for agent_id in sorted(self.test_scenarios.keys()):
            report = self.test_agent(agent_id)
            all_reports[agent_id] = report
            time.sleep(1)  # Brief pause between tests

        suite_duration = time.time() - suite_start

        # Generate summary
        summary = {
            "total_agents": len(all_reports),
            "passed": sum(
                1
                for r in all_reports.values()
                if r.get("validation") and r["validation"].get("valid")
            ),
            "failed": sum(1 for r in all_reports.values() if r["status"] in ["timeout", "error"]),
            "warnings": sum(
                1
                for r in all_reports.values()
                if r.get("validation")
                and not r["validation"].get("valid")
                and r["status"] == "completed"
            ),
            "total_duration": suite_duration,
            "timestamp": datetime.now().isoformat(),
            "agent_reports": all_reports,
        }

        # Print summary
        logger.info("📊 TEST SUITE SUMMARY")
        logger.info("✅ Passed:   %s/%s", summary["passed"], summary["total_agents"])
        logger.info("⚠️  Warnings: %s/%s", summary["warnings"], summary["total_agents"])
        logger.info("❌ Failed:   %s/%s", summary["failed"], summary["total_agents"])
        logger.info("⏱️  Duration: %.1fs", suite_duration)

        # Save detailed report
        report_file = self.reports_dir / f"agent_test_report_{int(time.time())}.json"
        report_file.write_text(json.dumps(summary, indent=2))
        logger.info("\n📄 Detailed report: %s", report_file)

        return summary


if __name__ == "__main__":
    suite = AgentTestSuite()
    results = suite.run_all_tests()

    # Print any failures for quick review
    failures = [
        (aid, report)
        for aid, report in results["agent_reports"].items()
        if report["status"] in ["timeout", "error"]
    ]

    if failures:
        logger.info("❌ FAILED AGENTS - DETAILS")
        for agent_id, report in failures:
            logger.info("\n%s:", agent_id)
            logger.info("  Status: %s", report["status"])
            if "error" in report:
                logger.info("  Error: %s", report["error"])
