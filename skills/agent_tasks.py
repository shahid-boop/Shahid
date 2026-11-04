"""Small in-process task queue; tasks run only when explicitly drained."""
from __future__ import annotations

from collections import deque
from skills.base import Skill


class AgentTasksSkill(Skill):
    name = "agent_tasks"
    description = "Queue and inspect simple assistant tasks."

    def __init__(self):
        self.tasks = deque()

    def run(self, action: str = "list", task: str = "", **arguments):
        if action == "list":
            return list(self.tasks)
        if action == "add":
            if not task.strip():
                raise ValueError("Task description is required.")
            item = {"task": task.strip(), "status": "queued"}
            self.tasks.append(item)
            return item
        raise ValueError("action must be 'add' or 'list'")
