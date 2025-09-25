## Summary of repo state
- STDIO, socket, and TCP share the guarded NDJSON loop and surface semantic failures as `{ok:false}` results (`mcp/transport.py:26`; `mcp/socket_main.py:95`; `tests/test_tcp.py:128`).
- Validation, diff, backend, and discovery utilities enforce deterministic sorting and 1 MiB payload caps with coverage across unit and integration tests (`mcp/validate.py:23`; `mcp/diff.py:19`; `tests/test_validate.py:38`; `tests/test_backend.py:56`).
- Docs and runtime scaffolding advertise the TCP option alongside STDIO/socket and keep container usage non-root with health checks wired through the ready file (`docs/mcp_spec.md:17`; `README.md:35`; `Dockerfile:24`; `docker-compose.yml:25`).

## Top gaps & fixes
- Add an assertion that STDIO shutdown removes the ready file to cover `_clear_ready_file` (`mcp/__main__.py:150`; `tests/test_stdio.py:201`).
- Extend TCP coverage with a concurrent client test to exercise `_handle_connection` thread management (`mcp/tcp_main.py:70`; `tests/test_tcp.py:102`).
- Add a regression test for `MCP_PORT=0` to ensure ephemeral port logging stays correct (`mcp/__main__.py:223`; `tests/test_tcp.py:42`).

## Alignment with mcp_spec.md
| Spec item | Status | Evidence |
| - | - | - |
| STDIO/socket NDJSON transports enforce 1 MiB guard | Present | `mcp/transport.py:26`; `mcp/socket_main.py:110`; `tests/test_socket.py:137` |
| TCP transport with host/port env wiring and guard | Present | `mcp/__main__.py:204`; `mcp/tcp_main.py:56`; `tests/test_tcp.py:42` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:134`; `tests/test_stdio.py:208`; `tests/test_tcp.py:147` |
| Ready/shutdown logs include mode + dirs + ISO timestamp | Present | `mcp/__main__.py:163`; `tests/test_entrypoint.py:44`; `tests/test_socket.py:155` |
| JSON-RPC semantic errors return `{ok:false}` payloads | Present | `mcp/transport.py:77`; `tests/test_stdio.py:256`; `tests/test_socket.py:120` |
| `validate` alias warns and maps to `validate_asset` | Present | `mcp/stdio_main.py:23`; `tests/test_stdio.py:105` |
| `validate_many` enforces `MCP_MAX_BATCH` and per-item limits | Present | `mcp/validate.py:199`; `tests/test_validate.py:103` |
| Path traversal rejected for schemas/examples/assets | Present | `mcp/core.py:16`; `tests/test_path_traversal.py:34` |
| Container runs as non-root with ready-file healthcheck | Present | `Dockerfile:24`; `docker-compose.yml:33`; `tests/test_container.py:4` |
| Golden replay covers tool surface | Present | `tests/fixtures/golden.jsonl:1`; `tests/test_golden.py:45` |

## Transports
- STDIO dispatch uses `process_line` for framed JSON-RPC with payload guard and result wrapping (`mcp/stdio_main.py:51`; `mcp/transport.py:77`; `tests/test_stdio.py:305`).
- Socket server starts with configurable mode, spawns one thread per client, and unlinks the socket on shutdown (`mcp/socket_main.py:27`; `mcp/socket_main.py:39`; `tests/test_socket.py:154`).
- TCP server mirrors the socket implementation with `SO_REUSEADDR`, per-connection threads, and guarded writes (`mcp/tcp_main.py:29`; `mcp/tcp_main.py:98`; `tests/test_tcp.py:102`).

## STDIO entrypoint & process model
- Entrypoint resolves schema roots, selects endpoint, and logs readiness/shutdown with ISO timestamps (`mcp/__main__.py:70`; `mcp/__main__.py:163`; `tests/test_entrypoint.py:44`).
- Ready file records `<pid> <ISO8601>` and is cleared on shutdown (`mcp/__main__.py:134`; `mcp/__main__.py:191`; `tests/test_stdio.py:201`).
- `--validate` CLI path infers schema and returns `{ok, schema}` payloads for tooling (`mcp/__main__.py:206`; `tests/test_entrypoint.py:111`).

## Socket server (multi-client handling, perms, unlink, logs)
- `SocketServer.start` ensures directory creation, pre-existing socket cleanup, and mode enforcement for least-privilege defaults (`mcp/socket_main.py:27`; `mcp/socket_main.py:35`).
- Concurrent clients are served via daemon threads with ordering verified in tests (`mcp/socket_main.py:67`; `tests/test_socket.py:223`).
- Shutdown closes listeners, drains client threads, and removes the socket path (`mcp/socket_main.py:39`; `tests/test_socket.py:284`).

## TCP server (binding, perms, multi-client, shutdown logs)
- TCP listener binds requested host/port with `SO_REUSEADDR` and returns the actual bound address for logging (`mcp/tcp_main.py:25`; `mcp/tcp_main.py:36`).
- Per-connection threads reuse the same NDJSON loop and respect MAX_BYTES guard (`mcp/tcp_main.py:70`; `mcp/tcp_main.py:113`; `tests/test_tcp.py:133`).
- Shutdown path logs mode/host/port with ISO timestamp and closes all threads (`mcp/__main__.py:216`; `tests/test_tcp.py:149`).

## Golden request/response examples
- Golden fixture drives list/get/validate/alias/batch/example/diff/backend/malformed flows with expected stderr markers (`tests/fixtures/golden.jsonl:1`; `tests/test_golden.py:45`).

## Payload size guard
- Dispatch enforces encoded-frame size before JSON decode, sending `{ok:false, reason=validation_failed}` (`mcp/transport.py:26`; `tests/test_stdio.py:305`).
- Socket/TCP loops independently enforce `MAX_BYTES` for raw frames (`mcp/socket_main.py:110`; `mcp/tcp_main.py:113`; `tests/test_socket.py:137`).
- Validation and backend paths reject oversize payloads (`mcp/validate.py:128`; `mcp/backend.py:38`; `tests/test_validate.py:52`; `tests/test_backend.py:56`).

## Schema validation contract
- `validate_asset` enforces schema presence, local-only lookup, and deterministic error ordering (`mcp/validate.py:120`; `tests/test_validate.py:24`).
- `get_example` validates results via `validate_asset`, surfacing `validation_failed` when examples do not conform (`mcp/core.py:147`; `tests/test_validate.py:24`).

## Batching
- `_max_batch` honors positive integer requirement from `MCP_MAX_BATCH` and bubbles configuration errors (`mcp/validate.py:27`; `tests/test_validate.py:90`).
- `validate_many` enforces batch limits and per-item payload guards, returning aggregated results (`mcp/validate.py:182`; `tests/test_validate.py:94`).

## Logging hygiene
- Logging uses `logging.info` with `timestamp=<ISO>` and mode/path/host context, keeping stdout reserved for JSON-RPC frames (`mcp/__main__.py:70`; `mcp/__main__.py:163`; `tests/test_stdio.py:95`).
- Deprecated alias warning goes to stderr as `mcp:warning` (`mcp/stdio_main.py:25`; `tests/test_stdio.py:130`).

## Container & health
- Dockerfile installs dependencies, drops to `USER mcp`, and sets default CMD to `python -m mcp` (`Dockerfile:1`; `Dockerfile:24`).
- Compose service exposes STDIO/socket/TCP envs, mounts `/tmp`, and uses ready-file healthcheck (`docker-compose.yml:16`; `docker-compose.yml:33`).
- `up.sh`/`down.sh` wrap compose lifecycle and clean lingering sockets (`up.sh:3`; `down.sh:12`).

## Schema discovery & validation
- Schema/example roots favor env overrides else submodule directories, with traversal guards (`mcp/core.py:27`; `mcp/core.py:53`; `tests/test_path_traversal.py:34`).
- Listings sort deterministically by name/version/path (`mcp/core.py:69`; `tests/test_submodule_integration.py:20`).

## Test coverage
- Unit and integration suites exercise STDIO/socket/tcp flows, validation, backend, diff, traversal, and golden replay (`tests/test_stdio.py:39`; `tests/test_socket.py:56`; `tests/test_tcp.py:42`; `tests/test_diff.py:1`; `tests/test_backend.py:21`; `tests/test_golden.py:45`).

## Dependencies & runtime
- Runtime depends on `jsonschema` and optional `referencing` for Draft 2020-12, plus `httpx` for backend calls (`requirements.txt:1`; `mcp/validate.py:8`; `mcp/backend.py:7`).
- Test suite relies on `pytest` with configuration in `pytest.ini` (`requirements.txt:3`; `pytest.ini:1`).

## Environment variables
- Endpoint selection and transport options documented and enforced at runtime (`mcp/__main__.py:81`; `README.md:122`).
- Discovery/back-end overrides wired through env with normalization helpers (`mcp/core.py:27`; `mcp/backend.py:17`; `.env.example:1`).

## Documentation accuracy
- Spec v0.2.6 outlines TCP additions, ready log details, and audit criteria reflected in README and compose docs (`docs/mcp_spec.md:12`; `README.md:33`; `docker-compose.yml:16`).

## Detected divergences
- None detected.

## Recommendations
- Add STDIO teardown assertion to confirm ready-file cleanup and guard against regressions (`mcp/__main__.py:150`; `tests/test_stdio.py:201`).
- Introduce a TCP multi-client test to validate thread lifecycle and ordering expectations (`mcp/tcp_main.py:70`; `tests/test_tcp.py:102`).
- Cover `MCP_PORT=0` behavior in tests to lock in ephemeral port logging semantics (`mcp/__main__.py:223`; `tests/test_tcp.py:42`).
