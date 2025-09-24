# AGENTS.md — Repo Snapshot (v0.2.6 Audit)

## Repo Summary
- STDIO and socket share the guarded NDJSON dispatcher with multi-client coverage and ready-file lifecycle intact (`mcp/transport.py:13`; `tests/test_socket.py:147`).
- Validation, diff, backend, and discovery flows remain deterministic under payload caps across units/integration (`mcp/validate.py:176`; `mcp/diff.py:49`; `tests/test_validate.py:56`).
- TCP transport and v0.2.6 observability upgrades are missing, leaving the runtime/docs at v0.2.5 behavior (`docs/mcp_spec.md:19`; `mcp/__main__.py:47`; `README.md:35`).
- Logging still omits shutdown directory fields and ISO timestamps, diverging from the new spec (`docs/mcp_spec.md:25`; `mcp/__main__.py:131`; `mcp/__main__.py:252`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend) | `requirements.txt:2`; `mcp/backend.py:7` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_stdio.py:12` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:8`; `mcp/validate.py:66` |

## Environment Variables
- `MCP_ENDPOINT`: accepts `stdio` or `socket`; rejects other transports such as the expected `tcp` (`mcp/__main__.py:47`).
- `MCP_READY_FILE`: defaults to `/tmp/mcp.ready`, written with `<pid> <ISO8601>` and cleared on shutdown (`mcp/__main__.py:80`; `tests/test_stdio.py:183`).
- `MCP_SOCKET_PATH` / `MCP_SOCKET_MODE`: configure UDS path and default 0600 permissions (`mcp/__main__.py:57`; `mcp/socket_main.py:35`).
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR`: override discovery roots (`mcp/core.py:27`; `mcp/core.py:40`).
- `SYN_BACKEND_URL` / `SYN_BACKEND_ASSETS_PATH`: enable backend POSTs and normalise asset path (`mcp/backend.py:30`; `mcp/backend.py:17`).
- `MCP_MAX_BATCH`: caps `validate_many`; enforced positive integer (`mcp/validate.py:27`).
- Missing: spec'd `MCP_HOST`/`MCP_PORT` for TCP are not implemented or documented (`docs/mcp_spec.md:19`; `.env.example:2`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, alias warning, payload guard | ✅ Present | `tests/test_stdio.py:56`; `tests/test_stdio.py:283` |
| Socket readiness, guard, multi-client threads | ✅ Present | `tests/test_socket.py:45`; `tests/test_socket.py:153` |
| TCP transport round-trip | ❌ Missing | `docs/mcp_spec.md:24`; `tests/` (no TCP coverage) |
| Path traversal rejection | ✅ Present | `tests/test_path_traversal.py:34` |
| Ready file lifecycle (PID + ISO) | ✅ Present | `tests/test_stdio.py:183`; `tests/test_socket.py:147` |
| Validation contract & batching | ✅ Present | `tests/test_validate.py:46`; `tests/test_validate.py:103` |
| Backend populate flows & guard | ✅ Present | `tests/test_backend.py:21`; `tests/test_backend.py:56` |
| Golden replay coverage (STDIO) | ✅ Present | `tests/fixtures/golden.jsonl:1`; `tests/test_golden.py:45` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO & socket NDJSON with 1 MiB guard | Present | `mcp/transport.py:13`; `tests/test_socket.py:119` |
| TCP transport (`MCP_ENDPOINT=tcp`, host/port, guard, tests) | Missing | `docs/mcp_spec.md:19`; `mcp/__main__.py:47`; `tests/test_entrypoint.py:99` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:80`; `tests/test_stdio.py:183` |
| Ready/shutdown logs include dirs + ISO timestamp | Divergent | `docs/mcp_spec.md:25`; `mcp/__main__.py:131`; `mcp/__main__.py:252` |
| Spec errors returned in JSON-RPC result payloads | Divergent | `meta/prompts/mcp_audit.json:10`; `tests/test_stdio.py:238` |
| `validate` alias warning (pre-v0.3) | Present | `mcp/stdio_main.py:25`; `tests/test_stdio.py:117` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:199`; `tests/test_validate.py:103` |
| Container runs non-root | Present | `Dockerfile:24`; `tests/test_container.py:1` |
| Docs/scripts updated for TCP | Missing | `docs/mcp_spec.md:23`; `README.md:35`; `.env.example:2` |

## Recommendations
1. Ship the TCP transport (shared handler, host/port env, guard, ready/shutdown logs) with an integration test mirroring the socket suite (`docs/mcp_spec.md:19`; `mcp/__main__.py:47`; `tests/test_socket.py:45`).
2. Include `schemas_dir`/`examples_dir` and ISO timestamps on shutdown logs for all transports by adjusting the logging formatter (`docs/mcp_spec.md:25`; `mcp/__main__.py:131`; `mcp/__main__.py:252`).
3. Return semantic failures as `{ok:False}` results instead of JSON-RPC errors when requests parse but violate contract (`meta/prompts/mcp_audit.json:10`; `mcp/transport.py:41`; `tests/test_stdio.py:238`).
4. Refresh README, `.env.example`, and docker-compose defaults to document and enable TCP mode once implemented (`docs/mcp_spec.md:23`; `README.md:35`; `docker-compose.yml:22`).
