import json
from pathlib import Path

from mcp import validate
from mcp.core import get_schema


FIX = Path("tests/fixtures")


def test_validate_valid_asset():
    schema = json.loads((FIX / "schemas/asset.schema.json").read_text())
    asset = json.loads((FIX / "examples/asset.valid.json").read_text())
    res = validate.validate_asset(asset, schema)
    assert res["ok"] is True
    assert res["errors"] == []


def test_validate_invalid_asset():
    schema = json.loads((FIX / "schemas/asset.schema.json").read_text())
    bad = json.loads((FIX / "examples/asset.invalid.json").read_text())
    res = validate.validate_asset(bad, schema)
    assert res["ok"] is False
    assert isinstance(res["errors"], list) and res["errors"]

