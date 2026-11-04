"""Optional Windows toast notifications for explicit monitoring subscriptions."""
from __future__ import annotations
import sys

def notify(title: str, message: str) -> dict:
    if sys.platform != "win32": raise OSError("Native toast notifications require Windows.")
    try: from winotify import Notification
    except ImportError as exc: raise RuntimeError("Install winotify to enable Windows toast notifications.") from exc
    Notification(app_id="Shahid Assistant", title=title[:100], msg=message[:500]).show()
    return {"sent": True}
