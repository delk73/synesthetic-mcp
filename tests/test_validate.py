import json
from pathlib import Path

import pytest

from mcp.core import get_schema
from mcp.validate import validate_asset


def _load(path: str):
    return json.loads(Path(path).read_text())


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


def test_validate_invalid_sorted_errors():
    # Deliberately invalid object for nested-synesthetic-asset (alias)
    asset = {"name": "", "extra": True}
    res = validate_asset(asset, "nested-synesthetic-asset")
    assert res["ok"] is False
    # ensure deterministic order
    paths = [e["path"] for e in res["errors"]]
    assert paths == sorted(paths)
