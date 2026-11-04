"""Opt-in Windows reminder polling with desktop toast notifications."""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from skills.reminders import ReminderSkill


class ReminderScheduler:
    def __init__(self, interval_seconds: int = 15,
                 notify: Callable[[str], None] | None = None,
                 store: ReminderSkill | None = None):
        self.interval_seconds = max(5, int(interval_seconds))
        self.notify = notify or self._windows_toast
        self.store = store or ReminderSkill()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._notified: set[str] = set()

    def start(self) -> None:
        """Start only after explicit user opt-in."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="reminder-scheduler")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def check_once(self) -> list[str]:
        now = datetime.now(timezone.utc)
        due_messages = []
        for item in self.store.run(action="list"):
            if item.get("done"):
                continue
            key = item.get("due_at", "") + "|" + item.get("text", "")
            if key in self._notified:
                continue
            due = datetime.fromisoformat(item["due_at"])
            if due <= now:
                message = item["text"]
                self.notify(message)
                self._notified.add(key)
                due_messages.append(message)
        return due_messages

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.check_once()
            except Exception:
                pass
            self._stop.wait(self.interval_seconds)

    @staticmethod
    def _windows_toast(message: str) -> None:
        try:
            from winotify import Notification
            Notification(app_id="Shahid Assistant", title="Reminder", msg=message).show()
        except ImportError as exc:
            raise RuntimeError("Install winotify to display Windows toast reminders.") from exc
