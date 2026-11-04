"""Explicit screen/webcam capture helpers; capture is never started automatically."""
from __future__ import annotations
from pathlib import Path
class CaptureUnavailable(RuntimeError): pass

def capture_screen(output: str = "data/captures/screen.png") -> str:
    try: import mss
    except ImportError as exc: raise CaptureUnavailable("Install mss and Pillow from requirements-vision.txt") from exc
    from PIL import Image
    path=Path(output); path.parent.mkdir(parents=True,exist_ok=True)
    with mss.mss() as sct:
        shot=sct.grab(sct.monitors[1]); Image.frombytes("RGB",shot.size,shot.rgb).save(path)
    return str(path)

def capture_camera(output: str = "data/captures/camera.jpg", camera_index: int = 0) -> str:
    try: import cv2
    except ImportError as exc: raise CaptureUnavailable("Install opencv-python from requirements-vision.txt") from exc
    path=Path(output); path.parent.mkdir(parents=True,exist_ok=True)
    cam=cv2.VideoCapture(camera_index)
    try:
        if not cam.isOpened(): raise CaptureUnavailable("Camera could not be opened.")
        ok, frame=cam.read()
        if not ok: raise CaptureUnavailable("Camera frame could not be read.")
        if not cv2.imwrite(str(path),frame): raise CaptureUnavailable("Could not save camera frame.")
    finally: cam.release()
    return str(path)
