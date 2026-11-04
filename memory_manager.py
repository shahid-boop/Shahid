"""Small local persistent-memory store for the assistant."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MEMORY_PATH = Path("data/memory.json")


class MemoryManager:
    def __init__(self, path: Path = MEMORY_PATH) -> None:
        self.path = path

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Could not read memory at {self.path}: {exc}") from exc
        if not isinstance(data, list):
            raise ValueError("Memory store must contain a JSON list.")
        return data

    def add(self, content: str) -> dict[str, str]:
        """Append one memory item and return the saved record."""
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Memory content cannot be empty.")

        record = {
            "content": content.strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        records = self._read()
        records.append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return record

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        return self._read()[-limit:]
