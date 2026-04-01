#!/usr/bin/env python3
"""SNS-CORE Orchestrator Adapter - Token-Efficient AI Coordination.

==================================================================

Adapter layer that adds SNS-CORE notation support to MultiAIOrchestrator,
enabling 40-50% token reduction in AI-to-AI communication.

Features:
- Traditional prompt → SNS-CORE notation conversion
- Automatic system routing with SNS templates
- Token usage tracking and comparison
- Backward compatible with existing orchestrator
- A/B testing support for validation

Integration:
    from src.orchestration.sns_orchestrator_adapter import SNSOrchestratorAdapter

    orchestrator = SNSOrchestratorAdapter()
    result = await orchestrator.execute_task_sns(
        "Analyze this code for security issues",
        enable_sns=True  # Toggle SNS-CORE on/off
    )

Author: NuSyQ Development Team
Version: 1.0.0 (SNS-CORE Pilot)
Date: October 13, 2025
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Import base orchestrator
try:
    from src.orchestration.unified_ai_orchestrator import (AISystemType,
                                                           MultiAIOrchestrator,
                                                           OrchestrationTask)
except ImportError:
    from multi_ai_orchestrator import (AISystemType, MultiAIOrchestrator,
                                       OrchestrationTask)

# Import SNS-CORE integration
from src.ai.sns_core_integration import SNSCoreConverter, SNSCoreHelper

logger = logging.getLogger(__name__)


class SNSMode(Enum):
    """SNS-CORE operation modes."""

    DISABLED = "disabled"  # Use traditional prompts only
    ENABLED = "enabled"  # Use SNS-CORE notation
    AB_TEST = "ab_test"  # Run both and compare
    AUTO = "auto"  # Auto-select based on task complexity


@dataclass
class SNSMetrics:
    """Metrics for SNS-CORE performance tracking."""

    task_id: str
    traditional_tokens: int
    sns_tokens: int
    tokens_saved: int
    savings_percent: float
    compression_ratio: float
    traditional_time_ms: float = 0.0
    sns_time_ms: float = 0.0
    time_saved_ms: float = 0.0
    responses_match: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


class SNSOrchestratorAdapter(MultiAIOrchestrator):
    """SNS-CORE enabled orchestrator adapter.

    Extends MultiAIOrchestrator with SNS-CORE notation support
    for token-efficient AI coordination.
    """

    def __init__(self, config_path: Path | None = None, sns_mode: SNSMode = SNSMode.AUTO) -> None:
        """Initialize SNS-CORE orchestrator adapter.

        Args:
            config_path: Path to orchestrator configuration file
            sns_mode: SNS-CORE operation mode (DISABLED, ENABLED, AB_TEST, AUTO)

        """
        super().__init__(config_path)

        self.sns_mode = sns_mode
        self.sns_helper = SNSCoreHelper()
        self.sns_converter = SNSCoreConverter()

        # SNS metrics tracking
        self.sns_metrics: dict[str, SNSMetrics] = {}
        self.total_tokens_saved = 0
        self.total_time_saved_ms = 0.0

        # SNS configuration
        self.sns_config = {
            "enable_validation": True,
            "fallback_on_error": True,
            "log_conversions": True,
            "track_metrics": True,
            "ab_test_percentage": 0.2,  # 20% of tasks run A/B test
        }

        logger.info("SNSOrchestratorAdapter initialized with mode: %s", sns_mode.value)

    def _should_use_sns(self, task: OrchestrationTask) -> bool:
        """Determine whether to use SNS-CORE for this task."""
        if self.sns_mode == SNSMode.DISABLED:
            return False
        if self.sns_mode == SNSMode.ENABLED:
            return True
        if self.sns_mode == SNSMode.AB_TEST:
            return True  # A/B test runs both
        if self.sns_mode == SNSMode.AUTO:
            # Auto-select based on task complexity
            # Use SNS for multi-step tasks with >50 token prompts
            token_count = len(task.content.split()) * 1.3  # Rough token estimate
            return token_count > 50
        return False

    async def execute_task_sns(
        self,
        content: str,
        task_type: str = "analysis",
        context: dict[str, Any] | None = None,
        enable_sns: bool | None = None,
        preferred_systems: list[AISystemType] | None = None,
    ) -> dict[str, Any]:
        """Execute task with optional SNS-CORE notation.

        Args:
            content: Task description (natural language or SNS notation)
            task_type: Type of task (analysis, generation, coordination, etc.)
            context: Additional context for task execution
            enable_sns: Override sns_mode for this specific task
            preferred_systems: Preferred AI systems to use

        Returns:
            Task result with SNS metrics if enabled

        """
        import uuid

        task_id = f"sns_task_{uuid.uuid4().hex[:8]}"

        # Create orchestration task
        task = OrchestrationTask(
            task_id=task_id,
            task_type=task_type,
            content=content,
            context=context or {},
            preferred_systems=preferred_systems or [],
        )

        # Determine SNS usage
        use_sns = enable_sns if enable_sns is not None else self._should_use_sns(task)

        if not use_sns:
            # Traditional execution
            return await self._execute_task_traditional(task)

        if self.sns_mode == SNSMode.AB_TEST:
            # A/B test: Run both and compare
            return await self._execute_task_ab_test(task)
        # SNS-CORE execution
        return await self._execute_task_with_sns(task)

    async def _execute_task_traditional(self, task: OrchestrationTask) -> dict[str, Any]:
        """Execute task using traditional prompts (no SNS-CORE)."""
        start_time = datetime.now()

        # Execute task using base orchestrator
        execution_result = await self.orchestrate_task_async(task=task)
        result = execution_result.get("primary_result", {})

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "task_id": task.task_id,
            "result": result,
            "mode": "traditional",
            "execution_time_ms": elapsed_ms,
            "status": task.status.value,
        }

    async def _execute_task_with_sns(self, task: OrchestrationTask) -> dict[str, Any]:
        """Execute task using SNS-CORE notation."""
        start_time = datetime.now()

        # Convert task content to SNS notation
        traditional_prompt = task.content
        sns_prompt = self._convert_to_sns(task)

        # Validate SNS notation
        if self.sns_config["enable_validation"]:
            is_valid, errors = self.sns_helper.validate_sns(sns_prompt)
            if not is_valid:
                logger.warning("SNS validation failed for task %s: %s", task.task_id, errors)
                if self.sns_config["fallback_on_error"]:
                    logger.info("Falling back to traditional prompt for task %s", task.task_id)
                    return await self._execute_task_traditional(task)

        # Update task content with SNS notation
        task.content = sns_prompt

        # Calculate token metrics
        metrics = self.sns_helper.compare_token_counts(traditional_prompt, sns_prompt)

        # Execute task using base orchestrator
        execution_result = await self.orchestrate_task_async(task=task)
        result = execution_result.get("primary_result", {})

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Track metrics
        if self.sns_config["track_metrics"]:
            sns_metrics = SNSMetrics(
                task_id=task.task_id,
                traditional_tokens=metrics["traditional_tokens"],
                sns_tokens=metrics["sns_tokens"],
                tokens_saved=metrics["tokens_saved"],
                savings_percent=metrics["savings_percent"],
                compression_ratio=metrics["compression_ratio"],
                sns_time_ms=elapsed_ms,
            )
            self.sns_metrics[task.task_id] = sns_metrics
            self.total_tokens_saved += metrics["tokens_saved"]

        return {
            "task_id": task.task_id,
            "result": result,
            "mode": "sns_core",
            "execution_time_ms": elapsed_ms,
            "status": task.status.value,
            "sns_metrics": {
                "traditional_tokens": metrics["traditional_tokens"],
                "sns_tokens": metrics["sns_tokens"],
                "tokens_saved": metrics["tokens_saved"],
                "savings_percent": f"{metrics['savings_percent']:.1f}%",
                "compression_ratio": f"{metrics['compression_ratio']:.2f}x",
            },
        }

    async def _execute_task_ab_test(self, task: OrchestrationTask) -> dict[str, Any]:
        """Execute task with A/B test (both traditional and SNS-CORE)."""
        import copy

        # Create two copies of the task
        task_traditional = copy.deepcopy(task)
        task_traditional.task_id = f"{task.task_id}_traditional"

        task_sns = copy.deepcopy(task)
        task_sns.task_id = f"{task.task_id}_sns"
        task_sns.content = self._convert_to_sns(task_sns)

        # Execute both in parallel
        traditional_start = datetime.now()
        exec_trad = await self.orchestrate_task_async(task=task_traditional)
        result_traditional = exec_trad.get("primary_result", {})
        traditional_time = (datetime.now() - traditional_start).total_seconds() * 1000

        sns_start = datetime.now()
        exec_sns = await self.orchestrate_task_async(task=task_sns)
        result_sns = exec_sns.get("primary_result", {})
        sns_time = (datetime.now() - sns_start).total_seconds() * 1000

        # Calculate metrics
        metrics = self.sns_helper.compare_token_counts(task.content, task_sns.content)

        # Compare responses
        responses_match = self._compare_responses(result_traditional, result_sns)

        # Track A/B test metrics
        ab_metrics = SNSMetrics(
            task_id=task.task_id,
            traditional_tokens=metrics["traditional_tokens"],
            sns_tokens=metrics["sns_tokens"],
            tokens_saved=metrics["tokens_saved"],
            savings_percent=metrics["savings_percent"],
            compression_ratio=metrics["compression_ratio"],
            traditional_time_ms=traditional_time,
            sns_time_ms=sns_time,
            time_saved_ms=traditional_time - sns_time,
            responses_match=responses_match,
        )
        self.sns_metrics[task.task_id] = ab_metrics

        return {
            "task_id": task.task_id,
            "mode": "ab_test",
            "traditional_result": result_traditional,
            "sns_result": result_sns,
            "comparison": {
                "tokens_saved": metrics["tokens_saved"],
                "savings_percent": f"{metrics['savings_percent']:.1f}%",
                "time_saved_ms": traditional_time - sns_time,
                "responses_match": responses_match,
            },
            "metrics": {
                "traditional": {
                    "tokens": metrics["traditional_tokens"],
                    "time_ms": traditional_time,
                },
                "sns_core": {"tokens": metrics["sns_tokens"], "time_ms": sns_time},
            },
        }

    def _convert_to_sns(self, task: OrchestrationTask) -> str:
        """Convert task content to SNS-CORE notation."""
        # Detect task type and use appropriate template
        use_case = self._detect_use_case(task)

        if use_case:
            # Use template for known use cases
            template = self.sns_helper.get_sns_template(use_case)
            # Customize template with task-specific content
            return self._customize_sns_template(template, task)
        # Generic conversion
        return self.sns_helper.convert_to_sns(task.content)

    def _detect_use_case(self, task: OrchestrationTask) -> str | None:
        """Detect SNS use case from task properties."""
        # Map task types to SNS templates
        use_case_map = {
            "orchestration": "orchestrator",
            "agent_communication": "chatdev_agent",
            "error_resolution": "quantum_resolver",
            "consciousness": "consciousness_bridge",
            "model_routing": "ollama_routing",
            "rag": "rag_orchestrator",
        }

        # Check task type
        if task.task_type in use_case_map:
            return use_case_map[task.task_type]

        # Check required capabilities
        if "consciousness_simulation" in task.required_capabilities:
            return "consciousness_bridge"
        if "software_development" in task.required_capabilities:
            return "chatdev_agent"
        if "quantum_computing" in task.required_capabilities:
            return "quantum_resolver"

        return None

    def _customize_sns_template(self, template: str, task: OrchestrationTask) -> str:
        """Customize SNS template with task-specific content."""
        # Extract key entities from task content
        content_parts = task.content.split("\n")

        # Simple customization: replace placeholder with first line
        if content_parts:
            return f"# {content_parts[0]}\n{template}"

        return template

    def _compare_responses(self, result1: Any, result2: Any) -> bool:
        """Compare two task results for semantic similarity using multiple strategies."""
        # Strategy 1: Exact equality
        if result1 == result2:
            return True

        # Strategy 2: dict comparison with status checks
        if isinstance(result1, dict) and isinstance(result2, dict):
            status1 = result1.get("status", "unknown")
            status2 = result2.get("status", "unknown")

            # Both succeeded/failed
            if status1 == status2:
                # Check additional similarity metrics
                output1 = str(result1.get("output", ""))
                output2 = str(result2.get("output", ""))

                # Simple string similarity (Jaccard on words)
                if output1 and output2:
                    words1 = set(output1.lower().split())
                    words2 = set(output2.lower().split())
                    intersection = len(words1 & words2)
                    union = len(words1 | words2)
                    jaccard_similarity = intersection / union if union > 0 else 0

                    # Consider semantically similar if >70% word overlap
                    return jaccard_similarity > 0.7

                return True

        # Strategy 3: String comparison with semantic similarity
        str1, str2 = str(result1), str(result2)
        if str1 == str2:
            return True

        # Basic token-level similarity for strings
        tokens1 = set(str1.lower().split())
        tokens2 = set(str2.lower().split())
        if tokens1 and tokens2:
            jaccard = len(tokens1 & tokens2) / len(tokens1 | tokens2)
            return jaccard > 0.7

        return False

    def get_sns_metrics_summary(self) -> dict[str, Any]:
        """Get summary of SNS-CORE performance metrics."""
        if not self.sns_metrics:
            return {"total_tasks": 0, "message": "No SNS-CORE tasks executed yet"}

        total_tasks = len(self.sns_metrics)
        total_traditional_tokens = sum(m.traditional_tokens for m in self.sns_metrics.values())
        total_sns_tokens = sum(m.sns_tokens for m in self.sns_metrics.values())
        total_saved = sum(m.tokens_saved for m in self.sns_metrics.values())

        avg_savings_percent = (
            (total_saved / total_traditional_tokens * 100) if total_traditional_tokens > 0 else 0
        )
        avg_compression = (
            (total_traditional_tokens / total_sns_tokens) if total_sns_tokens > 0 else 1.0
        )

        return {
            "total_tasks": total_tasks,
            "total_traditional_tokens": total_traditional_tokens,
            "total_sns_tokens": total_sns_tokens,
            "total_tokens_saved": total_saved,
            "average_savings_percent": f"{avg_savings_percent:.1f}%",
            "average_compression_ratio": f"{avg_compression:.2f}x",
            "estimated_annual_savings": self._estimate_annual_savings(avg_savings_percent),
        }

    def _estimate_annual_savings(self, avg_savings_percent: float) -> str:
        """Estimate annual cost savings from SNS-CORE usage."""
        # Conservative estimate based on current usage patterns
        monthly_tokens_baseline = 6_700_000  # From evaluation
        tokens_saved_monthly = monthly_tokens_baseline * (avg_savings_percent / 100)
        tokens_saved_yearly = tokens_saved_monthly * 12

        # Cost estimates ($0.002 per 1K tokens average)
        cost_per_million = 2.0
        yearly_savings = (tokens_saved_yearly / 1_000_000) * cost_per_million

        return f"${yearly_savings:.2f}/year (estimated, {avg_savings_percent:.1f}% reduction)"

    def export_sns_metrics(self, output_path: Path) -> bool:
        """Export SNS-CORE metrics to JSON file."""
        try:
            metrics_data = {"summary": self.get_sns_metrics_summary(), "tasks": []}

            for task_id, metrics in self.sns_metrics.items():
                metrics_data["tasks"].append(
                    {
                        "task_id": task_id,
                        "traditional_tokens": metrics.traditional_tokens,
                        "sns_tokens": metrics.sns_tokens,
                        "tokens_saved": metrics.tokens_saved,
                        "savings_percent": metrics.savings_percent,
                        "compression_ratio": metrics.compression_ratio,
                        "traditional_time_ms": metrics.traditional_time_ms,
                        "sns_time_ms": metrics.sns_time_ms,
                        "time_saved_ms": metrics.time_saved_ms,
                        "responses_match": metrics.responses_match,
                        "timestamp": metrics.timestamp.isoformat(),
                    },
                )

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2)

            logger.info("SNS metrics exported to %s", output_path)
            return True

        except Exception as e:
            logger.exception("Failed to export SNS metrics: %s", e)
            return False


# Convenience function for quick SNS-CORE orchestration
async def orchestrate_with_sns(
    content: str,
    task_type: str = "analysis",
    sns_mode: SNSMode = SNSMode.AUTO,
    **kwargs,
) -> dict[str, Any]:
    """Quick orchestration with SNS-CORE support.

    Usage:
        result = await orchestrate_with_sns(
            "Analyze code security and suggest improvements",
            task_type="analysis",
            sns_mode=SNSMode.ENABLED
        )
    """
    orchestrator = SNSOrchestratorAdapter(sns_mode=sns_mode)
    return await orchestrator.execute_task_sns(content, task_type, **kwargs)


# Example usage and testing
if __name__ == "__main__":

    async def test_sns_orchestrator() -> None:
        """Test SNS-CORE orchestrator adapter."""
        # Test 1: Traditional mode
        orchestrator = SNSOrchestratorAdapter(sns_mode=SNSMode.DISABLED)
        await orchestrator.execute_task_sns(
            "Analyze this code for performance bottlenecks and suggest optimizations",
            task_type="analysis",
        )

        # Test 2: SNS-CORE enabled
        orchestrator = SNSOrchestratorAdapter(sns_mode=SNSMode.ENABLED)
        result2 = await orchestrator.execute_task_sns(
            "Extract keywords from user query, classify intent, and generate search terms for RAG system",
            task_type="rag",
        )
        if "sns_metrics" in result2:
            pass

        # Test 3: A/B test mode
        orchestrator = SNSOrchestratorAdapter(sns_mode=SNSMode.AB_TEST)
        result3 = await orchestrator.execute_task_sns(
            "Route this task to appropriate AI system, extract parameters, and format response",
            task_type="orchestration",
        )
        if "comparison" in result3:
            result3["comparison"]

        # Print metrics summary
        summary = orchestrator.get_sns_metrics_summary()
        for _key, _value in summary.items():
            pass

    # Run tests
    asyncio.run(test_sns_orchestrator())
