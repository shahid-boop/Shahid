"""Windows application lookup using a conservative allowlist."""
from __future__ import annotations

import platform
import shutil
import subprocess
from skills.base import Skill


class AppIdentitySkill(Skill):
    name = "app_identity"
    description = "Check whether common Windows applications are installed."

    ALLOWED = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "explorer": "explorer.exe",
    }

    def run(self, app: str, **arguments):
        if platform.system() != "Windows":
            raise OSError("This skill is currently implemented for Windows.")
        key = app.strip().lower()
        if key not in self.ALLOWED:
            raise ValueError(f"Unsupported application. Choose: {', '.join(self.ALLOWED)}")
        executable = self.ALLOWED[key]
        return {"app": key, "available": shutil.which(executable) is not None}

    @classmethod
    def open_app(cls, app: str) -> None:
        """Launch only allowlisted built-in apps; caller must request this explicitly."""
        if platform.system() != "Windows":
            raise OSError("Windows only.")
        key = app.strip().lower()
        if key not in cls.ALLOWED:
            raise ValueError("Application is not allowlisted.")
        subprocess.Popen([cls.ALLOWED[key]], shell=False)
