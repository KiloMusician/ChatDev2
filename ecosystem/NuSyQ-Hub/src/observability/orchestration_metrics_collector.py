#!/usr/bin/env python3
"""Orchestration Performance Monitoring System.

Tracks, aggregates, and reports on multi-agent orchestration metrics.
"""

import json
import logging
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))


class OrchestrationMetrics:
    """Collect and analyze orchestration performance metrics."""

    def __init__(self, quest_log_path: Path):
        """Initialize OrchestrationMetrics with quest_log_path."""
        self.quest_log = quest_log_path
        self.metrics = defaultdict(list)
        self.load_quest_log()

    def load_quest_log(self):
        """Load and parse orchestration events from quest log."""
        if not self.quest_log.exists():
            logger.warning(f"[WARN] Quest log not found: {self.quest_log}")
            return

        with open(self.quest_log) as f:
            lines = f.readlines()

        for line in lines:
            try:
                entry = json.loads(line)
                task_type = entry.get("task_type", "unknown")

                # Extract metrics by task type
                if task_type in [
                    "orchestration_test",
                    "async_orchestration_test",
                    "ai_analysis",
                    "multi_model_comparison",
                ]:
                    result = entry.get("result", {})

                    if task_type == "async_orchestration_test":
                        self.metrics["async_parallel"].append(
                            {
                                "timestamp": entry.get("timestamp"),
                                "agents": result.get("total_agents"),
                                "successful": result.get("successful"),
                                "elapsed": result.get("elapsed_seconds"),
                                "tokens": result.get("total_tokens"),
                                "speedup": result.get("speedup"),
                            }
                        )
                    elif task_type == "multi_model_comparison":
                        results = result.get("results", [])
                        for model_result in results:
                            self.metrics["single_agent"].append(
                                {
                                    "model": model_result.get("model"),
                                    "tokens": model_result.get("tokens"),
                                    "response_length": model_result.get("response_length"),
                                }
                            )
                    elif task_type == "orchestration_test":
                        self.metrics["consensus"].append(
                            {
                                "timestamp": entry.get("timestamp"),
                                "agents_tested": result.get("agents_tested"),
                                "tokens_total": result.get("total_tokens"),
                                "status": result.get("status"),
                            }
                        )
            except json.JSONDecodeError:
                continue

    def generate_report(self) -> str:
        """Generate comprehensive performance report."""
        report = []
        report.append("\n" + "=" * 80)
        report.append("📊 ORCHESTRATION PERFORMANCE METRICS REPORT")
        report.append("=" * 80)
        report.append("")

        # Async parallel metrics
        if self.metrics["async_parallel"]:
            report.append("[⚡ ASYNC PARALLELIZATION METRICS]")
            async_data = self.metrics["async_parallel"]

            elapsed_times = [m["elapsed"] for m in async_data if m["elapsed"]]
            tokens = [m["tokens"] for m in async_data if m["tokens"]]
            speedups = [m["speedup"] for m in async_data if m["speedup"]]

            if elapsed_times:
                report.append(f"  Test runs: {len(async_data)}")
                report.append(f"  Avg execution time: {mean(elapsed_times):.1f}s")
                report.append(f"  Min: {min(elapsed_times):.1f}s, Max: {max(elapsed_times):.1f}s")

            if tokens:
                report.append(f"  Total tokens generated: {sum(tokens)}")
                report.append(f"  Avg tokens per run: {mean(tokens):.0f}")

            if speedups:
                report.append(f"  Parallelization speedup: {mean(speedups):.2f}x")

            report.append("")

        # Single agent metrics
        if self.metrics["single_agent"]:
            report.append("[🤖 SINGLE-AGENT PERFORMANCE]")
            agent_data = defaultdict(list)

            for metric in self.metrics["single_agent"]:
                model = metric.get("model", "unknown")
                agent_data[model].append(metric)

            for model, metrics_list in sorted(agent_data.items()):
                tokens = [m["tokens"] for m in metrics_list if m["tokens"]]
                if tokens:
                    report.append(f"  {model[:25]:25} - Avg: {mean(tokens):3.0f} tokens")

            report.append("")

        # Consensus metrics
        if self.metrics["consensus"]:
            report.append("[🎯 CONSENSUS GENERATION METRICS]")
            consensus_data = self.metrics["consensus"]

            successful = sum(1 for m in consensus_data if m["status"] == "OPERATIONAL")
            report.append(f"  Consensus runs: {len(consensus_data)}")
            report.append(
                f"  Success rate: {successful}/{len(consensus_data)} ({100 * successful / len(consensus_data):.0f}%)"
            )

            agents_tested = [m["agents_tested"] for m in consensus_data if m["agents_tested"]]
            if agents_tested:
                report.append(f"  Avg agents per run: {mean(agents_tested):.1f}")

            tokens_total = [m["tokens_total"] for m in consensus_data if m["tokens_total"]]
            if tokens_total:
                report.append(f"  Total tokens: {sum(tokens_total)}")

            report.append("")

        # Summary
        total_tasks = sum(len(v) for v in self.metrics.values())
        report.append("[📈 SUMMARY]")
        report.append(f"  Total orchestration tasks: {total_tasks}")
        report.append(f"  Test categories: {len(self.metrics)}")
        report.append(f"  Report generated: {datetime.now(UTC).isoformat()}")
        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def get_json_metrics(self) -> dict:
        """Export metrics as JSON for integration."""
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "async_parallel": self.metrics["async_parallel"],
            "single_agent": self.metrics["single_agent"],
            "consensus": self.metrics["consensus"],
            "summary": {
                "total_tasks": sum(len(v) for v in self.metrics.values()),
                "categories": list(self.metrics.keys()),
            },
        }


def main():
    """Run metrics analysis."""
    # Navigate from src/observability up to repo root, then to quest log
    repo_root = Path(__file__).parent.parent.parent  # Up from src/observability to root
    quest_log = repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"

    logger.info("[METRICS] Loading orchestration performance data...")

    metrics = OrchestrationMetrics(quest_log)

    # Print report
    report = metrics.generate_report()
    logger.info(report)

    # Save JSON metrics
    json_metrics = metrics.get_json_metrics()
    metrics_file = repo_root / "state" / "reports" / "orchestration_metrics.json"
    metrics_file.parent.mkdir(parents=True, exist_ok=True)

    with open(metrics_file, "w") as f:
        json.dump(json_metrics, f, indent=2)

    logger.info(f"[SAVED] Metrics exported to {metrics_file.name}")
    logger.info()


if __name__ == "__main__":
    main()
