from __future__ import annotations

from typing import Any, Dict


def create_app():
    try:
        from fastapi import FastAPI
    except Exception as e:
        raise ImportError(
            "FastAPI not installed; http adapter is optional"
        ) from e

    from .core import get_example, get_schema, list_examples, list_schemas
    from .validate import validate_asset
    from .diff import diff_assets
    from .backend import populate_backend

    app = FastAPI(title="synesthetic-mcp")

    @app.get("/schemas")
    def schemas() -> Dict[str, Any]:
        return list_schemas()

    @app.get("/schemas/{name}")
    def schema(name: str) -> Dict[str, Any]:
        return get_schema(name)

    @app.get("/examples")
    def examples(component: str | None = None) -> Dict[str, Any]:
        return list_examples(component)

    @app.get("/example")
    def example(path: str) -> Dict[str, Any]:
        return get_example(path)

    @app.post("/validate")
    def validate(body: Dict[str, Any]) -> Dict[str, Any]:
        return validate_asset(body.get("asset", {}), body.get("schema", ""))

    @app.post("/diff")
    def diff(body: Dict[str, Any]) -> Dict[str, Any]:
        return diff_assets(body.get("base", {}), body.get("new", {}))

    @app.post("/populate")
    def populate(body: Dict[str, Any]) -> Dict[str, Any]:
        return populate_backend(body.get("asset", {}), bool(body.get("validate_first", True)))

    return app

