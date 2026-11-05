"""Tkinter console that exposes registered skills with per-action confirmation."""
from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from desktop.skill_dispatch import SENSITIVE_SKILLS, dispatch_skill


class SkillConsole(ttk.Frame):
    """Small, explicit tool-dispatch panel for the existing skill registry."""

    def __init__(self, master: tk.Misc, registry: Any):
        super().__init__(master, padding=12)
        self.registry = registry
        self.skill_name = tk.StringVar()
        ttk.Label(
            self,
            text="Allowlisted tools run locally. Camera, screen, desktop input, "
                 "settings, plugin installation and state-changing actions ask "
                 "for confirmation before execution.",
            wraplength=620,
        ).pack(fill="x", anchor="w", pady=(0, 10))

        selector = ttk.Frame(self)
        selector.pack(fill="x")
        ttk.Label(selector, text="Tool").pack(side="left")
        self.selector = ttk.Combobox(
            selector, textvariable=self.skill_name, state="readonly", width=34
        )
        self.selector.pack(side="left", padx=(8, 8), fill="x", expand=True)
        ttk.Button(selector, text="Refresh", command=self.refresh).pack(side="left")

        ttk.Label(self, text="Arguments (JSON object)").pack(anchor="w", pady=(12, 4))
        self.arguments = tk.Text(self, height=7, wrap="word")
        self.arguments.pack(fill="x", expand=False)
        self.arguments.insert("1.0", "{}")

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=8)
        self.run_button = ttk.Button(actions, text="Run selected tool", command=self.run_selected)
        self.run_button.pack(side="left")
        self.status = ttk.Label(actions, text="Ready")
        self.status.pack(side="left", padx=12)

        ttk.Label(self, text="Result").pack(anchor="w", pady=(6, 4))
        self.result = tk.Text(self, height=12, wrap="word", state="disabled")
        self.result.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self) -> None:
        names = self.registry.names()
        self.selector.configure(values=names)
        if names and self.skill_name.get() not in names:
            self.skill_name.set(names[0])
        elif not names:
            self.skill_name.set("")
        self.status.configure(text=f"{len(names)} tools available")

    def _show_result(self, value: str) -> None:
        self.result.configure(state="normal")
        self.result.delete("1.0", "end")
        self.result.insert("1.0", value)
        self.result.configure(state="disabled")

    def run_selected(self) -> None:
        name = self.skill_name.get().strip()
        if not name:
            self.status.configure(text="Select a tool")
            return
        try:
            payload = json.loads(self.arguments.get("1.0", "end").strip() or "{}")
            if not isinstance(payload, dict):
                raise ValueError("Arguments must be a JSON object.")
            approved = False
            if name in SENSITIVE_SKILLS:
                approved = messagebox.askyesno(
                    "Confirm Shahid Assistant action",
                    f"Run '{name}' now?\n\n"
                    "This action may access private screen/camera data, interact "
                    "with the desktop, change a setting, install a plugin, or "
                    "modify local assistant data. Continue only if you intended it.",
                    parent=self.winfo_toplevel(),
                )
                if not approved:
                    self.status.configure(text="Cancelled")
                    self._show_result("Cancelled — no tool was run.")
                    return
            self.run_button.configure(state="disabled")
            self.status.configure(text="Running…")
            result = dispatch_skill(self.registry, name, payload, approved=approved)
            self._show_result(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            self.status.configure(text="Completed")
        except Exception as exc:
            self._show_result(f"{type(exc).__name__}: {exc}")
            self.status.configure(text="Tool failed")
        finally:
            self.run_button.configure(state="normal")
