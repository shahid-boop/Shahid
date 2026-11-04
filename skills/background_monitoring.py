"""Opt-in background health polling with explicit start/stop lifecycle."""
from __future__ import annotations

import threading
from typing import Callable, Any

from skills.proactive_checks import ProactiveChecksSkill


class BackgroundMonitoring:
    def __init__(self, interval_seconds: int = 300,
                 on_result: Callable[[dict[str, Any]], None] | None = None):
        if interval_seconds < 30:
            raise ValueError("Monitoring interval must be at least 30 seconds.")
        self.interval_seconds = interval_seconds
        self.on_result = on_result or (lambda result: None)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start polling only after an explicit call from the user."""
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="assistant-monitor")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.on_result(ProactiveChecksSkill().run())
            except Exception as exc:
                self.on_result({"error": str(exc)})
            self._stop.wait(self.interval_seconds)
