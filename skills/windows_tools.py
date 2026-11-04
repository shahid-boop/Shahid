"""Small, explicit Windows utilities. No shell command or arbitrary code execution."""
from __future__ import annotations
import platform
import webbrowser
from urllib.parse import urlparse

ALLOWED_APPS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "explorer": ["explorer.exe"],
}

def system_info(_: dict | None = None) -> dict:
    return {"os": platform.platform(), "python": platform.python_version(), "machine": platform.machine()}

def launch_app(payload: dict | None = None) -> dict:
    import subprocess
    name = str((payload or {}).get("name", "")).strip().lower()
    command = ALLOWED_APPS.get(name)
    if not command:
        raise ValueError(f"App is not allowlisted. Choose one of: {', '.join(sorted(ALLOWED_APPS))}")
    try:
        subprocess.Popen(command, shell=False)
    except OSError as exc:
        raise RuntimeError(f"Could not launch {name}: {exc}") from exc
    return {"launched": name}

def open_website(payload: dict | None = None) -> dict:
    url = str((payload or {}).get("url", "")).strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Provide a valid http:// or https:// website URL.")
    webbrowser.open(url, new=2)
    return {"opened": url}

def register_windows_skills(registry) -> None:
    registry.register("system_info", system_info)
    registry.register("launch_app", launch_app)
    registry.register("open_website", open_website)
