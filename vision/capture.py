"""Explicit opt-in screen/webcam snapshots. No background capture or upload."""
from __future__ import annotations
from pathlib import Path

class CaptureUnavailable(RuntimeError): pass

def capture_screen(output: str | Path, monitor: int = 1) -> str:
    try: import mss
    except ImportError as exc: raise CaptureUnavailable("Install requirements-live.txt for screen capture.") from exc
    target = Path(output); target.parent.mkdir(parents=True, exist_ok=True)
    with mss.mss() as sct:
        monitors = sct.monitors
        if monitor < 1 or monitor >= len(monitors): raise ValueError("Unknown monitor index")
        sct_img = sct.grab(monitors[monitor])
        from mss.tools import to_png
        target.write_bytes(to_png(sct_img.rgb, sct_img.size))
    return str(target)

def capture_camera(output: str | Path, camera_index: int = 0) -> str:
    try: import cv2
    except ImportError as exc: raise CaptureUnavailable("Install requirements-live.txt for camera capture.") from exc
    target = Path(output); target.parent.mkdir(parents=True, exist_ok=True)
    camera = cv2.VideoCapture(camera_index)
    try:
        if not camera.isOpened(): raise CaptureUnavailable("Camera could not be opened.")
        ok, frame = camera.read()
        if not ok: raise CaptureUnavailable("Camera frame could not be read.")
        if not cv2.imwrite(str(target), frame): raise CaptureUnavailable("Could not save camera frame.")
    finally: camera.release()
    return str(target)
