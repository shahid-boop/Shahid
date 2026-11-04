"""Guarded desktop automation primitives. Every action requires explicit confirmation."""
from __future__ import annotations
import sys

def _pyautogui():
    try: import pyautogui
    except ImportError as exc: raise RuntimeError("Install requirements-live.txt for desktop automation.") from exc
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.15
    return pyautogui

def screenshot(output: str, confirm: bool = False) -> dict:
    if not confirm: raise PermissionError("Explicit confirmation required for screen capture.")
    p = _pyautogui(); p.screenshot().save(output)
    return {"saved": output}

def click(x: int, y: int, confirm: bool = False) -> dict:
    if not confirm: raise PermissionError("Explicit confirmation required before clicking.")
    p = _pyautogui(); width, height = p.size()
    if not (0 <= x < width and 0 <= y < height): raise ValueError("Coordinates outside screen.")
    p.click(x, y)
    return {"clicked": [x, y]}

def type_text(text: str, confirm: bool = False) -> dict:
    if not confirm: raise PermissionError("Explicit confirmation required before typing.")
    if not isinstance(text, str) or len(text) > 1000: raise ValueError("Text must be at most 1000 characters.")
    _pyautogui().write(text, interval=0.01)
    return {"characters_typed": len(text)}
