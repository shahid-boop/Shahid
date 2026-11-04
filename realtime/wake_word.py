"""Optional openWakeWord detector; audio capture is supplied by the caller."""
from __future__ import annotations
class WakeWordUnavailable(RuntimeError): pass

class WakeWordDetector:
    def __init__(self, model_paths=None, threshold: float = 0.65):
        if not 0.0 < threshold < 1.0: raise ValueError("threshold must be between 0 and 1")
        try: from openwakeword.model import Model
        except ImportError as exc: raise WakeWordUnavailable("Install requirements-live.txt to enable wake-word detection.") from exc
        self._model = Model(wakeword_models=model_paths, inference_framework="onnx")
        self.threshold = threshold

    def process_pcm16(self, frame: bytes) -> list[str]:
        import numpy as np
        if len(frame) % 2: raise ValueError("PCM16 frame must contain an even number of bytes")
        samples = np.frombuffer(frame, dtype=np.int16)
        predictions = self._model.predict(samples)
        return [name for name, score in predictions.items() if float(score) >= self.threshold]

    def reset(self): self._model.reset()
