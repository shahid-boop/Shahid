"""Explicitly invoked health checks; no background surveillance."""
from __future__ import annotations

from skills.base import Skill
from skills.system_monitor import SystemMonitorSkill


class ProactiveChecksSkill(Skill):
    name = "proactive_checks"
    description = "Run a one-shot system health check when requested."

    def run(self, **arguments):
        stats = SystemMonitorSkill().run()
        warnings = []
        if stats["cpu_percent"] >= 90:
            warnings.append("CPU usage is high.")
        if stats["memory_percent"] >= 90:
            warnings.append("Memory usage is high.")
        if stats["disk_percent"] >= 90:
            warnings.append("System disk is nearly full.")
        return {"stats": stats, "warnings": warnings}
