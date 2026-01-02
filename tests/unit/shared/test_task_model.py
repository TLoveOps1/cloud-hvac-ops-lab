import pytest
from src.shared.models.task import Task
from datetime import datetime

def test_task_creation_success():
    task = Task("Fix Sensor Bug", "Investigate and resolve the intermittent sensor data issue.")
    assert task.title == "Fix Sensor Bug"
    assert task.description == "Investigate and resolve the intermittent sensor data issue."
    assert task.status == "pending"
    assert task.assigned_to is None
    assert isinstance(task.id, str)
    assert isinstance(task.created_at, str)
    assert datetime.fromisoformat(task.created_at) # Check if it's a valid ISO format

def test_task_creation_with_optional_fields():
    due_date = "2024-12-31"
    task = Task(
        "Deploy New Feature",
        "Deploy the new dashboard feature to production.",
        due_date=due_date,
        status="in_progress",
        assigned_to="Alice"
    )
    assert task.due_date == due_date
    assert task.status == "in_progress"
    assert task.assigned_to == "Alice"

def test_task_creation_empty_title_raises_error():
    with pytest.raises(ValueError, match="Task title cannot be empty."):
        Task("", "Description")
    with pytest.raises(ValueError, match="Task title cannot be empty."):
        Task("   ", "Description")

def test_task_creation_empty_description_raises_error():
    with pytest.raises(ValueError, match="Task description cannot be empty."):
        Task("Title", "")
    with pytest.raises(ValueError, match="Task description cannot be empty."):
        Task("Title", "   ")

def test_update_task_status_success():
    task = Task("Monitor System", "Keep an eye on the dashboard.")
    task.update_status("in_progress")
    assert task.status == "in_progress"
    task.update_status("completed")
    assert task.status == "completed"

def test_update_task_status_invalid_status_raises_error():
    task = Task("Monitor System", "Keep an eye on the dashboard.")
    with pytest.raises(ValueError, match="Invalid status"):
        task.update_status("invalid_status")

def test_assign_task_to_success():
    task = Task("Review Code", "Review PR #123.")
    task.assign_to("Bob")
    assert task.assigned_to == "Bob"

def test_assign_task_to_empty_assignee_raises_error():
    task = Task("Review Code", "Review PR #123.")
    with pytest.raises(ValueError, match="Assignee cannot be empty."):
        task.assign_to("")
    with pytest.raises(ValueError, match="Assignee cannot be empty."):
        task.assign_to("   ")

def test_task_to_dict():
    task = Task(
        "Test Task",
        "This is a test description.",
        due_date="2024-07-30",
        status="in_progress",
        assigned_to="Charlie"
    )
    task_dict = task.to_dict()
    assert task_dict['title'] == "Test Task"
    assert task_dict['description'] == "This is a test description."
    assert task_dict['due_date'] == "2024-07-30"
    assert task_dict['status'] == "in_progress"
    assert task_dict['assigned_to'] == "Charlie"
    assert 'id' in task_dict
    assert 'created_at' in task_dict

def test_task_from_dict():
    task_data = {
        "title": "From Dict Task",
        "description": "Created from a dictionary.",
        "due_date": "2024-08-15",
        "status": "completed",
        "assigned_to": "Diana"
    }
    task = Task.from_dict(task_data)
    assert task.title == "From Dict Task"
    assert task.description == "Created from a dictionary."
    assert task.due_date == "2024-08-15"
    assert task.status == "completed"
    assert task.assigned_to == "Diana"
    assert isinstance(task.id, str)
    assert isinstance(task.created_at, str)

def test_task_from_dict_missing_optional_fields():
    task_data = {
        "title": "Simple Task",
        "description": "No optional fields."
    }
    task = Task.from_dict(task_data)
    assert task.title == "Simple Task"
    assert task.description == "No optional fields."
    assert task.due_date is None
    assert task.status == "pending"
    assert task.assigned_to is None
