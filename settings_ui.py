"""Small Windows desktop settings editor for non-secret assistant preferences."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from config_manager import load_config, save_config


class SettingsWindow:
    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title("Shahid Assistant Settings")
        self.root.geometry("440x320")
        self.root.resizable(False, False)

        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Assistant name").grid(row=0, column=0, sticky="w", pady=6)
        self.name = tk.StringVar(value=self.config.get("assistant_name", "Shahid Assistant"))
        ttk.Entry(frame, textvariable=self.name, width=34).grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="Engine").grid(row=1, column=0, sticky="w", pady=6)
        self.engine = tk.StringVar(value=self.config.get("engine", "openai_compatible"))
        ttk.Combobox(frame, textvariable=self.engine, values=["openai_compatible", "gemini"], state="readonly").grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="Model").grid(row=2, column=0, sticky="w", pady=6)
        self.model = tk.StringVar(value=self.config.get("model", ""))
        ttk.Entry(frame, textvariable=self.model, width=34).grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="Base URL (optional)").grid(row=3, column=0, sticky="w", pady=6)
        self.base_url = tk.StringVar(value=self.config.get("base_url", ""))
        ttk.Entry(frame, textvariable=self.base_url, width=34).grid(row=3, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="Voice recording seconds").grid(row=4, column=0, sticky="w", pady=6)
        self.seconds = tk.IntVar(value=int(self.config.get("voice_record_seconds", 6)))
        ttk.Spinbox(frame, from_=2, to=20, textvariable=self.seconds, width=8).grid(row=4, column=1, sticky="w", pady=6)

        ttk.Label(frame, text="API key is read from environment/.env; never stored here.", wraplength=390).grid(row=5, column=0, columnspan=2, sticky="w", pady=10)
        ttk.Button(frame, text="Save settings", command=self.save).grid(row=6, column=1, sticky="e", pady=8)
        frame.columnconfigure(1, weight=1)

    def save(self):
        if not self.name.get().strip():
            messagebox.showerror("Invalid settings", "Assistant name cannot be empty.")
            return
        self.config.update({
            "assistant_name": self.name.get().strip(),
            "engine": self.engine.get(),
            "model": self.model.get().strip(),
            "base_url": self.base_url.get().strip(),
            "voice_record_seconds": max(2, min(20, self.seconds.get())),
        })
        save_config(self.config)
        messagebox.showinfo("Saved", "Settings saved. Restart the assistant to apply them.")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    SettingsWindow().run()
