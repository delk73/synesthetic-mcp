from __future__ import annotations

import sys
from typing import Any, Dict

from .backend import populate_backend
from .core import get_example, get_schema, list_examples, list_schemas
from .diff import diff_assets
from .transport import process_line
from .validate import validate_asset


def dispatch(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if method == "list_schemas":
        return list_schemas()
    if method == "get_schema":
        return get_schema(params.get("name", ""))
    if method == "list_examples":
        return list_examples(params.get("component"))
    if method == "get_example":
        return get_example(params.get("path", ""))
    if method in ("validate", "validate_asset"):
        # "validate" is the deprecated alias; keep accepting it for compatibility.
        asset = params.get("asset", {})
        if "schema" not in params or not params["schema"]:
            return {
                "ok": False,
                "reason": "validation_failed",
                "errors": [{"path": "/schema", "msg": "schema param is required"}],
            }
        schema = params["schema"]
        return validate_asset(asset, schema)
    if method == "diff_assets":
        return diff_assets(params.get("base", {}), params.get("new", {}))
    if method == "populate_backend":
        return populate_backend(
            params.get("asset", {}), bool(params.get("validate_first", True))
        )
    return {
        "ok": False,
        "reason": "unsupported",
        "detail": "tool not implemented",
    }


def main() -> None:
    # Minimal newline-delimited JSON-RPC-ish loop: {"id","method","params"}
    for line in sys.stdin:
        stripped = line.strip()
        if not stripped:
            continue
        out = process_line(stripped, dispatch)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
