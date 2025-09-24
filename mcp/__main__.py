"""Blocking MCP server entrypoint."""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import socket_main, stdio_main
from .core import SUBMODULE_SCHEMAS_DIR, _infer_schema_name_from_example
from .validate import validate_asset

DEFAULT_READY_FILE = "/tmp/mcp.ready"
DEFAULT_SOCKET_PATH = "/tmp/mcp.sock"


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


def _endpoint() -> str:
    raw = os.environ.get("MCP_ENDPOINT", "stdio")
    value = raw.strip() if raw else "stdio"
    if value in {"", "stdio", "stdio://"}:
        return "stdio"
    if value == "socket":
        return "socket"
    raise RuntimeError("Unsupported MCP transport; set MCP_ENDPOINT to 'stdio' or 'socket'")


def _socket_path() -> Path:
    raw = os.environ.get("MCP_SOCKET_PATH", DEFAULT_SOCKET_PATH)
    value = raw.strip() if raw else DEFAULT_SOCKET_PATH
    return Path(value)


def _socket_mode() -> int:
    raw = os.environ.get("MCP_SOCKET_MODE", "0600")
    value = raw.strip() if raw else "0600"
    try:
        return int(value, 8)
    except ValueError as exc:  # pragma: no cover - invalid configuration
        raise RuntimeError(f"Invalid MCP_SOCKET_MODE '{value}'") from exc


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
        pid = os.getpid()
        timestamp = datetime.now(timezone.utc).isoformat()
        path.write_text(f"{pid} {timestamp}\n", encoding="utf-8")
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


def _run_socket(
    socket_path: Path, mode: int, ready_file: Path | None, schemas_dir: str
) -> int:
    def _sigterm_handler(signum: int, _frame: object) -> None:  # pragma: no cover - signal
        raise KeyboardInterrupt

    handlers: list[tuple[int, object]] = []
    try:
        previous = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, _sigterm_handler)
        handlers.append((signal.SIGTERM, previous))
    except Exception:  # pragma: no cover - platform guard
        pass

    server = socket_main.SocketServer(socket_path, mode)
    exit_code = 0
    try:
        server.start()
    except Exception:
        logging.exception("mcp:error reason=socket_start_failed path=%s", socket_path)
        exit_code = 1
    else:
        logging.info(
            "mcp:ready mode=socket path=%s schemas_dir=%s",
            socket_path,
            schemas_dir,
        )
        _write_ready_file(ready_file)
        try:
            server.serve_forever(stdio_main.dispatch)
        except KeyboardInterrupt:
            exit_code = 0
        except Exception:
            logging.exception("mcp:error reason=runtime_failure mode=socket")
            exit_code = 1
        finally:
            logging.info("mcp:shutdown mode=socket")
            server.close()
            _clear_ready_file(ready_file)
    finally:
        for sig, previous in handlers:
            try:
                signal.signal(sig, previous)
            except Exception:
                pass
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
        endpoint = _endpoint()
    except Exception as exc:
        logging.error("mcp:error reason=setup_failed detail=%s", exc)
        sys.exit(2)

    ready_file = _ready_file_path()

    if endpoint == "stdio":
        code = _run_stdio(schemas_dir, ready_file)
    else:
        socket_path = _socket_path()
        try:
            mode = _socket_mode()
        except Exception as exc:
            logging.error("mcp:error reason=setup_failed detail=%s", exc)
            sys.exit(2)
        code = _run_socket(socket_path, mode, ready_file, schemas_dir)
    sys.exit(code)


if __name__ == "__main__":
    main()
