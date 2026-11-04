"""Opt-in webcam frame source for a HUD preview; caller owns display and lifecycle."""
from __future__ import annotations
import threading, time

class HudVideo:
    def __init__(self, camera_index: int = 0, fps: int = 10, on_frame=None):
        if not 1 <= fps <= 30: raise ValueError("fps must be between 1 and 30")
        self.camera_index, self.interval, self.on_frame = camera_index, 1.0/fps, on_frame
        self._stop=threading.Event(); self._thread=None; self._camera=None
    def start(self):
        try: import cv2
        except ImportError as exc: raise RuntimeError("Install requirements-live.txt for HUD video.") from exc
        if self._thread and self._thread.is_alive(): return
        self._camera=cv2.VideoCapture(self.camera_index)
        if not self._camera.isOpened():
            self._camera.release(); self._camera=None
            raise RuntimeError("Camera could not be opened.")
        self._stop.clear()
        def loop():
            while not self._stop.is_set():
                ok,frame=self._camera.read()
                if ok and self.on_frame: self.on_frame(frame)
                self._stop.wait(self.interval)
        self._thread=threading.Thread(target=loop,name="hud-video",daemon=True); self._thread.start()
    def stop(self):
        self._stop.set()
        if self._thread: self._thread.join(timeout=2)
        if self._camera: self._camera.release(); self._camera=None
