"""Lightweight Tkinter HUD/chat interface."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from typing import Callable


class AssistantWindow:
    def __init__(self, respond: Callable[[str], str]) -> None:
        self.respond = respond
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
        self._append("System", "Assistant interface ready.")

    def _append(self, speaker: str, message: str) -> None:
        self.output.configure(state="normal")
        self.output.insert(tk.END, f"{speaker}: {message}\n\n")
        self.output.see(tk.END)
        self.output.configure(state="disabled")

    def _send_event(self, _event) -> None:
        self._send()

    def _send(self) -> None:
        message = self.entry.get().strip()
        if not message:
            return
        self.entry.delete(0, tk.END)
        self._append("You", message)
        self.send_button.configure(state=tk.DISABLED)

        def work() -> None:
            try:
                answer = self.respond(message)
                self.root.after(0, lambda: self._append("Assistant", answer))
            except Exception as exc:
                self.root.after(0, lambda: self._append("Error", str(exc)))
            finally:
                self.root.after(0, lambda: self.send_button.configure(state=tk.NORMAL))

        threading.Thread(target=work, daemon=True).start()

    def run(self) -> None:
        self.root.mainloop()


def launch(respond: Callable[[str], str]) -> None:
    try:
        AssistantWindow(respond).run()
    except tk.TclError as exc:
        messagebox.showerror("Assistant UI", str(exc))
        raise
