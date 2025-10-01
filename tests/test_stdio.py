import contextlib
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from mcp import transport

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


def test_validate_asset_requires_schema(tmp_path):
    from subprocess import Popen, PIPE
    import json, sys

    proc = Popen([sys.executable, "-m", "mcp"], stdin=PIPE, stdout=PIPE, text=True)
    req = {"jsonrpc": "2.0", "id": 1, "method": "validate_asset", "params": {"asset": {}}}
    stdout, _ = proc.communicate(json.dumps(req) + "\n", timeout=5)
    resp = json.loads(stdout.strip())
    assert resp["result"]["ok"] is False
    assert resp["result"]["reason"] == "validation_failed"
    assert any(err["msg"] == "schema param is required" for err in resp["result"]["errors"])

def test_stdio_loop_smoke(monkeypatch):

    # Prepare a single JSON-RPC request line for list_schemas
    request: Dict[str, Any] = {"id": 1, "method": "list_schemas", "params": {}}
    stdin = io.StringIO(json.dumps(request) + "\n")
    stdout = io.StringIO()

    # Patch stdio and invoke the loop
    import mcp.stdio_main as stdio

    monkeypatch.setattr(stdio.sys, "stdin", stdin)
    monkeypatch.setattr(stdio.sys, "stdout", stdout)

    stdio.main()

    # Read the single response line and validate shape
    out_line = stdout.getvalue().strip().splitlines()[0]
    payload = json.loads(out_line)

    assert payload.get("jsonrpc") == "2.0"
    assert payload.get("id") == 1
    result = payload.get("result")
    assert isinstance(result, dict)
    assert result.get("ok") is True
    assert "schemas" in result and isinstance(result["schemas"], list)


def test_stdio_validate_alias_warns_to_stderr(tmp_path):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "id": {"type": "string", "minLength": 1},
            "name": {"type": "string", "minLength": 1},
            "schema": {"type": "string", "const": "asset"},
        },
        "required": ["id", "name"],
        "additionalProperties": False,
    }
    (schemas_dir / "asset.schema.json").write_text(json.dumps(schema))

    env = os.environ.copy()
    env["SYN_SCHEMAS_DIR"] = str(schemas_dir)
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        assert proc.stderr is not None
        ready_line = proc.stderr.readline()
        if not ready_line:
            code = proc.poll()
            raise AssertionError(f"mcp process exited early with code {code}")
        assert "mcp:ready" in ready_line
        assert "timestamp=" in ready_line
        _assert_iso_timestamp(ready_line)

        request = {
            "jsonrpc": "2.0",
            "id": 42,
            "method": "validate",
            "params": {
                "asset": {"id": "asset-1", "name": "Asset", "schema": "asset"},
                "schema": "asset",
            },
        }
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()

        assert proc.stdout is not None
        response_line = proc.stdout.readline()
        if not response_line:
            code = proc.poll()
            raise AssertionError(f"no response from mcp stdio loop (exit {code})")
        payload = json.loads(response_line)
        assert payload.get("id") == 42
        result = payload.get("result", {})
        assert result.get("ok") is True
        assert result.get("errors") == []

        warning_line = ""
        deadline = time.time() + 5
        while time.time() < deadline:
            line = proc.stderr.readline()
            if not line:
                if proc.poll() is not None:
                    break
                continue
            if "deprecated_alias" in line:
                warning_line = line
                break
        assert "deprecated_alias" in warning_line
        assert "method=validate" in warning_line

        shutdown_seen = False
        shutdown_line = ""
        if proc.stdin:
            proc.stdin.close()
        if proc.stdout:
            proc.stdout.close()
        deadline = time.time() + 5
        while time.time() < deadline:
            line = proc.stderr.readline()
            if not line:
                if proc.poll() is not None:
                    break
                continue
            if "mcp:shutdown" in line:
                shutdown_seen = True
                shutdown_line = line
                break
        proc.wait(timeout=5)
        assert shutdown_seen
        assert "timestamp=" in shutdown_line
        _assert_iso_timestamp(shutdown_line)
    finally:
        if proc.poll() is None:
            proc.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)


def test_stdio_entrypoint_validate_asset(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    ready_file = tmp_path / "mcp.ready"

    env = os.environ.copy()
    env.pop("MCP_ENDPOINT", None)
    env["MCP_READY_FILE"] = str(ready_file)
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp"],
        cwd=str(repo_root),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        # Wait for readiness log so we know the loop is accepting stdin.
        line = proc.stderr.readline()
        if not line:
            code = proc.poll()
            raise AssertionError(f"mcp process exited early with code {code}")
        assert "mcp:ready" in line
        assert "mode=stdio" in line
        assert "timestamp=" in line
        _assert_iso_timestamp(line)

        # Ensure the ready file is created for health checks.
        deadline = time.time() + 5
        while time.time() < deadline and not ready_file.exists():
            time.sleep(0.05)
        if not ready_file.exists():
            pytest.fail("ready file not created by stdio entrypoint")

        contents = ready_file.read_text().strip()
        parts = contents.split(" ", 1)
        assert len(parts) == 2, f"unexpected ready file contents: {contents!r}"
        pid_str, timestamp = parts
        assert pid_str == str(proc.pid)
        # Ensure the timestamp is valid ISO8601
        datetime.fromisoformat(timestamp)

        asset_path = (
            repo_root
            / "libs"
            / "synesthetic-schemas"
            / "examples"
            / "SynestheticAsset_Example1.json"
        )
        example = json.loads(asset_path.read_text())

        request = {
            "id": 99,
            "method": "validate_asset",
            "params": {"asset": example, "schema": "nested-synesthetic-asset"},
        }
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()

        assert proc.stdout is not None
        response_line = proc.stdout.readline()
        if not response_line:
            code = proc.poll()
            raise AssertionError(f"no response from mcp stdio loop (exit {code})")
        payload = json.loads(response_line)

        assert payload.get("id") == 99
        result = payload.get("result", {})
        assert result.get("ok") is True
        assert result.get("errors") == []

        if proc.stdin:
            proc.stdin.close()
        proc.wait(timeout=5)

        deadline = time.time() + 5
        while time.time() < deadline and ready_file.exists():
            time.sleep(0.05)
        assert not ready_file.exists()
    finally:
        if proc.poll() is None:
            proc.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)


def test_stdio_error_includes_request_id(monkeypatch):
    request: Dict[str, Any] = {
        "id": 7,
        "method": "get_schema",
        "params": "not-a-dict",
    }
    stdin = io.StringIO(json.dumps(request) + "\n")
    stdout = io.StringIO()

    import mcp.stdio_main as stdio

    monkeypatch.setattr(stdio.sys, "stdin", stdin)
    monkeypatch.setattr(stdio.sys, "stdout", stdout)

    stdio.main()

    out_line = stdout.getvalue().strip().splitlines()[0]
    payload = json.loads(out_line)

    assert payload.get("jsonrpc") == "2.0"
    assert payload.get("id") == 7
    result = payload.get("result")
    assert isinstance(result, dict)
    assert result.get("ok") is False
    assert result.get("reason") == "validation_failed"
    errors = result.get("errors")
    assert isinstance(errors, list)
    assert any(err.get("path") == "/params" for err in errors)


def test_stdio_unsupported_uses_detail(monkeypatch):
    request: Dict[str, Any] = {"id": 5, "method": "nope", "params": {}}
    stdin = io.StringIO(json.dumps(request) + "\n")
    stdout = io.StringIO()

    import mcp.stdio_main as stdio

    monkeypatch.setattr(stdio.sys, "stdin", stdin)
    monkeypatch.setattr(stdio.sys, "stdout", stdout)

    stdio.main()

    payload = json.loads(stdout.getvalue().strip())
    assert payload.get("id") == 5
    result = payload.get("result", {})
    assert result.get("reason") == "unsupported"
    assert result.get("detail") == "tool not implemented"


def test_jsonrpc_version_must_be_2_0():
    line = json.dumps({
        "jsonrpc": "1.0",
        "id": 13,
        "method": "list_schemas",
        "params": {},
    })

    frame = transport.process_line(line, lambda _method, _params: {"ok": True})
    payload = json.loads(frame)

    assert payload["id"] == 13
    result = payload["result"]
    assert result["ok"] is False
    assert result["reason"] == "validation_failed"
    assert {"path": "/jsonrpc", "msg": "jsonrpc must be '2.0'"} in result["errors"]


def test_stdio_rejects_oversized_request(monkeypatch):
    blob = "x" * (MAX_BYTES + 1)
    oversized = {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "validate_many",
        "params": {"assets": [blob]},
    }
    line = json.dumps(oversized)
    assert len(line.encode("utf-8")) > MAX_BYTES

    stdin = io.StringIO(line + "\n")
    stdout = io.StringIO()

    import mcp.stdio_main as stdio

    monkeypatch.setattr(stdio.sys, "stdin", stdin)
    monkeypatch.setattr(stdio.sys, "stdout", stdout)

    stdio.main()

    payload = json.loads(stdout.getvalue().strip())
    assert payload.get("id") is None
    result = payload.get("result", {})
    assert result.get("ok") is False
    assert result.get("reason") == "validation_failed"
    errors = result.get("errors", [])
    assert errors and errors[0].get("msg") == "payload_too_large"
