import random
import sqlite3
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()


# Database setup
def get_db():
    conn = sqlite3.connect("tasks.db")
    try:
        yield conn
    finally:
        conn.close()


@app.on_event("startup")
async def startup_event():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 1,
                completed BOOLEAN DEFAULT FALSE,
                category TEXT
            )
        """
        )
        conn.commit()


# Models
class Task(BaseModel):
    title: str
    description: str | None = None
    priority: int = 1
    category: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: int | None = None
    completed: bool | None = None
    category: str | None = None


# CRUD operations
@app.post("/tasks/", response_model=Task)
async def create_task(task: Task, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO tasks (title, description, priority, category)
        VALUES (?, ?, ?, ?)
    """,
        (task.title, task.description, task.priority, task.category),
    )
    db.commit()
    return {**task.dict(), "id": cursor.lastrowid}


@app.get("/tasks/", response_model=list[Task])
async def read_tasks(
    skip: int = 0,
    limit: int = 10,
    completed: bool | None = None,
    category: str | None = Query(None, title="Category filter"),
    db: sqlite3.Connection = Depends(get_db),
):
    cursor = db.cursor()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if completed is not None:
        query += " AND completed = ?"
        params.append(completed)

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, skip])

    cursor.execute(query, tuple(params))
    tasks = cursor.fetchall()
    return [
        Task(id=t[0], title=t[1], description=t[2], priority=t[3], completed=t[4], category=t[5])
        for t in tasks
    ]


@app.get("/tasks/{task_id}", response_model=Task)
async def read_task(task_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return Task(
        id=task[0],
        title=task[1],
        description=task[2],
        priority=task[3],
        completed=task[4],
        category=task[5],
    )


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: int, task_update: TaskUpdate, db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing_task = cursor.fetchone()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = {**dict(existing_task), **task_update.dict()}
    cursor.execute(
        """
        UPDATE tasks SET title = ?, description = ?, priority = ?, completed = ?, category = ?
        WHERE id = ?
    """,
        (
            task_data["title"],
            task_data["description"],
            task_data["priority"],
            task_data["completed"],
            task_data["category"],
            task_id,
        ),
    )
    db.commit()
    return Task(**task_data)


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    db.commit()


# AI-powered task suggestions
@app.get("/tasks/suggestions/", response_model=list[Task])
async def get_task_suggestions(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tasks WHERE completed = FALSE")
    pending_tasks = cursor.fetchall()

    # Simple AI logic to suggest tasks based on priority
    suggested_tasks = sorted(pending_tasks, key=lambda x: (x[3], random.random()))[:5]
    return [
        Task(id=t[0], title=t[1], description=t[2], priority=t[3], completed=t[4], category=t[5])
        for t in suggested_tasks
    ]


# Productivity insights
@app.get("/insights/", response_model=dict)
async def get_productivity_insights(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()

    # Total tasks
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cursor.fetchone()[0]

    # Completed tasks
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = TRUE")
    completed_tasks = cursor.fetchone()[0]

    # Tasks by category
    cursor.execute(
        """
        SELECT category, COUNT(*) as count 
        FROM tasks 
        GROUP BY category 
        ORDER BY count DESC
    """
    )
    tasks_by_category = cursor.fetchall()

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "tasks_by_category": {t[0]: t[1] for t in tasks_by_category},
    }


# CORS setup (for simplicity, using a middleware)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
