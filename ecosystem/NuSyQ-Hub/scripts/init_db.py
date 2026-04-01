"""Initialize nusyq_state.db and seed with a sample project.

Usage:
  python scripts/init_db.py
"""

from src.task_runtime.db import Database


def main():
    db = Database()
    # ensure at least one sample project exists
    cur = db.execute("SELECT id FROM projects WHERE name = ?", ("SimulatedVerse",))
    row = cur.fetchone()
    if row:
        print("Project 'SimulatedVerse' already present with id", row[0])
    else:
        cur = db.execute(
            "INSERT INTO projects (name, type, engine) VALUES (?, ?, ?)",
            ("SimulatedVerse", "game", "custom"),
        )
        print("Created project SimulatedVerse with id", cur.lastrowid)


if __name__ == "__main__":
    main()
