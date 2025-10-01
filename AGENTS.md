# AGENTS.md — Repo Snapshot (v0.2.7 Audit)

## Repo Summary
- JSON-RPC parsing now enforces `jsonrpc == "2.0"`, keeping transports spec-compliant and covered by a stdio regression test (`mcp/transport.py:32`; `tests/test_stdio.py:312`).
- SIGTERM paths for STDIO/socket/TCP confirm shutdown logs, ready-file cleanup, and negative exit codes, complementing existing SIGINT coverage (`tests/test_entrypoint.py:118`; `tests/test_socket.py:209`; `tests/test_tcp.py:180`).
- Deterministic validation, backend, diff, and traversal protections remain unchanged with golden replay still validating API surface (`mcp/validate.py:176`; `tests/test_backend.py:23`; `tests/test_golden.py:18`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:24` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:13` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:10`; `mcp/validate.py:70` |

## Environment Variables
- Transport selection/env validation (`MCP_ENDPOINT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE`, `MCP_HOST`, `MCP_PORT`) still gate startup; new SIGTERM tests exercise ready-file overrides and cleanup (`mcp/__main__.py:81`; `tests/test_entrypoint.py:118`; `tests/test_socket.py:233`; `tests/test_tcp.py:222`).
- Ready-file lifecycle maintains `<pid> <ISO>` content and removes files on shutdown across transports (`mcp/__main__.py:139`; `tests/test_stdio.py:208`; `tests/test_tcp.py:236`).
- Schema/example overrides remain fenced with traversal tests guarding escapes (`mcp/core.py:27`; `tests/test_path_traversal.py:31`).
- Backend URL/path and batch envs continue to steer populate behavior and `validate_many` limits (`mcp/backend.py:24`; `mcp/validate.py:27`; `tests/test_validate.py:118`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, alias warning, payload guard, jsonrpc gate | ✅ Present | `tests/test_stdio.py:126`; `tests/test_stdio.py:138`; `tests/test_stdio.py:312` |
| Socket readiness, guard, SIGTERM cleanup, multi-client threads, perms | ✅ Present | `tests/test_socket.py:101`; `tests/test_socket.py:141`; `tests/test_socket.py:209`; `tests/test_socket.py:259` |
| TCP transport round-trip, guard, SIGTERM cleanup, multi-client ordering | ✅ Present | `tests/test_tcp.py:90`; `tests/test_tcp.py:142`; `tests/test_tcp.py:180`; `tests/test_tcp.py:233` |
| Backend populate flows & guard | ✅ Present | `tests/test_backend.py:23`; `tests/test_backend.py:60` |
| Path traversal rejection | ✅ Present | `tests/test_path_traversal.py:31` |
| Ready file lifecycle (PID + ISO) | ✅ Present | `tests/test_stdio.py:208`; `tests/test_tcp.py:236` |
| Validation contract & batching | ✅ Present | `tests/test_validate.py:46`; `tests/test_validate.py:118`; `tests/test_validate.py:145` |
| Golden STDIO replay coverage | ✅ Present | `tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP 1 MiB guard | Present | `mcp/transport.py:26`; `tests/test_socket.py:141`; `tests/test_tcp.py:142` |
| Ready/shutdown logs include mode + dirs + ISO | Present | `mcp/__main__.py:165`; `tests/test_entrypoint.py:65`; `tests/test_tcp.py:226` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:139`; `mcp/__main__.py:155`; `tests/test_stdio.py:208`; `tests/test_socket.py:253` |
| Signal exit codes `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:176`; `tests/test_entrypoint.py:131`; `tests/test_socket.py:253`; `tests/test_tcp.py:236` |
| `validate` alias warns + requires schema | Present | `mcp/stdio_main.py:24`; `mcp/stdio_main.py:28`; `tests/test_stdio.py:138` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:199`; `tests/test_validate.py:118` |
| Socket default perms 0600 + multi-client ordering | Present | `mcp/socket_main.py:35`; `mcp/socket_main.py:66`; `tests/test_socket.py:109`; `tests/test_socket.py:259` |
| TCP ready/shutdown logs, guard, multi-client threads | Present | `mcp/tcp_main.py:264`; `mcp/tcp_main.py:275`; `tests/test_tcp.py:158`; `tests/test_tcp.py:233` |
| Schema/example traversal guard | Present | `mcp/core.py:16`; `mcp/core.py:61`; `tests/test_path_traversal.py:31` |
| Docs + metadata reflect v0.2.7 and TCP guard | Present | `README.md:2`; `README.md:36`; `README.md:177`; `docs/mcp_spec.md:30` |

## Recommendations
- Keep the JSON-RPC version enforcement test in CI to guard against regressions when adding new transports (`mcp/transport.py:32`; `tests/test_stdio.py:312`).
- Document sandbox requirements for socket/TCP tests since they skip when the environment blocks binds (`tests/test_socket.py:234`; `tests/test_tcp.py:219`).
- Continue running the golden replay alongside transport suites before tagging future releases (`tests/test_golden.py:18`).
