"""Provider boundary for OpenAI-compatible and Google Gemini text chat."""
from __future__ import annotations
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from config_manager import Settings
from gemini import GeminiEngine, GeminiError

class ProviderError(RuntimeError):
    pass

class ChatEngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._gemini = GeminiEngine(settings)

    def chat(self, messages: list[dict[str, str]]) -> str:
        provider = self.settings.provider
        if provider == "gemini":
            try:
                return self._gemini.chat(messages[-40:])
            except GeminiError as exc:
                raise ProviderError(str(exc)) from exc
        if provider not in {"openai", "openai-compatible"}:
            raise ProviderError(f"Unknown AI_PROVIDER: {provider}")
        if not self.settings.openai_api_key:
            raise ProviderError("OPENAI_API_KEY is missing. Copy .env.example to .env and add your key.")
        body = json.dumps({"model": self.settings.openai_model, "messages": messages[-40:], "temperature": 0.7}).encode("utf-8")
        request = Request(f"{self.settings.openai_base_url}/chat/completions", data=body,
            headers={"Authorization": f"Bearer {self.settings.openai_api_key}", "Content-Type": "application/json", "Accept": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read(1000).decode("utf-8", errors="replace")
            raise ProviderError(f"Provider returned HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ProviderError(f"Could not reach the AI provider: {exc}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError("Provider returned an invalid response.") from exc
        try:
            answer = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Provider response did not contain a chat message.") from exc
        if not isinstance(answer, str) or not answer.strip():
            raise ProviderError("Provider returned an empty answer.")
        return answer.strip()
