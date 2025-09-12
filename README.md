<!---
version: 0.1.0
owner: delk73
lastReviewed: 2025-09-12
--->

# Synesthetic MCP

Lightweight **Model Context Protocol (MCP)** server for Synesthetic assets.  
This repo adapts the canonical [synesthetic-schemas](https://github.com/delk73/synesthetic-schemas) into MCP resources and tools.

- **Resources**: schemas, examples (read-only, from SSOT).  
- **Tools**: validation, diff (RFC6902 patch ops), backend population.  
- **Guards**: enforce schema compliance before persistence.


## System Context

```mermaid
flowchart LR
  FE["sdfk_fe_ts\n(TypeScript Frontend)"]
  BE["sdfk-backend\n(Python API & CRUD)"]
  MCP["synesthetic-mcp\n(Python MCP Adapter)"]
  RLHF["sdfk_rlhf\n(RLHF Asset Generation)"]
  SSOT["synesthetic-schemas\n(SSOT: Schemas + Codegen)"]

  FE --> |Consumes API| BE
  RLHF --> |Generates Assets via MCP| MCP
  MCP --> |Validates + Persists| BE
  SSOT --> |Submodule + Python pkg| MCP
  SSOT --> |TypeScript types| FE
  SSOT --> |Python models| BE

  style MCP fill:#444444,stroke:#ffffff,stroke-width:2px
```

## Structure

```
synesthetic-mcp/
  README.md
  docs/
    mcp_spec.md        # Full spec for MCP v1 (resources, tools, error model)
  mcp/
    __init__.py
    core.py            # schema/example discovery
    validate.py        # validation helpers
    diff.py            # JSON Patch generation
    backend.py         # proxy client to backend
    stdio_main.py      # MCP stdio adapter
    http_main.py       # optional FastAPI adapter
  tests/
    test_validate.py
    test_diff.py
    test_tools.py
    fixtures/
      valid_asset.json
      invalid_asset.json
  meta/
    prompts/           # Canonical Codex/ChatGPT prompts used to spin up repo
```

## Development

* MCP server is written in **Python 3.11+**.
* Depends on generated Python models from [`synesthetic-schemas`](https://github.com/delk73/synesthetic-schemas).
* Use **FastAPI** for HTTP adapter, or run via **stdio** for direct agent integration.
* Tests use **pytest** and golden fixtures.

## Spec

See [docs/mcp\_spec.md](docs/mcp_spec.md) for the pinned v1 specification.

## Status

✅ Spec pinned in `docs/mcp_spec.md`
🚧 Implementation scaffolding in progress

