"""Performance Benchmarking Framework.

Comprehensive benchmarking of SNS-Core on real AI responses.

[OmniTag: performance_benchmarking, evaluation, metrics, optimization]
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from src.config.service_config import ServiceConfig


@dataclass
class BenchmarkResult:
    """Single benchmark result."""

    test_name: str
    original_text: str
    sns_output: str
    original_tokens: int
    sns_tokens: int
    savings_pct: float
    conversion_time_ms: float
    accuracy_score: float  # 0-100
    model_used: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "original_text": self.original_text[:100],  # Truncate for storage
            "sns_output": self.sns_output[:100],
            "original_tokens": self.original_tokens,
            "sns_tokens": self.sns_tokens,
            "savings_pct": round(self.savings_pct, 2),
            "conversion_time_ms": round(self.conversion_time_ms, 2),
            "accuracy_score": round(self.accuracy_score, 1),
            "model_used": self.model_used,
            "timestamp": self.timestamp,
        }


class PerformanceBenchmark:
    """Benchmarking framework for SNS-Core performance."""

    def __init__(self, state_dir: Path = Path("state"), ollama_url: str | None = None):
        """Initialize benchmark framework.

        Args:
            state_dir: Directory for benchmark results
            ollama_url: Ollama API endpoint (defaults to environment config)
        """
        self.state_dir = state_dir
        self.ollama_url = ollama_url or ServiceConfig.get_ollama_url()
        self.results_file = state_dir / "benchmark_results.jsonl"
        self.summary_file = state_dir / "benchmark_summary.json"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.results: list[BenchmarkResult] = []

    def create_test_dataset(self) -> dict[str, list[str]]:
        """Create comprehensive test dataset for benchmarking.

        Returns:
            Dictionary of test category -> test cases
        """
        return {
            "code_generation": [
                "Create a function that validates email addresses and returns true if valid",
                "Write a class for managing user sessions with timeout handling",
                "Implement a REST API endpoint that handles GET and POST requests",
                "Design a database query optimization for large data sets",
                "Build an error handling system with retry logic and circuit breaker pattern",
            ],
            "documentation": [
                "Document the API endpoints for a REST service",
                "Write user guide for configuring authentication",
                "Create system architecture documentation with diagrams",
                "Document error codes and troubleshooting steps",
                "Write release notes for version 2.0 of the software",
            ],
            "analysis": [
                "Analyze the performance bottleneck in this algorithm",
                "Explain the security implications of this code pattern",
                "Identify potential race conditions in concurrent code",
                "Evaluate the scalability of this microservice architecture",
                "Review the design patterns used in this codebase",
            ],
            "technical_explanation": [
                "Explain how async/await works in Python",
                "Describe the difference between TCP and UDP protocols",
                "Explain the Observer pattern in software design",
                "Describe how blockchain technology works",
                "Explain the concept of eventual consistency in distributed systems",
            ],
            "code_review": [
                "Review this code for security vulnerabilities",
                "Check this implementation for performance issues",
                "Verify this test coverage is adequate",
                "Identify code quality improvements needed",
                "Review this refactoring for correctness",
            ],
        }

    def estimate_tokens(self, text: str, _model: str = "gpt-3.5-turbo") -> int:
        """Estimate token count for text.

        Args:
            text: Text to estimate
            model: Model to estimate for

        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return max(1, len(text) // 4)

    def benchmark_sns_conversion(
        self,
        sns_converter: Callable[[str], tuple[str, dict[str, Any]]],
    ) -> list[BenchmarkResult]:
        """Benchmark SNS conversion on test dataset.

        Args:
            sns_converter: Function to convert text to SNS

        Returns:
            List of benchmark results
        """
        test_dataset = self.create_test_dataset()
        results = []

        for category, test_cases in test_dataset.items():
            for i, test_text in enumerate(test_cases):
                test_name = f"{category}_{i + 1}"

                # Measure conversion time
                start_time = time.time()
                sns_output, _metadata = sns_converter(test_text)
                conversion_time = (time.time() - start_time) * 1000  # Convert to ms

                # Estimate tokens
                original_tokens = self.estimate_tokens(test_text)
                sns_tokens = self.estimate_tokens(sns_output)
                savings_pct = (
                    (original_tokens - sns_tokens) / original_tokens * 100
                    if original_tokens > 0
                    else 0
                )

                # Accuracy scoring: check if SNS output contains expected symbols
                expected_symbols = "⨳⦾→◆○●ƒⓒ"
                symbols_found = sum(1 for char in sns_output if char in expected_symbols)
                accuracy = min(100, (symbols_found / len(expected_symbols)) * 100)

                result = BenchmarkResult(
                    test_name=test_name,
                    original_text=test_text,
                    sns_output=sns_output,
                    original_tokens=original_tokens,
                    sns_tokens=sns_tokens,
                    savings_pct=savings_pct,
                    conversion_time_ms=conversion_time,
                    accuracy_score=accuracy,
                    model_used="sns-core-normal",
                )
                results.append(result)

        return results

    def benchmark_llm_response(
        self,
        prompt: str,
        model: str = "llama2",
        sns_converter: Callable[[str], tuple[str, dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        """Benchmark LLM response generation with optional SNS conversion.

        Args:
            prompt: Prompt to send to LLM
            model: Model to use
            sns_converter: Optional SNS conversion function

        Returns:
            Benchmark result with timings and token usage
        """
        try:
            # Generate normal response
            start_time = time.time()
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            response.raise_for_status()
            generate_time = time.time() - start_time
            response_text = response.json().get("response", "")

            result = {
                "prompt": prompt[:100],
                "model": model,
                "generate_time_s": round(generate_time, 2),
                "response_length": len(response_text),
                "response_tokens": self.estimate_tokens(response_text),
            }

            # Convert to SNS if converter provided
            if sns_converter:
                start_time = time.time()
                sns_response, _metadata = sns_converter(response_text)
                conversion_time = time.time() - start_time
                sns_tokens = self.estimate_tokens(sns_response)
                savings = (result["response_tokens"] - sns_tokens) / result["response_tokens"] * 100

                result.update(
                    {
                        "sns_conversion_time_s": round(conversion_time, 3),
                        "sns_tokens": sns_tokens,
                        "token_savings_pct": round(savings, 1),
                        "total_time_s": round(generate_time + conversion_time, 2),
                    }
                )

            return result

        except Exception as e:
            return {"error": str(e), "prompt": prompt[:100], "model": model}

    def save_results(self) -> None:
        """Save all results to files."""
        # Save JSONL
        with open(self.results_file, "w") as f:
            for result in self.results:
                f.write(json.dumps(result.to_dict()) + "\n")

        # Save summary
        summary = self.generate_summary()
        with open(self.summary_file, "w") as f:
            json.dump(summary, f, indent=2)

    def generate_summary(self) -> dict[str, Any]:
        """Generate summary statistics from results.

        Returns:
            Summary dictionary
        """
        if not self.results:
            return {"status": "no_results"}

        savings_list = [r.savings_pct for r in self.results]
        times_list = [r.conversion_time_ms for r in self.results]
        accuracy_list = [r.accuracy_score for r in self.results]

        return {
            "timestamp": datetime.now().isoformat(),
            "total_benchmarks": len(self.results),
            "avg_savings_pct": round(sum(savings_list) / len(savings_list), 1),
            "min_savings_pct": round(min(savings_list), 1),
            "max_savings_pct": round(max(savings_list), 1),
            "avg_conversion_time_ms": round(sum(times_list) / len(times_list), 2),
            "avg_accuracy_score": round(sum(accuracy_list) / len(accuracy_list), 1),
            "by_category": self._summarize_by_category(),
            "estimated_yearly_savings_usd": round(
                sum(r.savings_pct for r in self.results)
                / len(self.results)
                * 50000  # Assume 50k tokens/day
                * 365
                * 0.00003,  # GPT-4 pricing
                2,
            ),
        }

    def _summarize_by_category(self) -> dict[str, dict[str, Any]]:
        """Summarize results by test category."""
        categories = {}

        for result in self.results:
            category = result.test_name.rsplit("_", 1)[0]
            if category not in categories:
                categories[category] = {
                    "count": 0,
                    "avg_savings": 0,
                    "avg_time_ms": 0,
                    "results": [],
                }

            categories[category]["results"].append(result)

        # Calculate averages
        for _category, data in categories.items():
            results = data.pop("results")
            data["count"] = len(results)
            data["avg_savings"] = round(sum(r.savings_pct for r in results) / len(results), 1)
            data["avg_time_ms"] = round(
                sum(r.conversion_time_ms for r in results) / len(results), 2
            )

        return categories

    def generate_benchmark_report(self) -> str:
        """Generate human-readable benchmark report.

        Returns:
            Formatted report string
        """
        summary = self.generate_summary()

        report = "# SNS-Core Performance Benchmark Report\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        report += "## Summary Metrics\n\n"
        report += f"- **Total Benchmarks:** {summary.get('total_benchmarks', 0)}\n"
        report += f"- **Average Token Savings:** {summary.get('avg_savings_pct', 0)}%\n"
        report += f"- **Token Savings Range:** {summary.get('min_savings_pct', 0)}% - {summary.get('max_savings_pct', 0)}%\n"
        report += f"- **Average Conversion Time:** {summary.get('avg_conversion_time_ms', 0)}ms\n"
        report += f"- **Average Accuracy Score:** {summary.get('avg_accuracy_score', 0)}/100\n"
        report += (
            f"- **Estimated Yearly Savings:** ${summary.get('estimated_yearly_savings_usd', 0)}\n\n"
        )

        report += "## Results by Category\n\n"
        for category, stats in summary.get("by_category", {}).items():
            report += f"### {category.replace('_', ' ').title()}\n"
            report += f"- Count: {stats.get('count', 0)}\n"
            report += f"- Avg Savings: {stats.get('avg_savings', 0)}%\n"
            report += f"- Avg Time: {stats.get('avg_time_ms', 0)}ms\n\n"

        return report


def run_performance_benchmark(
    sns_converter: Callable[[str], tuple[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Run full performance benchmark suite.

    Args:
        sns_converter: SNS conversion function

    Returns:
        Benchmark results summary
    """
    benchmark = PerformanceBenchmark()
    results = benchmark.benchmark_sns_conversion(sns_converter)
    benchmark.results = results
    benchmark.save_results()

    return benchmark.generate_summary()
