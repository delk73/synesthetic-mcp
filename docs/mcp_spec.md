## Version v0.2.6 (Current)

### 1. Purpose

The MCP adapter exposes **schemas**, **examples**, **validation**, **diff**, and **backend populate** as deterministic and stateless tools.

* **Resources:** served from disk, overridable via environment variables.  
* **Tools:** Validation (JSON Schema Draft 2020-12), Diff (RFC 6902: `add`,`remove`,`replace`), Backend populate.  
* **Transport:**
  * Ephemeral: **STDIO** over **JSON-RPC 2.0** (default).  
  * Persistent: **Socket** (Unix Domain Socket) over JSON-RPC 2.0.  
  * **NEW:** Optional **TCP transport** MAY be exposed for containerized setups where UDS mounting is impractical.  
* **Guards:** Assets MUST be validated before persistence. Schemas MUST NOT be mutated.

---

### v0.2.6 Additions

* **TCP mode:** `MCP_ENDPOINT=tcp` starts a TCP listener on `MCP_HOST:MCP_PORT` (defaults `0.0.0.0:7000`).
  * Same NDJSON JSON-RPC framing as STDIO/Socket.  
  * Preserves per-connection frame ordering.  
  * Logs `mcp:ready mode=tcp host=<h> port=<p>` on startup.  
  * Shutdown log mirrors the ready event and includes schema/example directories.  
* **Docs & scripts:** Up/down scripts, Dockerfile, and compose definitions updated to support TCP as first-class alongside STDIO and socket.  
* **Audit hardening:** Integration tests MUST cover TCP round-trip (list_schemas + validate).  
* **Observability:** Ready/shutdown logs MUST now include `schemas_dir` and `examples_dir` for all transports (STDIO, socket, TCP).  
* **Timestamps:** Ready and shutdown logs emit ISO-8601 UTC timestamps with each event.  

---

### Exit Criteria (v0.2.6)

* TCP transport works end-to-end, defaulting to `MCP_HOST=0.0.0.0`, `MCP_PORT=7000`.  
* `up.sh` and docker-compose bring up container with socket or TCP, no permission regressions.  
* Readiness logs show mode + address/path + schemas_dir + examples_dir.  
* All transports pass golden request/response tests.  
* Implementation, docs, and tests aligned.

---

## Version v0.2.5 (Previous)

### Additions in v0.2.5

* **Batch validation:** `validate_many` enforces `MCP_MAX_BATCH` (default 100). Oversized batch returns `{ "ok": false, "reason": "unsupported" }`.  
* **Non-root container:** Docker image MUST drop root privileges and still surface the ready file under `/tmp`.  
* **Expanded logging:** readiness logs include transport mode, socket path (if applicable), and schema/example roots.  
* **Alias lifecycle:** `"validate"` alias remains accepted but MUST emit a deprecation warning to stderr.  
* **Test coverage:** regression tests cover traversal rejection, socket multi-client ordering, and payload oversize guards across transports and batch validation.

### Exit Criteria (v0.2.5)

* `validate_many` enforces `MCP_MAX_BATCH`. Oversized batch returns `unsupported`.  
* Container builds/runs as non-root.  
* Readiness logs show `mode`, `path`, and `schemas_dir`.  
* `"validate"` alias accepted, with stderr deprecation warning.  
* Tests pass for traversal rejection, socket multi-client behavior, and oversize guards.  
* Implementation, docs, and tests remain aligned.

---

## Backlog (≥ v0.3)

* Drop `"validate"` alias entirely.  
* Add gRPC transport for typed schemas and streaming.  
* Structured metrics/telemetry hooks.  
* Schema hot-reload or live discovery.
