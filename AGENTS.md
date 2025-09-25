# AGENTS.md — Repo Snapshot (v0.2.6 Audit)

## Repo Summary
- Transports share the guarded NDJSON dispatcher and keep spec errors inside `{ok:false}` JSON-RPC results (`mcp/transport.py:17`; `mcp/socket_main.py:95`; `tests/test_stdio.py:261`).
- Validation, diff, backend, and discovery paths remain deterministic with traversal guards and 1 MiB caps under test (`mcp/validate.py:120`; `mcp/diff.py:42`; `mcp/core.py:69`; `tests/test_validate.py:56`; `tests/test_backend.py:56`).
- Logging, ready file lifecycle, and container defaults meet v0.2.6 expectations with ISO timestamps and non-root images (`mcp/__main__.py:163`; `mcp/__main__.py:280`; `Dockerfile:24`; `tests/test_socket.py:155`; `tests/test_tcp.py:151`).
- Docs, compose, and env samples document STDIO, socket, and TCP modes consistently (`docs/mcp_spec.md:17`; `README.md:35`; `docker-compose.yml:15`; `.env.example:1`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:7` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:17` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:9`; `mcp/validate.py:66` |

## Environment Variables
- `MCP_ENDPOINT`/`MCP_SOCKET_PATH`/`MCP_SOCKET_MODE`/`MCP_HOST`/`MCP_PORT` select transport endpoints with validation (`mcp/__main__.py:81`; `mcp/__main__.py:95`; `mcp/__main__.py:118`; `mcp/__main__.py:124`).
- `MCP_READY_FILE` writes `<pid> <ISO8601>` and clears on shutdown (`mcp/__main__.py:134`; `tests/test_stdio.py:200`).
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR` fence schema discovery roots (`mcp/core.py:27`; `mcp/core.py:61`).
- `SYN_BACKEND_URL` / `SYN_BACKEND_ASSETS_PATH` and `MCP_MAX_BATCH` influence backend posting and batch limits (`mcp/backend.py:17`; `mcp/validate.py:27`; `tests/test_validate.py:103`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, alias warning, payload guard | ✅ Present | `tests/test_stdio.py:39`; `tests/test_stdio.py:130`; `tests/test_stdio.py:310` |
| Socket readiness, guard, multi-client threads | ✅ Present (permission check missing) | `tests/test_socket.py:55`; `tests/test_socket.py:137`; `tests/test_socket.py:223` |
| TCP transport round-trip & guard | ⚠️ Missing validate coverage | `tests/test_tcp.py:104`; `tests/test_tcp.py:137` |
| Path traversal rejection | ✅ Present | `tests/test_path_traversal.py:34` |
| Ready file lifecycle (PID + ISO) | ✅ Present | `tests/test_stdio.py:200`; `tests/test_socket.py:169`; `tests/test_tcp.py:168` |
| Validation contract & batching | ✅ Present | `tests/test_validate.py:24`; `tests/test_validate.py:103` |
| Backend populate flows & guard | ✅ Present (network exception untested) | `tests/test_backend.py:21`; `tests/test_backend.py:56` |
| Golden replay coverage (STDIO) | ✅ Present | `tests/fixtures/golden.jsonl:1`; `tests/test_golden.py:45` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON with 1 MiB guard | Present | `mcp/transport.py:17`; `tests/test_socket.py:137` |
| TCP transport (`MCP_ENDPOINT=tcp`, host/port, guard, tests) | Missing validate round-trip | `docs/mcp_spec.md:64`; `tests/test_tcp.py:104` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:134`; `tests/test_stdio.py:200`; `tests/test_tcp.py:168` |
| Ready/shutdown logs include dirs + ISO timestamp | Present | `mcp/__main__.py:163`; `tests/test_entrypoint.py:62`; `tests/test_socket.py:155` |
| Spec errors returned in JSON-RPC result payloads | Present | `mcp/transport.py:61`; `tests/test_stdio.py:261`; `tests/test_socket.py:128` |
| `validate` alias warning (pre-v0.3) | Present | `mcp/stdio_main.py:23`; `tests/test_stdio.py:105` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:199`; `tests/test_validate.py:103` |
| Security defaults: socket mode 0600 | Missing automated check | `mcp/socket_main.py:35`; `tests/test_socket.py:98` |
| Container runs non-root | Present | `Dockerfile:24`; `tests/test_container.py:4` |
| Docs/scripts updated for TCP | Present | `docs/mcp_spec.md:17`; `README.md:35`; `docker-compose.yml:15` |

## Recommendations
- Add a TCP `validate_asset` request to the integration test matrix to meet the v0.2.6 audit clause (`docs/mcp_spec.md:64`; `tests/test_tcp.py:104`).
- Assert the Unix socket file mode after server startup to prove least-privilege defaults (`mcp/socket_main.py:35`; `tests/test_socket.py:98`).
- Cover the `httpx.HTTPError` branch in `populate_backend` to lock the 503 mapping (`mcp/backend.py:58`; `tests/test_backend.py:21`).
