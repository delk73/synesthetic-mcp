## Summary of repo state
- Shared NDJSON dispatcher applies the 1 MiB guard across STDIO/socket/TCP with regression coverage on oversize frames (`mcp/transport.py:26`; `tests/test_socket.py:141`; `tests/test_tcp.py:142`).
- Entrypoint logging captures mode, schema/example roots, and maintains the `<pid> <ISO8601>` ready file through shutdown with negative signal exits under test (`mcp/__main__.py:139`; `mcp/__main__.py:165`; `tests/test_stdio.py:203`; `tests/test_entrypoint.py:84`).
- Validation, diff, examples, and backend flows remain deterministic via sorted outputs, alias warnings, and guarded populate calls (`mcp/validate.py:176`; `mcp/stdio_main.py:24`; `mcp/diff.py:42`; `tests/test_backend.py:23`; `tests/test_validate.py:46`).

## Top gaps & fixes (3-5 bullets)
- Add a `jsonrpc == "2.0"` assertion in `parse_line` and cover rejection in a STDIO unit test to tighten JSON-RPC compliance (`mcp/transport.py:26`; `tests/test_stdio.py:261`).
- Extend the SIGTERM entrypoint test to assert ready-file cleanup so lifecycle guarantees cover both signals (`mcp/__main__.py:283`; `tests/test_entrypoint.py:87`).
- Mirror the SIGINT signal assertions for socket/TCP with SIGTERM coverage to prove cleanup and exit codes across transports (`mcp/__main__.py:275`; `tests/test_socket.py:158`; `tests/test_tcp.py:158`).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP enforce 1 MiB guard | Present | `mcp/transport.py:26`; `tests/test_socket.py:141`; `tests/test_tcp.py:142` |
| Ready/shutdown logs include mode + address/path + ISO timestamps | Present | `mcp/__main__.py:165`; `mcp/__main__.py:283`; `tests/test_entrypoint.py:65` |
| Ready file records `<pid> <ISO8601>` and is cleared on shutdown | Present | `mcp/__main__.py:139`; `mcp/__main__.py:155`; `tests/test_stdio.py:208`; `tests/test_tcp.py:317` |
| Signal shutdown exits use `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:176`; `mcp/__main__.py:407`; `tests/test_entrypoint.py:84`; `tests/test_entrypoint.py:125` |
| Socket 0600 perms + multi-client ordering | Present | `mcp/socket_main.py:35`; `mcp/socket_main.py:66`; `tests/test_socket.py:109`; `tests/test_socket.py:227` |
| TCP multi-client ordering + readiness logs | Present | `mcp/tcp_main.py:69`; `mcp/tcp_main.py:264`; `tests/test_tcp.py:158`; `tests/test_tcp.py:233` |
| Semantic validation errors return in JSON-RPC `result` | Present | `mcp/transport.py:85`; `tests/test_socket.py:124`; `tests/test_stdio.py:280` |
| `validate` alias warns and requires `schema` | Present | `mcp/stdio_main.py:24`; `mcp/stdio_main.py:28`; `tests/test_stdio.py:138` |
| `validate_many` honors `MCP_MAX_BATCH` and payload cap | Present | `mcp/validate.py:199`; `mcp/validate.py:208`; `tests/test_validate.py:118`; `tests/test_validate.py:145` |
| Schema/example traversal guards reject escapes | Present | `mcp/core.py:16`; `mcp/core.py:61`; `tests/test_path_traversal.py:31` |
| Golden suite covers list/get/validate/diff/backend/malformed | Present | `tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1` |
| Docs + metadata reflect v0.2.7 with TCP guard guidance | Present | `mcp/__init__.py:6`; `README.md:2`; `README.md:36`; `README.md:177` |

## Transports
- Socket/TCP servers share the NDJSON loop, enforcing payload caps before decoding (`mcp/socket_main.py:95`; `mcp/tcp_main.py:98`).
- End-to-end tests prove readiness logging, oversize rejection, and graceful client handling for both transports (`tests/test_socket.py:101`; `tests/test_tcp.py:111`).

## STDIO entrypoint & process model
- Entrypoint installs signal handlers, logs readiness/shutdown, writes the ready file, and runs the STDIO loop until stdin closes (`mcp/__main__.py:162`; `mcp/stdio_main.py:51`; `tests/test_stdio.py:150`).
- Ready file contents capture `<pid> <ISO8601>` and are removed once the loop exits (`mcp/__main__.py:139`; `tests/test_stdio.py:208`; `tests/test_stdio.py:253`).

## Socket server (multi-client handling, perms, unlink, logs)
- Startup unlinks stale sockets, binds with configurable mode (default 0600), spins per-connection threads, and unlinks on close (`mcp/socket_main.py:27`; `mcp/socket_main.py:35`; `mcp/socket_main.py:50`).
- Tests confirm mode enforcement, payload guard, multi-client ordering, and ready file cleanup after signals (`tests/test_socket.py:109`; `tests/test_socket.py:138`; `tests/test_socket.py:227`; `tests/test_socket.py:173`).

## TCP server (binding, perms, multi-client, shutdown logs)
- TCP listener binds requested or ephemeral port, logs bound host/port, and drains client threads on shutdown (`mcp/tcp_main.py:25`; `mcp/tcp_main.py:264`; `mcp/tcp_main.py:291`).
- Multi-client and validation tests assert per-connection ordering, alias handling, and ready file removal under SIGINT (`tests/test_tcp.py:233`; `tests/test_tcp.py:275`; `tests/test_tcp.py:317`).

## Lifecycle signals
- Custom signal handler raises `_SignalShutdown`, propagating `-signum` to callers before re-raising the original signal (`mcp/__main__.py:70`; `mcp/__main__.py:176`; `mcp/__main__.py:407`).
- Entry-point tests cover SIGINT/SIGTERM exit codes and shutdown logs (`tests/test_entrypoint.py:65`; `tests/test_entrypoint.py:84`; `tests/test_entrypoint.py:125`).

## Golden request/response examples
- Golden replay exercises list/get schema, validate + alias warning, batch validation, example success/failure, diff, backend disabled, and malformed payloads (`tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1`).

## Payload size guard
- Guard constant shared across transports, validation, and backend populate to return `payload_too_large` before dispatch (`mcp/validate.py:23`; `mcp/transport.py:26`; `mcp/backend.py:38`).
- Tests inject oversize frames/objects over STDIO/socket/TCP and inside `validate_many` to verify failures (`tests/test_stdio.py:310`; `tests/test_socket.py:141`; `tests/test_tcp.py:142`; `tests/test_validate.py:145`).

## Schema validation contract
- Alias folding, `$schemaRef` stripping, and sorted error lists keep validation deterministic (`mcp/validate.py:137`; `mcp/validate.py:176`).
- Invalid examples surface `validation_failed` responses while success paths return validated examples (`mcp/core.py:147`; `tests/test_validate.py:32`).

## Batching
- `validate_many` checks input type, enforces `MCP_MAX_BATCH`, and carries per-item results; tests cover mixed outcomes, limit enforcement, and oversize payloads (`mcp/validate.py:190`; `mcp/validate.py:199`; `tests/test_validate.py:118`; `tests/test_validate.py:145`).

## Logging hygiene
- `_log_event` emits ISO-8601 timestamps and contextual fields to stderr while STDIO writes JSON-RPC frames to stdout (`mcp/__main__.py:51`; `mcp/stdio_main.py:57`).
- Tests assert timestamp presence and alias warnings arriving on stderr (`tests/test_entrypoint.py:65`; `tests/test_stdio.py:138`).

## Container & health
- Docker image drops to `USER mcp` after install and preserves a non-root HOME (`Dockerfile:24`; `Dockerfile:27`).
- Ready-file lifecycle provides a simple health indicator consumed by tests and compose tooling (`mcp/__main__.py:139`; `tests/test_stdio.py:203`; `tests/test_tcp.py:317`).

## Schema discovery & validation
- Discovery honors `SYN_*` overrides with deterministic ordering and traversal guards (`mcp/core.py:27`; `mcp/core.py:69`; `tests/test_env_discovery.py:29`; `tests/test_path_traversal.py:31`).
- Submodule integration test ensures defaults fall back to bundled schemas/examples when present (`tests/test_submodule_integration.py:19`; `tests/test_submodule_integration.py:53`).

## Test coverage
- Transport suites cover framing, alias warnings, payload guards, multi-client ordering, and ready file cleanup (`tests/test_stdio.py:138`; `tests/test_socket.py:227`; `tests/test_tcp.py:233`).
- Backend, diff, validation, traversal, and golden fixtures exercise both happy and failure paths (`tests/test_backend.py:23`; `tests/test_diff.py:7`; `tests/test_validate.py:46`; `tests/test_golden.py:18`).

## Dependencies & runtime
- Runtime dependencies remain `jsonschema`, `httpx`, and `pytest`, matching container install steps (`requirements.txt:1`; `Dockerfile:16`; `Dockerfile:21`).

## Environment variables
- Entry-point validation covers transport selectors, socket mode, host/port, and ready file wiring (`mcp/__main__.py:86`; `mcp/__main__.py:100`; `mcp/__main__.py:123`; `mcp/__main__.py:139`).
- Tests verify env overrides for schemas/examples and unsupported endpoint handling (`tests/test_env_discovery.py:16`; `tests/test_entrypoint.py:167`).

## Documentation accuracy
- README front matter and transport sections reference v0.2.7, TCP usage, and shared 1 MiB guard, aligning with the spec additions (`README.md:2`; `README.md:35`; `README.md:176`; `docs/mcp_spec.md:40`).
- Spec file documents the same lifecycle expectations verified in tests (`docs/mcp_spec.md:24`; `docs/mcp_spec.md:30`).

## Detected divergences
- None detected.

## Recommendations
- Enforce and test the `jsonrpc == "2.0"` requirement so unsupported protocol versions return `validation_failed` instead of silently executing (`mcp/transport.py:26`; `tests/test_stdio.py:261`).
- Extend signal lifecycle tests to cover SIGTERM cleanup (ready file + shutdown log) for the STDIO path to match documented guarantees (`mcp/__main__.py:283`; `tests/test_entrypoint.py:87`).
- Add SIGTERM-driven shutdown tests for socket and TCP transports to ensure exit codes and cleanup stay consistent across endpoints (`mcp/__main__.py:275`; `tests/test_socket.py:158`; `tests/test_tcp.py:158`).
