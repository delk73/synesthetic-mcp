"""Blocking MCP server entrypoint."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys

from .core import SUBMODULE_SCHEMAS_DIR


def _resolve_schemas_dir() -> str:
    env_dir = os.environ.get("SYN_SCHEMAS_DIR")
    if env_dir:
        path = os.path.abspath(env_dir)
        if os.path.isdir(path):
            return path
        raise RuntimeError(f"SYN_SCHEMAS_DIR '{env_dir}' is not a directory")
    submodule_dir = os.path.abspath(SUBMODULE_SCHEMAS_DIR)
    if os.path.isdir(submodule_dir):
        return submodule_dir
    raise RuntimeError("No schemas directory available; set SYN_SCHEMAS_DIR")


def _resolve_host_port() -> tuple[str, int]:
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port_value = os.environ.get("MCP_PORT", "8000")
    try:
        port = int(port_value)
    except ValueError as exc:
        raise RuntimeError(f"MCP_PORT '{port_value}' is not an integer") from exc
    if port < 0 or port > 65535:
        raise RuntimeError(f"MCP_PORT '{port}' must be between 0 and 65535")
    return host, port


async def _serve_forever(host: str, port: int, schemas_dir: str) -> None:
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    ready = False

    def _request_shutdown() -> None:
        if not stop_event.is_set():
            stop_event.set()

    def _signal_handler(signum: int, _frame: object) -> None:
        try:
            loop.call_soon_threadsafe(_request_shutdown)
        except RuntimeError:
            _request_shutdown()

    handlers: list[tuple[str, int, object]] = []
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_shutdown)
            handlers.append(("loop", sig, None))
        except (NotImplementedError, RuntimeError):
            previous = signal.getsignal(sig)
            signal.signal(sig, _signal_handler)
            handlers.append(("signal", sig, previous))

    logging.info("mcp:ready host=%s port=%s schemas_dir=%s", host, port, schemas_dir)
    ready = True

    try:
        await stop_event.wait()
    finally:
        for kind, sig, previous in handlers:
            try:
                if kind == "loop":
                    loop.remove_signal_handler(sig)
                else:
                    signal.signal(sig, previous)
            except Exception:
                pass
        if ready:
            logging.info("mcp:shutdown")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        schemas_dir = _resolve_schemas_dir()
        host, port = _resolve_host_port()
    except Exception as exc:
        logging.error("mcp:error reason=setup_failed detail=%s", exc)
        sys.exit(2)

    try:
        asyncio.run(_serve_forever(host, port, schemas_dir))
    except KeyboardInterrupt:
        logging.info("mcp:shutdown")
        sys.exit(0)
    except Exception:
        logging.exception("mcp:error reason=runtime_failure")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
