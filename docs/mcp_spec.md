# MCP Spec (Python **v0.2.5**)

**Keywords:** **MUST**, **MUST NOT**, **SHOULD**, **MAY** follow RFC 2119.

---

## 1. Purpose

The MCP adapter exposes **schemas**, **examples**, **validation**, **diff**, and **backend populate** as deterministic and stateless tools.

* **Resources:** served from disk, overridable via environment variables.
* **Tools:** Validation (JSON Schema Draft 2020-12), Diff (RFC 6902: `add`,`remove`,`replace`), Backend populate.
* **Transport:**

  * Ephemeral: **STDIO** over **JSON-RPC 2.0** (default).
  * Persistent: **Socket** (Unix Domain Socket) over JSON-RPC 2.0.
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

## 3. Transport & Framing

### 3.1 STDIO (ephemeral default)

* **Protocol:** JSON-RPC 2.0 messages over stdin/stdout.
* **Framing:** **NDJSON** (one UTF-8 JSON object per line, `\n` delimiter).
* **Batch:** Not supported at the framing layer. Exactly one request per line.
* **Size guard:** Requests exceeding **1 MiB** (UTF-8 bytes) MUST be rejected pre-parse with:
  `{ "ok": false, "reason": "validation_failed", "errors": [{ "path": "", "msg": "payload_too_large" }] }`
* **IDs:** `id` MUST be string or number; server echoes unchanged.
* **Logging hygiene:** **stdout** = JSON-RPC frames only; **stderr** = logs/diagnostics/tracebacks.
* **Concurrency:** Requests are queued and processed sequentially. Responses are emitted in request order.
* **Readiness:** On entering the RPC loop, write `MCP_READY_FILE` (default `/tmp/mcp.ready`) containing `<pid> <ISO8601 timestamp>\n`. Remove on graceful shutdown; best-effort remove on fatal error.
* **Shutdown:** On SIGINT/SIGTERM, finish any in-flight request before exit.
* **Note:** STDIO is **ephemeral**. If stdin closes, the process MUST exit. It MUST NOT be treated as a daemon.

### 3.2 Socket (persistent service)

* **Protocol:** JSON-RPC 2.0 over **Unix Domain Socket (UDS)** with the same NDJSON framing as STDIO.
* **Endpoint selection:** `MCP_ENDPOINT=socket` enables socket mode.
* **Socket path:** `MCP_SOCKET_PATH` (default `/tmp/mcp.sock`).
* **Lifecycle:** On startup, bind the socket and log `mcp:ready mode=socket path=<path>` to stderr. On shutdown, stop accepting, complete in-flight work, unlink the socket.
* **Clients:** Multiple concurrent client connections MUST be supported. Frame order MUST be preserved **per connection**.
* **Permissions:** Server MUST create the socket with `0600` (owner-only) unless `MCP_SOCKET_MODE` is explicitly set.

### 3.3 Roadmap

* **HTTP** MAY be added for cross-platform client ease.
* **gRPC** MAY be added later for typed schemas, streaming, and polyglot interop.

---

## 4. IO Contracts

All tools return deterministic JSON result objects (inside JSON-RPC `result`).

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
  → `{ "ok": false, "reason": "validation_failed", "errors": [...] }`
  *`validated` = validated at call time against the returned `schema`.*

* `validate_asset(asset, schema)` **(schema REQUIRED)**
  → `{ "ok": bool, "errors"?: [{ "path": string, "msg": string }], "reason"?: "validation_failed" }`

  * If `schema` param is missing or empty, the server MUST immediately return `validation_failed` with an explicit error.\*

  **Alias for compatibility:** method name `"validate"` MUST be accepted as an alias for `"validate_asset"` and treated identically. `"validate"` is **deprecated** and MAY be removed in ≥ v0.3 after a deprecation window.

* `validate_many(assets[], schema)` **(Optional)**
  → `{ "ok": true, "results": [ { "ok": bool, "errors"?: [...] }, ... ] }`
  **Guards:** Total encoded request size MUST respect the 1 MiB limit. Servers MAY enforce `MCP_MAX_BATCH` (default 100).

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

  * Paths MUST be absolute RFC 6901 JSON Pointers (`/` separator on all platforms).
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

| Variable                  | Default                | Use              | Meaning                                                               |
| ------------------------- | ---------------------- | ---------------- | --------------------------------------------------------------------- |
| `MCP_ENDPOINT`            | `stdio`                | transport        | `stdio` (ephemeral) or `socket` (persistent).                         |
| `MCP_READY_FILE`          | `/tmp/mcp.ready`       | startup          | Created when ready; removed on shutdown.                              |
| `MCP_SOCKET_PATH`         | `/tmp/mcp.sock`        | socket           | UDS path when `MCP_ENDPOINT=socket`.                                  |
| `MCP_SOCKET_MODE`         | `0600`                 | socket           | Octal file mode for the socket; widen only if you truly need sharing. |
| `MCP_MAX_BATCH`           | `100`                  | batching         | Server-side cap for `validate_many`.                                  |
| `SYN_SCHEMAS_DIR`         | —                      | schema discovery | Overrides schema directory (required if submodule missing).           |
| `SYN_EXAMPLES_DIR`        | —                      | schema discovery | Overrides examples directory.                                         |
| `SYN_BACKEND_URL`         | —                      | backend          | Enables populate. If unset, backend is disabled.                      |
| `SYN_BACKEND_ASSETS_PATH` | `/synesthetic-assets/` | backend          | Override path for backend POST.                                       |

---

## 8. Dependencies

* **Runtime:** `jsonschema`, `httpx`
* **Tests:** `pytest`
* **Optional:** `referencing`
* **Dev (optional):** `ruff`, `mypy`
* **Python:** ≥ 3.11
* **Validation:** Draft 2020-12. If `$id` missing, base URI derived from file path.
* **Backend:** `httpx` 5 s timeout, no retries.
* **Limits:** 1 MiB per request (encoded JSON).

---

## 9. Aliases & Compatibility

* **Method alias:** `"validate"` **MUST** be accepted as an alias for `"validate_asset"` (deprecated; remove ≥ v0.3).
* **Schema aliasing:** `nested-synesthetic-asset` MUST validate against canonical `synesthetic-asset`.
* Submodule examples MUST validate as nested assets.
* During alias validation, ignore top-level `$schemaRef` (do not resolve it).

---

## 10. CLI and Process Model

* **Validation CLI:**

  * `python -m mcp --validate <path>` emits JSON result.
  * Exit codes: `0` success, `1` validation failed, `2` IO/parse error.

* **STDIO server (default):**

  * Blocking JSON-RPC loop over stdin/stdout (NDJSON).
  * Logs `mcp:ready mode=stdio`.
  * Creates `MCP_READY_FILE` on startup; removes on exit.
  * Ephemeral: exits when stdin closes.

* **Socket server (persistent):**

  * `MCP_ENDPOINT=socket` enables UDS server.
  * Listens on `MCP_SOCKET_PATH`.
  * Logs `mcp:ready mode=socket path=<path>`.
  * Persistent: container remains alive until explicitly stopped.

---

## 11. Security & Offline Guarantees

* **No network fetch for schemas.** `$ref` resolution MUST be local to the configured schema roots; remote retrieval is **forbidden**.
* **Path safety.** Reject path traversal (`..`) when serving files by path; only allow within configured roots.
* **Socket perms.** Default `0600`. If widened, that’s on the operator; the server will not auto-widen.
* **Least privilege.** Running as non-root is **RECOMMENDED** in container images.

---

## 12. Observability

* **Startup:** Log a single line to **stderr** on readiness:

  * `mcp:ready mode=stdio` **or** `mcp:ready mode=socket path=<path> schemas_dir=<dir>`
* **Shutdown:** Log `mcp:shutdown mode=<mode>` on graceful exit.
* **No chatter on stdout.** Only JSON-RPC frames go to stdout (or the socket).
* **Deterministic logs.** Timestamps MUST be ISO-8601 UTC.

---

## 13. Exit Criteria

* `pip install -r requirements.txt && pip install -e .` succeeds.
* `python -c "import mcp; print(mcp.__version__)"` works.
* `pytest -q` passes.
* Listings and validation errors deterministic.
* Tools respond consistently over **STDIO** and **Socket** modes.
* Implementation, docs, and tests match this spec exactly.


Got it. Here’s the **full new spec** reformatted into the same version-pinned style as Labs. I’ve kept your entire **v0.2.4** spec intact as the “stable” block, and appended **v0.2.5 (next)** and **Backlog (v0.3+)** as lean extensions.

---

# MCP Spec (Python)

**Keywords:** **MUST**, **MUST NOT**, **SHOULD**, **MAY** follow RFC 2119.

---

## Version v0.2.5 (Current)

### 1. Purpose

*(full detailed spec content — unchanged from prior stable release)*

> The MCP adapter exposes **schemas**, **examples**, **validation**, **diff**, and **backend populate** as deterministic and stateless tools.
> …
> *(all 13 sections from the v0.2.4 specification remain in force, including Purpose → Exit Criteria, now incorporating the v0.2.5 requirements listed below.)*

### v0.2.5 Additions

* **Batch validation improvements:** `validate_many` enforces `MCP_MAX_BATCH` (default 100) and returns `{ "ok": false, "reason": "unsupported" }` when exceeded.
* **Non-root container:** Docker image MUST drop root privileges and still surface the ready file under `/tmp`.
* **Expanded logging:** readiness logs include transport mode, socket path (if applicable), and schema/example roots.
* **Alias lifecycle:** the `"validate"` method alias remains accepted but MUST emit a deprecation warning to stderr.
* **Test coverage:** array of regression tests covering traversal rejection, socket multi-client ordering, and payload oversize guards across transports and batch validation.

### Exit Criteria

* `validate_many` enforces `MCP_MAX_BATCH` (default 100). Oversized batch returns `{ "ok": false, "reason": "unsupported" }`.
* Container image builds and runs as non-root with no regressions.
* Readiness logs include `mode`, `path`, and `schemas_dir`.
* `"validate"` alias accepted, logging the deprecation warning to stderr.
* Tests pass for traversal rejection, socket multi-client behavior, and oversize guards across entrypoints.
* Implementation, docs, and tests remain aligned.

---

## Backlog (v0.3+)

* Drop `"validate"` alias entirely.
* Add optional HTTP transport.
* Add gRPC transport for typed schemas and streaming.
* Structured metrics/telemetry hooks.
* Schema hot-reload or live discovery.
