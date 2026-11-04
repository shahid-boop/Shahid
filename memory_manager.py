"""Small local conversation store. Keeps a bounded history and never stores API keys."""
from __future__ import annotations
import json
from pathlib import Path
from threading import RLock
from typing import Any

class MemoryManager:
    def __init__(self, path: str | Path = "data/conversations.json", max_messages: int = 40):
        self.path = Path(path)
        self.max_messages = max(2, max_messages)
        self._lock = RLock()

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def get_messages(self, conversation_id: str = "default") -> list[dict[str, str]]:
        with self._lock:
            items = self._read().get(conversation_id, [])
            if not isinstance(items, list):
                return []
            return [m for m in items[-self.max_messages:] if isinstance(m, dict)
                    and m.get("role") in {"user", "assistant", "system"}
                    and isinstance(m.get("content"), str)]

    def append(self, role: str, content: str, conversation_id: str = "default") -> None:
        if role not in {"user", "assistant", "system"}:
            raise ValueError("Unsupported message role")
        content = content.strip()
        if not content:
            return
        with self._lock:
            data = self._read()
            items = data.get(conversation_id, [])
            if not isinstance(items, list):
                items = []
            items.append({"role": role, "content": content[:12000]})
            data[conversation_id] = items[-self.max_messages:]
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(".tmp")
            temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            temp.replace(self.path)

    def clear(self, conversation_id: str = "default") -> None:
        with self._lock:
            data = self._read()
            data.pop(conversation_id, None)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
