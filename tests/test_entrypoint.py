from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from typing import List


def _wait_for_line(proc: subprocess.Popen, needle: str, timeout: float = 10.0) -> str:
    deadline = time.time() + timeout
    if proc.stdout is None:
        raise AssertionError("process stdout not captured")
    lines: List[str] = []
    while time.time() < deadline:
        line = proc.stdout.readline()
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
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )

    try:
        ready_line = _wait_for_line(proc, "mcp:ready")
        assert "schemas_dir=" in ready_line

        proc.send_signal(signal.SIGINT)
        output, _ = proc.communicate(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()

    combined = "\n".join(filter(None, [ready_line, output]))
    assert "mcp:shutdown" in combined
    assert proc.returncode == 0
