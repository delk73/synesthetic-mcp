---
version: 0.1.0
owner: delk73
lastReviewed: 2025-09-12
---

# MCP Spec (Python v1)

## Purpose
Expose Synesthetic schemas, examples, and validation as **MCP resources and tools**.  
Keep the server lightweight, stateless, and strictly an adapter:

- **Resources**: read-only access to schemas and examples.  
- **Tools**: validation, patch generation, backend population.  
- **Guards**: enforce SSOT compliance before persistence.  

## Boundaries
- **Stateless**: no durable storage; only in-memory schema cache.  
- **Consumer repos**: import Python bindings from `synesthetic-schemas`.  
- **Backend**: remains CRUD/persistence only.  
- **Lab**: will live in its own repo later.

---

## Resources

- **`schemas/`**  
  - list available schemas (names, versions, paths).  
  - fetch full JSON Schema.  

- **`examples/`**  
  - list examples by component.  
  - fetch example JSON and validate inline.  

- **`assets/` (proxy)**  
  - list assets from backend (optional for v1).  

---

## Tools

- **`list_schemas()`**  
  → `[{"name":"NestedSynestheticAsset","version":"0.7.0","path":"..."}]`

- **`get_schema(name:str)`**  
  → `{ "schema": {...}, "version":"0.7.0" }`

- **`list_examples(component:str)`**  
  → `[{"path":"examples/shader/foo.json"}, …]`

- **`get_example(path:str)`**  
  → `{ "example": {...}, "schema":"Shader", "validated":true }`

- **`validate_asset(asset:dict, schema:str)`**  
  → `{ "ok": true, "errors": [] }`  
  or  
  → `{ "ok": false, "errors":[{"path":"/shader/uniforms/0","msg":"expected number"}] }`

- **`diff_assets(base:dict, new:dict)`**  
  → `{ "ok": true, "patch":[{ "op":"replace","path":"/shader/uniforms/0","value":1.5 }] }`

- **`populate_backend(asset:dict, validate_first:bool=true)`**  
  → `{ "ok": true, "asset_id":"uuid", "backend_url":"http://.../synesthetic-assets/nested/uuid" }`  
  or  
  → `{ "ok": false, "reason":"validation_failed", "errors":[...] }`

---

## Error Model

- **Validation errors**:  
  ```json
  { "ok": false, "reason": "validation_failed",
    "errors": [{ "path":"/shader/uniforms/0", "msg":"expected number" }] }
  ```    

* **Backend errors**:

  ```json
  { "ok": false, "reason":"backend_error", "status":500, "detail":"…" }
  ```

* **Unknown tool/resource**:

  ```json
  { "ok": false, "reason":"unsupported", "msg":"tool not implemented" }
  ```

---

## Implementation (Python)

* **Framework**: FastAPI (HTTP) + stdio adapter.
* **Validation**: reuse `synesthetic-schemas/python` Pydantic + `jsonschema`.
* **HTTP client**: `httpx` for backend calls.
* **Testing**: pytest, golden fixtures for each tool.
* **Packaging**: pip-installable; depends on `synesthetic-schemas` as a submodule or package.

---

## Repo Layout

```
synesthetic-mcp/
  README.md
  docs/
    mcp_spec.md
  mcp/
    __init__.py
    core.py          # schema/example discovery
    validate.py      # validation helpers
    diff.py          # JSON Patch generation
    backend.py       # proxy client
    stdio_main.py    # MCP stdio adapter
    http_main.py     # optional FastAPI adapter
  tests/
    test_validate.py
    test_diff.py
    test_tools.py
    fixtures/
      valid_asset.json
      invalid_asset.json
```

---

## Exit Criteria

* All resources/tools return deterministic JSON.
* CI runs pytest, pre-commit, and validates golden fixtures.
* Backend population tested against a mock backend (no DB dependency).