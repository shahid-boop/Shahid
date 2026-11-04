"""Local-only HTTP dashboard API for the assistant."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable


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
    print(f"Dashboard API listening at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
