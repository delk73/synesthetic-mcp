import contextlib
import json
import os
import stat
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

from mcp.validate import MAX_BYTES


def _assert_iso_timestamp(line: str) -> None:
    token = None
    for part in line.split():
        if part.startswith("timestamp="):
            token = part.split("=", 1)[1]
            break
    assert token, f"timestamp field missing in log: {line}"
    datetime.fromisoformat(token)


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
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()

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
            "SYN_EXAMPLES_DIR": str(examples_dir),
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
        assert "schemas_dir=" in ready_line
        assert "examples_dir=" in ready_line
        assert "timestamp=" in ready_line
        _assert_iso_timestamp(ready_line)
        assert socket_path.exists()
        socket_stat = os.stat(socket_path)
        assert stat.S_ISSOCK(socket_stat.st_mode)
        assert stat.S_IMODE(socket_stat.st_mode) == 0o600

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
            invalid_frame = json.loads(reader.readline())
            assert invalid_frame["id"] == 2
            result_payload = invalid_frame.get("result", {})
            assert result_payload.get("ok") is False
            assert result_payload.get("reason") == "validation_failed"
            assert any(
                err.get("path") == "/params" for err in result_payload.get("errors", [])
            )

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
        assert "timestamp=" in shutdown_line
        assert "schemas_dir=" in shutdown_line
        assert "examples_dir=" in shutdown_line
        _assert_iso_timestamp(shutdown_line)
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
        with contextlib.suppress(FileNotFoundError):
            if ready_file.exists():
                ready_file.unlink()

    assert proc.returncode == -signal.SIGINT
    assert not socket_path.exists()
    assert not ready_file.exists()


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-domain sockets not supported on Windows")
def test_socket_allows_multiple_concurrent_clients(tmp_path):
    socket_path = tmp_path / "mcp.sock"
    ready_file = tmp_path / "mcp.ready"
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    (schemas_dir / "asset.schema.json").write_text(json.dumps(_MINIMAL_SCHEMA))
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()

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
            "SYN_EXAMPLES_DIR": str(examples_dir),
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
        assert "timestamp=" in ready_line
        _assert_iso_timestamp(ready_line)

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client_one:
            client_one.connect(str(socket_path))
            reader_one = client_one.makefile("r", encoding="utf-8")
            writer_one = client_one.makefile("w", encoding="utf-8")

            request_one = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "list_schemas",
                "params": {},
            }
            writer_one.write(json.dumps(request_one) + "\n")
            writer_one.flush()

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client_two:
                client_two.settimeout(3.0)
                client_two.connect(str(socket_path))
                reader_two = client_two.makefile("r", encoding="utf-8")
                writer_two = client_two.makefile("w", encoding="utf-8")

                request_two = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "get_schema",
                    "params": {"name": "asset"},
                }
                writer_two.write(json.dumps(request_two) + "\n")
                writer_two.flush()

                try:
                    raw_two = reader_two.readline()
                except socket.timeout:
                    pytest.fail("second client timed out waiting for response")

                response_two = json.loads(raw_two)
                assert response_two["id"] == 2
                assert response_two["result"]["ok"] is True

                response_one = json.loads(reader_one.readline())
                assert response_one["id"] == 1
                assert response_one["result"]["ok"] is True

                # Ensure client one is still able to issue additional requests after client two completes.
                follow_up = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "list_examples",
                    "params": {},
                }
                writer_one.write(json.dumps(follow_up) + "\n")
                writer_one.flush()
                response_follow_up = json.loads(reader_one.readline())
                assert response_follow_up["id"] == 3
                assert response_follow_up["result"]["ok"] is True

                reader_two.close()
                writer_two.close()

            reader_one.close()
            writer_one.close()

        proc.send_signal(signal.SIGINT)
        shutdown_line = _wait_for_line(proc.stderr, proc, "mcp:shutdown")
        assert "timestamp=" in shutdown_line
        assert "schemas_dir=" in shutdown_line
        assert "examples_dir=" in shutdown_line
        _assert_iso_timestamp(shutdown_line)
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
        with contextlib.suppress(FileNotFoundError):
            if ready_file.exists():
                ready_file.unlink()

    assert proc.returncode == -signal.SIGINT
