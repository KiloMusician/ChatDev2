import time
from pathlib import Path

from src.orchestration.unified_ai_orchestrator import (
    OrchestrationTask,
    TaskPriority,
    create_orchestrator,
)


def main():
    orch = create_orchestrator()
    orch.start_orchestration()

    task = OrchestrationTask(
        task_id="smoke_test_001",
        task_type="custom_test",
        content="This is a safe smoke-test task to validate orchestration flow.",
        context={"source": "integration_test"},
        priority=TaskPriority.LOW,
        required_capabilities=[],
    )

    task_id = orch.submit_task(task)
    print(f"Submitted task: {task_id}")

    # Poll for status
    for i in range(10):
        status = orch.get_task_status(task_id)
        print(f"Status [{i}]: {status}")
        if status and status.get("status") in ["completed", "failed"]:
            break
        time.sleep(1)

    # Export final orchestration state
    out = Path("data/orchestration_state_after_task.json")
    orch.export_orchestration_state(out)
    print(f"Exported orchestration state to {out}")

    orch.stop_orchestration()


if __name__ == "__main__":
    main()
