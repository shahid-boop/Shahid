"""Read-only text file inspection within a configured workspace."""
from __future__ import annotations

from pathlib import Path
from skills.base import Skill


class FileProcessingSkill(Skill):
    name = "file_processing"
    description = "Read text files inside the assistant workspace."

    def __init__(self, workspace: Path = Path("workspace")):
        self.workspace = workspace.resolve()

    def run(self, path: str, **arguments):
        target = (self.workspace / path).resolve()
        if self.workspace not in target.parents and target != self.workspace:
            raise PermissionError("Path is outside the assistant workspace.")
        if target.suffix.lower() not in {".txt", ".md", ".json", ".csv", ".log", ".py"}:
            raise ValueError("Unsupported text file type.")
        if not target.is_file():
            raise FileNotFoundError(target)
        if target.stat().st_size > 2_000_000:
            raise ValueError("File is larger than the 2 MB safety limit.")
        return {"path": str(target.relative_to(self.workspace)), "content": target.read_text(encoding="utf-8")}
