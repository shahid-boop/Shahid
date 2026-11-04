"""OpenAI text-to-speech adapter."""
from __future__ import annotations

import os
from speech.base import TextToSpeech


class OpenAITextToSpeech(TextToSpeech):
    def __init__(self, model: str = "tts-1", voice: str = "nova"):
        self.model = model
        self.voice = voice

    def synthesize(self, text: str, output_path: str, response_format: str = "mp3") -> str:
        if not text.strip():
            raise ValueError("Text cannot be empty.")
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        if response_format not in {"mp3", "opus", "aac", "flac", "wav", "pcm"}:
            raise ValueError("Unsupported audio response format.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt first.") from exc
        response = OpenAI().audio.speech.create(
            model=self.model, voice=self.voice, input=text,
            response_format=response_format,
        )
        response.stream_to_file(output_path)
        return output_path
