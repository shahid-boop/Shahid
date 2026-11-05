"""Opt-in local audio skills for file transcription and bounded wake-word listening."""
from __future__ import annotations

import time
from pathlib import Path


def transcribe_audio(payload=None):
    data = payload or {}
    audio_path = str(data.get("audio_path", "")).strip()
    if not audio_path:
        raise ValueError("audio_path is required.")
    model_size = str(data.get("model_size", "small")).strip().lower()
    if model_size not in {"tiny", "base", "small", "medium", "large-v3"}:
        raise ValueError("model_size must be tiny, base, small, medium, or large-v3.")
    device = str(data.get("device", "cpu")).strip().lower()
    if device not in {"cpu", "cuda"}:
        raise ValueError("device must be cpu or cuda.")
    compute_type = str(data.get("compute_type", "int8")).strip().lower()
    if compute_type not in {"int8", "float16", "float32", "int8_float16"}:
        raise ValueError("Unsupported Whisper compute_type.")
    language = data.get("language")
    if language is not None and (not isinstance(language, str) or len(language) > 16):
        raise ValueError("language must be a short language code or omitted.")
    from realtime.whisper_transcriber import WhisperTranscriber
    transcriber = WhisperTranscriber(model_size=model_size, device=device, compute_type=compute_type)
    return transcriber.transcribe(Path(audio_path), language=language)


def listen_for_wake_word(payload=None):
    """Listen for a finite, user-requested interval; never runs as a background daemon."""
    data = payload or {}
    timeout_seconds = data.get("timeout_seconds", 30)
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 120:
        raise ValueError("timeout_seconds must be an integer from 1 to 120.")
    threshold = data.get("threshold", 0.65)
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0.0 < float(threshold) < 1.0:
        raise ValueError("threshold must be between 0 and 1.")
    model_paths = data.get("model_paths")
    if model_paths is not None and (
        not isinstance(model_paths, list) or not model_paths
        or any(not isinstance(path, str) or not path.strip() for path in model_paths)
    ):
        raise ValueError("model_paths must be a non-empty list of local model paths or omitted.")

    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Install requirements-live.txt to enable microphone wake-word listening.") from exc
    from realtime.wake_word import WakeWordDetector

    detector = WakeWordDetector(model_paths=model_paths, threshold=float(threshold))
    block_samples = 1280  # 80 ms at 16 kHz, mono PCM16.
    stream = sd.RawInputStream(
        samplerate=16000, blocksize=block_samples, channels=1, dtype="int16"
    )
    deadline = time.monotonic() + timeout_seconds
    stream.start()
    try:
        while time.monotonic() < deadline:
            audio, overflowed = stream.read(block_samples)
            if overflowed:
                continue
            matches = detector.process_pcm16(bytes(audio))
            if matches:
                return {"detected": True, "models": matches, "listened_seconds_max": timeout_seconds}
        return {"detected": False, "timed_out": True, "listened_seconds_max": timeout_seconds}
    finally:
        stream.stop()
        stream.close()


def register_audio_skills(registry):
    registry.register("transcribe_audio", transcribe_audio)
    registry.register("listen_for_wake_word", listen_for_wake_word)
