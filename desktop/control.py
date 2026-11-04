"""Guarded desktop actions. All actions require explicit caller invocation."""
from __future__ import annotations
import os, platform, subprocess
from urllib.parse import quote

def windows_settings(payload: dict | None = None) -> dict:
    if platform.system() != "Windows": raise RuntimeError("Windows settings are available only on Windows.")
    page=str((payload or {}).get("page","")).strip().lower()
    allowed={"display":"ms-settings:display","sound":"ms-settings:sound","bluetooth":"ms-settings:bluetooth",
             "wifi":"ms-settings:network-wifi","windows_update":"ms-settings:windowsupdate","privacy":"ms-settings:privacy"}
    if page not in allowed: raise ValueError(f"Allowed settings pages: {', '.join(sorted(allowed))}")
    os.startfile(allowed[page])
    return {"opened":page}

def app_identity(payload: dict | None = None) -> dict:
    if platform.system() != "Windows": raise RuntimeError("App identity lookup is Windows-only.")
    name=str((payload or {}).get("name","")).strip()
    if not name or len(name)>100: raise ValueError("Provide an app name up to 100 characters.")
    # Registry enumeration is read-only and deliberately limited to uninstall metadata.
    import winreg
    results=[]
    roots=[winreg.HKEY_LOCAL_MACHINE,winreg.HKEY_CURRENT_USER]
    paths=[r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
           r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"]
    for root in roots:
        for sub in paths:
            try: key=winreg.OpenKey(root,sub)
            except OSError: continue
            with key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        child_name=winreg.EnumKey(key,i); child=winreg.OpenKey(key,child_name)
                        with child:
                            display,_=winreg.QueryValueEx(child,"DisplayName")
                            if name.casefold() in str(display).casefold():
                                version=""
                                try: version,_=winreg.QueryValueEx(child,"DisplayVersion")
                                except OSError: pass
                                results.append({"name":display,"version":version})
                    except OSError: continue
    return {"matches":results[:30]}

def click_or_type(payload: dict | None = None) -> dict:
    """Narrow, explicit automation; coordinates and text must be supplied by the caller."""
    try: import pyautogui
    except ImportError as exc: raise RuntimeError("Install pyautogui from requirements-desktop.txt") from exc
    data=payload or {}; action=data.get("action")
    if action=="click":
        x,y=data.get("x"),data.get("y")
        if not all(isinstance(v,int) and 0<=v<=10000 for v in (x,y)): raise ValueError("Click needs integer x/y coordinates.")
        pyautogui.click(x,y); return {"clicked":[x,y]}
    if action=="type":
        value=data.get("text")
        if not isinstance(value,str) or len(value)>2000: raise ValueError("Text must be <= 2000 characters.")
        pyautogui.write(value, interval=0.02); return {"typed_characters":len(value)}
    if action=="hotkey":
        keys=data.get("keys")
        allowed={"ctrl","alt","shift","win","enter","tab","esc","space","up","down","left","right","c","v","x","a","s","f"}
        if not isinstance(keys,list) or not 1<=len(keys)<=4 or any(k not in allowed for k in keys): raise ValueError("Hotkey contains unsupported keys.")
        pyautogui.hotkey(*keys); return {"hotkey":keys}
    raise ValueError("Supported actions: click, type, hotkey")
