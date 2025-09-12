from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_FIXTURES_ROOT = Path("tests/fixtures")


@dataclass
class SchemaInfo:
    name: str
    version: Optional[str]
    path: Path


def _schemas_root() -> Path:
    # Prefer explicit env override
    env = os.getenv("SYNESTHETIC_SCHEMAS_DIR")
    if env:
        p = Path(env)
        if p.exists():
            return p
    # Try common location if submodule exists
    for candidate in (
        Path("synesthetic-schemas/python/schemas"),
        Path("synesthetic-schemas/schemas"),
        Path("schemas"),
        DEFAULT_FIXTURES_ROOT / "schemas",
    ):
        if candidate.exists():
            return candidate
    return DEFAULT_FIXTURES_ROOT / "schemas"


def _examples_root() -> Path:
    env = os.getenv("SYNESTHETIC_EXAMPLES_DIR")
    if env:
        p = Path(env)
        if p.exists():
            return p
    for candidate in (
        Path("synesthetic-schemas/python/examples"),
        Path("synesthetic-schemas/examples"),
        Path("examples"),
        DEFAULT_FIXTURES_ROOT / "examples",
    ):
        if candidate.exists():
            return candidate
    return DEFAULT_FIXTURES_ROOT / "examples"


def list_schemas() -> List[SchemaInfo]:
    root = _schemas_root()
    infos: List[SchemaInfo] = []
    for p in sorted(root.rglob("*.json")):
        try:
            with p.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            continue
        title = raw.get("title") or p.stem
        version = raw.get("version") or raw.get("$version") or raw.get("x-version")
        infos.append(SchemaInfo(name=title, version=version, path=p))
    return infos


def get_schema(name: str) -> Dict[str, Any]:
    """Fetch schema JSON by title or stem name."""
    root = _schemas_root()
    # Prefer title match
    for p in root.rglob("*.json"):
        try:
            raw = json.loads(p.read_text("utf-8"))
        except Exception:
            continue
        if raw.get("title") == name or p.stem == name:
            return raw
    raise FileNotFoundError(f"Schema not found: {name}")


def list_examples(component: Optional[str] = None) -> List[Path]:
    root = _examples_root()
    if not root.exists():
        return []
    paths = list(sorted(root.rglob("*.json")))
    if component:
        paths = [p for p in paths if component.lower() in "/".join(p.parts).lower()]
    return paths


def get_example(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        # Resolve relative to examples root for convenience
        base = _examples_root()
        p = base / p
    raw = json.loads(p.read_text("utf-8"))
    return raw

