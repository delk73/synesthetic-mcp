from mcp.diff import diff_assets


def test_idempotent_diff():
    obj = {"id": "abc", "name": "X", "tags": ["a", "b"]}
    res = diff_assets(obj, obj)
    assert res["ok"] is True
    assert res["patch"] == []


def test_list_replacement_single_replace():
    base = {"tags": ["a", "b", "c"]}
    new = {"tags": ["a", "x", "c", "d"]}
    res = diff_assets(base, new)
    patch = res["patch"]
    # Deterministically replace the array as a whole
    assert patch == [
        {"op": "replace", "path": "/tags", "value": new["tags"]},
    ]

