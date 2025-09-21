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
from typing import NamedTuple
from urllib.parse import urlparse

from . import stdio_main
from .core import SUBMODULE_SCHEMAS_DIR, _infer_schema_name_from_example
from .validate import validate_asset

DEFAULT_READY_FILE = "/tmp/mcp.ready"


class Endpoint(NamedTuple):
    mode: str
    host: str | None
    port: int | None


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


def _resolve_endpoint() -> Endpoint:
    raw = os.environ.get("MCP_ENDPOINT", "stdio")
    value = raw.strip() if raw else ""
    if value in {"", "stdio", "stdio://"}:
        return Endpoint("stdio", None, None)

    lowered = value.lower()
    if lowered in {"http", "tcp"}:
        host, port = _resolve_host_port()
        return Endpoint("http", host, port)

    parsed = urlparse(value)
    scheme = (parsed.scheme or "http").lower()
    if scheme not in {"http", "tcp"}:
        raise RuntimeError(f"Unsupported MCP_ENDPOINT scheme '{scheme}'")
    if parsed.hostname is None or parsed.port is None:
        raise RuntimeError(
            "MCP_ENDPOINT must include host and port (e.g. http://0.0.0.0:7000)"
        )
    return Endpoint("http", parsed.hostname, parsed.port)


def _ready_file_path() -> Path | None:
    raw = os.environ.get("MCP_READY_FILE", DEFAULT_READY_FILE)
    value = raw.strip() if raw else ""
    if not value:
        return None
    return Path(value)


def _write_ready_file(path: Path | None) -> None:
    if not path:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ready\n", encoding="utf-8")
    except KeyboardInterrupt:  # pragma: no cover - defensive
        logging.warning(
            "mcp:warning reason=ready_file_interrupted path=%s", path, exc_info=True
        )
    except Exception:
        logging.warning("mcp:warning reason=ready_file_failed path=%s", path, exc_info=True)


def _clear_ready_file(path: Path | None) -> None:
    if not path:
        return
    with contextlib.suppress(FileNotFoundError):
        path.unlink()


async def _http_health_handler(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
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


async def _serve_http_forever(
    host: str, port: int, schemas_dir: str, ready_file: Path | None
) -> None:
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
    logging.info(
        "mcp:ready mode=http host=%s port=%s schemas_dir=%s", host, port, schemas_dir
    )
    _write_ready_file(ready_file)
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
        _clear_ready_file(ready_file)
        if ready:
            logging.info("mcp:shutdown mode=http")


def _run_stdio(schemas_dir: str, ready_file: Path | None) -> int:
    def _sigterm_handler(signum: int, _frame: object) -> None:  # pragma: no cover - signal
        raise KeyboardInterrupt

    handlers: list[tuple[int, object]] = []
    try:
        previous = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, _sigterm_handler)
        handlers.append((signal.SIGTERM, previous))
    except Exception:  # pragma: no cover - platform guard
        pass

    logging.info("mcp:ready mode=stdio schemas_dir=%s", schemas_dir)
    _write_ready_file(ready_file)
    exit_code = 0
    try:
        stdio_main.main()
    except KeyboardInterrupt:
        exit_code = 0
    except Exception:
        logging.exception("mcp:error reason=runtime_failure mode=stdio")
        exit_code = 1
    finally:
        logging.info("mcp:shutdown mode=stdio")
        for sig, previous in handlers:
            try:
                signal.signal(sig, previous)
            except Exception:
                pass
        _clear_ready_file(ready_file)
    return exit_code


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
    except Exception as exc:
        logging.error("mcp:error reason=setup_failed detail=%s", exc)
        sys.exit(2)

    try:
        endpoint = _resolve_endpoint()
    except Exception as exc:
        logging.error("mcp:error reason=setup_failed detail=%s", exc)
        sys.exit(2)

    ready_file = _ready_file_path()

    if endpoint.mode == "stdio":
        code = _run_stdio(schemas_dir, ready_file)
        sys.exit(code)

    host = endpoint.host
    port = endpoint.port
    if host is None or port is None:
        logging.error("mcp:error reason=setup_failed detail=invalid_endpoint")
        sys.exit(2)

    try:
        asyncio.run(_serve_http_forever(host, port, schemas_dir, ready_file))
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        logging.exception("mcp:error reason=runtime_failure mode=http")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
