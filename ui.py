"""Tkinter HUD/chat interface with optional push-to-talk voice."""
from __future__ import annotations

import asyncio
import threading
import tkinter as tk
from tkinter import scrolledtext
from typing import Callable, Any


class AssistantWindow:
    def __init__(self, respond: Callable[[str], str], voice: Any = None, config: dict | None = None) -> None:
        self.respond = respond
        self.voice = voice
        self.config = config or {}
        self.root = tk.Tk()
        self.root.title("Shahid Assistant")
        self.root.geometry("760x560")
        self.root.minsize(520, 380)
        self.root.attributes("-topmost", bool(self.config.get("always_on_top", True)))

        self.output = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state="disabled")
        self.output.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12, 8))

        bottom = tk.Frame(self.root)
        bottom.pack(fill=tk.X, padx=12, pady=(0, 12))
        self.entry = tk.Entry(bottom)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self._send_event)
        self.send_button = tk.Button(bottom, text="Send", command=self._send)
        self.send_button.pack(side=tk.RIGHT, padx=(8, 0))
        self.voice_button = tk.Button(
            bottom, text="Push to talk", command=self._voice,
            state=tk.NORMAL if voice is not None else tk.DISABLED,
        )
        self.voice_button.pack(side=tk.RIGHT, padx=(8, 0))
        self.live_button = tk.Button(
            bottom, text="Start Live Voice", command=self._gemini_live,
            state=tk.NORMAL if voice is not None else tk.DISABLED,
        )
        self.live_button.pack(side=tk.RIGHT, padx=(8, 0))
        self._live_stop = None\n        self._live_session = None\n        self._append("System", "Assistant interface ready. Voice recording is push-to-talk only until Live Voice is explicitly started.")

    def _append(self, speaker: str, message: str) -> None:
        self.output.configure(state="normal")
        self.output.insert(tk.END, f"{speaker}: {message}\n\n")
        self.output.see(tk.END)
        self.output.configure(state="disabled")

    def _send_event(self, _event) -> None:
        self._send()

    def _set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        self.send_button.configure(state=state)
        if self.voice is not None:
            self.voice_button.configure(state=state)
            self.live_button.configure(state=state)

    def _send(self) -> None:
        message = self.entry.get().strip()
        if not message:
            return
        self.entry.delete(0, tk.END)
        self._append("You", message)
        self._set_busy(True)

        def work() -> None:
            try:
                answer = self.respond(message)
                self.root.after(0, lambda: self._append("Assistant", answer))
            except Exception as exc:
                self.root.after(0, lambda error=str(exc): self._append("Error", error))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=work, daemon=True).start()

    def _voice(self) -> None:
        if self.voice is None:
            return
        self._set_busy(True)
        self._append("System", "Listening for 6 seconds…")

        def work() -> None:
            try:
                heard = self.voice.listen_once()
                self.root.after(0, lambda: self._append("You (voice)", heard))
                answer = self.respond(heard)
                self.root.after(0, lambda: self._append("Assistant", answer))
                self.voice.speak(answer)
            except Exception as exc:
                self.root.after(0, lambda error=str(exc): self._append("Voice error", error))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=work, daemon=True).start()


    def _gemini_live(self) -> None:
        if self.voice is None:
            return
        if self._live_stop is not None:
            self._live_stop.set()
            if self._live_session is not None:
                self._live_session.stop()
            self.live_button.configure(text="Stopping…", state=tk.DISABLED)
            self._append("System", "Stopping Live Voice…")
            return

        import threading
        from speech.gemini_live import GeminiLiveClient
        from speech.live_voice import LiveVoiceSession

        stop_event = threading.Event()
        self._live_stop = stop_event
        client = GeminiLiveClient(
            model=self.config.get("gemini_live_model") or None,
            system_instruction=self.config.get(
                "system_prompt",
                "You are Shahid Assistant, a helpful Windows desktop assistant.",
            ),
        )
        session = LiveVoiceSession(client, sample_rate=self.voice.sample_rate)
        self._live_session = session
        self.live_button.configure(text="Stop Live Voice", state=tk.NORMAL)
        self._append("System", "Live microphone and speaker streaming started. Press Stop Live Voice to interrupt and disconnect.")

        def work() -> None:
            try:
                asyncio.run(session.run(stop_event))
            except Exception as exc:
                self.root.after(0, lambda error=str(exc): self._append("Live Voice error", error))
            finally:
                def finished():
                    self._live_stop = None
                    self._live_session = None
                    self.live_button.configure(text="Start Live Voice", state=tk.NORMAL)
                    self._append("System", "Live Voice stopped.")
                self.root.after(0, finished)

        threading.Thread(target=work, daemon=True, name="gemini-live-voice").start()

    def run(self) -> None:
        self.root.mainloop()


def launch(respond: Callable[[str], str], voice: Any = None, config: dict | None = None) -> None:
    AssistantWindow(respond, voice, config).run()
