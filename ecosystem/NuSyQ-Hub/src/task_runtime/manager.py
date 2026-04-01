import subprocess

from .db import Database
from .models import TaskModel


class TaskManager:
    def __init__(self, db_path: str | None = None):
        """Initialize TaskManager with db_path."""
        self.db = Database(db_path)
        self.model = TaskModel(self.db)

    def create_task(
        self, objective: str, project_id: int | None = None, metadata: str | None = None
    ) -> int:
        return self.model.create_task(objective=objective, project_id=project_id, metadata=metadata)

    def start_run(self, task_id: int, command: str) -> int:
        # Mark task running
        self.model.update_status(task_id, "running")
        run_id = self.model.create_run(task_id=task_id)

        # Execute command
        try:
            proc = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            logs = proc.stdout + "\n" + proc.stderr
            exit_code = proc.returncode
        except subprocess.SubprocessError as e:
            logs = str(e)
            exit_code = 1

        self.model.finish_run(run_id, exit_code=exit_code, logs=logs)

        # set task status based on exit code
        if exit_code == 0:
            self.model.update_status(task_id, "done")
        else:
            self.model.update_status(task_id, "blocked")

        return run_id

    def list_tasks(self, status: str | None = None):
        return self.model.list_tasks(status=status)
