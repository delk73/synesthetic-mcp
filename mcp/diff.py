from __future__ import annotations

from typing import Any, Dict, List, Tuple


PatchOp = Dict[str, Any]


def _join(path: List[str]) -> str:
    if not path:
        return "/"
    return "/" + "/".join(path)


def generate_patch(base: Any, new: Any, path: List[str] | None = None) -> List[PatchOp]:
    """Generate a minimal RFC6902-like patch (add/remove/replace) between two JSON values.

    This is intentionally simple and deterministic for small assets.
    """
    if path is None:
        path = []
    ops: List[PatchOp] = []

    if type(base) != type(new):
        ops.append({"op": "replace", "path": _join(path), "value": new})
        return ops

    if isinstance(base, dict):
        base_keys = set(base.keys())
        new_keys = set(new.keys())

        # removed keys
        for k in sorted(base_keys - new_keys):
            ops.append({"op": "remove", "path": _join(path + [k])})

        # added keys
        for k in sorted(new_keys - base_keys):
            ops.append({"op": "add", "path": _join(path + [k]), "value": new[k]})

        # modified keys
        for k in sorted(base_keys & new_keys):
            ops.extend(generate_patch(base[k], new[k], path + [k]))
        return ops

    if isinstance(base, list):
        # naive list diff: replace if different length or any differing item
        if len(base) != len(new):
            ops.append({"op": "replace", "path": _join(path), "value": new})
            return ops
        changed = False
        for i, (a, b) in enumerate(zip(base, new)):
            sub = generate_patch(a, b, path + [str(i)])
            if sub:
                changed = True
                ops.extend(sub)
        if changed:
            return ops
        return []

    # primitive values
    if base != new:
        ops.append({"op": "replace", "path": _join(path), "value": new})
    return ops


def apply_patch(doc: Any, patch: List[PatchOp]) -> Any:
    """Apply a minimal subset of RFC6902 patch ops (add/remove/replace)."""
    from copy import deepcopy

    def get_parent_and_key(root: Any, path: str) -> Tuple[Any, str]:
        if path == "/":
            return (None, "")
        parts = [p for p in path.split("/") if p]
        cur = root
        for p in parts[:-1]:
            key = int(p) if isinstance(cur, list) else p
            cur = cur[key]
        last = parts[-1]
        return cur, last

    out = deepcopy(doc)
    for op in patch:
        kind = op["op"]
        path = op["path"]
        if kind == "replace":
            if path == "/":
                out = op["value"]
            else:
                parent, key = get_parent_and_key(out, path)
                if isinstance(parent, list):
                    parent[int(key)] = op["value"]
                else:
                    parent[key] = op["value"]
        elif kind == "add":
            parent, key = get_parent_and_key(out, path)
            if isinstance(parent, list):
                if key == "-":
                    parent.append(op["value"])  # pragma: no cover
                else:
                    parent.insert(int(key), op["value"])  # pragma: no cover
            else:
                parent[key] = op["value"]
        elif kind == "remove":
            parent, key = get_parent_and_key(out, path)
            if isinstance(parent, list):
                parent.pop(int(key))
            else:
                parent.pop(key, None)
        else:  # pragma: no cover - unsupported ops by design
            raise ValueError(f"Unsupported op: {kind}")
    return out

