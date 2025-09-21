from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from typing import List, TextIO


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

    env = os.environ.copy()
    env.update(
        {
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "PYTHONUNBUFFERED": "1",
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
        if proc.stderr is None:
            raise AssertionError("stderr not captured")

        ready_line = _wait_for_line(proc.stderr, proc, "mcp:ready")
        assert "schemas_dir=" in ready_line

        proc.send_signal(signal.SIGINT)
        shutdown_line = _wait_for_line(proc.stderr, proc, "mcp:shutdown")
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()

    combined = "\n".join(filter(None, [ready_line, shutdown_line]))
    assert proc.returncode == 0


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

    env = os.environ.copy()
    env.update(
        {
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "MCP_ENDPOINT": "http",
            "PYTHONUNBUFFERED": "1",
        }
    )

    proc = _run_mcp([], env)
    combined = (proc.stdout or "") + (proc.stderr or "")

    assert proc.returncode == 2
    assert "mcp:error reason=setup_failed" in combined
    assert "Only STDIO transport is supported" in combined


def test_validate_flag_failure(tmp_path):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    (schemas_dir / "asset.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "const": "asset"},
                    "id": {"type": "string", "minLength": 1},
                },
                "required": ["schema", "id"],
                "additionalProperties": False,
            }
        )
    )

    asset_path = tmp_path / "invalid.json"
    asset_path.write_text(json.dumps({"schema": "asset", "id": ""}))

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
    assert payload["schema"] == "asset"
