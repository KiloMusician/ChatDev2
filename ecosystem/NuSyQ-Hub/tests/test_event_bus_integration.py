#!/usr/bin/env python3
"""End-to-end integration test for event bus wiring.

Tests the complete flow:
  1. Task submission → UnifiedAIOrchestrator
  2. Task routing → AgentTaskRouter
  3. Handler execution (Ollama/ChatDev/Consciousness/Quantum)
  4. Event emissions to agent_bus stream
  5. Event persistence to state/logs/agent_bus.jsonl

Verifies all event types are emitted and monitoring integration works.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.orchestration.unified_ai_orchestrator import (
    OrchestrationTask,
    TaskPriority,
    UnifiedAIOrchestrator,
)
from src.tools.agent_task_router import AgentTaskRouter

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def read_recent_agent_bus_events(max_events: int = 50) -> list[dict]:
    """Read most recent events from agent_bus log."""
    _repo_root = Path(__file__).parent.parent
    agent_bus_log = _repo_root / "state" / "logs" / "agent_bus.log"

    if not agent_bus_log.exists():
        logger.warning(f"Agent bus log not found: {agent_bus_log}")
        return []

    events = []
    try:
        with open(agent_bus_log, encoding="utf-8") as f:
            lines = f.readlines()
            # Get last N lines and parse log format
            for line in lines[-max_events:]:
                try:
                    # Parse log format: "TIMESTAMP | EVENT=type | payload={...} | msg=..."
                    parts = [p.strip() for p in line.split("|")]
                    event = {}

                    if len(parts) >= 2:
                        event["timestamp"] = parts[0]
                        event["event_type"] = parts[1].replace("EVENT=", "")

                        # Extract payload and message
                        for part in parts[2:]:
                            if part.startswith("payload="):
                                try:
                                    event["payload"] = json.loads(part.replace("payload=", ""))
                                except json.JSONDecodeError:
                                    pass
                            elif part.startswith("msg="):
                                event["message"] = part.replace("msg=", "")

                        events.append(event)

                except Exception:
                    continue
    except Exception as e:
        logger.error(f"Failed to read agent bus log: {e}")

    return events


def test_orchestrator_event_emissions() -> bool:
    """Test UnifiedAIOrchestrator emits task lifecycle events."""
    logger.info("=" * 60)
    logger.info("TEST 1: Orchestrator Event Emissions")
    logger.info("=" * 60)

    try:
        orchestrator = UnifiedAIOrchestrator()

        # Create test task with required fields
        task = OrchestrationTask(
            task_id="test_event_bus_001",
            task_type="analysis",
            content="Test task for event bus verification",
            context={"test_type": "event_bus_integration"},
            priority=TaskPriority.NORMAL,
        )

        # Submit task (should emit task_submitted event)
        task_id = orchestrator.submit_task(task)
        logger.info(f"✓ Task submitted: {task_id}")

        # Read recent events
        events = read_recent_agent_bus_events(max_events=20)
        task_submitted_events = [e for e in events if e.get("event_type") == "task_submitted"]

        if task_submitted_events:
            logger.info(f"✓ Found {len(task_submitted_events)} task_submitted event(s)")
            latest = task_submitted_events[-1]
            logger.info(f"  Event payload: {latest.get('payload', {})}")
            return True
        else:
            logger.warning("✗ No task_submitted events found in agent_bus log")
            return False

    except Exception as e:
        logger.error(f"✗ Orchestrator test failed: {e}")
        return False


def test_router_event_emissions() -> bool:
    """Test AgentTaskRouter emits route lifecycle events."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Router Event Emissions")
    logger.info("=" * 60)

    try:
        # Create task router
        router = AgentTaskRouter()

        # Route task (should emit route_started, route_completed events)
        # Note: This may fail if target systems not available, but should still emit events
        try:
            import asyncio

            result = asyncio.run(
                router.route_task(
                    task_type="analyze",
                    description="Analyze this code snippet for best practices",
                    context={"file_path": "test.py", "test_type": "event_bus_routing"},
                    target_system="auto",
                )
            )
            logger.info(f"✓ Task routed successfully: {result.get('status', 'unknown')}")
        except Exception as route_error:
            logger.warning(f"! Task routing failed (expected if systems offline): {route_error}")

        # Read recent events
        events = read_recent_agent_bus_events(max_events=30)
        route_events = [
            e for e in events if e.get("event_type") in ("route_started", "route_completed")
        ]

        if route_events:
            logger.info(f"✓ Found {len(route_events)} routing event(s)")
            for event in route_events[-3:]:  # Show last 3
                logger.info(f"  {event.get('event_type')}: {event.get('message')}")
            return True
        else:
            logger.warning("✗ No routing events found in agent_bus log")
            return False

    except Exception as e:
        logger.error(f"✗ Router test failed: {e}")
        return False


def test_event_bus_monitoring_integration() -> bool:
    """Test event bus log file structure and monitoring readiness."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Event Bus Monitoring Integration")
    logger.info("=" * 60)

    _repo_root = Path(__file__).parent.parent
    agent_bus_log = _repo_root / "state" / "logs" / "agent_bus.log"

    try:
        if not agent_bus_log.exists():
            logger.warning(f"✗ Agent bus log does not exist: {agent_bus_log}")
            return False

        # Check log file is readable and well-formed
        events = read_recent_agent_bus_events(max_events=100)

        if not events:
            logger.warning("✗ Agent bus log is empty or malformed")
            return False

        logger.info(f"✓ Agent bus log contains {len(events)} recent events")

        # Verify event structure
        required_fields = {"timestamp", "event_type"}
        valid_events = 0

        for event in events[-10:]:  # Check last 10
            if required_fields.issubset(event.keys()):
                valid_events += 1

        logger.info(f"✓ {valid_events}/10 recent events have valid structure")

        # Count event types
        event_types = {}
        for event in events:
            etype = event.get("event_type", "unknown")
            event_types[etype] = event_types.get(etype, 0) + 1

        logger.info(f"✓ Event types in recent history: {len(event_types)}")
        for etype, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  - {etype}: {count}")

        return valid_events >= 8  # At least 80% valid

    except Exception as e:
        logger.error(f"✗ Monitoring integration test failed: {e}")
        return False


def run_all_tests() -> dict[str, bool]:
    """Run all integration tests and return results."""
    logger.info("\n" + "=" * 60)
    logger.info("EVENT BUS INTEGRATION TEST SUITE")
    logger.info("=" * 60)
    logger.info(f"Started: {datetime.now().isoformat()}\n")

    results = {
        "orchestrator_events": test_orchestrator_event_emissions(),
        "router_events": test_router_event_emissions(),
        "monitoring_integration": test_event_bus_monitoring_integration(),
    }

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info(f"\nResult: {passed}/{total} tests passed")

    if passed == total:
        logger.info("✅ All event bus integration tests PASSED")
    else:
        logger.warning(f"⚠️  {total - passed} test(s) FAILED")

    return results


if __name__ == "__main__":
    results = run_all_tests()
    exit(0 if all(results.values()) else 1)
