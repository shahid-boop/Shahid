"""Safe workspace file tools. Access is confined to the assistant's workspace directory."""
from __future__ import annotations
from pathlib import Path
import os
from typing import Any

WORKSPACE = Path(__file__).resolve().parents[1] / "workspace"
MAX_READ_BYTES = 256_000
MAX_WRITE_BYTES = 256_000

def _target(payload: dict[str, Any] | None) -> Path:
    name = str((payload or {}).get("path", "")).strip()
    if not name:
        raise ValueError("A relative workspace path is required.")
    candidate = (WORKSPACE / name).resolve()
    root = WORKSPACE.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("Path must stay inside the workspace.")
    return candidate

def _relative(path: Path) -> str:
    # os.path.relpath handles Windows case-normalized temporary paths reliably.
    return os.path.relpath(str(path), str(WORKSPACE.resolve()))

def list_files(_: dict[str, Any] | None = None) -> dict[str, Any]:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    files = sorted(str(p.relative_to(WORKSPACE)) for p in WORKSPACE.rglob("*") if p.is_file())
    return {"workspace": str(WORKSPACE), "files": files}

def read_file(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    path = _target(payload)
    if not path.is_file():
        raise FileNotFoundError("Workspace file does not exist.")
    if path.stat().st_size > MAX_READ_BYTES:
        raise ValueError("File is too large to read (maximum 256 KB).")
    return {"path": _relative(path), "content": path.read_text(encoding="utf-8")}

def write_file(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = payload or {}
    path = _target(data)
    content = data.get("content")
    if not isinstance(content, str):
        raise ValueError("content must be a string.")
    if len(content.encode("utf-8")) > MAX_WRITE_BYTES:
        raise ValueError("Content is too large (maximum 256 KB).")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"written": str(path.relative_to(WORKSPACE)), "bytes": len(content.encode("utf-8"))}

def register_file_skills(registry) -> None:
    registry.register("list_workspace_files", list_files)
    registry.register("read_workspace_file", read_file)
    registry.register("write_workspace_file", write_file)
