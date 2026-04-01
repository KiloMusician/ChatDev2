"""Query the nusyq tasks DB and print summary.

Usage:
  python scripts/query_tasks.py
"""

from src.task_runtime.db import Database


def main():
    db = Database()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) as c FROM tasks")
    total = cur.fetchone()["c"]
    print(f"tasks_total= {total}")

    cur.execute("SELECT id, objective, status FROM tasks ORDER BY id LIMIT 5")
    rows = cur.fetchall()
    for r in rows:
        print(f"[{r['id']}] {r['status']} - {str(r['objective'])[:120]}")


if __name__ == "__main__":
    main()
