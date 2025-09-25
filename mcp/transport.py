from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Tuple

from .validate import MAX_BYTES


class PayloadTooLarge(Exception):
    """Raised when a JSON-RPC frame exceeds the configured transport limit."""


class InvalidRequest(Exception):
    """Raised when a JSON-RPC request is semantically invalid."""

    def __init__(
        self, rid: Any, reason: str, errors: List[Dict[str, Any]]
    ) -> None:
        super().__init__(reason)
        self.rid = rid
        self.reason = reason
        self.errors = errors


def parse_line(line: str) -> Tuple[Any, str, Dict[str, Any]]:
    encoded = line.encode("utf-8")
    if len(encoded) > MAX_BYTES:
        raise PayloadTooLarge
    data = json.loads(line)
    rid = data.get("id")
    method = data.get("method", "")
    if not isinstance(method, str) or not method.strip():
        raise InvalidRequest(
            rid,
            "validation_failed",
            [{"path": "/method", "msg": "method must be a non-empty string"}],
        )
    params_raw = data.get("params", {})
    if params_raw is None:
        params_raw = {}
    if not isinstance(params_raw, dict):
        raise InvalidRequest(
            rid,
            "validation_failed",
            [{"path": "/params", "msg": "params must be an object"}],
        )
    return rid, method, params_raw


def build_result_frame(rid: Any, result: Dict[str, Any]) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": rid, "result": result})


def build_error_frame(rid: Any, message: str, code: int = -32603) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}})


def payload_too_large_frame(rid: Any) -> str:
    result = build_failure_result(
        "validation_failed", [{"path": "", "msg": "payload_too_large"}]
    )
    return build_result_frame(rid, result)


def build_failure_result(
    reason: str, errors: List[Dict[str, Any]] | None = None, detail: str | None = None
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"ok": False, "reason": reason}
    if errors:
        payload["errors"] = errors
    if detail is not None:
        payload["detail"] = detail
    return payload


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
    except InvalidRequest as exc:
        if rid is None:
            rid = exc.rid
        return build_result_frame(rid, build_failure_result(exc.reason, exc.errors))
    except json.JSONDecodeError as exc:
        return build_error_frame(rid, str(exc))
    except Exception as exc:  # pragma: no cover - exercised via integration tests
        logging.exception("mcp:error reason=dispatch_failure")
        payload = build_failure_result(
            "internal_error",
            [{"path": "/", "msg": "unexpected_error"}],
            detail=str(exc),
        )
        return build_result_frame(rid, payload)
