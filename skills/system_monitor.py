"""Read-only Windows system health skill."""
from __future__ import annotations

import platform
from skills.base import Skill


class SystemMonitorSkill(Skill):
    name = "system_monitor"
    description = "Read basic CPU, memory, disk and OS information."

    def run(self, **arguments):
        if platform.system() != "Windows":
            raise OSError("This skill is currently implemented for Windows.")
        try:
            import psutil
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt to use system monitoring.") from exc
        return {
            "os": platform.platform(),
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("C:\\").percent,
        }
