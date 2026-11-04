"""Conversation orchestration for the desktop assistant."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from engine_pipeline import EnginePipeline
from memory_manager import MemoryManager


@dataclass
class Turn:
    role: str
    content: str


class AssistantRuntime:
    """Coordinates user input, provider responses and local conversation memory."""

    def __init__(
        self,
        engines: EnginePipeline,
        memory: MemoryManager,
        provider_name: str,
        system_prompt: str = "You are a helpful desktop assistant.",
    ) -> None:
        self.engines = engines
        self.memory = memory
        self.provider_name = provider_name
        self.system_prompt = system_prompt
        self.history: list[Turn] = []

    def respond(self, user_text: str) -> str:
        if not user_text or not user_text.strip():
            raise ValueError("User input cannot be empty.")
        prompt = self._build_prompt(user_text.strip())
        answer = self.engines.generate(self.provider_name, prompt)
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("The selected provider returned an empty response.")
        self.history.extend((Turn("user", user_text.strip()), Turn("assistant", answer.strip())))
        return answer.strip()

    def _build_prompt(self, user_text: str) -> str:
        transcript = "\n".join(f"{turn.role}: {turn.content}" for turn in self.history[-20:])
        return f"{self.system_prompt}\n{transcript}\nuser: {user_text}\nassistant:"
