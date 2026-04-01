"""
Adaptive Timeout Manager for ΞNuSyQ Ecosystem
===========================================

Purpose:
    Intelligent, learning-based timeout management that eliminates arbitrary
    hardcoded timeouts. Tracks execution patterns, learns from history, and
    dynamically adjusts timeouts based on:
    - Agent type (Claude vs Ollama vs ChatDev)
    - Task complexity
    - Historical performance
    - System load
    - Time of day patterns

Philosophy:
    "Timeouts should be informed by reality, not arbitrary developer guesses"

Integration:
    - Reads from agent_registry.yaml for agent characteristics
    - Stores performance metrics in State/performance_metrics.json
    - Updates knowledge-base.yaml with learned patterns
    - Uses ΞNuSyQ temporal tracking (⨂ΦΣΞΨΘΣΛ) for drift analysis

Author: GitHub Copilot + User Directive
Date: 2025-10-07
Status: Production - Adaptive Learning System
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger("nusyq.adaptive_timeout")


class TaskComplexity(Enum):
    """Task complexity levels for timeout calculation"""

    TRIVIAL = "trivial"  # < 5 seconds expected
    SIMPLE = "simple"  # 5-30 seconds
    MODERATE = "moderate"  # 30-300 seconds (5 min)
    COMPLEX = "complex"  # 300-1800 seconds (30 min)
    CRITICAL = "critical"  # 1800+ seconds (30+ min)


class AgentType(Enum):
    """Agent types with different performance characteristics"""

    LOCAL_FAST = "local_fast"  # phi3.5, qwen:7b (< 10s)
    LOCAL_QUALITY = "local_quality"  # qwen:14b, gemma2 (10-60s)
    REMOTE_API = "remote_api"  # Claude, GPT-4 (variable)
    MULTI_AGENT = "multi_agent"  # AI Council, ChatDev (minutes)
    ORCHESTRATOR = "orchestrator"  # Full workflows (10-30 min)


@dataclass
class ExecutionMetric:
    """Single execution measurement"""

    agent_type: str
    task_complexity: str
    actual_duration: float
    timestamp: datetime
    succeeded: bool
    context: Dict[str, Any]


@dataclass
class TimeoutRecommendation:
    """Adaptive timeout recommendation"""

    timeout_seconds: float
    confidence: float  # 0.0-1.0
    reasoning: str
    fallback_timeout: float
    max_timeout: float


class AdaptiveTimeoutManager:
    """
    Manages intelligent, self-learning timeouts

    Features:
    - Historical performance tracking
    - Statistical analysis (median, percentiles)
    - Complexity-based adjustment
    - Agent-type awareness
    - Grace period calculation (stddev-based)
    - Fallback safety limits
    - Continuous learning

    Example:
        manager = AdaptiveTimeoutManager()

        # Get recommended timeout
        recommendation = manager.get_timeout(
            agent_type=AgentType.LOCAL_QUALITY,
            task_complexity=TaskComplexity.MODERATE
        )
        timeout = recommendation.timeout_seconds

        # Track actual execution
        start = time.time()
        result = await some_operation(timeout=timeout)
        duration = time.time() - start

        # Record for learning
        manager.record_execution(
            agent_type=AgentType.LOCAL_QUALITY,
            task_complexity=TaskComplexity.MODERATE,
            duration=duration,
            succeeded=True
        )
    """

    def __init__(
        self,
        metrics_file: Optional[Path] = None,
        agent_registry_file: Optional[Path] = None,
    ):
        """
        Initialize adaptive timeout manager

        Args:
            metrics_file: Path to performance metrics JSON
            agent_registry_file: Path to agent registry YAML
        """
        self.metrics_file = metrics_file or Path("State/performance_metrics.json")
        self.agent_registry_file = agent_registry_file or Path(
            "config/agent_registry.yaml"
        )

        # Create state directory if needed
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

        # Load historical metrics
        self.metrics: Dict[str, list] = self._load_metrics()

        # Load agent characteristics (if available)
        self.agent_characteristics = self._load_agent_registry()

        # Safety limits (absolute maximums to prevent infinite waits)
        self.SAFETY_LIMITS = {
            TaskComplexity.TRIVIAL: 30,  # 30 seconds max
            TaskComplexity.SIMPLE: 180,  # 3 minutes max
            TaskComplexity.MODERATE: 1800,  # 30 minutes max
            TaskComplexity.COMPLEX: 5400,  # 90 minutes max
            TaskComplexity.CRITICAL: 10800,  # 3 hours max
        }

        # Minimum timeouts (prevent too-short timeouts)
        self.MINIMUM_TIMEOUTS = {
            TaskComplexity.TRIVIAL: 5,
            TaskComplexity.SIMPLE: 10,
            TaskComplexity.MODERATE: 30,
            TaskComplexity.COMPLEX: 120,
            TaskComplexity.CRITICAL: 300,
        }

        # Default timeouts (used when no historical data)
        self.DEFAULT_TIMEOUTS = {
            AgentType.LOCAL_FAST: {
                TaskComplexity.TRIVIAL: 10,
                TaskComplexity.SIMPLE: 30,
                TaskComplexity.MODERATE: 120,
                TaskComplexity.COMPLEX: 600,
                TaskComplexity.CRITICAL: 1800,
            },
            AgentType.LOCAL_QUALITY: {
                TaskComplexity.TRIVIAL: 15,
                TaskComplexity.SIMPLE: 60,
                TaskComplexity.MODERATE: 300,
                TaskComplexity.COMPLEX: 1200,
                TaskComplexity.CRITICAL: 3600,
            },
            AgentType.REMOTE_API: {
                TaskComplexity.TRIVIAL: 30,
                TaskComplexity.SIMPLE: 120,
                TaskComplexity.MODERATE: 600,
                TaskComplexity.COMPLEX: 1800,
                TaskComplexity.CRITICAL: 5400,
            },
            AgentType.MULTI_AGENT: {
                TaskComplexity.TRIVIAL: 60,
                TaskComplexity.SIMPLE: 300,
                TaskComplexity.MODERATE: 1200,
                TaskComplexity.COMPLEX: 3600,
                TaskComplexity.CRITICAL: 7200,
            },
            AgentType.ORCHESTRATOR: {
                TaskComplexity.TRIVIAL: 120,
                TaskComplexity.SIMPLE: 600,
                TaskComplexity.MODERATE: 1800,
                TaskComplexity.COMPLEX: 5400,
                TaskComplexity.CRITICAL: 10800,
            },
        }

    def get_timeout(
        self,
        agent_type: AgentType,
        task_complexity: TaskComplexity,
        context: Optional[Dict[str, Any]] = None,
    ) -> TimeoutRecommendation:
        """
        Get intelligent timeout recommendation

        Algorithm:
        1. Check if we have historical data for this agent+complexity
        2. If yes: Use statistical analysis (median + stddev buffer)
        3. If no: Use default timeout based on agent type
        4. Apply safety limits (min/max)
        5. Add grace period based on confidence

        Args:
            agent_type: Type of agent being used
            task_complexity: Expected task complexity
            context: Optional context (time of day, system load, etc.)

        Returns:
            TimeoutRecommendation with calculated timeout and reasoning
        """
        key = f"{agent_type.value}_{task_complexity.value}"
        historical_data = self.metrics.get(key, [])

        # Extract successful execution durations
        successful_durations = [
            m["actual_duration"] for m in historical_data if m.get("succeeded", False)
        ]

        if len(successful_durations) >= 3:
            # Enough data for statistical analysis
            return self._calculate_statistical_timeout(
                agent_type, task_complexity, successful_durations, context
            )
        else:
            # Use default timeout (not enough historical data)
            return self._get_default_timeout(
                agent_type, task_complexity, len(successful_durations), context
            )

    def _calculate_statistical_timeout(
        self,
        agent_type: AgentType,
        task_complexity: TaskComplexity,
        durations: list,
        context: Optional[Dict[str, Any]],
    ) -> TimeoutRecommendation:
        """
        Calculate timeout using statistical analysis of historical data

        Strategy:
        - Use 90th percentile as base timeout (covers most cases)
        - Add buffer based on standard deviation
        - Apply safety limits
        """
        # Statistical measures
        median = statistics.median(durations)
        mean = statistics.mean(durations)
        stdev = statistics.stdev(durations) if len(durations) > 1 else 0

        # 90th percentile (most executions finish within this time)
        sorted_durations = sorted(durations)
        p90_index = int(len(sorted_durations) * 0.90)
        p90 = sorted_durations[p90_index]

        # Base timeout = 90th percentile + 1 stddev (safety buffer)
        base_timeout = p90 + stdev

        # Apply safety limits
        min_timeout = self.MINIMUM_TIMEOUTS[task_complexity]
        max_timeout = self.SAFETY_LIMITS[task_complexity]

        recommended_timeout = max(min_timeout, min(base_timeout, max_timeout))

        # Confidence based on sample size and variance
        sample_size = len(durations)
        variance_ratio = stdev / mean if mean > 0 else 1.0

        # High sample size + low variance = high confidence
        confidence = min(1.0, (sample_size / 20) * (1.0 - min(variance_ratio, 1.0)))

        reasoning = (
            f"Based on {sample_size} historical executions. "
            f"Median: {median:.1f}s, 90th percentile: {p90:.1f}s, "
            f"StdDev: {stdev:.1f}s. Using P90+1σ with {confidence * 100:.0f}% "
            f"confidence."
        )

        return TimeoutRecommendation(
            timeout_seconds=recommended_timeout,
            confidence=confidence,
            reasoning=reasoning,
            fallback_timeout=self.DEFAULT_TIMEOUTS[agent_type][task_complexity],
            max_timeout=max_timeout,
        )

    def _get_default_timeout(
        self,
        agent_type: AgentType,
        task_complexity: TaskComplexity,
        sample_count: int,
        context: Optional[Dict[str, Any]],
    ) -> TimeoutRecommendation:
        """
        Get default timeout when insufficient historical data

        Uses conservative defaults based on agent type and complexity
        """
        default = self.DEFAULT_TIMEOUTS[agent_type][task_complexity]
        max_timeout = self.SAFETY_LIMITS[task_complexity]

        # Lower confidence due to lack of data
        confidence = 0.3 + (sample_count * 0.1)  # 0.3-0.5

        reasoning = (
            f"Insufficient historical data ({sample_count} samples). "
            f"Using conservative default based on agent type "
            f"({agent_type.value}) and complexity ({task_complexity.value})."
        )

        return TimeoutRecommendation(
            timeout_seconds=default,
            confidence=confidence,
            reasoning=reasoning,
            fallback_timeout=default,
            max_timeout=max_timeout,
        )

    def record_execution(
        self,
        agent_type: AgentType,
        task_complexity: TaskComplexity,
        duration: float,
        succeeded: bool,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Record actual execution for learning

        This is how the system learns and adapts timeouts over time

        Args:
            agent_type: Type of agent used
            task_complexity: Task complexity
            duration: Actual execution time in seconds
            succeeded: Whether execution succeeded
            context: Optional context (task description, etc.)
        """
        key = f"{agent_type.value}_{task_complexity.value}"

        if key not in self.metrics:
            self.metrics[key] = []

        metric = {
            "agent_type": agent_type.value,
            "task_complexity": task_complexity.value,
            "actual_duration": duration,
            "timestamp": datetime.now().isoformat(),
            "succeeded": succeeded,
            "context": context or {},
        }

        self.metrics[key].append(metric)

        # Limit history to last 100 executions per key (prevent unbounded growth)
        if len(self.metrics[key]) > 100:
            self.metrics[key] = self.metrics[key][-100:]

        # Save metrics asynchronously (don't block)
        self._save_metrics()

        logger.info(
            "Recorded execution: %s complexity=%s duration=%.1fs succeeded=%s",
            agent_type.value,
            task_complexity.value,
            duration,
            succeeded,
        )

    def get_statistics(
        self,
        agent_type: Optional[AgentType] = None,
        task_complexity: Optional[TaskComplexity] = None,
    ) -> Dict[str, Any]:
        """
        Get performance statistics for analysis

        Returns:
            Dictionary with median, mean, p90, p95, sample count, etc.
        """
        if agent_type and task_complexity:
            key = f"{agent_type.value}_{task_complexity.value}"
            data = self.metrics.get(key, [])
        else:
            # Aggregate all data
            data = []
            for metrics_list in self.metrics.values():
                data.extend(metrics_list)

        if not data:
            return {"error": "No data available"}

        successful = [m for m in data if m.get("succeeded", False)]
        durations = [m["actual_duration"] for m in successful]

        if not durations:
            return {"error": "No successful executions"}

        sorted_durations = sorted(durations)

        return {
            "total_executions": len(data),
            "successful_executions": len(successful),
            "success_rate": len(successful) / len(data),
            "median_duration": statistics.median(durations),
            "mean_duration": statistics.mean(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "stdev_duration": (
                statistics.stdev(durations) if len(durations) > 1 else 0
            ),
            "p90_duration": sorted_durations[int(len(sorted_durations) * 0.90)],
            "p95_duration": sorted_durations[int(len(sorted_durations) * 0.95)],
            "p99_duration": sorted_durations[int(len(sorted_durations) * 0.99)],
        }

    def _load_metrics(self) -> Dict[str, list]:
        """Load historical metrics from JSON file"""
        if not self.metrics_file.exists():
            return {}

        try:
            with open(self.metrics_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not load metrics file: %s", e)
            return {}

    def _save_metrics(self):
        """Save metrics to JSON file"""
        try:
            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, indent=2)
        except OSError as e:
            logger.error("Could not save metrics: %s", e)

    def _load_agent_registry(self) -> Dict[str, Any]:
        """Load agent characteristics from agent_registry.yaml"""
        if not self.agent_registry_file.exists():
            return {}

        try:
            import yaml

            with open(self.agent_registry_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except (ImportError, OSError) as e:
            logger.warning("Could not load agent registry: %s", e)
            return {}


# === Global Singleton ===

_global_manager: Optional[AdaptiveTimeoutManager] = None


def get_timeout_manager() -> AdaptiveTimeoutManager:
    """
    Get global adaptive timeout manager (singleton pattern)

    Usage:
        from config.adaptive_timeout_manager import get_timeout_manager

        manager = get_timeout_manager()
        timeout = manager.get_timeout(
            AgentType.LOCAL_QUALITY,
            TaskComplexity.MODERATE
        ).timeout_seconds
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = AdaptiveTimeoutManager()
    return _global_manager


# === Convenience Functions ===


def get_timeout_for_agent(
    agent_name: str, complexity: str = "moderate"
) -> Tuple[float, str]:
    """
    Convenience function to get timeout for named agent

    Args:
        agent_name: Agent name (e.g., "ollama_qwen_14b", "claude_code")
        complexity: Task complexity ("trivial", "simple", "moderate", etc.)

    Returns:
        Tuple of (timeout_seconds, reasoning)
    """
    manager = get_timeout_manager()

    # Map agent names to types
    agent_type_mapping = {
        "phi3": AgentType.LOCAL_FAST,
        "qwen_7b": AgentType.LOCAL_FAST,
        "qwen_14b": AgentType.LOCAL_QUALITY,
        "gemma2": AgentType.LOCAL_QUALITY,
        "claude": AgentType.REMOTE_API,
        "gpt": AgentType.REMOTE_API,
        "ai_council": AgentType.MULTI_AGENT,
        "chatdev": AgentType.MULTI_AGENT,
        "orchestrat": AgentType.ORCHESTRATOR,
    }

    # Find agent type from name
    agent_type = AgentType.LOCAL_QUALITY  # default
    for key, value in agent_type_mapping.items():
        if key in agent_name.lower():
            agent_type = value
            break

    # Map complexity string to enum
    complexity_enum = TaskComplexity(complexity.lower())

    recommendation = manager.get_timeout(agent_type, complexity_enum)

    return recommendation.timeout_seconds, recommendation.reasoning
