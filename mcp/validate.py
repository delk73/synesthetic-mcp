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

from .core import _schema_file_path, PathOutsideConfiguredRoot

# Alias mapping: accept nested alias but validate against canonical schema
_SCHEMA_ALIASES = {
    "nested-synesthetic-asset": "synesthetic-asset",
}


MAX_BYTES = 1 * 1024 * 1024  # 1 MiB
_DEFAULT_MAX_BATCH = 100


def _max_batch() -> int:
    raw = os.environ.get("MCP_MAX_BATCH")
    if raw is None or not raw.strip():
        return _DEFAULT_MAX_BATCH
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid MCP_MAX_BATCH '{raw}'") from exc
    if value <= 0:
        raise RuntimeError("MCP_MAX_BATCH must be a positive integer")
    return value


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


def _load_schema(name: str) -> tuple[Dict[str, Any], Path]:
    canonical = _SCHEMA_ALIASES.get(name, name)
    path = _schema_file_path(canonical)
    return json.loads(path.read_text()), path

def _build_local_registry():
    if Registry is None or Resource is None:
        return None

    base_dir = Path("libs/synesthetic-schemas")
    version_path = base_dir / "version.json"
    version: str | None = None
    try:
        version_data = json.loads(version_path.read_text())
        candidate = version_data.get("schemaVersion")
        if isinstance(candidate, str) and candidate:
            version = candidate
    except Exception:
        version = None

    schema_dir = base_dir / "schemas"
    if not schema_dir.is_dir():
        alt = base_dir / "jsonschema"
        if alt.is_dir():
            schema_dir = alt
        else:
            schema_dir = None

    registry = Registry()
    if schema_dir is None or not schema_dir.is_dir():
        return registry

    resources = {}
    for path in sorted(schema_dir.glob("*.json")):
        try:
            contents = json.loads(path.read_text())
        except Exception:
            continue
        if version:
            url = f"https://schemas.synesthetic.dev/{version}/{path.name}"
        else:
            url = None
        try:
            resource = Resource.from_contents(contents)
        except Exception:
            continue
        if url:
            resources[url] = resource
        schema_id = contents.get("$id")
        if isinstance(schema_id, str) and schema_id:
            resources.setdefault(schema_id, resource)

    if resources:
        registry = registry.with_resources(resources.items())

    return registry



def validate_asset(asset: Dict[str, Any], schema: str | None) -> Dict[str, Any]:
    if not schema:
        return {
            "ok": False,
            "reason": "validation_failed",
            "errors": [{"path": "", "msg": "schema_required"}],
        }

    if not _size_okay(asset):
        return {
            "ok": False,
            "reason": "validation_failed",
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
        schema_obj, schema_path = _load_schema(schema)
    except PathOutsideConfiguredRoot:
        return {
            "ok": False,
            "reason": "validation_failed",
            "errors": [{"path": "/schema", "msg": "schema_outside_configured_root"}],
        }
    except Exception as e:
        return {
            "ok": False,
            "reason": "validation_failed",
            "errors": [{"path": "/", "msg": f"schema_load_failed: {e}"}],
        }

    # Establish base_uri for $ref resolution from file path if $id missing
    base_uri = None
    if schema_path.exists():
        base_uri = schema_path.resolve().as_uri()
    schema_copy = dict(schema_obj)
    if base_uri and "$id" not in schema_copy:
        schema_copy["$id"] = base_uri

    registry = _build_local_registry()
    if registry is not None:
        validator = Draft202012Validator(schema_copy, registry=registry)
    else:
        validator = Draft202012Validator(schema_copy)
    errors = []
    for err in validator.iter_errors(payload):
        pointer = _pointer_from_path(err.absolute_path)
        errors.append({"path": pointer, "msg": err.message})

    errors.sort(key=lambda e: (e["path"], e["msg"]))
    if errors:
        return {"ok": False, "reason": "validation_failed", "errors": errors}
    return {"ok": True, "errors": []}


def validate_many(assets: List[Dict[str, Any]] | None, schema: str | None) -> Dict[str, Any]:
    if not schema:
        return {
            "ok": False,
            "reason": "validation_failed",
            "errors": [{"path": "/schema", "msg": "schema param is required"}],
        }

    if assets is None:
        assets = []
    if not isinstance(assets, list):
        return {
            "ok": False,
            "reason": "validation_failed",
            "errors": [{"path": "/assets", "msg": "assets must be an array"}],
        }

    limit = _max_batch()
    if len(assets) > limit:
        return {
            "ok": False,
            "reason": "unsupported",
            "detail": "batch_too_large",
            "limit": limit,
        }

    results: List[Dict[str, Any]] = []
    all_ok = True
    for item in assets:
        validation = validate_asset(item, schema)
        entry: Dict[str, Any] = {"ok": validation.get("ok", False)}
        if "errors" in validation and validation["errors"]:
            entry["errors"] = validation["errors"]
        if not entry["ok"] and validation.get("reason"):
            entry["reason"] = validation["reason"]
        results.append(entry)
        if not entry["ok"]:
            all_ok = False

    return {"ok": all_ok, "results": results}
