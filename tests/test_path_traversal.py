import json
from pathlib import Path

from mcp.core import get_example, get_schema
from mcp.validate import validate_asset

CANONICAL_PREFIX = "https://delk73.github.io/synesthetic-schemas/schema/0.7.3/"
CANONICAL_ASSET_SCHEMA = f"{CANONICAL_PREFIX}asset.schema.json"


_MINIMAL_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "id": {"type": "string", "minLength": 1},
    },
    "required": ["id"],
    "additionalProperties": False,
}


def _seed_roots(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    (schemas_dir / "asset.schema.json").write_text(json.dumps(_MINIMAL_SCHEMA))

    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()

    monkeypatch.setenv("SYN_SCHEMAS_DIR", str(schemas_dir))
    monkeypatch.setenv("SYN_EXAMPLES_DIR", str(examples_dir))

    return schemas_dir, examples_dir


def test_get_schema_rejects_traversal(monkeypatch, tmp_path):
    schemas_dir, _ = _seed_roots(tmp_path, monkeypatch)

    res = get_schema("../asset")

    assert res["ok"] is False
    assert res["reason"] == "validation_failed"
    assert any(err["msg"] == "invalid_path" for err in res["errors"])

    valid = get_schema("asset")
    assert valid["ok"] is True

    # Absolute path pointing outside the root should be rejected
    absolute_name = str((tmp_path / "elsewhere").resolve())
    res_abs = get_schema(absolute_name)
    assert res_abs["ok"] is False
    assert res_abs["reason"] == "validation_failed"


def test_get_example_rejects_traversal(monkeypatch, tmp_path):
    _, examples_dir = _seed_roots(tmp_path, monkeypatch)

    nested = examples_dir / "nested"
    nested.mkdir()
    example_path = nested / "asset.json"
    example_path.write_text(
        json.dumps({"$schema": CANONICAL_ASSET_SCHEMA, "id": "example"})
    )

    res = get_example("../asset.json")
    assert res["ok"] is False
    assert res["reason"] == "validation_failed"
    assert any(err["msg"] == "invalid_path" for err in res["errors"])

    res_abs = get_example(str(example_path))
    assert res_abs["ok"] is False
    assert res_abs["reason"] == "validation_failed"

    valid = get_example("nested/asset.json")
    assert valid["ok"] is True
    assert valid["schema"] == "asset"


def test_validate_asset_schema_path_guard(monkeypatch, tmp_path):
    _seed_roots(tmp_path, monkeypatch)

    asset = {"$schema": CANONICAL_ASSET_SCHEMA, "id": "ok"}

    invalid = dict(asset, **{"$schema": f"{CANONICAL_PREFIX}../asset.schema.json"})

    res = validate_asset(invalid)
    assert res["ok"] is False
    assert res["reason"] == "validation_failed"
    assert any(err["msg"] == "schema_outside_configured_root" for err in res["errors"])

    valid = validate_asset(asset)
    assert valid["ok"] is True
    assert valid.get("errors") == []
