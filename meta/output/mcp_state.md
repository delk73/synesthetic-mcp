## Summary of repo state
- Shared STDIO/socket/TCP dispatcher enforces the 1 MiB guard with ISO ready/shutdown logging under test (`mcp/transport.py:26`; `mcp/__main__.py:165`; `tests/test_tcp.py:89`).
- Validation, diff, and traversal protections stay deterministic with alias folding and sorted outputs (`mcp/core.py:69`; `mcp/validate.py:120`; `mcp/diff.py:42`; `tests/test_validate.py:46`; `tests/test_path_traversal.py:34`).
- Backend populate, golden flows, and container health drop root and exercise success/error paths (`mcp/backend.py:24`; `tests/test_backend.py:28`; `tests/test_golden.py:18`; `Dockerfile:24`).

## Top gaps & fixes (3-5 bullets)
- Implement spec-mandated `-SIGINT`/`-SIGTERM` exit codes and tighten assertions so shutdown no longer returns `0` (`docs/mcp_spec.md:24`; `mcp/__main__.py:157`; `tests/test_entrypoint.py:80`).
- Bump adapter metadata to v0.2.7 in both code and README to reflect the audited spec revision (`docs/mcp_spec.md:2`; `mcp/__init__.py:6`; `README.md:2`).
- Update README payload-guard notes so TCP is documented alongside STDIO/socket enforcement (`README.md:36`; `README.md:176`; `tests/test_tcp.py:135`).

## Alignment with mcp_spec.md
| Spec item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP enforce 1 MiB guard | Present | `mcp/transport.py:26`; `mcp/socket_main.py:110`; `tests/test_tcp.py:135` |
| Socket multi-client ordering + 0600 perms | Present | `mcp/socket_main.py:27`; `tests/test_socket.py:109`; `tests/test_socket.py:232` |
| TCP ready/shutdown logs + multi-client threads | Present | `mcp/tcp_main.py:25`; `tests/test_tcp.py:89`; `tests/test_tcp.py:233` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:134`; `tests/test_stdio.py:201`; `tests/test_tcp.py:317` |
| JSON-RPC errors stay in `result` for semantic failures | Present | `mcp/transport.py:85`; `tests/test_socket.py:124` |
| `validate` alias warns while delegating to `validate_asset` | Present | `mcp/stdio_main.py:23`; `tests/test_stdio.py:105` |
| `validate_many` honors `MCP_MAX_BATCH` | Present | `mcp/validate.py:199`; `tests/test_validate.py:118` |
| `get_example` returns `validation_failed` when invalid | Present | `mcp/core.py:147`; `tests/test_validate.py:32` |
| Traversal guard keeps schemas/examples under configured roots | Present | `mcp/core.py:16`; `tests/test_path_traversal.py:34` |
| Signal shutdown exit codes are `-SIGINT`/`-SIGTERM` | Missing | `docs/mcp_spec.md:24`; `mcp/__main__.py:157`; `tests/test_entrypoint.py:80` |
| Adapter metadata reflects spec v0.2.7 | Divergent | `mcp/__init__.py:6`; `README.md:2`; `docs/mcp_spec.md:2` |
| README states 1 MiB guard for STDIO/socket/TCP | Divergent | `README.md:36`; `README.md:176`; `tests/test_tcp.py:135` |

## Transports
- STDIO uses the shared dispatcher and exits cleanly when stdin closes (`mcp/stdio_main.py:52`; `tests/test_stdio.py:171`).
- Socket and TCP reuse the same NDJSON processing, so guard logic and request ordering stay consistent across transports (`mcp/socket_main.py:27`; `mcp/tcp_main.py:25`; `tests/test_tcp.py:233`).

## STDIO entrypoint & process model
- `_run_stdio` logs readiness/shutdown with mode, schema/example dirs, and ISO timestamps, writes the ready file, and flushes stdout per frame (`mcp/__main__.py:165`; `mcp/stdio_main.py:58`; `tests/test_stdio.py:201`).
- Current signal handling reraises as `KeyboardInterrupt`, so shutdown returns `0` instead of the documented negative signals (`mcp/__main__.py:157`; `tests/test_entrypoint.py:80`).

## Socket server (multi-client handling, perms, unlink, logs)
- Server binds/unlinks the path, enforces configurable mode (default 0600), and removes the socket on shutdown (`mcp/socket_main.py:27`; `mcp/socket_main.py:35`; `tests/test_socket.py:109`).
- Concurrent client test confirms per-connection ordering and continued service after overlapping requests (`tests/test_socket.py:227`; `tests/test_socket.py:269`).

## TCP server (binding, perms, multi-client, shutdown logs)
- TCP server binds requested or ephemeral ports, logs mode/host/port with ISO timestamps, and closes clients with shutdown cleanup (`mcp/tcp_main.py:25`; `tests/test_tcp.py:89`; `tests/test_tcp.py:296`).
- Multi-client threading preserves ordering and leaves the ready file cleaned up after shutdown (`tests/test_tcp.py:233`; `tests/test_tcp.py:317`).

## Lifecycle signals
- SIGINT triggers SIGTERM and raises `KeyboardInterrupt`, but exit codes remain `0`, missing the required `-SIGINT`/`-SIGTERM` semantics (`mcp/__main__.py:157`; `docs/mcp_spec.md:24`; `tests/test_entrypoint.py:80`).

## Golden request/response examples
- Golden replay covers list/get schema, validate + alias warning, batch, example success/failure, diff, backend, and malformed frames (`tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1`).

## Payload size guard
- Transports reject oversized frames before parsing, and validation/backend paths reuse the 1 MiB limit (`mcp/transport.py:26`; `mcp/validate.py:128`; `mcp/backend.py:38`; `tests/test_socket.py:141`; `tests/test_validate.py:56`).

## Schema validation contract
- Alias folding, `$schemaRef` stripping, and sorted error output keep validation deterministic (`mcp/validate.py:137`; `mcp/validate.py:176`; `tests/test_validate.py:46`).
- Invalid example responses propagate validation failures back to callers (`mcp/core.py:147`; `tests/test_validate.py:32`).

## Batching
- `validate_many` enforces the configured limit, per-item results, and payload guard with tests for mixed outcomes and oversize assets (`mcp/validate.py:199`; `tests/test_validate.py:118`; `tests/test_validate.py:145`).

## Logging hygiene
- `_log_event` emits ISO timestamps and key fields to stderr while stdout carries only JSON-RPC frames (`mcp/__main__.py:54`; `mcp/stdio_main.py:58`; `tests/test_entrypoint.py:62`).
- Deprecation warnings for the alias land on stderr as expected (`mcp/stdio_main.py:25`; `tests/test_stdio.py:130`).

## Container & health
- Docker image installs runtime deps then switches to `USER mcp`; compose health check watches the ready file (`Dockerfile:24`; `docker-compose.yml:35`; `tests/test_container.py:4`).

## Schema discovery & validation
- Env overrides direct schema/example roots with deterministic listings and traversal guards (`mcp/core.py:27`; `mcp/core.py:69`; `tests/test_env_discovery.py:32`; `tests/test_path_traversal.py:34`).

## Test coverage
- Transport suites cover guard failures, alias warnings, multi-client scenarios, and ready file cleanup across STDIO/socket/TCP (`tests/test_stdio.py:105`; `tests/test_socket.py:227`; `tests/test_tcp.py:233`).
- Backend, diff, batching, traversal, and golden tests exercise success and failure paths (`tests/test_backend.py:28`; `tests/test_diff.py:16`; `tests/test_validate.py:118`; `tests/test_golden.py:18`).

## Dependencies & runtime
- Runtime requirements remain `jsonschema`, `httpx`, `pytest`, installed in the container layer (`requirements.txt:1`; `Dockerfile:16`).

## Environment variables
- Transport/env validation guards reject unsupported endpoints and bad batch limits, and tests cover override discovery (`mcp/__main__.py:81`; `mcp/validate.py:27`; `tests/test_entrypoint.py:108`; `tests/test_env_discovery.py:29`).

## Documentation accuracy
- README still labels the payload guard as STDIO/socket-only and front-matter version as v0.2.6 despite TCP enforcement and spec bump (`README.md:2`; `README.md:36`; `README.md:176`).
- Spec document already reflects v0.2.7 expectations (`docs/mcp_spec.md:2`).

## Detected divergences
- README omits TCP from the 1 MiB guard description even though implementation and tests enforce it (`README.md:36`; `tests/test_tcp.py:135`).
- Package metadata (`__version__`) and README front matter lag the audited spec version (`mcp/__init__.py:6`; `README.md:2`; `docs/mcp_spec.md:2`).

## Recommendations
- Return `-SIGINT`/`-SIGTERM` on signal-driven shutdowns and assert them in `test_entrypoint_ready_and_shutdown` (`mcp/__main__.py:157`; `tests/test_entrypoint.py:80`; `docs/mcp_spec.md:24`).
- Update the published version strings to v0.2.7 in code and README front matter to match the spec (`mcp/__init__.py:6`; `README.md:2`; `docs/mcp_spec.md:2`).
- Refresh README transport notes so the 1 MiB guard explicitly covers STDIO/socket/TCP and mention the TCP guard under Serving Locally (`README.md:36`; `README.md:176`; `tests/test_tcp.py:135`).
