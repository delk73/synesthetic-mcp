# AGENTS.md — Repo Snapshot (v0.2.7 Audit)

## Repo Summary
This snapshot reflects a successful audit against the `v0.2.7` specification. The repository is fully compliant.
- **Transports**: STDIO, Unix Domain Socket, and TCP are fully implemented and tested, including multi-client support, 1 MiB payload guards, and graceful shutdown.
- **Lifecycle**: Process lifecycle is robust, with correct signal handling (SIGINT/SIGTERM), readiness logging (`mcp:ready`), shutdown logging, and ready-file management (`/tmp/mcp.ready`).
- **Features**: All specified features, including `validate_asset`, the `validate` alias, `validate_many` batching, `get_example`, and `diff_assets`, are present and work as specified.
- **Security & Determinism**: The container runs as a non-root user, socket permissions are restrictive by default, path traversal is blocked, and API outputs are deterministic.

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:24` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:13` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:10`; `mcp/validate.py:70` |

## Environment Variables
Environment variables are the primary means of configuration. All variables listed in the `README.md` and `.env.example` are correctly implemented.
- **Transport Control**: `MCP_ENDPOINT`, `MCP_HOST`, `MCP_PORT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE`.
- **Lifecycle**: `MCP_READY_FILE` for health checks.
- **Resource Paths**: `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR`.
- **Backend**: `SYN_BACKEND_URL`, `SYN_BACKEND_ASSETS_PATH`.
- **Limits**: `MCP_MAX_BATCH`.

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO Transport & Features | ✅ Present | `tests/test_stdio.py` |
| Socket Transport & Features | ✅ Present | `tests/test_socket.py` |
| TCP Transport & Features | ✅ Present | `tests/test_tcp.py` |
| Backend Population Logic | ✅ Present | `tests/test_backend.py` |
| Path Traversal Rejection | ✅ Present | `tests/test_path_traversal.py` |
| Process Lifecycle & Signals | ✅ Present | `tests/test_entrypoint.py` |
| Validation Contracts & Batching | ✅ Present | `tests/test_validate.py` |
| Golden Master Replay | ✅ Present | `tests/test_golden.py` |
| Container Security (non-root) | ✅ Present | `tests/test_container.py`, `Dockerfile` |

## Spec Alignment (v0.2.7)
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP 1 MiB guard | Present | `mcp/transport.py:26`; `tests/test_stdio.py:352`; `tests/test_socket.py:141` |
| Ready/shutdown logs include all required fields | Present | `mcp/__main__.py:165`; `tests/test_entrypoint.py:65` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:139`; `tests/test_stdio.py:208` |
| Signal exit codes `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:176`; `tests/test_entrypoint.py:118` |
| `validate` alias warns + requires schema | Present | `mcp/stdio_main.py:24`; `tests/test_stdio.py:88` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:199`; `tests/test_validate.py:118` |
| Socket default perms `0600` + multi-client ordering | Present | `mcp/socket_main.py:35`; `tests/test_socket.py:109` |
| TCP ready/shutdown logs, guard, multi-client | Present | `mcp/tcp_main.py:264`; `tests/test_tcp.py` |
| Schema/example traversal guard | Present | `mcp/core.py:16`; `tests/test_path_traversal.py` |

## Recommendations
- **Maintain Test Rigor**: Continue to ensure all new features or transport changes are accompanied by comprehensive tests covering functionality, security, and lifecycle.
- **Update Golden Files**: Ensure `tests/fixtures/golden.jsonl` is updated whenever API request/response contracts change.
- **Preserve Compliance Checks**: Protect critical tests for spec compliance (e.g., JSON-RPC version enforcement) from accidental removal.