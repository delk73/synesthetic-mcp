---
version: v0.2.8
lastReviewed: 2025-10-03
owner: mcp-core
---

# MCP Spec

## Purpose

The MCP adapter exposes **schemas**, **examples**, **validation**, **diff**, and **backend populate** as deterministic and stateless tools.

* **Resources:** served from disk, overridable via environment variables.  
* **Tools:** Validation (JSON Schema Draft 2020-12), Diff (RFC 6902: `add`,`remove`,`replace`), Backend populate.  
* **Transport:**
  * Ephemeral: **STDIO** over **JSON-RPC 2.0**.  
  * Persistent: **Socket** (Unix Domain Socket) over JSON-RPC 2.0.  
  * **TCP transport**: first-class option for containerized or distributed setups.  
* **Guards:** Assets MUST be validated before persistence. Schemas MUST NOT be mutated.  
* **Limits:** All transports enforce a **1 MiB payload cap**.  
* **Schema key:** Assets MUST include a top-level `"$schema"` field, per JSON Schema Draft 2020-12.  
  * MCP validators MUST reject assets missing this field.  
  * Legacy `"schema"` (no `$`) and `$schemaRef` keys are not valid and MUST NOT be used.

---

## v0.2.8 Additions

* **Schema alignment**  
  * All assets MUST declare their validating schema with `"$schema"`.  
  * Strict validation enforces presence of `"$schema"`.  
  * `$schemaRef` and `"schema"` are deprecated and MUST NOT be emitted.  
  * MCP validation functions (`validate_asset`, `validate_many`) take no `schema` parameter; validation MUST rely solely on the `"$schema"` field inside the asset.  
  * STDIO and other transports MUST NOT require `"schema"` in params.  
  * MCP responses MUST NOT backfill `schema` into payloads.  
  * A regression guard MUST ensure that all shipped examples include a valid `"$schema"` marker.

* **TCP transport fully aligned**  
  * TCP enforces the same **1 MiB guard** as STDIO/socket.  
  * Ready logs:  
    ```
    mcp:ready mode=tcp host=<h> port=<p> schemas_dir=<...> examples_dir=<...> timestamp=<ISO-8601 UTC>
    ```  
  * Shutdown logs MUST mirror ready logs with the same fields, differing only in `event=shutdown`.  
  * Documentation updated with **example usage**:  
    ```bash
    nc 127.0.0.1 8765
    ```  
    to send JSON-RPC frames over TCP.  

* **Lifecycle signals**  
  * SIGINT/SIGTERM shutdowns return exit code `-SIGINT`/`-SIGTERM`.  
  * **Logging invariant:** shutdown logs MUST always be emitted *before* process exit, even under signal termination. Self-kill (`os.kill`) MUST NOT pre-empt shutdown logging.  
  * Ready file format: `<pid> <ISO8601 timestamp>`.  

* **Documentation alignment**  
  * README and spec now state payload guard applies to **STDIO, socket, and TCP**.  
  * Serving Locally section includes TCP client example.  

---

## Exit Criteria (v0.2.8)

* TCP transport works end-to-end, default `MCP_HOST=0.0.0.0`, `MCP_PORT=7000`.  
* All transports (STDIO, socket, TCP) enforce 1 MiB guard.  
* Ready/shutdown logs show mode, address/path, schemas_dir, examples_dir, and ISO timestamps.  
* **Shutdown log invariant holds across all transports.**  
* Signal exits produce documented codes.  
* Tests cover TCP round-trip, oversize payload, multi-client ordering, and alias lifecycle.  
* Assets with `"$schema"` pass strict validation.  
* Assets with `"schema"` or `$schemaRef` are rejected.  
* Validation functions take no schema argument and rely solely on asset['$schema'].  
* Transports do not require `schema` params and do not set legacy `schema` fields in payloads.  
* Regression tests confirm all examples in `libs/synesthetic-schemas/examples` include `"$schema"`.  
* README/docs reflect actual implementation.  

---

## Version v0.2.7 (Previous)

* Schema key field was ambiguous (`"schema"`, `$schemaRef`).  
* v0.2.8 standardizes to `"$schema"` only.  

---

## Backlog (≥ v0.3)

* Drop `"validate"` alias entirely.  
* Add gRPC transport for typed schemas and streaming.  
* Structured metrics/telemetry hooks.  
* Schema hot-reload or live discovery.  
