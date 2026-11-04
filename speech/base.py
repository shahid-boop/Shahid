"""Provider-neutral speech interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod


class SpeechToText(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """Convert an audio file to text."""


class TextToSpeech(ABC):
    @abstractmethod
    def synthesize(self, text: str, output_path: str) -> str:
        """Write synthesized speech and return the output path."""
