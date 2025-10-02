# AGENTS.md — Repo Snapshot (v0.2.7 Audit)

## Repo Summary
- Transports and lifecycle flows satisfy v0.2.7 readiness/shutdown requirements with multi-client coverage (`mcp/__main__.py:185`, `tests/test_tcp.py:272`).
- Validation, batching, diff, and backend tooling enforce deterministic errors and guards (`mcp/validate.py:52`, `mcp/diff.py:16`, `tests/test_validate.py:103`).
- Documentation, env defaults, and container configuration align with runtime behavior (`README.md:94`, `.env.example:2`, `Dockerfile:24`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:30` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:63` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:10`; `mcp/validate.py:93` |

## Environment Variables
- Runtime reads transport, lifecycle, backend, and batching envs with validation (`mcp/__main__.py:103`, `mcp/backend.py:18`, `mcp/validate.py:92`).
- README and `.env.example` document defaults (`README.md:94`, `.env.example:9`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO transport & lifecycle | ✅ | `tests/test_stdio.py:173` |
| Socket transport & concurrency | ✅ | `tests/test_socket.py:146`; `tests/test_socket.py:346` |
| TCP transport & signals | ✅ | `tests/test_tcp.py:117`; `tests/test_tcp.py:411` |
| Backend populate | ✅ | `tests/test_backend.py:21`; `tests/test_backend.py:96` |
| Schema/path guards | ✅ | `tests/test_path_traversal.py:34` |
| Validation & batching | ✅ | `tests/test_validate.py:46`; `tests/test_validate.py:103` |
| Golden replay | ✅ | `tests/test_golden.py:45`; `tests/fixtures/golden.jsonl:1` |
| Container security | ✅ | `tests/test_container.py:4`; `Dockerfile:27` |

## Spec Alignment (v0.2.7)
| Spec Item | Status | Evidence |
| - | - | - |
| 1 MiB guard across STDIO/socket/TCP | Present | `mcp/transport.py:28`; `tests/test_stdio.py:355`; `tests/test_socket.py:185`; `tests/test_tcp.py:167` |
| Ready/shutdown logs mirror metadata | Present | `mcp/__main__.py:185`; `mcp/__main__.py:304`; `tests/test_entrypoint.py:85`; `tests/test_socket.py:283` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:156`; `tests/test_stdio.py:210`; `tests/test_tcp.py:252` |
| Signal exit codes `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:295`; `mcp/__main__.py:439`; `tests/test_entrypoint.py:105` |
| `validate` alias warns + schema required | Present | `mcp/stdio_main.py:23`; `mcp/stdio_main.py:28`; `tests/test_stdio.py:68`; `tests/test_stdio.py:35` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:92`; `tests/test_validate.py:103` |
| Socket perms 0600 + multi-client ordering | Present | `mcp/socket_main.py:27`; `tests/test_socket.py:146`; `tests/test_socket.py:346` |
| TCP multi-client + shutdown logging | Present | `mcp/tcp_main.py:25`; `mcp/tcp_main.py:304`; `tests/test_tcp.py:321`; `tests/test_tcp.py:411` |
| Schema/example traversal guard | Present | `mcp/core.py:18`; `mcp/core.py:62`; `tests/test_path_traversal.py:34`; `tests/test_path_traversal.py:61` |
| JSON-RPC error reserved for malformed frames | Present | `mcp/transport.py:70`; `mcp/transport.py:100`; `tests/fixtures/golden.jsonl:10` |

## Recommendations
- Keep transport regression tests in CI to protect shutdown invariants and multi-client handling (`tests/test_socket.py:278`, `tests/test_tcp.py:411`).
- Update golden fixtures whenever RPC contracts change to maintain deterministic assertions (`tests/test_golden.py:45`, `tests/fixtures/golden.jsonl:1`).
- Retain non-root container posture during dependency upgrades (`Dockerfile:24`, `tests/test_container.py:4`).
