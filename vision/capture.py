"""Explicit screen/webcam capture; never starts automatically."""
from pathlib import Path
class CaptureUnavailable(RuntimeError): pass
def capture_screen(output="data/captures/screen.png", monitor=1):
    if not isinstance(monitor,int) or monitor < 0: raise ValueError("monitor must be non-negative")
    try:
        import mss
        from PIL import Image
    except ImportError as exc: raise CaptureUnavailable("Install mss and Pillow from requirements-live.txt") from exc
    path=Path(output); path.parent.mkdir(parents=True,exist_ok=True)
    with mss.mss() as capture:
        if monitor >= len(capture.monitors): raise ValueError("monitor index is unavailable")
        shot=capture.grab(capture.monitors[monitor]); Image.frombytes("RGB",shot.size,shot.rgb).save(path)
    return str(path)
def capture_camera(output="data/captures/camera.jpg", camera_index=0):
    if not isinstance(camera_index,int) or camera_index < 0: raise ValueError("camera_index must be non-negative")
    try: import cv2
    except ImportError as exc: raise CaptureUnavailable("Install opencv-python from requirements-live.txt") from exc
    path=Path(output); path.parent.mkdir(parents=True,exist_ok=True); camera=cv2.VideoCapture(camera_index)
    try:
        if not camera.isOpened(): raise CaptureUnavailable("Camera could not be opened")
        ok,frame=camera.read()
        if not ok: raise CaptureUnavailable("Camera frame could not be read")
        if not cv2.imwrite(str(path),frame): raise CaptureUnavailable("Could not save camera frame")
    finally: camera.release()
    return str(path)
