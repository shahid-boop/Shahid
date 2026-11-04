"""Push-to-talk voice controller for Windows 11.

Recording starts only after an explicit call to listen_once(). Audio is not
captured in the background.
"""
from __future__ import annotations

import os
import tempfile
import wave
from pathlib import Path

from speech.openai_tts import OpenAITextToSpeech
from speech.whisper_stt import WhisperSpeechToText


class WindowsVoiceController:
    def __init__(self, sample_rate: int = 16000, seconds: int = 6):
        self.sample_rate = sample_rate
        self.seconds = seconds
        self.stt = WhisperSpeechToText()
        self.tts = OpenAITextToSpeech()

    def record_pcm_once(self) -> bytes:
        """Record a fixed-length PCM16 utterance after explicit UI invocation."""
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("Install sounddevice to enable microphone input.") from exc
        recording = sd.rec(
            int(self.seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        return recording.tobytes()

    def play_pcm(self, pcm16_bytes: bytes, sample_rate: int = 24000) -> None:
        """Play a PCM16 audio response through the default output device."""
        if not pcm16_bytes:
            return
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Install sounddevice and numpy for PCM playback.") from exc
        audio = np.frombuffer(pcm16_bytes, dtype=np.int16)
        sd.play(audio, samplerate=int(sample_rate), blocking=True)

    def listen_once(self) -> str:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("Install sounddevice to enable microphone input.") from exc

        recording = sd.rec(
            int(self.seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            audio_path = Path(temp.name)
        try:
            with wave.open(str(audio_path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(self.sample_rate)
                wav.writeframes(recording.tobytes())
            return self.stt.transcribe(str(audio_path))
        finally:
            audio_path.unlink(missing_ok=True)

    def speak(self, text: str) -> None:
        if not text.strip():
            return
        try:
            import winsound
        except ImportError as exc:
            raise OSError("Windows audio playback is required.") from exc
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            output_path = Path(temp.name)
        try:
            self.tts.synthesize(text, str(output_path), response_format="wav")
            winsound.PlaySound(str(output_path), winsound.SND_FILENAME)
        finally:
            output_path.unlink(missing_ok=True)
