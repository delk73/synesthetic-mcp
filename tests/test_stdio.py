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

import pytest


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
    error = payload.get("error")
    assert isinstance(error, dict)
    assert error.get("code") == -32603
