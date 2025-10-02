from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # pragma: no cover - environment guard
    sys.path.insert(0, str(ROOT))


def _wait_for_line(stream, proc, needle: str, timeout: float = 10.0) -> str:
    deadline = time.time() + timeout
    lines: List[str] = []
    grace_period = 1.0  # allow stderr flush after exit
    exited_at: float | None = None

    while time.time() < deadline:
        line = stream.readline()
        if not line:
            if proc.poll() is not None:
                if exited_at is None:
                    exited_at = time.time()
                if time.time() - exited_at > grace_period:
                    break
                time.sleep(0.05)
                continue
            time.sleep(0.05)
            continue
        text = line.strip()
        lines.append(text)
        if needle in text:
            return text
    raise AssertionError(f"did not observe '{needle}' in output: {lines}")


def pytest_collection_modifyitems(session, config, items) -> None:  # pragma: no cover - pytest hook
    patched = set()
    for item in items:
        module = getattr(item, "module", None)
        if module is None or module in patched:
            continue
        if hasattr(module, "_wait_for_line"):
            setattr(module, "_wait_for_line", _wait_for_line)
            patched.add(module)
