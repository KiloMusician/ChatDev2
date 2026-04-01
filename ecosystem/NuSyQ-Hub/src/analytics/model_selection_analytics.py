"""Model Selection Analytics - ZETA03 Performance Intelligence System.

Advanced performance analytics, decision archaeology, and optimization metrics.
"""

import json
import logging
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypedDict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


@dataclass
class ModelPerformanceMetrics:
    """Comprehensive model performance tracking."""

    model_name: str
    task_type: str
    response_time: float
    token_rate: float
    accuracy_score: float
    user_satisfaction: float
    memory_efficiency: float
    selection_frequency: int
    last_used: datetime
    success_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["last_used"] = self.last_used.isoformat()
        return result


class ReportDateRange(TypedDict):
    """Typed date range for analytics reports."""

    start: str
    end: str


class ReportSummary(TypedDict):
    """Typed summary section for analytics reports."""

    total_selections: int
    unique_models: int
    unique_tasks: int
    date_range: ReportDateRange


class ModelRankingEntry(TypedDict):
    """Ranking entry for a model within a task."""

    model: str
    score: float
    selections: int


class PerformanceReport(TypedDict, total=False):
    """Structured performance report output."""

    error: str
    summary: ReportSummary
    model_rankings: dict[str, list[ModelRankingEntry]]
    task_analysis: dict[str, Any]
    optimization_opportunities: list[str]


class ModelSelectionAnalytics:
    """Advanced analytics for intelligent model selection optimization."""

    def __init__(self, data_path: Path | None = None) -> None:
        """Initialize ModelSelectionAnalytics with data_path."""
        self.data_path = data_path or Path("logs/model_selection_analytics.json")
        self.data_path.parent.mkdir(parents=True, exist_ok=True)

        self.performance_metrics: list[ModelPerformanceMetrics] = []
        self.selection_patterns: dict[str, Any] = {}
        self.optimization_insights: dict[str, Any] = {}

        self.load_analytics_data()

    def load_analytics_data(self) -> None:
        """Load existing analytics data."""
        if self.data_path.exists():
            try:
                with open(self.data_path, encoding="utf-8") as f:
                    data = json.load(f)

                # Load performance metrics
                for metric_data in data.get("performance_metrics", []):
                    metric_data["last_used"] = datetime.fromisoformat(metric_data["last_used"])
                    self.performance_metrics.append(ModelPerformanceMetrics(**metric_data))

                self.selection_patterns = data.get("selection_patterns", {})
                self.optimization_insights = data.get("optimization_insights", {})

                logging.info("📊 Loaded %d analytics records", len(self.performance_metrics))

            except Exception as e:
                logging.exception("❌ Error loading analytics data: %s", e)

    def save_analytics_data(self) -> None:
        """Save analytics data to disk."""
        try:
            data = {
                "performance_metrics": [metric.to_dict() for metric in self.performance_metrics],
                "selection_patterns": self.selection_patterns,
                "optimization_insights": self.optimization_insights,
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logging.info("💾 Saved analytics data to %s", self.data_path)

        except Exception as e:
            logging.exception("❌ Error saving analytics data: %s", e)

    def record_model_performance(
        self,
        model_name: str,
        task_type: str,
        response_time: float,
        token_rate: float,
        accuracy_score: float = 1.0,
        user_satisfaction: float = 1.0,
        memory_efficiency: float = 1.0,
    ) -> None:
        """Record performance metrics for a model selection."""
        # Calculate selection frequency
        selection_frequency = sum(
            1
            for m in self.performance_metrics
            if m.model_name == model_name and m.task_type == task_type
        )

        metric = ModelPerformanceMetrics(
            model_name=model_name,
            task_type=task_type,
            response_time=response_time,
            token_rate=token_rate,
            accuracy_score=accuracy_score,
            user_satisfaction=user_satisfaction,
            memory_efficiency=memory_efficiency,
            selection_frequency=selection_frequency + 1,
            last_used=datetime.now(),
        )

        self.performance_metrics.append(metric)
        self._update_selection_patterns()
        self.save_analytics_data()

        logging.info("📈 Recorded performance for %s on %s", model_name, task_type)

    def _update_selection_patterns(self) -> None:
        """Update selection pattern analysis."""
        if not self.performance_metrics:
            return

        # Task distribution analysis
        task_counts = Counter(m.task_type for m in self.performance_metrics)
        self.selection_patterns["task_distribution"] = dict(task_counts)

        # Model preference analysis
        model_counts = Counter(m.model_name for m in self.performance_metrics)
        self.selection_patterns["model_preferences"] = dict(model_counts)

        # Time-based patterns
        recent_metrics = [
            m for m in self.performance_metrics if m.last_used > datetime.now() - timedelta(days=7)
        ]

        if recent_metrics:
            self.selection_patterns["recent_usage"] = {
                "most_used_model": Counter(m.model_name for m in recent_metrics).most_common(1)[0][
                    0
                ],
                "most_common_task": Counter(m.task_type for m in recent_metrics).most_common(1)[0][
                    0
                ],
                "average_response_time": statistics.mean(m.response_time for m in recent_metrics),
            }

    def get_optimal_model_recommendation(
        self, task_type: str, priority: str = "balanced"
    ) -> tuple[str, float]:
        """Get optimal model recommendation based on analytics."""
        # Filter metrics for this task type
        task_metrics = [m for m in self.performance_metrics if m.task_type == task_type]

        if not task_metrics:
            return "llama2:7b", 0.5  # Default fallback

        # Group by model and calculate composite scores
        model_scores = defaultdict(list)

        for metric in task_metrics:
            if priority == "speed":
                score = (1.0 / max(metric.response_time, 0.1)) * 0.6 + metric.accuracy_score * 0.4
            elif priority == "accuracy":
                score = metric.accuracy_score * 0.7 + metric.user_satisfaction * 0.3
            elif priority == "efficiency":
                score = (
                    metric.memory_efficiency * 0.5
                    + (1.0 / max(metric.response_time, 0.1)) * 0.3
                    + metric.accuracy_score * 0.2
                )
            else:  # balanced
                score = (
                    metric.accuracy_score * 0.3
                    + metric.user_satisfaction * 0.2
                    + metric.memory_efficiency * 0.2
                    + (1.0 / max(metric.response_time, 0.1)) * 0.2
                    + min(metric.token_rate / 1000, 1.0) * 0.1
                )

            model_scores[metric.model_name].append(score)

        # Calculate average scores
        avg_scores = {model: statistics.mean(scores) for model, scores in model_scores.items()}

        # Get best model
        best_model = max(avg_scores.items(), key=lambda x: x[1])

        logging.info(
            "🎯 Recommended %s for %s (score: %.3f)",
            best_model[0],
            task_type,
            best_model[1],
        )

        return best_model

    def generate_performance_report(self) -> PerformanceReport:
        """Generate comprehensive performance analysis report."""
        if not self.performance_metrics:
            return {"error": "No performance data available"}

        report: PerformanceReport = {
            "summary": {
                "total_selections": len(self.performance_metrics),
                "unique_models": len({m.model_name for m in self.performance_metrics}),
                "unique_tasks": len({m.task_type for m in self.performance_metrics}),
                "date_range": {
                    "start": min(m.last_used for m in self.performance_metrics).isoformat(),
                    "end": max(m.last_used for m in self.performance_metrics).isoformat(),
                },
            },
            "model_rankings": {},
            "task_analysis": {},
            "optimization_opportunities": [],
        }

        # Model rankings by task
        for task_type in {m.task_type for m in self.performance_metrics}:
            task_metrics = [m for m in self.performance_metrics if m.task_type == task_type]

            model_performance = defaultdict(list)
            for metric in task_metrics:
                composite_score = (
                    metric.accuracy_score * 0.4
                    + metric.user_satisfaction * 0.3
                    + metric.memory_efficiency * 0.2
                    + (1.0 / max(metric.response_time, 0.1)) * 0.1
                )
                model_performance[metric.model_name].append(composite_score)

            # Average scores
            avg_performance = {
                model: statistics.mean(scores) for model, scores in model_performance.items()
            }

            # Sort by performance
            ranked_models = sorted(avg_performance.items(), key=lambda x: x[1], reverse=True)

            report["model_rankings"][task_type] = [
                {"model": model, "score": round(score, 3), "selections": len(scores)}
                for (model, score), scores in zip(
                    ranked_models, model_performance.values(), strict=False
                )
            ]

        # Task analysis
        for task_type in {m.task_type for m in self.performance_metrics}:
            task_metrics = [m for m in self.performance_metrics if m.task_type == task_type]

            report["task_analysis"][task_type] = {
                "total_selections": len(task_metrics),
                "avg_response_time": round(
                    statistics.mean(m.response_time for m in task_metrics), 3
                ),
                "avg_accuracy": round(statistics.mean(m.accuracy_score for m in task_metrics), 3),
                "avg_satisfaction": round(
                    statistics.mean(m.user_satisfaction for m in task_metrics), 3
                ),
                "most_used_model": Counter(m.model_name for m in task_metrics).most_common(1)[0][0],
            }

        # Optimization opportunities
        self._identify_optimization_opportunities(report)

        return report

    def _identify_optimization_opportunities(self, report: PerformanceReport) -> None:
        """Identify potential optimization opportunities."""
        opportunities: list[Any] = []
        # Check for underperforming models
        for task_type, rankings in report["model_rankings"].items():
            if len(rankings) > 1:
                best_score = rankings[0]["score"]
                worst_score = rankings[-1]["score"]

                if best_score - worst_score > 0.3:  # Significant performance gap
                    opportunities.append(
                        {
                            "type": "model_replacement",
                            "task": task_type,
                            "suggestion": f"Consider replacing {rankings[-1]['model']} with {rankings[0]['model']} for {task_type}",
                            "potential_improvement": round((best_score - worst_score) * 100, 1),
                        }
                    )

        # Check for response time outliers
        avg_response_times: list[Any] = []
        for metrics_subset in [report["task_analysis"][task] for task in report["task_analysis"]]:
            avg_response_times.append(metrics_subset["avg_response_time"])

        if avg_response_times:
            overall_avg = statistics.mean(avg_response_times)
            for task_type, analysis in report["task_analysis"].items():
                if analysis["avg_response_time"] > overall_avg * 1.5:
                    opportunities.append(
                        {
                            "type": "performance_optimization",
                            "task": task_type,
                            "suggestion": f"Response times for {task_type} are {round(analysis['avg_response_time'] / overall_avg, 1)}x slower than average",
                            "current_time": analysis["avg_response_time"],
                            "target_time": overall_avg,
                        }
                    )

        report["optimization_opportunities"] = opportunities

    def create_performance_dashboard(self, output_path: Path | None = None) -> None:
        """Create visual performance dashboard."""
        if not self.performance_metrics:
            logging.warning("📊 No data available for dashboard")
            return

        output_path = output_path or Path("reports/model_selection_dashboard.png")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create DataFrame
        df = pd.DataFrame(
            [
                {
                    "model": m.model_name,
                    "task": m.task_type,
                    "response_time": m.response_time,
                    "accuracy": m.accuracy_score,
                    "satisfaction": m.user_satisfaction,
                    "efficiency": m.memory_efficiency,
                    "date": m.last_used,
                }
                for m in self.performance_metrics
            ]
        )

        # Create dashboard
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle("Model Selection Performance Dashboard", fontsize=16, fontweight="bold")

        # Model usage distribution
        model_counts = df["model"].value_counts()
        axes[0, 0].pie(model_counts.values, labels=model_counts.index, autopct="%1.1f%%")
        axes[0, 0].set_title("Model Usage Distribution")

        # Task type distribution
        task_counts = df["task"].value_counts()
        axes[0, 1].bar(task_counts.index, task_counts.values)
        axes[0, 1].set_title("Task Type Distribution")
        axes[0, 1].tick_params(axis="x", rotation=45)

        # Response time by model
        sns.boxplot(data=df, x="model", y="response_time", ax=axes[1, 0])
        axes[1, 0].set_title("Response Time by Model")
        axes[1, 0].tick_params(axis="x", rotation=45)

        # Accuracy vs Efficiency scatter
        for model in df["model"].unique():
            model_data = df[df["model"] == model]
            axes[1, 1].scatter(
                model_data["efficiency"], model_data["accuracy"], label=model, alpha=0.7
            )

        axes[1, 1].set_xlabel("Memory Efficiency")
        axes[1, 1].set_ylabel("Accuracy Score")
        axes[1, 1].set_title("Accuracy vs Efficiency by Model")
        axes[1, 1].legend()

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        logging.info("📊 Dashboard saved to %s", output_path)


def initialize_model_analytics() -> "ModelSelectionAnalytics":
    """Initialize model selection analytics system."""
    try:
        analytics = ModelSelectionAnalytics()

        # Create some sample data for demonstration

        logging.info("🚀 Model Selection Analytics System initialized")
        logging.info("📊 Current data: %d records", len(analytics.performance_metrics))

        return analytics

    except Exception as e:
        logging.exception("❌ Failed to initialize analytics: %s", e)
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Initialize analytics system
    analytics = initialize_model_analytics()

    # Generate report if data exists
    if analytics.performance_metrics:
        report = analytics.generate_performance_report()

        # Create dashboard
        analytics.create_performance_dashboard()
