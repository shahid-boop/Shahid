"""Safe workspace file operations. Delete and overwrite are intentionally absent."""
from __future__ import annotations

from pathlib import Path
from skills.base import Skill


class FileControlSkill(Skill):
    name = "file_control"
    description = "Create new text files in the assistant workspace without overwriting."

    def __init__(self, workspace: Path = Path("workspace")):
        self.workspace = workspace.resolve()

    def run(self, action: str, path: str, content: str = "", **arguments):
        if action != "create":
            raise ValueError("Only the non-destructive 'create' action is supported.")
        target = (self.workspace / path).resolve()
        if self.workspace not in target.parents:
            raise PermissionError("Path is outside the assistant workspace.")
        if target.suffix.lower() not in {".txt", ".md", ".json", ".csv"}:
            raise ValueError("Only text, Markdown, JSON and CSV files can be created.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as handle:
            handle.write(content)
        return {"created": str(target.relative_to(self.workspace))}
