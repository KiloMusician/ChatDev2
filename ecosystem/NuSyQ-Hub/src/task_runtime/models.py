from dataclasses import dataclass

from .db import Database


@dataclass
class Task:
    id: int
    project_id: int | None
    objective: str
    status: str
    metadata: str | None


@dataclass
class Run:
    id: int
    task_id: int
    started_at: str
    ended_at: str | None
    exit_code: int | None
    logs: str | None


class TaskModel:
    def __init__(self, db: Database):
        """Initialize TaskModel with db."""
        self.db = db

    def create_task(
        self, objective: str, project_id: int | None = None, metadata: str | None = None
    ) -> int:
        cur = self.db.execute(
            "INSERT INTO tasks (project_id, objective, metadata, status) VALUES (?, ?, ?, 'pending')",
            (project_id, objective, metadata),
        )
        return int(cur.lastrowid)

    def get_task(self, task_id: int) -> Task | None:
        rows = self.db.query("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not rows:
            return None
        r = rows[0]
        return Task(
            id=r["id"],
            project_id=r["project_id"],
            objective=r["objective"],
            status=r["status"],
            metadata=r["metadata"],
        )

    def update_status(self, task_id: int, status: str):
        self.db.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))

    def list_tasks(self, status: str | None = None) -> list[Task]:
        if status:
            rows = self.db.query(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC", (status,)
            )
        else:
            rows = self.db.query("SELECT * FROM tasks ORDER BY created_at DESC")
        return [
            Task(
                id=r["id"],
                project_id=r["project_id"],
                objective=r["objective"],
                status=r["status"],
                metadata=r["metadata"],
            )
            for r in rows
        ]

    # Runs
    def create_run(
        self, task_id: int, logs: str | None = None, exit_code: int | None = None
    ) -> int:
        cur = self.db.execute(
            "INSERT INTO runs (task_id, logs, exit_code) VALUES (?, ?, ?)",
            (task_id, logs, exit_code),
        )
        return int(cur.lastrowid)

    def finish_run(self, run_id: int, exit_code: int, logs: str | None = None):
        self.db.execute(
            "UPDATE runs SET ended_at = CURRENT_TIMESTAMP, exit_code = ?, logs = ? WHERE id = ?",
            (exit_code, logs, run_id),
        )

    def add_artifact(self, project_id: int, path: str, artifact_type: str | None = None) -> int:
        cur = self.db.execute(
            "INSERT INTO artifacts (project_id, path, type) VALUES (?, ?, ?)",
            (project_id, path, artifact_type),
        )
        return int(cur.lastrowid)
