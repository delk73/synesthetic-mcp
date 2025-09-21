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
  MCP["synesthetic-mcp\n(MCP Adapter: discovery, validation, diff, backend proxy)"]
  BE["sdfk-backend\n(Python API & CRUD store)"]
  SSOT["synesthetic-schemas\n(SSOT: JSON Schemas + Python bindings)"]

  MCP --> |"Validates assets (Protobuf/JSON)"| BE
  MCP --> |"Consumes Python pkg (submodule)"| SSOT
  BE --> |"Consumes Python pkg (submodule)"| SSOT

  %% Grayscale theme, MCP slightly lighter to highlight
  style MCP fill:#555555,stroke:#ffffff,stroke-width:2px,color:#ffffff
  style BE fill:#333333,stroke:#cccccc,stroke-width:1.5px,color:#ffffff
  style SSOT fill:#222222,stroke:#cccccc,stroke-width:1.5px,color:#ffffff
```

## Features

- Schema and example discovery
- JSON Schema validation (Draft 2020-12)
- RFC6902 diff (add/remove/replace only)
- Backend population (optional via `SYN_BACKEND_URL`)
- Canonical STDIO JSON-RPC loop (transport locked to STDIO)
- Per-request 1 MiB STDIO payload guard enforced before parsing

## Quickstart

1. Install deps: `pip install -r requirements.txt && pip install -e .`
2. Initialize schemas/examples: `git submodule update --init --recursive`.
3. Serve via Compose: `docker compose up serve` (runs the STDIO JSON-RPC loop, logs `mcp:ready mode=stdio`, and exposes `/tmp/mcp.ready` for health checks).
4. Or run the helper: `./serve.sh` builds the image, waits for a ready container, then tails logs.
5. Validate an asset locally: `python -m mcp --validate libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json`.

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
tests/
  test_validate.py
  test_diff.py
  test_backend.py
  test_env_discovery.py
  test_stdio.py
  test_submodule_integration.py  
```

## Development

* Python >= 3.11
* Install deps (minimal): `pip install -r requirements.txt`
  - Minimal deps: `jsonschema`, `httpx`, `pytest`
  - Optional extras: `referencing` (enhanced JSON Schema refs; import is optional)
  - Dev (optional): `ruff`, `mypy`
* Import check: `python -c "import mcp; print(mcp.__version__)"`
* Run tests: `pytest -q`
* Runtimes:
  - `python -m mcp` (canonical STDIO JSON-RPC loop; logs `mcp:ready mode=stdio` and blocks on stdin/stdout).
  - `python -m mcp.stdio_main` (invoke the loop directly when embedding).

## Dependencies

- Runtime: `jsonschema`, `httpx`
- Tests: `pytest`
- Dev (optional): `ruff`, `mypy`
- Extras (optional): `referencing` (ref handling performance/behavior)

## Environment

| Variable | Default | Behaviour |
| - | - | - |
| `MCP_ENDPOINT` | `stdio` | Transport selector fixed to STDIO. Any other value raises a setup failure. |
| `MCP_READY_FILE` | `/tmp/mcp.ready` | File touched on startup with `<pid> <ISO8601>` and removed on shutdown; Compose health checks test for its presence. Override when sandboxed. |
| `SYN_SCHEMAS_DIR` | `libs/synesthetic-schemas/jsonschema` when present | Overrides schema directory; required when submodule absent. Startup fails if the directory is missing. |
| `SYN_EXAMPLES_DIR` | `libs/synesthetic-schemas/examples` when present | Overrides examples directory; discovery falls back to submodule if unset. |
| `SYN_BACKEND_URL` | unset | Enables backend POSTs; missing keeps populate disabled (`unsupported`). |
| `SYN_BACKEND_ASSETS_PATH` | `/synesthetic-assets/` | Custom path for backend POST requests. |

`.env.example` captures these defaults for quick copying into local shells or Compose.

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
- Unsupported tool/resource: `{ ok:false, reason:'unsupported', detail }`
- Network errors map to backend_error with `status:503` and a brief `detail`.
- Payload too large (>1 MiB on STDIO): `{ ok:false, reason:'validation_failed', errors:[{ path:'', msg:'payload_too_large' }] }`

## CLI Usage

```
$ python -m mcp --validate path/to/asset.json
{"ok": true, "errors": [], "schema": "nested-synesthetic-asset"}
```

- Exit code `0`: validation succeeded.
- Exit code `1`: validation failed (payload includes `reason: validation_failed`).
- Exit code `2`: input errors (file missing, unreadable, or invalid JSON).

### Docker

Build and run tests in a container:

```
./test.sh
```

Notes:
- `docker-compose.yml` passes through env if set; there are no defaults to fixtures. The adapter’s own discovery logic picks the right source.
- No backend service is started by compose; backend calls are disabled unless `SYN_BACKEND_URL` is set.

### Serving Locally

- `docker compose up serve` (or `./serve.sh`) builds the image, starts `python -m mcp`, waits for `/tmp/mcp.ready`, and then tails logs.
- Transport remains STDIO-only; any alternate `MCP_ENDPOINT` value fails fast during startup.
- STDIO requests above 1 MiB (UTF-8 bytes) are rejected before parsing with `payload_too_large`.

## Spec

See `docs/mcp_spec.md` for deterministic IO contracts and limits.

## Status

✅ Spec pinned in `docs/mcp_spec.md`
✅ Minimal implementation with tests
