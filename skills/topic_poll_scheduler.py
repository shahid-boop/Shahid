"""Opt-in periodic topic polling with bounded, stoppable background work."""
from __future__ import annotations

import threading
from typing import Any, Callable

from skills.topic_monitoring import TopicMonitoringSkill


class TopicPollingScheduler:
    def __init__(
        self,
        interval_seconds: int = 3600,
        on_results: Callable[[dict[str, Any]], None] | None = None,
        store: TopicMonitoringSkill | None = None,
    ):
        if interval_seconds < 300:
            raise ValueError("Topic polling interval must be at least 300 seconds.")
        self.interval_seconds = int(interval_seconds)
        self.on_results = on_results or (lambda results: None)
        self.store = store or TopicMonitoringSkill()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start only after explicit opt-in from the user."""
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="topic-poll-scheduler"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def check_once(self) -> dict[str, Any]:
        results = self.store.run(action="check")
        self.on_results(results)
        return results

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.check_once()
            except Exception as exc:
                self.on_results({"error": str(exc)})
            self._stop.wait(self.interval_seconds)
