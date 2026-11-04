"""Optional local wake-word detector using openWakeWord."""
from __future__ import annotations
class WakeWordUnavailable(RuntimeError): pass
class WakeWordDetector:
    def __init__(self, model_path: str | None = None, threshold: float = 0.6):
        try:
            from openwakeword.model import Model
        except ImportError as exc: raise WakeWordUnavailable("Install openwakeword from requirements-wakeword.txt") from exc
        self.model = Model(wakeword_models=[model_path] if model_path else ["hey_jarvis"], inference_framework="onnx")
        self.threshold = threshold
    def predict(self, pcm16_frame):
        scores = self.model.predict(pcm16_frame)
        return {name: float(score) for name, score in scores.items() if float(score) >= self.threshold}
