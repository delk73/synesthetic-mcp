import json
import os
from pathlib import Path

import httpx

from mcp.backend import populate_backend


def _client_for(status: int, payload: dict, *, expect_path: str | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if expect_path is not None:
            assert request.url.path == expect_path
        return httpx.Response(status, json=payload)

    transport = httpx.MockTransport(handler)
    return httpx.Client(base_url="https://backend.example", transport=transport, timeout=5.0)


def test_backend_disabled_without_env(monkeypatch):
    monkeypatch.delenv("SYN_BACKEND_URL", raising=False)
    res = populate_backend({"schema": "asset", "id": "abc"}, validate_first=False)
    assert res["ok"] is False and res["reason"] == "unsupported"
    assert "msg" in res and isinstance(res["msg"], str)


def test_backend_success(monkeypatch):
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")
    client = _client_for(201, {"id": "xyz"}, expect_path="/synesthetic-assets/")
    res = populate_backend({"schema": "asset", "id": "abc", "name": "A"}, client=client, validate_first=False)
    assert res["ok"] is True
    assert res["asset_id"] == "xyz"


def test_backend_error(monkeypatch):
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")
    client = _client_for(500, {"error": "fail"})
    res = populate_backend({"schema": "asset", "id": "abc", "name": "A"}, client=client, validate_first=False)
    assert res["ok"] is False
    assert res["reason"] == "backend_error"
