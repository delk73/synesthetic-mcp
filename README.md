---
version: 0.1.0
owner: delk73
lastReviewed: 2025-09-12
---

# Synesthetic MCP

Lightweight **Model Context Protocol (MCP)** server for Synesthetic assets.  
This repo adapts the canonical [synesthetic-schemas](https://github.com/delk73/synesthetic-schemas) into MCP resources and tools.

- **Resources**: schemas, examples (read-only, from SSOT).  
- **Tools**: validation, diff (RFC6902 patch ops), backend population.  
- **Guards**: enforce schema compliance before persistence.

## Structure

```

synesthetic-mcp/
README.md
docs/
mcp\_spec.md        # Full spec for MCP v1 (resources, tools, error model)
mcp/
**init**.py
core.py            # schema/example discovery
validate.py        # validation helpers
diff.py            # JSON Patch generation
backend.py         # proxy client to backend
stdio\_main.py      # MCP stdio adapter
http\_main.py       # optional FastAPI adapter
tests/
test\_validate.py
test\_diff.py
test\_tools.py
fixtures/
valid\_asset.json
invalid\_asset.json
meta/
prompts/           # Canonical Codex/ChatGPT prompts used to spin up repo

```

## Development

- MCP server is written in **Python 3.11+**.  
- Depends on generated Python models from [`synesthetic-schemas`](https://github.com/delk73/synesthetic-schemas).  
- Use **FastAPI** for HTTP adapter, or run via **stdio** for direct agent integration.  
- Tests use **pytest** and golden fixtures.

## Spec

See [docs/mcp_spec.md](docs/mcp_spec.md) for the pinned v1 specification.

## Status

✅ Spec pinned in `docs/mcp_spec.md`  
🚧 Implementation scaffolding in progress
```