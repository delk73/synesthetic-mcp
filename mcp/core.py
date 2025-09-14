from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_SCHEMAS_DIR = "tests/fixtures/schemas"
DEFAULT_EXAMPLES_DIR = "tests/fixtures/examples"


def _schemas_dir() -> Path:
    return Path(os.environ.get("SYN_SCHEMAS_DIR", DEFAULT_SCHEMAS_DIR))


def _examples_dir() -> Path:
    return Path(os.environ.get("SYN_EXAMPLES_DIR", DEFAULT_EXAMPLES_DIR))


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
            items.append({"name": name, "version": version, "path": str(p)})
    items.sort(key=lambda x: (x["name"], x["version"], x["path"]))
    return {"ok": True, "schemas": items}


def get_schema(name: str) -> Dict[str, Any]:
    p = _schemas_dir() / f"{name}.schema.json"
    if not p.exists():
        return {"ok": False, "schema": None, "version": ""}
    data = json.loads(p.read_text())
    version = str(data.get("version", ""))
    return {"ok": True, "schema": data, "version": version}


def list_examples(component: str | None = None) -> Dict[str, Any]:
    d = _examples_dir()
    items: List[Dict[str, str]] = []
    if d.is_dir():
        for p in sorted(d.glob("*.json")):
            comp = p.name.split(".")[0]
            if component and component != "*" and comp != component:
                continue
            items.append({"component": comp, "path": str(p)})
    items.sort(key=lambda x: (x["component"], x["path"]))
    return {"ok": True, "examples": items}


def get_example(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = _examples_dir() / path
    if not p.exists():
        return {"ok": False, "example": None, "schema": "", "validated": False}
    data = json.loads(p.read_text())
    schema_name = p.name.split(".")[0]
    # validate lazily to avoid import cycles
    try:
        from .validate import validate_asset

        res = validate_asset(data, schema_name)
        validated = bool(res.get("ok", False))
    except Exception:
        validated = False
    return {"ok": True, "example": data, "schema": schema_name, "validated": validated}

