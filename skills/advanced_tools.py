"""Opt-in, allowlisted adapters for advanced diagram modules."""
from __future__ import annotations

def register_advanced_skills(registry, workspace="workspace"):
    def capture_screen(p):
        from vision.capture import capture_screen as fn
        if p.get("confirm") is not True: raise PermissionError("Set confirm=true after explicit approval.")
        return {"saved":fn(p.get("output","workspace/screen.png"),int(p.get("monitor",1)))}
    def capture_camera(p):
        from vision.capture import capture_camera as fn
        if p.get("confirm") is not True: raise PermissionError("Set confirm=true after explicit approval.")
        return {"saved":fn(p.get("output","workspace/camera.jpg"),int(p.get("camera_index",0)))}
    def windows_setting(p):
        from windows.settings import set_setting
        return set_setting(str(p.get("name","")),bool(p.get("enabled")),p.get("confirm") is True)
    def desktop_click(p):
        from automation.desktop import click
        return click(int(p.get("x",-1)),int(p.get("y",-1)),p.get("confirm") is True)
    def desktop_type(p):
        from automation.desktop import type_text
        return type_text(str(p.get("text","")),p.get("confirm") is True)
    registry.register("capture_screen",capture_screen)
    registry.register("capture_camera",capture_camera)
    registry.register("set_windows_preference",windows_setting)
    registry.register("desktop_click",desktop_click)
    registry.register("desktop_type",desktop_type)
