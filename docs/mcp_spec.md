# MCP Spec (Python v0.1.0)

## Purpose

Expose schemas, examples, validation, diff, and optional persistence as deterministic tools. Keep the adapter lightweight and stateless.

* Resources: serve schemas and examples from disk (env-overridable dirs).
* Tools: validation (Draft 2020-12), diff (RFC6902 add/remove/replace), backend populate.
* Guards: enforce schema compliance before persistence; never mutate schemas.

## Boundaries

* Stateless: no durable storage; reads schemas/examples from filesystem.
* Schema source: JSON Schemas and examples on disk.

  * Lookup order:

    1. Env overrides: `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR`
    2. Submodule: `libs/synesthetic-schemas/jsonschema`, `libs/synesthetic-schemas/examples`
  * If neither exists, listings may be empty and get operations return not found.
  * No local fixture fallback; the submodule is the single source of truth.
  * Refresh by process restart; no polling.
* Backend: optional via `SYN_BACKEND_URL`; 5s timeout; no retries.
* Optional env knob: `SYN_BACKEND_ASSETS_PATH` may override the POST path for asset creation.

---

## IO Contracts

* `list_schemas()`:
  `{ ok: bool, schemas: [{ name: str, version: str, path: str }] }`

* `get_schema(name)`:
  `{ ok: bool, schema: object, version: str }`

* `list_examples(component|'*')`:
  `{ ok: bool, examples: [{ component: str, path: str }] }`

* `get_example(path)`:
  `{ ok: bool, example: object, schema: str, validated: bool }`

* `validate_asset(asset, schema)`:
  `{ ok: bool, errors: [{ path: str, msg: str }], reason?:'validation_failed' }`

* `diff_assets(base, new)`:
  `{ ok: bool, patch: [{ op: 'add'|'remove'|'replace', path: str, value? }] }`

* `populate_backend(asset, validate_first)`:

  * Success: `{ ok: true, asset_id: str, backend_url: str }`
  * Error: `{ ok: false, reason: 'validation_failed'|'backend_error'|'unsupported', errors?, status?, detail? }`

---

## Determinism

* Sorting: `list_schemas` by name/version/path; `list_examples` by component/path.
* Validation errors: RFC6901 pointers from absolute path; sort by path then message.
* Diff: only `add`, `remove`, `replace` ops.
  Dict keys processed sorted; lists replaced as a single `replace` op; output sorted by path, then op order remove < add < replace.

---

## Error Model

* **Validation errors**

  ```json
  { "ok": false, "reason": "validation_failed",
    "errors": [{ "path":"/shader/uniforms/0", "msg":"expected number" }] }
  ```

* **Backend errors**

  ```json
  { "ok": false, "reason":"backend_error", "status":500, "detail":"…" }
  ```

* **Unsupported tool/resource**

  ```json
  { "ok": false, "reason":"unsupported", "msg":"tool not implemented" }
  ```

* **Network errors** (timeouts, refused connections)

  ```json
  { "ok": false, "reason":"backend_error", "status":503, "detail":"network_unreachable" }
  ```

---

## Implementation Notes

* Language: Python >= 3.11.
* Minimal deps in `requirements.txt`: `jsonschema`, `httpx`, `pytest`.
* Optional extras: `fastapi` (HTTP app), `uvicorn` (dev server), `referencing` (enhanced JSON Schema refs; import is optional).

---

## Discovery Order (Authoritative)

1. Env overrides first: `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR`.
2. Submodule second: `libs/synesthetic-schemas/` paths (`jsonschema/`, `examples/`).
3. No fixture fallback: if neither exists, listings are empty and get operations return not found.

## Dependencies (Scope)

- Runtime: `jsonschema`, `httpx`
- Tests: `pytest`
- Dev (optional): `ruff`, `mypy`
- Extras (optional): `fastapi`, `uvicorn`, `referencing`
* JSON Schema: Draft 2020-12; base-URI set from file path when `$id` missing.
* Backend: disabled unless `SYN_BACKEND_URL` set; `httpx` timeout 5s; no retries.
* Limits: 1 MiB max payload; read-only FS except reading schemas/examples.
* **Nested alias**:

  * Alias: `nested-synesthetic-asset`
  * Maps to canonical `synesthetic-asset` schema.
  * Used for submodule examples like `SynestheticAsset_Example*.json`.
  * Alias validation ignores top-level `$schemaRef` fields in examples.

---

## Repo Layout

See `README.md`.

---

## Exit Criteria

* Requirements install succeeds; `import mcp` exposes `__version__`.
* `pytest -q` passes.
* Deterministic ordering for listings and validation errors.
* Spec matches implementation choices above.
