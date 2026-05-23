from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


STATIC_DIR = Path(__file__).parent / "static"


def serve(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    server = ThreadingHTTPServer((host, port), Handler)
    return server


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = serve(host, port)
    print(f"http://{host}:{port}")
    server.serve_forever()
