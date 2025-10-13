# AGENTS.md — Repo Snapshot (v0.2.9 Audit)

## Repo Summary
- Version metadata still v0.2.7 instead of v0.2.9 (mcp/__init__.py:6; README.md:2)
- Validator only loads local schemas; canonical LABS host/version unused (mcp/validate.py:47-115; docs/mcp_spec.md:32-48)
- LABS_SCHEMA_BASE/LABS_SCHEMA_VERSION absent from code, env samples, and logs (mcp/__main__.py:185-207; .env.example:1-9)
- Bundled examples keep relative `$schema` markers (libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2)
- Ready/shutdown logs miss schemas_base/schema_version and exit codes resolve to 128+signal (mcp/__main__.py:185-439)
- Governance audit RPC/CLI missing despite spec requirement (mcp/stdio_main.py:14-39; docs/mcp_spec.md:112-124)
- Default transport remains MCP_ENDPOINT=stdio; docs and scripts mirror old default (mcp/__main__.py:102-110; docker-compose.yml:19-24)
- README TCP example uses `nc localhost` rather than `127.0.0.1` and omits LABS env (README.md:202-225)

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:9 |
| httpx | Backend populate client | Required (backend path) | requirements.txt:2; mcp/backend.py:20-84 |
| pytest | Test runner | Required (tests) | requirements.txt:3; .github/workflows/ci.yml:34 |
| referencing | Local schema registry support | Optional | mcp/validate.py:12-44 |

## Environment Variables
- Transports: MCP_ENDPOINT, MCP_HOST, MCP_PORT, MCP_SOCKET_PATH, MCP_SOCKET_MODE (mcp/__main__.py:102-152)
- Lifecycle health: MCP_READY_FILE controls `<pid> <ISO8601>` ready file (mcp/__main__.py:131-178)
- Resource roots: SYN_SCHEMAS_DIR, SYN_EXAMPLES_DIR (mcp/core.py:25-68; .env.example:4-7)
- Backend: SYN_BACKEND_URL, SYN_BACKEND_ASSETS_PATH (mcp/backend.py:10-33; .env.example:7-8)
- Batching: MCP_MAX_BATCH (mcp/validate.py:21-43)
- Missing: LABS_SCHEMA_BASE, LABS_SCHEMA_VERSION, MCP_MODE (docs/mcp_spec.md:44-86)

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO transport & lifecycle | ✅ | tests/test_stdio.py:42-153; tests/test_entrypoint.py:46-143 |
| Socket transport & cleanup | ✅ | tests/test_socket.py:52-190 |
| TCP transport, multi-client, signals | ✅ | tests/test_tcp.py:66-332 |
| Validation & batching | ✅ | tests/test_validate.py:19-184 |
| Backend populate | ✅ | tests/test_backend.py:18-142 |
| Golden replay | ✅ | tests/test_golden.py:24-94; tests/fixtures/golden.jsonl:1-9 |
| Container security | ✅ | tests/test_container.py:1-5; Dockerfile:23-31 |

## Spec Alignment (v0.2.9)
| Spec Item | Status | Evidence |
| - | - | - |
| Version metadata updated to v0.2.9 | Divergent | mcp/__init__.py:6; README.md:2 |
| Canonical $schema host/version enforced | Missing | mcp/validate.py:63-109; libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2 |
| Remote schema resolution via LABS env | Missing | mcp/validate.py:47-115; docs/mcp_spec.md:32-48 |
| LABS env logged on readiness | Missing | mcp/__main__.py:185-207; docs/mcp_spec.md:52-70 |
| Governance audit endpoint/CLI | Missing | mcp/stdio_main.py:14-39; docs/mcp_spec.md:112-124 |
| Default TCP mode (MCP_MODE) | Divergent | mcp/__main__.py:102-110; docker-compose.yml:19-24 |
| Lifecycle logs include schema metadata | Divergent | mcp/__main__.py:185-309; docs/mcp_spec.md:52-70 |
| Signal handling exits -2/-15 | Divergent | mcp/__main__.py:436-439; docs/mcp_spec.md:61-66 |
| Transport payload guard 1 MiB | Present | mcp/transport.py:13-47; tests/test_tcp.py:103-120 |
| Alias validate→validate_asset with warning | Present | mcp/stdio_main.py:24-33; tests/test_stdio.py:74-132 |
| Batching honors MCP_MAX_BATCH | Present | mcp/validate.py:21-160; tests/test_validate.py:123-148 |
| Deterministic listings/diffs | Present | mcp/core.py:78-112; mcp/diff.py:10-47 |
| Ready file `<pid> <ISO8601>` | Present | mcp/__main__.py:155-167; tests/test_entrypoint.py:55-112 |
| Payload cap test coverage | Present | tests/test_validate.py:68-184; tests/test_socket.py:119-152 |

## Recommendations
- Update package/README version metadata to v0.2.9 (mcp/__init__.py:6; README.md:2)
- Enforce canonical LABS schema host/version with remote fetch + cache guardrails (mcp/validate.py:47-115; docs/mcp_spec.md:32-48)
- Read/log LABS env in readiness events and add schema metadata fields (mcp/__main__.py:185-309)
- Implement governance_audit RPC and CLI flag per spec (docs/mcp_spec.md:112-124; mcp/stdio_main.py:14-39)
- Default to TCP via MCP_MODE, adjust compose/up.sh, and document `nc 127.0.0.1` plus LABS env (mcp/__main__.py:102-110; docker-compose.yml:19-24; README.md:202-225)
- Fix signal exit codes to return -2/-15 instead of 128+signal (mcp/__main__.py:436-439)
