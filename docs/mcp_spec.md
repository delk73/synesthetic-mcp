---
version: v0.2.9
lastReviewed: 2025-10-15
owner: mcp-core
---

# MCP Spec

## Purpose

The **Synesthetic MCP** adapter exposes **schemas**, **examples**, **validation**, **diff**, and optional **backend population** as deterministic, stateless tools wired directly to the canonical **Synesthetic Schemas v0.7.3** host.

* **Canonical schema base:**  
  `https://delk73.github.io/synesthetic-schemas/schema/0.7.3/`
* **Schema version:**  
  Derived from `LABS_SCHEMA_VERSION` (default `0.7.3`).
* **Source of truth:**  
  [synesthetic-schemas v0.7.3](https://github.com/delk73/synesthetic-schemas)

---

## Core Functions

| Tool | Purpose | Validation Source |
|------|----------|-------------------|
| `validate_asset` | Validate a single asset against its `$schema`. | Local or remote canonical schema |
| `validate_many` | Batch validation for multiple assets. | Same as above |
| `diff_assets` | RFC 6902 diff (`add`, `remove`, `replace`). | JSON Patch semantics |
| `populate_backend` | Convert validated assets for backend ingestion. | Deterministic serialization |

All validation conforms to **JSON Schema Draft 2020-12**.

---

## Transport

* **Ephemeral:** `STDIO` (JSON-RPC 2.0)  
* **Persistent:** `Socket` (Unix Domain) (JSON-RPC 2.0)  
* **Distributed:** `TCP` (JSON-RPC 2.0)

**Default:** `TCP` for container or CI environments.  
`STDIO` remains the fallback for CLI and Codex tests.

**Payload guard:** 1 MiB UTF-8 maximum per request.  
**Schema immutability:** no in-process mutation or patching.

---

## Schema Integration (v0.7.3 Alignment)

* **Canonical host:** `https://delk73.github.io/synesthetic-schemas/schema/`  
* **Legacy host (accepted):** `https://schemas.synesthetic.dev/`

Rules:
1. Every asset MUST include `"$schema"` referencing the canonical host.  
2. Relative markers are normalized via `LABS_SCHEMA_BASE` + `LABS_SCHEMA_VERSION`.  
3. Legacy absolute markers using the `.dev` host remain accepted for back-compat.  
4. `"schema"` and `"$schemaRef"` keys are invalid.  
5. Resolver supports both **remote fetch** and **cache lookup** (`LABS_SCHEMA_CACHE_DIR`).  
6. Examples under `synesthetic-schemas/examples` are verified upstream and not mutated in MCP.

---

## Logging & Lifecycle

**Ready Log**
```

mcp:ready mode=<transport> host=<h> port=<p> 
schemas_base=[https://delk73.github.io/synesthetic-schemas/schema/0.7.3](https://delk73.github.io/synesthetic-schemas/schema/0.7.3) 
schema_version=0.7.3 cache_dir=~/.cache/synesthetic-schemas timestamp=<ISO8601>

```

**Shutdown Log**  
Same fields + `event=shutdown`.

**Signal exits**  
`SIGINT` → `-2`; `SIGTERM` → `-15` (logged before exit).

---

## Environment Variables

| Variable | Default | Description |
|-----------|----------|-------------|
| `MCP_MODE` | `tcp` | Primary transport selector (`tcp`, `stdio`, `socket`) |
| `MCP_HOST` | `0.0.0.0` | TCP bind host |
| `MCP_PORT` | `7000` | TCP bind port |
| `MCP_READY_FILE` | `/tmp/mcp.ready` | Written on startup `<pid> <ISO8601>` |
| `MCP_MAX_BATCH` | `100` | Max batch size for `validate_many` |
| `LABS_SCHEMA_BASE` | `https://delk73.github.io/synesthetic-schemas/schema` | Canonical schema base URL (no trailing slash required) |
| `LABS_SCHEMA_VERSION` | `0.7.3` | Canonical schema version |
| `LABS_SCHEMA_CACHE_DIR` | `~/.cache/synesthetic-schemas` | Cache for downloaded canonical schemas |
| `SYN_SCHEMAS_DIR` | `libs/synesthetic-schemas/jsonschema` | Local schemas dir override |
| `SYN_EXAMPLES_DIR` | `libs/synesthetic-schemas/examples` | Local examples dir override |
| `SYN_BACKEND_URL` | unset | Optional backend endpoint |
| `SYN_BACKEND_ASSETS_PATH` | `/synesthetic-assets/` | Backend POST path |

`.env` and `.env.example` must mirror these names exactly.

---

## Startup (via `up.sh`)

`up.sh` builds and starts the containerized service in **TCP mode**:  
```

mcp:ready mode=tcp host=0.0.0.0 port=7000 
schemas_base=[https://delk73.github.io/synesthetic-schemas/schema/0.7.3](https://delk73.github.io/synesthetic-schemas/schema/0.7.3) 
timestamp=<ISO8601>

```

---

## v0.2.9 Additions

* **Canonical schema alignment** – all URLs resolved via `LABS_SCHEMA_BASE`.  
* **Governance parity** – `governance_audit()` RPC validates cache fingerprints.  
* **CLI integration** – `mcp --audit` and `mcp --schemas` surface RPC results.  
* **Cache fallback** – `_fetch_canonical_schema()` populates `LABS_SCHEMA_CACHE_DIR`.  
* **Lifecycle logs** – readiness includes `schemas_base`, `schema_version`, `cache_dir`.

---

## Exit Criteria (v0.2.9)

| Checkpoint | Requirement |
|-------------|-------------|
| Canonical Host | `$schema` → `https://delk73.github.io/synesthetic-schemas/schema/0.7.3/...` |
| Env Alignment | `LABS_SCHEMA_VERSION=0.7.3` and `LABS_SCHEMA_BASE` set |
| Validation Integrity | Validation passes only for canonical/legacy hosts |
| Transport Parity | STDIO, Socket, TCP identical guardrails + logs |
| Default Mode | `TCP` default confirmed in startup log |
| Governance Verification | `mcp --audit` → ✅ PASS |
| Regression Guard | Non-canonical hosts → `schema_must_use_canonical_host` |

---

## Version v0.2.8 (Previous)

* Added `$schema` enforcement and unified 1 MiB payload guard.  
* Normalized transport logs and signal exits.

---

## Backlog (≥ v0.3)

* gRPC transport prototype.  
* Structured telemetry metrics.  
* Dynamic schema hot-reload.  
* Live governance sync against `synesthetic-schemas` HEAD.