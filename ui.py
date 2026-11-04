"""Tkinter desktop HUD; keeps the UI independent from provider internals."""
from __future__ import annotations
import threading
import tkinter as tk
from tkinter import ttk
from config_manager import Settings
from engine_pipeline import ChatEngine, ProviderError
from memory_manager import MemoryManager

class AssistantUI:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.load()
        self.engine = ChatEngine(self.settings)
        self.memory = MemoryManager()
        self.root = tk.Tk()
        self.root.title("Shahid Assistant")
        self.root.geometry("720x560")
        self.root.minsize(520, 420)
        self.root.configure(bg="#0b1020")
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#0b1020")
        style.configure("TLabel", background="#0b1020", foreground="#eaf1ff")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground="#8edcff")
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="◉  SHAHID ASSISTANT", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Windows 11 · Local desktop interface").pack(anchor="w", pady=(4, 12))
        self.output = tk.Text(outer, wrap="word", bg="#121b30", fg="#edf2ff",
                              insertbackground="white", relief="flat", padx=12, pady=12,
                              font=("Segoe UI", 10), state="disabled")
        self.output.pack(fill="both", expand=True)
        self.output.tag_configure("user", foreground="#82d8ff", spacing1=8, spacing3=8)
        self.output.tag_configure("assistant", foreground="#d6dfff", spacing1=8, spacing3=8)
        self.input = tk.Text(outer, height=3, wrap="word", bg="#121b30", fg="#edf2ff",
                             insertbackground="white", relief="flat", padx=10, pady=8)
        self.input.pack(fill="x", pady=(12, 8))
        row = ttk.Frame(outer)
        row.pack(fill="x")
        self.status = ttk.Label(row, text="Ready")
        self.status.pack(side="left")
        self.send_button = tk.Button(row, text="Send", command=self.send, bg="#72d0ff",
                                     fg="#07101e", activebackground="#a1e0ff", relief="flat",
                                     padx=20, pady=7)
        self.send_button.pack(side="right")
        self.input.bind("<Control-Return>", self._send_shortcut)
        self._append("assistant", "Ready. Configure .env to connect an AI provider.")

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
        self.status.configure(text="Thinking…")
        threading.Thread(target=self._answer, args=(message,), daemon=True).start()

    def _answer(self, message: str) -> None:
        try:
            self.memory.append("user", message)
            history = [{"role":"system","content":"You are Shahid Assistant, a helpful Windows desktop assistant. Be accurate and state limitations."}]
            history.extend(self.memory.get_messages())
            reply = self.engine.chat(history)
            self.memory.append("assistant", reply)
            result = (reply, "Ready")
        except ProviderError as exc:
            result = (f"Provider error: {exc}", "Provider error")
        except Exception:
            result = ("Unexpected error while generating a response.", "Error")
        self.root.after(0, self._finish, *result)

    def _finish(self, reply: str, status: str) -> None:
        self._append("assistant", reply)
        self.status.configure(text=status)
        self.send_button.configure(state="normal")
        self.input.focus_set()

    def run(self) -> None:
        self.root.mainloop()

def run_ui() -> None:
    AssistantUI().run()
