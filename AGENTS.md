# AGENTS.md — Repo Snapshot (v0.2.9 Audit)

## Repo Summary
- Present — Validation enforces canonical `$schema`, rejects legacy keys, caps payloads, and blocks traversal with regression coverage (`mcp/validate.py:292`; `mcp/validate.py:300`; `tests/test_validate.py:80`; `tests/test_path_traversal.py:36`).
- Present — STDIO/socket/TCP share the JSON-RPC parser, log LABS metadata, and clean up ready-files on shutdown (`mcp/transport.py:26`; `mcp/__main__.py:319`; `tests/test_stdio.py:205`; `tests/test_tcp.py:184`).
- Present — Governance audit, backend gating, and golden fixtures validate compliance behaviours (`mcp/core.py:210`; `tests/test_backend.py:25`; `tests/test_golden.py:18`).
- Missing — `get_schema` lacks the spec-required `resolution` modes and still serves only raw schemas (`docs/mcp_spec.md:67`; `mcp/core.py:128`; `tests/test_labs_integration.py:15`).
- Divergent — README instructs checking out submodule commit `0fdc842` instead of the pinned `8286df4a4197f2fb45a8bd6c4a805262cba2e934` (`README.md:136`; `.git/modules/libs/synesthetic-schemas/HEAD:1`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:9` |
| httpx | Canonical schema fetch & backend client | Required | `requirements.txt:2`; `mcp/validate.py:169`; `mcp/backend.py:54` |
| pytest | Test runner | Required | `requirements.txt:3`; `tests/test_validate.py:19` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:12`; `mcp/validate.py:249` |

## Environment Variables
- Transports: `MCP_MODE`, `MCP_ENDPOINT`, `MCP_HOST`, `MCP_PORT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE` (`mcp/__main__.py:125`; `mcp/__main__.py:170`; `README.md:97`).
- Lifecycle health: `MCP_READY_FILE` writes `<pid> <ISO8601>` and is cleared on shutdown (`mcp/__main__.py:192`; `tests/test_stdio.py:225`).
- Schema governance: `LABS_SCHEMA_BASE`, `LABS_SCHEMA_VERSION`, `LABS_SCHEMA_CACHE_DIR` feed logs/resolver (`mcp/core.py:16`; `mcp/core.py:34`; `mcp/validate.py:169`).
- Resource roots: `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR` determine discovery ordering (`mcp/core.py:62`; `README.md:122`).
- Backend & batching: `SYN_BACKEND_URL`, `SYN_BACKEND_ASSETS_PATH`, `MCP_MAX_BATCH` (`mcp/backend.py:12`; `mcp/backend.py:16`; `mcp/validate.py:36`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO transport & lifecycle | ✅ | `tests/test_stdio.py:49`; `tests/test_entrypoint.py:39` |
| Socket transport & cleanup | ✅ | `tests/test_socket.py:68`; `tests/test_socket.py:312` |
| TCP transport, multi-client, signals | ✅ | `tests/test_tcp.py:66`; `tests/test_tcp.py:208` |
| Validation & batching | ✅ | `tests/test_validate.py:19`; `tests/test_validate.py:138` |
| Backend populate | ✅ | `tests/test_backend.py:25`; `tests/test_backend.py:117` |
| Governance & golden replay | ✅ | `tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1` |
| Container security | ✅ | `tests/test_container.py:4`; `Dockerfile:24` |

## Spec Alignment (v0.2.9)
| Spec Item | Status | Evidence |
| - | - | - |
| Version metadata updated to v0.2.9 | Present | `mcp/__init__.py:6`; `README.md:2` |
| Canonical $schema host/version enforced | Present | `mcp/validate.py:292`; `tests/test_validate.py:231` |
| Legacy schema keys rejected | Present | `mcp/validate.py:300`; `tests/test_validate.py:245` |
| Remote schema resolution via LABS env | Present | `mcp/validate.py:169`; `tests/test_validate.py:256` |
| LABS env logged on readiness | Present | `mcp/__main__.py:319`; `tests/test_entrypoint.py:70` |
| Governance audit endpoint | Present | `mcp/core.py:210`; `tests/test_golden.py:52` |
| Default TCP mode (MCP_MODE) | Present | `mcp/__main__.py:125`; `README.md:97` |
| Default TCP port (8765) | Present | `mcp/__main__.py:176`; `docker-compose.yml:24` |
| Lifecycle logs include schema metadata | Present | `mcp/__main__.py:319`; `tests/test_socket.py:137` |
| Signal handling exits -2/-15 | Present | `mcp/__main__.py:482`; `tests/test_entrypoint.py:115` |
| Transport payload guard 1 MiB | Present | `mcp/transport.py:28`; `tests/test_tcp.py:169` |
| Alias validate→validate_asset with warning | Present | `mcp/stdio_main.py:35`; `tests/test_stdio.py:150` |
| Batching honours MCP_MAX_BATCH | Present | `mcp/validate.py:354`; `tests/test_validate.py:138` |
| Deterministic listings/diffs | Present | `mcp/core.py:124`; `mcp/diff.py:50`; `tests/test_submodule_integration.py:34` |
| Ready file `<pid> <ISO8601>` | Present | `mcp/__main__.py:192`; `tests/test_stdio.py:225` |
| `get_schema` resolution modes (`preserve`/`inline`/`bundled`) | Missing | `docs/mcp_spec.md:67`; `mcp/core.py:128` |

## Recommendations
1. Implement `get_schema` `resolution` modes end-to-end (core, transports, tests, golden fixtures) to satisfy the v0.2.9 spec (`docs/mcp_spec.md:67`; `mcp/core.py:128`; `tests/test_labs_integration.py:15`).
2. Correct README submodule instructions to reference the pinned commit `8286df4a4197f2fb45a8bd6c4a805262cba2e934` (`README.md:136`; `.git/modules/libs/synesthetic-schemas/HEAD:1`).
3. Add coverage for `_tcp_port()` when `MCP_PORT` is unset to guard the 8765 default (`mcp/__main__.py:176`; `tests/test_tcp.py:68`).
