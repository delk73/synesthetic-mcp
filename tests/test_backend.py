import json
import os
from pathlib import Path

import httpx

from mcp.backend import populate_backend
from mcp.core import list_examples, get_example


CANONICAL_PREFIX = "https://delk73.github.io/synesthetic-schemas/schema/0.7.3/"
SCHEMA_URI = f"{CANONICAL_PREFIX}asset.schema.json"


def _client_for(status: int, payload: dict, *, expect_path: str | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if expect_path is not None:
            assert request.url.path == expect_path
        return httpx.Response(status, json=payload)

    transport = httpx.MockTransport(handler)
    return httpx.Client(base_url="https://backend.example", transport=transport, timeout=5.0)


def test_backend_disabled_without_env(monkeypatch):
    monkeypatch.delenv("SYN_BACKEND_URL", raising=False)
    res = populate_backend({"$schema": SCHEMA_URI, "id": "abc"}, validate_first=False)
    assert res["ok"] is False and res["reason"] == "unsupported"
    assert "detail" in res and isinstance(res["detail"], str)


def test_backend_success(monkeypatch):
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")
    client = _client_for(201, {"id": "xyz"}, expect_path="/synesthetic-assets/")
    res = populate_backend(
        {"$schema": SCHEMA_URI, "id": "abc", "name": "A"},
        client=client,
        validate_first=False,
    )
    assert res["ok"] is True
    assert res["asset_id"] == "xyz"


def test_backend_assets_path_override(monkeypatch):
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")
    monkeypatch.setenv("SYN_BACKEND_ASSETS_PATH", "/custom-assets/")
    client = _client_for(200, {"id": "override"}, expect_path="/custom-assets/")

    res = populate_backend(
        {"$schema": SCHEMA_URI, "id": "abc"},
        client=client,
        validate_first=False,
    )

    assert res["ok"] is True
    assert res["asset_id"] == "override"



def test_backend_error(monkeypatch):
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")
    client = _client_for(500, {"error": "fail"})
    res = populate_backend(
        {"$schema": SCHEMA_URI, "id": "abc", "name": "A"},
        client=client,
        validate_first=False,
    )
    assert res["ok"] is False
    assert res["reason"] == "backend_error"


def test_backend_payload_limit(monkeypatch):
    # Enable backend so payload size check is evaluated
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")
    oversized = {"$schema": SCHEMA_URI, "blob": "y" * (1_200_000)}
    # No client needed; size check happens before any network calls
    res = populate_backend(oversized, validate_first=False)
    assert res["ok"] is False
    # Consistent with validate path: reason is validation_failed and error indicates payload_too_large
    assert res.get("reason") == "validation_failed"
    assert any(e.get("msg") == "payload_too_large" for e in res.get("errors", []))


def _seed_backend_fixture(tmp_path: Path) -> None:
    schemas = tmp_path / "schemas"
    examples = tmp_path / "examples"
    schemas.mkdir()
    examples.mkdir()

    (schemas / "asset.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://example.test/asset.schema.json",
                "type": "object",
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "name": {"type": "string", "minLength": 1},
                },
                "required": ["id", "name"],
                "additionalProperties": False,
            }
        )
    )

    (examples / "asset.valid.json").write_text(
        json.dumps(
            {
                "$schema": SCHEMA_URI,
                "id": "example-id",
                "name": "Example",
            }
        )
    )


def test_backend_validation_default_posts(monkeypatch, tmp_path: Path):
    _seed_backend_fixture(tmp_path)

    monkeypatch.setenv("SYN_SCHEMAS_DIR", str(tmp_path / "schemas"))
    monkeypatch.setenv("SYN_EXAMPLES_DIR", str(tmp_path / "examples"))
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")

    listing = list_examples("*")
    assert listing["ok"] and listing["examples"]
    first = listing["examples"][0]
    example = get_example(Path(first["path"]).name)
    assert example["ok"] and example["validated"] is True
    asset = example["example"]

    called = {"post": False}

    def handler(request: httpx.Request) -> httpx.Response:
        called["post"] = True
        return httpx.Response(201, json={"id": "validated"})

    client = httpx.Client(
        base_url="https://backend.example",
        transport=httpx.MockTransport(handler),
        timeout=5.0,
    )

    res = populate_backend(asset, client=client)
    client.close()

    assert res["ok"] is True
    assert called["post"] is True


def test_backend_validation_default_blocks_invalid(monkeypatch, tmp_path: Path):
    _seed_backend_fixture(tmp_path)

    monkeypatch.setenv("SYN_SCHEMAS_DIR", str(tmp_path / "schemas"))
    monkeypatch.setenv("SYN_EXAMPLES_DIR", str(tmp_path / "examples"))
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")

    listing = list_examples("*")
    first = listing["examples"][0]
    example = get_example(Path(first["path"]).name)
    asset = dict(example["example"])
    asset.pop("id", None)

    called = {"post": False}

    def handler(request: httpx.Request) -> httpx.Response:
        called["post"] = True
        return httpx.Response(201, json={"id": "should-not-run"})

    client = httpx.Client(
        base_url="https://backend.example",
        transport=httpx.MockTransport(handler),
        timeout=5.0,
    )

    res = populate_backend(asset, client=client)
    client.close()

    assert res["ok"] is False
    assert res.get("reason") == "validation_failed"
    assert called["post"] is False

def test_backend_assets_path_normalization(monkeypatch):
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")
    monkeypatch.setenv("SYN_BACKEND_ASSETS_PATH", "custom-assets-no-slash")
    client = _client_for(200, {"id": "normalized"}, expect_path="/custom-assets-no-slash")

    res = populate_backend(
        {"$schema": SCHEMA_URI, "id": "abc"},
        client=client,
        validate_first=False,
    )

    assert res["ok"] is True
    assert res["asset_id"] == "normalized"


def test_backend_http_error_maps_to_503(monkeypatch):
    monkeypatch.setenv("SYN_BACKEND_URL", "https://backend.example")

    def boom(self, path, json=None, **kwargs):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(httpx.Client, "post", boom)

    res = populate_backend({"$schema": SCHEMA_URI}, validate_first=False)

    assert res["ok"] is False
    assert res["reason"] == "backend_error"
    assert res["status"] == 503
    assert res["detail"] == "HTTPError"
