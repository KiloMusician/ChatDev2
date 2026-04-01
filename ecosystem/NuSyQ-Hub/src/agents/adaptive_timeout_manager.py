#!/usr/bin/env python3
"""Adaptive Timeout Manager - Intelligent timeout handling for AI operations.

Learns from past performance and adjusts timeouts dynamically based on:
- Model size and complexity
- Historical generation times
- Task complexity
- System load
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AdaptiveTimeoutManager:
    """Manages timeouts intelligently based on historical performance."""

    def __init__(
        self,
        metrics_file: str = "data/timeout_metrics.json",
        enable_breathing: bool = True,
    ) -> None:
        """Initialize timeout manager.

        Args:
            metrics_file: Path to store performance metrics
            enable_breathing: Enable breathing-based pacing adjustments
        """
        self.metrics_file = Path(metrics_file)
        self.metrics: dict[str, Any] = self._load_metrics()
        self.enable_breathing = enable_breathing
        self.breathing_factor = 1.0  # Current breathing adjustment

        # Base timeouts per model size (in seconds)
        self.base_timeouts = {
            "3b": 30,  # Small models (phi3.5)
            "7b": 60,  # Medium models (codellama, qwen2.5-coder:7b)
            "9b": 90,  # Large models (gemma2, llama3.1)
            "14b": 120,  # Very large (qwen2.5-coder:14b)
            "16b": 150,  # Huge models (deepseek-coder-v2:16b)
            "default": 60,
        }

        # Complexity multipliers
        self.complexity_multipliers = {
            "simple": 1.0,
            "medium": 1.5,
            "complex": 2.0,
            "very_complex": 3.0,
        }

    def _load_metrics(self) -> dict[str, Any]:
        """Load historical performance metrics."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, ValueError, OSError) as e:
                logger.warning(f"Could not load metrics: {e}")

        return {
            "model_performance": {},
            "task_performance": {},
            "success_rate": {},
            "average_times": {},
        }

    def _save_metrics(self) -> None:
        """Save performance metrics."""
        try:
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save metrics: {e}")

    def get_timeout(
        self, model: str, task_type: str = "code_generation", complexity: str = "simple"
    ) -> float:
        """Calculate intelligent timeout for a task.

        Args:
            model: Model name (e.g., "qwen2.5-coder:14b")
            task_type: Type of task (e.g., "code_generation", "documentation")
            complexity: Task complexity level

        Returns:
            Timeout in seconds
        """
        # Extract model size
        model_size = self._extract_model_size(model)
        base_timeout = self.base_timeouts.get(model_size, self.base_timeouts["default"])

        # Apply complexity multiplier
        complexity_mult = self.complexity_multipliers.get(complexity, 1.0)
        calculated_timeout = base_timeout * complexity_mult

        # Adjust based on historical performance
        model_key = f"{model}:{task_type}"
        if model_key in self.metrics["average_times"]:
            avg_time = self.metrics["average_times"][model_key]
            # Add 50% buffer to average time
            historical_timeout = avg_time * 1.5
            # Use the larger of calculated and historical
            calculated_timeout = max(calculated_timeout, historical_timeout)

        # Check success rate and adjust
        if model_key in self.metrics["success_rate"]:
            success_rate = self.metrics["success_rate"][model_key]
            if success_rate < 0.5:  # Less than 50% success
                # Increase timeout by 50%
                calculated_timeout *= 1.5
                logger.info(
                    f"Low success rate ({success_rate:.0%}) for {model_key}, increasing timeout"
                )

        # Apply breathing factor if enabled
        if self.enable_breathing and self.breathing_factor != 1.0:
            original_timeout = calculated_timeout
            calculated_timeout *= self.breathing_factor
            logger.debug(
                f"Breathing adjustment: {original_timeout:.0f}s x "
                f"{self.breathing_factor:.2f} = {calculated_timeout:.0f}s"
            )

        logger.debug(f"Timeout for {model} ({task_type}, {complexity}): {calculated_timeout:.0f}s")
        return calculated_timeout

    def _extract_model_size(self, model: str) -> str:
        """Extract model size from model name.

        Args:
            model: Model name (e.g., "qwen2.5-coder:14b")

        Returns:
            Model size key (e.g., "14b")
        """
        # Extract size from common patterns
        if "3b" in model.lower() or "3.8b" in model.lower():
            return "3b"
        elif "7b" in model.lower():
            return "7b"
        elif "8b" in model.lower() or "9b" in model.lower():
            return "9b"
        elif "14b" in model.lower() or "15b" in model.lower():
            return "14b"
        elif "16b" in model.lower():
            return "16b"
        else:
            return "default"

    def record_attempt(self, model: str, task_type: str, duration: float, success: bool) -> None:
        """Record a generation attempt for future optimization.

        Args:
            model: Model name used
            task_type: Type of task performed
            duration: Time taken in seconds
            success: Whether the attempt succeeded
        """
        model_key = f"{model}:{task_type}"

        # Update average times
        if model_key not in self.metrics["average_times"]:
            self.metrics["average_times"][model_key] = duration
        else:
            # Exponential moving average (70% old, 30% new)
            old_avg = self.metrics["average_times"][model_key]
            self.metrics["average_times"][model_key] = (old_avg * 0.7) + (duration * 0.3)

        # Update success rate
        if model_key not in self.metrics["success_rate"]:
            self.metrics["success_rate"][model_key] = 1.0 if success else 0.0
            self.metrics["model_performance"][model_key] = {
                "attempts": 1,
                "successes": 1 if success else 0,
            }
        else:
            perf = self.metrics["model_performance"][model_key]
            perf["attempts"] += 1
            if success:
                perf["successes"] += 1
            self.metrics["success_rate"][model_key] = perf["successes"] / perf["attempts"]

        # Save updated metrics
        self._save_metrics()

        logger.info(
            f"Recorded {model_key}: {duration:.1f}s, "
            f"success={success}, avg={self.metrics['average_times'][model_key]:.1f}s, "
            f"success_rate={self.metrics['success_rate'][model_key]:.0%}"
        )

    def get_recommended_model(self, task_type: str, max_timeout: float | None = None) -> str:
        """Recommend best model based on performance history.

        Args:
            task_type: Type of task to perform
            max_timeout: Maximum acceptable timeout

        Returns:
            Recommended model name
        """
        # Find models with good success rates for this task
        candidates: list[tuple[str, float, float]] = []
        for key, success_rate in self.metrics["success_rate"].items():
            try:
                success_rate_val = float(success_rate)
            except (TypeError, ValueError):
                continue
            if task_type in key and success_rate_val > 0.6:  # At least 60% success
                model_name = key.split(":")[0]
                try:
                    avg_time = float(self.metrics["average_times"].get(key, float("inf")))
                except (TypeError, ValueError):
                    avg_time = float("inf")

                if max_timeout is None or avg_time <= max_timeout:
                    candidates.append((model_name, success_rate_val, avg_time))

        if candidates:
            # Sort by success rate (descending), then by time (ascending)
            candidates.sort(key=lambda x: (-x[1], x[2]))
            recommended = candidates[0][0]
            logger.info(f"Recommended model for {task_type}: {recommended}")
            return recommended

        # Default fallback
        return "qwen2.5-coder:14b"

    def update_breathing_factor(
        self,
        success_rate: float,
        backlog_level: float = 0.0,
        failure_burst: float = 0.0,
    ) -> None:
        """Update breathing factor based on system metrics.

        Breathing Philosophy: "Work faster when succeeding, slower when failing"

        Args:
            success_rate: Recent success rate (0.0-1.0)
            backlog_level: Queue fullness (0.0-1.0, optional)
            failure_burst: Recent failure density (0.0-1.0, optional)
        """
        if not self.enable_breathing:
            return

        # Simple breathing formula based on success and backlog
        if success_rate > 0.8 and backlog_level > 0.5:
            # High success + backlog → speed up
            self.breathing_factor = 0.85
            logger.info("🌬️ Breathing: ACCELERATE (high success + backlog)")
        elif success_rate < 0.3 or failure_burst > 0.5:
            # Low success or failure burst → slow down
            self.breathing_factor = 1.5
            logger.info("🌬️ Breathing: DECELERATE (failures detected)")
        elif success_rate < 0.5:
            # Moderate failures → moderate slowdown
            self.breathing_factor = 1.2
            logger.info("🌬️ Breathing: CAUTION (moderate failures)")
        else:
            # Steady state
            self.breathing_factor = 1.0
            logger.debug("🌬️ Breathing: STEADY")

    def should_retry(self, model: str, task_type: str, attempt: int) -> tuple[bool, str | None]:
        """Determine if we should retry with a different model.

        Args:
            model: Model that failed
            task_type: Type of task
            attempt: Current attempt number

        Returns:
            Tuple of (should_retry, alternative_model)
        """
        if attempt >= 3:
            return False, None

        # Get success rate for this model
        model_key = f"{model}:{task_type}"
        success_rate = self.metrics["success_rate"].get(model_key, 0.5)

        if success_rate < 0.3:  # Very low success rate
            # Try a smaller, faster model
            alternatives = {
                "qwen2.5-coder:14b": "qwen2.5-coder:7b",
                "deepseek-coder-v2:16b": "qwen2.5-coder:14b",
                "llama3.1:8b": "phi3.5:latest",
                "gemma2:9b": "llama3.1:8b",
            }

            alternative = alternatives.get(model)
            if alternative:
                logger.info(f"Low success rate for {model}, suggesting {alternative}")
                return True, alternative

        return False, None


# Global instance
_timeout_manager: AdaptiveTimeoutManager | None = None


def get_timeout_manager() -> AdaptiveTimeoutManager:
    """Get global timeout manager instance."""
    global _timeout_manager
    if _timeout_manager is None:
        _timeout_manager = AdaptiveTimeoutManager()
    return _timeout_manager
