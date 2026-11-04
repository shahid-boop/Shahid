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

        self.root.configure(bg="#101827")
        self._animation_phase = 0
        self._hud_status = "READY"
        self.visual = tk.Canvas(self.root, height=104, bg="#101827", highlightthickness=0)
        self.visual.pack(fill=tk.X, padx=12, pady=(10, 0))
        self._draw_hud()
        self.output = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state="disabled",
            bg="#172235", fg="#e5edf8", insertbackground="#ffffff",
            relief=tk.FLAT, borderwidth=0, padx=12, pady=10,
        )
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
        self.compact_button = tk.Button(bottom, text="Compact", command=self._toggle_compact)
        self.compact_button.pack(side=tk.RIGHT, padx=(8, 0))
        self.dock_button = tk.Button(bottom, text="Dock Right", command=self._dock_right)
        self.dock_button.pack(side=tk.RIGHT, padx=(8, 0))
        self.live_button = tk.Button(
            bottom, text="Start Live Voice", command=self._gemini_live,
            state=tk.NORMAL if voice is not None else tk.DISABLED,
        )
        self.live_button.pack(side=tk.RIGHT, padx=(8, 0))
        self._compact = False
        self._live_stop = None
        self._live_session = None
        self._append("System", "Assistant interface ready. Voice recording is push-to-talk only until Live Voice is explicitly started.")
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self._animate_hud()

    def _draw_hud(self) -> None:
        self.visual.delete("all")
        width = max(self.visual.winfo_width(), 520)
        center_x, center_y = 54, 51
        phase = self._animation_phase
        radius = 18 + (phase % 12)
        self.visual.create_oval(center_x-radius, center_y-radius, center_x+radius, center_y+radius, outline="#284a70", width=2)
        self.visual.create_oval(center_x-17, center_y-17, center_x+17, center_y+17, fill="#163e61", outline="#56c8ff", width=2)
        self.visual.create_oval(center_x-7, center_y-7, center_x+7, center_y+7, fill="#a8e8ff", outline="")
        self.visual.create_text(100, 39, anchor="w", text="SHAHID  /  AI ASSISTANT", fill="#e5edf8", font=("Segoe UI", 12, "bold"))
        self.visual.create_text(100, 65, anchor="w", text=self._hud_status, fill="#70d6ff", font=("Segoe UI", 9, "bold"))
        for index in range(28):
            bar_height = 3 + ((index * 7 + phase * 3) % 13)
            x = width - 18 - index * 8
            self.visual.create_line(x, center_y + bar_height, x, center_y - bar_height, fill="#245b83", width=2)

    def _animate_hud(self) -> None:
        if not self.root.winfo_exists():
            return
        self._animation_phase = (self._animation_phase + 1) % 120
        self._draw_hud()
        self.root.after(70, self._animate_hud)

    def _close(self) -> None:
        if self._live_stop is not None:
            self._live_stop.set()
            if self._live_session is not None:
                self._live_session.stop()
        self.root.destroy()

    def _toggle_compact(self) -> None:
        self._compact = not self._compact
        if self._compact:
            self.output.pack_forget()
            self.root.geometry("520x150")
            self.compact_button.configure(text="Expand")
        else:
            self.output.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12, 8), before=self.root.winfo_children()[-1])
            self.root.geometry("760x560")
            self.compact_button.configure(text="Compact")

    def _dock_right(self) -> None:
        self.root.update_idletasks()
        width = 520 if self._compact else 760
        height = self.root.winfo_height()
        x = self.root.winfo_screenwidth() - width
        self.root.geometry(f"{width}x{height}+{x}+0")
        self.dock_button.configure(text="Undock", command=self._undock)

    def _undock(self) -> None:
        self.root.geometry("520x150" if self._compact else "760x560")
        self.root.geometry("+120+100")
        self.dock_button.configure(text="Dock Right", command=self._dock_right)

    def _append(self, speaker: str, message: str) -> None:
        self.output.configure(state="normal")
        self.output.insert(tk.END, f"{speaker}: {message}\n\n")
        self.output.see(tk.END)
        self.output.configure(state="disabled")

    def _send_event(self, _event) -> None:
        self._send()

    def _set_busy(self, busy: bool) -> None:
        self._hud_status = "THINKING" if busy else "READY"
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
        self._hud_status = "LIVE VOICE"
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
                    self._hud_status = "READY"
                    self.live_button.configure(text="Start Live Voice", state=tk.NORMAL)
                    self._append("System", "Live Voice stopped.")
                self.root.after(0, finished)

        threading.Thread(target=work, daemon=True, name="gemini-live-voice").start()

    def run(self) -> None:
        self.root.mainloop()


def launch(respond: Callable[[str], str], voice: Any = None, config: dict | None = None) -> None:
    AssistantWindow(respond, voice, config).run()
