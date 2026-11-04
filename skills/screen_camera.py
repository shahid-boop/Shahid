"""User-invoked screen/camera capture interfaces (optional dependencies)."""
from __future__ import annotations

from pathlib import Path
from skills.base import Skill


class ScreenCaptureSkill(Skill):
    name = "screen_camera"
    description = "Capture the screen only when explicitly requested."

    def run(self, output_path: str = "workspace/screen.png", **arguments):
        try:
            import pyautogui
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt first.") from exc
        target = Path(output_path).resolve()
        workspace = Path("workspace").resolve()
        if workspace not in target.parents:
            raise PermissionError("Capture output must stay inside workspace.")
        target.parent.mkdir(parents=True, exist_ok=True)
        pyautogui.screenshot().save(target)
        return {"saved_to": str(target)}
