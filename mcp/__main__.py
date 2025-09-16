"""Blocking MCP server entrypoint."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import os
import signal
import sys
from pathlib import Path

from .core import SUBMODULE_SCHEMAS_DIR, _infer_schema_name_from_example
from .validate import validate_asset


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
    port_value = os.environ.get("MCP_PORT", "7000")
    try:
        port = int(port_value)
    except ValueError as exc:
        raise RuntimeError(f"MCP_PORT '{port_value}' is not an integer") from exc
    if port < 0 or port > 65535:
        raise RuntimeError(f"MCP_PORT '{port}' must be between 0 and 65535")
    return host, port


async def _http_health_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        data = await reader.read(1024)
        request_line = ""
        if data:
            try:
                request_line = data.splitlines()[0].decode("latin1")
            except Exception:
                request_line = ""
        if request_line.startswith("GET /healthz"):
            body = b"ok\n"
            headers = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode("ascii")
            writer.write(headers + body)
        else:
            writer.write(
                b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
            )
        await writer.drain()
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


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

    server = await asyncio.start_server(_http_health_handler, host=host, port=port)
    logging.info("mcp:ready host=%s port=%s schemas_dir=%s", host, port, schemas_dir)
    ready = True

    try:
        await stop_event.wait()
    finally:
        server.close()
        with contextlib.suppress(Exception):
            await server.wait_closed()
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


def _run_validation(path: str) -> int:
    target = Path(path)
    try:
        contents = target.read_text()
    except FileNotFoundError:
        result = {
            "ok": False,
            "reason": "io_error",
            "errors": [{"path": "/", "msg": f"file_not_found: {target}"}],
        }
        print(json.dumps(result))
        return 2
    except Exception as exc:
        result = {
            "ok": False,
            "reason": "io_error",
            "errors": [{"path": "/", "msg": f"read_failed: {exc}"}],
        }
        print(json.dumps(result))
        return 2

    try:
        asset = json.loads(contents)
    except json.JSONDecodeError as exc:
        result = {
            "ok": False,
            "reason": "parse_error",
            "errors": [
                {"path": "/", "msg": f"json_decode_error: line {exc.lineno} column {exc.colno}"}
            ],
        }
        print(json.dumps(result))
        return 2

    schema = _infer_schema_name_from_example(target, asset)
    try:
        validation = validate_asset(asset, schema)
    except Exception as exc:  # pragma: no cover - defensive guard
        result = {
            "ok": False,
            "reason": "validation_error",
            "errors": [{"path": "/", "msg": f"unexpected_error: {exc}"}],
        }
        print(json.dumps(result))
        return 2

    payload = dict(validation)
    payload.setdefault("schema", schema)
    print(json.dumps(payload))
    return 0 if validation.get("ok", False) else 1


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Synesthetic MCP server")
    parser.add_argument(
        "--validate",
        metavar="PATH",
        help="Validate a JSON asset file and print the result",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.validate:
        code = _run_validation(args.validate)
        sys.exit(code)

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
