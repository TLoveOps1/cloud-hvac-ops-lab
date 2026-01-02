import uuid
from datetime import datetime

class Task:
    def __init__(self, title: str, description: str, due_date: str = None, status: str = "pending", assigned_to: str = None):
        if not title or not isinstance(title, str) or len(title.strip()) == 0:
            raise ValueError("Task title cannot be empty.")
        if not description or not isinstance(description, str) or len(description.strip()) == 0:
            raise ValueError("Task description cannot be empty.")

        self.id = str(uuid.uuid4())
        self.title = title.strip()
        self.description = description.strip()
        self.created_at = datetime.utcnow().isoformat()
        self.due_date = due_date
        self.status = status
        self.assigned_to = assigned_to

    def update_status(self, new_status: str):
        valid_statuses = ["pending", "in_progress", "completed", "blocked"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")
        self.status = new_status

    def assign_to(self, assignee: str):
        if not assignee or not isinstance(assignee, str) or len(assignee.strip()) == 0:
            raise ValueError("Assignee cannot be empty.")
        self.assigned_to = assignee.strip()

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at,
            "due_date": self.due_date,
            "status": self.status,
            "assigned_to": self.assigned_to
        }

    @staticmethod
    def from_dict(data: dict):
        return Task(
            title=data['title'],
            description=data['description'],
            due_date=data.get('due_date'),
            status=data.get('status', 'pending'),
            assigned_to=data.get('assigned_to')
        )
