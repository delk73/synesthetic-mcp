# AGENTS.md — Repo Snapshot (v0.2.9 Audit)

## Repo Summary
- Present — Canonical schema enforcement, alias handling, payload cap, and batch guard are implemented with tests (mcp/validate.py:32-376; tests/test_validate.py:62-193).
- Present — STDIO/socket/TCP transports share JSON-RPC parsing, log schema metadata, and honour signal/ready file semantics (mcp/__main__.py:211-356; mcp/transport.py:26-105; tests/test_entrypoint.py:39-119; tests/test_tcp.py:113-190).
- Present — Governance audit RPC and golden fixtures validate compliance outputs (mcp/core.py:210-240; tests/fixtures/golden.jsonl:10; tests/test_golden.py:18-99).
- Divergent — Runtime default TCP port remains 7000 while spec/docs/docker-compose require 8765 (mcp/__main__.py:30; docs/mcp_spec.md:98; docker-compose.yml:24-37).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:9 |
| httpx | Canonical schema fetch & backend client | Required | requirements.txt:2; mcp/validate.py:161-178; mcp/backend.py:20-85 |
| pytest | Test runner | Required | requirements.txt:3; tests/test_validate.py:19-193 |
| referencing | Local schema registry support | Optional | mcp/validate.py:12-118 |

## Environment Variables
- Transports: `MCP_MODE`, `MCP_ENDPOINT`, `MCP_HOST`, `MCP_PORT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE` (mcp/__main__.py:125-185; README.md:95-103).
- Lifecycle health: `MCP_READY_FILE` writes `<pid> <ISO8601>` and is cleared on shutdown (mcp/__main__.py:186-208; tests/test_stdio.py:218-265).
- Schema governance: `LABS_SCHEMA_BASE`, `LABS_SCHEMA_VERSION`, `LABS_SCHEMA_CACHE_DIR` feed logs/resolver (mcp/core.py:16-44; mcp/__main__.py:72-78; mcp/validate.py:120-205).
- Resource roots: `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR` determine discovery ordering (mcp/core.py:62-101; README.md:107-111).
- Backend & batching: `SYN_BACKEND_URL`, `SYN_BACKEND_ASSETS_PATH`, `MCP_MAX_BATCH` (mcp/backend.py:12-58; mcp/validate.py:34-376).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO transport & lifecycle | ✅ | tests/test_stdio.py:49-389; tests/test_entrypoint.py:39-119 |
| Socket transport & cleanup | ✅ | tests/test_socket.py:68-223,312-400 |
| TCP transport, multi-client, signals | ✅ | tests/test_tcp.py:66-450 |
| Validation & batching | ✅ | tests/test_validate.py:19-193 |
| Backend populate | ✅ | tests/test_backend.py:25-210 |
| Governance & golden replay | ✅ | tests/test_golden.py:18-99; tests/fixtures/golden.jsonl:1-11 |
| Container security | ✅ | tests/test_container.py:4-5; Dockerfile:23-30 |

## Spec Alignment (v0.2.9)
| Spec Item | Status | Evidence |
| - | - | - |
| Version metadata updated to v0.2.9 | Present | mcp/__init__.py:6; README.md:2 |
| Canonical $schema host/version enforced | Present | mcp/validate.py:97-148; tests/test_validate.py:226-235 |
| Legacy schema keys rejected | Present | mcp/validate.py:297-302; tests/test_validate.py:238-249 |
| Remote schema resolution via LABS env | Present | mcp/validate.py:150-205; tests/test_validate.py:252-260 |
| LABS env logged on readiness | Present | mcp/__main__.py:215-347; tests/test_entrypoint.py:70-105 |
| Governance audit endpoint | Present | mcp/core.py:210-240; tests/fixtures/golden.jsonl:10 |
| Default TCP mode (MCP_MODE) | Present | mcp/__main__.py:125-145; README.md:97 |
| Default TCP port (8765) | Divergent | mcp/__main__.py:30; docs/mcp_spec.md:98; docker-compose.yml:24-37 |
| Lifecycle logs include schema metadata | Present | mcp/__main__.py:215-347; tests/test_socket.py:138-211 |
| Signal handling exits -2/-15 | Present | mcp/__main__.py:482-503; tests/test_entrypoint.py:91-116 |
| Transport payload guard 1 MiB | Present | mcp/transport.py:26-79; mcp/validate.py:32-83; tests/test_tcp.py:168-182 |
| Alias validate→validate_asset with warning | Present | mcp/stdio_main.py:29-33; tests/test_stdio.py:105-155 |
| Batching honours MCP_MAX_BATCH | Present | mcp/validate.py:354-376; tests/test_validate.py:131-156 |
| Deterministic listings/diffs | Present | mcp/core.py:108-162; mcp/diff.py:16-51 |
| Ready file `<pid> <ISO8601>` | Present | mcp/__main__.py:186-194; tests/test_stdio.py:218-265 |
| Governance CLI helper (`--audit`) | Present | mcp/__main__.py:418-446; tests/test_golden.py:52-82 |

## Recommendations
1. Update `DEFAULT_TCP_PORT` to 8765 then run `pytest` to confirm transport readiness logs remain stable (mcp/__main__.py:30; Makefile:32-34; tests/test_tcp.py:113-190).
2. Add a regression test covering `_tcp_port()` fallback when `MCP_PORT` is unset to guard the default (mcp/__main__.py:176-184; tests/test_tcp.py:89-123).
