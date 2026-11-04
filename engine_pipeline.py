"""Provider-neutral engine pipeline.

Concrete LLM, speech-to-text and text-to-speech providers are registered
in later implementation stages. This module defines their common boundary.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EngineProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, prompt: str, **options: Any) -> str:
        """Generate a text response from a prompt."""


class EnginePipeline:
    def __init__(self) -> None:
        self._providers: dict[str, EngineProvider] = {}

    def register(self, provider: EngineProvider) -> None:
        name = getattr(provider, "name", "")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Provider must define a non-empty name.")
        self._providers[name] = provider

    def available_providers(self) -> list[str]:
        return sorted(self._providers)

    def generate(self, provider_name: str, prompt: str, **options: Any) -> str:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")
        try:
            provider = self._providers[provider_name]
        except KeyError as exc:
            available = ", ".join(self.available_providers()) or "none"
            raise LookupError(
                f"Provider '{provider_name}' is not registered. Available: {available}"
            ) from exc
        return provider.generate(prompt, **options)
