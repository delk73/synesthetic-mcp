from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator
try:
    from referencing import Registry, Resource  # type: ignore
except Exception:  # pragma: no cover
    Registry = None  # type: ignore
    Resource = None  # type: ignore

from .core import _schemas_dir

# Alias mapping: accept nested alias but validate against canonical schema
_SCHEMA_ALIASES = {
    "nested-synesthetic-asset": "synesthetic-asset",
}


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
    canonical = _SCHEMA_ALIASES.get(name, name)
    p = _schemas_dir() / f"{canonical}.schema.json"
    return json.loads(Path(p).read_text())

_REGISTRY = None


def _ensure_registry():
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY
    if Registry is None or Resource is None:
        _REGISTRY = None
        return None
    mapping = {}
    d = _schemas_dir()
    if d.is_dir():
        for p in d.glob("*.schema.json"):
            try:
                obj = json.loads(Path(p).read_text())
            except Exception:
                continue
            uri = obj.get("$id")
            if isinstance(uri, str) and uri:
                try:
                    mapping[uri] = Resource.from_contents(obj)
                except Exception:
                    continue
    _REGISTRY = Registry().with_resources(mapping.items()) if mapping else Registry()
    return _REGISTRY



def validate_asset(asset: Dict[str, Any], schema: str) -> Dict[str, Any]:
    if not _size_okay(asset):
        return {
            "ok": False,
            "errors": [{"path": "/", "msg": "payload_too_large"}],
        }

    # Examples may carry a helper field not represented in JSON Schema.
    # Ignore a top-level "$schemaRef" if present for validation purposes.
    if isinstance(asset, dict) and "$schemaRef" in asset:
        payload = dict(asset)
        payload.pop("$schemaRef", None)
    else:
        payload = asset

    try:
        schema_obj = _load_schema(schema)
    except Exception as e:
        return {
            "ok": False,
            "errors": [{"path": "/", "msg": f"schema_load_failed: {e}"}],
        }

    # Establish base_uri for $ref resolution from file path if $id missing
    base_uri = None
    canonical = _SCHEMA_ALIASES.get(schema, schema)
    p = _schemas_dir() / f"{canonical}.schema.json"
    if p.exists():
        base_uri = p.resolve().as_uri()
    schema_copy = dict(schema_obj)
    if base_uri and "$id" not in schema_copy:
        schema_copy["$id"] = base_uri

    registry = _ensure_registry()
    if registry is not None:
        validator = Draft202012Validator(schema_copy, registry=registry)
    else:
        validator = Draft202012Validator(schema_copy)
    errors = []
    for err in validator.iter_errors(payload):
        pointer = _pointer_from_path(err.absolute_path)
        errors.append({"path": pointer, "msg": err.message})

    errors.sort(key=lambda e: (e["path"], e["msg"]))
    return {"ok": len(errors) == 0, "errors": errors}
