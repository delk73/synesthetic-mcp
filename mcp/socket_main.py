from __future__ import annotations

import contextlib
import os
import socket
from pathlib import Path
from typing import Any, Callable, Dict

from .transport import build_error_frame, payload_too_large_frame, process_line
from .validate import MAX_BYTES

Handler = Callable[[str, Dict[str, Any]], Dict[str, Any]]


class SocketServer:
    """Blocking Unix-domain socket server for MCP JSON-RPC requests."""

    def __init__(self, path: Path, mode: int) -> None:
        self._path = Path(path)
        self._mode = mode
        self._server: socket.socket | None = None

    def start(self) -> None:
        if self._server is not None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(FileNotFoundError):
            self._path.unlink()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(self._path))
        os.chmod(str(self._path), self._mode)
        server.listen(1)
        self._server = server

    def close(self) -> None:
        server = self._server
        if server is None:
            return
        try:
            server.close()
        finally:
            self._server = None
            with contextlib.suppress(FileNotFoundError):
                self._path.unlink()

    def serve_forever(self, handler: Handler) -> None:
        if self._server is None:
            self.start()
        assert self._server is not None
        server = self._server
        try:
            while True:
                conn, _ = server.accept()
                try:
                    _serve_connection(conn, handler)
                finally:
                    conn.close()
        finally:
            self.close()


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
            except BrokenPipeError:  # pragma: no cover - client disappeared mid-send
                return
