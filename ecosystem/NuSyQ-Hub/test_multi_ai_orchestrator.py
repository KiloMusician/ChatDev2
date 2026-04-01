#!/usr/bin/env python3
"""Test Multi-AI Orchestrator with real task"""

import asyncio
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_orchestrator():
    """Test the Multi-AI Orchestrator with a real task"""
    print("[*] Testing Multi-AI Orchestrator")
    print("=" * 60)

    try:
        from src.orchestration.unified_ai_orchestrator import (
            TaskPriority,
        )
        from src.orchestration.unified_ai_orchestrator import (
            UnifiedAIOrchestrator as MultiAIOrchestrator,
        )

        print("[OK] Multi-AI Orchestrator module loaded")

        # Initialize orchestrator
        orchestrator = MultiAIOrchestrator()
        print(f"[OK] Orchestrator initialized with {len(orchestrator.ai_systems)} AI systems")

        # List registered systems
        print("\n[*] Registered AI Systems:")
        for system_name, system in orchestrator.ai_systems.items():
            print(f"   - {system_name}: {system.system_type.value}")
            print(f"     Capabilities: {', '.join(system.capabilities[:3])}")

        # Submit a test task using orchestrate_task
        print("\n[*] Submitting test task: 'Analyze NuSyQ-Hub architecture'")

        task_id = orchestrator.orchestrate_task(
            task_type="analysis",
            content="Analyze the NuSyQ-Hub architecture and identify ChatDev integration points",
            context={
                "repository": "NuSyQ-Hub",
                "focus": "ChatDev integration",
                "output_format": "structured_report",
            },
            priority=TaskPriority.HIGH,
        )

        print(f"[OK] Task submitted with ID: {task_id}")

        # Check task status
        status = orchestrator.get_task_status(task_id)
        print(f"[OK] Task status: {status.get('status', 'unknown')}")

        # Get orchestrator metrics
        metrics = orchestrator.get_metrics()
        print("\n[*] Orchestrator Metrics:")
        print(f"   - Total tasks: {metrics.get('total_tasks', 0)}")
        print(f"   - Completed tasks: {metrics.get('completed_tasks', 0)}")
        print(f"   - Active systems: {metrics.get('active_systems', 0)}")

        return True

    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Orchestrator test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("[*] NuSyQ-Hub Multi-AI Orchestrator Test")
    print("=" * 60)

    success = asyncio.run(test_orchestrator())

    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] Multi-AI Orchestrator is OPERATIONAL!")
    else:
        print("[ERROR] Orchestrator test failed")
    print("=" * 60)
