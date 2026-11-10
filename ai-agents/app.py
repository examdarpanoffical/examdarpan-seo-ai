"""Local web dashboard for five Exam Darpan agent MVPs; Python stdlib only."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from agents import supervisor_workflow

ROOT = Path(__file__).resolve().parent


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if urlparse(self.path).path not in ("/", "/index.html"):
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        self._send(200, (ROOT / "dashboard.html").read_bytes())

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/run":
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 200_000:
                raise ValueError("Request must be between 1 byte and 200 KB")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            topic = str(payload.get("topic", "")).strip()[:200]
            official_url = str(payload.get("official_url", "")).strip()[:2000]
            source_notes = str(payload.get("source_notes", "")).strip()[:100_000]
            if not topic:
                raise ValueError("कृपया भर्ती या article का विषय लिखें।")
            result = supervisor_workflow(topic, official_url, source_notes)
            self._send(200, json.dumps(result, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send(400, json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def log_message(self, format: str, *args: object) -> None:
        print("[dashboard] " + (format % args))


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Exam Darpan AI Agents dashboard: http://127.0.0.1:8765")
    print("Local only. No automatic publishing or live source verification.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping dashboard...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
