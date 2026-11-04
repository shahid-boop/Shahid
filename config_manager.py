"""Load and persist local assistant configuration.

Secrets should be supplied through environment variables, not stored here.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path("data/config.json")

DEFAULT_CONFIG: dict[str, Any] = {
    "assistant_name": "Shahid Assistant",
    "engine": "openai_compatible",
    "model": "",
    "base_url": "",
    "voice_enabled": False,
    "always_on_top": True,
    "gemini_live_model": "gemini-live-2.5-flash-preview",
}


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Return saved settings merged over safe defaults."""
    if not path.exists():
        return DEFAULT_CONFIG.copy()

    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read configuration at {path}: {exc}") from exc

    if not isinstance(saved, dict):
        raise ValueError("Configuration must be a JSON object.")

    return {**DEFAULT_CONFIG, **saved}


def save_config(config: dict[str, Any], path: Path = CONFIG_PATH) -> None:
    """Persist non-secret settings as formatted JSON."""
    if not isinstance(config, dict):
        raise TypeError("config must be a dictionary")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
