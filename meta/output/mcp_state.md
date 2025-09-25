## Summary of repo state
- All three transports (STDIO, socket, TCP) share the guarded NDJSON dispatcher, emit ISO-8601 timestamps on readiness/shutdown, and clean up ready files or sockets on exit (`mcp/__main__.py:163`; `mcp/socket_main.py:27`; `mcp/tcp_main.py:14`; `tests/test_tcp.py:47`).
- Validation, diff, backend, and discovery flows remain deterministic with 1 MiB payload caps covered by unit and integration tests (`mcp/validate.py:120`; `mcp/diff.py:42`; `tests/test_validate.py:56`; `tests/test_backend.py:56`).
- Semantically invalid requests now return JSON-RPC results (`reason=validation_failed|unsupported`) instead of top-level errors, aligning transports with the v0.2.6 spec (`mcp/transport.py:73`; `tests/test_stdio.py:262`; `tests/test_socket.py:123`).

## Top gaps & fixes (3-5 bullets)
- None detected; implementation, tests, and docs align with the v0.2.6 specification.

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON loop with 1 MiB guard | Present | `mcp/transport.py:13`; `tests/test_stdio.py:292` |
| Socket multi-client ordering, guard, unlink | Present | `mcp/socket_main.py:66`; `tests/test_socket.py:187` |
| TCP transport (`MCP_ENDPOINT=tcp`, host/port, guard, tests) | Present | `mcp/__main__.py:216`; `mcp/tcp_main.py:14`; `tests/test_tcp.py:47` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:89`; `tests/test_stdio.py:196`; `tests/test_socket.py:147`; `tests/test_tcp.py:53` |
| Ready/shutdown logs include dirs + ISO timestamp | Present | `mcp/__main__.py:120`; `tests/test_entrypoint.py:67`; `tests/test_socket.py:105`; `tests/test_tcp.py:59` |
| `validate` alias warning | Present | `mcp/stdio_main.py:25`; `tests/test_stdio.py:107` |
| `validate_many` honours `MCP_MAX_BATCH` | Present | `mcp/validate.py:199`; `tests/test_validate.py:103` |
| `get_example` invalid → `validation_failed` | Present | `mcp/core.py:147`; `tests/test_validate.py:32` |
| Schema traversal guard (schemas & examples) | Present | `mcp/core.py:16`; `tests/test_path_traversal.py:34` |
| Deterministic listings/errors/diff ordering | Present | `mcp/core.py:85`; `mcp/diff.py:49`; `tests/test_submodule_integration.py:30` |
| Spec errors stay in JSON-RPC result | Present | `mcp/transport.py:73`; `tests/test_stdio.py:262`; `tests/test_tcp.py:78` |
| Payload guard inside validation/backend flows | Present | `mcp/validate.py:128`; `mcp/backend.py:58`; `tests/test_validate.py:56` |
| Container runs non-root | Present | `Dockerfile:24`; `tests/test_container.py:1` |
| Docs/scripts reflect TCP mode | Present | `docs/mcp_spec.md:19`; `README.md:35`; `.env.example:3`; `docker-compose.yml:19` |

## Transports
- STDIO, socket, and TCP dispatchers share `mcp.transport.process_line`, apply the 1 MiB guard, and flush NDJSON frames in order (`mcp/transport.py:41`; `mcp/socket_main.py:66`; `mcp/tcp_main.py:59`).
- TCP listener binds to `MCP_HOST:MCP_PORT`, supports per-connection threads, and logs readiness/shutdown with directory metadata (`mcp/__main__.py:216`; `mcp/tcp_main.py:14`; `tests/test_tcp.py:47`).

## STDIO entrypoint & process model
- Ready/shutdown logs carry ISO timestamps and schema/example roots; SIGINT/SIGTERM funnel through the shared shutdown handler so the ready file is always cleared (`mcp/__main__.py:115`; `mcp/__main__.py:247`; `tests/test_entrypoint.py:67`).

## Socket server (multi-client handling, perms, unlink, logs)
- Socket server unlinks stale files, enforces configured mode, serves clients concurrently, and removes the socket on shutdown (`mcp/socket_main.py:27`; `tests/test_socket.py:187`).

## TCP server (binding, perms, multi-client, shutdown logs)
- TCP server sets SO_REUSEADDR, tracks bound address, preserves per-connection ordering, and joins client threads on shutdown (`mcp/tcp_main.py:20`; `mcp/tcp_main.py:44`; `tests/test_tcp.py:47`).

## Golden request/response examples
- STDIO replay covers list/get schema, validation (+ alias), get_example success/failure, diff, backend disabled, and malformed JSON (still a JSON-RPC error) (`tests/fixtures/golden.jsonl:1`; `tests/test_golden.py:45`).

## Payload size guard
- Transport rejects oversized frames pre-parse, and validation/backend paths return `payload_too_large` inside result payloads (`mcp/transport.py:58`; `mcp/validate.py:128`; `mcp/backend.py:58`; `tests/test_tcp.py:89`).

## Schema validation contract
- `validate_asset` enforces schema presence, alias resolution, traversal guard, and deterministic errors; `get_example` validates retrieved assets (`mcp/validate.py:120`; `mcp/core.py:147`; `tests/test_validate.py:46`).

## Batching
- `_max_batch` enforces positive integers sourced from `MCP_MAX_BATCH`, returning `{ok:false, reason:'unsupported'}` when exceeded and surfacing per-entry payload violations (`mcp/validate.py:199`; `tests/test_validate.py:103`; `tests/test_validate.py:128`).

## Logging hygiene
- Ready/shutdown logs now include `timestamp=`, `mode`, transport-specific coordinates, and schema/example paths across all transports (`mcp/__main__.py:120`; `tests/test_entrypoint.py:67`; `tests/test_socket.py:105`; `tests/test_tcp.py:59`).

## Container & health
- Docker image runs as `mcp`, TCP variables flow through docker-compose, and health checks continue to rely on `/tmp/mcp.ready` (`Dockerfile:24`; `docker-compose.yml:16`; `.env.example:3`).

## Schema discovery & validation
- Env overrides, submodule fallbacks, traversal guards, and deterministic listings remain covered (`mcp/core.py:27`; `tests/test_env_discovery.py:6`; `tests/test_submodule_integration.py:22`).

## Test coverage
- Suite covers transports (STDIO/socket/TCP), validation, backend, diff, traversal, golden replay, and logging assertions; 38 tests pass with 3 platform skips (`tests/test_tcp.py:47`; `tests/test_socket.py:45`; `tests/test_validate.py:14`).

## Dependencies & runtime
- Runtime deps remain `jsonschema` and `httpx`, with optional `referencing`; CI exercises Python 3.11–3.13 (`requirements.txt:1`; `mcp/validate.py:8`; `.github/workflows/ci.yml:20`).

## Environment variables
- `MCP_ENDPOINT`, `MCP_SOCKET_*`, `MCP_HOST`, `MCP_PORT`, ready file, discovery, backend, and batching knobs are validated and documented (`mcp/__main__.py:47`; `README.md:94`; `.env.example:2`).

## Documentation accuracy
- Spec, README, env sample, and compose files document the v0.2.6 transport matrix, logging expectations, and environment variables (`docs/mcp_spec.md:17`; `README.md:35`; `.env.example:2`; `docker-compose.yml:16`).

## Detected divergences
- None.

## Recommendations
- None; v0.2.6 feature set is fully implemented and covered.
