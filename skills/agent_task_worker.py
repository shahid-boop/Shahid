"""Opt-in worker for durable tasks using only explicitly registered handlers."""
from __future__ import annotations

import threading
from typing import Any, Callable

from skills.agent_tasks import AgentTasksSkill


class AgentTaskWorker:
    def __init__(
        self,
        handlers: dict[str, Callable[..., Any]],
        store: AgentTasksSkill | None = None,
        poll_seconds: float = 2.0,
        on_result: Callable[[dict[str, Any]], None] | None = None,
    ):
        if poll_seconds < 0.25:
            raise ValueError("Task worker poll interval must be at least 0.25 seconds.")
        if not isinstance(handlers, dict) or any(not callable(fn) for fn in handlers.values()):
            raise ValueError("Task handlers must be an explicit mapping of names to callables.")
        self.handlers = dict(handlers)
        self.store = store or AgentTasksSkill()
        self.poll_seconds = float(poll_seconds)
        self.on_result = on_result or (lambda result: None)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="agent-task-worker")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def run_once(self) -> dict[str, Any] | None:
        queued = next((item for item in self.store.run(action="list")
                       if item.get("status") == "queued"), None)
        if queued is None:
            return None
        claimed = self.store.run(action="claim", task_id=queued["id"])
        handler = self.handlers.get(claimed.get("kind", "manual"))
        if handler is None:
            failed = self.store.run(action="fail", task_id=claimed["id"],
                                    error=f"No approved handler registered for task kind '{claimed.get('kind')}'.")
            self.on_result(failed)
            return failed
        try:
            result = handler(**claimed.get("payload", {}))
            completed = self.store.run(action="complete", task_id=claimed["id"])
            completed["result"] = result
            self.on_result(completed)
            return completed
        except Exception as exc:
            failed = self.store.run(action="fail", task_id=claimed["id"], error=str(exc))
            self.on_result(failed)
            return failed

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_once()
            except Exception as exc:
                self.on_result({"status": "worker_error", "error": str(exc)})
            self._stop.wait(self.poll_seconds)
