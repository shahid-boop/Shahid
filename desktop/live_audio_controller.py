"""Threaded, explicitly started Gemini Live microphone/speaker session controller."""
from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from typing import Any


class LiveAudioController:
    """Own one Live audio session and provide a cooperative stop signal."""

    def __init__(
        self,
        api_key: str,
        *,
        on_state: Callable[..., None] | None = None,
        on_transcript: Callable[[str, str], None] | None = None,
        runner: Callable[..., Any] | None = None,
    ) -> None:
        self.api_key = str(api_key or "").strip()
        self.on_state = on_state or (lambda *_args: None)
        self.on_transcript = on_transcript
        self._runner = runner
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, *, approved: bool) -> bool:
        """Start only after a fresh UI approval. Returns False if declined/already running."""
        if not approved:
            return False
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required for Gemini Live.")
        if self.running:
            return False

        self._stop_event.clear()

        def worker() -> None:
            self.on_state("connecting")
            try:
                if self._runner is not None:
                    self._runner(
                        self.api_key,
                        stop_event=self._stop_event,
                        on_transcript=self.on_transcript,
                    )
                else:
                    from realtime.audio_io import run_gemini_live_audio
                    asyncio.run(
                        run_gemini_live_audio(
                            self.api_key,
                            on_transcript=self.on_transcript,
                            stop_event=self._stop_event,
                        )
                    )
                self.on_state("stopped")
            except Exception as exc:
                self.on_state("error", str(exc))
        self._thread = threading.Thread(
            target=worker, name="shahid-gemini-live", daemon=True
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        """Request a cooperative stop; does not kill the audio thread."""
        self._stop_event.set()
