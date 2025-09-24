# AGENTS.md — Repo Snapshot (v0.2.5 Audit)

## Repo Summary
- STDIO and socket transports share the NDJSON loop with a 1 MiB pre-parse guard backed by integration coverage (`mcp/transport.py:13`, `mcp/socket_main.py:95`, `tests/test_stdio.py:283`, `tests/test_socket.py:119`).
- Ready-file lifecycle logs `<pid> <ISO8601>` and cleans up on both transports, with tests confirming creation and shutdown hooks (`mcp/__main__.py:80`, `mcp/__main__.py:170`, `tests/test_stdio.py:183`, `tests/test_socket.py:147`).
- Validation, batching, diff, and backend paths enforce deterministic ordering and payload caps across units (`mcp/validate.py:119`, `mcp/diff.py:16`, `mcp/backend.py:38`, `tests/test_validate.py:46`, `tests/test_backend.py:56`).
- Schema discovery stays local-only with traversal protection and deterministic listings (`mcp/core.py:16`, `mcp/core.py:69`, `tests/test_path_traversal.py:34`, `tests/test_submodule_integration.py:32`).
- Docker image runs as non-root and compose health checks rely on the ready file contract (`Dockerfile:24`, `docker-compose.yml:17`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_stdio.py:12 |
| referencing | Local schema registry support | Optional | mcp/validate.py:8; mcp/validate.py:70 |

## Environment Variables
- `MCP_ENDPOINT`: defaults to `stdio`; rejects unsupported transports (`mcp/__main__.py:47`).
- `MCP_READY_FILE`: `/tmp/mcp.ready` default; written on ready, removed on shutdown (`mcp/__main__.py:72`, `mcp/__main__.py:133`).
- `MCP_SOCKET_PATH` / `MCP_SOCKET_MODE`: control UDS location and 0600 perms (`mcp/__main__.py:57`, `mcp/socket_main.py:35`).
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR`: override discovery roots (`mcp/core.py:27`, `mcp/core.py:40`).
- `SYN_BACKEND_URL` / `SYN_BACKEND_ASSETS_PATH`: enable backend POST and path normalization (`mcp/backend.py:30`, `mcp/backend.py:17`).
- `MCP_MAX_BATCH`: caps `validate_many`; must be positive (`mcp/validate.py:27`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, guard, alias warning | ✅ **Present** | `tests/test_stdio.py:56`; `tests/test_stdio.py:283` |
| Socket readiness, guard, multi-client threads | ✅ **Present** | `tests/test_socket.py:87`; `tests/test_socket.py:153` |
| Path traversal rejection | ✅ **Present** | `tests/test_path_traversal.py:34` |
| Ready file lifecycle & shutdown | ✅ **Present** | `tests/test_stdio.py:183`; `tests/test_socket.py:147` |
| Validation contract & batching | ✅ **Present** | `tests/test_validate.py:46`; `tests/test_validate.py:103` |
| Backend populate flows & guard | ✅ **Present** | `tests/test_backend.py:21`; `tests/test_backend.py:56` |
| Schema discovery (env + submodule) | ✅ **Present** | `tests/test_env_discovery.py:6`; `tests/test_submodule_integration.py:32` |
| Diff determinism | ✅ **Present** | `tests/test_diff.py:1` |
| Golden replay coverage | ✅ **Present** | `tests/test_golden.py:45` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON with 1 MiB guard | ✅ **Present** | `mcp/transport.py:13`; `tests/test_socket.py:119` |
| Ready file `<pid> <ISO8601>` lifecycle | ✅ **Present** | `mcp/__main__.py:80`; `tests/test_stdio.py:183` |
| Path traversal rejection | ✅ **Present** | `mcp/core.py:16`; `tests/test_path_traversal.py:34` |
| Socket multi-client support | ✅ **Present** | `mcp/socket_main.py:66`; `tests/test_socket.py:153` |
| `validate` alias warning (v0.2.5) | ✅ **Present** | `mcp/stdio_main.py:23`; `tests/test_stdio.py:56` |
| `validate_many` batching with `MCP_MAX_BATCH` | ✅ **Present** | `mcp/validate.py:27`; `tests/test_validate.py:103` |
| Golden request/response set | ✅ **Present** | `tests/fixtures/golden.jsonl:1`; `tests/test_golden.py:45` |
| Documentation alignment (spec + README) | ✅ **Present** | `docs/mcp_spec.md:1`; `README.md:2` |

## Recommendations
1. Assert STDIO ready-file removal after shutdown to prevent regressions in cleanup (`mcp/__main__.py:133`; `tests/test_stdio.py:155`).
2. Capture default socket file permissions in the integration suite to lock in the 0600 requirement (`mcp/socket_main.py:35`; `tests/test_socket.py:45`).
3. Add coverage for invalid `MCP_MAX_BATCH` values so misconfiguration fails fast in tests (`mcp/validate.py:27`; `tests/test_validate.py:103`).
