"""Optional Gemini Live audio session adapter. Requires google-genai and a Live-capable API key."""
from __future__ import annotations
import asyncio
from typing import Callable

class GeminiLiveUnavailable(RuntimeError): pass

async def run_live_session(api_key: str, on_text: Callable[[str], None] | None = None,
                           model: str = "gemini-2.0-flash-live-001") -> None:
    if not api_key: raise GeminiLiveUnavailable("GOOGLE_API_KEY is required.")
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise GeminiLiveUnavailable("Install optional packages: pip install -r requirements-live.txt") from exc
    client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
    config = {"response_modalities": ["AUDIO"],
              "input_audio_transcription": {},
              "output_audio_transcription": {}}
    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            print("Gemini Live connected. Speak into the selected microphone; Ctrl+C to stop.")
            async for response in session.receive():
                server = getattr(response, "server_content", None)
                if server:
                    transcription = getattr(server, "input_transcription", None)
                    output = getattr(server, "output_transcription", None)
                    for item in (transcription, output):
                        text = getattr(item, "text", None) if item else None
                        if text and on_text: on_text(text)
                    audio = getattr(server, "model_turn", None)
                    if audio:
                        for part in getattr(audio, "parts", []):
                            data = getattr(getattr(part, "inline_data", None), "data", None)
                            if data:
                                # Audio playback is intentionally delegated to a platform audio backend.
                                raise GeminiLiveUnavailable("Live audio received; connect a supported PCM playback backend to hear output.")
    except asyncio.CancelledError: raise
    except Exception as exc:
        raise GeminiLiveUnavailable(f"Gemini Live session failed: {exc}") from exc

def run_live(api_key: str, on_text=None, model: str = "gemini-2.0-flash-live-001"):
    try: asyncio.run(run_live_session(api_key, on_text, model))
    except KeyboardInterrupt: return
