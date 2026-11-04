"""Allowlisted, explicitly confirmed Windows 11 actions."""
from __future__ import annotations

import platform
import subprocess
from skills.base import Skill


class WindowsAutomationSkill(Skill):
    name = "windows_automation"
    description = "Launch a few safe Windows utilities after explicit confirmation."

    ACTIONS = {
        "open_task_manager": ["taskmgr.exe"],
        "open_file_explorer": ["explorer.exe"],
        "open_notepad": ["notepad.exe"],
        "open_settings": ["cmd.exe", "/c", "start", "", "ms-settings:"],
    }

    def run(self, action: str, confirmed: bool = False, **arguments):
        if platform.system() != "Windows":
            raise OSError("This skill is available only on Windows.")
        if confirmed is not True:
            raise PermissionError("Set confirmed=true only after the user explicitly approves the action.")
        command = self.ACTIONS.get(action)
        if command is None:
            raise ValueError(f"Unsupported action. Choose one of: {', '.join(sorted(self.ACTIONS))}")
        subprocess.Popen(command, shell=False)
        return {"started": action}
