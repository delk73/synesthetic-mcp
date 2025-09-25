# AGENTS.md — Repo Snapshot (v0.2.6 Audit)

## Repo Summary
- Shared NDJSON dispatcher enforces the 1 MiB guard across STDIO/socket/TCP with ISO ready/shutdown logs and ready-file cleanup under test (`mcp/transport.py:26`; `mcp/socket_main.py:110`; `mcp/tcp_main.py:113`; `mcp/__main__.py:165`; `tests/test_socket.py:100`; `tests/test_tcp.py:90`).
- Validation, diff, and discovery stay deterministic with guarded paths, alias handling, and sorted outputs backed by fixtures (`mcp/validate.py:16`; `mcp/core.py:44`; `mcp/diff.py:42`; `tests/test_validate.py:56`; `tests/test_submodule_integration.py:28`).
- Backend populate respects payload caps, optional validation, and HTTP error mapping with dedicated tests (`mcp/backend.py:38`; `mcp/backend.py:60`; `tests/test_backend.py:56`; `tests/test_backend.py:172`).
- Golden STDIO replay exercises list/get/validate/diff/backend/malformed flows and asserts alias warnings on stderr (`tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:7` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:17` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:10`; `mcp/validate.py:121` |

## Environment Variables
- Transport selection (`MCP_ENDPOINT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE`, `MCP_HOST`, `MCP_PORT`) is validated before server start and rejects unsupported values (`mcp/__main__.py:81`; `mcp/__main__.py:95`; `mcp/__main__.py:118`).
- Ready-file lifecycle writes `<pid> <ISO8601>` and cleans up on shutdown across transports (`mcp/__main__.py:170`; `tests/test_stdio.py:201`; `tests/test_socket.py:175`; `tests/test_tcp.py:523`).
- Schema/example roots are fenced by env overrides with traversal rejection tests (`mcp/core.py:27`; `tests/test_path_traversal.py:34`).
- Backend URL/path and batch limit envs drive populate behavior and `validate_many` limits (`mcp/backend.py:17`; `mcp/validate.py:167`; `tests/test_validate.py:118`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, alias warning, payload guard | ✅ Present | `tests/test_stdio.py:39`; `tests/test_stdio.py:66`; `tests/test_stdio.py:189` |
| Socket readiness, guard, multi-client threads, perms | ✅ Present | `tests/test_socket.py:100`; `tests/test_socket.py:107`; `tests/test_socket.py:137`; `tests/test_socket.py:175` |
| TCP transport round-trip, guard, validate coverage | ✅ Present | `tests/test_tcp.py:90`; `tests/test_tcp.py:135`; `tests/test_tcp.py:210`; `tests/test_tcp.py:331` |
| Backend populate flows & guard | ✅ Present | `tests/test_backend.py:28`; `tests/test_backend.py:56`; `tests/test_backend.py:172` |
| Path traversal rejection | ✅ Present | `tests/test_path_traversal.py:34` |
| Ready file lifecycle (PID + ISO) | ✅ Present | `tests/test_stdio.py:201`; `tests/test_socket.py:175`; `tests/test_tcp.py:523` |
| Validation contract & batching | ✅ Present | `tests/test_validate.py:56`; `tests/test_validate.py:118` |
| Golden replay coverage (STDIO) | ✅ Present | `tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON with 1 MiB guard | Present | `mcp/transport.py:26`; `tests/test_socket.py:137` |
| TCP transport (`MCP_ENDPOINT=tcp`, guard, tests) | Present | `mcp/tcp_main.py:56`; `tests/test_tcp.py:135`; `tests/test_tcp.py:331` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:170`; `tests/test_stdio.py:201`; `tests/test_tcp.py:523` |
| Ready/shutdown logs include dirs + ISO timestamp | Present | `mcp/__main__.py:165`; `tests/test_entrypoint.py:62`; `tests/test_socket.py:100` |
| Spec errors returned in JSON-RPC result payloads | Present | `mcp/transport.py:77`; `tests/test_stdio.py:39`; `tests/test_socket.py:120` |
| `validate` alias warning (pre-v0.3) | Present | `mcp/stdio_main.py:23`; `tests/test_stdio.py:118` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:167`; `tests/test_validate.py:118` |
| Security defaults: socket mode 0600 proven in tests | Present | `mcp/socket_main.py:35`; `tests/test_socket.py:107` |
| Backend HTTPError → backend_error 503 verified | Present | `mcp/backend.py:60`; `tests/test_backend.py:172` |
| Docs still describe payload guard as STDIO/socket only | Divergent | `README.md:36`; `README.md:138`; `mcp/tcp_main.py:113` |

## Recommendations
- Refresh the README feature and error-model text so the 1 MiB guard explicitly covers TCP alongside STDIO/socket (`README.md:36`; `README.md:138`; `tests/test_tcp.py:135`).
- Add a Serving Locally example showing how to connect to the TCP transport (e.g., `nc`) to highlight the new endpoint (`README.md:147`; `tests/test_tcp.py:104`).
- Continue running the transport integration suites in CI to preserve guard, alias-warning, and backend error coverage (`tests/test_stdio.py:118`; `tests/test_socket.py:137`; `tests/test_backend.py:172`).
