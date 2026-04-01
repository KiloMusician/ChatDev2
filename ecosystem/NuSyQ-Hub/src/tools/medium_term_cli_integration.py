"""CLI Integration Module for Medium-Term Enhancements.

Provides command handlers for all 4 new features.

[OmniTag: cli_integration, medium_term_enhancements, orchestration]
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ai.sns_llm_fine_tuner import SNSLLMFineTuner
from src.evaluation.performance_benchmark import PerformanceBenchmark
from src.integration.cross_repo_sync import CrossRepoSNSSynchronizer
from src.ui.vscode_metrics_ui import VSCodeMetricsUI


class MediumTermEnhancementsIntegration:
    """Integration point for all medium-term enhancement CLI commands."""

    def __init__(self, state_dir: Path = Path("state")):
        """Initialize integration.

        Args:
            state_dir: State directory for all modules
        """
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    # ===== LLM Fine-Tuning Commands =====

    def handle_llm_fine_tuning(
        self,
        action: str = "prepare",
        model_name: str = "qwen2.5-coder",
    ) -> dict[str, Any]:
        """Handle LLM fine-tuning actions.

        Args:
            action: Action to perform (prepare, estimate, report)
            model_name: Model to fine-tune

        Returns:
            Result dictionary
        """
        fine_tuner = SNSLLMFineTuner(model_name=model_name, state_dir=self.state_dir)

        if action == "prepare":
            dataset_path = fine_tuner.prepare_fine_tuning_dataset()
            return {
                "status": "success",
                "action": "prepare",
                "dataset_path": dataset_path,
                "message": "Fine-tuning dataset prepared with augmentation",
            }

        elif action == "estimate":
            impact = fine_tuner.estimate_training_impact()
            return {
                "status": "success",
                "action": "estimate",
                "impact": impact,
            }

        elif action == "report":
            report = fine_tuner.generate_training_report()
            return {
                "status": "success",
                "action": "report",
                "report": report,
            }

        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}. Use: prepare, estimate, or report",
            }

    # ===== VS Code Metrics UI Commands =====

    def handle_vscode_metrics(
        self,
        action: str = "generate",
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """Handle VS Code metrics UI actions.

        Args:
            action: Action to perform (generate, config, export)
            output_path: Output file path for HTML generation

        Returns:
            Result dictionary
        """
        ui = VSCodeMetricsUI(state_dir=self.state_dir)

        if action == "generate":
            html = ui.generate_html_ui()
            output_file = Path(output_path or self.state_dir / "sns_metrics.html")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html)

            return {
                "status": "success",
                "action": "generate",
                "output_file": str(output_file),
                "message": "VS Code metrics dashboard HTML generated",
            }

        elif action == "config":
            config = ui.generate_extension_config()
            config_file = Path(output_path or self.state_dir / "extension_config.json")
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text(json.dumps(config, indent=2))

            return {
                "status": "success",
                "action": "config",
                "config_file": str(config_file),
                "message": "VS Code extension configuration generated",
            }

        elif action == "export":
            ui.save_webview_to_file(Path(output_path) if output_path else None)
            return {
                "status": "success",
                "action": "export",
                "message": "Webview exported to file",
            }

        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}. Use: generate, config, or export",
            }

    # ===== Cross-Repo Sync Commands =====

    def handle_cross_repo_sync(
        self,
        action: str = "status",
        hub_path: str | None = None,
        simverse_path: str | None = None,
    ) -> dict[str, Any]:
        """Handle cross-repository synchronization actions.

        Args:
            action: Action to perform (status, propagate, hooks, report)
            hub_path: Path to NuSyQ-Hub
            simverse_path: Path to SimulatedVerse

        Returns:
            Result dictionary
        """
        hub_path = Path(hub_path) if hub_path else Path.cwd()
        simverse_path = Path(simverse_path) if simverse_path else Path.cwd()

        sync = CrossRepoSNSSynchronizer(
            hub_path=hub_path,
            simverse_path=simverse_path,
        )

        if action == "status":
            changes = sync.detect_definition_changes()
            return {
                "status": "success",
                "action": "status",
                "changes_detected": {
                    "added": len(changes["added"]),
                    "removed": len(changes["removed"]),
                    "modified": len(changes["modified"]),
                },
                "details": changes,
            }

        elif action == "propagate":
            result = sync.propagate_definitions_to_repos()
            return {
                "status": "success",
                "action": "propagate",
                "repos_updated": result["repos_updated"],
                "errors": result.get("errors", []),
            }

        elif action == "hooks":
            result = sync.install_sync_hooks()
            return {
                "status": "success",
                "action": "hooks",
                "hooks_installed": result["hooks_installed"],
                "errors": result.get("errors", []),
            }

        elif action == "report":
            report = sync.generate_sync_report()
            return {
                "status": "success",
                "action": "report",
                "report": report,
            }

        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}. Use: status, propagate, hooks, or report",
            }

    # ===== Performance Benchmark Commands =====

    def handle_performance_benchmark(
        self,
        action: str = "prepare",
        sns_converter: callable | None = None,
    ) -> dict[str, Any]:
        """Handle performance benchmarking actions.

        Args:
            action: Action to perform (prepare, run, summary, report)
            sns_converter: SNS conversion function for benchmarking

        Returns:
            Result dictionary
        """
        benchmark = PerformanceBenchmark(state_dir=self.state_dir)

        if action == "prepare":
            dataset = benchmark.create_test_dataset()
            return {
                "status": "success",
                "action": "prepare",
                "categories": list(dataset.keys()),
                "total_tests": sum(len(tests) for tests in dataset.values()),
                "message": "Benchmark test dataset prepared",
            }

        elif action == "run" and sns_converter:
            results = benchmark.benchmark_sns_conversion(sns_converter)
            benchmark.results = results
            benchmark.save_results()

            return {
                "status": "success",
                "action": "run",
                "benchmarks_completed": len(results),
                "results_file": str(benchmark.results_file),
            }

        elif action == "summary":
            summary = benchmark.generate_summary()
            return {
                "status": "success",
                "action": "summary",
                "summary": summary,
            }

        elif action == "report":
            report = benchmark.generate_benchmark_report()
            report_file = self.state_dir / "benchmark_report.md"
            report_file.write_text(report)

            return {
                "status": "success",
                "action": "report",
                "report_file": str(report_file),
                "message": "Benchmark report generated",
            }

        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action} or missing converter. Use: prepare, run, summary, or report",
            }

    # ===== Dashboard Command =====

    def handle_metrics_dashboard(self) -> dict[str, Any]:
        """Display metrics dashboard.

        Returns:
            Dashboard data
        """
        ui = VSCodeMetricsUI(state_dir=self.state_dir)
        benchmark = PerformanceBenchmark(state_dir=self.state_dir)

        dashboard = {
            "status": "success",
            "metrics": benchmark.generate_summary(),
            "ui_config": ui.generate_extension_config(),
            "timestamp": json.dumps({"now": str(benchmark.state_dir)})[:50],
        }

        return dashboard

    # ===== Status Check =====

    def get_medium_term_status(self) -> dict[str, Any]:
        """Get status of all medium-term enhancements.

        Returns:
            Status of all 4 features
        """
        return {
            "status": "operational",
            "timestamp": "2025-12-30",
            "enhancements": {
                "llm_fine_tuning": {
                    "enabled": True,
                    "module": "src.ai.sns_llm_fine_tuner",
                    "actions": ["prepare", "estimate", "report"],
                },
                "vscode_metrics_ui": {
                    "enabled": True,
                    "module": "src.ui.vscode_metrics_ui",
                    "actions": ["generate", "config", "export"],
                },
                "cross_repo_sync": {
                    "enabled": True,
                    "module": "src.integration.cross_repo_sync",
                    "actions": ["status", "propagate", "hooks", "report"],
                },
                "performance_benchmark": {
                    "enabled": True,
                    "module": "src.evaluation.performance_benchmark",
                    "actions": ["prepare", "run", "summary", "report"],
                },
            },
        }
