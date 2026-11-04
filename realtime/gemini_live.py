"""Optional Gemini Live audio session adapter. Requires google-genai and a Live-capable API key."""
from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator

class GeminiLiveUnavailable(RuntimeError): pass

class GeminiLiveSession:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-live-001"):
        if not api_key: raise GeminiLiveUnavailable("GOOGLE_API_KEY is required.")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise GeminiLiveUnavailable("Install requirements-live.txt (google-genai).") from exc
        self._client = genai.Client(api_key=api_key)
        self._types = types
        self.model = model
        self._session = None
        self._manager = None

    async def __aenter__(self):
        config = self._types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            input_audio_transcription=self._types.AudioTranscriptionConfig(),
            output_audio_transcription=self._types.AudioTranscriptionConfig(),
        )
        self._manager = self._client.aio.live.connect(model=self.model, config=config)
        self._session = await self._manager.__aenter__()
        return self

    async def __aexit__(self, *exc):
        if self._manager:
            await self._manager.__aexit__(*exc)

    async def send_audio(self, pcm16: bytes, sample_rate: int = 16000) -> None:
        if not self._session: raise GeminiLiveUnavailable("Open the Live session first.")
        blob = self._types.Blob(data=pcm16, mime_type=f"audio/pcm;rate={sample_rate}")
        await self._session.send_realtime_input(audio=blob)

    async def send_text(self, text: str) -> None:
        if not self._session: raise GeminiLiveUnavailable("Open the Live session first.")
        await self._session.send_realtime_input(text=text)

    async def receive(self) -> AsyncIterator[object]:
        if not self._session: raise GeminiLiveUnavailable("Open the Live session first.")
        async for response in self._session.receive():
            yield response

    async def close(self) -> None:
        if self._manager:
            await self._manager.__aexit__(None, None, None)
            self._manager = None
            self._session = None
