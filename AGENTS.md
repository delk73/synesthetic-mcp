# AGENTS.md — Repo Snapshot (v0.2.6 Audit)

## Repo Summary
- STDIO, socket, and TCP transports share the guarded NDJSON loop, log ISO-8601 timestamps on readiness/shutdown, and tear down ready files or sockets reliably (`mcp/__main__.py:120`; `mcp/socket_main.py:27`; `mcp/tcp_main.py:14`; `tests/test_tcp.py:47`).
- Semantic request errors now surface as `{ok:false}` JSON-RPC results, keeping malformed frames as the only JSON-RPC errors (`mcp/transport.py:73`; `tests/test_stdio.py:262`; `tests/test_tcp.py:78`).
- Validation, diff, backend, and discovery flows remain deterministic with enforced 1 MiB caps and thorough test coverage (`mcp/validate.py:120`; `mcp/diff.py:49`; `tests/test_validate.py:56`; `tests/test_backend.py:56`).
- Docs, env samples, and compose wiring advertise TCP alongside STDIO/socket, aligning guidance with implementation (`docs/mcp_spec.md:17`; `README.md:35`; `.env.example:2`; `docker-compose.yml:16`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend) | `requirements.txt:2`; `mcp/backend.py:7` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:17` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:8`; `mcp/validate.py:66` |

## Environment Variables
- `MCP_ENDPOINT`: selects `stdio`, `socket`, or `tcp`; unsupported values raise setup errors (`mcp/__main__.py:47`).
- `MCP_READY_FILE`: defaults to `/tmp/mcp.ready`, written `<pid> <ISO8601>` and cleared on shutdown (`mcp/__main__.py:89`; `tests/test_stdio.py:196`).
- `MCP_SOCKET_PATH` / `MCP_SOCKET_MODE`: configure Unix-domain socket location and permissions (`mcp/__main__.py:57`; `mcp/socket_main.py:35`).
- `MCP_HOST` / `MCP_PORT`: configure TCP bind address and port, including ephemeral port support (`mcp/__main__.py:202`; `mcp/tcp_main.py:25`; `tests/test_tcp.py:47`).
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR`: override discovery roots (`mcp/core.py:27`; `mcp/core.py:40`).
- `SYN_BACKEND_URL` / `SYN_BACKEND_ASSETS_PATH`: control backend POST endpoint and path normalization (`mcp/backend.py:17`; `mcp/backend.py:30`).
- `MCP_MAX_BATCH`: positive integer cap enforced by `_max_batch` (`mcp/validate.py:27`; `tests/test_validate.py:103`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, alias warning, payload guard | ✅ Present | `tests/test_stdio.py:56`; `tests/test_stdio.py:292` |
| Socket readiness, guard, multi-client threads | ✅ Present | `tests/test_socket.py:45`; `tests/test_socket.py:187` |
| TCP transport round-trip & guard | ✅ Present | `tests/test_tcp.py:47` |
| Path traversal rejection | ✅ Present | `tests/test_path_traversal.py:34` |
| Ready file lifecycle (PID + ISO) | ✅ Present | `tests/test_stdio.py:196`; `tests/test_socket.py:147`; `tests/test_tcp.py:108` |
| Validation contract & batching | ✅ Present | `tests/test_validate.py:46`; `tests/test_validate.py:103` |
| Backend populate flows & guard | ✅ Present | `tests/test_backend.py:21`; `tests/test_backend.py:56` |
| Golden replay coverage (STDIO) | ✅ Present | `tests/fixtures/golden.jsonl:1`; `tests/test_golden.py:45` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON with 1 MiB guard | Present | `mcp/transport.py:13`; `tests/test_socket.py:130` |
| TCP transport (`MCP_ENDPOINT=tcp`, host/port, guard, tests) | Present | `mcp/__main__.py:216`; `mcp/tcp_main.py:14`; `tests/test_tcp.py:47` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:89`; `tests/test_stdio.py:196`; `tests/test_tcp.py:108` |
| Ready/shutdown logs include dirs + ISO timestamp | Present | `mcp/__main__.py:120`; `tests/test_entrypoint.py:67`; `tests/test_socket.py:105`; `tests/test_tcp.py:59` |
| Spec errors returned in JSON-RPC result payloads | Present | `mcp/transport.py:73`; `tests/test_stdio.py:262`; `tests/test_tcp.py:78` |
| `validate` alias warning (pre-v0.3) | Present | `mcp/stdio_main.py:25`; `tests/test_stdio.py:117` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:199`; `tests/test_validate.py:103` |
| Container runs non-root | Present | `Dockerfile:24`; `tests/test_container.py:1` |
| Docs/scripts updated for TCP | Present | `docs/mcp_spec.md:19`; `README.md:35`; `.env.example:2`; `docker-compose.yml:16` |

## Recommendations
- None; v0.2.6 requirements are fully satisfied.
