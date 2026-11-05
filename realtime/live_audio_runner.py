"""Cooperative-stop Gemini Live runner used by the desktop HUD."""
from __future__ import annotations

import asyncio
import threading


async def run_stoppable_gemini_live_audio(
    api_key: str,
    *,
    stop_event: threading.Event,
    on_transcript=None,
    model: str = "gemini-2.0-flash-live-001",
) -> None:
    """Run an explicitly approved Live audio session until stop_event is set."""
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is required")
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError(
            "Install requirements-live.txt for microphone and speaker streaming"
        ) from exc

    from realtime.gemini_live import GeminiLiveSession

    input_rate, output_rate, frame_samples = 16000, 24000, 1600
    input_stream = sd.RawInputStream(
        samplerate=input_rate, blocksize=frame_samples, channels=1, dtype="int16"
    )
    output_stream = sd.RawOutputStream(
        samplerate=output_rate, channels=1, dtype="int16"
    )
    input_started = output_started = False
    session = GeminiLiveSession(api_key, model)
    try:
        input_stream.start()
        input_started = True
        output_stream.start()
        output_started = True
        async with session:
            async def receive_loop():
                async for response in session.receive():
                    server = getattr(response, "server_content", None)
                    if not server:
                        continue
                    for field in ("input_transcription", "output_transcription"):
                        item = getattr(server, field, None)
                        value = getattr(item, "text", None) if item else None
                        if value and on_transcript:
                            on_transcript(field, value)
                    turn = getattr(server, "model_turn", None)
                    for part in getattr(turn, "parts", []) if turn else []:
                        inline = getattr(part, "inline_data", None)
                        data = getattr(inline, "data", None) if inline else None
                        if data:
                            await asyncio.to_thread(output_stream.write, data)

            receiver = asyncio.create_task(receive_loop())
            try:
                while not stop_event.is_set() and not receiver.done():
                    audio, overflow = await asyncio.to_thread(
                        input_stream.read, frame_samples
                    )
                    if overflow or stop_event.is_set():
                        continue
                    await session.send_audio(bytes(audio), input_rate)
            finally:
                receiver.cancel()
                await asyncio.gather(receiver, return_exceptions=True)
    finally:
        if input_started:
            input_stream.stop()
        input_stream.close()
        if output_started:
            output_stream.stop()
        output_stream.close()
