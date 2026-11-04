"""Configuration loading for Shahid Assistant (Windows 11 / Python 3.11+)."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def _load_env_file(path: Path = ROOT / ".env") -> None:
    """Load simple KEY=VALUE lines without overriding existing environment variables."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key.replace("_", "").isalnum():
            os.environ.setdefault(key, value)

@dataclass(frozen=True)
class Settings:
    provider: str = "openai"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    google_api_key: str = ""
    host: str = "127.0.0.1"
    port: int = 8765

    @classmethod
    def load(cls) -> "Settings":
        _load_env_file()
        try:
            port = int(os.getenv("APP_PORT", "8765"))
        except ValueError:
            port = 8765
        # The dashboard is deliberately loopback-only; don't allow accidental LAN exposure.
        host = os.getenv("APP_HOST", "127.0.0.1").strip()
        if host not in {"127.0.0.1", "localhost", "::1"}:
            host = "127.0.0.1"
        return cls(
            provider=os.getenv("AI_PROVIDER", "openai").strip().lower(),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            host=host,
            port=max(1024, min(port, 65535)),
        )
