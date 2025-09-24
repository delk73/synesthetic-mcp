from __future__ import annotations

import json
from typing import Any, Callable, Dict, Tuple

from .validate import MAX_BYTES


class PayloadTooLarge(Exception):
    """Raised when a JSON-RPC frame exceeds the configured transport limit."""


def parse_line(line: str) -> Tuple[Any, str, Dict[str, Any]]:
    encoded = line.encode("utf-8")
    if len(encoded) > MAX_BYTES:
        raise PayloadTooLarge
    data = json.loads(line)
    rid = data.get("id")
    method = data.get("method", "")
    params = data.get("params", {}) or {}
    return rid, method, params


def build_result_frame(rid: Any, result: Dict[str, Any]) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": rid, "result": result})


def build_error_frame(rid: Any, message: str, code: int = -32603) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}})


def payload_too_large_frame(rid: Any) -> str:
    result = {
        "ok": False,
        "reason": "validation_failed",
        "errors": [{"path": "", "msg": "payload_too_large"}],
    }
    return build_result_frame(rid, result)


def process_line(
    line: str, handler: Callable[[str, Dict[str, Any]], Dict[str, Any]]
) -> str:
    rid: Any = None
    try:
        rid, method, params = parse_line(line)
        result = handler(method, params)
        return build_result_frame(rid, result)
    except PayloadTooLarge:
        return payload_too_large_frame(rid)
    except Exception as exc:  # pragma: no cover - exercised via integration tests
        return build_error_frame(rid, str(exc))
