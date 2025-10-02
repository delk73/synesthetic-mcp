---
version: v0.2.7
lastReviewed: 2025-10-01
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

---

## v0.2.7 Additions

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

## Exit Criteria (v0.2.7)

* TCP transport works end-to-end, default `MCP_HOST=0.0.0.0`, `MCP_PORT=7000`.  
* All transports (STDIO, socket, TCP) enforce 1 MiB guard.  
* Ready/shutdown logs show mode, address/path, schemas_dir, examples_dir, and ISO timestamps.  
* **Shutdown log invariant holds across all transports.**  
* Signal exits produce documented codes.  
* Tests cover TCP round-trip, oversize payload, multi-client ordering, and alias lifecycle.  
* README/docs reflect actual implementation.  

---

## Version v0.2.6 (Previous)

### Additions in v0.2.6

* **TCP mode:** `MCP_ENDPOINT=tcp` starts a TCP listener on `MCP_HOST:MCP_PORT` (defaults `0.0.0.0:7000`).  
* Same NDJSON framing as STDIO/Socket.  
* Per-connection frame ordering preserved.  
* Logs `mcp:ready mode=tcp host=<h> port=<p>`.  
* Shutdown log mirrors ready event with schema/example dirs.  
* Integration tests must cover TCP.  
* Ready/shutdown logs must include schema/example dirs for all transports.  
* Ready/shutdown logs emit ISO-8601 UTC timestamps.  

### Exit Criteria (v0.2.6)

* TCP transport works end-to-end, default host/port.  
* Up/down scripts support TCP alongside socket.  
* Readiness logs include mode + address/path + schemas_dir + examples_dir.  
* All transports pass golden request/response tests.  
* Implementation, docs, and tests aligned.  

---

## Backlog (≥ v0.3)

* Drop `"validate"` alias entirely.  
* Add gRPC transport for typed schemas and streaming.  
* Structured metrics/telemetry hooks.  
* Schema hot-reload or live discovery.  
