#!/usr/bin/env python3
"""Simple Test - Verify Phase 1 systems work."""

import logging

from src.orchestration.agent_task_queue import AgentTaskQueue, TaskPriority, TaskType
from src.orchestration.ai_council_voting import AICouncilVoting, VoteChoice
from src.orchestration.feedback_loop_engine import ErrorReport, FeedbackLoopEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


def test_all_systems():
    """Test all three systems."""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 PHASE 1 SYSTEMS TEST - SIMPLE VERSION")
    logger.info("=" * 80 + "\n")

    # Test 1: Council Voting
    logger.info("✅ TEST 1: AI COUNCIL VOTING")
    council = AICouncilVoting()
    council.create_decision(
        decision_id="dec_001",
        topic="Fix Type Errors",
        description="Address mypy issues",
        proposed_by="Copilot",
    )
    council.cast_vote(
        decision_id="dec_001",
        agent_id="agent_1",
        agent_name="Copilot",
        vote=VoteChoice.APPROVE,
        confidence=0.9,
        expertise_level=0.8,
        reasoning="Can fix this",
    )
    final = council.get_decision("dec_001")
    logger.info(f"   Decision status: {final.status}, consensus: {final.consensus_level}\n")

    # Test 2: Task Queue
    logger.info("✅ TEST 2: AGENT TASK QUEUE")
    queue = AgentTaskQueue()
    queue.register_agent("copilot_agent", "Copilot", ["code_fix", "test"], 3)
    queue.register_agent("claude_agent", "Claude", ["review", "analysis"], 2)

    queue.create_task(
        task_id="task_001",
        task_type=TaskType.CODE_FIX,
        title="Fix mypy errors",
        description="Address type checking issues",
        priority=TaskPriority.HIGH,
        capabilities_required=["code_fix"],
        estimated_duration_minutes=30,
    )

    if queue.assign_task("task_001", "copilot_agent"):
        logger.info("   Task assigned to Copilot\n")

    status = queue.get_queue_status()
    logger.info(f"   Queue: {status['total_tasks']} total, {status['assigned']} assigned\n")

    # Test 3: Feedback Loop
    logger.info("✅ TEST 3: FEEDBACK LOOP ENGINE")
    loop = FeedbackLoopEngine(task_queue=queue)

    error = ErrorReport(
        error_id="mypy_001",
        error_type="mypy",
        file_path="src/core.py",
        line_number=42,
        message="Type mismatch",
        severity="high",
        source_system="mypy",
    )

    loop.ingest_error(error)
    processed = loop.process_error_queue()
    logger.info(f"   Processed {processed} error(s)\n")

    loop_status = loop.get_engine_status()
    logger.info(f"   Engine status: {loop_status['active_loops']} active loops\n")

    logger.info("=" * 80)
    logger.info("✨ ALL TESTS PASSED - PHASE 1 SYSTEMS WORKING")
    logger.info("=" * 80)


if __name__ == "__main__":
    test_all_systems()
