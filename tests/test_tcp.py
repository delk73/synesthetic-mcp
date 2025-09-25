import contextlib
import json
import os
import queue
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from mcp.validate import MAX_BYTES


def _wait_for_line(stream, proc, needle: str, timeout: float = 10.0) -> str:
    deadline = time.time() + timeout
    lines = []
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


def _available_port(host: str = "127.0.0.1") -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((host, 0))
            return probe.getsockname()[1]
    except PermissionError as exc:  # pragma: no cover - sandbox limitation
        pytest.skip(f"tcp sockets unavailable: {exc}")


@pytest.mark.skipif(sys.platform == "win32", reason="unreliable TCP shutdown timing on Windows CI")
def test_tcp_transport_end_to_end(tmp_path):
    host = "127.0.0.1"
    port = _available_port(host)

    ready_file = tmp_path / "mcp.ready"
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    minimal_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema": {"type": "string", "const": "asset"},
        },
        "required": ["schema"],
        "additionalProperties": True,
    }
    (schemas_dir / "synesthetic-asset.schema.json").write_text(json.dumps(minimal_schema))

    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()

    env = os.environ.copy()
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "SYN_EXAMPLES_DIR": str(examples_dir),
            "MCP_ENDPOINT": "tcp",
            "MCP_HOST": host,
            "MCP_PORT": str(port),
            "MCP_READY_FILE": str(ready_file),
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
        assert proc.stderr is not None
        ready_line = _wait_for_line(proc.stderr, proc, "mcp:ready")
        assert "mode=tcp" in ready_line
        assert f"host={host}" in ready_line
        assert "port=" in ready_line
        assert "schemas_dir=" in ready_line
        assert "examples_dir=" in ready_line
        assert "timestamp=" in ready_line

        # derive actual bound port in case the server chose a different one (e.g. port=0)
        bound_port = port
        for part in ready_line.split():
            if part.startswith("port="):
                bound_port = int(part.split("=", 1)[1])
                break

        with socket.create_connection((host, bound_port), timeout=5.0) as client:
            with client.makefile("r", encoding="utf-8") as reader, client.makefile(
                "w", encoding="utf-8"
            ) as writer:
                list_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "list_schemas",
                    "params": {},
                }
                writer.write(json.dumps(list_request) + "\n")
                writer.flush()
                resp = json.loads(reader.readline())
                assert resp["id"] == 1
                assert resp["result"]["ok"] is True

                bad_params = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "get_schema",
                    "params": "oops",
                }
                writer.write(json.dumps(bad_params) + "\n")
                writer.flush()
                invalid_resp = json.loads(reader.readline())
                assert invalid_resp["id"] == 2
                result = invalid_resp.get("result", {})
                assert result.get("ok") is False
                assert result.get("reason") == "validation_failed"
                assert any(err.get("path") == "/params" for err in result.get("errors", []))

                oversized = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "list_schemas",
                    "params": {"blob": "x" * (MAX_BYTES + 1)},
                }
                writer.write(json.dumps(oversized) + "\n")
                writer.flush()
                large_resp = json.loads(reader.readline())
                assert large_resp.get("id") is None
                result_large = large_resp.get("result", {})
                assert result_large.get("reason") == "validation_failed"
                assert any(
                    err.get("msg") == "payload_too_large" for err in result_large.get("errors", [])
                )

        proc.send_signal(signal.SIGINT)
        shutdown_line = _wait_for_line(proc.stderr, proc, "mcp:shutdown")
        assert "mode=tcp" in shutdown_line
        assert f"host={host}" in shutdown_line
        assert "port=" in shutdown_line
        assert "timestamp=" in shutdown_line
        assert "schemas_dir=" in shutdown_line
        assert "examples_dir=" in shutdown_line
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)
        with contextlib.suppress(FileNotFoundError):
            ready_file.unlink()

    assert proc.returncode == 0
    assert not ready_file.exists()


@pytest.mark.skipif(sys.platform == "win32", reason="unreliable TCP shutdown timing on Windows CI")
def test_tcp_allows_multiple_concurrent_clients(tmp_path):
    host = "127.0.0.1"
    port = _available_port(host)

    ready_file = tmp_path / "mcp.ready"
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    minimal_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema": {"type": "string", "const": "asset"},
        },
        "required": ["schema"],
        "additionalProperties": True,
    }
    (schemas_dir / "asset.schema.json").write_text(json.dumps(minimal_schema))

    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    (examples_dir / "asset.valid.json").write_text(
        json.dumps({"schema": "asset", "id": "example"})
    )

    env = os.environ.copy()
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "SYN_EXAMPLES_DIR": str(examples_dir),
            "MCP_ENDPOINT": "tcp",
            "MCP_HOST": host,
            "MCP_PORT": str(port),
            "MCP_READY_FILE": str(ready_file),
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
        assert "mode=tcp" in ready_line
        assert "timestamp=" in ready_line

        bound_port = port
        for part in ready_line.split():
            if part.startswith("port="):
                bound_port = int(part.split("=", 1)[1])
                break

        results = queue.Queue()

        def client_task(name: str, start_id: int, payloads):
            sequence = []
            with socket.create_connection((host, bound_port), timeout=5.0) as client:
                reader = client.makefile("r", encoding="utf-8")
                writer = client.makefile("w", encoding="utf-8")
                for offset, payload in enumerate(payloads):
                    rid = start_id + offset
                    request = {
                        "jsonrpc": "2.0",
                        "id": rid,
                        "method": payload["method"],
                        "params": payload.get("params", {}),
                    }
                    writer.write(json.dumps(request) + "\n")
                    writer.flush()
                    response = json.loads(reader.readline())
                    sequence.append(response)
                    time.sleep(0.05)
            results.put((name, sequence))

        client_payloads = [
            (
                "client_a",
                100,
                [
                    {"method": "list_schemas", "params": {}},
                    {"method": "list_examples", "params": {}},
                ],
            ),
            (
                "client_b",
                200,
                [
                    {"method": "get_schema", "params": {"name": "asset"}},
                    {"method": "list_schemas", "params": {}},
                ],
            ),
        ]

        threads = []
        for name, start_id, payloads in client_payloads:
            thread = threading.Thread(target=client_task, args=(name, start_id, payloads))
            threads.append(thread)

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        collected = {}
        while not results.empty():
            name, sequence = results.get()
            collected[name] = sequence

        assert set(collected.keys()) == {"client_a", "client_b"}
        for name, start_id in (("client_a", 100), ("client_b", 200)):
            sequence = collected[name]
            assert len(sequence) == 2
            for offset, response in enumerate(sequence):
                assert response["id"] == start_id + offset
                result = response.get("result", {})
                assert result.get("ok") is True

        with socket.create_connection((host, bound_port), timeout=5.0) as client:
            reader = client.makefile("r", encoding="utf-8")
            writer = client.makefile("w", encoding="utf-8")
            ping = {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "list_schemas",
                "params": {},
            }
            writer.write(json.dumps(ping) + "\n")
            writer.flush()
            pong = json.loads(reader.readline())
            assert pong["id"] == 999
            assert pong["result"]["ok"] is True

        proc.send_signal(signal.SIGINT)
        shutdown_line = _wait_for_line(proc.stderr, proc, "mcp:shutdown")
        assert "mode=tcp" in shutdown_line
        assert "timestamp=" in shutdown_line
        proc.wait(timeout=5)

        deadline = time.time() + 5
        while time.time() < deadline and ready_file.exists():
            time.sleep(0.05)
        assert not ready_file.exists()
    finally:
        if proc.poll() is None:
            proc.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)
        with contextlib.suppress(FileNotFoundError):
            ready_file.unlink()


@pytest.mark.skipif(sys.platform == "win32", reason="unreliable TCP shutdown timing on Windows CI")
def test_tcp_validate_requests(tmp_path):
    host = "127.0.0.1"
    port = _available_port(host)

    ready_file = tmp_path / "mcp.ready"
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    minimal_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema": {"type": "string", "const": "synesthetic-asset"},
            "id": {"type": "string", "minLength": 1},
        },
        "required": ["schema", "id"],
        "additionalProperties": False,
    }
    (schemas_dir / "synesthetic-asset.schema.json").write_text(json.dumps(minimal_schema))

    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()

    asset = {"schema": "synesthetic-asset", "id": "asset-123"}
    (examples_dir / "asset.valid.json").write_text(json.dumps(asset))

    env = os.environ.copy()
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "SYN_EXAMPLES_DIR": str(examples_dir),
            "MCP_ENDPOINT": "tcp",
            "MCP_HOST": host,
            "MCP_PORT": str(port),
            "MCP_READY_FILE": str(ready_file),
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
        assert "mode=tcp" in ready_line

        bound_port = port
        for part in ready_line.split():
            if part.startswith("port="):
                bound_port = int(part.split("=", 1)[1])
                break

        validate_request = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "validate_asset",
            "params": {"asset": asset, "schema": "synesthetic-asset"},
        }
        alias_request = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "validate",
            "params": {"asset": asset, "schema": "synesthetic-asset"},
        }

        with socket.create_connection((host, bound_port), timeout=5.0) as client:
            reader = client.makefile("r", encoding="utf-8")
            writer = client.makefile("w", encoding="utf-8")

            writer.write(json.dumps(validate_request) + "\n")
            writer.flush()
            response = reader.readline()
            if not response:
                raise AssertionError("no validate_asset response received")
            payload = json.loads(response)
            assert payload["id"] == 10
            result = payload.get("result", {})
            assert result.get("ok") is True
            assert result.get("errors") == []

            writer.write(json.dumps(alias_request) + "\n")
            writer.flush()
            alias_response = reader.readline()
            if not alias_response:
                raise AssertionError("no validate alias response received")
            payload_alias = json.loads(alias_response)
            assert payload_alias["id"] == 11
            alias_result = payload_alias.get("result", {})
            assert alias_result.get("ok") is True
            assert alias_result.get("errors") == []

        warning_line = _wait_for_line(proc.stderr, proc, "deprecated_alias")
        assert "method=validate" in warning_line

        proc.send_signal(signal.SIGINT)
        shutdown_line = _wait_for_line(proc.stderr, proc, "mcp:shutdown")
        assert "mode=tcp" in shutdown_line
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)
        with contextlib.suppress(FileNotFoundError):
            ready_file.unlink()

    assert proc.returncode == 0


@pytest.mark.skipif(sys.platform == "win32", reason="unreliable TCP shutdown timing on Windows CI")
def test_tcp_ephemeral_port_logs_bound_port(tmp_path):
    host = "127.0.0.1"

    ready_file = tmp_path / "mcp.ready"
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    minimal_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema": {"type": "string", "const": "asset"},
        },
        "required": ["schema"],
        "additionalProperties": True,
    }
    (schemas_dir / "asset.schema.json").write_text(json.dumps(minimal_schema))

    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()

    env = os.environ.copy()
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "SYN_SCHEMAS_DIR": str(schemas_dir),
            "SYN_EXAMPLES_DIR": str(examples_dir),
            "MCP_ENDPOINT": "tcp",
            "MCP_HOST": host,
            "MCP_PORT": "0",
            "MCP_READY_FILE": str(ready_file),
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
        assert "mode=tcp" in ready_line
        assert "port=" in ready_line

        bound_port = None
        for part in ready_line.split():
            if part.startswith("port="):
                bound_port = int(part.split("=", 1)[1])
                break

        assert bound_port is not None
        assert bound_port != 0

        with socket.create_connection((host, bound_port), timeout=5.0) as client:
            reader = client.makefile("r", encoding="utf-8")
            writer = client.makefile("w", encoding="utf-8")
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "list_schemas",
                "params": {},
            }
            writer.write(json.dumps(request) + "\n")
            writer.flush()
            response = json.loads(reader.readline())
            assert response["id"] == 1
            assert response["result"]["ok"] is True

        proc.send_signal(signal.SIGINT)
        shutdown_line = _wait_for_line(proc.stderr, proc, "mcp:shutdown")
        assert "port=" in shutdown_line
        assert f"port={bound_port}" in shutdown_line
        proc.wait(timeout=5)

        deadline = time.time() + 5
        while time.time() < deadline and ready_file.exists():
            time.sleep(0.05)
        assert not ready_file.exists()
    finally:
        if proc.poll() is None:
            proc.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)
        with contextlib.suppress(FileNotFoundError):
            ready_file.unlink()
