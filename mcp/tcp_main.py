from __future__ import annotations

import contextlib
import socket
import threading
from typing import Any, Callable, Dict, List, Tuple

from .transport import build_error_frame, payload_too_large_frame, process_line
from .validate import MAX_BYTES

Handler = Callable[[str, Dict[str, Any]], Dict[str, Any]]


class TCPServer:
    """Blocking TCP server for MCP JSON-RPC requests over NDJSON."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._requested_port = port
        self._server: socket.socket | None = None
        self._client_threads: List[threading.Thread] = []
        self._lock = threading.Lock()
        self._closing = False

    def start(self) -> Tuple[str, int]:
        if self._server is not None:
            return self.address

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self._host, self._requested_port))
        server.listen(5)
        self._server = server
        return self.address

    @property
    def address(self) -> Tuple[str, int]:
        server = self._server
        if server is None:
            return self._host, self._requested_port
        host, port = server.getsockname()
        return str(host), int(port)

    def close(self) -> None:
        server = self._server
        if server is None:
            return
        self._closing = True
        try:
            server.close()
        finally:
            self._server = None
            for thread in self._drain_threads():
                thread.join(timeout=1.0)

    def serve_forever(self, handler: Handler) -> None:
        if self._server is None:
            self.start()
        assert self._server is not None
        server = self._server
        try:
            while True:
                try:
                    conn, _ = server.accept()
                except OSError:
                    if self._closing:
                        break
                    raise
                thread = threading.Thread(
                    target=self._handle_connection,
                    args=(conn, handler),
                    daemon=True,
                )
                with self._lock:
                    self._client_threads.append(thread)
                thread.start()
        finally:
            self.close()

    def _handle_connection(self, conn: socket.socket, handler: Handler) -> None:
        try:
            _serve_connection(conn, handler)
        finally:
            with contextlib.suppress(Exception):
                conn.shutdown(socket.SHUT_RDWR)
            conn.close()
            with self._lock:
                current = threading.current_thread()
                self._client_threads = [t for t in self._client_threads if t is not current]

    def _drain_threads(self) -> List[threading.Thread]:
        with self._lock:
            threads = list(self._client_threads)
            self._client_threads.clear()
            return threads


def _serve_connection(conn: socket.socket, handler: Handler) -> None:
    buffer = b""
    while True:
        try:
            chunk = conn.recv(4096)
        except InterruptedError:  # pragma: no cover - platform specific
            continue
        if not chunk:
            break
        buffer += chunk
        while b"\n" in buffer:
            raw_line, buffer = buffer.split(b"\n", 1)
            stripped = raw_line.strip()
            if not stripped:
                continue
            if len(stripped) > MAX_BYTES:
                frame = payload_too_large_frame(None)
            else:
                try:
                    line = stripped.decode("utf-8")
                except UnicodeDecodeError as exc:
                    frame = build_error_frame(None, f"decode_error: {exc}")
                else:
                    frame = process_line(line, handler)
            payload = (frame + "\n").encode("utf-8")
            try:
                conn.sendall(payload)
            except BrokenPipeError:  # pragma: no cover - client vanished mid-send
                return

