"""Persistent task list; records tasks without executing arbitrary commands."""
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
class TaskStore:
    def __init__(self, path="data/tasks.json"): self.path, self.lock = Path(path), RLock()
    def _read(self):
        try:
            data=json.loads(self.path.read_text(encoding="utf-8")); return data if isinstance(data,list) else []
        except (OSError,json.JSONDecodeError): return []
    def add(self,title):
        title=str(title).strip()
        if not title or len(title)>300: raise ValueError("Task title must be 1-300 characters.")
        with self.lock:
            tasks=self._read(); item={"id":max([int(x.get("id",0)) for x in tasks]+[0])+1,"title":title,"status":"pending","created_at":datetime.now(timezone.utc).isoformat()}
            tasks.append(item); self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps(tasks,ensure_ascii=False,indent=2),encoding="utf-8"); return item
    def list(self):
        with self.lock: return self._read()
    def complete(self,task_id):
        with self.lock:
            tasks=self._read()
            for item in tasks:
                if item.get("id")==task_id:
                    item["status"]="completed"; self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps(tasks,ensure_ascii=False,indent=2),encoding="utf-8"); return item
            raise KeyError(f"Task not found: {task_id}")
def register_task_skills(registry,store=None):
    store=store or TaskStore()
    registry.register("task_add",lambda p:store.add((p or {}).get("title","")))
    registry.register("task_list",lambda p:{"tasks":store.list()})
    registry.register("task_complete",lambda p:store.complete(int((p or {}).get("id",0))))
