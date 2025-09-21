from pathlib import Path

import pytest

from mcp.core import (
    SUBMODULE_SCHEMAS_DIR,
    SUBMODULE_EXAMPLES_DIR,
    list_examples,
    list_schemas,
    get_example,
)
from mcp.validate import validate_asset


SUB_SCHEMAS = Path(SUBMODULE_SCHEMAS_DIR)
SUB_EXAMPLES = Path(SUBMODULE_EXAMPLES_DIR)


@pytest.mark.skipif(
    not (SUB_SCHEMAS.is_dir() and SUB_EXAMPLES.is_dir()),
    reason="synesthetic-schemas submodule not present",
)
def test_uses_submodule_when_present(monkeypatch):
    # Ensure env overrides are cleared so defaults apply
    monkeypatch.delenv("SYN_SCHEMAS_DIR", raising=False)
    monkeypatch.delenv("SYN_EXAMPLES_DIR", raising=False)

    ls = list_schemas()
    assert ls["ok"] and len(ls["schemas"]) >= 1
    assert any(str(SUBMODULE_SCHEMAS_DIR) in s["path"] for s in ls["schemas"])
    assert all(s["path"].endswith(".json") for s in ls["schemas"])
    assert all(not s["path"].endswith(".schema.json") for s in ls["schemas"])
    # deterministic ordering by name/version/path
    schemas_sorted = sorted(ls["schemas"], key=lambda x: (x["name"], x["version"], x["path"]))
    assert ls["schemas"] == schemas_sorted

    le = list_examples("all")
    assert le["ok"] and len(le["examples"]) >= 1
    assert any(str(SUBMODULE_EXAMPLES_DIR) in e["path"] for e in le["examples"])
    # deterministic ordering by component/path
    examples_sorted = sorted(le["examples"], key=lambda x: (x["component"], x["path"]))
    assert le["examples"] == examples_sorted

    legacy = list_examples("*")
    assert legacy == le

    # Try loading and validating the first example found
    first = le["examples"][0]
    ex = get_example(Path(first["path"]).name)
    assert ex["ok"] is True and ex["example"] is not None
    res = validate_asset(ex["example"], ex["schema"])
    assert res["ok"] is True
