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


def _available_port(host: str = "127.0.0.1") -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((host, 0))
            return probe.getsockname()[1]
    except PermissionError as exc:  # pragma: no cover - sandbox limitation
        pytest.skip(f"tcp sockets unavailable: {exc}")


@pytest.mark.skipif(sys.platform == "win32", reason="unreliable TCP shutdown timing on Windows CI")
def test_tcp_transport_end_to_end(tmp_path):
    host = "127.0.0.1"
    port = _available_port(host)

    ready_file = tmp_path / "mcp.ready"
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    minimal_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema": {"type": "string", "const": "asset"},
        },
        "required": ["schema"],
        "additionalProperties": True,
    }
    (schemas_dir / "asset.schema.json").write_text(json.dumps(minimal_schema))

    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()

    env = os.environ.copy()
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "SYN_EXAMPLES_DIR": str(examples_dir),
            "MCP_ENDPOINT": "tcp",
            "MCP_HOST": host,
            "MCP_PORT": str(port),
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
        assert "mode=tcp" in ready_line
        assert f"host={host}" in ready_line
        assert "port=" in ready_line
        assert "schemas_dir=" in ready_line
        assert "examples_dir=" in ready_line
        assert "timestamp=" in ready_line

        # derive actual bound port in case the server chose a different one (e.g. port=0)
        bound_port = port
        for part in ready_line.split():
            if part.startswith("port="):
                bound_port = int(part.split("=", 1)[1])
                break

        with socket.create_connection((host, bound_port), timeout=5.0) as client:
            with client.makefile("r", encoding="utf-8") as reader, client.makefile(
                "w", encoding="utf-8"
            ) as writer:
                list_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "list_schemas",
                    "params": {},
                }
                writer.write(json.dumps(list_request) + "\n")
                writer.flush()
                resp = json.loads(reader.readline())
                assert resp["id"] == 1
                assert resp["result"]["ok"] is True

                bad_params = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "get_schema",
                    "params": "oops",
                }
                writer.write(json.dumps(bad_params) + "\n")
                writer.flush()
                invalid_resp = json.loads(reader.readline())
                assert invalid_resp["id"] == 2
                result = invalid_resp.get("result", {})
                assert result.get("ok") is False
                assert result.get("reason") == "validation_failed"
                assert any(err.get("path") == "/params" for err in result.get("errors", []))

                oversized = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "list_schemas",
                    "params": {"blob": "x" * (MAX_BYTES + 1)},
                }
                writer.write(json.dumps(oversized) + "\n")
                writer.flush()
                large_resp = json.loads(reader.readline())
                assert large_resp.get("id") is None
                result_large = large_resp.get("result", {})
                assert result_large.get("reason") == "validation_failed"
                assert any(
                    err.get("msg") == "payload_too_large" for err in result_large.get("errors", [])
                )

        proc.send_signal(signal.SIGINT)
        shutdown_line = _wait_for_line(proc.stderr, proc, "mcp:shutdown")
        assert "mode=tcp" in shutdown_line
        assert f"host={host}" in shutdown_line
        assert "port=" in shutdown_line
        assert "timestamp=" in shutdown_line
        assert "schemas_dir=" in shutdown_line
        assert "examples_dir=" in shutdown_line
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)
        with contextlib.suppress(FileNotFoundError):
            ready_file.unlink()

    assert proc.returncode == 0
    assert not ready_file.exists()
