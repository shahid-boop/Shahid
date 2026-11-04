"""Opt-in RSS/Atom watcher with persistent deduplication."""
from __future__ import annotations
import json, re, threading, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

class TopicMonitor:
    def __init__(self, feeds, keywords, callback, interval_seconds=900, state_path="data/topic_monitor_seen.json"):
        if not 60 <= interval_seconds <= 86400: raise ValueError("Polling interval must be 60..86400 seconds")
        if not feeds or len(feeds) > 20: raise ValueError("Provide 1..20 feeds")
        if not keywords or len(keywords) > 100: raise ValueError("Provide 1..100 keywords")
        for url in feeds:
            parsed=urllib.parse.urlparse(url)
            if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("Only credential-free HTTPS feeds are allowed")
        self.feeds=list(feeds); self.keywords=[str(k).strip() for k in keywords if str(k).strip()]
        if not self.keywords: raise ValueError("Keywords cannot be blank")
        self.callback=callback; self.interval_seconds=interval_seconds; self.state_path=Path(state_path)
        self._stop=threading.Event(); self._thread=None; self._lock=threading.RLock()
        try:
            state=json.loads(self.state_path.read_text(encoding="utf-8")); self._seen=set(state if isinstance(state,list) else [])
        except (OSError,json.JSONDecodeError): self._seen=set()
    def _save(self):
        self.state_path.parent.mkdir(parents=True,exist_ok=True); tmp=self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(sorted(self._seen)[-5000:]),encoding="utf-8"); tmp.replace(self.state_path)
    def check_once(self):
        found=[]
        with self._lock:
            for url in self.feeds:
                req=urllib.request.Request(url,headers={"User-Agent":"ShahidAssistant/1.0"})
                with urllib.request.urlopen(req,timeout=15) as response: raw=response.read(2_000_001)
                if len(raw)>2_000_000: raise ValueError("Feed exceeds 2 MB")
                root=ET.fromstring(raw)
                for item in root.findall(".//item")+root.findall(".//{http://www.w3.org/2005/Atom}entry"):
                    title=(item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
                    link=item.findtext("link") or ""
                    if not link:
                        node=item.find("{http://www.w3.org/2005/Atom}link")
                        if node is not None: link=node.attrib.get("href","")
                    key=link or title; hay=(title+" "+link).casefold()
                    matched=any(re.search(r"(?<!\\w)"+re.escape(k.casefold())+r"(?!\\w)",hay) for k in self.keywords)
                    if key and key not in self._seen and matched: self._seen.add(key); found.append({"title":title,"url":link,"feed":url})
            if found: self._save()
        for item in found:
            try: self.callback(item)
            except Exception: pass
        return found
    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._stop.clear()
        def worker():
            while not self._stop.is_set():
                try: self.check_once()
                except Exception: pass
                self._stop.wait(self.interval_seconds)
        self._thread=threading.Thread(target=worker,name="shahid-topic-monitor",daemon=True); self._thread.start()
    def stop(self):
        self._stop.set()
        if self._thread: self._thread.join(timeout=5)
        self._thread=None
