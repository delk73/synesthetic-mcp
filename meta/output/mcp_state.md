## Summary of repo state
- STDIO, socket, and TCP transports share the guarded NDJSON dispatcher and surface semantic errors inside `result` payloads (`mcp/transport.py:17`, `mcp/socket_main.py:95`, `mcp/tcp_main.py:98`, `tests/test_stdio.py:261`, `tests/test_socket.py:120`).
- Validation, diff, backend, and discovery paths enforce deterministic ordering, traversal guards, and 1 MiB payload caps with dedicated tests (`mcp/validate.py:120`, `mcp/diff.py:42`, `mcp/core.py:69`, `mcp/backend.py:38`, `tests/test_validate.py:14`, `tests/test_diff.py:4`, `tests/test_path_traversal.py:34`, `tests/test_backend.py:56`).
- Logging, ready file lifecycle, and container defaults match v0.2.6 expectations with ISO-8601 timestamps, ready file cleanup, and non-root images (`mcp/__main__.py:163`, `mcp/__main__.py:280`, `tests/test_stdio.py:190`, `tests/test_socket.py:155`, `tests/test_tcp.py:151`, `Dockerfile:24`, `tests/test_container.py:4`).

## Top gaps & fixes (3-5 bullets)
- Add a TCP `validate_asset` round-trip to satisfy the v0.2.6 audit requirement for transport coverage (`docs/mcp_spec.md:64`, `tests/test_tcp.py:104`); extend `tests/test_tcp.py` to post a `validate_asset` request using the same client session.
- Prove the Unix socket honors the 0600 default by asserting `stat().st_mode` in the end-to-end test (`docs/mcp_spec.md:58`, `mcp/socket_main.py:35`, `tests/test_socket.py:98`); capture the mode before shutdown to ensure least-privilege permissions stay enforced.
- Exercise the network-exception path in `populate_backend` so the 503 mapping for `httpx.HTTPError` is covered (`mcp/backend.py:58`, `tests/test_backend.py:21`); configure a `MockTransport` that raises to confirm reason/status handling.

## Alignment with mcp_spec.md
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON loop rejects >1 MiB before dispatch | Present | `mcp/transport.py:17` · `tests/test_stdio.py:310` |
| Socket multi-client ordering, cleanup, and logs | Present | `mcp/socket_main.py:53` · `tests/test_socket.py:175` |
| TCP readiness/shutdown logs include host/port + dirs | Present | `mcp/__main__.py:264` · `tests/test_tcp.py:87` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:134` · `tests/test_stdio.py:200` |
| `validate` alias warns and routes to `validate_asset` | Present | `mcp/stdio_main.py:23` · `tests/test_stdio.py:105` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:199` · `tests/test_validate.py:103` |
| TCP integration covers `validate_asset` round-trip | Missing | `docs/mcp_spec.md:64` · `tests/test_tcp.py:104` |
| Socket file mode defaults to 0600 and is verified | Missing | `mcp/socket_main.py:35` · `tests/test_socket.py:98` |

## Transports
- STDIO loop shares the transport dispatcher and only emits JSON-RPC frames on stdout (`mcp/stdio_main.py:51`, `tests/test_stdio.py:39`).
- Socket server threads per client, unlinks the path on shutdown, and streams logs to stderr (`mcp/socket_main.py:77`, `tests/test_socket.py:154`).
- TCP server binds configured host/port (including `port=0`), maintains per-connection ordering, and closes gracefully (`mcp/tcp_main.py:25`, `tests/test_tcp.py:173`, `tests/test_tcp.py:331`).

## STDIO entrypoint & process model
- `_run_stdio` logs readiness/shutdown with schemas/examples dirs, installs signal handlers, and clears the ready file (`mcp/__main__.py:163`, `mcp/__main__.py:180`, `mcp/__main__.py:191`).
- Ready file contents record `<pid> <ISO>` and are removed once stdin closes (`mcp/__main__.py:134`, `tests/test_stdio.py:200`, `tests/test_stdio.py:250`).
- CLI `--validate` helper infers schema names and maps exit codes for automation (`mcp/__main__.py:299`, `tests/test_entrypoint.py:130`).

## Socket server (multi-client handling, perms, unlink, logs)
- Accept loop spawns daemon threads and tracks them for orderly shutdown (`mcp/socket_main.py:53`, `mcp/socket_main.py:88`).
- Startup log includes mode/path with ISO timestamp and ready file cleanup is verified (`mcp/__main__.py:213`, `tests/test_socket.py:98`, `tests/test_socket.py:169`).
- Socket path is `chmod`-ed to requested mode, but no automated assertion confirms the 0600 default (`mcp/socket_main.py:35`).

## TCP server (binding, perms, multi-client, shutdown logs)
- Server enables `SO_REUSEADDR`, records bound host/port, and exposes them for logging (`mcp/tcp_main.py:25`, `mcp/tcp_main.py:36`).
- Multi-client test asserts request ordering per connection and readiness/shutdown logs capture schema/example dirs (`tests/test_tcp.py:218`, `tests/test_tcp.py:311`).
- Ephemeral port binding is logged and asserted when `MCP_PORT=0` (`tests/test_tcp.py:331`, `tests/test_tcp.py:372`).

## Golden request/response examples
- Golden replay walks list/get schema, validate + alias, batch validate, diff, backend disabled, and malformed frame scenarios (`tests/fixtures/golden.jsonl:1`, `tests/test_golden.py:45`).
- Deprecated alias warning is observed via `stderr_contains` checks in the golden harness (`tests/fixtures/golden.jsonl:4`).

## Payload size guard
- Transport-level guard compares encoded byte length before JSON parsing (`mcp/transport.py:17`, `mcp/socket_main.py:110`, `mcp/tcp_main.py:113`).
- Validation and backend paths reject oversized assets with `payload_too_large` errors (`mcp/validate.py:128`, `mcp/backend.py:38`).
- Tests exercise oversize rejection across STDIO, socket, TCP, validation, and backend APIs (`tests/test_stdio.py:310`, `tests/test_socket.py:137`, `tests/test_tcp.py:137`, `tests/test_validate.py:56`, `tests/test_backend.py:56`).

## Schema validation contract
- `validate_asset` enforces schema presence, alias remapping, local registry, and sorted errors (`mcp/validate.py:120`, `mcp/validate.py:166`, `mcp/validate.py:176`).
- `get_example` infers schema, validates lazily, and returns `validation_failed` on errors (`mcp/core.py:147`, `tests/test_validate.py:32`).
- Path traversal and schema root guards raise `validation_failed` for out-of-root requests (`mcp/core.py:16`, `tests/test_path_traversal.py:34`).

## Batching
- `validate_many` enforces type checks, per-item validation, and `MCP_MAX_BATCH` limit with failure detail (`mcp/validate.py:182`, `mcp/validate.py:199`).
- Tests cover mixed success, oversized batches, and oversized per-asset payloads (`tests/test_validate.py:78`, `tests/test_validate.py:103`, `tests/test_validate.py:128`).

## Logging hygiene
- `_log_event` prefixes ISO-8601 timestamps and keeps logs on stderr (`mcp/__main__.py:50`, `mcp/__main__.py:54`).
- Ready/shutdown lines include mode + address/path + schemas/examples dir for every transport (`mcp/__main__.py:163`, `mcp/__main__.py:213`, `mcp/__main__.py:280`).
- Tests assert timestamp formatting and log fields across STDIO, socket, TCP (`tests/test_stdio.py:101`, `tests/test_socket.py:98`, `tests/test_tcp.py:87`, `tests/test_entrypoint.py:62`).

## Container & health
- Docker image installs deps, drops to `USER mcp`, and defaults to `python -m mcp` (`Dockerfile:16`, `Dockerfile:24`, `Dockerfile:30`).
- Compose `serve` service exposes TCP envs, mounts `/tmp` for ready file, and defines a ready-file healthcheck (`docker-compose.yml:15`, `docker-compose.yml:31`, `docker-compose.yml:35`).
- Tests confirm non-root default and ready file availability (`tests/test_container.py:4`).

## Schema discovery & validation
- Discovery prefers env overrides then submodule directories, with deterministic ordering of listings (`mcp/core.py:27`, `mcp/core.py:69`, `mcp/core.py:106`).
- Submodule integration test ensures canonical assets validate and ordering stays sorted (`tests/test_submodule_integration.py:23`, `tests/test_submodule_integration.py:34`).
- Env discovery test confirms overrides populate listing results (`tests/test_env_discovery.py:7`).

## Test coverage
- Transport behavior, logging, validation, diff, backend, batching, traversal, and container posture each have focused pytest modules (`tests/test_stdio.py`, `tests/test_socket.py`, `tests/test_tcp.py`, `tests/test_validate.py`, `tests/test_diff.py`, `tests/test_backend.py`, `tests/test_path_traversal.py`, `tests/test_container.py`).
- Golden replay secures deterministic responses for core JSON-RPC workflows (`tests/test_golden.py:45`).

## Dependencies & runtime
- Runtime deps are limited to `jsonschema` and `httpx`, with pytest for tests and optional `referencing` registry support (`requirements.txt:1`, `mcp/validate.py:8`).
- Optional registry import is guarded so missing extras do not break validation (`mcp/validate.py:9`).

## Environment variables
- Entry point parses `MCP_ENDPOINT`, socket path/mode, TCP host/port (including `0`), and ready file overrides with validation (`mcp/__main__.py:81`, `mcp/__main__.py:95`, `mcp/__main__.py:118`, `mcp/__main__.py:124`).
- Backend and schema discovery envs (`SYN_*`) are consumed by validation/backends (`mcp/backend.py:14`, `mcp/core.py:27`).
- README documents defaults alongside `.env.example` coverage (`README.md:94`, `.env.example:1`).

## Documentation accuracy
- README and spec document transports, payload guard, alias, batching, and container posture aligned with implementation (`README.md:35`, `docs/mcp_spec.md:17`).
- Compose and scripts mention TCP alongside STDIO/socket (`docker-compose.yml:15`, `up.sh:4`, `down.sh:7`).

## Detected divergences
- None beyond the noted missing transport/test coverage items; transports and APIs align with v0.2.6 spec language.

## Recommendations
- Extend TCP integration tests with a `validate_asset` call to satisfy the v0.2.6 audit clause (`docs/mcp_spec.md:64`, `tests/test_tcp.py:104`).
- Assert the Unix socket path permissions post-start to prove the default 0600 restriction (`mcp/socket_main.py:35`, `tests/test_socket.py:98`).
- Add a backend test that forces `httpx.HTTPError` to confirm `populate_backend` returns `{ok:false, reason:"backend_error", status:503}` (`mcp/backend.py:58`).
