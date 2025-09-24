import json
from pathlib import Path

import pytest

from mcp.core import get_example, get_schema
from mcp.validate import MAX_BYTES, validate_asset, validate_many


def _load(path: str):
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
    asset = _load("libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json")
    res = validate_asset(asset, "nested-synesthetic-asset")
    assert res["ok"] is True
    assert res["errors"] == []


def test_get_example_invalid_returns_error(tmp_path, monkeypatch):
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    invalid_example_path = examples_dir / "invalid_example.json"
    invalid_example_path.write_text(json.dumps({"schema": "synesthetic-asset", "name": "", "extra": True}))

    monkeypatch.setenv("SYN_EXAMPLES_DIR", str(examples_dir))

    res = get_example("invalid_example.json")

    assert res["ok"] is False
    assert res["reason"] == "validation_failed"


def test_validate_invalid_sorted_errors():
    # Deliberately invalid object for nested-synesthetic-asset (alias)
    asset = {"name": "", "extra": True}
    res = validate_asset(asset, "nested-synesthetic-asset")
    assert res["ok"] is False and res.get("reason") == "validation_failed"
    # Ensure deterministic order
    paths = [e["path"] for e in res["errors"]]
    assert paths == sorted(paths)


def test_validate_payload_limit():
    # Construct an object with a string payload well over 1 MiB
    oversized = {"blob": "x" * 1_200_000}
    res = validate_asset(oversized, "nested-synesthetic-asset")
    assert res["ok"] is False
    # Spec/code use reason 'validation_failed' with a payload_too_large error
    assert res.get("reason") == "validation_failed"
    assert any(e.get("msg") == "payload_too_large" for e in res.get("errors", []))


def test_validate_asset_empty_schema():
    """Regression: validate_asset must fail with reason=validation_failed if schema is empty."""
    asset = {"type": "synesthetic-asset", "id": "dummy"}

    result = validate_asset(asset, schema="")

    assert result["ok"] is False
    assert result["reason"] == "validation_failed"
    assert isinstance(result.get("errors"), list)
    assert result["errors"] == [{"path": "", "msg": "schema_required"}]


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

    assets = [{"id": "good"}, {"id": ""}]

    res = validate_many(assets, "asset")

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

    assets = [{"id": "first"}, {"id": "second"}]

    res = validate_many(assets, "asset")

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
    asset = {"id": "oversized", "name": gigantic_name}
    encoded_size = len(json.dumps(asset).encode("utf-8"))
    assert encoded_size > MAX_BYTES

    res = validate_many([asset], "asset")

    assert res["ok"] is False
    assert len(res["results"]) == 1
    first = res["results"][0]
    assert first["ok"] is False
    assert first["reason"] == "validation_failed"
    assert any(err.get("msg") == "payload_too_large" for err in first.get("errors", []))
