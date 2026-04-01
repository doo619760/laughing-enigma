"""Task manager tool - persistent to-do list and task tracking."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.config import TASKS_FILE


def _load_tasks() -> list:
    """Load tasks from disk."""
    if TASKS_FILE.exists():
        with open(TASKS_FILE) as f:
            return json.load(f)
    return []


def _save_tasks(tasks: list):
    """Save tasks to disk."""
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def add_task(title: str, priority: str = "medium", due_date: str = "") -> str:
    """Add a new task."""
    tasks = _load_tasks()
    task = {
        "id": len(tasks) + 1,
        "title": title,
        "priority": priority,
        "status": "pending",
        "due_date": due_date,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    tasks.append(task)
    _save_tasks(tasks)
    return f"Added task #{task['id']}: {title} [priority: {priority}]"


def list_tasks(status_filter: str = "", priority_filter: str = "") -> str:
    """List tasks with optional filters."""
    tasks = _load_tasks()
    if not tasks:
        return "No tasks found. Add one with the task manager!"

    if status_filter:
        tasks = [t for t in tasks if t["status"] == status_filter]
    if priority_filter:
        tasks = [t for t in tasks if t["priority"] == priority_filter]

    if not tasks:
        return "No tasks match the given filters."

    priority_symbols = {"high": "!!!", "medium": " ! ", "low": "   "}
    status_symbols = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}

    lines = ["Tasks:"]
    for t in tasks:
        pri = priority_symbols.get(t["priority"], "   ")
        stat = status_symbols.get(t["status"], "[ ]")
        due = f" (due: {t['due_date']})" if t.get("due_date") else ""
        lines.append(f"  {stat} #{t['id']} {pri} {t['title']}{due}")

    return "\n".join(lines)


def update_task(task_id: int, status: Optional[str] = None, title: Optional[str] = None,
                priority: Optional[str] = None) -> str:
    """Update a task's status, title, or priority."""
    tasks = _load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            if status:
                task["status"] = status
                if status == "completed":
                    task["completed_at"] = datetime.now().isoformat()
            if title:
                task["title"] = title
            if priority:
                task["priority"] = priority
            _save_tasks(tasks)
            return f"Updated task #{task_id}: {task['title']} [{task['status']}]"
    return f"Error: Task #{task_id} not found."


def delete_task(task_id: int) -> str:
    """Delete a task."""
    tasks = _load_tasks()
    original_count = len(tasks)
    tasks = [t for t in tasks if t["id"] != task_id]
    if len(tasks) == original_count:
        return f"Error: Task #{task_id} not found."
    _save_tasks(tasks)
    return f"Deleted task #{task_id}."


TOOL_DEFINITION = {
    "name": "task_manager",
    "description": (
        "Manage a persistent to-do list. Add, list, update, and delete tasks. "
        "Tasks have priorities (high/medium/low) and statuses (pending/in_progress/completed)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "list", "update", "delete"],
                "description": "The action to perform on tasks",
            },
            "title": {
                "type": "string",
                "description": "Task title (for 'add' or 'update')",
            },
            "task_id": {
                "type": "integer",
                "description": "Task ID (for 'update' or 'delete')",
            },
            "priority": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Task priority",
            },
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed"],
                "description": "Task status (for 'update')",
            },
            "due_date": {
                "type": "string",
                "description": "Due date in YYYY-MM-DD format (for 'add')",
            },
            "status_filter": {
                "type": "string",
                "description": "Filter tasks by status (for 'list')",
            },
            "priority_filter": {
                "type": "string",
                "description": "Filter tasks by priority (for 'list')",
            },
        },
        "required": ["action"],
    },
}


def handle(input_data: dict) -> str:
    """Handle a tool call from the API."""
    action = input_data["action"]

    if action == "add":
        return add_task(
            title=input_data.get("title", "Untitled task"),
            priority=input_data.get("priority", "medium"),
            due_date=input_data.get("due_date", ""),
        )
    elif action == "list":
        return list_tasks(
            status_filter=input_data.get("status_filter", ""),
            priority_filter=input_data.get("priority_filter", ""),
        )
    elif action == "update":
        return update_task(
            task_id=input_data.get("task_id", 0),
            status=input_data.get("status"),
            title=input_data.get("title"),
            priority=input_data.get("priority"),
        )
    elif action == "delete":
        return delete_task(task_id=input_data.get("task_id", 0))
    else:
        return f"Error: Unknown action '{action}'"
