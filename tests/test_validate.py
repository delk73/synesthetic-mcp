import json
from pathlib import Path

import pytest

from mcp.core import get_example, get_schema
from mcp.validate import MAX_BYTES, validate_asset, validate_many

CANONICAL_PREFIX = "https://delk73.github.io/synesthetic-schemas/schema/0.7.3/"
CANONICAL_ASSET_SCHEMA = f"{CANONICAL_PREFIX}asset.schema.json"
CANONICAL_SYNESTHETIC_SCHEMA = f"{CANONICAL_PREFIX}synesthetic-asset.schema.json"


def _load(path: str):
    # If it's a relative path, resolve it relative to the examples directory
    if not Path(path).is_absolute():
        from mcp.core import _examples_dir
        path = str(_examples_dir() / path)
    return json.loads(Path(path).read_text())


def test_get_schema_not_found():
    res = get_schema("missing-schema")
    assert res == {"ok": False, "reason": "not_found"}


def test_get_schema_and_validate_valid():
    s = get_schema("synesthetic-asset")
    assert s["ok"] is True
    # Canonical schema (from submodule) does not define a top-level version
    assert s["version"] == ""

    # Validate a canonical example from the submodule
    asset = _load("SynestheticAsset_Example1.json")
    res = validate_asset(asset)
    assert res["ok"] is True
    assert res["errors"] == []


def test_get_example_invalid_returns_error(tmp_path, monkeypatch):
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    invalid_example_path = examples_dir / "invalid_example.json"
    invalid_example_path.write_text(
        json.dumps(
            {
                "$schema": CANONICAL_SYNESTHETIC_SCHEMA,
                "name": "",
                "extra": True,
            }
        )
    )

    monkeypatch.setenv("SYN_EXAMPLES_DIR", str(examples_dir))

    res = get_example("invalid_example.json")

    assert res["ok"] is False
    assert res["reason"] == "validation_failed"


def test_validate_invalid_sorted_errors():
    # Deliberately invalid object for nested-synesthetic-asset (alias)
    asset = {
        "$schema": CANONICAL_SYNESTHETIC_SCHEMA,
        "name": "",
        "extra": True,
    }
    res = validate_asset(asset)
    assert res["ok"] is False and res.get("reason") == "validation_failed"
    # Ensure deterministic order
    paths = [e["path"] for e in res["errors"]]
    assert paths == sorted(paths)


def test_validate_payload_limit():
    # Construct an object with a string payload well over 1 MiB
    oversized = {
        "$schema": CANONICAL_SYNESTHETIC_SCHEMA,
        "blob": "x" * 1_200_000,
    }
    res = validate_asset(oversized)
    assert res["ok"] is False
    # Spec/code use reason 'validation_failed' with a payload_too_large error
    assert res.get("reason") == "validation_failed"
    assert any(e.get("msg") == "payload_too_large" for e in res.get("errors", []))


def test_validate_asset_empty_schema_marker():
    """Regression: validate_asset must fail when $schema marker is empty."""
    asset = {"$schema": "", "type": "synesthetic-asset", "id": "dummy"}

    result = validate_asset(asset)

    assert result["ok"] is False
    assert result["reason"] == "validation_failed"
    assert isinstance(result.get("errors"), list)
    assert result["errors"] == [
        {"path": "/$schema", "msg": "top-level $schema is required"}
    ]


def test_validate_many_mixed_results(tmp_path, monkeypatch):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    minimal = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {"id": {"type": "string", "minLength": 1}},
        "required": ["id"],
        "additionalProperties": False,
    }
    (schemas_dir / "asset.schema.json").write_text(json.dumps(minimal))

    monkeypatch.setenv("SYN_SCHEMAS_DIR", str(schemas_dir))

    assets = [
        {"$schema": CANONICAL_ASSET_SCHEMA, "id": "good"},
        {"$schema": CANONICAL_ASSET_SCHEMA, "id": ""},
    ]

    res = validate_many(assets)

    assert res["ok"] is False
    assert len(res["results"]) == 2
    assert res["results"][0]["ok"] is True
    assert res["results"][1]["ok"] is False
    assert res["results"][1]["reason"] == "validation_failed"


def test_validate_many_respects_max_batch(tmp_path, monkeypatch):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    minimal = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {"id": {"type": "string", "minLength": 1}},
        "required": ["id"],
        "additionalProperties": False,
    }
    (schemas_dir / "asset.schema.json").write_text(json.dumps(minimal))

    monkeypatch.setenv("SYN_SCHEMAS_DIR", str(schemas_dir))
    monkeypatch.setenv("MCP_MAX_BATCH", "1")

    assets = [
        {"$schema": CANONICAL_ASSET_SCHEMA, "id": "first"},
        {"$schema": CANONICAL_ASSET_SCHEMA, "id": "second"},
    ]

    res = validate_many(assets)

    assert res["ok"] is False
    assert res["reason"] == "unsupported"
    assert res["detail"] == "batch_too_large"
    assert res["limit"] == 1


def test_validate_many_rejects_large_payload(tmp_path, monkeypatch):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    minimal = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "id": {"type": "string", "minLength": 1},
            "name": {"type": "string", "minLength": 1},
        },
        "required": ["id", "name"],
        "additionalProperties": False,
    }
    (schemas_dir / "asset.schema.json").write_text(json.dumps(minimal))

    monkeypatch.setenv("SYN_SCHEMAS_DIR", str(schemas_dir))

    gigantic_name = "x" * (MAX_BYTES + 512)
    asset = {
        "$schema": CANONICAL_ASSET_SCHEMA,
        "id": "oversized",
        "name": gigantic_name,
    }
    encoded_size = len(json.dumps(asset).encode("utf-8"))
    assert encoded_size > MAX_BYTES

    res = validate_many([asset])

    assert res["ok"] is False
    assert len(res["results"]) == 1
    first = res["results"][0]
    assert first["ok"] is False
    assert first["reason"] == "validation_failed"
    assert any(err.get("msg") == "payload_too_large" for err in first.get("errors", []))


def test_validate_asset_rejects_missing_dollar_schema():
    asset = {"id": "asset-1"}
    res = validate_asset(asset)
    assert res["ok"] is False
    assert res["reason"] == "validation_failed"
    assert res["errors"][0]["path"] == "/$schema"


def test_validate_asset_accepts_relative_schema_marker():
    asset = _load("SynestheticAsset_Example1.json")
    asset["$schema"] = "synesthetic-asset.schema.json"

    res = validate_asset(asset)

    assert res["ok"] is True
    assert res["errors"] == []


def test_validate_asset_accepts_legacy_host_marker():
    asset = _load("SynestheticAsset_Example1.json")
    asset["$schema"] = CANONICAL_SYNESTHETIC_SCHEMA.replace(
        "https://delk73.github.io/synesthetic-schemas/schema/",
        "https://schemas.synesthetic.dev/",
    )

    res = validate_asset(asset)

    assert res["ok"] is True
    assert res["errors"] == []


def test_validate_asset_rejects_unknown_schema_host():
    asset = {"$schema": "https://example.com/schema/asset.schema.json", "id": "asset-1"}

    res = validate_asset(asset)

    assert res["ok"] is False
    assert res["reason"] == "validation_failed"
    assert any(
        err.get("msg") == "schema_must_use_canonical_host" for err in res.get("errors", [])
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"$schema": CANONICAL_ASSET_SCHEMA, "schema": "legacy"},
        {"$schema": CANONICAL_ASSET_SCHEMA, "$schemaRef": "legacy"},
    ],
)
def test_validate_asset_rejects_legacy_keys(payload):
    res = validate_asset(payload)
    assert res["ok"] is False
    assert res["reason"] == "validation_failed"
    assert res["errors"][0]["path"] == "/$schema"


def test_remote_schema_cache_fallback(monkeypatch, tmp_path):
    from mcp import validate
    monkeypatch.setenv('LABS_SCHEMA_BASE', 'https://delk73.github.io/synesthetic-schemas/schema/')
    monkeypatch.setenv('LABS_SCHEMA_VERSION', '0.7.3')
    test_url = 'https://delk73.github.io/synesthetic-schemas/schema/0.7.3/synesthetic-asset.schema.json'
    tmp_cache = tmp_path / 'cache'
    monkeypatch.setenv('LABS_SCHEMA_CACHE_DIR', str(tmp_cache))
    result = validate._fetch_canonical_schema(test_url, 'synesthetic-asset.schema.json')
    assert isinstance(result, dict)
    assert tmp_cache.joinpath('synesthetic-asset.schema.json').exists()
