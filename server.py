"""Local-only dashboard API and lightweight browser dashboard."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

DASHBOARD_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shahid Assistant</title>
<style>
body{font:16px system-ui;max-width:850px;margin:40px auto;padding:0 18px;background:#111827;color:#f9fafb}
header{display:flex;justify-content:space-between;align-items:center;gap:12px}small{color:#9ca3af}
#status{padding:12px;background:#1f2937;border-radius:10px;margin:18px 0;white-space:pre-wrap}
#chat{height:50vh;overflow:auto;background:#1f2937;padding:14px;border-radius:10px}
.msg{padding:10px;margin:8px 0;border-radius:8px;background:#374151;white-space:pre-wrap}
form{display:flex;gap:8px;margin-top:12px}input{flex:1;padding:12px;border-radius:8px;border:0}
button{padding:12px 18px;border:0;border-radius:8px;cursor:pointer}
</style></head><body>
<header><div><h1>Shahid Assistant</h1><small>Local dashboard · localhost only</small></div><button onclick="refresh()">Refresh status</button></header>
<div id="status">Loading status…</div><div id="chat" aria-live="polite"></div>
<form id="form"><input id="message" autocomplete="off" placeholder="Write a message…" required><button>Send</button></form>
<script>
const statusBox=document.getElementById('status'),chat=document.getElementById('chat');
async function refresh(){try{const r=await fetch('/api/status');statusBox.textContent=JSON.stringify(await r.json(),null,2)}catch(e){statusBox.textContent='Status unavailable'}}
function add(role,text){const el=document.createElement('div');el.className='msg';el.textContent=role+': '+text;chat.appendChild(el);chat.scrollTop=chat.scrollHeight}
document.getElementById('form').addEventListener('submit',async e=>{e.preventDefault();const input=document.getElementById('message'),message=input.value.trim();if(!message)return;input.value='';add('You',message);try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});const data=await r.json();add('Assistant',data.reply||data.error||'No response')}catch(err){add('Error','Dashboard request failed')}});
refresh();
</script></body></html>"""


def make_handler(status_provider: Callable[[], dict], chat_handler: Callable[[str], str]):
    class DashboardHandler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/":
                body = DASHBOARD_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path != "/api/status":
                self._send(404, {"error": "not_found"})
                return
            self._send(200, status_provider())

        def do_POST(self) -> None:
            if self.path != "/api/chat":
                self._send(404, {"error": "not_found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 32_768:
                    self._send(400, {"error": "invalid_request_size"})
                    return
                payload = json.loads(self.rfile.read(length))
                message = payload.get("message", "") if isinstance(payload, dict) else ""
                if not isinstance(message, str) or not message.strip():
                    self._send(400, {"error": "message_required"})
                    return
                self._send(200, {"reply": chat_handler(message.strip())})
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send(400, {"error": "invalid_json"})
            except Exception:
                self._send(500, {"error": "assistant_error"})

        def log_message(self, format: str, *args) -> None:
            return

    return DashboardHandler


def serve(status_provider: Callable[[], dict], chat_handler: Callable[[str], str],
          host: str = "127.0.0.1", port: int = 8765) -> None:
    """Serve the dashboard API on loopback only by default."""
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("Dashboard must bind to localhost unless remote access is secured.")
    server = ThreadingHTTPServer((host, port), make_handler(status_provider, chat_handler))
    print(f"Dashboard available at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
