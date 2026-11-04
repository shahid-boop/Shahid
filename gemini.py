"""Google Gemini text API adapter using the standard library.

This is the text-generation adapter. It does not claim to implement Gemini Live audio.
"""
from __future__ import annotations
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from config_manager import Settings

class GeminiError(RuntimeError):
    pass

class GeminiEngine:
    def __init__(self, settings: Settings, model: str = "gemini-2.5-flash"):
        self.settings = settings
        self.model = model

    def chat(self, messages: list[dict[str, str]]) -> str:
        key = self.settings.google_api_key
        if not key:
            raise GeminiError("GOOGLE_API_KEY is missing. Add it to your local .env file.")
        contents = []
        system_parts = []
        for item in messages:
            role = item.get("role", "user")
            content = str(item.get("content", ""))
            if role == "system":
                system_parts.append(content)
            elif role in {"user", "assistant"} and content:
                contents.append({"role": "model" if role == "assistant" else "user",
                                 "parts": [{"text": content}]})
        if not contents:
            raise GeminiError("No user messages were supplied.")
        body = {"contents": contents, "generationConfig": {"temperature": 0.7}}
        if system_parts:
            body["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={key}"
        req = Request(url, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"}, method="POST")
        try:
            with urlopen(req, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read(1000).decode("utf-8", errors="replace")
            raise GeminiError(f"Gemini HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise GeminiError(f"Gemini connection failed: {exc}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GeminiError("Gemini returned invalid JSON.") from exc
        try:
            answer = "".join(part.get("text", "") for part in data["candidates"][0]["content"]["parts"])
        except (KeyError, IndexError, TypeError) as exc:
            raise GeminiError("Gemini response contained no text candidate.") from exc
        if not answer.strip():
            raise GeminiError("Gemini returned an empty response.")
        return answer.strip()
