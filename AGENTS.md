# AGENTS.md — Repo Snapshot (v0.2.5 Audit)

## Repo Summary
- **Transports:** STDIO and socket transports are functional, but testing for payload size guards is incomplete.
- **Schema Safety:** Local-only schema discovery is implemented correctly with path traversal protections.
- **Tools:** Core tools like validation, diff, and backend population are implemented. However, testing for the `validate` alias deprecation warning is missing.
- **Process Model:** The entrypoint and process model are correctly implemented for both STDIO and socket transports.
- **Container & Compose:** The container correctly runs as a non-root user.

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_stdio.py:13 |
| referencing | Local schema registry support | Optional | mcp/validate.py:8; mcp/validate.py:66 |

## Environment Variables
- `MCP_ENDPOINT`: defaults to `stdio`; rejects unsupported transports.
- `MCP_READY_FILE`: `/tmp/mcp.ready` by default; written on ready and removed on shutdown.
- `MCP_SOCKET_PATH` / `MCP_SOCKET_MODE`: control UDS location and permissions.
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR`: override discovery roots.
- `SYN_BACKEND_URL`: enables backend POST; unset returns `unsupported`.
- `MCP_MAX_BATCH`: caps `validate_many`; must be positive.

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, guard, alias warning | 🟡 **Divergent** | `tests/test_stdio.py` (alias warning not tested) |
| Socket readiness, guard, multi-client threads | 🟡 **Divergent** | `tests/test_socket.py` (payload guard not tested for all methods) |
| Path traversal rejection | ✅ **Present** | `tests/test_path_traversal.py` |
| Ready file lifecycle & shutdown | ✅ **Present** | `tests/test_entrypoint.py`, `tests/test_socket.py` |
| Validation contract & batching | ✅ **Present** | `tests/test_validate.py` |
| Backend populate flows & guard | ✅ **Present** | `tests/test_backend.py` |
| Schema discovery (env + submodule) | ✅ **Present** | `tests/test_env_discovery.py`, `tests/test_submodule_integration.py` |
| Diff determinism | ✅ **Present** | `tests/test_diff.py` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON with 1 MiB guard | 🟡 **Divergent** | Incomplete test coverage |
| Ready file `<pid> <ISO8601>` lifecycle | ✅ **Present** | `mcp/__main__.py` |
| Path traversal rejection | ✅ **Present** | `mcp/core.py`, `tests/test_path_traversal.py` |
| Socket multi-client support | ✅ **Present** | `mcp/socket_main.py`, `tests/test_socket.py` |
| `validate` alias warning (v0.2.5) | 🟡 **Divergent** | `mcp/stdio_main.py` (no test) |
| `validate_many` batching with `MCP_MAX_BATCH` | ✅ **Present** | `mcp/validate.py`, `tests/test_validate.py` |

## Recommendations
1.  Add a test to `tests/test_stdio.py` that uses the `validate` alias and asserts that the deprecation warning is written to `stderr`.
2.  Add tests to `tests/test_validate.py` and `tests/test_stdio.py` to ensure oversized payloads are rejected by `validate_many` and the stdio transport.
3.  Create a `golden.jsonl` file in `tests/fixtures` with example requests and responses for all MCP methods.