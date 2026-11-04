"""Explicit skill registry; no automatic imports or arbitrary code execution."""
from __future__ import annotations
from collections.abc import Callable
from typing import Any

Skill = Callable[[dict[str, Any]], dict[str, Any]]

class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, name: str, handler: Skill) -> None:
        clean = name.strip().lower()
        if not clean or not clean.replace("_", "").isalnum():
            raise ValueError("Skill names may contain only letters, numbers, and underscores")
        if clean in self._skills:
            raise ValueError(f"Skill already registered: {clean}")
        self._skills[clean] = handler

    def names(self) -> list[str]:
        return sorted(self._skills)

    def run(self, name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        key = name.strip().lower()
        if key not in self._skills:
            raise KeyError(f"Skill is not allowlisted: {key}")
        result = self._skills[key](payload or {})
        if not isinstance(result, dict):
            raise TypeError("Skill handlers must return a dictionary")
        return result
