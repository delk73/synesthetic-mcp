import json
from pathlib import Path

import pytest

from mcp.core import get_schema
from mcp.validate import validate_asset


def _load(path: str):
    return json.loads(Path(path).read_text())


def test_get_schema_and_validate_valid():
    s = get_schema("asset")
    assert s["ok"] is True
    assert s["version"] == "1.0.0"

    asset = _load("tests/fixtures/examples/asset.valid.json")
    res = validate_asset(asset, "asset")
    assert res["ok"] is True
    assert res["errors"] == []


def test_validate_invalid_sorted_errors():
    asset = _load("tests/fixtures/examples/asset.invalid.json")
    res = validate_asset(asset, "asset")
    assert res["ok"] is False
    # ensure deterministic order
    paths = [e["path"] for e in res["errors"]]
    assert paths == sorted(paths)

