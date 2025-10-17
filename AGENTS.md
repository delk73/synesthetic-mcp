# AGENTS.md — Repo Snapshot (v0.2.9 Audit)

## Repo Summary
- Present — Canonical schema enforcement, alias handling, payload cap, and traversal guards are implemented with tests (`mcp/validate.py:26-376`; `tests/test_validate.py:62-260`; `tests/test_path_traversal.py:58-116`).
- Present — STDIO/socket/TCP transports share the JSON-RPC parser, log LABS metadata, and respect signal/ready-file semantics (`mcp/transport.py:26-105`; `mcp/__main__.py:211-347`; `tests/test_stdio.py:200-265`; `tests/test_tcp.py:66-205`).
- Present — Governance audit RPC, backend gating, and golden fixtures validate compliance behaviours (`mcp/core.py:210-240`; `tests/test_backend.py:25-210`; `tests/test_golden.py:18-99`).
- Divergent — README still cites submodule commit `0fdc842` while the repository pins `8286df4a4197f2fb45a8bd6c4a805262cba2e934` (`README.md:136-142`; `.git/modules/libs/synesthetic-schemas/HEAD:1`).
- Divergent — `.env` omits the trailing slash for `LABS_SCHEMA_BASE`, diverging from documented defaults (`.env:9`; `docs/mcp_spec.md:96-108`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:9` |
| httpx | Canonical schema fetch & backend client | Required | `requirements.txt:2`; `mcp/validate.py:161-178`; `mcp/backend.py:20-85` |
| pytest | Test runner | Required | `requirements.txt:3`; `tests/test_validate.py:19-193` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:12-118` |

## Environment Variables
- Transports: `MCP_MODE`, `MCP_ENDPOINT`, `MCP_HOST`, `MCP_PORT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE` (`mcp/__main__.py:125-185`; `README.md:95-104`).
- Lifecycle health: `MCP_READY_FILE` writes `<pid> <ISO8601>` and is cleared on shutdown (`mcp/__main__.py:186-208`; `tests/test_stdio.py:218-265`).
- Schema governance: `LABS_SCHEMA_BASE`, `LABS_SCHEMA_VERSION`, `LABS_SCHEMA_CACHE_DIR` feed logs/resolver (`mcp/core.py:16-44`; `mcp/__main__.py:72-78`; `mcp/validate.py:120-205`).
- Resource roots: `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR` determine discovery ordering (`mcp/core.py:62-101`; `README.md:115-128`).
- Backend & batching: `SYN_BACKEND_URL`, `SYN_BACKEND_ASSETS_PATH`, `MCP_MAX_BATCH` (`mcp/backend.py:12-85`; `mcp/validate.py:36-376`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO transport & lifecycle | ✅ | `tests/test_stdio.py:49-389`; `tests/test_entrypoint.py:39-169` |
| Socket transport & cleanup | ✅ | `tests/test_socket.py:68-223`; `tests/test_socket.py:312-400` |
| TCP transport, multi-client, signals | ✅ | `tests/test_tcp.py:66-520` |
| Validation & batching | ✅ | `tests/test_validate.py:19-260` |
| Backend populate | ✅ | `tests/test_backend.py:25-210` |
| Governance & golden replay | ✅ | `tests/test_golden.py:18-99`; `tests/fixtures/golden.jsonl:1-11` |
| Container security | ✅ | `tests/test_container.py:1-5`; `Dockerfile:23-30` |

## Spec Alignment (v0.2.9)
| Spec Item | Status | Evidence |
| - | - | - |
| Version metadata updated to v0.2.9 | Present | `mcp/__init__.py:6`; `README.md:2` |
| Canonical $schema host/version enforced | Present | `mcp/validate.py:97-148`; `tests/test_validate.py:226-235` |
| Legacy schema keys rejected | Present | `mcp/validate.py:297-302`; `tests/test_validate.py:238-249` |
| Remote schema resolution via LABS env | Present | `mcp/validate.py:150-210`; `tests/test_validate.py:252-260` |
| LABS env logged on readiness | Present | `mcp/__main__.py:215-347`; `tests/test_entrypoint.py:70-116` |
| Governance audit endpoint | Present | `mcp/core.py:210-240`; `tests/test_golden.py:52-92` |
| Default TCP mode (MCP_MODE) | Present | `mcp/__main__.py:125-145`; `README.md:82-104` |
| Default TCP port (8765) | Present | `mcp/__main__.py:30`; `docker-compose.yml:24-37`; `docs/mcp_spec.md:98-123` |
| Lifecycle logs include schema metadata | Present | `mcp/__main__.py:215-347`; `tests/test_socket.py:140-211` |
| Signal handling exits -2/-15 | Present | `mcp/__main__.py:482-503`; `tests/test_entrypoint.py:91-169` |
| Transport payload guard 1 MiB | Present | `mcp/transport.py:26-79`; `tests/test_tcp.py:168-182` |
| Alias validate→validate_asset with warning | Present | `mcp/stdio_main.py:29-33`; `tests/test_stdio.py:120-155` |
| Batching honours MCP_MAX_BATCH | Present | `mcp/validate.py:354-376`; `tests/test_validate.py:131-156` |
| Deterministic listings/diffs | Present | `mcp/core.py:108-162`; `mcp/diff.py:16-51`; `tests/test_submodule_integration.py:28-42` |
| Ready file `<pid> <ISO8601>` | Present | `mcp/__main__.py:186-204`; `tests/test_stdio.py:218-233` |
| Governance CLI helper (`--audit`) | Present | `mcp/__main__.py:418-446`; `tests/test_golden.py:52-82` |

## Recommendations
1. Update README to point to the current submodule commit `8286df4a4197f2fb45a8bd6c4a805262cba2e934` (`README.md:136-142`; `.git/modules/libs/synesthetic-schemas/HEAD:1`).
2. Normalize `.env`’s `LABS_SCHEMA_BASE` to keep the canonical trailing slash in step with docs (`.env:9`; `mcp/core.py:16-24`).
3. Add coverage for `_tcp_port()` when `MCP_PORT` is unset to lock the 8765 fallback (`mcp/__main__.py:176-184`; `tests/test_tcp.py:89-205`).
