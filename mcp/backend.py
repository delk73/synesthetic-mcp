from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import httpx

from .validate import validate_asset, MAX_BYTES


def _backend_url() -> Optional[str]:
    return os.environ.get("SYN_BACKEND_URL")

def _assets_path() -> str:
    p = os.environ.get("SYN_BACKEND_ASSETS_PATH", "/synesthetic-assets/")
    if not p.startswith("/"):
        p = "/" + p
    return p


def populate_backend(
    asset: Dict[str, Any],
    validate_first: bool = True,
    *,
    client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    url = _backend_url()
    if not url:
        return {
            "ok": False,
            "reason": "unsupported",
            "detail": "backend disabled",
        }

    if len(json.dumps(asset).encode("utf-8")) > MAX_BYTES:
        return {
            "ok": False,
            "reason": "validation_failed",
            "errors": [{"path": "/", "msg": "payload_too_large"}],
        }

    if validate_first:
        v = validate_asset(asset)
        if not v.get("ok", False):
            return {"ok": False, "reason": "validation_failed", "errors": v["errors"]}

    need_close = False
    if client is None:
        client = httpx.Client(base_url=url, timeout=5.0)
        need_close = True

    try:
        resp = client.post(_assets_path(), json=asset)
    except httpx.HTTPError as e:
        if need_close:
            client.close()
        return {
            "ok": False,
            "reason": "backend_error",
            "status": 503,
            "detail": str(e.__class__.__name__),
        }
    finally:
        if need_close:
            client.close()

    if 200 <= resp.status_code < 300:
        try:
            data = resp.json()
        except Exception:
            data = {}
        asset_id = str(data.get("id", ""))
        return {"ok": True, "asset_id": asset_id, "backend_url": url}

    detail = ""
    try:
        detail = resp.text
    except Exception:
        detail = ""
    return {
        "ok": False,
        "reason": "backend_error",
        "status": resp.status_code,
        "detail": detail,
    }
