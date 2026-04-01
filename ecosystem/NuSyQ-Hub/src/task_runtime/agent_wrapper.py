from contextlib import contextmanager

from .manager import TaskManager


class AgentPreconditionError(Exception):
    pass


@contextmanager
def task_context(objective: str, project_id: int | None = None, precondition_callable=None):
    """Context manager that creates a task, runs body, records run and enforces simple pre/post conditions.

    Example usage:
        with task_context("Build Windows EXE") as ctx:
            # run build steps
            ctx.run("npm run build")

    The context exposes a small API with .run(command) to execute shell commands under the task.
    """
    manager = TaskManager()
    task_id = manager.create_task(objective, project_id=project_id)

    # optional precondition check (e.g., ensure smart_search was called or repo clean)
    if precondition_callable and not precondition_callable():
        manager.model.update_status(task_id, "blocked")
        raise AgentPreconditionError("Precondition failed for task")

    class Ctx:
        def __init__(self, task_id: int, manager: TaskManager):
            self.task_id = task_id
            self.manager = manager

        def run(self, command: str):
            return self.manager.start_run(self.task_id, command)

        def id(self):
            return self.task_id

    ctx = Ctx(task_id, manager)
    try:
        yield ctx
    finally:
        # If task still pending/running, leave as-is; manager.start_run sets done/blocked.
        pass
