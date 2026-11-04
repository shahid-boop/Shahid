"""Narrow, user-scoped Windows preference controls with explicit allowlisting."""
from __future__ import annotations
import sys

_ALLOWED = {
 "show_file_extensions": (r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "HideFileExt", 0, 1),
 "show_hidden_files": (r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "Hidden", 1, 2),
 "dark_app_mode": (r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "AppsUseLightTheme", 0, 1),
}

def list_settings() -> dict:
    return {"available": sorted(_ALLOWED), "scope": "HKCU only", "requires_admin": False}

def set_setting(name: str, enabled: bool, confirm: bool = False) -> dict:
    if sys.platform != "win32": raise OSError("Windows settings are available only on Windows.")
    if name not in _ALLOWED: raise ValueError("Setting is not allowlisted.")
    if not confirm: raise PermissionError("Pass confirm=True after user approval.")
    import winreg
    key_path, value_name, on_value, off_value = _ALLOWED[name]
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, on_value if enabled else off_value)
    return {"setting": name, "enabled": bool(enabled), "restart_explorer_may_be_required": True}
