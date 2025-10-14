from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import httpx
from jsonschema import Draft202012Validator
try:
    from referencing import Registry, Resource  # type: ignore
except Exception:  # pragma: no cover
    Registry = None  # type: ignore
    Resource = None  # type: ignore

from .core import (
    _schema_file_path,
    PathOutsideConfiguredRoot,
    labs_schema_base,
    labs_schema_cache_dir,
    labs_schema_prefix,
    labs_schema_version,
)

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


def _validation_error(path: str, msg: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "reason": "validation_failed",
        "errors": [{"path": path, "msg": msg}],
    }


class SchemaResolutionError(RuntimeError):
    """Raised when schema loading fails."""


def _schema_filename_parts(filename: str) -> Tuple[str, str]:
    if filename.endswith(".schema.json"):
        return filename[: -len(".schema.json")], ".schema.json"
    if filename.endswith(".json"):
        return filename[: -len(".json")], ".json"
    return filename, ".json"


def _schema_target(marker: str) -> Tuple[str, str, str, str]:
    raw = marker.strip()
    if not raw:
        raise ValueError("empty_marker")

    canonical_prefix = labs_schema_prefix()
    without_fragment = raw.split("#", 1)[0].strip()
    parsed = urlparse(without_fragment)
    if not parsed.scheme:
        raise ValueError("schema_not_canonical")
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("schema_not_canonical")
    if not without_fragment.startswith(canonical_prefix):
        raise ValueError("schema_not_canonical")

    path_component = parsed.path or ""
    if "/../" in path_component or path_component.endswith("/.."):
        raise PathOutsideConfiguredRoot(path_component or without_fragment)

    filename = Path(path_component).name
    if not filename:
        raise ValueError("invalid_schema_marker")

    base_name, extension = _schema_filename_parts(filename)
    canonical_name = _SCHEMA_ALIASES.get(base_name, base_name)
    canonical_filename = f"{canonical_name}{extension}"
    canonical_url = f"{canonical_prefix}{canonical_filename}"
    return canonical_name, canonical_filename, without_fragment, canonical_url


def _cache_path(canonical_filename: str) -> Path | None:
    cache_dir = labs_schema_cache_dir()
    if cache_dir is None:
        return None
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return None
    return cache_dir / canonical_filename


def _fetch_canonical_schema(url: str, canonical_filename: str) -> Dict[str, Any]:
    cache_path = _cache_path(canonical_filename)
    if cache_path and cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except Exception:
            cache_path.unlink(missing_ok=True)

    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        raise SchemaResolutionError(str(exc)) from exc

    if cache_path:
        try:
            cache_path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass
    return data


def _load_schema(
    name: str,
    canonical_filename: str,
    requested_url: str,
    canonical_url: str,
) -> tuple[Dict[str, Any], Path | None]:
    canonical = _SCHEMA_ALIASES.get(name, name)
    try:
        path = _schema_file_path(canonical)
    except PathOutsideConfiguredRoot:
        raise
    try:
        return json.loads(path.read_text()), path
    except FileNotFoundError:
        pass
    except Exception as exc:
        raise SchemaResolutionError(f"schema_load_failed: {exc}") from exc

    try:
        schema = _fetch_canonical_schema(canonical_url, canonical_filename)
    except SchemaResolutionError as primary_exc:
        if requested_url != canonical_url:
            fallback_filename = Path(urlparse(requested_url).path or "").name or canonical_filename
            schema = _fetch_canonical_schema(requested_url, fallback_filename)
        else:
            raise primary_exc
    return schema, None

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
            url = f"https://delk73.github.io/synesthetic-schemas/schema/{version}/{path.name}"
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



def validate_asset(asset: Dict[str, Any]) -> Dict[str, Any]:
    if not _size_okay(asset):
        return {
            "ok": False,
            "reason": "validation_failed",
            "errors": [{"path": "/", "msg": "payload_too_large"}],
        }

    if not isinstance(asset, dict):
        return _validation_error("/", "asset must be an object")

    schema_marker = asset.get("$schema")
    if not isinstance(schema_marker, str) or not schema_marker.strip():
        return _validation_error("/$schema", "top-level $schema is required")
    try:
        (
            schema_name,
            canonical_filename,
            requested_url,
            canonical_url,
        ) = _schema_target(schema_marker)
    except PathOutsideConfiguredRoot:
        return _validation_error("/$schema", "schema_outside_configured_root")
    except ValueError as exc:
        message = str(exc)
        if message == "schema_not_canonical":
            return _validation_error("/$schema", "schema_must_use_canonical_host")
        if message == "empty_marker":
            return _validation_error("/$schema", "top-level $schema is required")
        return _validation_error("/$schema", "invalid_schema_marker")

    legacy_keys = [key for key in ("schema", "$schemaRef") if key in asset]
    if legacy_keys:
        joined = ",".join(sorted(legacy_keys))
        return _validation_error(
            "/$schema", f"legacy schema keys not allowed: {joined}"
        )

    payload = dict(asset)
    payload.pop("$schema", None)

    try:
        schema_obj, schema_path = _load_schema(
            schema_name, canonical_filename, requested_url, canonical_url
        )
    except PathOutsideConfiguredRoot:
        return _validation_error("/$schema", "schema_outside_configured_root")
    except SchemaResolutionError as exc:
        return {
            "ok": False,
            "reason": "validation_failed",
            "errors": [{"path": "/", "msg": f"schema_resolution_failed: {exc}"}],
        }

    # Establish base_uri for $ref resolution from file path if $id missing
    base_uri = None
    if schema_path and schema_path.exists():
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


def validate_many(assets: List[Dict[str, Any]] | None) -> Dict[str, Any]:
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
        validation = validate_asset(item)
        entry: Dict[str, Any] = {"ok": validation.get("ok", False)}
        if "errors" in validation and validation["errors"]:
            entry["errors"] = validation["errors"]
        if not entry["ok"] and validation.get("reason"):
            entry["reason"] = validation["reason"]
        results.append(entry)
        if not entry["ok"]:
            all_ok = False

    return {"ok": all_ok, "results": results}
