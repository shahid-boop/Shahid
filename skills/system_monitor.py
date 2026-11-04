"""Read-only system monitoring using Python's standard library."""
from __future__ import annotations
import os, shutil, platform
from pathlib import Path

def system_status(_: dict | None = None) -> dict:
    disk = shutil.disk_usage(Path.home())
    return {"platform": platform.platform(), "python": platform.python_version(),
            "cpu_count": os.cpu_count(), "home_disk_total_bytes": disk.total,
            "home_disk_free_bytes": disk.free}

def register_monitoring_skill(registry):
    registry.register("system_status", system_status)
