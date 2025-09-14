from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _escape_token(tok: str) -> str:
    return tok.replace("~", "~0").replace("/", "~1")


def _join(path: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{path}/{key}"
    return f"{path}/{_escape_token(str(key))}"


def _collect(base: Any, new: Any, path: str, ops: List[Dict[str, Any]]):
    # identical
    if base == new:
        return

    # dicts: recurse by sorted keys
    if isinstance(base, dict) and isinstance(new, dict):
        base_keys = set(base.keys())
        new_keys = set(new.keys())
        for k in sorted(base_keys - new_keys):
            ops.append({"op": "remove", "path": _join(path, k)})
        for k in sorted(new_keys - base_keys):
            ops.append({"op": "add", "path": _join(path, k), "value": new[k]})
        for k in sorted(base_keys & new_keys):
            _collect(base[k], new[k], _join(path, k), ops)
        return

    # lists: deterministic single replace when different
    if isinstance(base, list) and isinstance(new, list):
        ops.append({"op": "replace", "path": path, "value": new})
        return

    # scalar or type change: replace
    ops.append({"op": "replace", "path": path, "value": new})


def diff_assets(base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    ops: List[Dict[str, Any]] = []
    _collect(base, new, "", ops)
    # normalize root path to '/'
    for op in ops:
        if op["path"] == "":
            op["path"] = "/"
    order = {"remove": 0, "add": 1, "replace": 2}
    ops.sort(key=lambda o: (o["path"], order.get(o["op"], 99)))
    return {"ok": True, "patch": ops}

