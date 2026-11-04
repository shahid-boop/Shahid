"""Optional Windows speech input/output. Install requirements-voice.txt to enable."""
from __future__ import annotations

class SpeechUnavailable(RuntimeError):
    pass

class SpeechEngine:
    def __init__(self, language: str = "ur-PK"):
        self.language = language
        try:
            import speech_recognition as sr
            import pyttsx3
        except ImportError as exc:
            raise SpeechUnavailable("Voice packages missing. Install: pip install -r requirements-voice.txt") from exc
        self._sr = sr
        self._recognizer = sr.Recognizer()
        self._tts = pyttsx3.init()

    def listen(self, timeout: int = 6, phrase_time_limit: int = 15) -> str:
        try:
            with self._sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            return self._recognizer.recognize_google(audio, language=self.language)
        except self._sr.WaitTimeoutError:
            return ""
        except self._sr.UnknownValueError:
            return ""
        except self._sr.RequestError as exc:
            raise SpeechUnavailable(f"Speech recognition service error: {exc}") from exc
        except OSError as exc:
            raise SpeechUnavailable(f"Microphone/audio device unavailable: {exc}") from exc

    def speak(self, text: str) -> None:
        if text.strip():
            self._tts.say(text)
            self._tts.runAndWait()
