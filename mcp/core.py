from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

SUBMODULE_SCHEMAS_DIR = "libs/synesthetic-schemas/jsonschema"
SUBMODULE_EXAMPLES_DIR = "libs/synesthetic-schemas/examples"

DEFAULT_LABS_SCHEMA_BASE = "https://delk73.github.io/synesthetic-schemas/schema/"
DEFAULT_LABS_SCHEMA_VERSION = "0.7.3"
DEFAULT_LABS_SCHEMA_CACHE_DIR = ".cache/synesthetic-schemas"


def labs_schema_base() -> str:
    raw = os.environ.get("LABS_SCHEMA_BASE", DEFAULT_LABS_SCHEMA_BASE)
    base = raw.strip() or DEFAULT_LABS_SCHEMA_BASE
    if not base.endswith("/"):
        base = f"{base}/"
    return base


def labs_schema_version() -> str:
    raw = os.environ.get("LABS_SCHEMA_VERSION", DEFAULT_LABS_SCHEMA_VERSION)
    version = raw.strip() or DEFAULT_LABS_SCHEMA_VERSION
    return version


def labs_schema_prefix() -> str:
    return f"{labs_schema_base()}{labs_schema_version().strip().rstrip('/')}/"


def labs_schema_cache_dir() -> Path | None:
    raw = os.environ.get("LABS_SCHEMA_CACHE_DIR")
    if raw is not None and not raw.strip():
        return None
    if raw:
        return Path(raw).expanduser()
    try:
        home = Path.home()
    except Exception:
        return None
    return home / DEFAULT_LABS_SCHEMA_CACHE_DIR / labs_schema_version()


class PathOutsideConfiguredRoot(ValueError):
    """Raised when a requested file escapes the configured root directory."""


def _resolve_within_root(root: Path, relative: str) -> Path:
    base = root.resolve(strict=False)
    fragment = Path(relative)
    if fragment.is_absolute():
        raise PathOutsideConfiguredRoot(relative)
    candidate = (base / fragment).resolve(strict=False)
    if base == candidate or base not in candidate.parents:
        raise PathOutsideConfiguredRoot(relative)
    return candidate


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


def _schema_file_path(name: str) -> Path:
    name = str(name)
    if not name or not name.strip():
        raise PathOutsideConfiguredRoot(name)
    root = _schemas_dir()
    return _resolve_within_root(root, f"{name}.schema.json")


def _example_file_path(relative: str) -> Path:
    relative = str(relative)
    if not relative or not relative.strip():
        raise PathOutsideConfiguredRoot(relative)
    root = _examples_dir()
    return _resolve_within_root(root, relative)


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
    try:
        p = _schema_file_path(name)
    except PathOutsideConfiguredRoot:
        return {
            "ok": False,
            "reason": "validation_failed",
            "errors": [{"path": "/name", "msg": "invalid_path"}],
        }

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
    # 1) Prefer explicit $schema marker (v0.2.8 contract)
    marker = data.get("$schema")
    if isinstance(marker, str) and marker:
        raw = marker.split("#", 1)[0]
        candidate = Path(raw).name or marker
        if candidate.endswith(".schema.json"):
            return candidate[: -len(".schema.json")]
        if candidate.endswith(".json"):
            return candidate[: -len(".json")]
        return candidate
    # 2) Minimal filename fallback for canonical asset examples
    # Map SynestheticAsset_* examples to the nested alias for validation
    if p.name.startswith("SynestheticAsset"):
        return "nested-synesthetic-asset"
    # 3) Last resort: base filename without extension
    return p.stem


def get_example(path: str) -> Dict[str, Any]:
    try:
        p = _example_file_path(path)
    except PathOutsideConfiguredRoot:
        return {
            "ok": False,
            "reason": "validation_failed",
            "errors": [{"path": "/path", "msg": "invalid_path"}],
        }

    if not p.exists():
        return {"ok": False, "reason": "not_found"}
    data = json.loads(p.read_text())
    schema_name = _infer_schema_name_from_example(p, data)
    # validate lazily to avoid import cycles
    try:
        from .validate import validate_asset

        res = validate_asset(data)
        if not res.get("ok", False):
            return res
    except Exception as e:
        return {"ok": False, "reason": "validation_failed", "errors": [{"path": "/", "msg": str(e)}]}
    return {"ok": True, "example": data, "schema": schema_name, "validated": True}


def governance_audit() -> Dict[str, Any]:
    prefix = labs_schema_prefix()
    base = labs_schema_base()
    version = labs_schema_version()

    examples_dir = _examples_dir()
    example_paths = sorted(
        p for p in examples_dir.rglob("*.json") if p.is_file()
    )

    missing: List[str] = []
    for path in example_paths:
        try:
            data = json.loads(path.read_text())
        except Exception:
            missing.append(path.name)
            continue
        marker = data.get("$schema")
        if not isinstance(marker, str) or not marker.startswith(prefix):
            missing.append(path.name)

    missing_sorted = sorted(set(missing))
    status = "ok" if not missing_sorted else "partial"
    return {
        "ok": status == "ok",
        "schemas_base": base,
        "schema_version": version,
        "examples_checked": len(example_paths),
        "missing_schema": missing_sorted,
        "transports": ["stdio", "socket", "tcp"],
        "status": status,
    }
