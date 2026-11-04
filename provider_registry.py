"""Provider registry and environment-backed OpenAI-compatible adapter."""
from __future__ import annotations

import os
from typing import Any

from engine_pipeline import EnginePipeline, EngineProvider


class OpenAICompatibleProvider(EngineProvider):
    name = "openai_compatible"

    def __init__(self, api_key: str | None = None, base_url: str | None = None,
                 model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.model = model or os.getenv("OPENAI_MODEL", "")

    def generate(self, prompt: str, **options: Any) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        if not self.model:
            raise RuntimeError("OPENAI_MODEL is not configured.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from exc

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **options,
        )
        content = response.choices[0].message.content
        return content or ""


def build_engine_pipeline(config: dict[str, Any]) -> EnginePipeline:
    pipeline = EnginePipeline()
    if config.get("engine") == "openai_compatible":
        pipeline.register(OpenAICompatibleProvider(
            base_url=config.get("base_url") or None,
            model=config.get("model") or None,
        ))
    return pipeline
