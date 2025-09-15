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


def test_backend_assets_path_override(monkeypatch):
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")
    monkeypatch.setenv("SYN_BACKEND_ASSETS_PATH", "/custom-assets/")
    client = _client_for(200, {"id": "override"}, expect_path="/custom-assets/")

    res = populate_backend({"schema": "asset", "id": "abc"}, client=client, validate_first=False)

    assert res["ok"] is True
    assert res["asset_id"] == "override"


def test_backend_error(monkeypatch):
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")
    client = _client_for(500, {"error": "fail"})
    res = populate_backend({"schema": "asset", "id": "abc", "name": "A"}, client=client, validate_first=False)
    assert res["ok"] is False
    assert res["reason"] == "backend_error"


def test_backend_payload_limit(monkeypatch):
    # Enable backend so payload size check is evaluated
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")
    oversized = {"blob": "y" * (1_200_000)}
    # No client needed; size check happens before any network calls
    res = populate_backend(oversized, validate_first=False)
    assert res["ok"] is False
    # Consistent with validate path: reason is validation_failed and error indicates payload_too_large
    assert res.get("reason") == "validation_failed"
    assert any(e.get("msg") == "payload_too_large" for e in res.get("errors", []))
