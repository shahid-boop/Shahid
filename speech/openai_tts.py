"""OpenAI text-to-speech adapter."""
from __future__ import annotations

import os
from speech.base import TextToSpeech


class OpenAITextToSpeech(TextToSpeech):
    def __init__(self, model: str = "tts-1", voice: str = "nova"):
        self.model = model
        self.voice = voice

    def synthesize(self, text: str, output_path: str) -> str:
        if not text.strip():
            raise ValueError("Text cannot be empty.")
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt first.") from exc
        response = OpenAI().audio.speech.create(model=self.model, voice=self.voice, input=text)
        response.stream_to_file(output_path)
        return output_path
