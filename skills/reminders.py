"""Persistent local reminders; no background scheduler or network access required."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

class ReminderStore:
    def __init__(self, path: str | Path = "data/reminders.json"):
        self.path = Path(path)
        self._lock = RLock()

    def _load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def add(self, text: str, due: str = "") -> dict:
        text = text.strip()
        if not text or len(text) > 1000:
            raise ValueError("Reminder text must be 1-1000 characters.")
        if due:
            try:
                datetime.fromisoformat(due.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("due must be an ISO-8601 date/time.") from exc
        with self._lock:
            items = self._load()
            item = {"id": max([int(x.get("id", 0)) for x in items] + [0]) + 1,
                    "text": text, "due": due, "created_at": datetime.now(timezone.utc).isoformat(),
                    "done": False}
            items.append(item)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
            return item

    def list(self) -> list[dict]:
        with self._lock:
            return self._load()

    def complete(self, reminder_id: int) -> dict:
        with self._lock:
            items = self._load()
            for item in items:
                if item.get("id") == reminder_id:
                    item["done"] = True
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
                    return item
            raise KeyError(f"Reminder not found: {reminder_id}")

def register_reminder_skill(registry, store: ReminderStore | None = None):
    store = store or ReminderStore()
    registry.register("reminder_add", lambda p: store.add(str(p.get("text", "")), str(p.get("due", ""))))
    registry.register("reminder_list", lambda p: {"reminders": store.list()})
    registry.register("reminder_complete", lambda p: store.complete(int(p.get("id", 0))))
