"""Limited Windows settings launcher; no silent settings mutation."""
from __future__ import annotations

import platform
import subprocess
from skills.base import Skill


class ComputerSettingsSkill(Skill):
    name = "computer_settings"
    description = "Open selected Windows Settings pages after explicit user request."

    PAGES = {
        "display": "ms-settings:display",
        "sound": "ms-settings:sound",
        "bluetooth": "ms-settings:bluetooth",
        "wifi": "ms-settings:network-wifi",
        "windows_update": "ms-settings:windowsupdate",
        "privacy": "ms-settings:privacy",
    }

    def run(self, page: str, **arguments):
        if platform.system() != "Windows":
            raise OSError("Windows only.")
        key = page.strip().lower()
        if key not in self.PAGES:
            raise ValueError(f"Unsupported page. Choose: {', '.join(self.PAGES)}")
        subprocess.Popen(["cmd", "/c", "start", "", self.PAGES[key]], shell=False)
        return {"opened": key}
