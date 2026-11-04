"""Open a user-selected local media file with its Windows default app."""
from __future__ import annotations

import os
import platform
from pathlib import Path
from skills.base import Skill


class VideoPlayerSkill(Skill):
    name = "video_player"
    description = "Open a video file chosen by the user from the workspace."

    def run(self, path: str, **arguments):
        if platform.system() != "Windows":
            raise OSError("Windows only.")
        workspace = Path("workspace").resolve()
        target = (workspace / path).resolve()
        if workspace not in target.parents or target.suffix.lower() not in {".mp4", ".mkv", ".avi", ".mov"}:
            raise PermissionError("Choose a supported video inside workspace.")
        if not target.is_file():
            raise FileNotFoundError(target)
        os.startfile(str(target))
        return {"opened": str(target.relative_to(workspace))}
