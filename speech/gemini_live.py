"""Gemini Live API session wrapper for real-time text/audio/video input.

This module uses the official google-genai async Live API. Audio/video are
sent only when the caller explicitly invokes the corresponding method.
"""
from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterable, Awaitable, Callable
from typing import Any


class GeminiLiveClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        system_instruction: str = "You are Shahid Assistant, a helpful Windows desktop assistant.",
    ) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model = model or os.getenv("GEMINI_LIVE_MODEL", "gemini-live-2.5-flash-preview")
        self.system_instruction = system_instruction
        self._client = None
        self._session = None
        self._context = None
        self._closed = True

    async def connect(self, response_modalities: tuple[str, ...] = ("AUDIO",)) -> None:
        if self._session is not None:
            return
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is not configured for Gemini Live.")
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("Install google-genai to use Gemini Live.") from exc
        self._client = genai.Client(api_key=self.api_key)
        self._context = self._client.aio.live.connect(
            model=self.model,
            config={
                "response_modalities": list(response_modalities),
                "system_instruction": self.system_instruction,
                "input_audio_transcription": {},
                "output_audio_transcription": {},
            },
        )
        self._session = await self._context.__aenter__()
        self._closed = False

    async def send_text(self, text: str) -> None:
        self._require_session()
        if not text.strip():
            raise ValueError("Text input cannot be empty.")
        await self._session.send_realtime_input(text=text.strip())

    async def send_audio(self, pcm16_bytes: bytes, sample_rate: int = 16000) -> None:
        self._require_session()
        if not pcm16_bytes:
            raise ValueError("Audio input cannot be empty.")
        from google.genai import types
        await self._session.send_realtime_input(
            audio=types.Blob(data=pcm16_bytes, mime_type=f"audio/pcm;rate={int(sample_rate)}")
        )

    async def send_video_frame(self, jpeg_bytes: bytes) -> None:
        self._require_session()
        if not jpeg_bytes:
            raise ValueError("Video frame cannot be empty.")
        from google.genai import types
        await self._session.send_realtime_input(
            video=types.Blob(data=jpeg_bytes, mime_type="image/jpeg")
        )

    async def text_turn(self, text: str) -> str:
        """Send one text turn through a connected Live session and return its text."""
        self._require_session()
        await self.send_text(text)
        chunks: list[str] = []
        async for message in self._session.receive():
            if message.text:
                chunks.append(message.text)
            server_content = getattr(message, "server_content", None)
            if getattr(server_content, "turn_complete", False):
                break
        return "".join(chunks).strip()

    async def audio_turn(self, pcm16_bytes: bytes, sample_rate: int = 16000) -> tuple[str, bytes]:
        """Send a recorded PCM16 utterance and collect Gemini Live text/audio output."""
        if not pcm16_bytes:
            raise ValueError("Audio input cannot be empty.")
        await self.connect(response_modalities=("AUDIO",))
        await self.send_audio(pcm16_bytes, sample_rate=sample_rate)
        await self._session.send_realtime_input(audio_stream_end=True)
        text_chunks: list[str] = []
        audio_chunks: list[bytes] = []
        async for message in self._session.receive():
            if message.text:
                text_chunks.append(message.text)
            server_content = getattr(message, "server_content", None)
            model_turn = getattr(server_content, "model_turn", None)
            for part in getattr(model_turn, "parts", []) or []:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    audio_chunks.append(inline_data.data)
            if getattr(server_content, "turn_complete", False):
                break
        return "".join(text_chunks).strip(), b"".join(audio_chunks)

    async def receive(self, on_text: Callable[[str], Any] | None = None,
                      on_audio: Callable[[bytes], Any] | None = None,
                      stop_event: asyncio.Event | None = None) -> None:
        """Consume server messages until stop_event is set or connection ends."""
        self._require_session()
        stop_event = stop_event or asyncio.Event()
        while not stop_event.is_set():
            try:
                async for message in self._session.receive():
                    if message.text and on_text:
                        result = on_text(message.text)
                        if isinstance(result, Awaitable):
                            await result
                    server_content = getattr(message, "server_content", None)
                    model_turn = getattr(server_content, "model_turn", None)
                    for part in getattr(model_turn, "parts", []) or []:
                        inline_data = getattr(part, "inline_data", None)
                        if inline_data and getattr(inline_data, "data", None) and on_audio:
                            result = on_audio(inline_data.data)
                            if isinstance(result, Awaitable):
                                await result
                    if stop_event.is_set():
                        return
            except asyncio.CancelledError:
                raise
            except Exception:
                if stop_event.is_set():
                    return
                raise

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        context, session = self._context, self._session
        self._context = None
        self._session = None
        try:
            if context is not None:
                await context.__aexit__(None, None, None)
            elif session is not None:
                await session.close()
        finally:
            if self._client is not None:
                close = getattr(self._client, "aclose", None)
                if close:
                    result = close()
                    if isinstance(result, Awaitable):
                        await result
                self._client = None

    def _require_session(self) -> None:
        if self._session is None or self._closed:
            raise RuntimeError("Gemini Live is not connected. Call connect() first.")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
