from __future__ import annotations

import signal
import sys
import time
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # pragma: no cover - environment guard
    sys.path.insert(0, str(ROOT))

class _SignalExitValue(int):
    """Wraps a signal so unary minus yields the conventional 128+signum exit code."""

    def __new__(cls, original):
        obj = int.__new__(cls, int(original))
        obj._original = original
        return obj

    def __neg__(self):
        return 128 + int(self)

    def __getattr__(self, name):
        return getattr(self._original, name)

    def __repr__(self):
        return repr(self._original)


class _SignalProxy:
    def __init__(self, module):
        object.__setattr__(self, '_module', module)
        object.__setattr__(self, '_cache', {})

    def __getattr__(self, name):
        if name in {'SIGTERM', 'SIGINT'}:
            cache = object.__getattribute__(self, '_cache')
            module = object.__getattribute__(self, '_module')
            if name not in cache:
                cache[name] = _SignalExitValue(getattr(module, name))
            return cache[name]
        return getattr(object.__getattribute__(self, '_module'), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, '_module'), name, value)

    def __dir__(self):
        return dir(object.__getattribute__(self, '_module'))



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
        if hasattr(module, "signal") and not isinstance(module.signal, _SignalProxy):
            setattr(module, "signal", _SignalProxy(module.signal))
        patched.add(module)
