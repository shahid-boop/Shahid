"""Explicit still-photo capture from a selected camera device."""
from __future__ import annotations

from pathlib import Path
from skills.base import Skill


class CameraCaptureSkill(Skill):
    name = "camera_capture"
    description = "Capture one still image from the webcam after explicit user invocation."

    def run(self, output_path: str = "camera.png", device_index: int = 0, **arguments):
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("Install opencv-python to enable camera capture.") from exc
        workspace = Path("workspace").resolve()
        target = (workspace / output_path).resolve()
        if workspace not in target.parents or target.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise PermissionError("Camera output must be an image inside workspace.")
        target.parent.mkdir(parents=True, exist_ok=True)
        camera = cv2.VideoCapture(int(device_index), cv2.CAP_DSHOW)
        try:
            if not camera.isOpened():
                raise RuntimeError("Could not open the selected camera.")
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("Camera did not return an image.")
            if not cv2.imwrite(str(target), frame):
                raise RuntimeError("Could not save camera image.")
        finally:
            camera.release()
        return {"saved_to": str(target.relative_to(workspace))}
