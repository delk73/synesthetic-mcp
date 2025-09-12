from __future__ import annotations

import json
from typing import Any, Dict, Optional

import httpx


class BackendClient:
    def __init__(self, base_url: str, client: Optional[httpx.Client] = None):
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client()

    def populate_backend(
        self,
        asset: Dict[str, Any],
        *,
        validate_first: bool = True,
        validator=None,
        schema: Optional[Dict[str, Any]] = None,
        endpoint: str = "/assets",
    ) -> Dict[str, Any]:
        if validate_first and validator is not None and schema is not None:
            res = validator(asset, schema)
            if not res.get("ok", False):
                return {"ok": False, "reason": "validation_failed", "errors": res.get("errors", [])}

        url = f"{self.base_url}{endpoint}"
        try:
            r = self._client.post(url, json=asset, timeout=10)
            r.raise_for_status()
        except httpx.HTTPError as e:
            detail = None
            try:
                detail = r.text  # type: ignore[name-defined]
            except Exception:  # pragma: no cover
                detail = str(e)
            return {
                "ok": False,
                "reason": "backend_error",
                "status": getattr(e.response, "status_code", None),
                "detail": detail,
            }

        try:
            data = r.json()
        except Exception:
            data = {"id": None}
        return {"ok": True, "asset_id": data.get("id"), "backend_url": url}

