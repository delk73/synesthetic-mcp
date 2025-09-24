# AGENTS.md — Repo Snapshot (v0.2.5 Audit)

## Repo Summary
- STDIO and socket transports satisfy v0.2.5 requirements with alias warnings and payload caps covered by tests (`tests/test_stdio.py:56-147`, `tests/test_socket.py:87-220`).
- Validation, batching, and backend paths enforce the 1 MiB guard and batch limits as specified (`tests/test_validate.py:56-157`, `tests/test_backend.py:63-77`).
- Golden request/response fixtures now lock in deterministic JSON-RPC behavior across all methods (`tests/fixtures/golden.jsonl:1-10`, `tests/test_golden.py:18-105`).
- Schema discovery remains local-only with traversal protections and deterministic listings (`tests/test_path_traversal.py:25-74`, `tests/test_submodule_integration.py:28-53`).
- Container image runs as non-root and compose health checks rely on the MCP ready file (`Dockerfile:1-31`, `docker-compose.yml:17-33`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_stdio.py:12 |
| referencing | Local schema registry support | Optional | mcp/validate.py:8; mcp/validate.py:66 |

## Environment Variables
- `MCP_ENDPOINT`: defaults to `stdio`; rejects unsupported transports (`mcp/__main__.py:47-55`).
- `MCP_READY_FILE`: `/tmp/mcp.ready` default; written on ready, removed on shutdown (`mcp/__main__.py:115-138`).
- `MCP_SOCKET_PATH` / `MCP_SOCKET_MODE`: control UDS location and perms (`mcp/__main__.py:57-70`, `mcp/socket_main.py:30-51`).
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR`: override discovery roots (`mcp/core.py:60-118`).
- `SYN_BACKEND_URL` / `SYN_BACKEND_ASSETS_PATH`: enable backend POST and path override (`mcp/backend.py:17-52`).
- `MCP_MAX_BATCH`: caps `validate_many`; must be positive (`mcp/validate.py:27-37`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, guard, alias warning | ✅ **Present** | `tests/test_stdio.py:56-147`; `tests/test_stdio.py:283-310` |
| Socket readiness, guard, multi-client threads | ✅ **Present** | `tests/test_socket.py:87-148`; `tests/test_socket.py:199-220` |
| Path traversal rejection | ✅ **Present** | `tests/test_path_traversal.py:25-74` |
| Ready file lifecycle & shutdown | ✅ **Present** | `tests/test_entrypoint.py:61-159` |
| Validation contract & batching | ✅ **Present** | `tests/test_validate.py:56-157` |
| Backend populate flows & guard | ✅ **Present** | `tests/test_backend.py:26-181` |
| Schema discovery (env + submodule) | ✅ **Present** | `tests/test_env_discovery.py:6-26`; `tests/test_submodule_integration.py:16-53` |
| Diff determinism | ✅ **Present** | `tests/test_diff.py:1-21` |
| Golden replay coverage | ✅ **Present** | `tests/test_golden.py:18-105` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON with 1 MiB guard | ✅ **Present** | `mcp/transport.py:13-50`; `tests/test_socket.py:119-131` |
| Ready file `<pid> <ISO8601>` lifecycle | ✅ **Present** | `mcp/__main__.py:115-170`; `tests/test_entrypoint.py:61-74` |
| Path traversal rejection | ✅ **Present** | `mcp/core.py:45-86`; `tests/test_path_traversal.py:25-74` |
| Socket multi-client support | ✅ **Present** | `mcp/socket_main.py:59-123`; `tests/test_socket.py:199-220` |
| `validate` alias warning (v0.2.5) | ✅ **Present** | `mcp/stdio_main.py:23-36`; `tests/test_stdio.py:56-147`; `tests/test_golden.py:66-80` |
| `validate_many` batching with `MCP_MAX_BATCH` | ✅ **Present** | `mcp/validate.py:199-218`; `tests/test_validate.py:103-156` |
| Golden request/response set | ✅ **Present** | `tests/fixtures/golden.jsonl:1-10`; `tests/test_golden.py:18-105` |
| Documentation version alignment | 🟡 **Divergent** | `docs/mcp_spec.md:1-2`; `README.md:1-4` |

## Recommendations
1. Promote the v0.2.5 requirements out of the “Scope (Next)” block and update the spec heading to the current version (`docs/mcp_spec.md:1-2`, `docs/mcp_spec.md:167-215`).
2. Refresh README metadata so the version banner matches the implemented release (`README.md:1-4`).
3. Remove the duplicate `test_backend_assets_path_normalization` definition to keep backend tests unambiguous (`tests/test_backend.py:46-57`, `tests/test_backend.py:170-181`).
