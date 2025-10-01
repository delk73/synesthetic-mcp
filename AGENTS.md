# AGENTS.md — Repo Snapshot (v0.2.7 Audit)

## Repo Summary
- STDIO/socket/TCP share the 1 MiB NDJSON guard with ISO ready/shutdown logs validated end-to-end (`mcp/transport.py:26`; `mcp/__main__.py:165`; `tests/test_tcp.py:89`).
- Validation, diff, traversal fences, and backend populate stay deterministic with targeted regression coverage (`mcp/core.py:69`; `mcp/validate.py:120`; `mcp/diff.py:42`; `tests/test_validate.py:46`; `tests/test_backend.py:28`).
- Signal handling still returns `0` on SIGINT/SIGTERM despite the v0.2.7 requirement for negative exit codes (`docs/mcp_spec.md:24`; `mcp/__main__.py:157`; `tests/test_entrypoint.py:80`).
- README and `__version__` remain at v0.2.6 and omit TCP from the payload-guard blurb even though TCP enforcement shipped (`mcp/__init__.py:6`; `README.md:2`; `README.md:36`; `tests/test_tcp.py:135`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:24` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:13` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:10`; `mcp/validate.py:93` |

## Environment Variables
- Transport selection (`MCP_ENDPOINT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE`, `MCP_HOST`, `MCP_PORT`) validated before server start (`mcp/__main__.py:81`; `mcp/__main__.py:118`; `tests/test_entrypoint.py:108`).
- Ready-file lifecycle writes `<pid> <ISO8601>` and cleans up across transports (`mcp/__main__.py:134`; `tests/test_stdio.py:201`; `tests/test_tcp.py:317`).
- Schema/example roots fenced by env overrides with traversal rejection tests (`mcp/core.py:27`; `tests/test_path_traversal.py:34`).
- Backend URL/path and batch limit envs drive populate behavior and `validate_many` limits (`mcp/backend.py:24`; `mcp/validate.py:27`; `tests/test_validate.py:118`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, alias warning, payload guard | ✅ Present | `tests/test_stdio.py:52`; `tests/test_stdio.py:105`; `tests/test_stdio.py:141` |
| Socket readiness, guard, multi-client threads, perms | ✅ Present | `tests/test_socket.py:101`; `tests/test_socket.py:109`; `tests/test_socket.py:227` |
| TCP transport round-trip, guard, multi-client ordering | ✅ Present | `tests/test_tcp.py:89`; `tests/test_tcp.py:135`; `tests/test_tcp.py:233` |
| Backend populate flows & guard | ✅ Present | `tests/test_backend.py:28`; `tests/test_backend.py:56` |
| Path traversal rejection | ✅ Present | `tests/test_path_traversal.py:34` |
| Ready file lifecycle (PID + ISO) | ✅ Present | `tests/test_stdio.py:201`; `tests/test_tcp.py:317` |
| Validation contract & batching | ✅ Present | `tests/test_validate.py:46`; `tests/test_validate.py:118`; `tests/test_validate.py:145` |
| Golden STDIO replay coverage | ✅ Present | `tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP 1 MiB guard | Present | `mcp/transport.py:26`; `mcp/tcp_main.py:98`; `tests/test_tcp.py:135` |
| Ready/shutdown logs include mode + dirs + ISO | Present | `mcp/__main__.py:165`; `tests/test_entrypoint.py:62`; `tests/test_tcp.py:152` |
| `validate` alias warns to stderr | Present | `mcp/stdio_main.py:23`; `tests/test_stdio.py:105` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:199`; `tests/test_validate.py:118` |
| Socket default perms 0600 proved in tests | Present | `mcp/socket_main.py:35`; `tests/test_socket.py:109` |
| Signal exit codes `-SIGINT`/`-SIGTERM` | Missing | `docs/mcp_spec.md:24`; `mcp/__main__.py:157`; `tests/test_entrypoint.py:80` |
| README documents guard across STDIO/socket/TCP | Divergent | `README.md:36`; `README.md:176`; `tests/test_tcp.py:135` |
| Adapter version bumped to v0.2.7 | Divergent | `mcp/__init__.py:6`; `README.md:2`; `docs/mcp_spec.md:2` |

## Recommendations
- Emit `-SIGINT`/`-SIGTERM` exit codes on signal shutdown and adjust lifecycle tests to assert them (`mcp/__main__.py:157`; `tests/test_entrypoint.py:80`; `docs/mcp_spec.md:24`).
- Update version metadata (README front matter and `__version__`) to v0.2.7 so tooling reflects the audited release (`README.md:2`; `mcp/__init__.py:6`; `docs/mcp_spec.md:2`).
- Refresh README transport text to include TCP in the documented 1 MiB guard coverage (`README.md:36`; `README.md:176`; `tests/test_tcp.py:135`).
