from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, TextIO

import pytest

CANONICAL_PREFIX = "https://delk73.github.io/synesthetic-schemas/schema/0.7.3/"
CANONICAL_ASSET_SCHEMA = f"{CANONICAL_PREFIX}asset.schema.json"


def _wait_for_line(stream: TextIO, proc: subprocess.Popen, needle: str, timeout: float = 10.0) -> str:
    deadline = time.time() + timeout
    if stream.closed:
        raise AssertionError("stream unexpectedly closed")
    lines: List[str] = []
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


def test_entrypoint_ready_and_shutdown(tmp_path):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    ready_file = tmp_path / "mcp.ready"

    env = os.environ.copy()
    env.update(
        {
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "SYN_EXAMPLES_DIR": str(examples_dir),
            "PYTHONUNBUFFERED": "1",
            "MCP_READY_FILE": str(ready_file),
            "MCP_MODE": "stdio",
        }
    )

    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        if proc.stderr is None:
            raise AssertionError("stderr not captured")

        ready_line = _wait_for_line(proc.stderr, proc, "mcp:ready")
        assert "mode=stdio" in ready_line
        assert "schemas_dir=" in ready_line
        assert "examples_dir=" in ready_line
        assert "schemas_base=" in ready_line
        assert "schema_version=" in ready_line
        assert "cache_dir=" in ready_line
        assert "timestamp=" in ready_line
        _assert_iso_timestamp(ready_line)

        deadline = time.time() + 5
        while time.time() < deadline and not ready_file.exists():
            time.sleep(0.05)
        assert ready_file.exists(), "ready file not created before shutdown"

        ready_fields = {
            part
            for part in ready_line.split()
            if "=" in part and not part.startswith("timestamp=")
        }

        proc.send_signal(signal.SIGTERM)
        shutdown_line = _wait_for_line(proc.stderr, proc, "mcp:shutdown")
        assert "mode=stdio" in shutdown_line
        assert "schemas_base=" in shutdown_line
        assert "schema_version=" in shutdown_line
        assert "cache_dir=" in shutdown_line
        assert "timestamp=" in shutdown_line
        _assert_iso_timestamp(shutdown_line)

        shutdown_fields = {
            part
            for part in shutdown_line.split()
            if "=" in part and not part.startswith("timestamp=")
        }
        assert ready_fields.issubset(shutdown_fields)

        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
        if proc.stdin is not None:
            with contextlib.suppress(Exception):
                proc.stdin.close()

    assert proc.returncode == -int(signal.SIGTERM)
    deadline = time.time() + 5
    while time.time() < deadline and ready_file.exists():
        time.sleep(0.05)
    assert not ready_file.exists(), "ready file not removed on SIGTERM"


def test_entrypoint_sigterm_exit_code(tmp_path):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    ready_file = tmp_path / "mcp.ready"

    env = os.environ.copy()
    env.update(
        {
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "SYN_EXAMPLES_DIR": str(examples_dir),
            "PYTHONUNBUFFERED": "1",
            "MCP_READY_FILE": str(ready_file),
            "MCP_MODE": "stdio",
        }
    )

    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        if proc.stderr is None:
            raise AssertionError("stderr not captured")

        _wait_for_line(proc.stderr, proc, "mcp:ready")
        deadline = time.time() + 5
        while time.time() < deadline and not ready_file.exists():
            time.sleep(0.05)
        assert ready_file.exists(), "ready file not created before SIGTERM"
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
        if proc.stdin is not None:
            with contextlib.suppress(Exception):
                proc.stdin.close()

    assert proc.returncode == -int(signal.SIGTERM)
    deadline = time.time() + 5
    while time.time() < deadline and ready_file.exists():
        time.sleep(0.05)
    assert not ready_file.exists(), "ready file not removed on SIGTERM"


def _run_mcp(args, env):
    return subprocess.run(
        [sys.executable, "-m", "mcp", *args],
        text=True,
        capture_output=True,
        env=env,
    )


def test_invalid_schema_dir(tmp_path):
    env = os.environ.copy()
    env.update({
        "SYN_SCHEMAS_DIR": str(tmp_path / "missing"),
        "PYTHONUNBUFFERED": "1",
    })

    proc = _run_mcp([], env)
    combined = (proc.stdout or "") + (proc.stderr or "")

    assert proc.returncode == 2
    assert "mcp:error reason=setup_failed" in combined


def test_non_stdio_endpoint_rejected(tmp_path):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()

    env = os.environ.copy()
    env.update(
        {
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "SYN_EXAMPLES_DIR": str(examples_dir),
            "MCP_ENDPOINT": "http",
            "PYTHONUNBUFFERED": "1",
        }
    )

    proc = _run_mcp([], env)
    combined = (proc.stdout or "") + (proc.stderr or "")

    assert proc.returncode == 2
    assert "mcp:error reason=setup_failed" in combined
    assert "Unsupported MCP transport" in combined


def test_validate_flag_failure(tmp_path):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    (schemas_dir / "asset.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                },
                "required": ["id"],
                "additionalProperties": False,
            }
        )
    )

    asset_path = tmp_path / "invalid.json"
    asset_path.write_text(json.dumps({"$schema": CANONICAL_ASSET_SCHEMA, "id": ""}))

    env = os.environ.copy()
    env.update(
        {
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "PYTHONUNBUFFERED": "1",
        }
    )

    proc = _run_mcp(["--validate", str(asset_path)], env)

    assert proc.returncode != 0
    assert proc.stdout
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert "schema" not in payload


def test_socket_endpoint_invokes_socket_server(monkeypatch, tmp_path):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()

    monkeypatch.setenv("SYN_SCHEMAS_DIR", str(schemas_dir))
    monkeypatch.setenv("MCP_MODE", "socket")
    socket_path = tmp_path / "server.sock"
    monkeypatch.setenv("MCP_SOCKET_PATH", str(socket_path))
    ready_file = tmp_path / "mcp.ready"
    monkeypatch.setenv("MCP_READY_FILE", str(ready_file))

    calls = {}

    class DummyServer:
        def __init__(self, path, mode):
            calls["init"] = (Path(path), mode)

        def start(self):
            calls["started"] = True

        def serve_forever(self, handler):
            calls["handler"] = handler
            raise KeyboardInterrupt

        def close(self):
            calls["closed"] = True

    monkeypatch.setattr("mcp.socket_main.SocketServer", DummyServer)

    from mcp import __main__ as cli

    with pytest.raises(SystemExit) as excinfo:
        cli.main([])

    assert excinfo.value.code == 0
    assert calls["init"][0] == socket_path
    assert calls["started"] is True
    assert callable(calls["handler"])
    assert calls.get("closed") is True
    assert not ready_file.exists()
def _assert_iso_timestamp(line: str) -> None:
    token = None
    for part in line.split():
        if part.startswith("timestamp="):
            token = part.split("=", 1)[1]
            break
    assert token, f"timestamp field missing in log: {line}"
    datetime.fromisoformat(token)
