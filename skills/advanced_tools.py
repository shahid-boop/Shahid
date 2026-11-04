"""Allowlisted optional diagram integrations with explicit user confirmation."""
from __future__ import annotations
_topic_monitor = None

def register_advanced_skills(registry, workspace="workspace"):
    def capture_screen(p):
        from vision.capture import capture_screen as fn
        if p.get("confirm") is not True: raise PermissionError("Set confirm=true after explicit approval")
        output=str(p.get("output","workspace/screen.png"))
        return {"saved":fn(output,int(p.get("monitor",1)))}
    def capture_camera(p):
        from vision.capture import capture_camera as fn
        if p.get("confirm") is not True: raise PermissionError("Set confirm=true after explicit approval")
        return {"saved":fn(str(p.get("output","workspace/camera.jpg")),int(p.get("camera_index",0)))}
    def windows_setting(p):
        from windows.settings import set_setting
        return set_setting(str(p.get("name","")),p.get("enabled") is True,p.get("confirm") is True)
    def settings_list(_):
        from windows.settings import list_settings
        return list_settings()
    def desktop_click(p):
        from automation.desktop import click
        if p.get("confirm") is not True: raise PermissionError("Set confirm=true after explicit approval")
        return click(int(p.get("x",-1)),int(p.get("y",-1)),True)
    def desktop_type(p):
        from automation.desktop import type_text
        if p.get("confirm") is not True: raise PermissionError("Set confirm=true after explicit approval")
        return type_text(str(p.get("text","")),True)
    def desktop_screenshot(p):
        from automation.desktop import screenshot
        if p.get("confirm") is not True: raise PermissionError("Set confirm=true after explicit approval")
        return screenshot(str(p.get("output","workspace/desktop.png")),True)
    def app_lookup(p):
        from desktop.control import app_identity
        return app_identity(p)
    def monitor_start(p):
        global _topic_monitor
        from monitoring.topic_monitor import TopicMonitor
        from monitoring.notifications import notify
        if _topic_monitor is not None: raise RuntimeError("A topic monitor is already running")
        feeds=p.get("feeds"); keywords=p.get("keywords")
        if not isinstance(feeds,list) or not isinstance(keywords,list): raise ValueError("feeds and keywords must be lists")
        _topic_monitor=TopicMonitor(feeds,keywords,lambda item: notify("Shahid Assistant: topic match",item.get("title","New match")),int(p.get("interval_seconds",900)))
        _topic_monitor.start()
        return {"started":True,"feeds":len(feeds),"keywords":len(keywords)}
    def monitor_stop(_):
        global _topic_monitor
        if _topic_monitor is None: return {"stopped":False,"reason":"not_running"}
        _topic_monitor.stop(); _topic_monitor=None
        return {"stopped":True}
    def install_plugin(p):
        from plugins.marketplace import install_archive
        return install_archive(p["archive"],p["destination"],p["sha256"],p["manifest"],p["public_key_hex"])
    handlers={
        "capture_screen":capture_screen,"capture_camera":capture_camera,
        "set_windows_preference":windows_setting,"list_windows_preferences":settings_list,
        "desktop_click":desktop_click,"desktop_type":desktop_type,"desktop_screenshot":desktop_screenshot,
        "lookup_installed_app":app_lookup,"start_topic_monitor":monitor_start,"stop_topic_monitor":monitor_stop,
        "install_signed_plugin":install_plugin,
    }
    for name,handler in handlers.items(): registry.register(name,handler)
