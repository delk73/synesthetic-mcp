# AGENTS.md — Repo Snapshot (v0.2.6 Audit)

## Repo Summary
- Shared NDJSON dispatcher enforces 1 MiB guard across transports, with ISO ready/shutdown logs and ready-file cleanup under test (`mcp/transport.py:26`; `mcp/__main__.py:165`; `tests/test_stdio.py:171`; `tests/test_socket.py:155`; `tests/test_tcp.py:153`).
- Validation, diff, and discovery remain deterministic with guarded paths and alias handling backed by fixtures (`mcp/validate.py:92`; `mcp/diff.py:12`; `mcp/core.py:44`; `tests/test_submodule_integration.py:33`).
- Backend populate observes payload caps and optional validation while docs/Compose describe STDIO, socket, and TCP usage consistently (`mcp/backend.py:45`; `README.md:35`; `docker-compose.yml:21`; `.env.example:1`).
- Golden STDIO replay covers list/get/validate/diff/backend/malformed flows and checks alias warnings on stderr (`tests/test_golden.py:45`; `tests/fixtures/golden.jsonl:1`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:7` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:17` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:10`; `mcp/validate.py:121` |

## Environment Variables
- Transport selection (`MCP_ENDPOINT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE`, `MCP_HOST`, `MCP_PORT`) validated before server start (`mcp/__main__.py:81`; `mcp/__main__.py:118`).
- Ready-file lifecycle writes `<pid> <ISO8601>` and cleans up on shutdown (`mcp/__main__.py:134`; `tests/test_stdio.py:201`).
- Schema/example roots fenced by env overrides with traversal rejection (`mcp/core.py:27`; `tests/test_path_traversal.py:25`).
- Backend URL/path and batch limit envs drive populate and `validate_many` limits (`mcp/backend.py:17`; `mcp/validate.py:167`; `tests/test_validate.py:87`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, alias warning, payload guard | ✅ Present | `tests/test_stdio.py:39`; `tests/test_stdio.py:66`; `tests/test_stdio.py:189` |
| Socket readiness, guard, multi-client threads | ✅ Present (permission check missing) | `tests/test_socket.py:100`; `tests/test_socket.py:137`; `tests/test_socket.py:175` |
| TCP transport round-trip & guard | ⚠️ Missing validate coverage | `docs/mcp_spec.md:21`; `tests/test_tcp.py:108` |
| Backend populate flows & guard | ⚠️ HTTPError branch untested | `mcp/backend.py:60`; `tests/test_backend.py:18` |
| Path traversal rejection | ✅ Present | `tests/test_path_traversal.py:25` |
| Ready file lifecycle (PID + ISO) | ✅ Present | `tests/test_stdio.py:201`; `tests/test_socket.py:155`; `tests/test_tcp.py:153` |
| Validation contract & batching | ✅ Present | `tests/test_validate.py:32`; `tests/test_validate.py:87` |
| Golden replay coverage (STDIO) | ✅ Present | `tests/test_golden.py:45`; `tests/fixtures/golden.jsonl:1` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON with 1 MiB guard | Present | `mcp/transport.py:26`; `tests/test_socket.py:137` |
| TCP transport (`MCP_ENDPOINT=tcp`, host/port, guard, tests) | Missing validate round-trip | `docs/mcp_spec.md:21`; `tests/test_tcp.py:108` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:134`; `tests/test_stdio.py:201`; `tests/test_tcp.py:168` |
| Ready/shutdown logs include dirs + ISO timestamp | Present | `mcp/__main__.py:165`; `tests/test_entrypoint.py:31`; `tests/test_socket.py:155` |
| Spec errors returned in JSON-RPC result payloads | Present | `mcp/transport.py:87`; `tests/test_stdio.py:39`; `tests/test_socket.py:120` |
| `validate` alias warning (pre-v0.3) | Present | `mcp/stdio_main.py:20`; `tests/test_stdio.py:129` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:167`; `tests/test_validate.py:87` |
| Security defaults: socket mode 0600 proven in tests | Missing | `mcp/socket_main.py:35`; `tests/test_socket.py:106` |
| Backend HTTPError → backend_error 503 verified | Missing | `mcp/backend.py:60`; `tests/test_backend.py:18` |
| Docs/scripts updated for TCP | Present | `docs/mcp_spec.md:13`; `README.md:35`; `docker-compose.yml:21` |

## Recommendations
- Add a TCP `validate_asset` (or alias) request to the integration test matrix to satisfy the v0.2.6 audit requirement (`docs/mcp_spec.md:21`; `tests/test_tcp.py:108`).
- Extend socket tests with a permission assertion on the socket path (expected 0600) to prove least-privilege defaults (`mcp/socket_main.py:35`; `tests/test_socket.py:106`).
- Simulate `httpx.HTTPError` in backend tests to verify the 503 mapping and lock in error handling (`mcp/backend.py:60`; `tests/test_backend.py:18`).
