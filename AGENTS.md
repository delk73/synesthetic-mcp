# AGENTS.md — Repo Snapshot

## Repo Summary
- **Transports:** STDIO and Unix-domain socket endpoints share the NDJSON loop, 1 MiB guard, and readiness lifecycle (mcp/stdio_main.py:13; mcp/transport.py:41; mcp/socket_main.py:15; mcp/__main__.py:125; tests/test_stdio.py:29; tests/test_socket.py:45).
- **Path Safety:** Schema/example lookups now reject traversal and schema escapes before touching disk (mcp/core.py:16; mcp/validate.py:130; tests/test_path_traversal.py:53).
- **Tools:** Validation, diff, and backend populate remain deterministic with local-only schemas and coverage for error ordering and guards (mcp/validate.py:106; mcp/diff.py:42; mcp/backend.py:28; tests/test_validate.py:46; tests/test_backend.py:28).
- **Schema Discovery:** Env overrides and submodule fallback continue to drive listings with ordering guarantees (mcp/core.py:27; mcp/core.py:40; tests/test_env_discovery.py:29; tests/test_submodule_integration.py:23).
- **Container Hardening:** Image now runs as a non-root user while keeping `/tmp` writable for ready files (Dockerfile:23).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:5 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_stdio.py:12 |
| referencing | Local schema registry support | Optional | mcp/validate.py:9 |

## Environment Variables
- `MCP_ENDPOINT`: defaults to `stdio`; set to `socket` to run the Unix-domain socket server (mcp/__main__.py:36).
- `MCP_READY_FILE`: `/tmp/mcp.ready` by default; written on readiness and removed on shutdown (mcp/__main__.py:69, mcp/__main__.py:152, mcp/__main__.py:161).
- `MCP_SOCKET_PATH` / `MCP_SOCKET_MODE`: configure the socket path and file mode when socket transport is enabled (mcp/__main__.py:46, mcp/__main__.py:52; docker-compose.yml:15).
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR`: override discovery roots; missing directories fail fast (mcp/__main__.py:23; tests/test_env_discovery.py:29).
- `SYN_BACKEND_URL`: gates backend POST; unset returns `unsupported` (mcp/backend.py:20; tests/test_backend.py:21).
- `SYN_BACKEND_ASSETS_PATH`: normalized to a leading slash before POST (mcp/backend.py:24; tests/test_backend.py:46).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, guard, alias coverage | ✅ | tests/test_stdio.py:29; tests/test_stdio.py:56; tests/test_stdio.py:184 |
| Socket server handshake & cleanup (skipped if UDS blocked) | ✅ | tests/test_socket.py:45 |
| Path traversal rejection | ✅ | tests/test_path_traversal.py:53 |
| Ready file lifecycle & shutdown | ✅ | tests/test_stdio.py:92; tests/test_entrypoint.py:31 |
| Validation contract & ordering | ✅ | tests/test_validate.py:46 |
| Backend populate flows & guard | ✅ | tests/test_backend.py:28; tests/test_backend.py:65 |
| Schema discovery (env + submodule) | ✅ | tests/test_env_discovery.py:29; tests/test_submodule_integration.py:23 |
| Diff determinism | ✅ | tests/test_diff.py:6 |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON transport | Present | mcp/stdio_main.py:13; mcp/socket_main.py:15; mcp/transport.py:41 |
| Ready file `<pid> <ISO8601>` lifecycle | Present | mcp/__main__.py:104; mcp/__main__.py:148; tests/test_stdio.py:92 |
| 1 MiB per-request guard | Present | mcp/transport.py:13; mcp/socket_main.py:77; tests/test_stdio.py:184 |
| `validate` alias coverage | Present | mcp/stdio_main.py:22; tests/test_stdio.py:56 |
| Path traversal rejection | Present | mcp/core.py:16; mcp/validate.py:130; tests/test_path_traversal.py:53 |
| Container security guidance | Present | Dockerfile:23 |

## Recommendations
- Monitor socket support in CI environments that permit UDS to ensure the integration test runs without skips.
- Consider extending socket mode to handle concurrent clients if future workloads require it.
