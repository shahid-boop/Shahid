"""Common contract for assistant skills."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Skill(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, **arguments: Any) -> Any:
        """Execute a skill with validated arguments."""
