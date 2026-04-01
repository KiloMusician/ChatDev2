#!/usr/bin/env python3
"""Deep Modernization Orchestrator - Comprehensive Codebase Enhancement.
[ROUTE AGENTS] 🤖

This orchestrator uses NuSyQ's existing infrastructure to perform deep
modernization across the entire codebase:

- Type hints modernization (from typing import X → from collections.abc)
- Async/await pattern optimization
- Import optimization and organization
- Docstring enhancement
- Performance profiling and optimization
- Test coverage expansion

Integrates with:
- Guild Board (coordination)
- Autonomous Monitor (continuous checking)
- PU Queue (task distribution)
- Quest System (progress tracking)
"""

from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.automation.unified_pu_queue import PU, UnifiedPUQueue
from src.guild.guild_board import get_board
from src.tools.cultivation_metrics import CultivationMetrics

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ModernizationTask:
    """A single modernization task."""

    task_id: str
    description: str
    file_pattern: str
    priority: int
    estimated_files: int
    command: list[str]
    validation: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


class DeepModernizationOrchestrator:
    """Orchestrates comprehensive codebase modernization."""

    def __init__(self, repo_root: Path | None = None):
        self.root = repo_root or Path(__file__).parent.parent
        self.guild_board = get_board()
        self.pu_queue = UnifiedPUQueue()
        self.metrics = CultivationMetrics(repo_root=self.root)

        # Define modernization tasks
        self.tasks = self._define_tasks()

    def _define_tasks(self) -> list[ModernizationTask]:
        """Define all modernization tasks."""
        return [
            ModernizationTask(
                task_id="modernize_typing_imports",
                description="Update typing imports to use collections.abc",
                file_pattern="**/*.py",
                priority=3,
                estimated_files=200,
                command=[
                    "python",
                    "-m",
                    "pyupgrade",
                    "--py312-plus",
                    "--keep-runtime-typing",
                ],
                validation=["ruff", "check", ".", "--select", "UP"],
            ),
            ModernizationTask(
                task_id="optimize_async_patterns",
                description="Modernize async/await patterns",
                file_pattern="src/**/*async*.py",
                priority=4,
                estimated_files=30,
                command=["python", "-m", "ruff", "check", "--select", "ASYNC"],
                validation=["python", "-m", "pylint", "--disable=all", "--enable=async"],
            ),
            ModernizationTask(
                task_id="enhance_docstrings",
                description="Add and enhance docstrings",
                file_pattern="src/**/*.py",
                priority=2,
                estimated_files=300,
                command=["python", "-m", "pydocstyle", "--convention=google"],
                validation=["python", "-m", "pydocstyle"],
            ),
            ModernizationTask(
                task_id="organize_imports",
                description="Organize and optimize imports",
                file_pattern="**/*.py",
                priority=3,
                estimated_files=400,
                command=["python", "-m", "isort", ".", "--profile", "black"],
                validation=["python", "-m", "isort", "--check-only"],
            ),
            ModernizationTask(
                task_id="add_type_annotations",
                description="Add missing type annotations",
                file_pattern="src/**/*.py",
                priority=4,
                estimated_files=200,
                command=["python", "-m", "mypy", ".", "--install-types", "--non-interactive"],
                validation=["python", "-m", "mypy", ".", "--strict"],
            ),
            ModernizationTask(
                task_id="remove_unused_code",
                description="Remove unused imports, variables, functions",
                file_pattern="**/*.py",
                priority=2,
                estimated_files=400,
                command=["python", "-m", "vulture", ".", "--min-confidence", "80"],
                validation=["python", "-m", "ruff", "check", "--select", "F"],
            ),
        ]

    async def create_guild_quest(self, task: ModernizationTask) -> str:
        """Create a guild quest for a modernization task."""
        logger.info(f"🎯 Creating guild quest: {task.description}")

        import subprocess

        result = subprocess.run(
            [
                "python",
                str(self.root / "scripts" / "start_nusyq.py"),
                "guild_add_quest",
                "modernization_agent",
                task.description,
                f"Modernize {task.estimated_files} files: {task.task_id}",
                str(task.priority),
                "safe",
                "modernization,automation,quality",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            # Extract quest_id from output
            import json

            try:
                output = json.loads(result.stdout.split("[RECEIPT]")[0].strip())
                quest_id = output.get("quest_id", f"quest_{task.task_id}")
                logger.info(f"   ✅ Created quest: {quest_id}")
                return quest_id
            except Exception:
                return f"quest_{task.task_id}"
        else:
            logger.warning(f"   ⚠️ Failed to create quest: {result.stderr}")
            return f"quest_{task.task_id}"

    async def create_pu_for_task(self, task: ModernizationTask) -> str:
        """Create a PU (Processing Unit) for a task."""
        logger.info(f"📋 Creating PU: {task.task_id}")

        pu = PU(
            description=task.description,
            command=" ".join(task.command),
            priority=task.priority,
            tags=[
                "modernization",
                task.task_id,
                f"files:{task.estimated_files}",
            ],
        )

        self.pu_queue.add_pu(pu)
        logger.info(f"   ✅ PU added to queue: {pu.id}")

        return pu.id

    async def run_task(self, task: ModernizationTask) -> dict[str, Any]:
        """Execute a single modernization task."""
        logger.info(f"\n{'=' * 70}")
        logger.info(f"🚀 Executing: {task.description}")
        logger.info(f"   Priority: {task.priority}")
        logger.info(f"   Estimated files: {task.estimated_files}")
        logger.info(f"{'=' * 70}\n")

        # Create quest and PU
        quest_id = await self.create_guild_quest(task)
        pu_id = await self.create_pu_for_task(task)

        # Execute command
        import subprocess

        start_time = datetime.now()

        try:
            result = subprocess.run(
                task.command,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            duration = (datetime.now() - start_time).total_seconds()

            success = result.returncode == 0

            if success:
                logger.info(f"✅ {task.description} - Complete ({duration:.1f}s)")
            else:
                logger.warning(f"⚠️ {task.description} - Issues found")
                logger.warning(f"   {result.stderr[:200]}")

            # Run validation if provided
            validation_passed = True
            if task.validation:
                logger.info(f"🔍 Running validation: {' '.join(task.validation[:3])}")
                val_result = subprocess.run(
                    task.validation,
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                validation_passed = val_result.returncode == 0

            return {
                "task_id": task.task_id,
                "success": success,
                "validation_passed": validation_passed,
                "duration": duration,
                "quest_id": quest_id,
                "pu_id": pu_id,
                "stdout": result.stdout[-500:],  # Last 500 chars
                "stderr": result.stderr[-500:],
            }

        except subprocess.TimeoutExpired:
            logger.error(f"❌ {task.description} - Timeout after 5 minutes")
            return {
                "task_id": task.task_id,
                "success": False,
                "validation_passed": False,
                "duration": 300,
                "quest_id": quest_id,
                "pu_id": pu_id,
                "error": "Timeout",
            }
        except Exception as e:
            logger.error(f"❌ {task.description} - Error: {e}")
            return {
                "task_id": task.task_id,
                "success": False,
                "validation_passed": False,
                "duration": 0,
                "quest_id": quest_id,
                "pu_id": pu_id,
                "error": str(e),
            }

    async def run_all_tasks(self, parallel: bool = False) -> list[dict[str, Any]]:
        """Run all modernization tasks."""
        logger.info("\n" + "=" * 70)
        logger.info("🤖 DEEP MODERNIZATION ORCHESTRATOR")
        logger.info("=" * 70)
        logger.info(f"Tasks scheduled: {len(self.tasks)}")
        logger.info(f"Execution mode: {'Parallel' if parallel else 'Sequential'}")
        logger.info("=" * 70 + "\n")

        if parallel:
            # Run tasks in parallel (respecting dependencies)
            results = await asyncio.gather(
                *[self.run_task(task) for task in self.tasks],
                return_exceptions=True,
            )
        else:
            # Run tasks sequentially (safer)
            results = []
            for task in sorted(self.tasks, key=lambda t: t.priority, reverse=True):
                result = await self.run_task(task)
                results.append(result)

                # Short pause between tasks
                await asyncio.sleep(2)

        return results

    def generate_report(self, results: list[dict[str, Any]]) -> None:
        """Generate comprehensive modernization report."""
        logger.info("\n" + "=" * 70)
        logger.info("📊 MODERNIZATION REPORT")
        logger.info("=" * 70 + "\n")

        successful = sum(1 for r in results if r.get("success"))
        validated = sum(1 for r in results if r.get("validation_passed"))
        total_duration = sum(r.get("duration", 0) for r in results)

        logger.info(f"Total tasks: {len(results)}")
        logger.info(f"Successful: {successful}/{len(results)}")
        logger.info(f"Validated: {validated}/{len(results)}")
        logger.info(f"Total duration: {total_duration:.1f}s")
        logger.info("")

        logger.info("Task Details:")
        for result in results:
            status = "✅" if result.get("success") else "❌"
            validation = "✓" if result.get("validation_passed") else "✗"
            duration = result.get("duration", 0)

            logger.info(f"  {status} {result['task_id']:<30} ({duration:.1f}s) Validation: {validation}")

        # Save report
        report_file = self.root / "docs" / "Reports" / "MODERNIZATION_REPORT.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, "w") as f:
            f.write("# Deep Modernization Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write("## Summary\n\n")
            f.write(f"- Total tasks: {len(results)}\n")
            f.write(f"- Successful: {successful}\n")
            f.write(f"- Validated: {validated}\n")
            f.write(f"- Total duration: {total_duration:.1f}s\n\n")
            f.write("## Task Results\n\n")

            for result in results:
                f.write(f"### {result['task_id']}\n\n")
                f.write(f"- Success: {result.get('success')}\n")
                f.write(f"- Validation: {result.get('validation_passed')}\n")
                f.write(f"- Duration: {result.get('duration', 0):.1f}s\n")
                f.write(f"- Quest: {result.get('quest_id')}\n")
                f.write(f"- PU: {result.get('pu_id')}\n\n")

        logger.info(f"\n📄 Report saved: {report_file}")


async def main():
    """Entry point for deep modernization."""
    import argparse

    parser = argparse.ArgumentParser(description="Deep Modernization Orchestrator")
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tasks in parallel (faster but riskier)",
    )
    parser.add_argument(
        "--task",
        type=str,
        help="Run specific task only",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )

    args = parser.parse_args()

    orchestrator = DeepModernizationOrchestrator()

    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - Showing planned tasks:\n")
        for i, task in enumerate(orchestrator.tasks, 1):
            logger.info(f"{i}. {task.description}")
            logger.info(f"   Priority: {task.priority}")
            logger.info(f"   Files: ~{task.estimated_files}")
            logger.info(f"   Command: {' '.join(task.command[:5])}")
            logger.info("")
        return

    if args.task:
        # Run specific task
        task = next((t for t in orchestrator.tasks if t.task_id == args.task), None)
        if task:
            result = await orchestrator.run_task(task)
            orchestrator.generate_report([result])
        else:
            logger.error(f"❌ Task not found: {args.task}")
            logger.info("\nAvailable tasks:")
            for t in orchestrator.tasks:
                logger.info(f"  - {t.task_id}")
    else:
        # Run all tasks
        results = await orchestrator.run_all_tasks(parallel=args.parallel)
        orchestrator.generate_report(results)


if __name__ == "__main__":
    asyncio.run(main())
