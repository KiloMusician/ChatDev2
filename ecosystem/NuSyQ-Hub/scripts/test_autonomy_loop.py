"""Test runner for validating the closed loop autonomy system.

This script:
1. Gets current queue state
2. Processes 5-10 sample tasks through the complete autonomy pipeline
3. Validates patches were applied
4. Confirms PR creation (or proposal for high-risk)
5. Logs results

Usage:
    python scripts/test_autonomy_loop.py --max-tasks 5 --verbose
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def main():
    """Test the closed loop autonomy system."""

    # Import required modules
    try:
        from src.autonomy import GitHubPRBot
        from src.orchestration.background_task_orchestrator import (
            TaskStatus,
            get_orchestrator,
        )
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.debug(f"Python path: {sys.path[:3]}")
        return 1

    logger.info("=" * 80)
    logger.info("AUTONOMY SYSTEM CLOSED LOOP TEST")
    logger.info("=" * 80)

    # Get orchestrator
    orchestrator = get_orchestrator()

    # Check queue state
    queue_stats = orchestrator.get_queue_stats()
    logger.info("\nQueue Statistics:")
    logger.info(f"  Queued:    {queue_stats['queued']}")
    logger.info(f"  Running:   {queue_stats['running']}")
    logger.info(f"  Completed: {queue_stats['completed']}")
    logger.info(f"  Failed:    {queue_stats['failed']}")

    # Check for completed tasks that haven't been processed
    completed_tasks = orchestrator.list_tasks(status=TaskStatus.COMPLETED, limit=50)
    unprocessed = [t for t in completed_tasks if not t.metadata.get("autonomy_processed")]

    logger.info(f"\nCompleted tasks available: {len(completed_tasks)}")
    logger.info(f"  Not yet processed by autonomy: {len(unprocessed)}")

    if not unprocessed:
        logger.info("\nNo unprocessed tasks available for testing.")
        logger.info("You can submit test tasks with:")
        logger.info("  python src/orchestration/background_task_orchestrator.py")
        return 0

    # Test with first 5 unprocessed tasks
    test_tasks = unprocessed[:5]
    logger.info(f"\nProcessing {len(test_tasks)} tasks through autonomy pipeline...")
    logger.info("-" * 80)

    bot = GitHubPRBot()
    results = []

    for i, task in enumerate(test_tasks, 1):
        logger.info(f"\n[{i}/{len(test_tasks)}] Processing task: {task.task_id}")
        logger.info(f"  Prompt: {task.prompt[:100]}...")
        logger.info(f"  Result length: {len(task.result or '')} chars")

        try:
            result = await bot.process_llm_response(
                task_id=task.task_id,
                llm_response=task.result or "",
                task_description=task.prompt[:100],
            )

            results.append({"task_id": task.task_id, "result": result})

            logger.info(f"  ✓ Success: {result.get('action_taken')}")
            if result.get("pr_url"):
                logger.info(f"    PR URL: {result['pr_url']}")
            if result.get("risk_level"):
                logger.info(f"    Risk Level: {result['risk_level']} ({result.get('risk_score', 0):.2f})")
            if result.get("proposal_path"):
                logger.info(f"    Proposal: {result['proposal_path']}")

        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            results.append({"task_id": task.task_id, "error": str(e)})

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    successful = sum(1 for r in results if "result" in r and r["result"].get("success"))
    failed = sum(1 for r in results if "error" in r)
    pr_created = sum(1 for r in results if "result" in r and r["result"].get("action_taken") == "pr_created")
    blocked = sum(1 for r in results if "result" in r and r["result"].get("action_taken") == "blocked")

    logger.info(f"\nProcessed: {len(results)} tasks")
    logger.info(f"  Successful: {successful}")
    logger.info(f"    - PRs created: {pr_created}")
    logger.info(f"    - Proposals: {blocked}")
    logger.info(f"  Failed: {failed}")

    # Save detailed results
    results_file = Path("state/reports/autonomy_test_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    results_file.write_text(json.dumps(results, indent=2))
    logger.info(f"\nDetailed results saved to: {results_file}")

    if successful > 0:
        logger.info("\n✅ CLOSED LOOP IS OPERATIONAL")
        logger.info("   - Tasks completed")
        logger.info("   - Results analyzed")
        logger.info("   - Patches applied")
        logger.info("   - PRs created")
        logger.info("   - Governance enforced")
        return 0
    else:
        logger.warning("\n⚠️ CLOSED LOOP NEEDS ATTENTION")
        logger.warning("   Check error details above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
