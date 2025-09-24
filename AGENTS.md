# AGENTS.md — Repo Snapshot

## Repo Summary
- **Transports:** STDIO and socket share the NDJSON dispatcher, 1 MiB guard, and ready-file lifecycle; socket now runs each client in its own thread to support concurrent connections (mcp/stdio_main.py:46; mcp/socket_main.py:36; mcp/socket_main.py:67; tests/test_socket.py:147).
- **Path Safety:** Schema/example lookups reject traversal before disk access and retain deterministic listings (mcp/core.py:16; mcp/core.py:85; tests/test_path_traversal.py:34; tests/test_submodule_integration.py:34).
- **Tools:** Validation, diff, and backend operations preserve ordering and payload limits with thorough coverage (mcp/validate.py:114; mcp/validate.py:162; mcp/diff.py:49; mcp/backend.py:38; tests/test_validate.py:46; tests/test_backend.py:65).
- **Process Model:** Entry point logs readiness to stderr, writes `<pid> <ISO8601>` to the ready file, and cleans up on shutdown for both transports (mcp/__main__.py:104; mcp/__main__.py:161; tests/test_stdio.py:121; tests/test_socket.py:131).
- **Container & Compose:** Image runs as non-root and compose healthchecks rely on the ready file while passing transport env vars through (Dockerfile:24; docker-compose.yml:18; docker-compose.yml:26).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_stdio.py:12 |
| referencing | Local schema registry support | Optional | mcp/validate.py:9 |

## Environment Variables
- `MCP_ENDPOINT`: defaults to `stdio`; rejects unsupported transports (mcp/__main__.py:36; tests/test_entrypoint.py:95).
- `MCP_READY_FILE`: `/tmp/mcp.ready` by default; written on ready and removed on shutdown (mcp/__main__.py:69; mcp/__main__.py:115).
- `MCP_SOCKET_PATH` / `MCP_SOCKET_MODE`: configure UDS location and permissions (mcp/__main__.py:47; mcp/__main__.py:52; mcp/socket_main.py:34).
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR`: override discovery roots; invalid schema directories abort startup (mcp/__main__.py:23; tests/test_entrypoint.py:81).
- `SYN_BACKEND_URL`: enables backend POST; unset returns `unsupported` (mcp/backend.py:30; tests/test_backend.py:21).
- `SYN_BACKEND_ASSETS_PATH`: normalized to a leading slash before POST (mcp/backend.py:17; tests/test_backend.py:46).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, guard, alias coverage | ✅ | tests/test_stdio.py:29; tests/test_stdio.py:56; tests/test_stdio.py:220 |
| Socket server handshake, guard, and multi-client threads | ✅ | tests/test_socket.py:84; tests/test_socket.py:114; tests/test_socket.py:147 |
| Path traversal rejection | ✅ | tests/test_path_traversal.py:34 |
| Ready file lifecycle & shutdown | ✅ | tests/test_entrypoint.py:54; tests/test_socket.py:131 |
| Validation contract & ordering | ✅ | tests/test_validate.py:46 |
| Backend populate flows & guard | ✅ | tests/test_backend.py:28; tests/test_backend.py:65 |
| Schema discovery (env + submodule) | ✅ | tests/test_env_discovery.py:29; tests/test_submodule_integration.py:28 |
| Diff determinism | ✅ | tests/test_diff.py:11 |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON transport | Present | mcp/stdio_main.py:46; mcp/socket_main.py:95; mcp/transport.py:41 |
| Ready file `<pid> <ISO8601>` lifecycle | Present | mcp/__main__.py:69; mcp/__main__.py:161; tests/test_stdio.py:121 |
| 1 MiB per-request guard | Present | mcp/transport.py:15; mcp/socket_main.py:110; tests/test_stdio.py:220 |
| `validate` alias coverage | Present | mcp/stdio_main.py:22; tests/test_stdio.py:56 |
| Path traversal rejection | Present | mcp/core.py:16; mcp/validate.py:130; tests/test_path_traversal.py:53 |
| Socket multi-client support | Present | mcp/socket_main.py:67; tests/test_socket.py:147 |

## Recommendations
- Strengthen the multi-client socket regression by sending overlapping requests from both clients to verify ordering under load (tests/test_socket.py:191).
- Add automated coverage for `MCP_SOCKET_MODE` overrides to guard permissions behavior (mcp/__main__.py:52; mcp/socket_main.py:34).
- Add a STDIO test ensuring the process exits cleanly when stdin closes without signals (mcp/stdio_main.py:46).
