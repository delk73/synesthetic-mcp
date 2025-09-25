# AGENTS.md — Repo Snapshot (v0.2.6 Audit)

## Repo Summary
- All transports share the guarded NDJSON loop and surface semantic errors as `{ok:false}` results (`mcp/transport.py:26`; `mcp/socket_main.py:95`; `tests/test_stdio.py:256`).
- Validation, diff, backend, and discovery paths stay deterministic with 1 MiB payload caps and dedicated tests (`mcp/validate.py:23`; `mcp/diff.py:19`; `tests/test_validate.py:52`; `tests/test_backend.py:56`).
- Readiness/shutdown logging carries ISO timestamps plus schema/example dirs, and ready files/sockets are created then cleared on exit (`mcp/__main__.py:163`; `mcp/__main__.py:191`; `tests/test_socket.py:154`; `tests/test_tcp.py:149`).
- Docs, env samples, and compose wiring document TCP alongside STDIO/socket, matching runtime defaults and non-root container posture (`docs/mcp_spec.md:17`; `README.md:35`; `.env.example:1`; `Dockerfile:24`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend) | `requirements.txt:2`; `mcp/backend.py:7` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:17` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:8`; `mcp/validate.py:66` |

## Environment Variables
- `MCP_ENDPOINT`/`MCP_SOCKET_PATH`/`MCP_SOCKET_MODE`/`MCP_HOST`/`MCP_PORT` select transport details with validation (`mcp/__main__.py:81`; `mcp/__main__.py:204`; `README.md:120`).
- `MCP_READY_FILE` controls ready file path which is written `<pid> <ISO8601>` and cleared on shutdown (`mcp/__main__.py:134`; `tests/test_stdio.py:208`).
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR` gate schema discovery roots (`mcp/core.py:27`; `mcp/core.py:61`).
- `SYN_BACKEND_URL` / `SYN_BACKEND_ASSETS_PATH` and `MCP_MAX_BATCH` influence backend posting and batch validation limits (`mcp/backend.py:17`; `mcp/validate.py:27`; `tests/test_validate.py:103`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, alias warning, payload guard | ✅ Present | `tests/test_stdio.py:39`; `tests/test_stdio.py:130`; `tests/test_stdio.py:305` |
| Socket readiness, guard, multi-client threads | ✅ Present | `tests/test_socket.py:55`; `tests/test_socket.py:137`; `tests/test_socket.py:223` |
| TCP transport round-trip & guard | ✅ Present | `tests/test_tcp.py:42`; `tests/test_tcp.py:133` |
| Path traversal rejection | ✅ Present | `tests/test_path_traversal.py:34` |
| Ready file lifecycle (PID + ISO) | ✅ Present | `tests/test_stdio.py:208`; `tests/test_socket.py:165`; `tests/test_tcp.py:147` |
| Validation contract & batching | ✅ Present | `tests/test_validate.py:24`; `tests/test_validate.py:103` |
| Backend populate flows & guard | ✅ Present | `tests/test_backend.py:21`; `tests/test_backend.py:56` |
| Golden replay coverage (STDIO) | ✅ Present | `tests/fixtures/golden.jsonl:1`; `tests/test_golden.py:45` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON with 1 MiB guard | Present | `mcp/transport.py:26`; `tests/test_socket.py:137` |
| TCP transport (`MCP_ENDPOINT=tcp`, host/port, guard, tests) | Present | `mcp/__main__.py:204`; `mcp/tcp_main.py:56`; `tests/test_tcp.py:42` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:134`; `tests/test_stdio.py:208`; `tests/test_tcp.py:147` |
| Ready/shutdown logs include dirs + ISO timestamp | Present | `mcp/__main__.py:163`; `tests/test_entrypoint.py:44`; `tests/test_socket.py:155` |
| Spec errors returned in JSON-RPC result payloads | Present | `mcp/transport.py:77`; `tests/test_stdio.py:256`; `tests/test_socket.py:120` |
| `validate` alias warning (pre-v0.3) | Present | `mcp/stdio_main.py:25`; `tests/test_stdio.py:130` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:199`; `tests/test_validate.py:103` |
| Container runs non-root | Present | `Dockerfile:24`; `tests/test_container.py:4` |
| Docs/scripts updated for TCP | Present | `docs/mcp_spec.md:19`; `README.md:35`; `docker-compose.yml:16` |

## Recommendations
- Assert STDIO shutdown removes the ready file to cover `_clear_ready_file` (`mcp/__main__.py:150`; `tests/test_stdio.py:201`).
- Add a TCP multi-client test to exercise `_handle_connection` threading (`mcp/tcp_main.py:70`; `tests/test_tcp.py:102`).
- Cover `MCP_PORT=0` ephemeral binding in tests to lock logging semantics (`mcp/__main__.py:223`; `tests/test_tcp.py:42`).
