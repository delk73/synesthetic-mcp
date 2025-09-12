from mcp import diff


def test_generate_and_apply_patch_primitives():
    base = {"a": 1}
    new = {"a": 2}
    patch = diff.generate_patch(base, new)
    assert {op["op"] for op in patch} == {"replace"}
    out = diff.apply_patch(base, patch)
    assert out == new


def test_generate_and_apply_patch_objects():
    base = {"a": 1, "b": {"c": 3}}
    new = {"a": 1, "b": {"c": 4, "d": 5}, "e": 9}
    patch = diff.generate_patch(base, new)
    ops = [op["op"] for op in patch]
    assert "remove" not in ops  # no removals here
    out = diff.apply_patch(base, patch)
    assert out == new


def test_generate_and_apply_patch_lists():
    base = {"xs": [1, 2, 3]}
    new = {"xs": [1, 2, 4]}
    patch = diff.generate_patch(base, new)
    out = diff.apply_patch(base, patch)
    assert out == new

