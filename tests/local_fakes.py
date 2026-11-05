"""Ephemeral loopback HTTP server that simulates LM Studio and ComfyUI in tests."""

from __future__ import annotations

import json
import socket
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@dataclass
class Route:
    status: int = 200
    body: bytes = b"{}"
    headers: dict[str, str] = field(default_factory=dict)
    delay: float = 0.0
    omit_length: bool = False


def json_route(data: object, status: int = 200) -> Route:
    return Route(status=status, body=json.dumps(data).encode("utf-8"))


MODELS = {"object": "list", "data": [{"id": "qwen/qwen3-4b", "object": "model"}]}
SYSTEM_STATS = {"system": {"os": "nt"}, "devices": []}
CHAT = {
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "Hola desde el modelo"}}],
    "usage": {"prompt_tokens": 7, "completion_tokens": 4, "total_tokens": 11},
}


class FakeServer:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], Route] = {}
        self.requests: list[tuple[str, str, bytes]] = []
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                fake._handle(self, "GET", b"")

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                fake._handle(self, "POST", self.rfile.read(length))

            def log_message(self, format: str, *args: object) -> None:
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def __enter__(self) -> FakeServer:
        self.thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()

    def _handle(self, handler: BaseHTTPRequestHandler, method: str, body: bytes) -> None:
        self.requests.append((method, handler.path, body))
        route = self.routes.get((method, handler.path), Route(status=404, body=b"no"))
        if route.delay:
            time.sleep(route.delay)
        try:
            handler.send_response(route.status)
            for key, value in route.headers.items():
                handler.send_header(key, value)
            if not route.omit_length:
                handler.send_header("Content-Length", str(len(route.body)))
            handler.send_header("Connection", "close")
            handler.end_headers()
            handler.wfile.write(route.body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return


def closed_port_url() -> str:
    """A loopback URL on a port that was just released, so nothing listens there."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    return f"http://127.0.0.1:{port}"
