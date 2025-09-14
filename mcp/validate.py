from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator

from .core import _schemas_dir


MAX_BYTES = 1 * 1024 * 1024  # 1 MiB


def _pointer_from_path(parts) -> str:
    # RFC6901 escaping
    def esc(s: str) -> str:
        return s.replace("~", "~0").replace("/", "~1")

    out = ""
    for part in parts:
        if isinstance(part, int):
            out += f"/{part}"
        else:
            out += f"/{esc(str(part))}"
    return out or "/"


def _size_okay(obj: Any) -> bool:
    try:
        return len(json.dumps(obj).encode("utf-8")) <= MAX_BYTES
    except Exception:
        return False


def _load_schema(name: str) -> Dict[str, Any]:
    p = _schemas_dir() / f"{name}.schema.json"
    return json.loads(Path(p).read_text())


def validate_asset(asset: Dict[str, Any], schema: str) -> Dict[str, Any]:
    if not _size_okay(asset):
        return {
            "ok": False,
            "errors": [{"path": "/", "msg": "payload_too_large"}],
        }

    try:
        schema_obj = _load_schema(schema)
    except Exception as e:
        return {
            "ok": False,
            "errors": [{"path": "/", "msg": f"schema_load_failed: {e}"}],
        }

    # Establish base_uri for $ref resolution from file path if $id missing
    base_uri = None
    p = _schemas_dir() / f"{schema}.schema.json"
    if p.exists():
        base_uri = p.resolve().as_uri()
    schema_copy = dict(schema_obj)
    if base_uri and "$id" not in schema_copy:
        schema_copy["$id"] = base_uri

    validator = Draft202012Validator(schema_copy)
    errors = []
    for err in validator.iter_errors(asset):
        pointer = _pointer_from_path(err.absolute_path)
        errors.append({"path": pointer, "msg": err.message})

    errors.sort(key=lambda e: (e["path"], e["msg"]))
    return {"ok": len(errors) == 0, "errors": errors}

