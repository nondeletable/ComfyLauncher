"""Serves bench.html and collects the result the page posts back."""

from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PAGE = Path(__file__).with_name("bench.html")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class BenchServer:
    """One run's server: hands out the page, waits for one result."""

    def __init__(self, port: int | None = None):
        self.port = port or free_port()
        self.result: dict = {}
        self._done = threading.Event()
        self._srv = ThreadingHTTPServer(("127.0.0.1", self.port), self._handler())
        self._thread = threading.Thread(target=self._srv.serve_forever, daemon=True)

    def _handler(self):
        bench = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass  # the harness prints its own progress

            def do_GET(self):
                body = PAGE.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                size = int(self.headers.get("Content-Length", 0))
                bench.result.update(json.loads(self.rfile.read(size) or b"{}"))
                self.send_response(204)
                self.end_headers()
                bench._done.set()

        return Handler

    def url(self, query: str) -> str:
        return f"http://127.0.0.1:{self.port}/?{query}"

    def __enter__(self) -> "BenchServer":
        self._thread.start()
        return self

    def wait(self, timeout: float) -> dict | None:
        return self.result if self._done.wait(timeout) else None

    def __exit__(self, *exc):
        self._srv.shutdown()
        self._srv.server_close()
