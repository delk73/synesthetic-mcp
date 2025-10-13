# AGENTS.md — Repo Snapshot (v0.2.9 Audit)

## Repo Summary
- Version metadata, documentation, and tooling now align on v0.2.9 with TCP as the default transport (mcp/__init__.py:6; README.md:2,82-110; docker-compose.yml:18-33).
- LABS schema base/version drive validation, remote resolution, and readiness logs, with canonical examples and tests enforcing the contract (mcp/validate.py:90-288; mcp/__main__.py:211-240; libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2; tests/test_validate.py:200-219).
- Governance surface gained a `governance_audit` RPC and golden coverage, closing v0.2.9 parity (mcp/core.py:206-236; mcp/stdio_main.py:20-44; tests/fixtures/golden.jsonl:10).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:9 |
| httpx | Canonical schema fetch & backend client | Required | requirements.txt:2; mcp/validate.py:131-151; mcp/backend.py:20-84 |
| pytest | Test runner | Required | requirements.txt:3; tests/test_validate.py:19-219 |
| referencing | Local schema registry support | Optional | mcp/validate.py:12-118 |

## Environment Variables
- Transports: `MCP_MODE`, `MCP_ENDPOINT`, `MCP_HOST`, `MCP_PORT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE` (mcp/__main__.py:114-178; README.md:95-103).
- Lifecycle health: `MCP_READY_FILE` maintains `<pid> <ISO8601>` readiness markers (mcp/__main__.py:186-208; tests/test_entrypoint.py:78-118).
- Schema governance: `LABS_SCHEMA_BASE`, `LABS_SCHEMA_VERSION`, `LABS_SCHEMA_CACHE_DIR` feed logs and resolver (mcp/core.py:11-44; mcp/__main__.py:72-78; mcp/validate.py:120-151).
- Resource roots: `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR` (mcp/core.py:62-101; README.md:107-111).
- Backend & batching: `SYN_BACKEND_URL`, `SYN_BACKEND_ASSETS_PATH`, `MCP_MAX_BATCH` (mcp/backend.py:10-48; mcp/validate.py:21-43).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO transport & lifecycle | ✅ | tests/test_stdio.py:70-208; tests/test_entrypoint.py:46-119 |
| Socket transport & cleanup | ✅ | tests/test_socket.py:52-190 |
| TCP transport, multi-client, signals | ✅ | tests/test_tcp.py:66-520 |
| Validation & batching (canonical host, payload, batch limits) | ✅ | tests/test_validate.py:19-219 |
| Backend populate | ✅ | tests/test_backend.py:18-142 |
| Governance & golden replay | ✅ | tests/test_golden.py:31-90; tests/fixtures/golden.jsonl:1-10 |
| Container security | ✅ | tests/test_container.py:1-5; Dockerfile:23-31 |

## Spec Alignment (v0.2.9)
| Spec Item | Status | Evidence |
| - | - | - |
| Version metadata updated to v0.2.9 | Present | mcp/__init__.py:6; README.md:2 |
| Canonical $schema host/version enforced | Present | mcp/validate.py:90-288; tests/test_validate.py:200-206 |
| Remote schema resolution via LABS env | Present | mcp/validate.py:120-171 |
| LABS env logged on readiness | Present | mcp/__main__.py:72-240; tests/test_entrypoint.py:70-105 |
| Governance audit endpoint | Present | mcp/core.py:206-236; mcp/stdio_main.py:20-44; tests/fixtures/golden.jsonl:10 |
| Default TCP mode (MCP_MODE) | Present | mcp/__main__.py:114-144; docker-compose.yml:18-33 |
| Lifecycle logs include schema metadata | Present | mcp/__main__.py:211-317; tests/test_socket.py:80-138 |
| Signal handling exits -2/-15 | Present | mcp/__main__.py:474-480; tests/test_entrypoint.py:108-119 |
| Transport payload guard 1 MiB | Present | mcp/validate.py:21-44; mcp/transport.py:13-47; tests/test_tcp.py:102-144 |
| Alias validate→validate_asset with warning | Present | mcp/stdio_main.py:29-35; tests/test_stdio.py:105-152 |
| Batching honors MCP_MAX_BATCH | Present | mcp/validate.py:314-333; tests/test_validate.py:123-148 |
| Deterministic listings/diffs | Present | mcp/core.py:104-158; mcp/diff.py:10-47 |
| Ready file `<pid> <ISO8601>` | Present | mcp/__main__.py:186-208; tests/test_entrypoint.py:78-118 |
| Governance CLI helper (`--audit`) | Divergent | docs/mcp_spec.md:118-124 (no argparse flag yet) |

## Recommendations
1. Wire up a `--audit` CLI flag that invokes governance_audit and transport self-checks per spec guidance (docs/mcp_spec.md:118-124; mcp/__main__.py:412-480).
2. Add tests that simulate missing local schemas to assert httpx fallback/cache behaviour (mcp/validate.py:131-171).
3. Mirror `LABS_SCHEMA_CACHE_DIR` guidance in docs/mcp_spec.md to match runtime/README expectations (README.md:95-111; docs/mcp_spec.md:32-90).
