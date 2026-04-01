import os
import sys
from pathlib import Path


def main() -> None:
    # Ensure NuSyQ-Hub src is importable before importing project modules.
    hub_src = Path(os.getenv("NUSYQ_HUB_ROOT", "/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub"))
    if str(hub_src) not in sys.path:
        sys.path.insert(0, str(hub_src))

    from src.orchestration.multi_ai_orchestrator import (  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
        MultiAIOrchestrator,
        OrchestrationTask,
        TaskPriority,
    )

    orchestrator = MultiAIOrchestrator()
    task = OrchestrationTask(
        task_id="selftest-001",
        task_type="ping",
        content="ping",
        context={},
        priority=TaskPriority.BACKGROUND,
    )
    orchestrator.task_queue.put((task.priority.value, task))
    print("Enqueued task selftest-001")


if __name__ == "__main__":
    main()
