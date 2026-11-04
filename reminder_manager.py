"""Persistent, local reminders with explicit completion and bounded input."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

class ReminderManager:
    def __init__(self, path: str | Path = "data/reminders.json"):
        self.path = Path(path)
        self._lock = RLock()

    def _load(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _save(self, items: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def add(self, text: str, due_at: str | None = None) -> dict[str, Any]:
        title = text.strip()
        if not title or len(title) > 500:
            raise ValueError("Reminder text must contain 1–500 characters.")
        due = None
        if due_at:
            parsed = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("due_at must include a timezone, e.g. +05:00 or Z.")
            due = parsed.astimezone(timezone.utc).isoformat()
        item = {"id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
                "text": title, "due_at": due, "done": False,
                "created_at": datetime.now(timezone.utc).isoformat()}
        with self._lock:
            items = self._load()
            items.append(item)
            self._save(items)
        return item

    def list(self, include_done: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            return [x for x in self._load() if include_done or not x.get("done")]

    def complete(self, reminder_id: str) -> dict[str, Any]:
        with self._lock:
            items = self._load()
            for item in items:
                if item.get("id") == reminder_id:
                    item["done"] = True
                    self._save(items)
                    return item
        raise KeyError("Reminder not found.")
