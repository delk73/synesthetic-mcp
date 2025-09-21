from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

SUBMODULE_SCHEMAS_DIR = "libs/synesthetic-schemas/jsonschema"
SUBMODULE_EXAMPLES_DIR = "libs/synesthetic-schemas/examples"


def _schemas_dir() -> Path:
    # Env override takes precedence
    env = os.environ.get("SYN_SCHEMAS_DIR")
    if env:
        return Path(env)
    # Prefer submodule if present
    sub = Path(SUBMODULE_SCHEMAS_DIR)
    if sub.is_dir():
        return sub
    # No local fixture fallback; return as-is for callers to handle
    return sub


def _examples_dir() -> Path:
    # Env override takes precedence
    env = os.environ.get("SYN_EXAMPLES_DIR")
    if env:
        return Path(env)
    # Prefer submodule if present
    sub = Path(SUBMODULE_EXAMPLES_DIR)
    if sub.is_dir():
        return sub
    # No local fixture fallback; return as-is for callers to handle
    return sub


def list_schemas() -> Dict[str, Any]:
    d = _schemas_dir()
    items: List[Dict[str, str]] = []
    if d.is_dir():
        for p in d.glob("*.schema.json"):
            try:
                data = json.loads(p.read_text())
            except Exception:
                continue
            name = p.name.replace(".schema.json", "")
            version = str(data.get("version", ""))
            if p.name.endswith(".schema.json"):
                listed_path = str(p.with_name(p.name.replace(".schema.json", ".json")))
            else:
                listed_path = str(p)
            items.append({"name": name, "version": version, "path": listed_path})
    items.sort(key=lambda x: (x["name"], x["version"], x["path"]))
    return {"ok": True, "schemas": items}


def get_schema(name: str) -> Dict[str, Any]:
    p = _schemas_dir() / f"{name}.schema.json"
    if not p.exists():
        return {"ok": False, "reason": "not_found"}
    data = json.loads(p.read_text())
    version = str(data.get("version", ""))
    return {"ok": True, "schema": data, "version": version}


def list_examples(component: str | None = None) -> Dict[str, Any]:
    d = _examples_dir()
    items: List[Dict[str, str]] = []
    target = None
    if component:
        normalized = component.strip()
        if normalized not in {"*", "all"}:
            target = normalized
    if d.is_dir():
        for p in sorted(d.rglob("*.json")):
            if not p.is_file():
                continue
            comp = p.name.split(".")[0]
            if target is not None and comp != target:
                continue
            items.append({"component": comp, "path": str(p)})
    items.sort(key=lambda x: (x["component"], x["path"]))
    return {"ok": True, "examples": items}


def _infer_schema_name_from_example(p: Path, data: Dict[str, Any]) -> str:
    # 1) Explicit field
    schema = data.get("schema")
    if isinstance(schema, str) and schema:
        return schema
    # 2) $schemaRef like 'jsonschema/synesthetic-asset.schema.json'
    ref = data.get("$schemaRef")
    if isinstance(ref, str) and ref:
        name = Path(ref).name
        if name.endswith(".schema.json"):
            return name[: -len(".schema.json")]
        if name.endswith(".json"):
            return name[: -len(".json")]
    # 3) Minimal filename fallback for canonical asset examples
    # Map SynestheticAsset_* examples to the nested alias for validation
    if p.name.startswith("SynestheticAsset"):
        return "nested-synesthetic-asset"
    # 4) Last resort: base filename without extension
    return p.stem


def get_example(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = _examples_dir() / path
    if not p.exists():
        return {"ok": False, "reason": "not_found"}
    data = json.loads(p.read_text())
    schema_name = _infer_schema_name_from_example(p, data)
    # validate lazily to avoid import cycles
    try:
        from .validate import validate_asset

        res = validate_asset(data, schema_name)
        validated = bool(res.get("ok", False))
    except Exception:
        validated = False
    return {"ok": True, "example": data, "schema": schema_name, "validated": validated}
