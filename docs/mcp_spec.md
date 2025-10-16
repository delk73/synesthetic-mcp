---
version: v0.2.9
lastReviewed: 2025-10-16
owner: mcp-core
---

# Synesthetic MCP Specification (v0.2.9)

## Purpose

The **Synesthetic MCP** adapter exposes **schemas**, **examples**, **validation**, **diff**, and optional **backend population** as deterministic, stateless tools wired directly to the canonical **Synesthetic Schemas v0.7.3** host.

* **Canonical schema base:**  
  `https://delk73.github.io/synesthetic-schemas/schema/0.7.3/`
* **Schema version:**  
  Derived dynamically from `LABS_SCHEMA_VERSION` (`0.7.3` by default).
* **Source of truth:**  
  [synesthetic-schemas @ 8286df4a4197f2fb45a8bd6c4a805262cba2e934](https://github.com/delk73/synesthetic-schemas/commit/8286df4a4197f2fb45a8bd6c4a805262cba2e934)

---

## Core Functions

| Tool | Purpose | Validation Source |
|------|----------|-------------------|
| `validate_asset` | Validate a single asset against its `$schema`. | Canonical or locally cached schema |
| `validate_many` | Batch validation for multiple assets. | Same as above |
| `diff_assets` | Produce RFC 6902 diff (`add`, `remove`, `replace`). | JSON Patch semantics |
| `populate_backend` | Serialize validated assets for backend ingestion. | Deterministic serialization |

All validation conforms to **JSON Schema Draft 2020-12**.

---

## Transport

| Type | Mode | Protocol | Notes |
|------|------|-----------|-------|
| Ephemeral | STDIO | JSON-RPC 2.0 | Used for CLI and Codex integration |
| Persistent | Socket | JSON-RPC 2.0 | Unix-domain socket |
| Distributed | TCP | JSON-RPC 2.0 | Default for container and CI |

**Default:** `TCP`  
**Payload limit:** 1 MiB UTF-8 per request  
**Schema immutability:** No in-process patching or mutation.

---

## Schema Integration (v0.7.3 Alignment)

* **Canonical host:** `https://delk73.github.io/synesthetic-schemas/schema/`
* **Placeholder host:** `https://schemas.synesthetic.dev/`
* **Submodule pin:** `libs/synesthetic-schemas` must resolve to commit `8286df4a4197f2fb45a8bd6c4a805262cba2e934` or a future audited tag.

### Rules

1. Every asset MUST include a top-level `"$schema"` referencing the canonical host.  
2. Relative or legacy `.dev` hosts are normalized via `LABS_SCHEMA_BASE` + `LABS_SCHEMA_VERSION`.  
3. Keys `schema` and `$schemaRef` are **rejected** → `validation_failed @ '/$schema'`.  
4. Resolver supports both **remote fetch** and **cache lookup** (`LABS_SCHEMA_CACHE_DIR`).  
5. Examples from the submodule are trusted and never rewritten by MCP.  
6. The **`make preflight`** target validates the submodule, publishes canonical docs, and re-verifies all schema URLs.

---

## Logging & Lifecycle

**Startup (ready) log**
```

mcp:ready mode=<transport> host=<host> port=<port>
schemas_base=[https://delk73.github.io/synesthetic-schemas/schema/0.7.3](https://delk73.github.io/synesthetic-schemas/schema/0.7.3)
schema_version=0.7.3 cache_dir=~/.cache/synesthetic-schemas timestamp=<ISO8601>

```

**Shutdown log**
```

mcp:shutdown mode=<transport> event=shutdown timestamp=<ISO8601>

```

**Signal handling**
- `SIGINT` → exit code `-2`
- `SIGTERM` → exit code `-15`
- Both emit final `mcp:shutdown` entry before termination.  
Timestamps use ISO-8601 UTC with ms precision.

---

## Environment Variables

| Variable | Default | Description |
|-----------|----------|-------------|
| `MCP_MODE` | `tcp` | Transport selector (`tcp`, `stdio`, `socket`) |
| `MCP_HOST` | `0.0.0.0` | TCP bind address |
| `MCP_PORT` | `8765` | TCP port |
| `MCP_READY_FILE` | `/tmp/mcp.ready` | Ready file `<pid> <ISO8601>` |
| `MCP_MAX_BATCH` | `100` | Max batch size for `validate_many` |
| `LABS_SCHEMA_BASE` | `https://delk73.github.io/synesthetic-schemas/schema` | Canonical schema base |
| `LABS_SCHEMA_VERSION` | `0.7.3` | Canonical schema version |
| `LABS_SCHEMA_CACHE_DIR` | `~/.cache/synesthetic-schemas` | Schema cache directory |
| `SYN_SCHEMAS_DIR` | `libs/synesthetic-schemas/jsonschema` | Local schema override |
| `SYN_EXAMPLES_DIR` | `libs/synesthetic-schemas/examples` | Local examples override |
| `SYN_BACKEND_URL` | unset | Optional backend endpoint |
| `SYN_BACKEND_ASSETS_PATH` | `/synesthetic-assets/` | Backend POST path |

`.env` and `.env.example` must match these exactly.  
`.env` values override container defaults.

---

## Startup Flow

`./up.sh` runs the containerized service in **TCP mode**:
```

mcp:ready mode=tcp host=0.0.0.0 port=8765
schemas_base=[https://delk73.github.io/synesthetic-schemas/schema/0.7.3](https://delk73.github.io/synesthetic-schemas/schema/0.7.3)
timestamp=<ISO8601>

```

---

## v0.2.9 Additions and Enforcement

* Canonical schema alignment and placeholder rewrite validation  
* Preflight pipeline verifying submodule commit, schema publication, and canonicalization  
* Environment-driven schema resolution (`LABS_SCHEMA_BASE`, `LABS_SCHEMA_VERSION`)  
* Deterministic logging and lifecycle parity across all transports  
* Validation alias: `validate` → `validate_asset` (deprecated warning retained)  
* Strict 1 MiB payload cap enforced in STDIO, Socket, and TCP handlers  
* Batch validation limit via `MCP_MAX_BATCH`  
* Lexicographic determinism in listings, diffs, and error ordering  
* Non-root container execution and readiness probe support

---

## Exit Criteria (v0.2.9)

| Checkpoint | Requirement |
|-------------|-------------|
| Canonical host alignment | All `$schema` fields resolve to canonical base + version |
| Submodule pin | `libs/synesthetic-schemas` commit = audited hash (`8286df4…`) |
| Env alignment | `LABS_SCHEMA_BASE` / `LABS_SCHEMA_VERSION` exported and logged |
| Validation integrity | Canonical / legacy host assets validate; others rejected |
| Transport parity | STDIO, Socket, TCP identical logging + signal behavior |
| Default mode | `TCP` confirmed via startup log |
| Schema preflight | `make preflight` passes clean (normalize → publish → validate) |
| Governance parity | Achieved via preflight submodule verification |
| Payload guard | 1 MiB enforced + tests present |
| Deterministic order | Diff + validate_many sorted lexicographically |
| Docs parity | README / mcp_spec.md show canonical host and TCP example |

---

## Future (≥ v0.3)

* gRPC transport prototype  
* Structured telemetry metrics  
* Dynamic schema hot-reload  
* Live governance sync against `synesthetic-schemas` HEAD