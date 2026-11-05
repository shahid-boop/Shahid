"""Tkinter desktop HUD with chat, voice input, and guarded skill dispatch."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from config_manager import Settings
from engine_pipeline import ChatEngine, ProviderError
from memory_manager import MemoryManager
from desktop.skill_console import SkillConsole


class AssistantUI:
    def __init__(self, settings: Settings | None = None):
        # Import here to keep the registry/bootstrap boundary out of UI module import time.
        from main import build_registry

        self.settings = settings or Settings.load()
        self.engine = ChatEngine(self.settings)
        self.memory = MemoryManager()
        self.skills = build_registry()
        self.root = tk.Tk()
        self.root.title("Shahid Assistant")
        self.root.geometry("820x680")
        self.root.minsize(560, 460)
        self.root.configure(bg="#0b1020")
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#0b1020")
        style.configure("TLabel", background="#0b1020", foreground="#eaf1ff")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground="#8edcff")
        style.configure("TNotebook", background="#0b1020", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 7))

        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="◉  SHAHID ASSISTANT", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Windows 11 · Local desktop interface").pack(anchor="w", pady=(4, 12))

        notebook = ttk.Notebook(outer)
        notebook.pack(fill="both", expand=True)
        chat_tab = ttk.Frame(notebook, padding=10)
        tools_tab = ttk.Frame(notebook, padding=10)
        notebook.add(chat_tab, text="Chat")
        notebook.add(tools_tab, text="Tools")

        self.output = tk.Text(
            chat_tab, wrap="word", bg="#121b30", fg="#edf2ff",
            insertbackground="white", relief="flat", padx=12, pady=12,
            font=("Segoe UI", 10), state="disabled",
        )
        self.output.pack(fill="both", expand=True)
        self.output.tag_configure("user", foreground="#82d8ff", spacing1=8, spacing3=8)
        self.output.tag_configure("assistant", foreground="#d6dfff", spacing1=8, spacing3=8)

        self.input = tk.Text(
            chat_tab, height=3, wrap="word", bg="#121b30", fg="#edf2ff",
            insertbackground="white", relief="flat", padx=10, pady=8,
        )
        self.input.pack(fill="x", pady=(12, 8))

        row = ttk.Frame(chat_tab)
        row.pack(fill="x")
        self.status = ttk.Label(row, text="Ready")
        self.status.pack(side="left")
        self.speak_replies = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="Speak replies", variable=self.speak_replies).pack(side="left", padx=(12, 0))
        self.voice_button = tk.Button(
            row, text="Voice input", command=self.listen_once,
            bg="#263a59", fg="#edf2ff", activebackground="#354d70",
            relief="flat", padx=12, pady=7,
        )
        self.voice_button.pack(side="right", padx=(8, 0))
        self.send_button = tk.Button(
            row, text="Send", command=self.send, bg="#72d0ff",
            fg="#07101e", activebackground="#a1e0ff", relief="flat",
            padx=20, pady=7,
        )
        self.send_button.pack(side="right")
        self.input.bind("<Control-Return>", self._send_shortcut)

        self.skill_console = SkillConsole(tools_tab, self.skills)
        self.skill_console.pack(fill="both", expand=True)
        self._append("assistant", "Ready. Configure .env to connect an AI provider. Use the Tools tab for allowlisted desktop skills.")

    def _send_shortcut(self, _event):
        self.send()
        return "break"

    def _append(self, role: str, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", ("You: " if role == "user" else "Shahid: ") + text + "\n", role)
        self.output.see("end")
        self.output.configure(state="disabled")

    def send(self) -> None:
        message = self.input.get("1.0", "end").strip()
        if not message:
            return
        self.input.delete("1.0", "end")
        self._append("user", message)
        self.send_button.configure(state="disabled")
        self.voice_button.configure(state="disabled")
        self.status.configure(text="Thinking…")
        speak = bool(self.speak_replies.get())
        threading.Thread(target=self._answer, args=(message, speak), daemon=True).start()

    def _answer(self, message: str, speak: bool = False) -> None:
        try:
            self.memory.append("user", message)
            history = [{
                "role": "system",
                "content": "You are Shahid Assistant, a helpful Windows desktop assistant. Be accurate and state limitations.",
            }]
            history.extend(self.memory.get_messages())
            reply = self.engine.chat(history)
            self.memory.append("assistant", reply)
            status = "Ready"
            if speak:
                try:
                    from speech_engine import SpeechEngine
                    SpeechEngine().speak(reply)
                except Exception as exc:
                    status = "Ready · voice output unavailable"
                    reply += f"\n\n[Voice output unavailable: {exc}]"
            result = (reply, status)
        except ProviderError as exc:
            result = (f"Provider error: {exc}", "Provider error")
        except Exception as exc:
            result = (f"Unexpected error while generating a response: {exc}", "Error")
        self.root.after(0, self._finish, *result)

    def listen_once(self) -> None:
        """Capture one phrase only after the user presses the Voice input button."""
        self.voice_button.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self.status.configure(text="Listening…")
        threading.Thread(target=self._listen_once, daemon=True).start()

    def _listen_once(self) -> None:
        try:
            from speech_engine import SpeechEngine
            text = SpeechEngine().listen()
            self.root.after(0, self._voice_ready, text)
        except Exception as exc:
            self.root.after(0, self._voice_failed, str(exc))

    def _voice_ready(self, text: str) -> None:
        self.voice_button.configure(state="normal")
        self.send_button.configure(state="normal")
        if not text.strip():
            self.status.configure(text="No speech detected")
            return
        self.input.delete("1.0", "end")
        self.input.insert("1.0", text)
        self.send()

    def _voice_failed(self, error: str) -> None:
        self.voice_button.configure(state="normal")
        self.send_button.configure(state="normal")
        self.status.configure(text="Voice input unavailable")
        self._append("assistant", f"Voice input unavailable: {error}")

    def _finish(self, reply: str, status: str) -> None:
        self._append("assistant", reply)
        self.status.configure(text=status)
        self.send_button.configure(state="normal")
        self.voice_button.configure(state="normal")
        self.input.focus_set()

    def run(self) -> None:
        self.root.mainloop()


def run_ui() -> None:
    AssistantUI().run()
