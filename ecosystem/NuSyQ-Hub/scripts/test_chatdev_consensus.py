#!/usr/bin/env python3
"""ChatDev Multi-Model Consensus Test
===================================

Tests multi-model consensus using installed Ollama models for a simple
code generation task. Validates orchestrator → ChatDev integration.

OmniTag: {
    "purpose": "Test ChatDev multi-model consensus with Ollama models",
    "dependencies": ["multi_ai_orchestrator", "ollama", "chatdev"],
    "context": "Validation of local LLM multi-agent coordination",
    "evolution_stage": "v1.0"
}
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.orchestration.unified_ai_orchestrator import (
    MultiAIOrchestrator,
    OrchestrationTask,
    TaskPriority,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_chatdev_consensus():
    """Test ChatDev consensus with multiple Ollama models"""
    logger.info("🧪 Starting ChatDev Consensus Test")

    # Load model configuration
    config_path = Path(__file__).parent.parent / "config" / "chatdev_ollama_models.json"
    with open(config_path, encoding="utf-8") as f:
        model_config = json.load(f)

    logger.info(f"📋 Loaded model configuration: {model_config['agent_assignments']}")

    # Initialize orchestrator
    orchestrator = MultiAIOrchestrator()
    logger.info("✅ Orchestrator initialized")

    # Create test task (using correct OrchestrationTask fields)
    task = OrchestrationTask(
        task_id="chatdev_consensus_001",
        task_type="code_generation",
        content=(
            "Generate a simple Python function that calculates the Fibonacci sequence "
            "using memoization. Include docstring, type hints, and pytest test."
        ),
        context={
            "consensus_mode": True,
            "models": model_config["consensus_pools"]["high_quality"],
            "target_file": "fibonacci_memoized.py",
            "ollama_endpoint": model_config["ollama_endpoint"],
        },
        priority=TaskPriority.HIGH,
    )

    logger.info(f"📝 Task created: {task.task_id}")
    logger.info(f"🤖 Consensus models: {task.context['models']}")

    # Submit task (using correct method name)
    orchestrator.submit_task(task)
    logger.info("✅ Task submitted")

    # Start orchestration (this will run in background)
    logger.info("🚀 Starting orchestration...")
    orchestrator.start_orchestration()

    # Wait for task completion or timeout
    max_wait = 180  # 3 minutes
    waited = 0
    check_interval = 5

    while waited < max_wait:
        await asyncio.sleep(check_interval)
        waited += check_interval

        if task.task_id in orchestrator.completed_tasks:
            completed = orchestrator.completed_tasks[task.task_id]
            logger.info(f"✅ Task completed: {completed.status}")
            logger.info(f"📊 Result: {completed.result}")

            # Save result
            output_dir = Path(__file__).parent.parent / "data" / "chatdev_tests"
            output_dir.mkdir(parents=True, exist_ok=True)

            result_file = output_dir / f"consensus_result_{task.task_id}.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "task_id": completed.task_id,
                        "status": completed.status.value,
                        "result": completed.result,
                        "models": task.context["models"],
                        "execution_time": waited,
                    },
                    f,
                    indent=2,
                )

            logger.info(f"💾 Result saved to: {result_file}")
            break

        if waited % 30 == 0:
            logger.info(f"⏳ Waiting for task completion... ({waited}s / {max_wait}s)")

    else:
        logger.warning(f"⚠️ Task timeout after {max_wait}s")

    # Stop orchestration
    orchestrator.stop_orchestration()
    logger.info("🛑 Orchestration stopped")


if __name__ == "__main__":
    asyncio.run(test_chatdev_consensus())
