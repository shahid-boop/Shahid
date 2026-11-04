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
        self.root = tk.Tk()
        self.root.title("Shahid Assistant")
        self.root.geometry("760x560")
        self.root.minsize(520, 380)

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
            bottom, text="Gemini Live", command=self._gemini_live,
            state=tk.NORMAL if voice is not None else tk.DISABLED,
        )
        self.live_button.pack(side=tk.RIGHT, padx=(8, 0))
        self._append("System", "Assistant interface ready. Voice recording is push-to-talk only.")

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
        self._set_busy(True)
        self._append("System", "Gemini Live: recording one utterance. Check microphone permission.")

        def work() -> None:
            try:
                from speech.gemini_live import GeminiLiveClient

                async def request_live(pcm: bytes):
                    client = GeminiLiveClient(
                        model=self.config.get("gemini_live_model") or None,
                        system_instruction=self.config.get(
                            "system_prompt",
                            "You are Shahid Assistant, a helpful Windows desktop assistant.",
                        )
                    )
                    try:
                        return await client.audio_turn(pcm, self.voice.sample_rate)
                    finally:
                        await client.close()

                pcm = self.voice.record_pcm_once()
                heard, audio = asyncio.run(request_live(pcm))
                self.root.after(0, lambda text=heard: self._append("Gemini Live", text or "[Audio response received]"))
                self.voice.play_pcm(audio, sample_rate=24000)
            except Exception as exc:
                self.root.after(0, lambda error=str(exc): self._append("Gemini Live error", error))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=work, daemon=True).start()

    def run(self) -> None:
        self.root.mainloop()


def launch(respond: Callable[[str], str], voice: Any = None, config: dict | None = None) -> None:
    AssistantWindow(respond, voice, config).run()
