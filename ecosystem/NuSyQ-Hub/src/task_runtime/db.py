import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[2] / "state" / "nusyq_state.db"


class Database:
    def __init__(self, path: str | None = None):
        """Initialize Database with path."""
        self.path = Path(path) if path else DEFAULT_DB
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self):
        cur = self.conn.cursor()
        cur.executescript(
            """
        BEGIN;
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            engine TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            objective TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME,
            exit_code INTEGER,
            logs TEXT,
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        );

        CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            path TEXT NOT NULL,
            type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,
            name TEXT,
            local_path TEXT,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );


        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(run_id) REFERENCES runs(id)
        );
        COMMIT;
        """
        )
        self.conn.commit()

    def cursor(self):
        return self.conn.cursor()

    def execute(self, *args, **kwargs):
        cur = self.conn.cursor()
        cur.execute(*args, **kwargs)
        self.conn.commit()
        return cur

    def query(self, *args, **kwargs):
        cur = self.conn.cursor()
        cur.execute(*args, **kwargs)
        return cur.fetchall()

    def close(self):
        self.conn.close()
