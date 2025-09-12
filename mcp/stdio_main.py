from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from . import diff, validate
from .core import get_example, get_schema, list_examples, list_schemas


def _handle_request(req: Dict[str, Any]) -> Dict[str, Any]:
    method = req.get("method")
    params = req.get("params", {})
    rid = req.get("id")

    try:
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": rid, "result": {"server": "synesthetic-mcp", "version": "0.1.0"}}
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": rid,
                "result": [
                    {"name": "validate_asset"},
                    {"name": "diff_assets"},
                ],
            }
        if method == "resources/list":
            schemas = [s.__dict__ | {"path": str(s.path)} for s in list_schemas()]
            examples = [str(p) for p in list_examples()]
            return {"jsonrpc": "2.0", "id": rid, "result": {"schemas": schemas, "examples": examples}}
        if method == "tools/call":
            tool = params.get("name")
            if tool == "validate_asset":
                asset = params.get("asset")
                schema_name = params.get("schema")
                schema = get_schema(schema_name)
                out = validate.validate_asset(asset, schema)
                return {"jsonrpc": "2.0", "id": rid, "result": out}
            if tool == "diff_assets":
                base = params.get("base")
                new = params.get("new")
                patch = diff.generate_patch(base, new)
                return {"jsonrpc": "2.0", "id": rid, "result": {"ok": True, "patch": patch}}
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "unsupported tool"}}
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "unsupported method"}}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32000, "message": str(e)}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synesthetic MCP stdio server")
    parser.add_argument("--stdio", action="store_true", help="Run in stdio JSON-RPC mode")
    args = parser.parse_args(argv)

    if not args.stdio:
        print("Use --stdio to start JSON-RPC over stdio.")
        return 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "parse error"}}) + "\n")
            sys.stdout.flush()
            continue
        resp = _handle_request(req)
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

