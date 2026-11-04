"""OpenAI Whisper speech-to-text adapter."""
from __future__ import annotations

import os
from speech.base import SpeechToText


class WhisperSpeechToText(SpeechToText):
    def __init__(self, model: str = "whisper-1"):
        self.model = model

    def transcribe(self, audio_path: str) -> str:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt first.") from exc
        with open(audio_path, "rb") as audio:
            result = OpenAI().audio.transcriptions.create(model=self.model, file=audio)
        return result.text
