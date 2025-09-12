from __future__ import annotations

from typing import Any, Dict, List, Optional

from jsonschema import Draft2020Validator, ValidationError


def validate_asset(asset: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Validate an asset dict against a JSON Schema.

    Returns a standardized result dict: { ok: bool, errors: [ {path, msg} ] }
    """
    try:
        validator = Draft2020Validator(schema)
    except Exception as e:  # pragma: no cover - schema construction errors
        return {"ok": False, "reason": "schema_error", "errors": [{"path": "/", "msg": str(e)}]}

    errors: List[Dict[str, Any]] = []
    for err in validator.iter_errors(asset):
        path = "/" + "/".join(str(p) for p in err.path)
        errors.append({"path": path or "/", "msg": err.message})

    return {"ok": len(errors) == 0, "errors": errors}

