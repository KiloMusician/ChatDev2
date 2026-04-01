#!/usr/bin/env python3
"""NuSyQ System Optimizer - Analyzes and improves system efficiency.

Identifies:
- Duplicate tasks (wastes resources)
- Stale/orphaned tasks
- Missing result application
- Underutilized capabilities
- Optimization opportunities

Fixes:
- Deduplicates queue
- Archives completed results
- Generates actionable improvement tasks
- Connects results to actual code changes
"""

import json
import logging
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SystemOptimizer")


class SystemOptimizer:
    """Analyzes and optimizes the NuSyQ system."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.data_path = self.project_root / "data"
        self.results_path = self.data_path / "task_results"
        self.results_path.mkdir(parents=True, exist_ok=True)

    def analyze_queue_efficiency(self) -> dict:
        """Analyze task queue for inefficiencies."""
        from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator

        bg = BackgroundTaskOrchestrator()

        # Count duplicates
        prompts = [t.prompt for t in bg.tasks.values()]
        prompt_counts = Counter(prompts)

        # Analyze by status
        by_status = Counter(t.status.name for t in bg.tasks.values())

        # Analyze by target
        by_target = Counter(t.target.name for t in bg.tasks.values())

        # Find tasks without results
        completed_no_result = [t for t in bg.tasks.values() if t.status.name == "COMPLETED" and not t.result]

        return {
            "total_tasks": len(bg.tasks),
            "unique_prompts": len(set(prompts)),
            "duplicate_count": sum(c - 1 for c in prompt_counts.values() if c > 1),
            "duplicate_rate": (1 - len(set(prompts)) / len(prompts)) * 100 if prompts else 0,
            "by_status": dict(by_status),
            "by_target": dict(by_target),
            "top_duplicates": [(p[:50], c) for p, c in prompt_counts.most_common(5) if c > 1],
            "completed_no_result": len(completed_no_result),
        }

    def deduplicate_queue(self, dry_run: bool = True) -> dict:
        """Remove duplicate queued tasks, keeping one of each."""
        from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator

        bg = BackgroundTaskOrchestrator()

        # Group queued tasks by prompt
        queued = [t for t in bg.tasks.values() if t.status.name == "QUEUED"]
        by_prompt = {}
        for task in queued:
            if task.prompt not in by_prompt:
                by_prompt[task.prompt] = []
            by_prompt[task.prompt].append(task)

        # Find duplicates to remove
        to_remove = []
        for _prompt, tasks in by_prompt.items():
            if len(tasks) > 1:
                # Keep highest priority, remove rest
                tasks.sort(key=lambda t: t.priority.value, reverse=True)
                to_remove.extend(tasks[1:])  # Remove all but first

        if not dry_run and to_remove:
            for task in to_remove:
                del bg.tasks[task.task_id]
            bg._save_tasks()

        return {
            "duplicates_found": len(to_remove),
            "unique_prompts_with_dupes": len([p for p, t in by_prompt.items() if len(t) > 1]),
            "dry_run": dry_run,
            "removed": not dry_run,
        }

    def archive_completed_results(self) -> dict:
        """Save completed task results to files for review/application."""
        from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator

        bg = BackgroundTaskOrchestrator()

        completed = [t for t in bg.tasks.values() if t.status.name == "COMPLETED" and t.result]

        archived = 0
        for task in completed:
            # Create archive file
            archive_file = self.results_path / f"{task.task_id}.json"
            if not archive_file.exists():
                archive_data = {
                    "task_id": task.task_id,
                    "prompt": task.prompt,
                    "result": task.result,
                    "model": task.model,
                    "target": task.target.name,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "requesting_agent": task.requesting_agent,
                }
                with open(archive_file, "w") as f:
                    json.dump(archive_data, f, indent=2)
                archived += 1

        return {
            "total_completed": len(completed),
            "newly_archived": archived,
            "archive_path": str(self.results_path),
        }

    def generate_improvement_tasks(self) -> list:
        """Generate actionable tasks based on analysis."""
        from src.orchestration.background_task_orchestrator import (
            BackgroundTaskOrchestrator,
            TaskPriority,
            TaskTarget,
        )

        bg = BackgroundTaskOrchestrator()

        # Analyze what's missing
        existing_prompts = {t.prompt for t in bg.tasks.values()}

        improvement_prompts = [
            # System improvements
            (
                "Implement task deduplication in BackgroundTaskOrchestrator.submit_task() to prevent duplicate prompts",
                TaskPriority.HIGH,
            ),
            ("Add result caching with hash-based lookup for identical prompts", TaskPriority.HIGH),
            (
                "Create task result applier that converts LLM suggestions into actual code changes",
                TaskPriority.HIGH,
            ),
            # Full-stack development capabilities
            (
                "Design a project scaffold generator supporting Python, TypeScript, and GDScript",
                TaskPriority.NORMAL,
            ),
            ("Create database migration generator for SQLAlchemy and Prisma", TaskPriority.NORMAL),
            ("Implement API client generator from OpenAPI specs", TaskPriority.NORMAL),
            # Game development
            (
                "Generate Godot 4 GDScript template for a 2D platformer character controller",
                TaskPriority.NORMAL,
            ),
            (
                "Create Unity C# template for inventory system with item stacking",
                TaskPriority.NORMAL,
            ),
            ("Design a game state machine pattern for turn-based combat", TaskPriority.NORMAL),
            # DevOps pipeline
            ("Generate Terraform module for AWS Lambda deployment", TaskPriority.LOW),
            (
                "Create Kubernetes deployment manifest with health checks and autoscaling",
                TaskPriority.LOW,
            ),
            # Self-improvement
            (
                "Analyze src/orchestration/ and identify functions that should be async but aren't",
                TaskPriority.NORMAL,
            ),
            (
                "Generate comprehensive error handling wrapper for all API calls",
                TaskPriority.NORMAL,
            ),
            (
                "Design telemetry and metrics collection for task processing performance",
                TaskPriority.NORMAL,
            ),
        ]

        submitted = []
        for prompt, priority in improvement_prompts:
            if prompt not in existing_prompts:
                task = bg.submit_task(
                    prompt=prompt,
                    target=TaskTarget.OLLAMA,
                    priority=priority,
                    requesting_agent="system_optimizer",
                    metadata={"category": "system_improvement", "auto_generated": True},
                )
                submitted.append(task.task_id)

        return submitted

    def run_full_optimization(self) -> dict:
        """Run complete optimization cycle."""
        logger.info("=" * 60)
        logger.info("  SYSTEM OPTIMIZATION CYCLE")
        logger.info("=" * 60)

        # 1. Analyze
        logger.info("\n📊 Analyzing queue efficiency...")
        analysis = self.analyze_queue_efficiency()
        logger.info(f"   Total tasks: {analysis['total_tasks']}")
        logger.info(f"   Unique prompts: {analysis['unique_prompts']}")
        logger.info(f"   Duplicate rate: {analysis['duplicate_rate']:.1f}%")

        # 2. Deduplicate (dry run first)
        logger.info("\n🔄 Checking for duplicates...")
        dedup_check = self.deduplicate_queue(dry_run=True)
        logger.info(f"   Found {dedup_check['duplicates_found']} duplicate tasks")

        # 3. Archive results
        logger.info("\n📁 Archiving completed results...")
        archive = self.archive_completed_results()
        logger.info(f"   Archived {archive['newly_archived']} new results")

        # 4. Generate improvements
        logger.info("\n🚀 Generating improvement tasks...")
        new_tasks = self.generate_improvement_tasks()
        logger.info(f"   Created {len(new_tasks)} new improvement tasks")

        logger.info("\n" + "=" * 60)
        logger.info("  OPTIMIZATION COMPLETE")
        logger.info("=" * 60)

        return {
            "analysis": analysis,
            "deduplication": dedup_check,
            "archive": archive,
            "new_tasks": new_tasks,
        }


def main():
    optimizer = SystemOptimizer()
    result = optimizer.run_full_optimization()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
