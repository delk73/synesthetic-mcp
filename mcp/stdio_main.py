from __future__ import annotations

import json
import sys
from typing import Any, Dict

from .core import get_example, get_schema, list_examples, list_schemas
from .validate import validate_asset
from .diff import diff_assets
from .backend import populate_backend


def _handle(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if method == "list_schemas":
        return list_schemas()
    if method == "get_schema":
        return get_schema(params.get("name", ""))
    if method == "list_examples":
        return list_examples(params.get("component"))
    if method == "get_example":
        return get_example(params.get("path", ""))
    if method == "validate_asset":
        return validate_asset(params.get("asset", {}), params.get("schema", ""))
    if method == "diff_assets":
        return diff_assets(params.get("base", {}), params.get("new", {}))
    if method == "populate_backend":
        return populate_backend(
            params.get("asset", {}), bool(params.get("validate_first", True))
        )
    return {"ok": False, "reason": "unsupported", "msg": "tool not implemented"}


def main() -> None:
    # Minimal newline-delimited JSON-RPC-ish loop: {"id","method","params"}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        rid = None
        try:
            req = json.loads(line)
            rid = req.get("id")
            method = req.get("method", "")
            params = req.get("params", {}) or {}
            result = _handle(method, params)
            out = {"jsonrpc": "2.0", "id": rid, "result": result}
        except Exception as e:
            out = {
                "jsonrpc": "2.0",
                "id": rid,
                "error": {"code": -32603, "message": str(e)},
            }
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
