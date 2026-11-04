"""Conversation orchestration for the desktop assistant."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine_pipeline import EnginePipeline
from memory_manager import MemoryManager
from skills.loader import SkillLoader


@dataclass
class Turn:
    role: str
    content: str


class AssistantRuntime:
    """Coordinates conversation, persistent transcript and explicit skill calls."""

    def __init__(
        self,
        engines: EnginePipeline,
        memory: MemoryManager,
        provider_name: str,
        skills: SkillLoader | None = None,
        system_prompt: str = "You are a helpful desktop assistant.",
    ) -> None:
        self.engines = engines
        self.memory = memory
        self.provider_name = provider_name
        self.skills = skills or SkillLoader()
        self.system_prompt = system_prompt
        self.history: list[Turn] = []

    def respond(self, user_text: str) -> str:
        if not user_text or not user_text.strip():
            raise ValueError("User input cannot be empty.")
        prompt = self._build_prompt(user_text.strip())
        answer = self.engines.generate(self.provider_name, prompt)
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("The selected provider returned an empty response.")
        user_message = user_text.strip()
        assistant_message = answer.strip()
        self.history.extend((Turn("user", user_message), Turn("assistant", assistant_message)))
        self.memory.add(f"user: {user_message}")
        self.memory.add(f"assistant: {assistant_message}")
        return assistant_message

    def run_skill(self, name: str, **arguments: Any) -> Any:
        """Run a named skill only when explicitly requested by the caller."""
        return self.skills.run(name, **arguments)

    def _build_prompt(self, user_text: str) -> str:
        recent_memory = self.memory.recent(limit=10)
        memory_context = "\n".join(item["content"] for item in recent_memory)
        transcript = "\n".join(
            f"{turn.role}: {turn.content}" for turn in self.history[-20:]
        )
        return (
            f"{self.system_prompt}\n"
            f"Recent saved context:\n{memory_context}\n"
            f"Current conversation:\n{transcript}\n"
            f"user: {user_text}\nassistant:"
        )
