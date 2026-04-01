"""Unit tests for AI Task Manager API."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Add parent directory to path to import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app

client = TestClient(app)


def test_create_task():
    """Test creating a new task."""
    response = client.post(
        "/tasks/",
        json={
            "title": "Test Task",
            "description": "This is a test task",
            "priority": 1,
            "category": "testing",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "This is a test task"
    assert data["priority"] == 1


def test_read_tasks():
    """Test reading all tasks."""
    # Create a task first
    client.post("/tasks/", json={"title": "Task 1", "description": "Description 1", "priority": 1})

    # Read tasks
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_read_single_task():
    """Test reading a single task by ID."""
    # Create a task
    create_response = client.post(
        "/tasks/", json={"title": "Single Task", "description": "Test", "priority": 2}
    )
    task_id = create_response.json()["id"]

    # Read it
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Single Task"


def test_update_task():
    """Test updating a task."""
    # Create a task
    create_response = client.post(
        "/tasks/", json={"title": "Original", "description": "Original desc", "priority": 1}
    )
    task_id = create_response.json()["id"]

    # Update it
    response = client.put(f"/tasks/{task_id}", json={"title": "Updated", "completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["completed"] is True


def test_delete_task():
    """Test deleting a task."""
    # Create a task
    create_response = client.post(
        "/tasks/", json={"title": "To Delete", "description": "Will be deleted", "priority": 1}
    )
    task_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404


def test_task_not_found():
    """Test accessing non-existent task."""
    response = client.get("/tasks/99999")
    assert response.status_code == 404


def test_ai_suggestions():
    """Test AI suggestions endpoint."""
    response = client.get("/suggestions/")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


def test_filter_by_category():
    """Test filtering tasks by category."""
    # Create tasks with different categories
    client.post("/tasks/", json={"title": "Work Task", "category": "work", "priority": 1})
    client.post("/tasks/", json={"title": "Personal Task", "category": "personal", "priority": 1})

    # Filter by category
    response = client.get("/tasks/?category=work")
    assert response.status_code == 200
    tasks = response.json()
    assert all(task["category"] == "work" for task in tasks if "category" in task)


def test_filter_by_completed():
    """Test filtering tasks by completion status."""
    # Create completed and incomplete tasks
    client.post("/tasks/", json={"title": "Incomplete", "priority": 1})
    task2 = client.post("/tasks/", json={"title": "Complete", "priority": 1}).json()

    # Mark one as complete
    client.put(f"/tasks/{task2['id']}", json={"completed": True})

    # Filter by completed status
    response = client.get("/tasks/?completed=true")
    assert response.status_code == 200
    tasks = response.json()
    assert all(task.get("completed") for task in tasks)


def test_pagination():
    """Test pagination parameters."""
    # Create multiple tasks
    for i in range(5):
        client.post("/tasks/", json={"title": f"Task {i}", "priority": 1})

    # Test limit
    response = client.get("/tasks/?limit=2")
    assert response.status_code == 200
    assert len(response.json()) <= 2

    # Test skip
    response = client.get("/tasks/?skip=2&limit=2")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) <= 2


def test_invalid_task_id():
    """Test handling of invalid task ID."""
    response = client.get("/tasks/invalid")
    assert response.status_code == 422  # Validation error


def test_create_task_without_required_fields():
    """Test creating task without required fields."""
    response = client.post("/tasks/", json={})
    assert response.status_code == 422  # Validation error
