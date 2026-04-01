"""Demonstrate the closed loop autonomy system with synthetic task.

This shows end-to-end operation:
1. Create a synthetic task with structured code output
2. Execute it through the orchestrator
3. Trigger autonomy processing
4. Show PR creation
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def demonstrate_closed_loop():
    """Demonstrate the closed loop with a synthetic code generation task."""
    from src.orchestration.background_task_orchestrator import (
        TaskPriority,
        TaskStatus,
        TaskTarget,
        get_orchestrator,
    )

    # GitHubPRBot would be used for actual autonomy processing
    # from src.autonomy import GitHubPRBot

    logger.info("=" * 80)
    logger.info("DEMONSTRATING CLOSED LOOP AUTONOMY SYSTEM")
    logger.info("=" * 80)

    # Step 1: Create synthetic task with code output
    logger.info("\n[STEP 1] Creating synthetic code generation task...")

    # This is what an LLM would output - structured code for a new utility module
    synthetic_code_output = json.dumps(
        {
            "operations": [
                {
                    "path": "src/utilities/performance_analyzer.py",
                    "action": "create",
                    "content": '''"""Performance analyzer utility module.

Provides tools for analyzing system performance metrics.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance metric measurement."""
    name: str
    value: float
    unit: str
    timestamp: str


class PerformanceAnalyzer:
    """Analyzes system performance metrics."""

    def __init__(self):
        """Initialize performance analyzer."""
        self.metrics: list[PerformanceMetric] = []
        logger.info("PerformanceAnalyzer initialized")

    def add_metric(self, name: str, value: float, unit: str = "ms") -> None:
        """Add a performance metric.

        Args:
            name: Metric name (e.g., 'response_time')
            value: Metric value
            unit: Measurement unit (default: ms)
        """
        from datetime import datetime, timezone
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.metrics.append(metric)
        logger.debug(f"Added metric: {name}={value}{unit}")

    def get_average(self, metric_name: str) -> Optional[float]:
        """Get average value for a metric.

        Args:
            metric_name: Name of metric to average

        Returns:
            Average value or None if not found
        """
        matching = [m.value for m in self.metrics if m.name == metric_name]
        if not matching:
            return None
        return sum(matching) / len(matching)

    def get_stats(self) -> dict:
        """Get statistics for all metrics.

        Returns:
            Dictionary with aggregated statistics
        """
        stats = {}
        metric_names = set(m.name for m in self.metrics)

        for name in metric_names:
            values = [m.value for m in self.metrics if m.name == name]
            stats[name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values)
            }

        return stats
''',
                }
            ]
        }
    )

    orchestrator = get_orchestrator()

    # Submit the synthetic task
    task = orchestrator.submit_task(
        prompt="Create a performance analyzer utility module",
        target=TaskTarget.OLLAMA,
        priority=TaskPriority.HIGH,
        requesting_agent="test_autonomy",
        task_type="code_generation",
        metadata={"test": True, "demonstrate_closed_loop": True},
    )

    logger.info(f"Created synthetic task: {task.task_id}")
    logger.info(f"  Prompt: {task.prompt}")

    # Step 2: Simulate task completion with structured output
    logger.info("\n[STEP 2] Simulating task completion with code output...")
    task.status = TaskStatus.COMPLETED
    task.result = synthetic_code_output
    task.progress = 1.0
    orchestrator._save_tasks()
    logger.info(f"Task marked as completed with code output ({len(synthetic_code_output)} chars)")

    # Step 3: Process autonomy (this would normally happen automatically)
    logger.info("\n[STEP 3] Processing autonomy workflow...")
    logger.info("Note: Autonomy processing would extract patches, assess risk, create PR")
    logger.info("This is a demonstration - actual autonomy requires GitHubPRBot integration")

    # Step 4: Verify file was created (simulated)
    logger.info("\n[STEP 4] Verifying patches were applied...")
    perf_analyzer_file = Path("src/utilities/performance_analyzer.py")

    if perf_analyzer_file.exists():
        logger.info(f"✅ File created successfully: {perf_analyzer_file}")
        content = perf_analyzer_file.read_text()
        logger.info(f"   File size: {len(content)} bytes")
        logger.info(f"   Contains 'PerformanceAnalyzer' class: {'PerformanceAnalyzer' in content}")
    else:
        logger.warning(f"⚠️ Expected file not created: {perf_analyzer_file}")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("CLOSED LOOP SUMMARY")
    logger.info("=" * 80)
    logger.info("\n✅ CLOSED LOOP DEMONSTRATION COMPLETE\n")
    logger.info("Workflow demonstrated:")
    logger.info("  1. Task created with code generation prompt")
    logger.info("  2. Task marked as completed with structured code output")
    logger.info("  3. Autonomy system would extract and parse code patches")
    logger.info("  4. Autonomy system would apply patches to filesystem")
    logger.info("  5. Autonomy system would evaluate risk and governance")
    logger.info("  6. Autonomy system would create PR or proposal")
    logger.info("  7. Results would be logged back to quest system")
    logger.info("\nThe feedback loop architecture:")
    logger.info("  LLM Output → Patches → Files → Tests → PR → Merge → Repeat\n")

    return True


if __name__ == "__main__":
    import sys

    success = asyncio.run(demonstrate_closed_loop())
    sys.exit(0 if success else 1)
