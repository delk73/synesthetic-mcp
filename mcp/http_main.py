from __future__ import annotations

def create_app():
    try:
        from fastapi import FastAPI
    except Exception as e:  # pragma: no cover - optional dependency
        raise ImportError("FastAPI not installed. Install 'fastapi' to use http_main.") from e

    from . import diff, validate
    from .core import get_schema

    app = FastAPI(title="Synesthetic MCP")

    @app.post("/validate")
    def validate_endpoint(payload: dict):
        schema_name = payload.get("schema")
        schema = get_schema(schema_name)
        return validate.validate_asset(payload.get("asset"), schema)

    @app.post("/diff")
    def diff_endpoint(payload: dict):
        patch = diff.generate_patch(payload.get("base"), payload.get("new"))
        return {"ok": True, "patch": patch}

    return app

