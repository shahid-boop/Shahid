"""Optional local Whisper transcription using faster-whisper."""
from __future__ import annotations
from pathlib import Path

class WhisperUnavailable(RuntimeError): pass

class WhisperTranscriber:
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        try: from faster_whisper import WhisperModel
        except ImportError as exc: raise WhisperUnavailable("Install requirements-live.txt to enable Whisper.") from exc
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str | Path, language: str | None = None) -> dict:
        path = Path(audio_path)
        if not path.is_file(): raise FileNotFoundError(path)
        segments, info = self._model.transcribe(str(path), language=language, vad_filter=True)
        rows = [{"start": float(s.start), "end": float(s.end), "text": s.text.strip()} for s in segments]
        return {"language": info.language, "language_probability": float(info.language_probability),
                "text": " ".join(x["text"] for x in rows), "segments": rows}
