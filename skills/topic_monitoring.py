"""Manual topic watchlist with explicit polling; no hidden always-on tracking."""
from __future__ import annotations

import json
from pathlib import Path

from skills.base import Skill
from skills.web_search import WebSearchSkill


class TopicMonitoringSkill(Skill):
    name = "topic_monitoring"
    description = "Save topics and check them for fresh public search results on request."

    def __init__(self, path: Path = Path("data/topics.json")):
        self.path = path
        self.search = WebSearchSkill()

    def _read(self):
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Topic watchlist must be a list.")
        return data

    def run(self, action: str = "list", topic: str = "", **arguments):
        topics = self._read()
        if action == "list":
            return topics
        if action == "add":
            value = topic.strip()
            if not value:
                raise ValueError("Topic cannot be empty.")
            if value not in topics:
                topics.append(value)
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(json.dumps(topics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return {"added": value}
        if action == "check":
            selected = [topic.strip()] if topic.strip() else topics
            return {value: self.search.run(query=value, max_results=5) for value in selected}
        raise ValueError("action must be list, add or check")
