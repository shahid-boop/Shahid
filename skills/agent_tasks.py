"""Durable local task queue with explicit execution and recoverable claims."""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from skills.base import Skill


class AgentTasksSkill(Skill):
    name = "agent_tasks"
    description = "Persist, claim, complete, fail and inspect assistant tasks."

    def __init__(self, path: Path = Path("data/tasks.json")):
        self.path = path
        self._lock = threading.RLock()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Task store is unreadable: {exc}") from exc
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise ValueError("Task store must contain a JSON array of objects.")
        return data

    def _write(self, tasks: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temp.replace(self.path)

    def run(self, action: str = "list", task: str = "", task_id: str = "", **arguments):
        with self._lock:
            tasks = self._read()
            if action == "list":
                return tasks
            if action == "add":
                value = task.strip()
                if not value:
                    raise ValueError("Task description is required.")
                kind = str(arguments.get("kind", "manual")).strip()
                payload = arguments.get("payload", {})
                if not kind or len(kind) > 80 or not isinstance(payload, dict):
                    raise ValueError("Task kind must be 1-80 characters and payload must be an object.")
                item = {"id": uuid.uuid4().hex, "task": value, "kind": kind,
                        "payload": payload, "status": "queued",
                        "created_at": self._now(), "updated_at": self._now(),
                        "attempts": 0, "last_error": None}
                tasks.append(item)
                self._write(tasks)
                return item
            item = next((entry for entry in tasks if entry.get("id") == task_id), None)
            if item is None:
                raise LookupError(f"Unknown task id: {task_id}")
            if action == "claim":
                if item.get("status") != "queued":
                    raise ValueError("Only queued tasks can be claimed.")
                item.update(status="running", updated_at=self._now(),
                            attempts=int(item.get("attempts", 0)) + 1)
            elif action == "complete":
                if item.get("status") != "running":
                    raise ValueError("Only running tasks can be completed.")
                item.update(status="completed", updated_at=self._now(), completed_at=self._now())
            elif action == "fail":
                if item.get("status") != "running":
                    raise ValueError("Only running tasks can be failed.")
                item.update(status="failed", updated_at=self._now(),
                            last_error=str(arguments.get("error", "Task failed"))[:1000])
            elif action == "retry":
                if item.get("status") not in {"failed", "running"}:
                    raise ValueError("Only failed or interrupted running tasks can be retried.")
                item.update(status="queued", updated_at=self._now(), last_error=None)
            else:
                raise ValueError("action must be list, add, claim, complete, fail or retry")
            self._write(tasks)
            return item
