"""Persistent local reminders; due reminders can be polled by the runtime."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from skills.base import Skill


class ReminderSkill(Skill):
    name = "reminders"
    description = "Create and list local reminders with ISO-8601 due times."

    def __init__(self, path: Path = Path("data/reminders.json")):
        self.path = path

    def _read(self):
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Reminder data must be a list.")
        return data

    def run(self, action: str = "list", text: str = "", due_at: str = "", **arguments):
        items = self._read()
        if action == "list":
            return items
        if action != "add":
            raise ValueError("action must be 'add' or 'list'")
        if not text.strip():
            raise ValueError("Reminder text is required.")
        due = datetime.fromisoformat(due_at)
        if due.tzinfo is None:
            raise ValueError("due_at must include a timezone offset.")
        item = {"text": text.strip(), "due_at": due.astimezone(timezone.utc).isoformat(), "done": False}
        items.append(item)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return item
