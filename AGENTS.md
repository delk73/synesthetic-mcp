# AGENTS.md — Repo Snapshot (v0.2.7 Audit)

## Repo Summary
- STDIO/socket/TCP reuse the NDJSON dispatcher with the 1 MiB guard covered in transport regressions (`mcp/transport.py:26`; `tests/test_tcp.py:142`).
- Entrypoint logs mode + dirs, manages the `<pid> <ISO>` ready file, and propagates negative exit codes on signals (`mcp/__main__.py:139`; `mcp/__main__.py:165`; `tests/test_entrypoint.py:84`).
- Validation/diff/backend flows stay deterministic with alias warnings, sorted errors, and guarded populate (`mcp/stdio_main.py:24`; `mcp/validate.py:176`; `tests/test_backend.py:23`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:24` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:13` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:10`; `mcp/validate.py:70` |

## Environment Variables
- Transport selection and validation (`MCP_ENDPOINT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE`, `MCP_HOST`, `MCP_PORT`) gate startup before servers begin (`mcp/__main__.py:86`; `mcp/__main__.py:100`; `mcp/__main__.py:123`; `tests/test_entrypoint.py:167`).
- Ready-file lifecycle writes `<pid> <ISO>` and clears on shutdown across STDIO/socket/TCP (`mcp/__main__.py:139`; `tests/test_stdio.py:208`; `tests/test_tcp.py:317`).
- Schema/example roots respect env overrides with traversal rejection tests guarding escapes (`mcp/core.py:27`; `tests/test_path_traversal.py:31`).
- Backend URL/path and batch envs steer populate behavior and `validate_many` limits (`mcp/backend.py:24`; `mcp/validate.py:27`; `tests/test_validate.py:118`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, alias warning, payload guard | ✅ Present | `tests/test_stdio.py:126`; `tests/test_stdio.py:138`; `tests/test_stdio.py:310` |
| Socket readiness, guard, multi-client threads, perms | ✅ Present | `tests/test_socket.py:101`; `tests/test_socket.py:109`; `tests/test_socket.py:227` |
| TCP transport round-trip, guard, multi-client ordering | ✅ Present | `tests/test_tcp.py:90`; `tests/test_tcp.py:142`; `tests/test_tcp.py:233` |
| Backend populate flows & guard | ✅ Present | `tests/test_backend.py:23`; `tests/test_backend.py:60` |
| Path traversal rejection | ✅ Present | `tests/test_path_traversal.py:31` |
| Ready file lifecycle (PID + ISO) | ✅ Present | `tests/test_stdio.py:208`; `tests/test_tcp.py:317` |
| Validation contract & batching | ✅ Present | `tests/test_validate.py:46`; `tests/test_validate.py:118`; `tests/test_validate.py:145` |
| Golden STDIO replay coverage | ✅ Present | `tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP 1 MiB guard | Present | `mcp/transport.py:26`; `tests/test_socket.py:141`; `tests/test_tcp.py:142` |
| Ready/shutdown logs include mode + dirs + ISO | Present | `mcp/__main__.py:165`; `mcp/__main__.py:283`; `tests/test_entrypoint.py:65` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:139`; `mcp/__main__.py:155`; `tests/test_stdio.py:208`; `tests/test_tcp.py:317` |
| Signal exit codes `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:176`; `mcp/__main__.py:407`; `tests/test_entrypoint.py:84`; `tests/test_entrypoint.py:125` |
| `validate` alias warns + requires schema | Present | `mcp/stdio_main.py:24`; `mcp/stdio_main.py:28`; `tests/test_stdio.py:138` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:199`; `tests/test_validate.py:118` |
| Socket default perms 0600 + multi-client ordering | Present | `mcp/socket_main.py:35`; `mcp/socket_main.py:66`; `tests/test_socket.py:109`; `tests/test_socket.py:227` |
| TCP ready/shutdown logs, guard, multi-client threads | Present | `mcp/tcp_main.py:264`; `mcp/tcp_main.py:275`; `tests/test_tcp.py:158`; `tests/test_tcp.py:233` |
| Schema/example traversal guard | Present | `mcp/core.py:16`; `mcp/core.py:61`; `tests/test_path_traversal.py:31` |
| Docs + metadata reflect v0.2.7 and TCP guard | Present | `README.md:2`; `README.md:36`; `README.md:177`; `docs/mcp_spec.md:30` |

## Recommendations
- Enforce and test `jsonrpc == "2.0"` so unsupported protocol frames return `validation_failed` instead of executing (`mcp/transport.py:26`; `tests/test_stdio.py:261`).
- Extend STDIO SIGTERM coverage to assert ready-file cleanup alongside exit codes (`mcp/__main__.py:283`; `tests/test_entrypoint.py:87`).
- Add SIGTERM shutdown tests for socket and TCP to prove cleanup and exit behavior across all transports (`mcp/__main__.py:275`; `tests/test_socket.py:158`; `tests/test_tcp.py:158`).
