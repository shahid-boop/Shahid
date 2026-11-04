"""Opt-in RSS topic watcher. Polling starts only when explicitly started by the user."""
from __future__ import annotations
import re, threading, time, urllib.request, xml.etree.ElementTree as ET
from dataclasses import dataclass

@dataclass
class TopicMonitor:
    feeds: list[str]
    keywords: list[str]
    callback: object
    interval_seconds: int = 900
    def __post_init__(self):
        if not 60 <= self.interval_seconds <= 86400: raise ValueError("Polling interval must be 60..86400 seconds")
        if not self.feeds or len(self.feeds) > 20: raise ValueError("Provide 1..20 RSS/Atom feeds")
        if not self.keywords: raise ValueError("At least one keyword is required")
        for url in self.feeds:
            if not url.startswith("https://"): raise ValueError("Only HTTPS feeds are allowed")
        self._stop = threading.Event(); self._thread = None; self._seen = set()
    def check_once(self) -> list[dict]:
        found=[]
        for url in self.feeds:
            req=urllib.request.Request(url, headers={"User-Agent":"ShahidAssistantTopicMonitor/1.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                raw=response.read(2_000_000)
            root=ET.fromstring(raw)
            for item in root.findall(".//item") + root.findall(".//{http://www.w3.org/2005/Atom}entry"):
                title=(item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
                link=item.findtext("link") or ""
                if not link:
                    node=item.find("{http://www.w3.org/2005/Atom}link")
                    if node is not None: link=node.attrib.get("href","")
                key=link or title
                text=(title+" "+link).lower()
                if key and key not in self._seen and any(re.search(r"(?<!\w)"+re.escape(k.lower())+r"(?!\w)",text) for k in self.keywords):
                    self._seen.add(key); found.append({"title":title,"url":link,"feed":url})
        for item in found: self.callback(item)
        return found
    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._stop.clear()
        def run():
            while not self._stop.is_set():
                try: self.check_once()
                except Exception: pass
                self._stop.wait(self.interval_seconds)
        self._thread=threading.Thread(target=run,name="topic-monitor",daemon=True); self._thread.start()
    def stop(self):
        self._stop.set()
        if self._thread: self._thread.join(timeout=3)
