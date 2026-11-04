"""Continuous microphone-to-Gemini Live audio with concurrent speaker playback.

Microphone access begins only after start() is explicitly called. Pressing the
UI stop control cancels capture, sending and playback and closes device streams.
"""
from __future__ import annotations

import asyncio
import queue
import threading
from typing import Any

from speech.gemini_live import GeminiLiveClient


class AdaptiveEchoCanceller:
    """NLMS echo reducer driven by a Windows WASAPI loopback reference."""
    def __init__(self, taps=96, step=0.18):
        import numpy as np
        self.np = np
        self.weights = np.zeros(taps, dtype=np.float32)
        self.history = np.zeros(taps, dtype=np.float32)
        self.step = step

    def process(self, microphone, reference):
        np = self.np
        mic = np.frombuffer(microphone, dtype=np.int16).astype(np.float32)
        ref = np.frombuffer(reference, dtype=np.int16).astype(np.float32)
        ref = ref[:len(mic)] if len(ref) >= len(mic) else np.pad(ref, (0, len(mic)-len(ref)))
        output = np.empty_like(mic)
        for index, sample in enumerate(ref):
            self.history[1:] = self.history[:-1]
            self.history[0] = sample / 32768.0
            estimate = float(np.dot(self.weights, self.history))
            error = mic[index] / 32768.0 - estimate
            norm = float(np.dot(self.history, self.history)) + 1e-5
            self.weights += (self.step * error / norm) * self.history
            output[index] = max(-32768, min(32767, error * 32768.0))
        rms = float(np.sqrt(np.mean(output * output))) if len(output) else 0.0
        return output.astype(np.int16).tobytes(), rms

class LiveVoiceSession:
    def __init__(
        self,
        client: GeminiLiveClient,
        sample_rate: int = 16000,
        output_rate: int = 24000,
        chunk_ms: int = 100,
    ):
        self.client = client
        self.sample_rate = int(sample_rate)
        self.output_rate = int(output_rate)
        self.chunk_frames = max(160, self.sample_rate * int(chunk_ms) // 1000)
        self._audio_out: queue.Queue[bytes] = queue.Queue(maxsize=80)
        self._input_queue: asyncio.Queue[bytes] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop = threading.Event()
        self._input_stream: Any = None
        self._output_stream: Any = None
        self._loopback_stream: Any = None
        self._reference_audio = queue.Queue(maxsize=40)
        self._aec = None
        self._assistant_speaking = threading.Event()
        self._speech_threshold = 650.0
        self._speech_hangover = 0

    def stop(self) -> None:
        self._stop.set()
        # Discard queued speech immediately so playback is interruptible.
        while True:
            try:
                self._audio_out.get_nowait()
            except queue.Empty:
                break

    async def run(self, stop_event: threading.Event | None = None) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("Install sounddevice to use continuous voice.") from exc

        external_stop = stop_event or self._stop
        self._loop = asyncio.get_running_loop()
        self._input_queue = asyncio.Queue(maxsize=40)

        def on_loopback(indata, frames, timing, status):
            if status:
                return
            try:
                self._reference_audio.put_nowait(bytes(indata))
            except queue.Full:
                try:
                    self._reference_audio.get_nowait()
                    self._reference_audio.put_nowait(bytes(indata))
                except queue.Empty:
                    pass

        def on_input(indata, frames, timing, status):
            if status:
                return
            payload = bytes(indata)
            samples = memoryview(payload).cast('h')
            rms = math.sqrt(sum(value * value for value in samples) / max(1, len(samples)))
            if self._aec is not None:
                try:
                    reference = self._reference_audio.get_nowait()
                    payload, rms = self._aec.process(payload, reference)
                except queue.Empty:
                    pass
            if rms >= self._speech_threshold:
                self._speech_hangover = 8
            elif self._speech_hangover:
                self._speech_hangover -= 1
            if self._speech_hangover and (self._assistant_speaking.is_set() or not self._audio_out.empty()):
                while True:
                    try:
                        self._audio_out.get_nowait()
                    except queue.Empty:
                        break
                self._assistant_speaking.clear()
            if self._loop and self._input_queue:
                def enqueue():
                    if self._input_queue.full():
                        try:
                            self._input_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                    self._input_queue.put_nowait(payload)
                self._loop.call_soon_threadsafe(enqueue)
        def on_output(outdata, frames, timing, status):
            needed = frames * 2
            chunks = bytearray()
            while len(chunks) < needed:
                try:
                    part = self._audio_out.get_nowait()
                except queue.Empty:
                    break
                take = min(len(part), needed - len(chunks))
                chunks.extend(part[:take])
                if len(part) > take:
                    self._audio_out.put_nowait(part[take:])
            outdata[:] = bytes(chunks).ljust(needed, b"\x00")

        await self.client.connect(response_modalities=("AUDIO",))
        self._input_stream = sd.RawInputStream(
            samplerate=self.sample_rate, blocksize=self.chunk_frames,
            channels=1, dtype="int16", callback=on_input,
        )
        self._output_stream = sd.RawOutputStream(
            samplerate=self.output_rate, channels=1, dtype="int16",
            blocksize=0, callback=on_output,
        )
        self._input_stream.start()
        self._output_stream.start()

        async def send_loop():
            from google.genai import types
            while not external_stop.is_set():
                try:
                    chunk = await asyncio.wait_for(self._input_queue.get(), timeout=0.2)
                except asyncio.TimeoutError:
                    continue
                await self.client._session.send_realtime_input(
                    audio=types.Blob(data=chunk, mime_type=f"audio/pcm;rate={self.sample_rate}")
                )
            await self.client._session.send_realtime_input(audio_stream_end=True)

        async def receive_loop():
            async for message in self.client._session.receive():
                server_content = getattr(message, "server_content", None)
                model_turn = getattr(server_content, "model_turn", None)
                for part in getattr(model_turn, "parts", []) or []:
                    inline_data = getattr(part, "inline_data", None)
                    audio = getattr(inline_data, "data", None) if inline_data else None
                    if audio:
                        try:
                            self._audio_out.put_nowait(audio)
                        except queue.Full:
                            # Prefer recent speech over stale queued audio.
                            try:
                                self._audio_out.get_nowait()
                                self._audio_out.put_nowait(audio)
                            except queue.Empty:
                                pass
                if external_stop.is_set() and getattr(server_content, "turn_complete", False):
                    return

        sender = asyncio.create_task(send_loop())
        receiver = asyncio.create_task(receive_loop())
        try:
            while not external_stop.is_set():
                if receiver.done():
                    await receiver
                    break
                await asyncio.sleep(0.05)
            if not sender.done():
                try:
                    await asyncio.wait_for(sender, timeout=1.0)
                except asyncio.TimeoutError:
                    sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)
            if not receiver.done():
                try:
                    await asyncio.wait_for(receiver, timeout=1.5)
                except asyncio.TimeoutError:
                    receiver.cancel()
            await asyncio.gather(receiver, return_exceptions=True)
        finally:
            self.stop()
            for stream in (self._input_stream, self._output_stream):
                if stream is not None:
                    try:
                        stream.stop()
                        stream.close()
                    except Exception:
                        pass
            self._input_stream = self._output_stream = None
            await self.client.close()
