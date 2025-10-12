---
version: v0.2.9
lastReviewed: 2025-10-12
owner: mcp-core
---

# MCP Spec

## Purpose

The MCP adapter exposes **schemas**, **examples**, **validation**, **diff**, and **backend populate** as deterministic, stateless tools wired directly to the canonical **Synesthetic Schemas v0.7.3** host.

* **Schema base:**  
  `https://delk73.github.io/synesthetic-schemas/schema/0.7.3/`
* **Schema version:**  
  Derived from environment variable `LABS_SCHEMA_VERSION` (default `0.7.3`).
* **Specification source:**  
  [synesthetic-schemas v0.7.3](https://github.com/delk73/synesthetic-schemas)

---

## Core Functions

| Tool | Purpose | Validation Source |
|------|----------|-------------------|
| `validate_asset` | Validate a single asset against its `$schema`. | Remote or cached schema |
| `validate_many` | Batch validation for multiple assets. | Same as above |
| `diff_assets` | Compute RFC 6902 diff (`add`, `remove`, `replace`). | JSON Patch semantics |
| `populate_backend` | Convert validated assets to backend-ready JSON. | Deterministic serialization |

All validation conforms to **JSON Schema Draft 2020-12**.

---

## Transport

* **Ephemeral:** `STDIO` over **JSON-RPC 2.0**.  
* **Persistent:** `Socket` (Unix Domain Socket) over **JSON-RPC 2.0**.  
* **TCP:** first-class transport for distributed or containerized execution.  

**Payload guard:** all transports enforce **1 MiB max payload**.  
**Schema immutability:** schemas must never be modified in-process.

---

## Schema Integration (v0.7.3 Alignment)

* All assets MUST include a top-level `"$schema"` field referencing the canonical host:  
  `https://delk73.github.io/synesthetic-schemas/schema/0.7.3/<schema>.schema.json`
* MCP validation relies exclusively on this field.  
  * `"$schema"` is mandatory.  
  * `"schema"` and `"$schemaRef"` are invalid and rejected.
* The validator automatically fetches or caches the referenced schema.  
* The schema resolver must support both **remote URL resolution** and **local cache lookup** (`/schemas/0.7.3/`).
* **Regression guard:** all shipped examples must include a valid canonical `$schema`.

---

## Logging and Lifecycle

* **Ready log:**
```

mcp:ready mode=<transport> host=<h> port=<p> schemas_base=[https://delk73.github.io/.../0.7.3](https://delk73.github.io/.../0.7.3) timestamp=<ISO-8601>

```
* **Shutdown log:** identical fields plus `event=shutdown`.
* **Signal exits:** `SIGINT` → `-2`; `SIGTERM` → `-15`.
* Shutdown logs must always emit before exit; no self-kill pre-emption.

---

## Makefile and Environment Integration

Environment keys:
```

LABS_SCHEMA_VERSION=0.7.3
LABS_SCHEMA_BASE=[https://delk73.github.io/synesthetic-schemas/schema/](https://delk73.github.io/synesthetic-schemas/schema/)
MCP_HOST=0.0.0.0
MCP_PORT=7000

```

Make targets:
* `validate` — run local validator using canonical host.
* `check-schema-ids` — ensure all loaded schemas match canonical base.
* `audit-all` — full governance + transport audit.

---

## v0.2.9 Additions

* **Canonical schema alignment**  
  * All MCP modules now derive schema URLs from `LABS_SCHEMA_BASE`.  
  * Validation routines enforce canonical host prefix and version match.  
  * Added on-boot schema resolver logging and cache fingerprinting.
* **Governance parity**  
  * MCP automatically verifies that local cache hashes match published schema fingerprints from `version.json`.  
  * `governance_audit()` endpoint exposes compliance summary.
* **CLI integration**  
  * `mcp --audit` → runs governance + transport self-test.  
  * `mcp --schemas` → lists locally cached schema URLs and versions.

---

## Exit Criteria (v0.2.9)

| Checkpoint | Requirement |
|-------------|-------------|
| **Canonical Host** | All `$schema` fields resolve to `https://delk73.github.io/synesthetic-schemas/schema/0.7.3/…` |
| **Environment Alignment** | `LABS_SCHEMA_VERSION` = `0.7.3` and `LABS_SCHEMA_BASE` set |
| **Validation Integrity** | Assets validated exclusively via `$schema` |
| **Transport Parity** | STDIO, socket, and TCP enforce identical guards and logging invariants |
| **Governance Verification** | `mcp --audit` reports ✅ Global Compliance PASS |
| **Regression Guard** | All bundled examples contain valid `$schema` entries |

---

## Version v0.2.8 (Previous)

* Added strict `"$schema"` enforcement and unified payload guards.  
* Standardized logging and transport readiness signals.

---

## Backlog (≥ v0.3)

* gRPC transport for typed streaming.  
* Structured telemetry / metrics.  
* Dynamic schema hot-reload.  
* Live governance sync against `synesthetic-schemas` HEAD.
