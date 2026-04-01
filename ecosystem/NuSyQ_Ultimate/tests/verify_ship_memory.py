#!/usr/bin/env python3
"""Quick verification of Ship Memory integration"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.agent_router import AgentRouter


def test_ship_memory_integration():
    """Test Ship Memory integration with Agent Router."""
    print("🚢 Testing Ship Memory Integration")
    print("=" * 60)

    # Initialize router
    router = AgentRouter()
    print(f"✅ Agent Router loaded: {len(router.agents)} agents")
    print(f"✅ Ship Memory enabled: {router.ship_memory is not None}")

    if not router.ship_memory:
        print("❌ Ship Memory not available")
        raise AssertionError("Ship Memory not available")

    # Record test task
    print("\n📝 Recording test task...")
    router.record_task_completion(
        agent_name="test_agent", task_type="test_task", success=True, duration=1.5
    )

    # Get performance
    perf = router.get_agent_performance("test_agent")
    print(f"✅ Performance retrieved: {perf}")

    # Verify
    assert perf["tasks_completed"] == 1
    assert perf["success_rate"] == 1.0
    assert perf["average_duration"] == 1.5

    print("\n✅ All tests passed!")
    print(f"Memory file: {router.ship_memory.memory_file}")


if __name__ == "__main__":
    try:
        test_ship_memory_integration()
        exit(0)
    except (RuntimeError, AssertionError, AttributeError):
        exit(1)
