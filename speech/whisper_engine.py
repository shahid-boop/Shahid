"""Optional local Whisper transcription; model downloads occur on first use."""
from __future__ import annotations
class WhisperUnavailable(RuntimeError): pass
class WhisperTranscriber:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        try: from faster_whisper import WhisperModel
        except ImportError as exc: raise WhisperUnavailable("Install faster-whisper from requirements-whisper.txt") from exc
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
    def transcribe(self, audio_path: str, language: str | None = None) -> dict:
        segments, info = self.model.transcribe(audio_path, language=language, vad_filter=True)
        parts = [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
        return {"language": info.language, "language_probability": info.language_probability,
                "text": " ".join(x["text"] for x in parts), "segments": parts}
