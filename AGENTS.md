# AGENTS.md — Repo Snapshot (v0.2.6 Audit Refresh)

## Repo Summary
- Shared NDJSON dispatcher enforces the 1 MiB guard across STDIO/socket/TCP with ISO ready/shutdown logs and ready-file cleanup under test (`mcp/transport.py:26`; `mcp/__main__.py:54`; `tests/test_socket.py:288`; `tests/test_tcp.py:311`).
- Deterministic schema discovery, validation (including alias folding), and diffing keep outputs sorted and traversal-safe (`mcp/core.py:69`; `mcp/validate.py:176`; `mcp/diff.py:22`; `tests/test_validate.py:46`; `tests/test_path_traversal.py:32`).
- Backend populate respects payload caps, optional validation, and HTTP error mapping with targeted coverage (`mcp/backend.py:34`; `mcp/backend.py:55`; `tests/test_backend.py:172`).
- Golden STDIO replay exercises list/get/validate/alias/batch/example/diff/backend/malformed flows (`tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:7` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:17` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:10`; `mcp/validate.py:93` |

## Environment Variables
- Transport selection (`MCP_ENDPOINT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE`, `MCP_HOST`, `MCP_PORT`) is validated before server start and rejects unsupported values (`mcp/__main__.py:81`; `mcp/__main__.py:101`; `tests/test_entrypoint.py:108`).
- Ready-file lifecycle writes `<pid> <ISO8601>` and cleans up across transports (`mcp/__main__.py:134`; `tests/test_stdio.py:143`; `tests/test_socket.py:173`; `tests/test_tcp.py:317`).
- Schema/example roots are fenced by env overrides with traversal rejection tests (`mcp/core.py:27`; `tests/test_path_traversal.py:31`).
- Backend URL/path and batch limit envs drive populate behavior and `validate_many` limits (`mcp/backend.py:17`; `mcp/validate.py:27`; `tests/test_validate.py:118`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, alias warning, payload guard | ✅ Present | `tests/test_stdio.py:56`; `tests/test_stdio.py:126`; `tests/test_stdio.py:160` |
| Socket readiness, guard, multi-client threads, perms | ✅ Present | `tests/test_socket.py:100`; `tests/test_socket.py:108`; `tests/test_socket.py:228`; `tests/test_socket.py:294` |
| TCP transport round-trip, guard, validate flows | ✅ Present | `tests/test_tcp.py:221`; `tests/test_tcp.py:296`; `tests/test_tcp.py:389` |
| Backend populate flows & guard | ✅ Present | `tests/test_backend.py:38`; `tests/test_backend.py:172` |
| Path traversal rejection | ✅ Present | `tests/test_path_traversal.py:32` |
| Ready file lifecycle (PID + ISO) | ✅ Present | `tests/test_stdio.py:143`; `tests/test_socket.py:173`; `tests/test_tcp.py:317` |
| Validation contract & batching | ✅ Present | `tests/test_validate.py:46`; `tests/test_validate.py:118`; `tests/test_validate.py:145` |
| Golden replay coverage (STDIO) | ✅ Present | `tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON with 1 MiB guard | Present | `mcp/transport.py:26`; `tests/test_socket.py:137` |
| TCP transport (`MCP_ENDPOINT=tcp`, guard, tests) | Present | `mcp/tcp_main.py:25`; `tests/test_tcp.py:381`; `tests/test_tcp.py:296` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:134`; `tests/test_tcp.py:317` |
| Ready/shutdown logs include dirs + ISO timestamp | Present | `mcp/__main__.py:120`; `tests/test_entrypoint.py:62`; `tests/test_socket.py:288` |
| Spec errors returned in JSON-RPC result payloads | Present | `mcp/transport.py:66`; `tests/test_stdio.py:39`; `tests/test_socket.py:120` |
| `validate` alias warning (pre-v0.3) | Present | `mcp/stdio_main.py:23`; `tests/test_stdio.py:137` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:200`; `tests/test_validate.py:118` |
| Security defaults: socket mode 0600 proven in tests | Present | `mcp/socket_main.py:24`; `tests/test_socket.py:108` |
| Backend HTTPError → backend_error 503 verified | Present | `mcp/backend.py:55`; `tests/test_backend.py:172` |
| Docs list payload guard as STDIO/socket-only | Divergent | `README.md:36`; `README.md:147`; `mcp/tcp_main.py:114` |

## Recommendations
- Refresh the README payload guard text so TCP is documented alongside STDIO/socket enforcement (`README.md:36`; `README.md:147`; `tests/test_tcp.py:381`).
- Add a TCP client snippet (e.g., `nc`) in Serving Locally to surface the new transport path (`README.md:172`; `tests/test_tcp.py:296`).
- Clarify README shutdown expectations to mention `-SIGINT` exit codes on signal-driven termination (`README.md:174`; `tests/test_entrypoint.py:80`).
