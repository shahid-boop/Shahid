"""Web search skill using the optional duckduckgo-search package."""
from __future__ import annotations

from skills.base import Skill


class WebSearchSkill(Skill):
    name = "web_search"
    description = "Search the public web and return titles, links and snippets."

    def run(self, query: str, max_results: int = 5, **arguments):
        if not query.strip():
            raise ValueError("Search query cannot be empty.")
        try:
            from duckduckgo_search import DDGS
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt to enable web search.") from exc
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max(1, min(max_results, 10))))
