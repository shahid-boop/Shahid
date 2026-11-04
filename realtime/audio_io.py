"""Sounddevice bridge for Gemini Live PCM audio; starts only when explicitly called."""
from __future__ import annotations
import asyncio

async def run_gemini_live_audio(api_key: str, model: str = "gemini-2.0-flash-live-001", on_transcript=None):
    if not api_key: raise ValueError("GOOGLE_API_KEY is required")
    try: import sounddevice as sd
    except ImportError as exc: raise RuntimeError("Install requirements-live.txt for microphone and speaker streaming") from exc
    from realtime.gemini_live import GeminiLiveSession
    input_rate, output_rate, frame_samples = 16000, 24000, 1600
    input_stream = sd.RawInputStream(samplerate=input_rate, blocksize=frame_samples, channels=1, dtype="int16")
    output_stream = sd.RawOutputStream(samplerate=output_rate, channels=1, dtype="int16")
    input_stream.start(); output_stream.start()
    session = GeminiLiveSession(api_key, model)
    try:
        async with session:
            async def receive_loop():
                async for response in session.receive():
                    server = getattr(response, "server_content", None)
                    if not server: continue
                    for field in ("input_transcription", "output_transcription"):
                        item = getattr(server, field, None)
                        value = getattr(item, "text", None) if item else None
                        if value and on_transcript: on_transcript(field, value)
                    turn = getattr(server, "model_turn", None)
                    for part in getattr(turn, "parts", []) if turn else []:
                        inline = getattr(part, "inline_data", None)
                        data = getattr(inline, "data", None) if inline else None
                        if data: await asyncio.to_thread(output_stream.write, data)
            receiver = asyncio.create_task(receive_loop())
            try:
                while not receiver.done():
                    audio, overflow = await asyncio.to_thread(input_stream.read, frame_samples)
                    if overflow: continue
                    await session.send_audio(bytes(audio), input_rate)
            finally:
                receiver.cancel()
                await asyncio.gather(receiver, return_exceptions=True)
    finally:
        input_stream.stop(); input_stream.close()
        output_stream.stop(); output_stream.close()
