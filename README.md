---
version: 0.1.0
owner: delk73
lastReviewed: 2025-09-12
---

# Synesthetic MCP

Minimal, deterministic MCP-style adapter exposing schemas, examples, validation, diff, and an optional backend-populate tool.

## System Context
```mermaid
flowchart LR
  FE["sdfk_fe_ts\n(TypeScript Frontend)"]
  BE["sdfk-backend\n(Python API & CRUD)"]
  MCP["synesthetic-mcp\n(Python MCP Adapter)"]
  SSOT["synesthetic-schemas\n(SSOT: Schemas + Examples)"]

  MCP --> |Validates + Persists| BE
  SSOT --> |Submodule| MCP
  SSOT --> |Types| FE

  style MCP fill:#444444,stroke:#ffffff,stroke-width:2px
```

## Features

- Schema and example discovery
- JSON Schema validation (Draft 2020-12)
- RFC6902 diff (add/remove/replace only)
- Backend population (optional via `SYN_BACKEND_URL`)
- Minimal stdio loop; optional HTTP app factory

## Structure

```
README.md
requirements.txt
docs/
  mcp_spec.md
mcp/
  __init__.py
  core.py
  validate.py
  diff.py
  backend.py
  stdio_main.py
  http_main.py
tests/
  test_validate.py
  test_diff.py
  test_backend.py
  test_env_discovery.py
  meta/
  prompts/
```

## Development

* Python >= 3.11
* Install deps (minimal): `pip install -r requirements.txt`
  - Minimal deps: `jsonschema`, `httpx`, `pytest`
  - Optional extras: `fastapi` (HTTP app), `uvicorn` (dev server), `referencing` (enhanced JSON Schema refs; import is optional)
  - Dev (optional): `ruff`, `mypy`
* Import check: `python -c "import mcp; print(mcp.__version__)"`
* Run tests: `pytest -q`
* Runtimes:
  - `python -m mcp.stdio_main` (newline-delimited JSON requests)
  - `uvicorn 'mcp.http_main:create_app'` (FastAPI optional)

## Dependencies

- Runtime: `jsonschema`, `httpx`
- Tests: `pytest`
- Dev (optional): `ruff`, `mypy`
- Extras (optional): `fastapi`, `uvicorn` (HTTP adapter), `referencing` (ref handling performance/behavior)

### Environment Discovery

- `SYN_SCHEMAS_DIR` and `SYN_EXAMPLES_DIR` override paths when set.
- Otherwise, schemas/examples are loaded from the `libs/synesthetic-schemas` submodule.
- If neither is available, listings are empty and get operations return not found (no fixture fallback).

### Submodule (SSOT)

Authoritative schemas/examples live at `libs/synesthetic-schemas` (git submodule).

Order of discovery used by the adapter:
1) `SYN_SCHEMAS_DIR` and `SYN_EXAMPLES_DIR` if set
2) `libs/synesthetic-schemas/jsonschema` and `libs/synesthetic-schemas/examples` if present
3) If neither exists, listings are empty and get operations return not found

Initialize the submodule:

```
git submodule update --init --recursive
```

### Schema Aliases (Nested Assets)

* **`synesthetic-asset`** → canonical schema (flat).
* **`nested-synesthetic-asset`** → alias for assets with components inlined.
* All component types may be embedded (shader, tone, haptic, control, modulation, rule bundle).
* Alias validation loads the canonical `synesthetic-asset` schema.
* Examples `SynestheticAsset_Example*.json` are treated as `nested-synesthetic-asset`.
* `$schemaRef` in examples is ignored during validation.
* Tests use the nested alias; submodule is the single source of truth.

## Error Model

- Validation failed: `{ ok:false, reason:'validation_failed', errors:[{ path, msg }] }`
- Backend error: `{ ok:false, reason:'backend_error', status, detail }`
- Unsupported tool/resource: `{ ok:false, reason:'unsupported', msg }`
- Network errors map to backend_error with `status:503` and a brief `detail`.

### Docker

Build and run tests in a container:

```
./test.sh
```

Notes:
- `docker-compose.yml` passes through env if set; there are no defaults to fixtures. The adapter’s own discovery logic picks the right source.
- No backend service is started by compose; backend calls are disabled unless `SYN_BACKEND_URL` is set.

## Spec

See `docs/mcp_spec.md` for deterministic IO contracts and limits.

## Status

✅ Spec pinned in `docs/mcp_spec.md`
✅ Minimal implementation with tests
