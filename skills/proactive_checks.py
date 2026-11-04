"""Explicit health checks; no hidden background activity."""
from datetime import datetime, timezone
from pathlib import Path
def run_checks(_=None):
    checks=[{"name":n+"_directory","ok":Path(n).is_dir()} for n in ("data","workspace")]
    checks.append({"name":"utc_clock","ok":True,"value":datetime.now(timezone.utc).isoformat()})
    return {"checks":checks,"ok":all(x["ok"] for x in checks)}
def register_proactive_skills(registry): registry.register("run_checks",run_checks)
