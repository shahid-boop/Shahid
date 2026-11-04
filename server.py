"""Local dashboard. Binds to loopback only and never serves configuration secrets."""
from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from config_manager import Settings
from engine_pipeline import ChatEngine, ProviderError
from memory_manager import MemoryManager

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shahid Assistant</title><style>
:root{color-scheme:dark;font:16px system-ui;background:#0b1020;color:#edf2ff}body{max-width:850px;margin:0 auto;padding:24px}
header{display:flex;align-items:center;gap:14px}.orb{width:48px;height:48px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#c7f5ff,#3986ff 45%,#20245e);box-shadow:0 0 30px #3986ff88}
h1{font-size:1.35rem;margin:0}p{color:#aab7d3}.panel{background:#131b30;border:1px solid #293654;border-radius:16px;padding:18px;margin-top:20px}
#log{min-height:180px;max-height:50vh;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere}.msg{padding:12px;border-radius:10px;margin:8px 0;background:#1c2944}.user{border-left:3px solid #66c9ff}.assistant{border-left:3px solid #9a8cff}
textarea{width:100%;box-sizing:border-box;resize:vertical;min-height:90px;background:#0b1020;color:inherit;border:1px solid #344363;border-radius:10px;padding:12px;font:inherit}
button{background:#6dc8ff;color:#07101e;border:0;border-radius:10px;padding:11px 18px;font-weight:700;cursor:pointer}button:disabled{opacity:.5}#status{font-size:.9rem;color:#aab7d3}
</style></head><body><header><div class="orb"></div><div><h1>Shahid Assistant</h1><p>Local Windows assistant · browser dashboard</p></div></header>
<section class="panel"><div id="log" aria-live="polite">Ready. Add your provider API key to .env to enable AI chat.</div><p id="status">Connected to localhost</p>
<form id="form"><textarea id="prompt" maxlength="12000" placeholder="Type your message..." required></textarea><p><button id="send" type="submit">Send message</button></p></form></section>
<script>
const log=document.querySelector('#log'),form=document.querySelector('#form'),promptBox=document.querySelector('#prompt'),send=document.querySelector('#send'),statusBox=document.querySelector('#status');
function add(role,text){const d=document.createElement('div');d.className='msg '+role;d.textContent=(role==='user'?'You: ':'Shahid Assistant: ')+text;log.appendChild(d);log.scrollTop=log.scrollHeight}
form.addEventListener('submit',async e=>{e.preventDefault();const message=promptBox.value.trim();if(!message)return;add('user',message);promptBox.value='';send.disabled=true;statusBox.textContent='Thinking…';try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});const data=await r.json();if(!r.ok)throw new Error(data.error||'Request failed');add('assistant',data.reply);statusBox.textContent='Ready'}catch(err){add('assistant','Error: '+err.message);statusBox.textContent='Request failed'}finally{send.disabled=false;promptBox.focus()}});
</script></body></html>"""

class DashboardHandler(BaseHTTPRequestHandler):
    engine: ChatEngine
    memory: MemoryManager

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")
        elif path == "/api/health":
            self._send(200, b'{"ok":true,"service":"shahid-assistant"}', "application/json")
        else:
            self._send(404, b'{"error":"not found"}', "application/json")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/chat":
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 16000:
                raise ValueError("Request must be between 1 and 16000 bytes.")
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            message = data.get("message") if isinstance(data, dict) else None
            if not isinstance(message, str) or not message.strip() or len(message) > 12000:
                raise ValueError("message must be a non-empty string up to 12000 characters.")
            self.memory.append("user", message)
            history = [{"role":"system","content":"You are Shahid Assistant, a helpful Windows desktop assistant. Be accurate and clearly state limitations."}]
            history.extend(self.memory.get_messages())
            reply = self.engine.chat(history)
            self.memory.append("assistant", reply)
            self._send(200, json.dumps({"reply":reply}, ensure_ascii=False).encode(), "application/json; charset=utf-8")
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send(400, json.dumps({"error":str(exc)}).encode(), "application/json; charset=utf-8")
        except ProviderError as exc:
            self._send(502, json.dumps({"error":str(exc)}).encode(), "application/json; charset=utf-8")
        except Exception:
            self._send(500, b'{"error":"Internal server error"}', "application/json")

    def log_message(self, fmt: str, *args: object) -> None:
        # Keep local terminal output useful without logging request bodies.
        print(f"[dashboard] {self.address_string()} - {fmt % args}")

def serve(settings: Settings | None = None) -> None:
    settings = settings or Settings.load()
    if settings.host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Dashboard must bind to loopback only.")
    handler = type("ConfiguredDashboardHandler", (DashboardHandler,), {
        "engine": ChatEngine(settings), "memory": MemoryManager()
    })
    server = ThreadingHTTPServer((settings.host, settings.port), handler)
    print(f"Shahid Assistant dashboard: http://{settings.host}:{settings.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard…")
    finally:
        server.server_close()
