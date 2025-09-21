# MCP Spec (Python v0.2.3)

**Keywords:** **MUST**, **MUST NOT**, **SHOULD**, **MAY** follow RFC 2119.

---

## 1. Purpose

The MCP adapter exposes **schemas**, **examples**, **validation**, **diff**, and **backend populate** as deterministic and stateless tools.

* **Resources:** served from disk, overridable via environment variables.
* **Tools:** Validation (JSON Schema Draft 2020-12), Diff (RFC 6902: `add`,`remove`,`replace`), Backend populate.
* **Transport:** All tools are available over **STDIO** using **JSON-RPC 2.0**.
* **Guards:** Assets MUST be validated before persistence. Schemas MUST NOT be mutated.

---

## 2. Boundaries

* **Stateless.** The adapter does not persist data. All resources are read from the filesystem.

* **Schema sources (priority order):**

  1. `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR`
  2. Submodule: `libs/synesthetic-schemas/jsonschema`, `libs/synesthetic-schemas/examples`
  3. If neither exists: listings are empty; `get_*` return not-found

  No fixture fallback. The submodule is SSOT when env overrides are not provided.

* **Refresh:** Files are read on process start only. No polling.

* **Backend:** Enabled only if `SYN_BACKEND_URL` is set. HTTP client timeout 5 s. No retries. `SYN_BACKEND_ASSETS_PATH` MAY override POST path.

---

## 3. Transport & Framing (STDIO)

* **Protocol:** JSON-RPC 2.0 messages. Every request/response MUST include `"jsonrpc": "2.0"`.
* **Framing:** **NDJSON** (one UTF-8 JSON object per line, `\n` delimiter).
* **Batch:** Not supported. Exactly one request per line.
* **Size guard:** Requests exceeding **1 MiB** (UTF-8 bytes) MUST be rejected pre-parse with `{ "ok": false, "reason": "validation_failed", "errors": [{ "path": "", "msg": "payload_too_large" }] }`.
* **IDs:** `id` MUST be string or number; server echoes unchanged.
* **Logging hygiene:**

  * **stdout:** JSON-RPC frames only.
  * **stderr:** all logs, diagnostics, tracebacks.
* **Concurrency:** Requests are queued and processed sequentially. Responses are emitted in request order.
* **Readiness:**

  * On entering the RPC loop (post-discovery), create `MCP_READY_FILE` (default `/tmp/mcp.ready`).
  * File content: `<pid> <ISO8601 timestamp>\n`.
  * Remove on graceful shutdown; best-effort remove on fatal error.
* **Shutdown:** On SIGINT/SIGTERM, the server MUST finish any in-flight request before exiting.

### Request/Response Example

Each JSON-RPC message is one UTF-8 line terminated with `\n`.

**Request (client → server):**

```json
{"jsonrpc":"2.0","id":1,"method":"list_schemas","params":{}}
```

**Response (server → client):**

```json
{"jsonrpc":"2.0","id":1,"result":{"ok":true,"schemas":[{"name":"synesthetic-asset","version":"0.7.0","path":"libs/synesthetic-schemas/jsonschema/synesthetic-asset.json"}]}}
```

Rules illustrated:

* `"jsonrpc": "2.0"` always present.
* `"id"` echoed unchanged.
* `"method"` maps directly to tool (`list_schemas`).
* Response wraps tool output in `"result"`.
* One line per frame, no pretty-printing or extra whitespace.

---

## 4. IO Contracts

All tools MUST return deterministic JSON result objects over STDIO.

* `list_schemas()`
  → `{ "ok": true, "schemas": [{ "name": string, "version": string, "path": string }] }`

* `get_schema(name)`
  → `{ "ok": true, "schema": object, "version": string }`
  → `{ "ok": false, "reason": "not_found" }`

* `list_examples(component | "all")`
  → `{ "ok": true, "examples": [{ "component": string, "path": string }] }`

* `get_example(path)`
  → `{ "ok": true, "example": object, "schema": string, "validated": bool }`
  → `{ "ok": false, "reason": "not_found" }`
  *`validated` = validated at call time against the returned `schema`.*

* `validate_asset(asset, schema)` **(schema REQUIRED)**
  → `{ "ok": bool, "errors"?: [{ "path": string, "msg": string }], "reason"?: "validation_failed" }`

* `diff_assets(base, new)`
  → `{ "ok": true, "patch": [{ "op": "add"|"remove"|"replace", "path": string, "value"?: any }] }`

* `populate_backend(asset, validate_first)`

  * Success: `{ "ok": true, "asset_id": string, "backend_url": string }`
  * Error: `{ "ok": false, "reason": "validation_failed"|"backend_error"|"unsupported", "errors"?: array, "status"?: int, "detail"?: string }`

---

## 5. Determinism

* **Sorting:**

  * `list_schemas` by `name`, then `version`, then `path`
  * `list_examples` by `component`, then `path`

* **Validation errors:**

  * Paths MUST be absolute RFC 6901 JSON Pointers.
  * Use `/` as separator on all platforms.
  * Sort by `path`, then `msg`.

* **Diff:**

  * Allowed ops: `add`, `remove`, `replace`.
  * Object keys processed in sorted order.
  * Arrays replaced wholesale with a single `replace`.
  * Patch items sorted by `path`; if equal, `remove` < `add` < `replace`.
  * Determinism MUST NOT produce an invalid patch.

---

## 6. Error Model

* **Validation error**

  ```json
  { "ok": false, "reason": "validation_failed",
    "errors": [{ "path": "/shader/uniforms/0", "msg": "expected number" }] }
  ```

* **Backend error**

  ```json
  { "ok": false, "reason": "backend_error", "status": 500, "detail": "internal error" }
  ```

* **Unsupported**

  ```json
  { "ok": false, "reason": "unsupported", "detail": "tool not implemented" }
  ```

* **Network error**

  ```json
  { "ok": false, "reason": "backend_error", "status": 503, "detail": "network_unreachable" }
  ```

* **Payload too large**

  ```json
  { "ok": false, "reason": "validation_failed",
    "errors": [{ "path": "", "msg": "payload_too_large" }] }
  ```

---

## 7. Environment Variables

| Variable                  | Default                | Use              | Meaning                                                     |
| ------------------------- | ---------------------- | ---------------- | ----------------------------------------------------------- |
| `MCP_READY_FILE`          | `/tmp/mcp.ready`       | startup          | Created when ready, removed on shutdown.                    |
| `SYN_SCHEMAS_DIR`         | —                      | schema discovery | Overrides schema directory (required if submodule missing). |
| `SYN_EXAMPLES_DIR`        | —                      | schema discovery | Overrides examples directory.                               |
| `SYN_BACKEND_URL`         | —                      | backend          | Enables populate. If unset, backend is disabled.            |
| `SYN_BACKEND_ASSETS_PATH` | `/synesthetic-assets/` | backend          | Override path for backend POST.                             |

---

## 8. Dependencies

* **Runtime:** `jsonschema`, `httpx`
* **Tests:** `pytest`
* **Optional:** `referencing`
* **Dev (optional):** `ruff`, `mypy`
* **Python:** ≥ 3.11
* **Validation:** Draft 2020-12. If `$id` missing, base URI derived from file path.
* **Backend:** `httpx` 5 s timeout, no retries.
* **Limits:** 1 MiB per request (UTF-8 bytes of JSON line).

---

## 9. Aliases and Examples

* **Alias:** `nested-synesthetic-asset` MUST validate against canonical `synesthetic-asset`.
* Submodule examples MUST validate as nested assets.
* During alias validation, ignore top-level `$schemaRef` (do not resolve it).

---

## 10. CLI and Process Model

* **Validation CLI:**

  * `python -m mcp --validate <path>` emits JSON result.
  * Exit codes: 0 success, 1 validation failed, 2 IO/parse error.

* **STDIO server:**

  * Blocking JSON-RPC loop over stdin/stdout (NDJSON).
  * Logs `mcp:ready mode=stdio` on readiness (stderr).
  * Creates `MCP_READY_FILE` on startup; removes on exit.
  * On SIGINT/SIGTERM, MUST complete in-flight request then exit.

---

## 11. Exit Criteria

* `pip install -r requirements.txt && pip install -e .` succeeds.
* `python -c "import mcp; print(mcp.__version__)"` works.
* `pytest -q` passes.
* Listings and validation errors deterministic.
* Tools respond consistently over STDIO.
* Implementation, docs, and tests match this spec exactly.
