"""stdlib HTTP directory server — Stronghold deploy target."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from ami.builtin.neighbors.models import Peer

from .store import DirectoryStore


class DirectoryApp:
    """Routing + auth for /health and /v1/neighbors."""

    def __init__(self, store: DirectoryStore, *, token: Optional[str] = None) -> None:
        self.store = store
        self.token = (token or "").strip() or None

    def _authorized(self, headers: Dict[str, str]) -> bool:
        if not self.token:
            return True
        auth = headers.get("Authorization") or headers.get("authorization") or ""
        if auth.lower().startswith("bearer "):
            return auth[7:].strip() == self.token
        return (headers.get("X-AMI-Token") or "") == self.token

    def handle(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: bytes,
    ) -> Tuple[int, Dict[str, str], bytes]:
        method = method.upper()
        parsed = urlparse(path)
        route = parsed.path.rstrip("/") or "/"

        if route == "/health" and method == "GET":
            return self._json(200, {"ok": True, "service": "ami-neighbors-directory"})

        if not self._authorized(headers):
            return self._json(401, {"ok": False, "error": "unauthorized"})

        if route == "/v1/neighbors" and method == "GET":
            return self._json(200, self.store.snapshot_dict())

        if route == "/v1/neighbors" and method == "POST":
            try:
                payload = json.loads(body.decode("utf-8") or "{}")
            except (UnicodeDecodeError, json.JSONDecodeError):
                return self._json(400, {"ok": False, "error": "invalid json"})
            if not isinstance(payload, dict):
                return self._json(400, {"ok": False, "error": "body must be object"})
            try:
                peer = Peer.from_dict(payload)
            except (KeyError, TypeError, ValueError) as exc:
                return self._json(400, {"ok": False, "error": f"invalid peer: {exc}"})
            saved = self.store.upsert(peer)
            return self._json(200, {"ok": True, "peer": saved.to_dict()})

        if route.startswith("/v1/neighbors/") and method == "DELETE":
            peer_id = route[len("/v1/neighbors/") :].strip()
            if not peer_id:
                return self._json(400, {"ok": False, "error": "peer_id required"})
            removed = self.store.remove(peer_id)
            return self._json(200 if removed else 404, {"ok": removed, "peer_id": peer_id})

        return self._json(404, {"ok": False, "error": "not found"})

    @staticmethod
    def _json(status: int, payload: Dict[str, Any]) -> Tuple[int, Dict[str, str], bytes]:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(data)),
            "Cache-Control": "no-store",
        }
        return status, headers, data


def make_handler(app: DirectoryApp) -> type:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # quiet unit tests
            return

        def _headers_dict(self) -> Dict[str, str]:
            return {k: v for k, v in self.headers.items()}

        def _read_body(self) -> bytes:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0:
                return b""
            return self.rfile.read(length)

        def _dispatch(self, method: str) -> None:
            status, headers, body = app.handle(method, self.path, self._headers_dict(), self._read_body())
            self.send_response(status)
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            if body and method != "HEAD":
                self.wfile.write(body)

        def do_GET(self) -> None:
            self._dispatch("GET")

        def do_POST(self) -> None:
            self._dispatch("POST")

        def do_DELETE(self) -> None:
            self._dispatch("DELETE")

        def do_HEAD(self) -> None:
            self._dispatch("HEAD")

    return Handler


def serve_directory(
    host: str = "127.0.0.1",
    port: int = 4178,
    *,
    store: Optional[DirectoryStore] = None,
    token: Optional[str] = None,
    data_path: Optional[str] = None,
    ttl_seconds: float = 3600.0,
) -> ThreadingHTTPServer:
    st = store or DirectoryStore(Path(data_path) if data_path else None, ttl_seconds=ttl_seconds)
    app = DirectoryApp(st, token=token)
    httpd = ThreadingHTTPServer((host, port), make_handler(app))
    return httpd


def serve_forever_background(
    host: str = "127.0.0.1",
    port: int = 0,
    **kwargs: Any,
) -> Tuple[ThreadingHTTPServer, str]:
    """Start server on a thread; port 0 = ephemeral. Returns (server, base_url)."""
    httpd = serve_directory(host=host, port=port, **kwargs)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    bound_host, bound_port = httpd.server_address[:2]
    base = f"http://{bound_host}:{bound_port}"
    return httpd, base
