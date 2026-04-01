"""Submit diverse development tasks to the queue."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.background_task_orchestrator import (
    BackgroundTaskOrchestrator,
    TaskPriority,
    TaskTarget,
)


async def main():
    bg = BackgroundTaskOrchestrator()

    # Game Development Code Generation
    game_dev_tasks = [
        (
            "Generate a complete Python class for a 2D sprite animation state machine with frame management, state transitions, and update logic",
            TaskPriority.HIGH,
        ),
        (
            "Create a Python inventory system with ItemStack, Inventory, and save/load JSON serialization",
            TaskPriority.HIGH,
        ),
        (
            "Generate Python code for a turn-based combat system with AttackAction, DefendAction, and SkillAction classes",
            TaskPriority.NORMAL,
        ),
        (
            "Create a Python particle emitter class with position, velocity, lifetime, and color gradients",
            TaskPriority.NORMAL,
        ),
    ]

    # Full-Stack Development
    fullstack_tasks = [
        (
            "Generate a FastAPI router with GET, POST, PUT, DELETE endpoints for a User resource with Pydantic validation",
            TaskPriority.HIGH,
        ),
        (
            "Create SQLAlchemy models for User, Project, Task with relationships and timestamps",
            TaskPriority.HIGH,
        ),
        (
            "Generate a React TypeScript functional component for a task queue dashboard with real-time WebSocket updates",
            TaskPriority.NORMAL,
        ),
        (
            "Create a Python async batch processor using asyncio.gather with rate limiting and error handling",
            TaskPriority.CRITICAL,
        ),
    ]

    # Testing & Quality
    testing_tasks = [
        (
            "Generate comprehensive pytest tests for BackgroundTaskOrchestrator including mocks, fixtures, and edge cases",
            TaskPriority.HIGH,
        ),
        (
            "Create pytest tests for parallel task processing with asyncio using pytest-asyncio",
            TaskPriority.NORMAL,
        ),
        (
            "Generate property-based tests using Hypothesis for task queue edge cases",
            TaskPriority.NORMAL,
        ),
    ]

    # DevOps
    devops_tasks = [
        (
            "Generate a multi-stage Dockerfile for NuSyQ with Poetry, healthcheck, and non-root user",
            TaskPriority.NORMAL,
        ),
        (
            "Create docker-compose.yml with app, Ollama, Redis, and Postgres services with volumes and networks",
            TaskPriority.NORMAL,
        ),
        (
            "Generate GitHub Actions workflow with pytest, ruff, black, and deployment to production",
            TaskPriority.NORMAL,
        ),
    ]

    all_tasks = game_dev_tasks + fullstack_tasks + testing_tasks + devops_tasks
    submitted = []

    print("🚀 Submitting code generation tasks...")
    for prompt, priority in all_tasks:
        task = bg.submit_task(
            prompt=prompt,
            target=TaskTarget.OLLAMA,
            priority=priority,
            requesting_agent="github_copilot",
            metadata={
                "category": "code_generation",
                "produces_code": True,
                "batch": "dev_enhancement",
            },
        )
        submitted.append(task.task_id)
        emoji = (
            "🎮"
            if "sprite" in prompt or "particle" in prompt or "combat" in prompt
            else (
                "🌐"
                if "FastAPI" in prompt or "React" in prompt or "SQL" in prompt
                else "🧪"
                if "pytest" in prompt or "test" in prompt
                else "🔧"
            )
        )
        print(f"{emoji} [{priority.name:8}] {prompt[:65]}...")

    print(f"\n✅ Submitted {len(submitted)} codegen tasks")
    print(f"Task IDs: {submitted[:3]}...")

    stats = bg.get_queue_stats()
    print(f"Queue now: {stats['queued']} queued, {stats['completed']} completed")


if __name__ == "__main__":
    asyncio.run(main())
