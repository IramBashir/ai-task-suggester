# test_main.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_create_read_update_delete_task():
    # Create
    task_data = {
        "title": "Test Task",
        "description": "Test Desc",
        "category": "Work",
        "deadline": "2025-08-18",
        "subtasks": ["sub1", "sub2"]
    }
    res = client.post("/tasks/", json=task_data)
    assert res.status_code == 200
    task = res.json()
    assert task["title"] == "Test Task"
    task_id = task["id"]

    # Read
    res = client.get(f"/tasks/{task_id}")
    assert res.status_code == 200
    assert res.json()["id"] == task_id

    # Update
    update_data = {"title": "Updated Task", "category": "Personal"}
    res = client.put(f"/tasks/{task_id}", json=update_data)
    assert res.status_code == 200
    assert res.json()["title"] == "Updated Task"
    assert res.json()["category"] == "Personal"

    # Delete
    res = client.delete(f"/tasks/{task_id}")
    assert res.status_code == 204

    # Confirm deletion
    res = client.get(f"/tasks/{task_id}")
    assert res.status_code == 404
