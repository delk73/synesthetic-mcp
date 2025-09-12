import json
from pathlib import Path

from mcp import diff
from mcp import validate as v
from mcp.core import get_example, get_schema, list_examples, list_schemas


FIX = Path("tests/fixtures")


def test_list_and_get_schema():
    schemas = list_schemas()
    assert any(s.name == "SynestheticAsset" for s in schemas)
    schema = get_schema("SynestheticAsset")
    assert schema["title"] == "SynestheticAsset"


def test_list_and_get_example_and_validate():
    exs = list_examples()
    assert exs
    ex = get_example(exs[0])
    schema = json.loads((FIX / "schemas/asset.schema.json").read_text())
    res = v.validate_asset(ex, schema)
    assert set(res.keys()) == {"ok", "errors"}


def test_diff_tool_roundtrip():
    base = {"a": 1, "b": {"c": 3}}
    new = {"a": 2, "b": {"c": 3}}
    patch = diff.generate_patch(base, new)
    out = diff.apply_patch(base, patch)
    assert out == new

