"""Discover and execute explicitly registered skills."""
from __future__ import annotations

from skills.base import Skill


class SkillLoader:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        name = getattr(skill, "name", "")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Skill must have a non-empty name.")
        self._skills[name] = skill

    def list_skills(self) -> list[dict[str, str]]:
        return [
            {"name": skill.name, "description": skill.description}
            for skill in sorted(self._skills.values(), key=lambda item: item.name)
        ]

    def run(self, name: str, **arguments):
        if name not in self._skills:
            raise LookupError(f"Unknown skill: {name}")
        return self._skills[name].run(**arguments)
