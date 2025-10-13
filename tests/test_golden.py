from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

GOLDEN_PATH = Path(__file__).resolve().parent / "fixtures" / "golden.jsonl"
SCHEMAS_DIR = Path("tests/fixtures/schemas")
EXAMPLES_DIR = Path("tests/fixtures/examples")


@pytest.mark.slow
def test_golden_requests():
    env = os.environ.copy()
    env["SYN_SCHEMAS_DIR"] = str(SCHEMAS_DIR)
    env["SYN_EXAMPLES_DIR"] = str(EXAMPLES_DIR)
    env["PYTHONUNBUFFERED"] = "1"
    env["MCP_MODE"] = "stdio"

    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        assert proc.stdin is not None
        assert proc.stdout is not None
        assert proc.stderr is not None

        ready_line = proc.stderr.readline()
        if not ready_line:
            code = proc.poll()
            raise AssertionError(f"mcp process failed to start (exit {code})")
        assert "mcp:ready" in ready_line

        for raw in GOLDEN_PATH.read_text().splitlines():
            if not raw:
                continue
            record = json.loads(raw)
            expected = record["response"]

            if "request" in record:
                payload = json.dumps(record["request"])
            else:
                payload = record["raw_request"]

            proc.stdin.write(payload + "\n")
            proc.stdin.flush()

            line = proc.stdout.readline()
            if not line:
                code = proc.poll()
                raise AssertionError(f"missing response for {record['description']} (exit {code})")
            actual = json.loads(line.strip())
            assert actual == expected

            expected_stderr = record.get("stderr_contains")
            if expected_stderr:
                observed = ""
                deadline = time.time() + 5
                while time.time() < deadline:
                    log_line = proc.stderr.readline()
                    if not log_line:
                        if proc.poll() is not None:
                            break
                        time.sleep(0.01)
                        continue
                    observed = log_line
                    if expected_stderr in log_line:
                        break
                assert expected_stderr in observed

        proc.stdin.close()

        shutdown_seen = False
        deadline = time.time() + 5
        while time.time() < deadline:
            log_line = proc.stderr.readline()
            if not log_line:
                if proc.poll() is not None:
                    break
                time.sleep(0.01)
                continue
            if "mcp:shutdown" in log_line:
                shutdown_seen = True
                break
        proc.wait(timeout=5)
        assert shutdown_seen
    finally:
        if proc.stdout:
            proc.stdout.close()
        if proc.stderr:
            proc.stderr.close()
        if proc.poll() is None:
            proc.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)
