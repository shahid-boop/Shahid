"""Confirmed Windows UI actions with a narrow, auditable operation allowlist."""
from __future__ import annotations

import platform
import subprocess
from skills.base import Skill


class WindowsAutomationSkill(Skill):
    name = "windows_automation"
    description = "Launch approved apps and perform individually confirmed basic UI actions."

    ACTIONS = {
        "open_task_manager": ["taskmgr.exe"],
        "open_file_explorer": ["explorer.exe"],
        "open_notepad": ["notepad.exe"],
        "open_settings": ["cmd.exe", "/c", "start", "", "ms-settings:"],
    }
    SAFE_KEYS = {
        "enter", "tab", "escape", "space", "backspace", "delete",
        "up", "down", "left", "right", "home", "end", "pageup", "pagedown",
        "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
    }
    SAFE_HOTKEYS = {("ctrl", "c"), ("ctrl", "v"), ("ctrl", "x"), ("ctrl", "a"),
                    ("ctrl", "f"), ("ctrl", "s"), ("alt", "tab"), ("alt", "f4")}

    @staticmethod
    def _pyautogui():
        try:
            import pyautogui
        except ImportError as exc:
            raise RuntimeError("Install pyautogui to enable UI automation.") from exc
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.15
        return pyautogui

    def run(self, action: str, confirmed: bool = False, **arguments):
        if platform.system() != "Windows":
            raise OSError("This skill is available only on Windows.")
        if confirmed is not True:
            raise PermissionError("Every UI action requires explicit user confirmation.")
        command = self.ACTIONS.get(action)
        if command is not None:
            subprocess.Popen(command, shell=False)
            return {"started": action}

        gui = self._pyautogui()
        if action == "click":
            x, y = arguments.get("x"), arguments.get("y")
            if not isinstance(x, int) or not isinstance(y, int) or x < 0 or y < 0:
                raise ValueError("click requires non-negative integer x and y coordinates.")
            width, height = gui.size()
            if x >= width or y >= height:
                raise ValueError("Click coordinates are outside the current screen.")
            gui.click(x=x, y=y)
            return {"clicked": {"x": x, "y": y}}
        if action == "type_text":
            value = arguments.get("text")
            if not isinstance(value, str) or not value or len(value) > 2000:
                raise ValueError("type_text requires 1-2000 characters.")
            gui.write(value, interval=0.01)
            return {"typed_characters": len(value)}
        if action == "press_key":
            key = str(arguments.get("key", "")).lower()
            if key not in self.SAFE_KEYS:
                raise ValueError(f"Unsupported key. Allowed: {', '.join(sorted(self.SAFE_KEYS))}")
            gui.press(key)
            return {"pressed": key}
        if action == "hotkey":
            keys = tuple(str(key).lower() for key in arguments.get("keys", []))
            if keys not in self.SAFE_HOTKEYS:
                raise ValueError("Hotkey is not in the safe allowlist.")
            gui.hotkey(*keys)
            return {"hotkey": list(keys)}
        raise ValueError("Unsupported action. Choose an approved app launch or click/type_text/press_key/hotkey.")
