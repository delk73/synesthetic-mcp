import contextlib
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from mcp.validate import MAX_BYTES


_MINIMAL_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "schema": {"type": "string", "const": "asset"},
    },
    "required": ["schema"],
    "additionalProperties": True,
}


def _wait_for_line(stream, proc, needle: str, timeout: float = 10.0) -> str:
    deadline = time.time() + timeout
    lines = []
    while time.time() < deadline:
        line = stream.readline()
        if not line:
            if proc.poll() is not None:
                break
            time.sleep(0.05)
            continue
        text = line.strip()
        lines.append(text)
        if needle in text:
            return text
    raise AssertionError(f"did not observe '{needle}' in output: {lines}")


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-domain sockets not supported on Windows")
def test_socket_transport_end_to_end(tmp_path):
    socket_path = tmp_path / "mcp.sock"
    ready_file = tmp_path / "mcp.ready"
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    (schemas_dir / "asset.schema.json").write_text(json.dumps(_MINIMAL_SCHEMA))

    probe_path = tmp_path / "probe.sock"
    probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        probe.bind(str(probe_path))
    except PermissionError as exc:
        probe.close()
        pytest.skip(f"unix-domain sockets unavailable: {exc}")
    else:
        probe.close()
        with contextlib.suppress(FileNotFoundError):
            probe_path.unlink()

    env = os.environ.copy()
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "PYTHONPATH": env.get("PYTHONPATH", "") or str(Path.cwd()),
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "MCP_ENDPOINT": "socket",
            "MCP_SOCKET_PATH": str(socket_path),
            "MCP_READY_FILE": str(ready_file),
        }
    )

    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        assert proc.stderr is not None
        ready_line = _wait_for_line(proc.stderr, proc, "mcp:ready")
        assert "mode=socket" in ready_line
        assert socket_path.exists()

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(str(socket_path))
            reader = client.makefile("r", encoding="utf-8")
            writer = client.makefile("w", encoding="utf-8")

            request = {"jsonrpc": "2.0", "id": 1, "method": "list_schemas", "params": {}}
            writer.write(json.dumps(request) + "\n")
            writer.flush()
            response = json.loads(reader.readline())
            assert response["id"] == 1
            assert response["result"]["ok"] is True

            malformed = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "get_schema",
                "params": "not-a-dict",
            }
            writer.write(json.dumps(malformed) + "\n")
            writer.flush()
            error_frame = json.loads(reader.readline())
            assert error_frame["id"] == 2
            assert error_frame.get("error", {}).get("code") == -32603

            oversized = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "list_schemas",
                "params": {"blob": "x" * (MAX_BYTES + 1)},
            }
            writer.write(json.dumps(oversized) + "\n")
            writer.flush()
            large_frame = json.loads(reader.readline())
            assert large_frame.get("id") is None
            result = large_frame.get("result", {})
            assert result.get("reason") == "validation_failed"
            assert any(err.get("msg") == "payload_too_large" for err in result.get("errors", []))

            reader.close()
            writer.close()

        proc.send_signal(signal.SIGINT)
        shutdown_line = _wait_for_line(proc.stderr, proc, "mcp:shutdown")
        assert "mode=socket" in shutdown_line
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
        with contextlib.suppress(FileNotFoundError):
            if ready_file.exists():
                ready_file.unlink()

    assert proc.returncode == 0
    assert not socket_path.exists()
    assert not ready_file.exists()
